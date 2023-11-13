import json
import os
from pathlib import Path

from huey import PriorityRedisHuey

from django.core.serializers.json import DjangoJSONEncoder

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


def django_json_dumps(obj):
    return json.dumps(obj, separators=(",", ":"), cls=DjangoJSONEncoder)


def send_redis_message(message_type, data=None):
    conn = get_redis_connection()
    conn.publish(REDIS_PUBSUB_KEY, django_json_dumps({"type": message_type, "data": data}))


def send_config_update_redis_message():
    send_redis_message("db-change", {"table": "redis/config", "op": "update"})


class DjangoPriorityRedisHuey(PriorityRedisHuey):
    def __init__(self, *args, **kwargs):
        connection = get_redis_connection()
        kwargs["connection_pool"] = connection.connection_pool
        super().__init__(*args, **kwargs)


def listdir_recursive(dirname):
    dirname = Path(dirname)
    files = (os.path.join(dp, f) for dp, _, fn in os.walk(dirname) for f in fn)
    return [str(Path(file).relative_to(dirname)) for file in files]
