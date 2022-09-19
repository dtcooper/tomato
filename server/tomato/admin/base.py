from django.contrib import admin, messages


class NoNullRelatedOnlyFieldListFilter(admin.RelatedOnlyFieldListFilter):
    include_empty_choice = False


class ListPrefetchRelatedMixin:
    list_prefetch_related = None

    def get_queryset(self, request):
        # For performance https://code.djangoproject.com/ticket/29985#comment:3
        queryset = super().get_queryset(request)
        if self.list_prefetch_related and request.resolver_match.view_name.endswith("changelist"):
            queryset = queryset.prefetch_related(self.list_prefetch_related)
        return queryset


class TomatoModelAdminBase(ListPrefetchRelatedMixin, admin.ModelAdmin):
    save_on_top = True
    exclude = ("created_by",)  # XXX should be excluded by modeladmin directly

    @admin.action(description="Enable selected %(verbose_name_plural)s", permissions=("add", "change", "delete"))
    def enable(self, request, queryset):
        num = queryset.update(enabled=True)
        if num:
            self.message_user(request, f"Enabled {num} {self.model._meta.verbose_name}(s).", messages.SUCCESS)

    @admin.action(description="Disable selected %(verbose_name_plural)s", permissions=("add", "change", "delete"))
    def disable(self, request, queryset):
        num = queryset.update(enabled=False)
        if num:
            self.message_user(request, f"Disabled {num} {self.model._meta.verbose_name}(s).", messages.SUCCESS)

    def has_view_permission(self, request, obj=None):
        return True

    def has_module_permission(self, request):
        return True

    def save_model(self, request, obj, form, change):
        if not change and hasattr(obj, "created_by"):
            obj.created_by = request.user
        return super().save_model(request, obj, form, change)
