from django import forms
from django.contrib import admin, messages
from django.contrib.admin.helpers import AdminForm
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe

from constance.admin import Config as Constance
from constance.admin import ConstanceAdmin as BaseConstanceAdmin

from .models import Asset, Rotator, User


STRFTIME_FMT = "%a %b %-d %Y %-I:%M %p"


class ConstanceAdmin(BaseConstanceAdmin):
    def has_module_permission(self, request):
        return True

    def has_view_permission(self, request, obj=None):
        return True


Constance._meta.verbose_name = Constance._meta.verbose_name_plural = "configuration"


class UserAdmin(UserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        ("Permissions", {"fields": ("is_active", "is_superuser", "groups")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    readonly_fields = ("last_login", "date_joined")
    list_display = ("username", "email", "is_active", "groups_display")
    list_filter = ("is_superuser", "is_active", "groups")

    @admin.display(description="Groups")
    def groups_display(self, instance):
        if instance.is_superuser:
            return mark_safe("<strong><em>All groups!</em></strong> (Superuser)")
        else:
            groups_html = format_html_join("\n", mark_safe("<li>{}</li>"), instance.groups.values_list("name"))
            return mark_safe(f"<ul>\n{groups_html}</ul>") if groups_html else None


class AssetUploadForm(forms.Form):
    files = forms.FileField(
        widget=forms.ClearableFileInput(attrs={"multiple": True}),
        required=True,
        label="Audio file(s)",
        help_text=f"Select multiple files to be uploaded as {Asset._meta.verbose_name_plural }.",
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
            )


class RotatorAdmin(admin.ModelAdmin):
    exclude = ("uuid",)  # XXX


class AssetAdmin(admin.ModelAdmin):
    exclude = ("uuid",)  # XXX
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
                    asset = Asset(file=audio_file)
                    assets.append(asset)

                    try:
                        asset.full_clean()
                    except forms.ValidationError as validation_error:
                        for field, error_list in validation_error:
                            for error in error_list:
                                form.add_error("files" if field == "file" else "__all__", error)

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


admin.site.unregister(Group)
admin.site.unregister([Constance])
admin.site.register([Constance], ConstanceAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(Rotator, RotatorAdmin)
admin.site.register(Asset, AssetAdmin)
