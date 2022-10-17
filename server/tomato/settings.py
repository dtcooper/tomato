from decimal import Decimal
from pathlib import Path

from django.core.exceptions import ValidationError

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

DEBUG_LOGS_PORT = env.int("DEBUG_LOGS_PORT", default=8001)

EMAIL_EXCEPTIONS_ENABLED = env.bool("EMAIL_EXCEPTIONS_ENABLED", default=True)
if EMAIL_EXCEPTIONS_ENABLED:
    EMAIL_ADMIN_ADDRESS = env("EMAIL_ADMIN_ADDRESS")
    EMAIL_HOST = env("EMAIL_HOST")
    EMAIL_HOST_USER = env("EMAIL_USERNAME")
    EMAIL_HOST_PASSWORD = env("EMAIL_PASSWORD")
    EMAIL_PORT = env.int("EMAIL_PORT", default=587)
    EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=(EMAIL_PORT == 587))
    DEFAULT_FROM_EMAIL = SERVER_EMAIL = env("EMAIL_FROM_ADDRESS")


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
            "PARSER_CLASS": "redis.connection.HiredisParser",
        },
        "KEY_PREFIX": "cache",
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"

HUEY = {
    "expire_time": 60 * 60,
    "huey_class": "tomato.utils.DjangoPriorityRedisExpiryHuey",
    "immediate": False,
    "name": "tomato",
    "store_none": True,
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


def validate_no_more_than_three(value):
    if len(value) > 3:
        raise ValidationError("Pick a maximum of three choices.")


CONSTANCE_BACKEND = "constance.backends.redisd.RedisBackend"
CONSTANCE_SUPERUSER_ONLY = False
CONSTANCE_REDIS_CONNECTION = "redis://redis"
CONSTANCE_ADDITIONAL_FIELDS = {
    "wait_interval": (
        "django.forms.DecimalField",
        {
            "decimal_places": 2,
            "max_value": 600 * 60,
            "min_value": 0,
            "widget": "django.forms.TextInput",
            "widget_kwargs": {"attrs": {"size": 8}},
        },
    ),
    "ui_modes": (
        "django.forms.MultipleChoiceField",
        {
            "choices": (("idiot", "Idiot mode"), ("easy", "Easy mode"), ("advanced", "Advanced mode")),
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
            "validators": (validate_no_more_than_three,),
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
    "sync_interval": (
        "django.forms.DecimalField",
        {
            "decimal_places": 2,
            "max_value": 15 * 60,
            "min_value": 1,
            "widget": "django.forms.TextInput",
            "widget_kwargs": {"attrs": {"size": 8}},
        },
    ),
}
CONSTANCE_CONFIG = {
    "SINGLE_PLAY_ROTATORS": (
        [],
        "Optional rotators to play a single asset from in the Desktop app.",
        "single_play_rotators",
    ),
    "BROADCAST_COMPRESSION": (
        False,
        "Enable broadcast compression, smoothing out dynamic range in audio output (client-side).",
    ),
    "EXTRACT_METADATA_FROM_FILE": (
        True,
        (
            "Attempt to txtract metadata from audio file (for example an ID3 tag), if this is set to False the system"
            " just uses filename"
        ),
    ),
    "END_DATE_PRIORITY_WEIGHT_MULTIPLIER": (
        Decimal(0),
        (
            "Multiply an asset's weight by this number if it has an end date AND the current date is the end date (set"
            " to 0 to disable)"
        ),
        "asset_end_date_priority_weight_multiplier",
    ),
    "WAIT_INTERVAL": (
        Decimal(20 * 60),
        "Time to wait between stop sets (in seconds). Set to 0 to disable the wait interval entirely.",
        "wait_interval",
    ),
    "SYNC_INTERVAL": (Decimal(5 * 20), "Time between client-server syncs (in seconds).", "sync_interval"),
    "WAIT_INTERVAL_SUBTRACTS_FROM_STOPSET_PLAYTIME": (
        False,
        (
            "Wait time subtracts the playtime of a stop set in minutes. This will provide more even results, ie the "
            "number of stop sets played per hour will be more consistent at the expense of a DJs air time."
        ),
    ),
    "TRIM_SILENCE": (
        True,
        (
            "Trim silence from the beginning and end of audio files (server-side). Since this processing is done on the"
            " server, it's applied at the time an audio file is uploaded. This means files will have silence trimmed"
            " (or not) according to this setting at the time of upload."
        ),
    ),
    "UI_MODES": (["idiot", "easy"], "What UI modes are available to the desktop app.", "ui_modes"),
}
CONSTANCE_CONFIG_FIELDSETS = {
    "User Interface Options": (
        "WAIT_INTERVAL",
        "WAIT_INTERVAL_SUBTRACTS_FROM_STOPSET_PLAYTIME",
        "SYNC_INTERVAL",
        "UI_MODES",
        "SINGLE_PLAY_ROTATORS",
    ),
    "Airing Options": ("END_DATE_PRIORITY_WEIGHT_MULTIPLIER",),
    "Audio Options": ("BROADCAST_COMPRESSION", "TRIM_SILENCE", "EXTRACT_METADATA_FROM_FILE"),
}

SHELL_PLUS_IMPORTS = [
    "from constance import config",
    "from user_messages import api as user_messages_api",
    "from tomato import constants",
    "from tomato.ffmpeg import ffprobe",
    "from tomato.tasks import process_asset",
]
