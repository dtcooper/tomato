import itertools

from django.conf import settings
from django.contrib import admin
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from constance import config as constance_config
from constance.admin import Config

from ..constants import COLORS_DICT, HELP_DOCS_URL
from ..models import Asset, ClientLogEntry, Rotator, Stopset, User
from .asset import AssetAdmin
from .client_log_entry import ClientLogEntryAdmin
from .config import ConfigAdmin
from .rotator import RotatorAdmin
from .stopset import StopsetAdmin
from .user import UserAdmin


MODELS_HELP_DOCS_TEXT = {
    model_cls: format_html(
        'For more information about {}, <a href="{}concepts#{}" target="_blank">see the docs</a>.',
        model_cls._meta.verbose_name_plural,
        HELP_DOCS_URL,
        model_cls._meta.verbose_name.lower().replace(" ", "-"),
    )
    for model_cls in (Asset, Rotator, Stopset)
}


class TomatoAdminSite(admin.AdminSite):
    site_url = None
    index_title = "Tomato administration"
    empty_value_display = mark_safe("<em>None</em>")

    @property
    def site_title(self):
        return constance_config.STATION_NAME

    @property
    def site_header(self):
        return format_html(
            '<img src="{0}" width="32">&nbsp;&nbsp;{1}&nbsp;&nbsp;<img src="{0}" width="32">',
            static("tomato/tomato.png"),
            self.site_title,
        )

    def each_context(self, request):
        context = super().each_context(request)

        help_docs_text = None
        for models_dict in itertools.chain.from_iterable(app["models"] for app in context["available_apps"]):
            if request.path.startswith(models_dict["admin_url"]):
                help_docs_text = MODELS_HELP_DOCS_TEXT.get(models_dict["model"])
                break

        return {
            "help_docs_url": HELP_DOCS_URL,
            "help_docs_text": help_docs_text,
            "tomato_version": settings.TOMATO_VERSION,
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
