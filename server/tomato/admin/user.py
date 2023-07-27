from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import AdminPasswordChangeForm as DjangoAdminPasswordChangeForm
from django.contrib.auth.models import Group
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe

from ..constants import EDIT_ALL_GROUP_NAME, EDIT_ONLY_ASSETS_GROUP_NAME
from ..utils import mark_logged_out_users
from .base import ListPrefetchRelatedMixin, NoNullRelatedOnlyFieldFilter


class AdminPasswordChangeForm(DjangoAdminPasswordChangeForm):
    def save(self, commit=True):
        user = super().save(commit=commit)
        mark_logged_out_users([user.id])
        return user


class UserAdmin(ListPrefetchRelatedMixin, DjangoUserAdmin):
    add_fieldsets = (
        (None, {"fields": ("username", "password1", "password2")}),
        ("Permissions", {"fields": ("is_superuser", "enable_client_logs", "groups")}),
    )
    add_form_template = None  # Removed the top of page warning
    change_password_form = AdminPasswordChangeForm
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Permissions", {"fields": ("is_active", "is_superuser", "enable_client_logs", "groups")}),
        ("Additional information", {"fields": ("last_login", "created_at", "created_by")}),
    )
    filter_horizontal = ("groups",)
    list_display = ("username", "is_active", "groups_display", "enable_client_logs")
    list_filter = ("is_superuser", "is_active", "groups", ("created_by", NoNullRelatedOnlyFieldFilter), "enable_client_logs")
    list_prefetch_related = ("groups",)
    readonly_fields = ("last_login", "created_at", "created_by")
    save_on_top = True
    search_fields = ("username",)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not obj.is_active:
            mark_logged_out_users([obj.id])

    def delete_model(self, request, obj):
        user_id = obj.id
        super().delete_model(request, obj)
        mark_logged_out_users([user_id])

    def delete_queryset(self, request, queryset):
        user_ids = list(queryset.values_list("id", flat=True))
        super().delete_queryset(request, queryset)
        mark_logged_out_users(user_ids)

    @admin.display(description="Permissions")
    def groups_display(self, obj):
        if obj.is_superuser:
            return mark_safe("<strong>Administrator</strong> (all permissions)")
        else:
            groups = [(group.name,) for group in obj.groups.all()]
            return format_html_join(mark_safe("<br>\n"), "&#x25cf; {}", groups) or None

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        user = form.instance

        user_groups = set(user.groups.values_list("name", flat=True))
        edit_groups = {EDIT_ALL_GROUP_NAME, EDIT_ONLY_ASSETS_GROUP_NAME}

        if edit_groups.issubset(user_groups):
            user.groups.remove(Group.objects.get(name=EDIT_ONLY_ASSETS_GROUP_NAME))
            self.message_user(
                request,
                mark_safe(
                    f'Removing redundant <em>"{EDIT_ONLY_ASSETS_GROUP_NAME}"</em> from user {user.username}\'s groups'
                ),
                level=messages.WARNING,
            )
