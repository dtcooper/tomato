from django import forms
from django.contrib import messages
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path

from ..models import Asset, Rotator
from .base import TomatoModelAdminBase


class AssetUploadForm(forms.Form):
    files = forms.FileField(
        widget=forms.ClearableFileInput(attrs={"multiple": True}),
        required=True,
        label="Audio file(s)",
        help_text=f"Select multiple files to be uploaded as {Asset._meta.verbose_name_plural}.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if Rotator.objects.exists():
            self.fields["rotators"] = forms.ModelMultipleChoiceField(
                Rotator.objects.all(),
                required=False,
                help_text=(
                    'Optionally select rotator(s) to add the newly uploaded audio assets to. Hold down "Control", or'
                    ' "Command" on a Mac, to select more than one.'
                ),
                widget=FilteredSelectMultiple("test", False),
            )


class AssetAdmin(TomatoModelAdminBase):
    readonly_fields = ("duration", "created_at", "status")
    filter_horizontal = ("rotators",)

    def upload_view(self, request):
        if not self.has_add_permission(request):
            raise PermissionDenied

        opts = self.model._meta

        if request.method == "POST":
            form = AssetUploadForm(request.POST, request.FILES)
            if form.is_valid():
                files = request.FILES.getlist("files")
                rotators = form.cleaned_data.get("rotators")
                assets = []

                for audio_file in files:
                    asset = Asset(file=audio_file, created_by=request.user)
                    assets.append(asset)

                    try:
                        asset.full_clean()
                    except forms.ValidationError as validation_error:
                        for field, error_list in validation_error:
                            for error in error_list:
                                form.add_error("files" if field == "file" else "__all__", f"{audio_file}: {error}")

            # If no errors where added
            if form.is_valid():
                for asset in assets:
                    asset.save()

                    if rotators:
                        asset.rotators.add(*rotators)

                self.message_user(request, f"Uploaded {len(assets)} {opts.verbose_name_plural}.", messages.SUCCESS)

                return redirect("admin:tomato_asset_changelist")
        else:
            form = AssetUploadForm()

        return TemplateResponse(
            request,
            "admin/tomato/asset/upload.html",
            {
                "app_label": opts.app_label,
                "form": form,
                "opts": opts,
                "title": f"Bulk upload {opts.verbose_name_plural}",
                **self.admin_site.each_context(request),
            },
        )

    def get_urls(self):
        return [
            path(r"upload/", self.admin_site.admin_view(self.upload_view), name="tomato_asset_upload")
        ] + super().get_urls()
