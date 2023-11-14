import logging

from tomato.constants import CLIENT_LOG_ENTRY_TYPES
from tomato.models import ClientLogEntry, serialize_for_api

from .base import Connection, ConnectionsBase
from .schemas import (
    AdminMessageTypes,
    DjangoServerMessageTypes,
    OutgoingDjangoServerMessageTypes,
    OutgoingUserMessageTypes,
    UserMessageTypes,
)
from .utils import retry_on_failure


logger = logging.getLogger(__name__)


class DjangoServerConnections(ConnectionsBase):
    Types = DjangoServerMessageTypes
    mode = "server"

    async def process_broadcast(self, connection: Connection, data):
        assert isinstance(data, str), "Message should be a string"
        await users.broadcast(OutgoingUserMessageTypes.BROADCAST_NOTICE, data)
        await connection.message(OutgoingDjangoServerMessageTypes.RESPONSE, {"success": True, "message": data})


class AdminConnections(ConnectionsBase):
    Types = AdminMessageTypes
    mode = "admin"

    async def hello(self, connection: Connection):
        await connection.send({"test": "You are an admin!"})


class UserConnections(ConnectionsBase):
    Types = UserMessageTypes
    mode = "user"

    def __init__(self):
        self._last_serialized_data = None
        super().__init__()

    async def hello(self, connection: Connection):
        await connection.message(OutgoingUserMessageTypes.DATA, await self.get_last_serialized_data())

    async def get_last_serialized_data(self):
        if self._last_serialized_data is None:
            self._last_serialized_data = await retry_on_failure(serialize_for_api)
        return self._last_serialized_data

    async def broadcast_data_change(self, force=False):
        serialized_data = await serialize_for_api()
        if force or serialized_data != self._last_serialized_data:
            await self.broadcast(OutgoingUserMessageTypes.DATA, serialized_data)
            self._last_serialized_data = serialized_data
        else:
            logger.debug("No change to DB data. Not broadcasting.")

    async def process_log(self, connection: Connection, data):
        uuid = data.pop("id")
        if connection.user.enable_client_logs:
            data.update({
                "created_by": connection.user,
                "ip_address": connection.addr,
            })

            if data["type"] not in CLIENT_LOG_ENTRY_TYPES:
                data["type"] = "unspecified"
            _, created = await ClientLogEntry.objects.aupdate_or_create(id=uuid, defaults=data)
            logger.info(f"Acknowledged log {uuid} for {connection.user}, {created=}")
            response = {"success": True, "id": uuid, "updated_existing": not created, "ignored": False}
        else:
            logger.info(f"Ignored log {uuid} for {connection.user}")
            response = {"success": True, "id": uuid, "updated_existing": False, "ignored": True}
        return (OutgoingUserMessageTypes.ACKNOWLEDGE_LOG, response)


admins: AdminConnections = AdminConnections()
users: UserConnections = UserConnections()
django_servers: DjangoServerConnections = DjangoServerConnections()


CONNECTION_MODES_TO_CONNECTIONS = {
    admins.mode: admins,
    users.mode: users,
    django_servers.mode: django_servers,
}
