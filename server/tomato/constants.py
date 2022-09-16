import json

from django.conf import settings


with open(settings.PROJECT_DIR / ".." / ".." / "constants.json", "rb") as file:
    _data = json.load(file)

SCHEMA_VERSION = _data["schema_version"]
CLIENT_LOG_ENTRY_TYPES = _data["client_log_entry_types"]
COLORS = _data["colors"]
COLORS_DICT = {c["name"]: {k: c[k] for k in c.keys() if k != "name"} for c in COLORS}
