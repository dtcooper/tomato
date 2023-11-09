import enum
import json

from django.conf import settings


with open(settings.PROJECT_DIR / "constants.json", "rb") as _file:
    _data = json.load(_file)

PROTOCOL_VERSION = _data["protocol_version"]
HELP_DOCS_URL = "http://dtcooper.github.io/tomato/"
CLIENT_LOG_ENTRY_TYPES = set(_data["client_log_entry_types"])
COLORS = _data["colors"]
COLORS_DICT = {c["name"]: {k: c[k] for k in c.keys() if k != "name"} for c in COLORS}

REDIS_PUBSUB_KEY = "tomato::pubsub"
POSTGRES_CHANGES_CHANNEL = "tomato_model_changes"

EDIT_ONLY_ASSETS_GROUP_NAME = "Edit ONLY audio assets"
EDIT_ALL_GROUP_NAME = "Edit audio assets, rotators & stop sets"


class MessageTypeServer(enum.StrEnum):
    DB_CHANGES = "db-changes"
    DB_CHANGE_FORCE_UPDATE = "db-change-force"
    DB_CHANGE_USER = "db-change-user"
    RELOAD_PLAYLIST = "reload-playlist"


class MessageTypeUser(enum.StrEnum):
    CREATE_LOG_ENTRY = "create-log-entry"


class MessageTypeAdmin(enum.StrEnum):
    pass


del _data, _file
