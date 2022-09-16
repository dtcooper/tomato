from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.safestring import mark_safe

from constance.admin import Config

from ..models import Asset, ClientLogEntry, Rotator, Stopset, User
from .asset import AssetAdmin
from .client_log_entry import ClientLogEntryAdmin
from .config import ConfigAdmin
from .rotator import RotatorAdmin
from .stopset import StopsetAdmin
from .user import UserAdmin


admin.site.site_url = None
admin.site.site_title = admin.site.site_header = "Tomato Administration"
admin.site.index_title = None
admin.site.empty_value_display = mark_safe("<em>None</em>")


admin.site.unregister(Group)
admin.site.unregister([Config])
admin.site.register(Asset, AssetAdmin)
admin.site.register(ClientLogEntry, ClientLogEntryAdmin)
admin.site.register([Config], ConfigAdmin)
admin.site.register(Rotator, RotatorAdmin)
admin.site.register(Stopset, StopsetAdmin)
admin.site.register(User, UserAdmin)
