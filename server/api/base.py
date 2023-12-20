from collections import defaultdict
from importlib import import_module
from inspect import iscoroutinefunction
import logging
from weakref import WeakSet

from django.conf import settings
from django.contrib.auth import HASH_SESSION_KEY, SESSION_KEY
from django.utils.crypto import constant_time_compare

from starlette.websockets import WebSocket

from tomato.constants import PROTOCOL_VERSION
from tomato.models import User
from tomato.utils import django_json_dumps

from .utils import TomatoAuthError


logger = logging.getLogger(__name__)
SERVER_STATUS = {"server": "Tomato Radio Automation", "version": settings.TOMATO_VERSION, "protocol": PROTOCOL_VERSION}
SessionStore = import_module(settings.SESSION_ENGINE).SessionStore


class Connection:
    def __init__(self, websocket: WebSocket, user: User):
        self._ws: WebSocket = websocket
        self.user: User = user

    @property
    def addr(self):
        return self._ws.client.host

    async def receive(self):
        return await self._ws.receive_json()

    async def receive_message(self):
        data = await self.receive()
        return (data["type"], data["data"])

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
        self.connections: WeakSet[Connection] = WeakSet()
        self.user_ids_to_connections: defaultdict[int, WeakSet[Connection]] = defaultdict(WeakSet)
        super().__init__()

    @property
    def is_admin(self):
        raise NotImplementedError()

    async def hello(self, connection: Connection):
        raise NotImplementedError()

    async def authorize_extra(self, user: User) -> bool:
        raise NotImplementedError()

    def cleanup_user_ids_to_connections(self):
        for user_id in list(self.user_ids_to_connections.keys()):
            if len(self.user_ids_to_connections[user_id]) == 0:
                del self.user_ids_to_connections[user_id]

    async def authorize(self, greeting: dict, websocket: WebSocket) -> Connection:
        if greeting["protocol_version"] != PROTOCOL_VERSION:
            what, action = (
                ("an older", "downgrade") if greeting["protocol_version"] > PROTOCOL_VERSION else ("a newer", "upgrade")
            )
            raise TomatoAuthError(f"Server running {what} protocol than you. You'll need to {action} Tomato.")

        is_session = greeting["method"] == "session"

        if is_session:
            if "sessionid" not in websocket.cookies:
                raise TomatoAuthError("No sessionid cookie, can't complete session auth!")
            store = SessionStore(session_key=websocket.cookies["sessionid"])
            lookup = {"id": store.get(SESSION_KEY)}
        else:
            lookup = {"username": greeting["username"]}

        try:
            user = await User.objects.aget(**lookup)
        except User.DoesNotExist:
            pass
        else:
            if user.is_active and (not self.is_admin or user.is_superuser):
                if is_session:
                    session_hash = store.get(HASH_SESSION_KEY)
                    if session_hash and constant_time_compare(session_hash, user.get_session_auth_hash()):
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
        count = 0
        for count, connection in enumerate(self.connections, 1):
            try:
                await connection.send_raw(raw_message)
            except Exception:
                logger.exception("Error sending to websocket")
        logger.info(f"Broadcasted {message_type} message to {count} {'admins' if self.is_admin else 'users'}")

    async def message(self, user_id: int, message_type, message=None):
        raw_message = django_json_dumps({"type": message_type, "data": message})  # No sense serializing more than once
        if user_id in self.user_ids_to_connections:
            for connection in self.user_ids_to_connections[user_id]:
                try:
                    await connection.send_raw(raw_message)
                except Exception:
                    logger.exception("Error sending to websocket")
        logger.info(f"Sent {message_type} message to {user_id=}")

    async def authorize_and_process_new_websocket(self, greeting: dict, websocket: WebSocket):
        connection: Connection = await self.authorize(greeting, websocket)
        await connection.send(
            {"success": True, "admin_mode": self.is_admin, "user": connection.user.username, **SERVER_STATUS}
        )
        await self.hello(connection)
        self.connections.add(connection)
        self.user_ids_to_connections[connection.user.id].add(connection)

        self.cleanup_user_ids_to_connections()
        await self.run_for_connection(connection)

    async def process(self, connection, message_type, message):
        assert message_type in self.Types, f"Invalid message type: {message_type}"
        return await self.process_methods[message_type](connection, message)

    async def run_for_connection(self, connection: Connection):
        while True:
            message_type, message = await connection.receive_message()
            response = await self.process(connection, message_type, message)
            if response is not None:
                response_message_type, response_message = response
                await connection.message(response_message_type, response_message)
