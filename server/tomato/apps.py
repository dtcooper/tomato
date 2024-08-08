from pathlib import Path

from django.apps import AppConfig, apps
from django.conf import settings
from django.conf.locale.en import formats as en_formats
from django.db.models import signals

from .constants import EDIT_ALL_GROUP_NAME, EDIT_ONLY_ASSETS_GROUP_NAME


class TomatoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tomato"
    verbose_name = "Radio automation"

    def ready(self):
        self.patch_formats()
        temp_upload_path = Path(settings.MEDIA_ROOT) / settings.FILE_FORM_UPLOAD_DIR
        temp_upload_path.mkdir(parents=True, exist_ok=True)
        signals.post_migrate.connect(self.create_groups, sender=self)

    def patch_formats(self):
        en_formats.SHORT_DATETIME_FORMAT = "n/j/y g:i A"
        en_formats.DATETIME_FORMAT = "M j Y, g:i A"

    def create_groups(self, using=None, *args, **kwargs):
        all_groups = []
        Asset = apps.get_model("tomato.Asset")
        AssetAlternate = apps.get_model("tomato.AssetAlternate")
        ClientLogEntry = apps.get_model("tomato.ClientLogEntry")
        ContentType = apps.get_model("contenttypes.ContentType")
        Group = apps.get_model("auth.Group")
        Permission = apps.get_model("auth.Permission")
        Rotator = apps.get_model("tomato.Rotator")
        Stopset = apps.get_model("tomato.Stopset")
        StopsetRotator = apps.get_model("tomato.StopsetRotator")

        asset = ContentType.objects.get_for_model(Asset)
        asset_alternate = ContentType.objects.get_for_model(AssetAlternate)
        rotator = ContentType.objects.get_for_model(Rotator)
        stopset = ContentType.objects.get_for_model(Stopset)
        stopset_rotator = ContentType.objects.get_for_model(StopsetRotator)
        client_log_entry = ContentType.objects.get_for_model(ClientLogEntry)

        extra_perms = Asset._meta.permissions

        for name, content_types in (
            (EDIT_ALL_GROUP_NAME, (asset, asset_alternate, rotator, stopset, stopset_rotator)),
            (EDIT_ONLY_ASSETS_GROUP_NAME, (asset,)),
            (f"View and export {ClientLogEntry._meta.verbose_name_plural}", (client_log_entry,)),
        ):
            group, _ = Group.objects.get_or_create(name=name)
            group.permissions.add(
                *Permission.objects.filter(content_type__in=content_types).exclude(
                    codename__in=[codename for codename, _ in extra_perms]
                )
            )
            all_groups.append(group)

        group, _ = Group.objects.get_or_create(name="Modify configuration")
        # tomato comes after constance in INSTALLED_APPS, so this should always exist
        group.permissions.add(Permission.objects.get(codename="change_config"))
        all_groups.append(group)

        for codename, perm_name in extra_perms:
            group, _ = Group.objects.get_or_create(name=perm_name)
            group.permissions.add(Permission.objects.get(codename=codename))
            all_groups.append(group)

        Group.objects.exclude(id__in=[group.id for group in all_groups]).delete()
