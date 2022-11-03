from django.contrib import admin
from django.db.models import Prefetch
from django.urls import reverse
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe

from ..models import Rotator, StopsetRotator
from .base import AiringFilter, AiringMixin, NoNullRelatedOnlyFieldFilter, NumAssetsMixin, TomatoModelAdminBase


class StopsetRotatorInline(admin.TabularInline):
    can_delete = True
    extra = 0
    min_num = 1
    model = StopsetRotator
    show_change_link = True
    verbose_name = "rotator entry in this stop set"
    verbose_name_plural = "rotator entries in this stop set"

    def get_formset(self, request, obj, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        widget = formset.form.base_fields["rotator"].widget
        widget.can_delete_related = False
        widget.can_view_related = False
        return formset


class StopsetAdmin(AiringMixin, NumAssetsMixin, TomatoModelAdminBase):
    actions = ("enable", "disable")
    add_fieldsets = (
        (None, {"fields": ("name",)}),
        AiringMixin.AIRING_INFO_FIELDSET,
    )
    fieldsets = (
        (None, {"fields": ("name", "airing")}),
        AiringMixin.AIRING_INFO_FIELDSET,
        ("Additional information", {"fields": ("num_assets", "created_by", "created_at")}),
    )
    inlines = (StopsetRotatorInline,)
    list_display = ("name", "airing", "air_date", "weight", "rotators_display", "num_assets")
    list_filter = (AiringFilter, "enabled", ("created_by", NoNullRelatedOnlyFieldFilter), "rotators")
    list_prefetch_related = Prefetch("rotators", queryset=Rotator.objects.order_by("stopsetrotator__id"))
    readonly_fields = ("num_assets", "rotators_display", "airing") + TomatoModelAdminBase.readonly_fields

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj is not None and not self.has_change_permission(request, obj):
            fieldsets += ((StopsetRotatorInline.verbose_name_plural.capitalize(), {"fields": ("rotators_display",)}),)
        return fieldsets

    @admin.display(description="Rotators")
    def rotators_display(self, obj):
        rotators = [
            (i, reverse("admin:tomato_rotator_change", args=(r.id,)), r.get_color(content=True), r.get_color(), r.name)
            for i, r in enumerate(obj.rotators.all(), 1)
        ]
        return (
            format_html_join(
                mark_safe("<br>\n"),
                '{}. <a href="{}" style="padding: 1px 3px; color: {}; background-color: {}">{}</a>',
                rotators,
            )
            or None
        )
