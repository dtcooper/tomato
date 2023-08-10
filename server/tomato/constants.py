import json

from django.conf import settings


with open(settings.PROJECT_DIR / "constants.json", "rb") as file:
    _data = json.load(file)

PROTOCOL_VERSION = _data["protocol_version"]
HELP_DOCS_URL = "http://dtcooper.github.io/tomato/"
CLIENT_LOG_ENTRY_TYPES = set(_data["client_log_entry_types"])
COLORS = _data["colors"]
COLORS_DICT = {c["name"]: {k: c[k] for k in c.keys() if k != "name"} for c in COLORS}

REDIS_PUBSUB_KEY = "tomato::pubsub"

EDIT_ONLY_ASSETS_GROUP_NAME = "Edit ONLY audio assets"
EDIT_ALL_GROUP_NAME = "Edit audio assets, rotators & stop sets"
