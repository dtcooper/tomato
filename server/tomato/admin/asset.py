import urllib.parse

from django import forms
from django.contrib import admin, messages
from django.contrib.admin.helpers import ActionForm
from django.contrib.admin.widgets import FilteredSelectMultiple, RelatedFieldWidgetWrapper
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

from django_file_form.forms import FileFormMixin, MultipleUploadedFileField
from django_file_form.model_admin import FileFormAdminMixin

from ..models import Asset, AssetAlternate, Rotator
from ..tasks import bulk_process_assets, process_asset
from ..utils import mark_models_dirty
from .base import NO_ICON, YES_ICON, AiringFilter, AiringMixin, NoNullRelatedOnlyFieldFilter, TomatoModelAdminBase


class AssetActionForm(ActionForm):
    rotator = forms.ModelChoiceField(Rotator.objects.all(), required=False, label=" ", empty_label="--- Rotator ---")


class AssetUploadForm(FileFormMixin, forms.Form):
    files = MultipleUploadedFileField(
        label="Audio files",
        help_text="Select one or more files to be uploaded as audio assets.",
    )
    rotators = forms.ModelMultipleChoiceField(
        queryset=Rotator.objects.all(),
        required=False,
        help_text="Rotators that the newly uploaded asset will be included in.",
        widget=FilteredSelectMultiple("rotators", False),
    )

    def __init__(self, request, admin_site, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["rotators"].widget = RelatedFieldWidgetWrapper(
            self.fields["rotators"].widget,
            Asset._meta.get_field("rotators").remote_field,
            admin_site,
            can_add_related=request.user.has_perm("tomato.add_rotator"),
        )


class StatusFilter(admin.SimpleListFilter):
    title = "status"
    parameter_name = "status"

    def lookups(self, request, model_admin):
        return (("ready", "Ready"), ("processing", "Processing"))

    def queryset(self, request, queryset):
        value = self.value()
        if value == "ready":
            return queryset.filter(status=Asset.Status.READY)
        elif value == "processing":
            return queryset.exclude(status=Asset.Status.READY)


class AssetAdminBase(FileFormAdminMixin, TomatoModelAdminBase):
    ADDITIONAL_INFO_FIELDSET = ("Additional information", {"fields": ("created_at", "created_by")})

    readonly_fields = ("duration", "file_display", "filename_display") + TomatoModelAdminBase.readonly_fields

    @admin.display(description="Play")
    def list_player(self, obj):
        objs = [obj]
        if isinstance(obj, Asset):
            objs.extend(obj.alternates.all())
        objs = list(filter(lambda o: o.file and o.status == o.Status.READY, objs))

        if objs:
            html = mark_safe('<div style="text-align: center; width: max-content; display: flex; gap: 3px;">')
            for obj in objs:
                html += format_html(
                    '<a class="play-asset-list-display" href="{}">&#x25B6;&#xFE0F;</a>',
                    obj.file.url,
                )
            return html + mark_safe("</div>")
        else:
            return ""

    @staticmethod
    def _get_player_html(obj):
        return format_html(
            '<audio src="{}" style="height: 45px; width: 450px; max-width: 100%" controlslist="noplaybackrate"'
            ' preload="auto" controls />',
            obj.file.url,
        )

    @admin.display(description="Player")
    def file_display(self, obj):
        if isinstance(obj, AssetAlternate) or not obj.alternates.exists():
            return self._get_player_html(obj)
        else:
            objs = [obj]
            objs.extend(obj.alternates.all())

            html = mark_safe("<table><thead><th>File</th><th>Audio</th</thead><tbody>")
            for n, obj in enumerate(objs):
                html += format_html(
                    '<tr><td style="vertical-align: middle;">{}</td><td>', "Primary" if n == 0 else f"Alternate #{n}"
                )
                if obj.file and obj.status == obj.Status.READY:
                    html += self._get_player_html(obj)
                else:
                    html += mark_safe("<em>Being processed...</em>")
                html += mark_safe("</td></tr>")
            return html + mark_safe("</tbody></table>")

    @admin.display(description="Filename")
    def filename_display(self, obj):
        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            reverse(f"admin:tomato_{self.model._meta.model_name}_download", args=(obj.id,)),
            obj.filename,
        )

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = self.readonly_fields
        if obj is not None and obj.status != Asset.Status.READY:
            readonly_fields += ("file",)
        return readonly_fields

    def save_model(self, request, obj, form, change):
        should_process = "file" in obj.get_dirty_fields()
        if should_process:
            obj.status = Asset.Status.PENDING

        empty_name = False
        if isinstance(obj, Asset):
            empty_name = obj.name.strip()

        super().save_model(request, obj, form, change)

        if should_process:
            process_asset(obj, empty_name=empty_name, user=request.user)
            self.message_user(
                request,
                f'{obj._meta.verbose_name.capitalize()} "{obj.name}" is being processed. A message will appear when it'
                " is ready. Refresh this page and you can edit it at that time.",
                messages.WARNING,
            )

    def download_view(self, request, asset_id):
        if not self.has_view_permission(request):
            raise PermissionDenied

        asset = get_object_or_404(self.model, id=asset_id)

        # Use fancy feature of nginx to provide content disposition headers
        response = HttpResponse()
        response["X-Accel-Redirect"] = asset.file.url
        response["Content-Disposition"] = f"attachment; filename*=utf-8''{urllib.parse.quote(asset.filename)}"
        return response

    def get_urls(self):
        return [
            path(
                "<asset_id>/download/",
                self.admin_site.admin_view(self.download_view),
                name=f"tomato_{self.model._meta.model_name}_download",
            ),
        ] + super().get_urls()


