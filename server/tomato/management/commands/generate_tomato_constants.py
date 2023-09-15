import json

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.html import strip_tags

from tomato.models import ClientLogEntry


class Command(BaseCommand):
    help = "Update constants file with latest data from server"
    CONSTANTS_FILE_PATH = settings.PROJECT_DIR / "constants.json"

    def add_arguments(self, parser):
        parser.add_argument("-b", "--bump-protocol-version", action="store_true", help="Bump protocol version.")

    def handle(self, *args, **options):
        with open(self.CONSTANTS_FILE_PATH, "r") as file:
            constants = json.load(file)

        if options["bump_protocol_version"]:
            constants["protocol_version"] += 1

        constants.update(
            {
                "client_log_entry_types": sorted(ClientLogEntry.Type.values),
                "settings_descriptions": {
                    key: strip_tags(value[1].replace("<br>", " "))
                    for key, value in settings.CONSTANCE_CONFIG.items()
                    if key not in settings.CONSTANCE_SERVER_ONLY_SETTINGS
                },
            }
        )

        with open(self.CONSTANTS_FILE_PATH, "w") as file:
            json.dump(constants, file, indent=2, sort_keys=True)
            file.write("\n")
        self.stdout.write(self.style.SUCCESS("Successfully wrote constants.json file!"))
