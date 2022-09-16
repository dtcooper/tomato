from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe


class UserAdmin(DjangoUserAdmin):
    save_on_top = True
    add_form_template = None  # Removed the top of page warning
    readonly_fields = ("last_login", "date_joined")
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Permissions", {"fields": ("is_active", "is_superuser", "groups")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"fields": ("username", "password1", "password2")}),
        ("Permissions", {"fields": ("is_superuser", "groups")}),
    )
    list_display = ("username", "is_active", "groups_display")
    list_filter = ("is_superuser", "is_active", "groups")
    search_fields = ("username",)
    filter_horizontal = ("groups",)

    @admin.display(description="Permissions")
    def groups_display(self, instance):
        if instance.is_superuser:
            return mark_safe("<strong>Administrator</strong> (all permissions)")
        else:
            groups = instance.groups.order_by("name").values_list("name")
            return format_html_join(mark_safe("<br>\n"), "&#x25cf; {}", groups) or None
