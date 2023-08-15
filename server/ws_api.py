import asyncio
import json
import logging
import weakref

from asgiref.sync import sync_to_async
import redis.asyncio as redis
from uvicorn.logging import ColourizedFormatter

from starlette.applications import Starlette
from starlette.endpoints import WebSocketEndpoint
from starlette.responses import PlainTextResponse
from starlette.routing import Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles

import django
from django.conf import settings
from django.contrib.auth import authenticate
from django.core.serializers.json import DjangoJSONEncoder


django.setup()

from tomato.constants import CLIENT_LOG_ENTRY_TYPES, PROTOCOL_VERSION, REDIS_PUBSUB_KEY  # noqa - after django.setup()
from tomato.models import ClientLogEntry, serialize_for_api  # noqa


PUBSUB_TIMEOUT = 120


logger = logging.getLogger(__name__)


async def index(request):
    return PlainTextResponse("There are only forty people in the world and five of them are hamburgers.\n")


async def retry_on_failure(coro, sleep_time_on_failure=1, *args, **kwargs):
    running = True
    while running:
        try:
            value = await coro(*args, **kwargs)
            return value
        except asyncio.CancelledError:
            running = False
        except Exception:
            logger.exception(f"An error occurred, retrying in {sleep_time_on_failure} second(s)")
            await asyncio.sleep(sleep_time_on_failure)


def failure(reason, **kwargs):
    return {"success": False, "error": reason, **kwargs}


class APIWebSocketEndpoint(WebSocketEndpoint):
    encoding = "json"
    subscribers = weakref.WeakKeyDictionary()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    async def on_connect(self, websocket):
        await websocket.accept()

    async def on_receive(self, websocket, data):
        if self.user is None:
            await self.on_recieve_unauthenticated(websocket, data)
        else:
            await self.on_recieve_authenticated(websocket, data)

    async def process_log(self, data):
        if self.user.enable_client_logs:
            uuid = data.pop("id")
            data["created_by"] = self.user
            if data["type"] not in CLIENT_LOG_ENTRY_TYPES:
                data["type"] = "unspecified"
            _, created = await ClientLogEntry.objects.aupdate_or_create(id=uuid, defaults=data)
            return {"success": True, "id": uuid, "updated_existing": not created, "ignored": False}
        else:
            return {"success": True, "id": uuid, "updated_existing": False, "ignored": True}

    async def on_recieve_authenticated(self, websocket, data):
        message_type = data.get("type")
        if message_type == "log":
            response = await self.process_log(data["data"])
        else:
            message_type = "error"
            response = {"message": f"Invalid message type: {json.dumps(message_type)}"}
        await websocket.send_json({"type": message_type, "data": response})

    async def on_recieve_unauthenticated(self, websocket, data):
        protocol_version = data.pop("protocol_version", None)
        if protocol_version == PROTOCOL_VERSION:
            if set(data.keys()) == {"username", "password"}:
                self.user = await sync_to_async(authenticate)(**data)
            if self.user is not None:
                logger.info(f"Accepted login credentials for {self.user}")
                await websocket.send_json({"success": True})
                self.authenticated = True
                await self.broadcast_data_change(single_websocket=websocket)
                logger.info(f"Sent hello of initial data to {self.user}")
                self.subscribers[websocket] = self
            else:
                logger.info("Invalid login credentials")
                await websocket.send_json(failure("Invalid username or password. Please try again.", field="userpass"))
                await websocket.close()

        else:
            error = "Server incompatible with client."
            if isinstance(protocol_version, int):
                if protocol_version > PROTOCOL_VERSION:
                    error = "Server running an older protocol than you. You need to downgrade Tomato."
                else:
                    error = "Server running a newer protocol than you. You need to upgrade Tomato."
            logger.info(f"Client sent protocol_version = {protocol_version!r}, but we are on {PROTOCOL_VERSION!r}.")
            await websocket.send_json(failure(error))
            await websocket.close()

    @classmethod
    async def broadcast_data_change(cls, single_websocket=None):
        while app.state.data is None:
            logger.warning("No initial data from app yet! Trying again.")
            await asyncio.sleep(0.5)

        subscribers = cls.subscribers.keys() if single_websocket is None else (single_websocket,)
        json_data = json.dumps({"type": "data", "data": app.state.data}, cls=DjangoJSONEncoder)
        num_broadcasted_to = 0

        for websocket in subscribers:
            try:
                await websocket.send_text(json_data)
            except Exception:
                logger.exception("Error broadcasting to subscriber")
            num_broadcasted_to += 1

        return num_broadcasted_to

    @classmethod
    async def logout_users(cls, user_ids):
        user_ids = set(user_ids)
        for websocket, endpoint in cls.subscribers.items():
            if endpoint.user is not None and endpoint.user.id in user_ids:
                logger.info(f"Disconnecting user {endpoint.user} by request from backend")
                await websocket.close()


async def background_subscriber():
    conn = redis.Redis(host="redis")
    logger.info("Connected to redis.")

    async def update_from_api_and_broadcast(force=False):
        data = await retry_on_failure(serialize_for_api)
        if force or data != app.state.data:
            app.state.data = data
            num_broadcasted_to = await APIWebSocketEndpoint.broadcast_data_change()
            if num_broadcasted_to > 0:
                logger.info(f"Broadcasted updated data to {num_broadcasted_to} subscribers(s)")
            else:
                logger.info("Updated data, no subscribers yet")
        else:
            logger.info("Broadcast requested, but no data change. Ignoring.")

    await update_from_api_and_broadcast()

    async with conn.pubsub() as pubsub:
        await pubsub.subscribe(REDIS_PUBSUB_KEY)
        logger.info(f"Subscribed to redis key {REDIS_PUBSUB_KEY!r}")
        got_first_none = False  # After connection, we get a stray None, no sense broadcasting because of it

        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=PUBSUB_TIMEOUT)

            if message is not None:
                message = json.loads(message["data"])
                logger.debug(f"Got message: {message}")
                if message["type"] in ("update", "force-update"):  # force-update for testing
                    await update_from_api_and_broadcast(force=message["type"] == "force-update")
                elif message["type"] == "logout":
                    await APIWebSocketEndpoint.logout_users(message["data"])
            elif got_first_none:
                logger.info(f"Subscription timed out after {PUBSUB_TIMEOUT} seconds.")
                await update_from_api_and_broadcast()
            else:
                got_first_none = True


async def startup():
    init_logger()
    app.state.data = None
    app.state.background_subscriber_task = asyncio.create_task(retry_on_failure(background_subscriber))


async def shutdown():
    app.state.background_subscriber_task.cancel()
    await app.state.background_subscriber_task


def init_logger():
    # Use a uvicorn-like logger
    handler = logging.StreamHandler()
    formatter = ColourizedFormatter("{levelprefix:<8} [api] {message}", style="{")
    handler.setFormatter(formatter)
    logger.setLevel("DEBUG" if settings.DEBUG else "INFO")
    logger.addHandler(handler)


routes = [
    Route("/", index, name="index"),
    WebSocketRoute("/api/", APIWebSocketEndpoint, name="api"),
]

if settings.DEBUG:
    # For development, serve assets too
    routes.append(Mount("/assets", StaticFiles(directory=settings.MEDIA_ROOT), name="media"))

app = Starlette(debug=settings.DEBUG, routes=routes, on_startup=[startup], on_shutdown=[shutdown])
