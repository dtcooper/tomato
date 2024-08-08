import logging

from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.generic import TemplateView

from ...constants import PROTOCOL_VERSION
from ...models import serialize_for_api_sync
from .base import AdminViewMixin


logger = logging.getLogger(__name__)


class AdminConfigureLiveClientsView(AdminViewMixin, TemplateView):
    name = "configure_live_clients"
    perms = ("tomato.configure_live_clients",)
    title = "Configure live clients"


@method_decorator(xframe_options_sameorigin, name="dispatch")
class AdminConfigureLiveClientsIFrameView(AdminViewMixin, TemplateView):
    hide_from_app_list = True
    name = "configure_live_clients_iframe"
    perms = ("tomato.configure_live_clients",)
    title = "Configure live clients"

    def get_context_data(self, **kwargs):
        return {
            "configure_live_clients_data": {
                "is_secure": self.request.is_secure(),
                "debug": settings.DEBUG,
                "protocol_version": PROTOCOL_VERSION,
                "serialized_data": serialize_for_api_sync(skip_config=True),
                "admin_username": self.request.user.username,
            },
            **super().get_context_data(**kwargs),
        }
