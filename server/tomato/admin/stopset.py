from django.contrib import admin

from ..models import StopSetRotator


class StopSetRotatorInline(admin.TabularInline):
    min_num = 1
    extra = 0
    model = StopSetRotator
    verbose_name = "rotator entry"
    verbose_name_plural = "rotator entries"


class StopSetAdmin(admin.ModelAdmin):
    inlines = (StopSetRotatorInline,)
