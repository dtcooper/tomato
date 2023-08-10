from collections import OrderedDict
from decimal import Decimal
from pathlib import Path

from django.core.exceptions import ValidationError
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

EMAIL_EXCEPTIONS_ENABLED = env.bool("EMAIL_EXCEPTIONS_ENABLED", default=True)
if EMAIL_EXCEPTIONS_ENABLED:
    EMAIL_ADMIN_ADDRESS = env("EMAIL_ADMIN_ADDRESS")
    EMAIL_HOST = env("EMAIL_HOST")
    EMAIL_HOST_USER = env("EMAIL_USERNAME")
    EMAIL_HOST_PASSWORD = env("EMAIL_PASSWORD")
    EMAIL_PORT = env.int("EMAIL_PORT", default=587)
    EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=(EMAIL_PORT == 587))
    DEFAULT_FROM_EMAIL = SERVER_EMAIL = env("EMAIL_FROM_ADDRESS")

ADMIN_NOTICE_TEXT = env("ADMIN_NOTICE_TEXT", default=None)
ADMIN_NOTICE_TEXT_COLOR = env("ADMIN_NOTICE_TEXT_COLOR", default="#ffffff")
ADMIN_NOTICE_BACKGROUND = env("ADMIN_NOTICE_BACKGROUND", default="#ff0000")

# For development purposes only only
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
    # For django debug framework
    import socket

    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + ["127.0.0.1", "10.0.2.2"]

INSTALLED_APPS = [
    # Django
    "admin_notice",  # Third-party, but needs to come before admin
    "django.contrib.admin.apps.SimpleAdminConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "constance",
    "huey.contrib.djhuey",
    "django_file_form",
    "user_messages",
]
if DEBUG:
    INSTALLED_APPS.extend(
        [
            "debug_toolbar",
            "django_extensions",
        ]
    )
INSTALLED_APPS.extend(
    [
        # Local
        "tomato",
        # cleanup should be last
        "django_cleanup",
    ]
)

AUTH_USER_MODEL = "tomato.User"

MIDDLEWARE = []
if DEBUG:
    MIDDLEWARE.append("debug_toolbar.middleware.DebugToolbarMiddleware")
MIDDLEWARE.extend(
    [
        "django.middleware.security.SecurityMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
        "tomato.middleware.DirtyModelsToRedisMiddleware",
    ]
)

ROOT_URLCONF = "tomato.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://redis",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {"max_connections": 50},
            "PICKLE_VERSION": -1,
            "PARSER_CLASS": "redis.connection.HiredisParser",
        },
        "KEY_PREFIX": "cache",
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"

HUEY = {
    "results": False,
    "huey_class": "tomato.utils.DjangoPriorityRedisHuey",
    "immediate": HUEY_IMMEDIATE_MODE,
    "name": "tomato",
}

LANGUAGE_CODE = "en-us"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = "/serve/static"
MEDIA_URL = "/assets/"
MEDIA_ROOT = "/serve/assets"
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
        "filters": ["require_debug_false"],
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


def rotator_choices():
    from tomato.models import Rotator

    return tuple(Rotator.objects.values_list("id", "name").order_by("name"))


def validate_no_more_than_eight(value):
    if len(value) > 8:
        raise ValidationError("Pick a maximum of three choices.")


