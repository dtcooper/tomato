from django.apps import AppConfig, apps
from django.db.models import signals


class TomatoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tomato"
    verbose_name = "Radio automation"

    def ready(self):
        signals.post_migrate.connect(self.create_groups, sender=self)

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
        assets_name = Asset._meta.verbose_name_plural
        rotator_name = Rotator._meta.verbose_name_plural
        stopset_name = Stopset._meta.verbose_name_plural
        client_log_entry_name = ClientLogEntry._meta.verbose_name_plural

        asset = ContentType.objects.get_for_model(Asset)
        rotator = ContentType.objects.get_for_model(Rotator)
        stopset = ContentType.objects.get_for_model(Stopset)
        stopset_rotator = ContentType.objects.get_for_model(StopsetRotator)
        client_log_entry = ContentType.objects.get_for_model(ClientLogEntry)

        for name, content_types in (
            (f"Edit {assets_name}, {rotator_name} & {stopset_name}", (asset, rotator, stopset, stopset_rotator)),
            (f"Edit {assets_name}, but NOT {rotator_name} & {stopset_name}", (asset,)),
            (f"View and export {client_log_entry_name}", (client_log_entry,)),
        ):
            group, _ = Group.objects.get_or_create(name=name)
            group.permissions.add(*Permission.objects.filter(content_type__in=content_types))
            all_groups.append(group)

        group, _ = Group.objects.get_or_create(name="Modify configuration")
        # tomato comes after constance in INSTALLED_APPS, so this should always exist
        group.permissions.add(Permission.objects.get(codename="change_config"))
        all_groups.append(group)

        Group.objects.exclude(id__in=[group.id for group in all_groups]).delete()
