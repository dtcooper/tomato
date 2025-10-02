import json
import logging
import math

import redis.asyncio as redis

from tomato.constants import REDIS_MESSAGES_PUBSUB_KEY

from .base import MessagesBase
from .connections import admins, users
from .schemas import ServerMessageTypes
from .utils import task


logger = logging.getLogger(__name__)
DB_QUEUE_DEDUPE_TIMEOUT = 0.2
DB_QUEUE_NUM_DEDUPE_TIMEOUTS_WITH_NO_MESSAGES_BEFORE_REFRESH = math.floor(90 / DB_QUEUE_DEDUPE_TIMEOUT)  # 90 seconds


class ServerMessages(MessagesBase):
    Types = ServerMessageTypes

    async def process_db_change(self, message):
        force = message.get("force", False)
        logger.debug(f"Got DB change message {force=}")
        await users.broadcast_data_change(force=force)

    async def process_logout(self, message):
        admin_only = message.get("admin_only", False)
        user_ids = message["user_ids"]
        logger.info(f"Got logout for user {user_ids=}{' (admin only)' if admin_only else ''}")
        for user_id in user_ids:
            if not admin_only:
                await users.disconnect_user(user_id)
            await admins.disconnect_user(user_id)

    @task
    async def consume_redis_notifications(self):
        conn = redis.Redis(host="redis")

        async with conn.pubsub() as pubsub:
            await pubsub.subscribe(REDIS_MESSAGES_PUBSUB_KEY)
            logger.info(f"Subscribed to redis pubsubs key {REDIS_MESSAGES_PUBSUB_KEY!r}")

            while True:
                redis_message = await pubsub.get_message(ignore_subscribe_messages=True)
                if redis_message:
                    notifications = json.loads(redis_message["data"])
                    for notification in notifications:
                        if isinstance(notification, str):
                            message_type, message = notification, None
                        else:
                            message_type, message = notification

                        logger.debug(f"Got redis notification: {message_type}: ({message=!r}")
                        await self.process(message_type, message or {})


server_messages = ServerMessages()
