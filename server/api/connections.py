import logging

from tomato.constants import CLIENT_LOG_ENTRY_TYPES
from tomato.models import ClientLogEntry, get_config_async, serialize_for_api

from .base import Connection, ConnectionsBase
from .schemas import AdminMessageTypes, OutgoingAdminMessageTypes, OutgoingUserMessageTypes, UserMessageTypes
from .utils import retry_on_failure


logger = logging.getLogger(__name__)


class AdminConnections(ConnectionsBase):
    Types = AdminMessageTypes
    is_admin = True

    async def hello(self, connection: Connection):
        await connection.message(OutgoingAdminMessageTypes.HELLO, {"num_connected_users": users.num_connections})

    async def process_reload_playlist(self, connection: Connection, data):
        logger.info("Reloading all playlist via admin request")
        await users.broadcast(OutgoingAdminMessageTypes.RELOAD_PLAYLIST)
        await connection.message(OutgoingAdminMessageTypes.RELOAD_PLAYLIST, {"success": True})


class UserConnections(ConnectionsBase):
    Types = UserMessageTypes
    is_admin = False

    def __init__(self):
        self.last_serialized_data = None
        super().__init__()

    async def hello(self, connection: Connection):
        await connection.message(OutgoingUserMessageTypes.DATA, self.last_serialized_data)

    async def init_last_serialized_data(self):
        logger.info("Initializing serialized data for clients")
        self.last_serialized_data = await retry_on_failure(serialize_for_api)

    async def broadcast_data_change(self, force=False):
        serialized_data = await serialize_for_api()
        if force or serialized_data != self.last_serialized_data:
            await self.broadcast(OutgoingUserMessageTypes.DATA, serialized_data)
            if await get_config_async("RELOAD_PLAYLIST_AFTER_DATA_CHANGES"):
                await self.broadcast(OutgoingUserMessageTypes.RELOAD_PLAYLIST)
            self.last_serialized_data = serialized_data
        else:
            logger.debug("No change to DB data. Not broadcasting.")

    async def process_log(self, connection: Connection, data):
        uuid = data.pop("id")
        if connection.user.enable_client_logs or data["type"] == "internal_error":
            data.update({
                "created_by": connection.user,
                "ip_address": connection.addr,
            })

            if data["type"] not in CLIENT_LOG_ENTRY_TYPES:
                data["type"] = "unspecified"
            _, created = await ClientLogEntry.objects.aupdate_or_create(id=uuid, defaults=data)
            logger.info(f"Acknowledged {data['type']} log {uuid} for {connection.user}, {created=}")
            response = {"success": True, "id": uuid, "updated_existing": not created, "ignored": False}
        else:
            logger.info(f"Ignored {data['type']} log {uuid} for {connection.user}")
            response = {"success": True, "id": uuid, "updated_existing": False, "ignored": True}
        return (OutgoingUserMessageTypes.ACKNOWLEDGE_LOG, response)


admins: AdminConnections = AdminConnections()
users: UserConnections = UserConnections()