class AssetAdmin(AiringMixin, AssetAdminBase):
    ROTATORS_FIELDSET = ("Rotators", {"fields": ("rotators",)})
    NAME_AIRING_FIELDSET = (None, {"fields": ("name", "airing")})

    add_fieldsets = (
        (None, {"fields": ("name",)}),
        ("Audio file", {"fields": ("file",)}),
        ROTATORS_FIELDSET,
        AiringMixin.AIRING_INFO_FIELDSET,
    )
    action_form = AssetActionForm
    actions = (
        "enable",
        "disable",
        "add_rotator",
        "remove_rotator",
        "delete_selected",
    )
    fieldsets = (
        NAME_AIRING_FIELDSET,
        ("Audio file", {"fields": ("file", "filename_display", "file_display", "duration", "alternates_display")}),
        ROTATORS_FIELDSET,
        AiringMixin.AIRING_INFO_FIELDSET,
        AssetAdminBase.ADDITIONAL_INFO_FIELDSET,
    )
    filter_horizontal = ("rotators",)
    field_to_highlight = "name"
    list_display = (
        "list_player",
        "name",
        "airing",
        "air_date",
        "weight",
        "duration",
        "rotators_display",
        "created_at",
    )
    list_display_links = ("name",)
    list_filter = (
        AiringFilter,
        "rotators",
        "enabled",
        StatusFilter,
        ("created_by", NoNullRelatedOnlyFieldFilter),
    )
    list_prefetch_related = ("rotators",)
    search_fields = ("name", "original_filename")
    no_change_fieldsets = (
        NAME_AIRING_FIELDSET,
        ("Audio file", {"fields": ("filename_display", "file_display", "duration", "alternates_display_readonly")}),
        ("Rotators", {"fields": ("rotators_display",)}),
        AiringMixin.AIRING_INFO_FIELDSET,
        AssetAdminBase.ADDITIONAL_INFO_FIELDSET,
    )
    readonly_fields = ("airing", "alternates_display", "rotators_display") + AssetAdminBase.readonly_fields

    @admin.display(description="Rotator(s)")
    def rotators_display(self, obj):
        html = mark_safe("")
        for url, content_color, color, enabled, name in (
            (
                reverse("admin:tomato_rotator_change", args=(r.id,)),
                r.get_color(content=True),
                r.get_color(),
                r.enabled,
                r.name,
            )
            for r in obj.rotators.all()
        ):
            html = html + format_html(
                '<div style="padding: 2px 0">&#x25cf; <a href="{}" style="color: {}; background-color: {};">',
                url,
                content_color,
                color,
            )
            if not enabled:
                html = html + format_html('<span style="text-decoration: line-through">{}</span></a> (disabled)', name)
            else:
                html = html + format_html("{}</a>", name)
            html = html + mark_safe("</div>")

        if not html:
            return mark_safe('<span style="color: red"><strong>WARNING:</strong> not in any rotators</span>')
        return html

    @admin.display(description="Alternate file(s)")
    def alternates_display(self, obj, readonly=False):
        alternates = list(obj.alternates.all())
        html = mark_safe("")
        if alternates:
            files = format_html_join(
                "\n",
                '<li><a href="{}">{}</a></li>',
                ((reverse("admin:tomato_assetalternate_change", args=(alt.id,)), alt.name) for alt in alternates),
            )
            html += format_html('<ol style="padding-inline-start: 0;">\n{}\n</ol>\n', files)
        if readonly:
            return html or mark_safe("<em>None</em>")
        else:
            return html + format_html(
                '<a href="{}?asset_id={}" class="addlink">Add new alternate file</a>',
                reverse("admin:tomato_assetalternate_add"),
                obj.id,
            )

    @admin.display(description="Alternate file(s)")
    def alternates_display_readonly(self, obj):
        return self.alternates_display(obj, readonly=True)

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
            mark_models_dirty(request)
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
            mark_models_dirty(request)
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
                        asset.full_clean(exclude={"original_filename"})
                    except forms.ValidationError as validation_error:
                        for field, error_list in validation_error:
                            for error in error_list:
                                form.add_error(
                                    "files" if field == "file" else "__all__", format_html("{}: {}", audio_file, error)
                                )

            # If no errors where added
            if form.is_valid():
                for asset in assets:
                    asset.save()
                    if rotators:
                        asset.rotators.add(*rotators)
                mark_models_dirty(request)
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
            path("upload/", self.admin_site.admin_view(self.upload_view), name="tomato_asset_upload"),
        ] + super().get_urls()


