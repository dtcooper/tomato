from collections import defaultdict
from importlib import import_module
from inspect import iscoroutinefunction
import logging
import uuid

from asgiref.sync import sync_to_async

from django.conf import settings
from django.contrib.auth import HASH_SESSION_KEY, SESSION_KEY
from django.utils.crypto import constant_time_compare

from starlette.websockets import WebSocket

from tomato.constants import PROTOCOL_VERSION
from tomato.models import User, get_config_async
from tomato.utils import django_json_dumps

from .utils import TomatoAuthError


logger = logging.getLogger(__name__)
SERVER_STATUS = {"server": "Tomato Radio Automation", "version": settings.TOMATO_VERSION, "protocol": PROTOCOL_VERSION}
SessionStore = import_module(settings.SESSION_ENGINE).SessionStore


class Connection:
    def __init__(self, websocket: WebSocket, user: User):
        self._ws: WebSocket = websocket
        self.id = str(uuid.uuid4())
        self.user: User = user

    @property
    def addr(self):
        return self._ws.client.host

    async def receive(self):
        return await self._ws.receive_json()

    async def receive_message(self):
        data = await self.receive()
        return (data["type"], data.get("data", {}))

    async def message(self, message_type, message=None):
        await self.send({"type": message_type, "data": message})

    async def send(self, obj):
        await self.send_raw(django_json_dumps(obj))

    async def send_raw(self, text):
        await self._ws.send_text(text)

    async def disconnect(self):
        await self._ws.close()

    def __repr__(self):
        return f"Connection({self.user.username}, {self.addr})"


class MessagesBase:
    def __init__(self):
        self.process_methods = {}
        for message_type in self.Types:
            method_name = f"process_{message_type.replace('-', '_')}"
            method = getattr(self, method_name, None)
            if not iscoroutinefunction(method):
                raise NotImplementedError(
                    f"Must implement coroutine function {self.__class__.__name__}.{method_name}(...)"
                )
            self.process_methods[message_type] = method

    async def process(self, message_type, message):
        assert message_type in self.Types, f"Invalid message type: {message_type}"
        await self.process_methods[message_type](message)


class ConnectionsBase(MessagesBase):
    def __init__(self):
        self.connections: dict[str, Connection] = {}
        self.user_ids_to_connections: defaultdict[int, set[Connection]] = defaultdict(set)
        super().__init__()

    @property
    def is_admin(self):
        raise NotImplementedError()

    @property
    def num_connections(self):
        return len(self.connections)

    async def hello(self, connection: Connection):
        pass

    async def on_connect(self, connection: Connection):
        pass

    async def on_disconnect(self, connection: Connection):
        pass

    async def authorize(self, greeting: dict, websocket: WebSocket) -> Connection:
        if greeting["protocol_version"] != PROTOCOL_VERSION:
            what, action = (
                ("an older", "downgrade") if greeting["protocol_version"] > PROTOCOL_VERSION else ("a newer", "upgrade")
            )
            raise TomatoAuthError(f"Server running {what} protocol than you. You'll need to {action} Tomato.")

        if is_session := greeting["method"] == "session":
            if "sessionid" not in websocket.cookies:
                raise TomatoAuthError("No sessionid cookie, can't complete session auth!")
            store = SessionStore(session_key=websocket.cookies["sessionid"])
            lookup = {"id": await sync_to_async(store.get)(SESSION_KEY)}
        else:
            lookup = {"username": greeting["username"]}

        try:
            user = await User.objects.aget(**lookup)
        except User.DoesNotExist:
            pass
        else:
            if user.is_active and (
                not self.is_admin or await sync_to_async(user.has_perm)("tomato.configure_live_clients")
            ):
                if is_session:
                    session_hash = store.get(HASH_SESSION_KEY)
                    if session_hash and await sync_to_async(constant_time_compare)(
                        session_hash, await sync_to_async(user.get_session_auth_hash)()
                    ):
                        logger.info(f"Authorized admin session for {user}")
                        return Connection(websocket, user)
                elif await user.acheck_password(greeting["password"]):
                    logger.info(f"Authorized user connection for {user}")
                    return Connection(websocket, user)
        raise TomatoAuthError("Invalid username or password.", should_sleep=True, field="userpass")

    async def disconnect_user(self, user_id: int):
        if user_id in self.user_ids_to_connections:
            for connection in self.user_ids_to_connections[user_id]:
                try:
                    await connection.disconnect()
                except Exception:
                    logger.exception(f"Error disconnecting websocket {user_id=}")
        logger.debug(f"Disconnected {user_id=}, {self.is_admin=}")

    async def refresh_user(self, user: User):
        if user.id in self.user_ids_to_connections:
            for connection in self.user_ids_to_connections[user.id]:
                connection.user = user
        logger.debug(f"Refreshed {user}, {self.is_admin=}")

    async def broadcast(self, message_type, message=None):
        raw_message = django_json_dumps({"type": message_type, "data": message})  # No sense serializing more than once
        for connection in self.connections.values():
            try:
                await connection.send_raw(raw_message)
            except Exception:
                logger.exception("Recoverable error while sending to websocket")

    async def message_user(self, user_id: int, message_type, message=None):
        raw_message = django_json_dumps({"type": message_type, "data": message})  # No sense serializing more than once
        if user_id in self.user_ids_to_connections:
            for connection in self.user_ids_to_connections[user_id]:
                try:
                    await connection.send_raw(raw_message)
                except Exception:
                    logger.exception("Recoverable error while sending to websocket")

    async def message(self, connection_id: int, message_type, message=None):
        raw_message = django_json_dumps({"type": message_type, "data": message})  # No sense serializing more than once
        try:
            connection = self.connections[connection_id]
            await connection.send_raw(raw_message)
        except Exception:
            logger.exception("Recoverable error while sending to websocket")

    async def authorize_and_process_new_websocket(self, greeting: dict, websocket: WebSocket):
        connection: Connection = await self.authorize(greeting, websocket)

        if (
            not self.is_admin
            and connection.user.id in self.user_ids_to_connections
            and await get_config_async("ONE_CLIENT_LOGIN_PER_ACCOUNT")
        ):
            raise TomatoAuthError("That user account is already logged in on another computer.")

        await connection.send(
            {"success": True, "admin_mode": self.is_admin, "user": connection.user.username, **SERVER_STATUS}
        )
        await self.hello(connection)
        self.connections[connection.id] = connection
        self.user_ids_to_connections[connection.user.id].add(connection)
        await self.on_connect(connection)
        try:
            await self.run_for_connection(connection)
        finally:
            del self.connections[connection.id]
            user_id = connection.user.id
            self.user_ids_to_connections[user_id].remove(connection)
            if len(self.user_ids_to_connections[user_id]) == 0:
                del self.user_ids_to_connections[user_id]
            await self.on_disconnect(connection)

    async def process(self, connection, message_type, message):
        assert (
            message_type in self.Types
        ), f"Invalid message type: process_{message_type}() needed on {type(self).__name__}"
        return await self.process_methods[message_type](connection, message)

    async def run_for_connection(self, connection: Connection):
        while True:
            message_type, message = await connection.receive_message()
            response = await self.process(connection, message_type, message)
            if response is not None:
                response_message_type, response_message = response
                await connection.message(response_message_type, response_message)
