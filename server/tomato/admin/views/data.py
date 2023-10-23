import tempfile
import logging

from django import forms
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import FormView

from django_file_form.forms import FileFormMixin, UploadedFileField

from ...models import ImportTomatoDataException, export_data_as_zip, import_data_from_zip
from .base import AdminViewMixin


logger = logging.getLogger(__name__)


class AdminDataForm(FileFormMixin, forms.Form):
    mode = forms.ChoiceField(choices=tuple((name, name) for name in ("import", "export")))
    file = UploadedFileField(required=False)


class AdminDataView(AdminViewMixin, FormView):
    form_class = AdminDataForm
    name = "data"
    perms = (
        'tomato.add_asset',
        'tomato.add_assetalternate',
        'tomato.add_rotator',
        'tomato.add_stopset',
        'tomato.add_stopsetrotator',
    )
    title = "Manage asset data"
    success_url = reverse_lazy("admin:extra_data")

    def form_invalid(self, form):
        print(form.errors)
        return super().form_invalid(form)

    def form_valid(self, form):
        mode = form.cleaned_data["mode"]
        zip_file = tempfile.NamedTemporaryFile("wb+")

        if mode == "export":
            zip_filename = export_data_as_zip(zip_file)
            zip_file.seek(0)
            response = HttpResponse(zip_file, content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
            return response
        
        elif mode == "import":
            file = form.cleaned_data["file"]
            try:
                import_data_from_zip(file, created_by=self.request.user)
            except ImportTomatoDataException as e:
                messages.add_message(self.request, messages.ERROR, f"Import error: {e}")
            except Exception as e:
                error_str = "Unexpected import error!"
                if settings.DEBUG:
                    error_str = f"{error_str} [Debug: {e}]"
                logger.exception("Unexpected import error!")
                messages.add_message(self.request, messages.ERROR, error_str)
            else:
                messages.add_message(self.request, messages.INFO, "Successfully imported!")

        return super().form_valid(form)
