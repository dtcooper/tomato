from urllib.parse import urlparse, urlunparse

from django.apps import AppConfig, apps
from django.conf import settings
from django.db.models import signals

from s3file.forms import S3FileInputMixin

from .constants import EDIT_ALL_GROUP_NAME, EDIT_ONLY_ASSETS_GROUP_NAME


if settings.USE_MINIO:
    _build_attrs_original = S3FileInputMixin.build_attrs

    def _build_attrs_monkey_patched_minio_to_localhost(self, *args, **kwargs):
        attrs = _build_attrs_original(self, *args, **kwargs)
        url = urlparse(attrs["data-url"])
        url = url._replace(netloc=settings.DOMAIN_NAME, scheme="https", path=f"s3/{url.path}")
        attrs["data-url"] = urlunparse(url)
        return attrs

    _build_attrs_monkey_patched_minio_to_localhost.__name__ = "build_attrs"


class TomatoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tomato"
    verbose_name = "Radio automation"

    def ready(self):
        signals.post_migrate.connect(self.create_groups, sender=self)
        if settings.USE_MINIO:
            S3FileInputMixin.build_attrs = _build_attrs_monkey_patched_minio_to_localhost

    def create_groups(self, using=None, *args, **kwargs):
        all_groups = []
        Asset = apps.get_model("tomato.Asset")
        ClientLogEntry = apps.get_model("tomato.ClientLogEntry")
        ContentType = apps.get_model("contenttypes.ContentType")
        Group = apps.get_model("auth.Group")
        Permission = apps.get_model("auth.Permission")
        Rotator = apps.get_model("tomato.Rotator")
        Stopset = apps.get_model("tomato.Stopset")
        StopsetRotator = apps.get_model("tomato.StopsetRotator")

        asset = ContentType.objects.get_for_model(Asset)
        rotator = ContentType.objects.get_for_model(Rotator)
        stopset = ContentType.objects.get_for_model(Stopset)
        stopset_rotator = ContentType.objects.get_for_model(StopsetRotator)
        client_log_entry = ContentType.objects.get_for_model(ClientLogEntry)

        for name, content_types in (
            (EDIT_ALL_GROUP_NAME, (asset, rotator, stopset, stopset_rotator)),
            (EDIT_ONLY_ASSETS_GROUP_NAME, (asset,)),
            (f"View and export {ClientLogEntry._meta.verbose_name_plural}", (client_log_entry,)),
        ):
            group, _ = Group.objects.get_or_create(name=name)
            group.permissions.add(*Permission.objects.filter(content_type__in=content_types))
            all_groups.append(group)

        group, _ = Group.objects.get_or_create(name="Modify configuration")
        # tomato comes after constance in INSTALLED_APPS, so this should always exist
        group.permissions.add(Permission.objects.get(codename="change_config"))
        all_groups.append(group)

        Group.objects.exclude(id__in=[group.id for group in all_groups]).delete()
