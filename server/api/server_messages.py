import asyncio
import json
import logging

import psycopg
import redis.asyncio as redis

from django.conf import settings

from tomato.constants import POSTGRES_CHANGES_CHANNEL, REDIS_PUBSUB_KEY
from tomato.models import User

from .base import MessagesBase
from .connections import admins, users
from .schemas import OutgoingUserMessageTypes, ServerMessageTypes
from .utils import task


logger = logging.getLogger(__name__)


class ServerMessages(MessagesBase):
    Types = ServerMessageTypes

    def __init__(self):
        self.pending_db_changes = asyncio.Queue()
        super().__init__()

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
                await disconnect(reason="user not existing")
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

    async def process_db_change(self, message):
        if message["table"] == "users":
            await self.validate_user(user_id=message["user_id"], password_change=message["password_change"])
        else:
            await self.pending_db_changes.put(message)

    async def process_db_changes(self, messages, force_broadcast=False):
        if settings.DEBUG and not force_broadcast:
            logger.debug(f"Got changes to tables: {', '.join(sorted({m['table'] for m in messages}))}")
        await users.broadcast_data_change(force=force_broadcast)

    async def process_db_changes_force(self, message):
        logger.info("Forcing broadcast of data message")
        await self.process_db_changes(message, force_broadcast=True)

    async def process_reload_playlist(self, message):
        user_id = message.get("user_id") if message else None
        if user_id is None:
            await users.broadcast(OutgoingUserMessageTypes.RELOAD_PLAYLIST)
        else:
            await users.message(user_id, OutgoingUserMessageTypes.RELOAD_PLAYLIST)

    @task
    async def consume_redis_notifications(self):
        conn = redis.Redis(host="redis")

        async with conn.pubsub() as pubsub:
            await pubsub.subscribe(REDIS_PUBSUB_KEY)
            logger.info(f"Subscribed to redis key {REDIS_PUBSUB_KEY!r}")

            while True:
                redis_message = await pubsub.get_message(ignore_subscribe_messages=True)
                if redis_message:
                    message = json.loads(redis_message["data"])
                    await self.process(message_type=message["type"], message=message["data"])

    @task
    async def consume_db_notifications_debouncer(self):
        messages = []

        while True:
            try:
                messages.append(await asyncio.wait_for(self.pending_db_changes.get(), timeout=0.2))
            except asyncio.TimeoutError:
                # When we have received at least one db change for the timeout, then process them (debounce)
                if messages:
                    await self.process(message_type=self.Types.DB_CHANGES, message=messages)
                    messages = []

    @task
    async def consume_db_notifications(self):
        conn = await psycopg.AsyncConnection.connect(host="db", user="postgres", password="postgres", autocommit=True)
        await conn.execute(f"LISTEN {POSTGRES_CHANGES_CHANNEL}")
        logger.info(f"Listening to postgres channel {POSTGRES_CHANGES_CHANNEL!r}")

        notifications = conn.notifies()
        async for notification in notifications:
            db_change_data = json.loads(notification.payload)
            logger.debug(f"Got Postgres notification: {db_change_data}")
            await self.process(self.Types.DB_CHANGE, db_change_data)


server_messages = ServerMessages()