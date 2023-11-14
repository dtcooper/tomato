import json
import os
from pathlib import Path

from huey import PriorityRedisHuey
import websocket

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

from django_redis import get_redis_connection

from .constants import PROTOCOL_VERSION


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


def send_server_message(message_type, message=None):
    ws = websocket.create_connection("ws://api:8000/api", timeout=5)
    ws.send(
        json.dumps({
            "tomato": "radio-automation",
            "protocol_version": PROTOCOL_VERSION,
            "mode": "server",
            "method": "secret-key",
            "secret_key": settings.SECRET_KEY,
        })
    )
    auth_response = json.loads(ws.recv())
    if not auth_response["success"]:
        raise Exception(f'Websocket error: {auth_response["error"]}')

    ws.send(json.dumps({"type": message_type, "data": message}))
    return json.loads(ws.recv())


class DjangoPriorityRedisHuey(PriorityRedisHuey):
    def __init__(self, *args, **kwargs):
        connection = get_redis_connection()
        kwargs["connection_pool"] = connection.connection_pool
        super().__init__(*args, **kwargs)


def listdir_recursive(dirname):
    dirname = Path(dirname)
    files = (os.path.join(dp, f) for dp, _, fn in os.walk(dirname) for f in fn)
    return [str(Path(file).relative_to(dirname)) for file in files]
