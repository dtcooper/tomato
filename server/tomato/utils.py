import datetime
import json

from huey import PriorityRedisHuey

from django_redis import get_redis_connection

from .constants import REDIS_PUBSUB_KEY


def once_at_startup(crontab):
    needs_to_run = True

    def startup_crontab(*args, **kwargs):
        nonlocal needs_to_run
        if needs_to_run:
            needs_to_run = False
            return True
        else:
            return crontab(*args, **kwargs)

    return startup_crontab


def send_redis_message(message_type, data):
    conn = get_redis_connection()
    conn.publish(REDIS_PUBSUB_KEY, json.dumps({"type": message_type, "data": data}))


def mark_models_dirty():
    send_redis_message("update", datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))


def mark_logged_out_users(user_ids):
    send_redis_message("logout", user_ids)


class DjangoPriorityRedisHuey(PriorityRedisHuey):
    def __init__(self, *args, **kwargs):
        connection = get_redis_connection()
        kwargs["connection_pool"] = connection.connection_pool
        super().__init__(*args, **kwargs)
