from django.contrib import admin
from django.db.models import Prefetch
from django.urls import reverse
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe

from ..models import Rotator, StopsetRotator
from .base import TomatoModelAdminBase


class StopsetRotatorInline(admin.TabularInline):
    save_on_top = True
    min_num = 1
    extra = 0
    model = StopsetRotator
    verbose_name = "rotator entry in this stop set"
    verbose_name_plural = "rotator entries in this stop set"
    can_delete = True
    show_change_link = True

    def get_formset(self, request, obj, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        widget = formset.form.base_fields["rotator"].widget
        widget.can_delete_related = False
        widget.can_view_related = False
        return formset


class StopsetAdmin(TomatoModelAdminBase):
    list_display = ("name", "enabled", "airing", "air_date", "weight", "rotators_display")
    actions = ("enable", "disable")
    list_prefetch_related = Prefetch("rotators", queryset=Rotator.objects.order_by("stopsetrotator__id"))
    inlines = (StopsetRotatorInline,)
    list_filter = ("enabled",)

    @admin.display(description="Rotators")
    def rotators_display(self, obj):
        rotators = [
            (i, reverse("admin:tomato_rotator_change", args=(r.id,)), r.get_color("dark"), r.name)
            for i, r in enumerate(obj.rotators.all(), 1)
        ]
        return format_html_join(mark_safe("<br>\n"), '{}. <a href="{}" style="color: {}">{}</a>', rotators) or None
