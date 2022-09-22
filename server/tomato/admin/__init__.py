import itertools

from django.contrib import admin
from django.utils.safestring import mark_safe

from constance.admin import Config

from ..constants import COLORS_DICT
from ..models import Asset, ClientLogEntry, Rotator, Stopset, User
from .asset import AssetAdmin
from .client_log_entry import ClientLogEntryAdmin
from .config import ConfigAdmin
from .rotator import RotatorAdmin
from .stopset import StopsetAdmin
from .user import UserAdmin


MODELS_HELP_DOCS_TEXT = {
    Asset: mark_safe(
        "For information about what an audio asset is, <a"
        ' href="https://dtcooper.github.io/tomato/concepts/#audio-asset" target="_blank">see the docs</a>.'
    ),
    Rotator: mark_safe(
        'For information about what a rotators are, <a href="https://dtcooper.github.io/tomato/concepts/#rotator"'
        ' target="_blank">see the docs</a>.'
    ),
    Stopset: mark_safe(
        'For information about what an stop sets are, <a href="https://dtcooper.github.io/tomato/concepts/#stop-set"'
        ' target="_blank">see the docs</a>.'
    ),
}


class TomatoAdminSite(admin.AdminSite):
    site_url = None
    site_title = site_header = "Tomato Radio Automation"
    index_title = None
    empty_value_display = mark_safe("<em>None</em>")

    def each_context(self, request):
        context = super().each_context(request)

        help_docs_text = None
        for models_dict in itertools.chain.from_iterable(app["models"] for app in context["available_apps"]):
            if request.path.startswith(models_dict["admin_url"]):
                help_docs_text = MODELS_HELP_DOCS_TEXT.get(models_dict["model"])
                break

        return {
            "help_docs_text": help_docs_text,
            "tomato_json_data": {"colors": COLORS_DICT},
            **context,
        }


admin_site = TomatoAdminSite()

admin_site.register(Asset, AssetAdmin)
admin_site.register(ClientLogEntry, ClientLogEntryAdmin)
admin_site.register([Config], ConfigAdmin)
admin_site.register(Rotator, RotatorAdmin)
admin_site.register(Stopset, StopsetAdmin)
admin_site.register(User, UserAdmin)
