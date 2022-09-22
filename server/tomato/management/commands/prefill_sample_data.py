import json
from pathlib import Path
import shutil
import tempfile
from urllib.parse import urlparse
import zipfile

import requests

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from tomato.models import Asset, Rotator, Stopset, StopsetRotator
from tomato.tasks import process_asset


SAMPLE_DATA_URL = "https://tomato.nyc3.digitaloceanspaces.com/bmir-sample-assets.zip"
ALL_MODELS_TEXT = "all audio assets, rotators and stop sets"


class Command(BaseCommand):
    help = "Setup with sample assets"

    def add_arguments(self, parser):
        parser.add_argument("--delete-all", action="store_true", help=f"Delete {ALL_MODELS_TEXT} before proceeding")
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            help="Don't prompt user when running with --delete-all",
        )

    def handle(self, *args, **options):
        if options["delete_all"]:
            if (
                options["interactive"]
                and input(f"Are you SURE you want to delete {ALL_MODELS_TEXT} [y/N]? ")[:1].lower() != "y"
            ):
                self.stdout.write(self.style.ERROR("Aborting..."))
                return

            for model_cls in (Asset, Rotator, Stopset):
                model_cls.objects.all().delete()

            self.stdout.write(f"Deleted {ALL_MODELS_TEXT}!")

        self.stdout.write(f"Downloading {SAMPLE_DATA_URL}...")
        for model_cls in (Asset, Rotator, Stopset):
            if model_cls.objects.exists():
                raise CommandError(f"One or more {model_cls._meta.verbose_name_plural} already exists! Exiting.")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            zip_filename = temp_dir / Path(urlparse(SAMPLE_DATA_URL).path).name

            with requests.get(SAMPLE_DATA_URL, stream=True) as response:
                with open(zip_filename, "wb") as zip_file:
                    shutil.copyfileobj(response.raw, zip_file)

            print("Extract archive...")
            with zipfile.ZipFile(zip_filename, "r") as archive:
                archive.extractall(temp_dir)

            temp_dir = temp_dir / zip_filename.with_suffix("").name

            print("Loading metadata...")
            with open(temp_dir / "metadata.json", "r") as metadata_file:
                metadata = json.load(metadata_file)

            rotator_names = [d.name for d in temp_dir.iterdir() if d.is_dir()]

            mp3_dir = Path(settings.MEDIA_ROOT) / "prefill"
            mp3_dir.mkdir(parents=True, exist_ok=True)
            rotators = {}

            for rotator_name in rotator_names:
                rotator_dir = temp_dir / rotator_name
                rotator = rotators[rotator_name] = Rotator.objects.create(
                    name=rotator_name,
                    color=metadata["rotator_colors"][rotator_name],
                )

                for mp3_tmp_filename in rotator_dir.iterdir():
                    mp3_filename = mp3_dir / mp3_tmp_filename.name
                    print(f"Importing {mp3_filename.name}...")

                    shutil.move(mp3_tmp_filename, mp3_filename)

                    asset = Asset(file=f"prefill/{mp3_filename.name}")
                    asset.clean()
                    asset.save()
                    asset.rotators.add(rotator)
                    process_asset(asset)

            for stopset_name, rotator_names in metadata["stopsets"].items():
                stopset = Stopset.objects.create(
                    name=stopset_name,
                )
                for rotator_name in rotator_names:
                    StopsetRotator.objects.create(
                        stopset=stopset,
                        rotator=rotators[rotator_name],
                    )
