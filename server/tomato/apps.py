from django.apps import AppConfig, apps
from django.db.models import signals


class TomatoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tomato"

    def ready(self):
        signals.post_migrate.connect(self.create_groups, sender=self)

    def create_groups(self, using=None, *args, **kwargs):
        all_groups = []
        Group = apps.get_model("auth.Group")
        Permission = apps.get_model("auth.Permission")

        group, _ = Group.objects.get_or_create(name="Modify configuration")
        # tomato comes after constance in INSTALLED_APPS, so this should always exist
        group.permissions.add(Permission.objects.get(codename="change_config"))
        all_groups.append(group)

        # print(Group.objects.exclude(id__in=all_groups))
