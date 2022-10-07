from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

from .base import NoNullRelatedOnlyFieldListFilter, TomatoModelAdminBase


class RotatorAdmin(TomatoModelAdminBase):
    list_display = ("name", "color_display", "stopsets_display", "created_by")
    list_prefetch_related = "stopsets"
    add_fields = ("name", "color", "color_preview")
    # Average asset length?
    # Assets
    fields = ("name", "color", "color_preview", "stopsets_display")
    readonly_fields = ("stopsets_display", "color_preview")
    list_filter = ("stopsets", ("created_by", NoNullRelatedOnlyFieldListFilter))

    @admin.display(description="Color", ordering="color")
    def color_display(self, obj=None):
        return format_html('<span style="color: {}">{}</span>', obj.get_color("dark"), obj.get_color_display())

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
