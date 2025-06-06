from collections import OrderedDict
import datetime
from decimal import Decimal
from pathlib import Path
import re

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.utils.safestring import mark_safe

import environ


env = environ.Env()
env.read_env("/.env")

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

DEBUG = env.bool("DEBUG", default=False)

DOMAIN_NAME = env("DOMAIN_NAME", default=None)
REQUIRE_STRONG_PASSWORDS = env("REQUIRE_STRONG_PASSWORDS", default=not DEBUG)
SECRET_KEY = env("SECRET_KEY")
TIME_ZONE = env("TIMEZONE", default="US/Pacific")

DEBUG_LOGS_PORT = env.int("DEBUG_LOGS_PORT", default=8002)

EMAIL_ENABLED = env.bool("EMAIL_ENABLED", default=False)
EMAIL_EXCEPTIONS_ENABLED = env.bool("EMAIL_EXCEPTIONS_ENABLED", default=False)
PASSWORD_RESET_TIMEOUT = 60 * 60 * 6  # 6 hours

EMAIL_DEBUG_ONLY_PRINT_TO_CONSOLE_ONLY = DEBUG and env.bool("EMAIL_DEBUG_ONLY_PRINT_TO_CONSOLE_ONLY", default=False)

if EMAIL_ENABLED:
    if EMAIL_DEBUG_ONLY_PRINT_TO_CONSOLE_ONLY:
        EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    else:
        EMAIL_HOST = env("EMAIL_HOST")
        EMAIL_HOST_USER = env("EMAIL_USERNAME")
        EMAIL_HOST_PASSWORD = env("EMAIL_PASSWORD")
        EMAIL_PORT = env.int("EMAIL_PORT", default=587)
        EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=EMAIL_PORT in (465, 587))
        DEFAULT_FROM_EMAIL = SERVER_EMAIL = env("EMAIL_FROM_ADDRESS")

elif EMAIL_EXCEPTIONS_ENABLED:
    raise ImproperlyConfigured("EMAIL_ENABLED=False but EMAIL_EXCEPTIONS_ENABLED=True.")

if EMAIL_EXCEPTIONS_ENABLED:
    EMAIL_ADMIN_ADDRESS = env("EMAIL_ADMIN_ADDRESS_TO_SEND_EXCEPTIONS")

ADMIN_NOTICE_TEXT = env("ADMIN_NOTICE_TEXT", default=None)
ADMIN_NOTICE_TEXT_COLOR = env("ADMIN_NOTICE_TEXT_COLOR", default="#ffffff")
ADMIN_NOTICE_BACKGROUND = env("ADMIN_NOTICE_BACKGROUND", default="#ff0000")

# For development purposes only
HUEY_IMMEDIATE_MODE = DEBUG and env("HUEY_IMMEDIATE_MODE", default=False)

# Compute version
TOMATO_VERSION = "dev" if DEBUG else "unknown"
if (version_file := PROJECT_DIR / ".tomato_version").exists():
    with open(version_file, "r") as file:
        TOMATO_VERSION = file.read().strip()


ALLOWED_HOSTS = {"app"}
if DEBUG:
    ALLOWED_HOSTS.add("localhost")
if DOMAIN_NAME:
    ALLOWED_HOSTS.add(DOMAIN_NAME)
ALLOWED_HOSTS = list(ALLOWED_HOSTS)

if DEBUG:
    DENIED_PATHS = ("/utils/configure_live_clients_iframe/",)
    # Show debug toolbar
    DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda request: request.path not in DENIED_PATHS}

INSTALLED_APPS = [
    # Django
    "admin_notice",  # Third-party, but needs to come before admin
    "django.contrib.admin.apps.SimpleAdminConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    # Third-party
    "constance",
    "django_admin_logs",
    "django_file_form",
    "huey.contrib.djhuey",
    "pgtrigger",
    "user_messages",
]
if DEBUG:
    INSTALLED_APPS.extend([
        "debug_toolbar",
        "django_extensions",
    ])
INSTALLED_APPS.extend([
    # Local
    "tomato",
])

AUTH_USER_MODEL = "tomato.User"
SESSION_COOKIE_AGE = 60 * 24 * 60 * 60  # 60 days

MIDDLEWARE = []
if DEBUG:
    MIDDLEWARE.append("debug_toolbar.middleware.DebugToolbarMiddleware")
MIDDLEWARE.extend([
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
])

