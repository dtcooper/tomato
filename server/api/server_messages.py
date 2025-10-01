import json
import logging
import math

import psycopg

from tomato.constants import POSTGRES_MESSAGES_CHANNEL
from tomato.models import User

from .base import MessagesBase
from .connections import admins, users
from .schemas import ServerMessageTypes
from .utils import task


logger = logging.getLogger(__name__)
DB_QUEUE_DEDUPE_TIMEOUT = 0.2
DB_QUEUE_NUM_DEDUPE_TIMEOUTS_WITH_NO_MESSAGES_BEFORE_REFRESH = math.floor(90 / DB_QUEUE_DEDUPE_TIMEOUT)  # 90 seconds


class ServerMessages(MessagesBase):
    Types = ServerMessageTypes

    async def validate_user(self, user_id, password_change=False):
        async def disconnect(reason, admin_only=False):
            logger.info(f"Disconnecting user {user_id=} due to {reason}{' (admin only)' if admin_only else ''}")
            if not admin_only:
                await users.disconnect_user(user_id)
            await admins.disconnect_user(user_id)

        if password_change:
            await disconnect(reason="password change")

        else:
            try:
                user = await User.objects.aget(id=user_id)
            except User.DoesNotExist:
                await disconnect(reason="user account deleted")
            else:

                async def refresh(users_only=False):
                    await users.refresh_user(user)
                    if not users_only:
                        await admins.refresh_user(user)

                if not user.is_active:
                    await disconnect(reason="user set to inactive")
                elif not user.is_superuser:
                    await disconnect(reason="user not being a superuser!", admin_only=True)
                    await refresh(users_only=True)
                else:
                    await refresh()
                    logger.debug(f"User {user} got a change, but does not need to be disconnected")

    async def process_db_change(self, message, force=False):
        await users.broadcast_data_change(force=force)

    async def process_db_change_force(self, message=None):
        logger.info("Forcing broadcast of data message")
        await self.process_db_change(message, force=True)

    @staticmethod
    async def disconnect(user_id, admin_only=False):
        logger.info(f"Disconnecting user {user_id=} {' (admin only)' if admin_only else ''}")
        if not admin_only:
            await users.disconnect_user(user_id)
        await admins.disconnect_user(user_id)

    async def process_logout(self, message, admin_only=False):
        logger.info(f"Got logout for user user_ids={message['user_ids']}")

        for user_id in message["user_ids"]:
            await self.disconnect(user_id=user_id, admin_only=message.get("admin_only", False))

    @task
    async def consume_db_notifications(self):
        conn = await psycopg.AsyncConnection.connect(host="db", user="postgres", password="postgres", autocommit=True)
        await conn.execute(f"LISTEN {POSTGRES_MESSAGES_CHANNEL}")
        logger.info(f"Listening to postgres channel {POSTGRES_MESSAGES_CHANNEL!r}")

        db_notifications = conn.notifies()
        async for db_notification in db_notifications:
            notifications = json.loads(db_notification.payload)
            for notification in notifications:
                if isinstance(notification, str):
                    message_type, message = notification, None
                else:
                    message_type, message = notification

                logger.debug(f"Got Postgres notification: {message_type}: ({message=!r}")
                await self.process(message_type, message)


server_messages = ServerMessages()
