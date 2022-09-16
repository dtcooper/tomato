from django.contrib import admin

from ..models import StopsetRotator
from .base import TomatoModelAdminBase


class StopsetRotatorInline(admin.TabularInline):
    save_on_top = True
    min_num = 1
    extra = 0
    model = StopsetRotator
    verbose_name = "rotator entry"
    verbose_name_plural = "rotator entries"


class StopsetAdmin(TomatoModelAdminBase):
    inlines = (StopsetRotatorInline,)