ROOT_URLCONF = "tomato.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # For admin overrides
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                # django-user-messages: Swap out django.contrib.messages.context_processors.messages
                "user_messages.context_processors.messages",
                "admin_notice.context_processors.notice",
            ],
        },
    },
]

SILENCED_SYSTEM_CHECKS = ("admin.E404",)  # Needed for django-user-messages

WSGI_APPLICATION = "tomato.wsgi.application"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "postgres",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "db",
        "PORT": 5432,
    }
}

HUEY = {
    "results": False,
    "huey_class": "huey.SqliteHuey",
    "filename": "/huey/huey.db",
    "immediate": HUEY_IMMEDIATE_MODE,
    "name": "tomato",
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "cache",
    }
}

LANGUAGE_CODE = "en-us"
USE_I18N = True
USE_TZ = True

# Let nginx handle these
DATA_UPLOAD_MAX_NUMBER_FIELDS = None
DATA_UPLOAD_MAX_MEMORY_SIZE = None

STATIC_URL = "/static/"
STATIC_ROOT = "/serve/static"
MEDIA_URL = "/assets/"
MEDIA_ROOT = "/serve/assets"
LOGIN_URL = "/login/"
FILE_FORM_MUST_LOGIN = True
FILE_FORM_UPLOAD_DIR = "_temp_uploads"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        }
    },
    "formatters": {
        "console": {
            "format": "[%(asctime)s] %(levelname)s:%(name)s:%(lineno)s:%(funcName)s: %(message)s",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "console", "level": "INFO"},
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "django.request": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "huey": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "tomato": {
            "handlers": ["console"],
            "level": "INFO",
        },
    },
}
if EMAIL_EXCEPTIONS_ENABLED:
    ADMINS = [(f"{DOMAIN_NAME} Admin", EMAIL_ADMIN_ADDRESS)]
    LOGGING["handlers"]["mail_admins"] = {
        "level": "ERROR",
        "filters": None if EMAIL_DEBUG_ONLY_PRINT_TO_CONSOLE_ONLY else ["require_debug_false"],
        "class": "django.utils.log.AdminEmailHandler",
        "include_html": True,
    }
    LOGGING["loggers"]["django.request"]["handlers"].append("mail_admins")
    LOGGING["loggers"]["huey"]["handlers"].append("mail_admins")

