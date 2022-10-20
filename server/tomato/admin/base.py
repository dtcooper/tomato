from django.contrib import admin, messages
from django.template.defaultfilters import pluralize
from django.templatetags.static import static
from django.utils import timezone
from django.utils.formats import date_format as django_date_format
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

from ..models import Asset, Stopset


YES_ICON = static("admin/img/icon-yes.svg")
NO_ICON = static("admin/img/icon-no.svg")


def format_datetime(dt, format="SHORT_DATETIME_FORMAT"):
    return django_date_format(timezone.localtime(dt), format)


class NoNullRelatedOnlyFieldFilter(admin.RelatedOnlyFieldListFilter):
    include_empty_choice = False


class AiringFilter(admin.SimpleListFilter):
    title = "airing"
    parameter_name = "airing"

    def lookups(self, request, model_admin):
        return (
            ("eligible", "Eligible to air"),
            ("not-eligible", "Not eligible to air"),
        )

    def queryset(self, request, queryset):
        if self.value() == "eligible":
            return queryset.eligible_to_air()
        if self.value() == "not-eligible":
            return queryset.not_eligible_to_air()


class ListPrefetchRelatedMixin:
    list_prefetch_related = None

    def get_queryset(self, request):
        # For performance https://code.djangoproject.com/ticket/29985#comment:3
        queryset = super().get_queryset(request)
        if self.list_prefetch_related and request.resolver_match.view_name.endswith("changelist"):
            queryset = queryset.prefetch_related(self.list_prefetch_related)
        return queryset


class SaveCreatedByMixin:
    def save_model(self, request, obj, form, change):
        if not change and hasattr(obj, "created_by"):
            obj.created_by = request.user
        return super().save_model(request, obj, form, change)


class AiringMixin:
    AIRING_INFO_FIELDSET = ("Airing Information", {"fields": ("enabled", "weight", "begin", "end")})

    @admin.display(description="Air date")
    def air_date(self, obj):
        if obj.begin and obj.end:
            return f"{format_datetime(obj.begin)} to {format_datetime(obj.end)}"
        elif obj.begin:
            return format_html("<strong>Starts</strong> at {}", format_datetime(obj.begin))
        elif obj.end:
            return format_html("<strong>Ends</strong> on {}", format_datetime(obj.begin))
        else:
            return "Can air any time"

    @admin.display(description="Eligible to air")
    def airing(self, obj):
        eligible, reason = obj.is_eligible_to_air(with_reason=True)
        if eligible:
            return format_html('<img src="{}">', YES_ICON)
        else:
            return format_html('<img src="{}"> {}', NO_ICON, reason)

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


class NumAssetsMixin:
    @admin.display(description="Assets")
    def num_assets(self, obj):
        if isinstance(obj, Stopset):
            assets = Asset.objects.filter(rotators__in=obj.rotators.distinct().values_list("id", flat=True))
        else:
            assets = Asset.objects.filter(rotators=obj.id)

        display = []
        total = assets.count()
        num_eligible = assets.eligible_to_air().count()
        num_not_eligible = total - num_eligible

        if num_eligible:
            display.append((f"{num_eligible} eligible to air",))
        if num_not_eligible:
            display.append((f"{num_not_eligible} not eligible to air",))
        display.append((format_html("<strong>{} asset{} total</strong>", total, pluralize(total)),))
        return format_html_join(mark_safe("<br>\n"), "&#x25cf; {}", display)


class TomatoModelAdminBase(ListPrefetchRelatedMixin, SaveCreatedByMixin, admin.ModelAdmin):
    add_fieldsets = None
    list_max_show_all = 2500
    list_per_page = 250
    readonly_fields = ("created_by", "created_at")
    save_on_top = True
    search_fields = ("name",)

    def get_fieldsets(self, request, obj=None):
        if obj is None and self.add_fieldsets is not None:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    def has_view_permission(self, request, obj=None):
        return True

    def has_module_permission(self, request):
        return True
