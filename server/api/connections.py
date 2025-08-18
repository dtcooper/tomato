import logging

from tomato.constants import CLIENT_LOG_ENTRY_TYPES
from tomato.models import ClientLogEntry, serialize_for_api

from .base import Connection, ConnectionsBase
from .schemas import AdminMessageTypes, OutgoingAdminMessageTypes, OutgoingUserMessageTypes, UserMessageTypes
from .utils import get_config_async, retry_on_failure


logger = logging.getLogger(__name__)


class AdminConnections(ConnectionsBase):
    Types = AdminMessageTypes
    OutgoingTypes = OutgoingAdminMessageTypes
    is_admin = True

    async def hello(self, connection: Connection):
        await self.update_user_connections(connection)

    async def on_disconnect(self, connection: Connection):
        await users.broadcast(OutgoingAdminMessageTypes.UNSUBSCRIBE, {"connection_id": connection.id})

    async def update_user_connections(self, connection: Connection | None = None):
        msg = [
            {"username": conn.user.username, "user_id": conn.user.id, "connection_id": id, "addr": conn.addr}
            for id, conn in users.connections.items()
        ]
        if connection is None:
            await self.broadcast(self.OutgoingTypes.USER_CONNECTIONS, msg)
        else:
            await connection.message(self.OutgoingTypes.USER_CONNECTIONS, msg)

    async def process_reload_playlist(self, connection: Connection, data):
        if data and (connection_id := data.get("connection_id")):
            logger.info(f"Reloading {connection_id=} playlists via admin request")
            await users.message(
                connection_id,
                OutgoingUserMessageTypes.RELOAD_PLAYLIST,
                {"notify": True, "connection_id": connection.id, "force": True},
            )
        else:
            logger.info("Reloading all playlists via admin request")
            await users.broadcast(
                OutgoingUserMessageTypes.RELOAD_PLAYLIST,
                {"notify": True, "connection_id": connection.id, "force": True},
            )

    async def process_notify(self, connection: Connection, data):
        connection_id = data.pop("connection_id")
        await users.message(connection_id, OutgoingUserMessageTypes.NOTIFY, {"connection_id": connection.id, **data})

    async def process_subscribe(self, connection: Connection, data):
        # Tell specific user to subscribe to this connection
        await users.message(data["connection_id"], OutgoingUserMessageTypes.SUBSCRIBE, {"connection_id": connection.id})

    async def process_unsubscribe(self, connection: Connection, data):
        # Tell specific user to unsubscribe to all connections
        await users.message(data["connection_id"], OutgoingUserMessageTypes.UNSUBSCRIBE)

    async def process_swap(self, connection: Connection, data):
        await users.message(
            data.pop("connection_id"), OutgoingUserMessageTypes.SWAP, {"connection_id": connection.id, **data}
        )

    async def process_play(self, connection: Connection, data):
        await users.message(data.pop("connection_id"), OutgoingUserMessageTypes.PLAY, {"connection_id": connection.id})

    async def process_logout(self, connection: Connection, data):
        await users.message(data.pop("connection_id"), OutgoingUserMessageTypes.LOGOUT)


class UserConnections(ConnectionsBase):
    Types = UserMessageTypes
    OutgoingTypes = OutgoingUserMessageTypes
    is_admin = False

    def __init__(self):
        self.last_serialized_data = None
        super().__init__()

    async def hello(self, connection: Connection):
        await connection.message(self.OutgoingTypes.DATA, self.last_serialized_data)

    async def on_connect(self, connection: Connection):
        await admins.update_user_connections()

    async def on_disconnect(self, connection: Connection):
        await admins.update_user_connections()

    async def init_last_serialized_data(self):
        logger.info("Initializing serialized data for clients")
        self.last_serialized_data = await retry_on_failure(serialize_for_api)

    async def broadcast_data_change(self, force=False):
        serialized_data = await serialize_for_api()
        has_changed = serialized_data != self.last_serialized_data
        if force or has_changed:
            await self.broadcast(self.OutgoingTypes.DATA, serialized_data)
            if has_changed and await get_config_async("RELOAD_PLAYLIST_AFTER_DATA_CHANGES"):
                await self.broadcast(self.OutgoingTypes.RELOAD_PLAYLIST, {"notify": False, "force": False})
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
        return (self.OutgoingTypes.ACKNOWLEDGE_LOG, response)

    async def process_unsubscribe(self, connection: Connection, data):
        # Tell all admins user has unsubscribed
        await admins.broadcast(OutgoingAdminMessageTypes.UNSUBSCRIBE, {"connection_id": connection.id})

    async def process_client_data(self, connection: Connection, data):
        # Receive client data (which means we're subscribed)
        await admins.message(
            data.pop("connection_id"), OutgoingAdminMessageTypes.CLIENT_DATA, {"connection_id": connection.id, **data}
        )

    async def process_ack_action(self, connection: Connection, data):
        await admins.message(
            data.pop("connection_id"), OutgoingAdminMessageTypes.ACK_ACTION, {"connection_id": connection.id, **data}
        )


admins: AdminConnections = AdminConnections()
users: UserConnections = UserConnections()
