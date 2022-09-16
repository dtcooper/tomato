from django.contrib import admin


class TomatoModelAdminBase(admin.ModelAdmin):
    save_on_top = True
    exclude = ("created_by",)  # XXX should be excluded by model

    def has_view_permission(self, request, obj=None):
        return True

    def has_module_permission(self, request):
        return True

    def save_model(self, request, obj, form, change):
        if not change and hasattr(obj, "created_by"):
            obj.created_by = request.user
        return super().save_model(request, obj, form, change)
