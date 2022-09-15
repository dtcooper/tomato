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
        Group = apps.get_model("auth.Group")
        Permission = apps.get_model("auth.Permission")
        ContentType = apps.get_model("contenttypes.ContentType")
        Asset = apps.get_model("tomato.Asset")
        StopSet = apps.get_model("tomato.StopSet")
        StopSetRotator = apps.get_model("tomato.StopSetRotator")
        Rotator = apps.get_model("tomato.Rotator")
        assets_name = Asset._meta.verbose_name_plural
        rotator_name = Rotator._meta.verbose_name_plural
        stopset_name = StopSet._meta.verbose_name_plural

        asset_content_type = ContentType.objects.get_for_model(Asset)
        all_content_types = (
            asset_content_type,
            ContentType.objects.get_for_model(Rotator),
            ContentType.objects.get_for_model(StopSet),
            ContentType.objects.get_for_model(StopSetRotator),
        )

        group, _ = Group.objects.get_or_create(name=f"Edit {assets_name}, {rotator_name} & {stopset_name}")
        group.permissions.add(*Permission.objects.filter(content_type__in=all_content_types))
        all_groups.append(group)

        group, _ = Group.objects.get_or_create(name=f"Edit {assets_name} ONLY, view {rotator_name} & {stopset_name}")
        group.permissions.add(
            *Permission.objects.filter(content_type__in=all_content_types, codename__startswith="view_")
        )
        group.permissions.add(*Permission.objects.filter(content_type=asset_content_type))
        all_groups.append(group)

        # group, _ = Group.objects.get_or_create(name='View and export Client Log Entries')
        # group.permissions.add(*Permission.objects.filter(content_type=log_entry))

        group, _ = Group.objects.get_or_create(name=f"View {assets_name}, {rotator_name} & {stopset_name}")
        group.permissions.add(
            *Permission.objects.filter(content_type__in=all_content_types, codename__startswith="view_")
        )
        all_groups.append(group)

        group, _ = Group.objects.get_or_create(name="Modify configuration")
        # tomato comes after constance in INSTALLED_APPS, so this should always exist
        group.permissions.add(Permission.objects.get(codename="change_config"))
        all_groups.append(group)

        Group.objects.exclude(id__in=[group.id for group in all_groups]).delete()
