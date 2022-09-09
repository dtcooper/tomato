from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create necessary groups for users"

    def handle(self, *args, **options):
        group, _ = Group.objects.get_or_create(name="Modify site-wide configuration")
        group.permissions.add(Permission.objects.get(codename="change_config"))

        self.stdout.write("Groups successfully created!")
