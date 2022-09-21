from decimal import Decimal
from pathlib import Path

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
    import socket  # only if you haven't already imported this

    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + ["127.0.0.1", "10.0.2.2"]

INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
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
                "tomato.utils.json_data_context_processor",
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

ADMINS = [(f"{DOMAIN_NAME} Admin", EMAIL_ADMIN_ADDRESS)]
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
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
            "include_html": True,
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "django.request": {
            "handlers": ["mail_admins", "console"],
            "level": "INFO",
            "propagate": False,
        },
        "huey": {
            "handlers": ["mail_admins", "console"],
            "level": "INFO",
            "propagate": False,
        },
        "tomato": {
            "handlers": ["console"],
            "level": "INFO",
        },
    },
}

if REQUIRE_STRONG_PASSWORDS:
    AUTH_PASSWORD_VALIDATORS = [
        {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
        {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 12}},
        {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
        {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    ]

CONSTANCE_BACKEND = "constance.backends.redisd.RedisBackend"
CONSTANCE_SUPERUSER_ONLY = False
CONSTANCE_REDIS_CONNECTION = "redis://redis"
CONSTANCE_ADDITIONAL_FIELDS = {
    "wait_interval_minutes": (
        "django.forms.fields.DecimalField",
        {
            "decimal_places": 2,
            "max_value": 600,
            "min_value": 0,
            "widget": "django.forms.TextInput",
            "widget_kwargs": {"attrs": {"size": 8}},
        },
    ),
}
CONSTANCE_CONFIG = {
    "BROADCAST_COMPRESSION": (False, "Enable broadcast compression, smoothing out dynamic range in audio output"),
    "WAIT_INTERVAL_MINUTES": (
        Decimal(20),
        "Time to wait between stop sets (in minutes). Set to 0 to disable the wait interval entirely.",
        "wait_interval_minutes",
    ),
    "WAIT_INTERVAL_SUBTRACTS_STOPSET_PLAYTIME": (
        False,
        (
            "Wait time subtracts the playtime of a stop set in minutes. This will provide more "
            "even results, ie the number of stop sets played per hour will be more consistent at "
            "the expense of a DJs air time."
        ),
    ),
}

SHELL_PLUS_IMPORTS = [
    "from user_messages import api as user_messages_api",
    "from tomato.ffmpeg import ffprobe",
    "from tomato.tasks import process_asset",
]
