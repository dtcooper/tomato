from django.contrib import admin
from django.db.models import Prefetch
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe

from ..models import Stopset
from .base import TomatoModelAdminBase


class RotatorAdmin(TomatoModelAdminBase):
    list_display = ("name", "color", "stopsets_display")
    list_prefetch_related = Prefetch("stopsets", queryset=Stopset.objects.distinct())
    search_fields = ("name",)
    fields = ("name", "color", "stopsets_display")
    readonly_fields = ("stopsets_display",)

    @admin.display(description="Stop sets")
    def stopsets_display(self, obj):
        # TODO on change view (not changelist) this doesn't display right
        stopsets = [(r.name,) for r in obj.stopsets.all()]
        return format_html_join(mark_safe("<br>\n"), "&#x25cf; {}", stopsets) or None
