from django.contrib import admin

from ..admin import admin_site
from .models import Submission


class SubmissionAdmin(admin.ModelAdmin):
    def has_view_permission(self, request, obj=None):
        return True

    def has_module_permission(self, request):
        return True


admin_site.register(Submission, SubmissionAdmin)
