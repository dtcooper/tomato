import asyncio
import logging

from schema import SchemaError

import django
from django.conf import settings

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket, WebSocketDisconnect
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware


django.setup()

from .base import SERVER_STATUS
from .connections import admins, users
from .schemas import greeting_schema
from .server_messages import server_messages
from .utils import RUNNING_TASKS, TomatoAuthError, init_logger


logger = logging.getLogger(__name__)


async def index(request: Request):
    return PlainTextResponse("There are only forty people in the world and five of them are hamburgers.\n")


async def api(websocket: WebSocket):
    await websocket.accept()

    try:
        try:
            greeting = greeting_schema.validate(await websocket.receive_json())
        except SchemaError:
            if settings.DEBUG:
                logger.exception("Schema validation error")
            raise TomatoAuthError("Invalid handshake. Are you sure you're running Tomato?")

        connections = admins if greeting["admin_mode"] else users
        await connections.authorize_and_process_new_websocket(greeting, websocket)

    except TomatoAuthError as auth_error:
        if auth_error.should_sleep:
            await asyncio.sleep(0.5, 1.5)
        error_msg = {"success": False, "error": str(auth_error)}
        if auth_error.field:
            error_msg["field"] = auth_error.field
        await websocket.send_json(error_msg)
        await websocket.close()

    except WebSocketDisconnect:
        pass

    else:
        await websocket.close()


async def status(request: Request):
    return JSONResponse(SERVER_STATUS)


async def startup():
    init_logger()

    await users.init_last_serialized_data()
    server_messages.consume_redis_notifications()
    server_messages.consume_db_notifications()
    server_messages.consume_db_notifications_debouncer()


async def shutdown():
    for running_task in RUNNING_TASKS:
        running_task.cancel()
        await running_task


routes = [
    Route("/", index, name="index"),
    WebSocketRoute("/api", api, name="api"),
    Route("/api", status, name="status"),
]

if settings.DEBUG:
    # For development, serve assets too
    routes.append(Mount("/assets", StaticFiles(directory=settings.MEDIA_ROOT), name="media"))


app = Starlette(
    debug=settings.DEBUG,
    routes=routes,
    on_startup=[startup],
    on_shutdown=[shutdown],
    middleware=[Middleware(ProxyHeadersMiddleware, trusted_hosts="*")],
)
