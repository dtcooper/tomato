from django.contrib import admin


class ClientLogEntryAdmin(admin.ModelAdmin):
    save_on_top = True

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return False
