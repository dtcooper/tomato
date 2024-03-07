import itertools
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.templatetags.static import static
from django.urls import path
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from constance import config as constance_config
from constance.admin import Config

from ..constants import COLORS_DICT, HELP_DOCS_URL, PROTOCOL_VERSION
from ..models import Asset, AssetAlternate, ClientLogEntry, Rotator, Stopset, User
from .asset import AssetAdmin, AssetAlternateAdmin
from .client_log_entry import ClientLogEntryAdmin
from .config import ConfigAdmin
from .rotator import RotatorAdmin
from .stopset import StopsetAdmin
from .user import UserAdmin
from .views import extra_views


MODELS_HELP_DOCS_TEXT = {
    model_cls: format_html(
        'For more information about {}, <a href="{}concepts#{}" target="_blank">see the docs</a>.',
        model_cls._meta.verbose_name_plural,
        HELP_DOCS_URL,
        model_cls._meta.verbose_name.lower().replace(" ", "-"),
    )
    for model_cls in (Asset, Rotator, Stopset)
}
MODELS_HELP_DOCS_TEXT[AssetAlternate] = MODELS_HELP_DOCS_TEXT[Asset]


class TomatoAdminSite(admin.AdminSite):
    app_list_template_original = str(
        (Path(apps.get_app_config("admin").path) / "templates" / "admin" / "app_list.html").absolute()
    )
    empty_value_display = mark_safe("None")
    index_title = "Tomato administration"
    site_url = None

    @property
    def site_title(self):
        return constance_config.STATION_NAME

    @property
    def site_header(self):
        return format_html(
            '<span style="display: flex; align-items: center; gap: 5px"><img src="{}" width="28">{}</span>',
            static("tomato/tomato.png"),
            self.site_title,
        )

    def get_urls(self):
        urls = [
            path(
                "utils/",
                self.admin_view(self.app_index),
                kwargs={
                    "app_label": None,
                    "extra_context": {"app_list": [{"name": "Utilities"}], "title": "Utilities administration"},
                },
                name="app_list_extra",
            )
        ]
        urls.extend(
            path(f"utils/{view.get_path()}", self.admin_view(view.as_view(self)), name=f"extra_{view.name}")
            for view in extra_views
        )
        urls.extend(super().get_urls())
        return urls

    def each_context(self, request):
        context = super().each_context(request)

        help_docs_text = None
        for models_dict in itertools.chain.from_iterable(app["models"] for app in context["available_apps"]):
            if request.path.startswith(models_dict["admin_url"]):
                help_docs_text = MODELS_HELP_DOCS_TEXT.get(models_dict["model"])
                break

        return {
            "app_list_template_original": self.app_list_template_original,
            "app_list_extra": [
                {"url": f"admin:extra_{view.name}", "title": view.title}
                for view in extra_views
                if view.check_perms(request)
            ],
            "app_list_extra_highlight": request.resolver_match.view_name in [
                f"admin:extra_{view.name}" for view in extra_views
            ],
            "help_docs_text": help_docs_text,
            "help_docs_url": HELP_DOCS_URL,
            "protocol_version": PROTOCOL_VERSION,
            "tomato_json_data": {"colors": COLORS_DICT, "station_name": constance_config.STATION_NAME},
            "tomato_version": settings.TOMATO_VERSION,
            "station_name": constance_config.STATION_NAME,
            **context,
        }


admin_site = TomatoAdminSite()

admin_site.register(Asset, AssetAdmin)
admin_site.register(AssetAlternate, AssetAlternateAdmin)
admin_site.register(ClientLogEntry, ClientLogEntryAdmin)
admin_site.register([Config], ConfigAdmin)
admin_site.register(Rotator, RotatorAdmin)
admin_site.register(Stopset, StopsetAdmin)
admin_site.register(User, UserAdmin)
