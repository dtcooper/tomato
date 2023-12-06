import csv

from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.urls import path
from django.utils.safestring import mark_safe
from django.utils.timezone import localtime

from ..models import ClientLogEntry
from .base import ListPrefetchRelatedMixin, format_datetime


class CSVBuffer:
    def write(self, value):
        return value


class ClientLogEntryAdmin(ListPrefetchRelatedMixin, admin.ModelAdmin):
    actions = ("csv",)
    date_hierarchy = "created_at"
    empty_value_display = mark_safe("Unknown / deleted")
    fields = ("id", "created_at_display", "category", "type", "created_by", "ip_address", "description_display")
    list_display = ("created_at_display", "category", "type", "created_by", "ip_address", "description_display")
    list_filter = ("created_by", "type")
    list_max_show_all = 2500
    list_per_page = 250
    list_prefetch_related = ("created_by",)
    readonly_fields = ("created_at_display", "category", "description_display")
    save_on_top = True
    search_fields = ("description",)
    show_facets = admin.ShowFacets.ALWAYS

    @admin.display(ordering="-created_at", description="Created at")
    def created_at_display(self, obj):
        return format_datetime(obj.created_at, "M j Y, g:i:s A")

    @admin.display(ordering="description", description="Description")
    def description_display(self, obj):
        return obj.description.strip() or mark_safe("<em>None</em>")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return False

    @admin.action(description=f"Export selected {ClientLogEntry._meta.verbose_name_plural} as CSV")
    def csv(self, request, queryset):
        filename = f"tomato-client-log-entries-{localtime().strftime('%Y%M%S%H%M%S')}.csv"
        response = HttpResponse(
            content_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

        writer = csv.writer(response, quoting=csv.QUOTE_ALL)
        writer.writerow(("ID", "Created At", "Category", "Type", "Created By", "Description"))

        for entry in queryset.order_by("created_at").prefetch_related("created_by"):
            writer.writerow(
                (
                    str(entry.id),
                    localtime(entry.created_at).strftime("%Y/%m/%d %H:%M:%S"),
                    entry.category(),
                    entry.type,
                    "unknown/deleted" if entry.created_by is None else entry.created_by.username,
                    entry.description,
                )
            )

        return response

    def csv_view(self, request):
        if not self.has_view_permission(request):
            raise PermissionDenied

        return self.csv(request, ClientLogEntry.objects.all())

    def get_urls(self):
        return [
            path("csv/", self.admin_site.admin_view(self.csv_view), name="tomato_clientlogentry_csv"),
        ] + super().get_urls()
