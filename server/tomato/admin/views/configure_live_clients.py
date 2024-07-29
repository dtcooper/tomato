import json
import logging

from websockets.sync.client import connect as websocket_connect

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import TemplateView

from ...constants import PROTOCOL_VERSION
from .base import AdminViewMixin


logger = logging.getLogger(__name__)


class AdminConfigureLiveClientsView(AdminViewMixin, TemplateView):
    name = "configure_live_clients"
    perms = ("tomato.immediate_play_asset",)
    title = "Configure live clients"

    def post(self, request, *args, **kwargs):
        # Probably needs a refactor but okay for now
        try:
            with websocket_connect("ws://api:8000/api") as ws:
                ws.send(
                    json.dumps({
                        "user_id": request.user.id,
                        "tomato": "radio-automation",
                        "protocol_version": PROTOCOL_VERSION,
                        "admin_mode": True,
                        "method": "secret-key",
                        "key": settings.SECRET_KEY,
                    })
                )
                response = json.loads(ws.recv())
                if not response["success"]:
                    raise Exception(f"Error connecting: {response}")

                response = json.loads(ws.recv())
                if not response["type"] == "hello":
                    raise Exception(f"Invalid hello response type: {response}")
                num_connected_users = response["data"]["num_connected_users"]

                ws.send(json.dumps({"type": "reload-playlist"}))
                response = json.loads(ws.recv())
                if not response["type"] == "reload-playlist":
                    raise Exception(f"Invalid reload-playlist response type: {response}")
                if not response["data"]["success"]:
                    raise Exception(f"Failure reloading playlist: {response}")

        except Exception:
            logger.exception("Error while connecting to api")
            self.message_user(
                "An error occurred while connecting to the server. Check logs for more information.", messages.ERROR
            )
        else:
            self.message_user(f"Reloaded the playlist of {num_connected_users} connected desktop client(s)!")

        return redirect("admin:extra_configure_live_clients")
