from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from .models import TomatoUser


STRFTIME_FMT = '%a %b %-d %Y %-I:%M %p'


class TomatoUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_superuser', 'groups',)}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    readonly_fields = ("last_login", "date_joined")
    list_display = ('username', 'email', 'is_superuser')
    list_filter = ('is_superuser', 'is_active', 'groups')


#admin.site.unregister(TomatoUser)
admin.site.unregister(Group)
admin.site.register(TomatoUser, TomatoUserAdmin)
