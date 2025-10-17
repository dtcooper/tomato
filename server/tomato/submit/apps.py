from django.apps import AppConfig
from django.conf import settings


class TomatoSubmitConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tomato.submit"

    def ready(self):
        import tomato.submit.admin

        if settings.DEBUG:
            from django.utils.autoreload import autoreload_started

            from .templatetags.submit import CONSTANTS_FILE

            autoreload_started.connect(lambda sender, *args, **kwargs: sender.extra_files.add(CONSTANTS_FILE))
