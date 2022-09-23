from django import forms
from django.contrib import admin, messages
from django.contrib.admin.helpers import ActionForm
from django.contrib.admin.widgets import FilteredSelectMultiple, RelatedFieldWidgetWrapper
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

from django_file_form.forms import FileFormMixin, MultipleUploadedFileField
from django_file_form.model_admin import FileFormAdminMixin

from ..models import Asset, Rotator
from ..tasks import bulk_process_assets, process_asset
from .base import NoNullRelatedOnlyFieldListFilter, TomatoModelAdminBase


class AssetActionForm(ActionForm):
    rotator = forms.ModelChoiceField(Rotator.objects.all(), required=False, label=" ", empty_label="--- Rotator ---")


class AssetUploadForm(FileFormMixin, forms.Form):
    files = MultipleUploadedFileField(
        label="Audio files",
        help_text="Select one or more files to be uploaded as audio assets.",
    )
    rotators = forms.ModelMultipleChoiceField(
        Rotator.objects.all(), required=False, help_text="Rotators that the newly uploaded asset will be included in."
    )

    def __init__(self, request, admin_site, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["rotators"].widget = RelatedFieldWidgetWrapper(
            FilteredSelectMultiple("rotators", False),
            Asset._meta.get_field("rotators").remote_field,
            admin_site,
            can_add_related=request.user.has_perm("tomato.add_rotator"),
        )


class StatusFilter(admin.SimpleListFilter):
    title = "status"
    parameter_name = "status"

    def lookups(self, request, model_admin):
        return (("ready", "Ready to play"), ("processing", "Processing"))

    def queryset(self, request, queryset):
        value = self.value()
        if value == "ready":
            return queryset.filter(status=Asset.Status.READY)
        elif value == "processing":
            return queryset.exclude(status=Asset.Status.READY)


class AssetAdmin(FileFormAdminMixin, TomatoModelAdminBase):
    action_form = AssetActionForm
    actions = ("enable", "disable", "add_rotator", "remove_rotator")
    exclude = ()
    readonly_fields = ("duration", "created_at", "status", "created_by", "file_display")
    list_filter = ("enabled", "rotators", StatusFilter, ("created_by", NoNullRelatedOnlyFieldListFilter))
    list_per_page = 250
    filter_horizontal = ("rotators",)
    list_display = ("name", "status", "weight", "rotators_display", "created_by", "created_at")
    date_hierarchy = "created_at"
    list_prefetch_related = "rotators"

    @admin.display(description="Audio", empty_value="")
    def file_display(self, obj):
        if obj.file:
            return format_html(
                '<audio src="{}" style="height: 45px; width: 100%;" controlslist="nodownload noplaybackrate"'
                ' preload="auto" controls />',
                obj.file.url,
            )

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        if obj is not None and obj.status != Asset.Status.READY:
            readonly_fields.append("file")
        return readonly_fields

    def save_model(self, request, obj, form, change):
        should_process = "file" in obj.get_dirty_fields()
        if should_process:
            obj.status = Asset.Status.PENDING

        super().save_model(request, obj, form, change)

        if should_process:
            process_asset(obj, user=request.user)
            self.message_user(
                request,
                f'Audio asset "{obj.name}" is being processed. A message will appear when it is ready. Refresh this'
                " page and you can edit it at that time.",
                messages.WARNING,
            )

    @admin.display(description="Rotators")
    def rotators_display(self, obj):
        rotators = [(r.name,) for r in obj.rotators.all()]
        return format_html_join(mark_safe("<br>\n"), "&#x25cf; {}", rotators) or None

    @admin.action(description="Add selected audio assets to rotator", permissions=("add", "change", "delete"))
    def add_rotator(self, request, queryset):
        rotator_id = request.POST.get("rotator")
        if rotator_id:
            rotator = Rotator.objects.get(id=rotator_id)
            for asset in queryset:
                asset.rotators.add(rotator)
            self.message_user(
                request, f"Added {len(queryset)} audio assets to rotator {rotator.name}.", messages.SUCCESS
            )
        else:
            self.message_user(request, "You must select a rotator to add audio assets to.", messages.WARNING)

    @admin.action(description="Remove selected audio assets from rotator", permissions=("add", "change", "delete"))
    def remove_rotator(self, request, queryset):
        rotator_id = request.POST.get("rotator")
        if rotator_id:
            rotator = Rotator.objects.get(id=rotator_id)
            for asset in queryset:
                asset.rotators.remove(rotator)
            self.message_user(
                request, f"Removed {len(queryset)} audio assets from rotator {rotator.name}.", messages.SUCCESS
            )
        else:
            self.message_user(request, "You must select a rotator to remove audio assets from.", messages.WARNING)

    def upload_view(self, request):
        if not self.has_add_permission(request):
            raise PermissionDenied

        opts = self.model._meta

        if request.method == "POST":
            form = AssetUploadForm(request, self.admin_site, request.POST, request.FILES)
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
                bulk_process_assets(assets, user=request.user)

                form.delete_temporary_files()
                self.message_user(request, f"Uploaded {len(assets)} audio assets.", messages.SUCCESS)
                return redirect("admin:tomato_asset_changelist")

        else:
            form = AssetUploadForm(request, self.admin_site)

        return TemplateResponse(
            request,
            "admin/tomato/asset/upload.html",
            {
                "app_label": opts.app_label,
                "form": form,
                "opts": opts,
                "title": "Bulk upload audio assets",
                "media": self.media,
                **self.admin_site.each_context(request),
            },
        )

    def get_urls(self):
        return [
            path(r"upload/", self.admin_site.admin_view(self.upload_view), name="tomato_asset_upload")
        ] + super().get_urls()