class AssetAlternateAdmin(AssetAdminBase):
    ASSET_STATUS_FIELDSET = (None, {"fields": ("asset", "status_display")})

    add_fieldsets = ((None, {"fields": ("asset",)}), ("Audio file", {"fields": ("file",)}))
    fieldsets = (
        ASSET_STATUS_FIELDSET,
        ("Audio file", {"fields": ("file", "filename_display", "file_display", "duration")}),
        AssetAdminBase.ADDITIONAL_INFO_FIELDSET,
    )
    list_display = ("list_player", "name", "status_display", "duration", "created_at", "asset_display")
    list_display_links = ("name",)
    list_filter = (StatusFilter, ("created_by", NoNullRelatedOnlyFieldFilter))
    list_prefetch_related = ("asset",)
    no_change_fieldsets = (
        ASSET_STATUS_FIELDSET,
        ("Audio file", {"fields": ("filename_display", "file_display", "duration")}),
        AssetAdminBase.ADDITIONAL_INFO_FIELDSET,
    )
    ordering = ("asset__created_at", "asset__id", "id")
    readonly_fields = ("status_display",) + AssetAdminBase.readonly_fields
    search_fields = ("asset__name", "original_filename")

    @admin.display(description="Status", ordering="status")
    def status_display(self, obj):
        if obj.status == obj.Status.READY:
            return format_html('<img src="{}">', YES_ICON)
        else:
            return format_html('<img src="{}"> {}', NO_ICON, "Processing")

    @admin.display(description=AssetAlternate._meta.get_field("asset").verbose_name, ordering="asset__name")
    def asset_display(self, obj):
        return format_html(
            '<a href="{}">{}</a>', reverse("admin:tomato_asset_change", args=(obj.asset.id,)), obj.asset.name
        )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return AssetAlternate.annotate_queryset_with_num_before(qs)

    def get_changeform_initial_data(self, request):
        form_data = super().get_changeform_initial_data(request)
        asset_id = request.GET.get("asset_id")
        if asset_id is not None:
            form_data["asset"] = asset_id
        return form_data

    def formfield_for_dbfield(self, *args, **kwargs):
        formfield = super().formfield_for_dbfield(*args, **kwargs)
        formfield.widget.can_delete_related = False
        formfield.widget.can_change_related = False
        formfield.widget.can_add_related = False
        formfield.widget.can_view_related = False
        return formfield
