import json
import logging
import os
from pathlib import Path
import threading

from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection

from .constants import POSTGRES_MESSAGES_CHANNEL


logger = logging.getLogger(__name__)


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


def concise_json_dumps(obj, **kwargs):
    return json.dumps(obj, separators=(",", ":"), sort_keys=True, **kwargs)


def django_json_dumps(obj):
    return concise_json_dumps(obj, cls=DjangoJSONEncoder)


def listdir_recursive(dirname):
    dirname = Path(dirname)
    files = (os.path.join(dp, f) for dp, _, fn in os.walk(dirname) for f in fn)
    return [str(Path(file).relative_to(dirname)) for file in files]


def pg_notify(channel, payload):
    cursor = connection.cursor()
    cursor.execute("SELECT pg_notify(%s, %s)", (channel, json.dumps(payload)))


def dedupe(list_to_dedupe):
    seen = set()
    deduped = []
    for item in list_to_dedupe:
        hashable_message = concise_json_dumps(item)
        if hashable_message not in seen:
            seen.add(hashable_message)
            deduped.append(item)
    return deduped


notify_api_local = threading.local()


def notify_api(message_type="db-change", extra_data=None, *, force=False):
    notify_api_multiple([message_type if extra_data is None else (message_type, extra_data)], force=force)


def notify_api_multiple(messages: list, *, force=False):
    has_request = getattr(notify_api_local, "request", None) is not None
    is_blocking = getattr(notify_api_local, "blocked_pending_notify_api_messages_list", None) is not None
    if force or (not has_request and not is_blocking):
        logger.debug(
            f"Sending {len(messages)} notifications to API (de-duped) via Postgres NOTIFY on channel"
            f" {POSTGRES_MESSAGES_CHANNEL}"
        )
        cursor = connection.cursor()
        cursor.execute("SELECT pg_notify(%s, %s)", (POSTGRES_MESSAGES_CHANNEL, concise_json_dumps(dedupe(messages))))
    elif has_request:
        notify_api_local.request._notify_api_messages.extend(messages)
    else:
        notify_api_local.blocked_pending_notify_api_messages_list.extend(messages)


def block_pending_notify_api_messages():
    notify_api_local.blocked_pending_notify_api_messages_list = []


def unblock_and_flush_blocked_pending_notify_api_messages():
    if getattr(notify_api_local, "blocked_pending_notify_api_messages_list", None):
        notify_api_multiple(notify_api_local.blocked_pending_notify_api_messages_list, force=True)
    notify_api_local.blocked_pending_notify_api_messages_list = None
