from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe


class UserAdmin(DjangoUserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Permissions", {"fields": ("is_active", "is_superuser", "groups")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    readonly_fields = ("last_login", "date_joined")
    list_display = ("username", "is_active", "groups_display")
    list_filter = ("is_superuser", "is_active", "groups")

    @admin.display(description="Groups")
    def groups_display(self, instance):
        if instance.is_superuser:
            return mark_safe("<strong>Administrator</strong> (all groups)")
        else:
            groups = instance.groups.order_by("name").values_list("name")
            groups_html = format_html_join("\n", mark_safe("<li>{}</li>"), groups)
            return mark_safe(f'<ul style="margin-left: 0">\n{groups_html}</ul>') if groups_html else None
