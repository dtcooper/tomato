from django_admin_logs.admin import LogEntryAdmin

from django.contrib import admin
from django.contrib.admin.models import LogEntry


class ServerLogEntry(LogEntry):
    class Meta:
        proxy = True
        verbose_name = "admin log entry"
        verbose_name_plural = "admin logs"


class ServerLogEntryAdmin(LogEntryAdmin):
    show_facets = admin.ShowFacets.ALWAYS
    list_max_show_all = 5000
    list_per_page = 500
    save_on_top = True