MIGRATION_MODULES = {"constance": None}  # Ignore constance models
CONSTANCE_BACKEND = "constance.backends.redisd.RedisBackend"
CONSTANCE_SUPERUSER_ONLY = False
CONSTANCE_IGNORE_ADMIN_VERSION_CHECK = True
CONSTANCE_REDIS_CONNECTION = "redis://redis"
CONSTANCE_ADDITIONAL_FIELDS = {
    "ui_modes": (
        "django.forms.MultipleChoiceField",
        {
            "choices": (("0", "Simple view"), ("1", "Standard view"), ("2", "Advanced view")),
            "widget": "django.forms.widgets.CheckboxSelectMultiple",
            "required": True,
        },
    ),
    "single_play_rotators": (
        "django.forms.MultipleChoiceField",
        {
            "choices": rotator_choices,
            "widget": "django.forms.widgets.CheckboxSelectMultiple",
            "required": False,
            "validators": (validate_no_more_than_eight,),
        },
    ),
    "asset_end_date_priority_weight_multiplier": (
        "django.forms.DecimalField",
        {
            "decimal_places": 2,
            "min_value": 0,
            "widget": "django.forms.TextInput",
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
            "widget_kwargs": {"attrs": {"size": 40}},
            "required": True,
        },
    ),
    "stopset_overdue_message": (
        "django.forms.CharField",
        {
            "max_length": 250,
            "widget": "django.forms.TextInput",
            "widget_kwargs": {"attrs": {"size": 60}},
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
}
_constance_not_implemented_html = '<span style="color: red">(Currently not implemented.)</span>'
CONSTANCE_CONFIG = {
    "STATION_NAME": ("Tomato Radio Automation", "The name of your station.", "short_text"),
    "SINGLE_PLAY_ROTATORS": (
        [],
        mark_safe(
            "Optional rotators to play a single asset from in the Desktop app. You can choose a maximum of 3."
            f" {_constance_not_implemented_html}"
        ),
        "single_play_rotators",
    ),
    "BROADCAST_COMPRESSION": (
        False,
        mark_safe(
            "Enable broadcast compression, smoothing out dynamic range in audio output.<br><strong>NOTE:</strong> "
            "compression is applied at the time you play an audio asset and performed on-the-fly in the desktop app."
        ),
    ),
    "EXTRACT_METADATA_FROM_FILE": (
        True,
        (
            "Attempt to extract metadata from audio file, if this is set to False the system just uses filename. For"
            " example with mp3s, metadata would extracted from an ID3 tag."
        ),
    ),
    "END_DATE_PRIORITY_WEIGHT_MULTIPLIER": (
        Decimal(0),
        mark_safe(
            "Multiply an asset's weight by this number if it has an end date <strong>and</strong> the current date is"
            f" the end date. Set to 0 to disable this feature. {_constance_not_implemented_html}"
        ),
        "asset_end_date_priority_weight_multiplier",
    ),
    "WAIT_INTERVAL": (
        20 * 60,  # 20 minutes
        "Time to wait between stop sets (in seconds). Set to 0 to disable the wait interval entirely.",
        "seconds",
    ),
    "NO_REPEAT_ASSETS_TIME": (
        0,
        (
            "The time (in seconds) required to elapse for the Desktop app to attempt to not repeat any assets. Set to 0"
            " to disable and allow potential repetition in the randomization algorithm. If there are not enough assets"
            " in a rotator to respect this setting, it will be ignored."
        ),
        "seconds",
    ),
    "STOPSET_ENTITY_NAME": (
        "stop set",
        "Override the language in the Desktop app to change the word 'stop set' to something custom",
        "short_text",
    ),
    "STOPSET_PRELOAD_COUNT": (
        2,
        (
            "Number of stopsets to preload in the UI. 2-3 is a good value for this, since new data could make preloaded"
            " ones stale."
        ),
        "stopset_preload_count",
    ),
    "STOPSET_OVERDUE_TIME": (
        0,
        mark_safe(
            'The time (in seconds) after the <code>WAIT_INTERVAL</code> after which an "overdue" message will flash.'
            " Set to 0 disable."
        ),
        "seconds",
    ),
    "STOPSET_OVERDUE_MESSAGE": (
        "You're overdue to play the next stopset. Please play it as soon as possible.",
        mark_safe(
            "The overdue message to be displayed when <code>STOPSET_OVERDUE_TIME</code>."
            f" {_constance_not_implemented_html}"
        ),
        "stopset_overdue_message",
    ),
    "ALLOW_REPEATS_IN_STOPSET": (
        False,
        (
            mark_safe(
                "The randomization algorithm will try its absolute best to avoid duplicates. However, when that's not"
                " possible (for example because of a nearly empty rotator), do you want <strong>the same asset</strong>"
                " to repeat, or for the rotator to be ignored in a given stop set?"
            )
        ),
    ),
    "WAIT_INTERVAL_SUBTRACTS_FROM_STOPSET_PLAYTIME": (
        False,
        (
            "Wait time subtracts the playtime of a stop set in minutes. This will provide more even results, ie the "
            "number of stop sets played per hour will be more consistent at the expense of a DJs air time."
        ),
    ),
    "TRIM_SILENCE": (
        True,
        mark_safe(
            "Trim silence from the beginning and end of audio files. Since this processing is done on the server, it's"
            " applied <strong>only</strong> at the time an audio file is uploaded. This means files will have silence"
            " trimmed (or not) according to this setting at the time of upload."
        ),
    ),
    "PREVENT_DUPLICATE_ASSETS": (
        True,
        (
            "Prevent duplicate audio assets from being uploaded when set. If not set, you may have multiple audio"
            " assets with the same underlying audio file."
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
    "UI_MODES": (["0", "1"], "What user interface modes are available to the desktop app.", "ui_modes"),
    "WARN_ON_EMPTY_ROTATORS": (True, "Warn when a rotator has no eligible assets to choose from. (Desktop app only)"),
}
CONSTANCE_CONFIG_FIELDSETS = OrderedDict(
    (
        (
            "User Interface Options",
            (
                "STATION_NAME",
                "UI_MODES",
            ),
        ),
        (
            "Audio Options",
            (
                "AUDIO_BITRATE",
                "EXTRACT_METADATA_FROM_FILE",
                "PREVENT_DUPLICATE_ASSETS",
                "TRIM_SILENCE",
            ),
        ),
        (
            "Airing Options",
            (
                "BROADCAST_COMPRESSION",
                "WAIT_INTERVAL",
                "WAIT_INTERVAL_SUBTRACTS_FROM_STOPSET_PLAYTIME",
                "WARN_ON_EMPTY_ROTATORS",
                "STOPSET_ENTITY_NAME",
                "STOPSET_PRELOAD_COUNT",
                "STOPSET_OVERDUE_TIME",
                "STOPSET_OVERDUE_MESSAGE",
                "NO_REPEAT_ASSETS_TIME",
                "ALLOW_REPEATS_IN_STOPSET",
                "SINGLE_PLAY_ROTATORS",
                "END_DATE_PRIORITY_WEIGHT_MULTIPLIER",
            ),
        ),
    )
)

SHELL_PLUS_IMPORTS = [
    "from constance import config",
    "from user_messages import api as user_messages_api",
    "from tomato import constants",
    "from tomato.ffmpeg import ffmpeg_convert, ffprobe",
    "from tomato.models import serialize_for_api",
    "from tomato.tasks import bulk_process_assets, process_asset",
]
