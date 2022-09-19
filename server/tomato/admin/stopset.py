from django.contrib import admin
from django.db.models import Prefetch
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
    list_display = ("name", "rotators_display")
    list_prefetch_related = Prefetch("rotators", queryset=Rotator.objects.order_by("stopsetrotator__id"))
    inlines = (StopsetRotatorInline,)

    @admin.display(description="Rotators")
    def rotators_display(self, obj):
        rotators = [(i, r.name) for i, r in enumerate(obj.rotators.all(), 1)]
        return format_html_join(mark_safe("<br>\n"), "{}. {}", rotators) or None
