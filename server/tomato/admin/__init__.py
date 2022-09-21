from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.safestring import mark_safe

from constance.admin import Config
from django_file_form.models import TemporaryUploadedFile
from user_messages.models import Message

from ..models import Asset, ClientLogEntry, Rotator, Stopset, User
from .asset import AssetAdmin
from .client_log_entry import ClientLogEntryAdmin
from .config import ConfigAdmin
from .rotator import RotatorAdmin
from .stopset import StopsetAdmin
from .user import UserAdmin


admin.site.site_url = None
admin.site.site_title = admin.site.site_header = "Tomato Radio Automation"
admin.site.index_title = None
admin.site.empty_value_display = mark_safe("<em>None</em>")


admin.site.unregister([Config, Group, Message, TemporaryUploadedFile])
admin.site.register(Asset, AssetAdmin)
admin.site.register(ClientLogEntry, ClientLogEntryAdmin)
admin.site.register([Config], ConfigAdmin)
admin.site.register(Rotator, RotatorAdmin)
admin.site.register(Stopset, StopsetAdmin)
admin.site.register(User, UserAdmin)
