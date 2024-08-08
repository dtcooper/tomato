import logging
import tempfile

from django import forms
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.generic import TemplateView

from django_file_form.forms import FileFormMixin, UploadedFileField

from ...models import (
    REQUIRED_EMPTY_FOR_IMPORT_MODEL_CLASSES,
    ImportTomatoDataException,
    export_data_as_zip,
    import_data_from_zip,
)
from .base import AdminViewMixin


logger = logging.getLogger(__name__)


class ImportUploadForm(FileFormMixin, forms.Form):
    file = UploadedFileField()


class AdminAssetDataView(AdminViewMixin, TemplateView):
    name = "asset_data"
    perms = ("tomato.export_import",)
    title = "Manage asset data"

    def get_context_data(self, **kwargs):
        import_upload_form = ImportUploadForm()
        if self.request.method == "POST":
            action = self.request.POST.get("action")
            if action == "import":
                import_upload_form = ImportUploadForm(self.request.POST, self.request.FILES)

        return {
            "import_upload_form": import_upload_form,
            "can_delete": self.request.user.is_superuser,
            "can_import": not any(model_cls.objects.exists() for model_cls in REQUIRED_EMPTY_FOR_IMPORT_MODEL_CLASSES),
            **super().get_context_data(**kwargs),
        }

    def do_export(self):
        zip_file = tempfile.NamedTemporaryFile("wb+")
        zip_filename = export_data_as_zip(zip_file)
        zip_file.seek(0)  # Go back to beginning of file
        response = HttpResponse(zip_file, content_type="application/octet-stream")
        response["Content-Disposition"] = f'attachment; filename="{zip_filename}"'
        return response

    def do_import(self, file):
        try:
            info = import_data_from_zip(file, created_by=self.request.user)
        except ImportTomatoDataException as e:
            self.message_user(f"Import error: {e}", messages.ERROR)
        except Exception as e:
            error_str = "Unexpected import error! Please try again."
            if settings.DEBUG:
                error_str = f"{error_str} Debug: {e}"
            logger.exception("Unexpected import error!")
            self.message_user(error_str, messages.ERROR)
        else:
            self.message_user(f"Successfully imported {', '.join(f'{num} {entity}' for entity, num in info.items())}!")
        return redirect("admin:extra_asset_data")

    def do_delete(self):
        for model_cls in REQUIRED_EMPTY_FOR_IMPORT_MODEL_CLASSES:
            model_cls.objects.all().delete()
        self.message_user("All asset data completely deleted!", messages.WARNING)
        return redirect("admin:extra_asset_data")

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        can_import, can_delete = context["can_import"], context["can_delete"]
        action = self.request.POST.get("action")
        if can_import and action == "import":
            if context["import_upload_form"].is_valid():
                uploaded_file = context["import_upload_form"].cleaned_data["file"]
                return self.do_import(uploaded_file)
        elif action == "export":
            return self.do_export()
        elif can_delete and action == "delete":
            return self.do_delete()

        return self.render_to_response(context)
