from django.contrib import admin
from django.contrib.auth.models import Group

from constance.admin import Config as Constance

from ..models import Asset, Rotator, StopSet, User
from .asset import AssetAdmin
from .constance import ConstanceAdmin
from .rotator import RotatorAdmin
from .stopset import StopSetAdmin
from .user import UserAdmin


admin.site.unregister([Constance])
admin.site.register([Constance], ConstanceAdmin)
admin.site.unregister(Group)
admin.site.register(User, UserAdmin)
admin.site.register(Rotator, RotatorAdmin)
admin.site.register(Asset, AssetAdmin)
admin.site.register(StopSet, StopSetAdmin)
