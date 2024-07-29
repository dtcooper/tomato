from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

from .base import AiringEnabledMixin, NoNullRelatedOnlyFieldFilter, NumAssetsMixin, TomatoModelAdminBase


class RotatorAdmin(AiringEnabledMixin, NumAssetsMixin, TomatoModelAdminBase):
    actions = (
        "enable",
        "disable",
        "enable_single_play",
        "disable_single_play",
        "enable_evenly_cycle",
        "disable_evenly_cycle",
    )
    list_display = (
        "name",
        "enabled",
        "is_single_play",
        "evenly_cycle",
        "color_display",
        "stopsets_display",
        "num_assets",
    )
    list_prefetch_related = ("stopsets",)
    COLOR_FIELDSET = ("Color", {"fields": ("color", "color_preview")})
    add_fieldsets = (
        (None, {"fields": ("name", "is_single_play", "evenly_cycle")}),
        COLOR_FIELDSET,
    )
    fieldsets = (
        (None, {"fields": ("name",)}),
        ("Airing Information", {"fields": ("enabled", "is_single_play", "evenly_cycle")}),
        COLOR_FIELDSET,
        ("Stop sets", {"fields": ("stopsets_display",)}),
        ("Additional information", {"fields": ("num_assets", "created_by", "created_at")}),
    )
    # Average asset length?
    # Assets
    readonly_fields = ("stopsets_display", "color_preview", "num_assets") + TomatoModelAdminBase.readonly_fields
    list_filter = (
        "enabled",
        "stopsets",
        ("created_by", NoNullRelatedOnlyFieldFilter),
        "is_single_play",
        "evenly_cycle",
    )

    @admin.action(
        description="Enable single play for selected %(verbose_name_plural)s", permissions=("add", "change", "delete")
    )
    def enable_single_play(self, request, queryset):
        num = queryset.update(is_single_play=True)
        if num:
            self.message_user(
                request, f"Enabled single play for {num} {self.model._meta.verbose_name}(s) .", messages.SUCCESS
            )

    @admin.action(
        description="Disable single play for selected %(verbose_name_plural)s", permissions=("add", "change", "delete")
    )
    def disable_single_play(self, request, queryset):
        num = queryset.update(is_single_play=False)
        if num:
            self.message_user(
                request, f"Disabled single play for {num} {self.model._meta.verbose_name}(s).", messages.SUCCESS
            )

    @admin.action(
        description="Enable cycle evenly for selected %(verbose_name_plural)s", permissions=("add", "change", "delete")
    )
    def enable_evenly_cycle(self, request, queryset):
        num = queryset.update(evenly_cycle=True)
        if num:
            self.message_user(
                request, f"Enabled cycle evenly for {num} {self.model._meta.verbose_name}(s) .", messages.SUCCESS
            )

    @admin.action(
        description="Disable cycle evenly for selected %(verbose_name_plural)s", permissions=("add", "change", "delete")
    )
    def disable_evenly_cycle(self, request, queryset):
        num = queryset.update(evenly_cycle=False)
        if num:
            self.message_user(
                request, f"Disabled cycle evenly for {num} {self.model._meta.verbose_name}(s).", messages.SUCCESS
            )

    @admin.display(description="Color", ordering="color")
    def color_display(self, obj=None):
        return format_html(
            '<span style="padding: 1px 3px; color: {}; background-color: {}">{}</span>',
            obj.get_color(content=True),
            obj.get_color(),
            obj.get_color_display(),
        )

    @admin.display(description="Color preview")
    def color_preview(self, obj):
        return format_html(
            '<div id="id_color_preview" style="width: 8em; height: 3em; border: 1px solid #333; display:'
            ' inline-block; background-color: {};"></div>',
            obj.get_color(),
        )

    @admin.display(description="Stop sets")
    def stopsets_display(self, obj):
        stopsets = sorted(set(obj.stopsets.all()), key=lambda s: s.name)  # Simulated distinct()
        return format_html_join(
            mark_safe("<br>\n"),
            '&#x25cf; <a href="{}">{}</a>',
            [(reverse("admin:tomato_stopset_change", args=(s.id,)), s.name) for s in stopsets],
        ) or mark_safe('<span style="color: red"><strong>WARNING:</strong> not in any stop sets</span>')
