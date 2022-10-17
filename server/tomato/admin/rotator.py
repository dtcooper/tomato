from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

from .base import NoNullRelatedOnlyFieldFilter, NumAssetsMixin, TomatoModelAdminBase


class RotatorAdmin(NumAssetsMixin, TomatoModelAdminBase):
    list_display = ("name", "color_display", "stopsets_display", "num_assets")
    list_prefetch_related = "stopsets"
    add_fieldsets = (
        (None, {"fields": ("name",)}),
        ("Color", {"fields": ("color", "color_preview")}),
    )
    fieldsets = add_fieldsets + (
        ("Stop sets", {"fields": ("stopsets_display",)}),
        ("Additional information", {"fields": ("num_assets", "created_by", "created_at")}),
    )
    # Average asset length?
    # Assets
    readonly_fields = ("stopsets_display", "color_preview", "num_assets") + TomatoModelAdminBase.readonly_fields
    list_filter = ("stopsets", ("created_by", NoNullRelatedOnlyFieldFilter))

    @admin.display(description="Color", ordering="color")
    def color_display(self, obj=None):
        return format_html('<span style="padding: 1px 3px; color: {}; background-color: {}">{}</span>', obj.get_color(content=True), obj.get_color(), obj.get_color_display())

    @admin.display(description="Color preview")
    def color_preview(self, obj):
        return format_html(
            '<div id="id_color_preview" style="width: 8em; height: 3em; border: 1px solid #333; display: inline-block;'
            ' background-color: {};"></div>',
            obj.get_color(),
        )

    @admin.display(description="Stop sets")
    def stopsets_display(self, obj):
        stopsets = sorted(set(obj.stopsets.all()), key=lambda s: s.name)  # Simulated distinct()
        return (
            format_html_join(
                mark_safe("<br>\n"),
                '&#x25cf; <a href="{}">{}</a>',
                [(reverse("admin:tomato_stopset_change", args=(s.id,)), s.name) for s in stopsets],
            )
            or None
        )
