import itertools
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.contrib.admin import actions
from django.templatetags.static import static
from django.urls import path
from django.utils.html import format_html

from constance import config as constance_config
from constance.admin import Config

from ..constants import COLORS_DICT, HELP_DOCS_URL, PROTOCOL_VERSION
from ..models import Asset, AssetAlternate, ClientLogEntry, Rotator, Stopset, User
from .asset import AssetAdmin, AssetAlternateAdmin
from .client_log_entry import ClientLogEntryAdmin
from .config import ConfigAdmin
from .rotator import RotatorAdmin
from .server_log_entry import ServerLogEntry, ServerLogEntryAdmin
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
actions.delete_selected.short_description = "DANGER: Delete selected %(verbose_name_plural)s"


class TomatoAdminSite(admin.AdminSite):
    app_list_template_original = str(
        (Path(apps.get_app_config("admin").path) / "templates" / "admin" / "app_list.html").absolute()
    )
    empty_value_display = "None"
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

    def get_app_list_extra_context(self, request):
        app_list_extra = [
            {"url": f"admin:extra_{view.name}", "title": view.title, "external": False}
            for view in extra_views
            if view.check_perms(request) and not view.hide_from_app_list
        ]

        if request.user.is_superuser:
            app_list_extra.append({"url": "server_logs", "title": "Server logs", "external": True})

        admin_view_names = {view["url"] for view in app_list_extra if not view["external"]}
        return {
            "app_list_extra": sorted(app_list_extra, key=lambda view: view["title"].lower()),
            "app_list_extra_highlight": request.resolver_match.view_name in admin_view_names,
        }

    def each_context(self, request):
        context = super().each_context(request)

        help_docs_text = None
        for models_dict in itertools.chain.from_iterable(app["models"] for app in context["available_apps"]):
            if request.path.startswith(models_dict["admin_url"]):
                help_docs_text = MODELS_HELP_DOCS_TEXT.get(models_dict["model"])
                break

        return {
            "app_list_template_original": self.app_list_template_original,
            "help_docs_text": help_docs_text,
            "help_docs_url": HELP_DOCS_URL,
            "protocol_version": PROTOCOL_VERSION,
            "tomato_json_data": {"colors": COLORS_DICT, "station_name": constance_config.STATION_NAME},
            "tomato_version": settings.TOMATO_VERSION,
            "station_name": constance_config.STATION_NAME,
            **self.get_app_list_extra_context(request),
            **context,
        }


admin_site = TomatoAdminSite()

admin_site.register(Asset, AssetAdmin)
admin_site.register(AssetAlternate, AssetAlternateAdmin)
admin_site.register(ClientLogEntry, ClientLogEntryAdmin)
admin_site.register([Config], ConfigAdmin)
admin_site.register(Rotator, RotatorAdmin)
admin_site.register(ServerLogEntry, ServerLogEntryAdmin)
admin_site.register(Stopset, StopsetAdmin)
admin_site.register(User, UserAdmin)
