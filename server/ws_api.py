import asyncio
import json
import logging
from weakref import WeakSet

from asgiref.sync import sync_to_async
import redis.asyncio as redis
from uvicorn.logging import ColourizedFormatter

from starlette.applications import Starlette
from starlette.endpoints import WebSocketEndpoint
from starlette.responses import PlainTextResponse
from starlette.routing import Route, WebSocketRoute

import django
from django.conf import settings
from django.contrib.auth import authenticate
from django.core.serializers.json import DjangoJSONEncoder


django.setup()

from tomato.constants import MODELS_DIRTY_REDIS_PUBSUB_KEY, PROTOCOL_VERSION  # noqa [after django.setup()]
from tomato.models import ClientLogEntry, serialize_for_api  # noqa


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


def failure(reason):
    return {"success": False, "error": reason}


class APIWebSocketEndpoint(WebSocketEndpoint):
    encoding = "json"
    subscribers = WeakSet()

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
        uuid = data.pop("id")
        data["created_by"] = self.user
        _, created = await ClientLogEntry.objects.aupdate_or_create(id=uuid, defaults=data)
        return {"success": True, "updated_existing": not created}

    async def on_recieve_authenticated(self, websocket, data):
        message_type = data.get("type")
        if message_type == "log":
            response = await self.process_log(data["data"])
        else:
            response = failure(f"Invalid message type: {json.dumps(message_type)}")
        await websocket.send_json(response)

    async def on_recieve_unauthenticated(self, websocket, data):
        if set(data.keys()) == {"username", "password", "protocol_version"}:
            protocol_version = data.pop("protocol_version")
            if protocol_version == PROTOCOL_VERSION:
                self.user = await sync_to_async(authenticate)(**data)
            else:
                logger.info(f"Client expected protocol {protocol_version}, but we are on {PROTOCOL_VERSION}.")
                await websocket.send_json(failure("Invalid client protocol version. Please update your client."))
                await websocket.close()

        if self.user is not None:
            logger.info(f"Accepted login credentials for {self.user}")
            await websocket.send_json({"success": True})
            self.authenticated = True
            await self.broadcast_data_change(single_websocket=websocket)
            self.subscribers.add(websocket)
        else:
            logger.info("Invalid login credentials")
            await websocket.send_json(failure("Invalid username or password."))
            await websocket.close()

    @classmethod
    async def broadcast_data_change(cls, single_websocket=None):
        while app.state.data is None:
            logger.warning("No initial data from app yet! Trying again.")
            await asyncio.sleep(0.5)

        subscribers = cls.subscribers if single_websocket is None else (single_websocket,)
        json_data = json.dumps({"type": "data", "data": app.state.data}, cls=DjangoJSONEncoder)
        num_broadcasted_to = 0

        for websocket in subscribers:
            try:
                await websocket.send_text(json_data)
            except Exception:
                logger.exception("Error broadcasting to subscriber")
            num_broadcasted_to += 1

        return num_broadcasted_to


async def background_subscriber():
    conn = redis.Redis(host="redis")
    logger.info("Connected to redis.")

    async def update_from_api_and_broadcast():
        data = await retry_on_failure(serialize_for_api, async_redis_conn=conn)
        if data != app.state.data:
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
        await pubsub.subscribe(MODELS_DIRTY_REDIS_PUBSUB_KEY)
        logger.info(f"Subscribed to redis key {MODELS_DIRTY_REDIS_PUBSUB_KEY!r}")

        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=None)

            # Consume all additional messages (avoids duplication)
            while (skipped := await pubsub.get_message(ignore_subscribe_messages=True, timeout=0)) is not None:
                logger.debug(f"Skipped: {skipped['data'].decode()}")

            if message is not None:
                logger.debug(f"Got message: {message['data'].decode()}")
                await update_from_api_and_broadcast()


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


app = Starlette(
    debug=settings.DEBUG,
    routes=[
        Route("/", index),
        WebSocketRoute("/api/", APIWebSocketEndpoint),
    ],
    on_startup=[startup],
    on_shutdown=[shutdown],
)
