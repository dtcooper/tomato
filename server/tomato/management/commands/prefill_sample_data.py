import argparse
from pathlib import Path
import tempfile
import time
from urllib.request import urlretrieve

from django.core.management.base import BaseCommand, CommandError

from tomato.models import REQUIRED_EMPTY_FOR_IMPORT_MODEL_CLASSES, User, import_data_from_zip


SAMPLE_DATA_URL = "https://tomato.nyc3.digitaloceanspaces.com/bmir-sample-data-20231023-185614.zip"


def show_download_progress(block_num, block_size, total_size):
    print(f"Retrieved {block_num * block_size / total_size * 100:.01f}%", end="\r", flush=True)


class Command(BaseCommand):
    help = "Setup project with sample assets"

    def add_arguments(self, parser):
        parser.add_argument("--delete-all", action="store_true", help="Delete all asset data before proceeding")
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            help="Don't prompt user when running with --delete-all",
        )
        parser.add_argument("--created-by", default=None, help="Username of the user to create assets with")
        parser.add_argument("--trim-if-enabled", action="store_true", help=argparse.SUPPRESS)
        parser.add_argument("zipfile", nargs="?", help="Optional path of zipfile, otherwise one will be downloaded")

    def handle(self, *args, **options):
        before_time = time.time()
        created_by = None

        if options["created_by"]:
            try:
                created_by = User.objects.get(username=options["created_by"])
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"User {options['created_by']} does not exist. Skipping..."))
                pass

        if options["delete_all"]:
            if (
                options["interactive"]
                and input("Are you SURE you want to delete all asset data before proceeding [y/N]? ")[:1].lower() != "y"
            ):
                self.stdout.write(self.style.ERROR("Aborting..."))
                return

            for model_cls in REQUIRED_EMPTY_FOR_IMPORT_MODEL_CLASSES:
                model_cls.objects.all().delete()

            self.stdout.write(self.style.WARNING("Deleted all asset data!"))

        for model_cls in REQUIRED_EMPTY_FOR_IMPORT_MODEL_CLASSES:
            if model_cls.objects.exists():
                raise CommandError(
                    f"One or more {model_cls._meta.verbose_name_plural} already exists! Run with --delete-all to delete"
                    " them. Exiting."
                )

        def download(zip_filename):
            with open(zip_filename, "rb") as file:
                return import_data_from_zip(file, created_by=created_by)

        if options["zipfile"]:
            zip_filename = options["zipfile"]
            self.stdout.write(f"Using local archive {zip_filename}...")
            stats = download(zip_filename)
        else:
            self.stdout.write(f"Downloading {SAMPLE_DATA_URL}...")
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_filename = Path(temp_dir) / "sample-data.zip"
                urlretrieve(SAMPLE_DATA_URL, zip_filename, reporthook=show_download_progress)
                print("\nDownloaded!")
                stats = download(zip_filename)

        self.stdout.write(f"Successfully imported {', '.join(f'{num} {entity}' for entity, num in stats.items())}!")
        self.stdout.write(self.style.SUCCESS(f"Done! Took {time.time() - before_time:.3f} seconds."))