if REQUIRE_STRONG_PASSWORDS:
    AUTH_PASSWORD_VALIDATORS = [
        {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
        {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
        {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
        {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    ]


DJANGO_ADMIN_LOGS_ENABLED = True
DJANGO_ADMIN_LOGS_DELETABLE = True


def validate_reset_times(values):
    if values != "0":
        values = (v.strip() for v in values.split("\n") if v.strip())
        for value in values:
            error = not re.search(r"^[0-9]{1,2}:[0-9]{2}$", value)
            try:
                datetime.datetime.strptime(value, "%H:%M")
            except ValueError:
                error = True

            if error:
                raise ValidationError(f'Error parsing time value: "{value}"')


CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"
CONSTANCE_SUPERUSER_ONLY = False
CONSTANCE_IGNORE_ADMIN_VERSION_CHECK = True
_style_full_width = {"style": "width: calc(100% - 5px)"}
CONSTANCE_ADDITIONAL_FIELDS = {
    "ui_modes": (
        "django.forms.MultipleChoiceField",
        {
            "choices": (("0", "Simple view"), ("1", "Standard view"), ("2", "Advanced view")),
            "widget": "django.forms.widgets.CheckboxSelectMultiple",
            "required": True,
        },
    ),
    "asset_end_date_priority_weight_multiplier": (
        "django.forms.DecimalField",
        {
            "decimal_places": 2,
            "min_value": 0,
            "widget": "django.forms.NumberInput",
            "widget_kwargs": {"attrs": {"size": 8}},
        },
    ),
    "audio_bitrate": (
        "django.forms.ChoiceField",
        {
            "choices": tuple(
                (str(bitrate), f"{bitrate}kbps")
                for bitrate in (32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320)
            ),
        },
    ),
    "short_text": (
        "django.forms.CharField",
        {
            "max_length": 50,
            "widget": "django.forms.TextInput",
            "widget_kwargs": {"attrs": _style_full_width},
            "required": True,
        },
    ),
    "stopset_preload_count": (
        "django.forms.IntegerField",
        {
            "widget": "django.forms.TextInput",
            "min_value": 1,
            "max_value": 20,
        },
    ),
    "seconds": (
        "django.forms.IntegerField",
        {
            "widget": "django.forms.TextInput",
            "min_value": 0,
            "max_value": 24 * 60 * 60,
        },
    ),
    "reset_times": (
        "django.forms.CharField",
        {
            "widget": "django.forms.Textarea",
            "widget_kwargs": {"attrs": {"rows": 8, **_style_full_width}},
            "validators": (validate_reset_times,),
        },
    ),
    "silence": (
        "django.forms.IntegerField",
        {
            "widget": "django.forms.TextInput",
            "min_value": 0,
            "max_value": 60,
        },
    ),
    "clock": (
        "django.forms.ChoiceField",
        {"choices": (("", "Off"), ("12h", "12 Hour"), ("24h", "24 Hour")), "required": False},
    ),
}
del _style_full_width

CONSTANCE_CONFIG = {
    "STATION_NAME": ("Tomato Radio Automation", "The name of your station.", "short_text"),
    "BROADCAST_COMPRESSION": (
        False,
        mark_safe(
            "Enable broadcast compression when <code>True</code>, smoothing out dynamic range in audio"
            " output.<br><strong>NOTE:</strong> compression is applied at the time you play an audio asset and"
            " performed on-the-fly in the desktop app."
        ),
    ),
    "EXTRACT_METADATA_FROM_FILE": (
        True,
        mark_safe(
            "Attempt to extract metadata from audio file when <code>True</code>, if this is set to <code>False</code>"
            " the system just uses filename. For example with mp3s, metadata would extracted from an ID3 tag."
        ),
    ),
    "END_DATE_PRIORITY_WEIGHT_MULTIPLIER": (
        Decimal(0),
        mark_safe(
            "Multiply an asset's weight by this number if it has an end date <strong>and</strong> the end date is"
            " in the next 24 hours (one day). <strong>Set to 0 to disable</strong> this feature."
        ),
        "asset_end_date_priority_weight_multiplier",
    ),
    "WAIT_INTERVAL": (
        20 * 60,  # 20 minutes
        mark_safe(
            "Time to wait between stop sets (in seconds). <strong>Set to 0 to disable</strong> the wait interval"
            " entirely."
        ),
        "seconds",
    ),
    "NO_REPEAT_ASSETS_TIME": (
        0,
        mark_safe(
            "The time (in seconds) required to elapse for the Desktop app to attempt to not repeat any assets."
            " <strong>Set to 0 to disable</strong> and allow potential repetition in the randomization algorithm. If"
            " there are not enough assets in a rotator to respect this setting, it will be ignored."
        ),
        "seconds",
    ),
    "STOPSET_PRELOAD_COUNT": (
        2,
        (
            "Number of stopsets to preload in the UI. 2 or 3 are good values for this, since new data could make"
            " preloaded ones stale."
        ),
        "stopset_preload_count",
    ),
    "STOPSET_OVERDUE_TIME": (
        0,
        mark_safe(
            'The time (in seconds) after the <code>WAIT_INTERVAL</code> after which an "overdue" message will flash.'
            " <strong>Set to 0 disable</strong>."
        ),
        "seconds",
    ),
    "ALLOW_REPEATS_IN_STOPSET": (
        False,
        (
            mark_safe(
                "The randomization algorithm will try its absolute best to avoid duplicates. However, when that's not"
                " possible (for example because of a nearly empty rotator), do you want <strong>the same asset</strong>"
                " to repeat (<code>True</code>), or for the rotator to be ignored in a given stop set"
                " (<code>False</code>)?"
            )
        ),
    ),
    "WAIT_INTERVAL_SUBTRACTS_FROM_STOPSET_PLAYTIME": (
        False,
        mark_safe(
            "Wait time subtracts the playtime of a stop set in minutes when <code>True</code>. When enabled Tomato will"
            " provide more even results, ie the number of stop sets played per hour will be more consistent at the"
            " possible expense of an individual DJs air time."
        ),
    ),
    "WAIT_INTERVAL_SUBTRACTS_FROM_STOPSET_PLAYTIME_MIN_LENGTH": (
        600,
        mark_safe(
            "When <code>WAIT_INTERVAL_SUBTRACTS_FROM_STOPSET_PLAYTIME</code> is set to <code>True</code>, wait"
            " intervals are of variable length. A very long stopset might naively result in a negative wait interval."
            " This setting avoids that by setting minimum wait interval length (in seconds)."
        ),
        "seconds",
    ),
    "TRIM_SILENCE": (
        True,
        mark_safe(
            "Trim silence from the beginning and end of audio files when <code>True</code>. Since this processing is"
            " done on the server, it's applied <strong>only</strong> at the time an audio file is uploaded. This means"
            " files will have silence trimmed (or not) according to this setting at the time of upload."
        ),
    ),
    "PREVENT_DUPLICATE_ASSETS": (
        True,
        mark_safe(
            "Prevent duplicate audio assets from being uploaded when <code>True</code>. If <code>False</code>, you may"
            " have multiple audio assets with the same underlying audio file."
        ),
    ),
    "AUDIO_BITRATE": (
        "192",
        mark_safe(
            "The audio bitrate to convert an asset to, if <strong>and only if</strong> processing is"
            " required.<br><strong>NOTE:</strong> processing is required when a file that is uploaded is"
            " <strong>not</strong> a valid MP3 file or <strong>TRIM_SILENCE</strong> is on."
        ),
        "audio_bitrate",
    ),
    "UI_MODES": (["0", "1", "2"], "Restrict what user interface modes are available to the desktop app.", "ui_modes"),
    "UI_MODE_RESET_TIMES": (
        "0",
        mark_safe(
            "Reset UI mode to the simplest enabled mode according to this setting. Enter a list of times (in 24-hour"
            " <code>HH:MM</code> format) with each time on a single line. <strong>Set to 0 disable</strong>."
            " The below example would reset the UI mode at midnight, 6am, noon, and"
            " 6pm:<br><br><code>00:00<br>06:00<br>12:00<br>18:00</code>"
        ),
        "reset_times",
    ),
    "WARN_ON_EMPTY_ROTATORS": (True, "Warn when a rotator is disabled or has no eligible assets to choose from."),
    "RELOAD_PLAYLIST_AFTER_DATA_CHANGES": (False, "Reload all connected client playlists when a data change occurs."),
    "ONE_CLIENT_LOGIN_PER_ACCOUNT": (False, "Only allow one desktop client to be connected per account."),
    "REJECT_SILENCE_LENGTH": (
        0,
        mark_safe("Reject silence assets of this many seconds. <strong>Set to 0 disable</strong>."),
        "silence",
    ),
    "CLOCK": (
        "",
        (
            "This will enable a clock that displays the current time in the desktop app (12- or 24-hour display). On"
            " larger screens the date will also display."
        ),
        "clock",
    ),
    "ENABLE_ASSET_DELETION": (True, "If disabled, no one can delete assets (can only archive soft delete)"),
}

CONSTANCE_CONFIG_FIELDSETS = OrderedDict((
    (
        "User interface options",
        (
            "STATION_NAME",
            "CLOCK",
            "UI_MODES",
            "UI_MODE_RESET_TIMES",
            "ONE_CLIENT_LOGIN_PER_ACCOUNT",
        ),
    ),
    (
        "Server audio processing",
        (
            "ENABLE_ASSET_DELETION",
            "AUDIO_BITRATE",
            "EXTRACT_METADATA_FROM_FILE",
            "PREVENT_DUPLICATE_ASSETS",
            "TRIM_SILENCE",
            "REJECT_SILENCE_LENGTH",
            "RELOAD_PLAYLIST_AFTER_DATA_CHANGES",
        ),
    ),
    (
        "Playout options",
        (
            "BROADCAST_COMPRESSION",
            "WARN_ON_EMPTY_ROTATORS",
            "WAIT_INTERVAL",
            "WAIT_INTERVAL_SUBTRACTS_FROM_STOPSET_PLAYTIME",
            "WAIT_INTERVAL_SUBTRACTS_FROM_STOPSET_PLAYTIME_MIN_LENGTH",
            "NO_REPEAT_ASSETS_TIME",
            "STOPSET_OVERDUE_TIME",
            "STOPSET_PRELOAD_COUNT",
            "ALLOW_REPEATS_IN_STOPSET",
            "END_DATE_PRIORITY_WEIGHT_MULTIPLIER",
        ),
    ),
))
CONSTANCE_SERVER_ONLY_SETTINGS = set(CONSTANCE_CONFIG_FIELDSETS["Server audio processing"])

SHELL_PLUS_IMPORTS = [
    "from constance import config",
    "from user_messages import api as user_messages_api",
    "from tomato import constants",
    "from tomato.ffmpeg import ffmpeg_convert, ffprobe, silence_detect",
    "from tomato.models import export_data_as_zip, import_data_from_zip, serialize_for_api",
    "from tomato.tasks import bulk_process_assets, process_asset, cleanup",
]
