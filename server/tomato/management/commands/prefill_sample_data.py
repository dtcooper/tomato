import json
from pathlib import Path
import shutil
import tempfile
import time
from urllib.parse import urlparse
import zipfile

import requests

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from tomato.models import Asset, Rotator, Stopset, StopsetRotator, User
from tomato.tasks import bulk_process_assets


SAMPLE_DATA_URL = "https://tomato.nyc3.digitaloceanspaces.com/bmir-sample-assets.zip"
SAMPLE_DATA_FOLDER = Path(urlparse(SAMPLE_DATA_URL).path).with_suffix("").name
ALL_MODELS_TEXT = "audio assets, rotators and stop sets"


class Command(BaseCommand):
    help = "Setup project with sample assets"

    def add_arguments(self, parser):
        parser.add_argument("--delete-all", action="store_true", help=f"Delete all {ALL_MODELS_TEXT} before proceeding")
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            help="Don't prompt user when running with --delete-all",
        )
        parser.add_argument("--created-by", default=None, help="Username of the user to create assets with")
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
                and input(f"Are you SURE you want to delete all {ALL_MODELS_TEXT} [y/N]? ")[:1].lower() != "y"
            ):
                self.stdout.write(self.style.ERROR("Aborting..."))
                return

            for model_cls in (Asset, Rotator, Stopset):
                model_cls.objects.all().delete()

            self.stdout.write(self.style.WARNING(f"Deleted {ALL_MODELS_TEXT}!"))

        for model_cls in (Asset, Rotator, Stopset):
            if model_cls.objects.exists():
                raise CommandError(
                    f"One or more {ALL_MODELS_TEXT} already exists! Run with --delete-all to delete them. Exiting."
                )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)

            if options["zipfile"]:
                zip_filename = options["zipfile"]
                self.stdout.write(f"Using local archive {zip_filename}...")
            else:
                self.stdout.write(f"Downloading {SAMPLE_DATA_URL}...")
                zip_filename = (temp_dir / SAMPLE_DATA_FOLDER).with_stem(".zip")
                with requests.get(SAMPLE_DATA_URL, stream=True) as response:
                    with open(zip_filename, "wb") as zip_file:
                        shutil.copyfileobj(response.raw, zip_file)

            self.stdout.write("Extracting zip archive...")
            with zipfile.ZipFile(zip_filename, "r") as archive:
                archive.extractall(temp_dir)

            temp_dir = temp_dir / SAMPLE_DATA_FOLDER
            if not temp_dir.exists():
                raise CommandError(f"Archive didn't contain a folder named {SAMPLE_DATA_FOLDER}!")

            self.stdout.write("Loading metadata...")

            metadata_path = temp_dir / "metadata.json"
            if not metadata_path.exists():
                raise CommandError("No metadata JSON file found in archive!")

            with open(metadata_path, "r") as metadata_file:
                metadata = json.load(metadata_file)

            rotator_names = [d.name for d in temp_dir.iterdir() if d.is_dir()]
            num_audio_files = len(list(temp_dir.rglob("*/*.*")))

            mp3_dir = Path(settings.MEDIA_ROOT) / "prefill"
            shutil.rmtree(mp3_dir, ignore_errors=True)
            mp3_dir.mkdir(parents=True, exist_ok=True)
            rotators = {}
            num = 1

            assets = []

            for rotator_name in rotator_names:
                rotator_dir = temp_dir / rotator_name

                self.stdout.write(f"Creating rotator {rotator_name}...")
                rotator = rotators[rotator_name] = Rotator.objects.create(
                    name=rotator_name,
                    created_by=created_by,
                    color=metadata["rotator_colors"][rotator_name],
                )

                for mp3_tmp_filename in rotator_dir.iterdir():
                    mp3_filename = mp3_dir / mp3_tmp_filename.name
                    self.stdout.write(f" * {num}/{num_audio_files} - Importing {mp3_filename.name}...")

                    shutil.move(mp3_tmp_filename, mp3_filename)
                    asset = Asset(file=f"prefill/{mp3_filename.name}", created_by=created_by)
                    asset.clean()
                    asset.save()
                    asset.rotators.add(rotator)
                    assets.append(asset)
                    num += 1

            bulk_process_assets(assets, user=created_by)

        for stopset_name, rotator_names in metadata["stopsets"].items():
            self.stdout.write(f"Creating stop set {stopset_name} with {len(rotator_names)} rotators...")
            stopset = Stopset.objects.create(name=stopset_name, created_by=created_by)
            for rotator_name in rotator_names:
                StopsetRotator.objects.create(
                    stopset=stopset,
                    rotator=rotators[rotator_name],
                )

        self.stdout.write(self.style.SUCCESS(f"Done! Took {time.time() - before_time:.3f} seconds."))
