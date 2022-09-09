import json

from django.conf import settings


with open(settings.PROJECT_DIR / ".." / "constants.json", "rb") as file:
    _DATA = json.load(file)

COLORS = _DATA["colors"]
COLORS_DICT = {c["name"]: {k: c[k] for k in c.keys() if k != "name"} for c in COLORS}
