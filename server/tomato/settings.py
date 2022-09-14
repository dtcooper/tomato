from collections import OrderedDict
from pathlib import Path

from django.core import validators

import environ


env = environ.Env()
env.read_env("/.env")

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

DEBUG = env.bool("DEBUG", default=False)
DOMAIN_NAME = env("DOMAIN_NAME", default=None)
REQUIRE_STRONG_PASSWORDS = env("REQUIRE_STRONG_PASSWORDS", default=False)
SECRET_KEY = env("SECRET_KEY")
TIME_ZONE = env("TIMEZONE", default="US/Pacific")

AWS_S3_REGION_NAME = env("DIGITALOCEAN_SPACES_REGION_NAME")
AWS_ACCESS_KEY_ID = env("DIGITALOCEAN_SPACES_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("DIGITALOCEAN_SPACES_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("DIGITALOCEAN_SPACES_STORAGE_BUCKET_NAME")

ALLOWED_HOSTS = {"app"}
if DEBUG:
    ALLOWED_HOSTS.add("localhost")
if DOMAIN_NAME:
    ALLOWED_HOSTS.add(DOMAIN_NAME)
ALLOWED_HOSTS = list(ALLOWED_HOSTS)

INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "constance",
    "django_extensions",
    "s3file",
    # Local
    "tomato",
    # cleanup should be last
    "django_cleanup",
]

AUTH_USER_MODEL = "tomato.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "s3file.middleware.S3FileMiddleware",
]

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
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "tomato.wsgi.application"

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

LANGUAGE_CODE = "en-us"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = "/serve/static"
MEDIA_URL = "/media/"
MEDIA_ROOT = "/serve/media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AWS_S3_FILE_OVERWRITE = False
AWS_S3_ENDPOINT_URL = f"https://{AWS_S3_REGION_NAME}.digitaloceanspaces.com"
AWS_DEFAULT_ACL = "public-read"
AWS_QUERYSTRING_AUTH = False
DEFAULT_FILE_STORAGE = "s3file.storages_optimized.S3OptimizedUploadStorage"

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
        "django.forms.fields.IntegerField",
        {
            "widget": "django.forms.TextInput",
            "widget_kwargs": {"attrs": {"size": 5}},
            "validators": [validators.MinValueValidator(0), validators.MaxValueValidator(600)],
        },
    ),
}
CONSTANCE_CONFIG = OrderedDict(
    {
        "WAIT_INTERVAL_MINUTES": (
            20,
            "Time to wait between stop sets (in minutes). Set to 0 to disable the wait interval.",
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
)

SHELL_PLUS_IMPORTS = [
    "from tomato.ffmpeg import ffprobe",
]
