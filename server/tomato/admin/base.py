from django.contrib import admin, messages
from django.templatetags.static import static
from django.utils import timezone
from django.utils.formats import date_format as django_date_format
from django.utils.html import format_html


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


def format_datetime(dt, format="SHORT_DATETIME_FORMAT"):
    return django_date_format(timezone.localtime(dt), format)


class TomatoModelAdminBase(ListPrefetchRelatedMixin, admin.ModelAdmin):
    save_on_top = True
    search_fields = ("name",)
    exclude = ("created_by",)  # XXX should be excluded by modeladmin directly
    add_fields = None

    @admin.display(description="Air date")
    def air_date(self, obj):
        if obj.begin and obj.end:
            return f"{format_datetime(obj.begin)} to {format_datetime(obj.end)}"
        elif obj.begin:
            return format_html("<strong>Starts</strong> at {}", format_datetime(obj.begin))
        elif obj.end:
            return format_html("<strong>Ends</strong> on {}", format_datetime(obj.begin))
        else:
            return "Airs any time"

    @admin.display(description="Eligible to Air")
    def airing(self, obj):
        if not obj.enabled:
            return format_html('<img src="{}"> {}', static("admin/img/icon-no.svg"), "Not enabled")
        else:
            now = timezone.now()
            if obj.begin and obj.begin > now:
                return format_html('<img src="{}"> {}', static("admin/img/icon-no.svg"), "Before start air date")
            if obj.end and obj.end < now:
                return format_html('<img src="{}"> {}', static("admin/img/icon-no.svg"), "After end air date")
        return format_html('<img src="{}">', static("admin/img/icon-yes.svg"))

    def get_fields(self, request, obj=None):
        if obj is None and self.add_fields is not None:
            return self.add_fields
        return super().get_fields(request, obj)

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
