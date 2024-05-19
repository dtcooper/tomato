from adafruit_datetime import datetime
from os import stat


__version__ = "0.0.4-dev"
PRODUCT_NAME = "Tomato Button Box"
LAST_MODIFIED = str(datetime.fromtimestamp(max(stat(f"{f}.py")[8] for f in ("code", "boot", "common")))) + " UTC"
