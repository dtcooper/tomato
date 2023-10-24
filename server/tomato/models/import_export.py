import datetime
import itertools
import json
import logging
from pathlib import Path
import shutil
import tempfile
import zipfile

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone

from ..tasks import bulk_process_assets
from .asset import Asset, AssetAlternate
from .rotator import Rotator
from .serialize import serialize_for_api_sync
from .stopset import Stopset, StopsetRotator


EXPORT_FORMAT = 1  # In case we break compatibility
EXPORT_FOLDER_NAME_PREFIX = "tomato-export-data"
REQUIRED_EMPTY_FOR_IMPORT_MODEL_CLASSES = (Asset, AssetAlternate, Rotator, Stopset, StopsetRotator)
logger = logging.getLogger(__name__)


class ImportTomatoDataException(Exception):
    pass


def export_data_as_zip(file):
    export_folder_name = Path(f"{EXPORT_FOLDER_NAME_PREFIX}-{timezone.localtime().strftime('%Y%m%d-%H%M%S')}")

    zip = zipfile.ZipFile(file, "w")

    metadata = serialize_for_api_sync(skip_config=True)
    # Remove IDs from all but rotators (only they are needed for import)
    for asset in metadata["assets"]:
        del asset["id"], asset["url"]
        for alternate in asset["alternates"]:
            del alternate["id"], alternate["url"]
    for stopset in metadata["stopsets"]:
        del stopset["id"]
    metadata["export_format"] = EXPORT_FORMAT

    zip.writestr(
        str(export_folder_name / "metadata.json"),
        f"{json.dumps(metadata, indent=2, sort_keys=True, cls=DjangoJSONEncoder)}\n",
    )

    media_root = Path(settings.MEDIA_ROOT)

    for n, asset in enumerate(metadata["assets"], 1):
        logger.info(f"Exporting {n}/{len(metadata['assets'])} assets...")
        for file in itertools.chain((asset,), asset["alternates"]):
            local_file_path = media_root / file["file"]
            export_file_path = export_folder_name / "assets" / file["file"]
            zip.write(str(local_file_path), str(export_file_path))

    zip.close()
    logger.info("Export done!")
    return f"{export_folder_name}.zip"


def import_data_from_zip(file, created_by=None):
    for model_cls in REQUIRED_EMPTY_FOR_IMPORT_MODEL_CLASSES:
        if model_cls.objects.exists():
            raise ImportTomatoDataException(f"can't import data when {model_cls._meta.verbose_name_plural} exist!")

    try:
        zip = zipfile.ZipFile(file)
    except zipfile.BadZipFile:
        raise ImportTomatoDataException("bad archive format!")

    stats = {"rotators": 0, "assets": 0, "stopsets": 0}

    with tempfile.TemporaryDirectory(delete=True) as temp_dir:
        temp_dir = Path(temp_dir)
        zip.extractall(str(temp_dir))

        temp_dir_contents = list(temp_dir.iterdir())
        if len(temp_dir_contents) != 1 or not temp_dir_contents[0].is_dir():
            raise ImportTomatoDataException("needs exactly one folder!")

        temp_dir = temp_dir_contents[0]
        metadata_file = temp_dir / "metadata.json"
        assets_prefix = temp_dir / "assets"
        media_root = Path(settings.MEDIA_ROOT)

        if not metadata_file.exists():
            raise ImportTomatoDataException("no metadata file!")

        with open(metadata_file, "r") as file:
            metadata = json.load(file)

        if metadata["export_format"] != EXPORT_FORMAT:
            raise ImportTomatoDataException("Invalid format version!")

        rotator_id_to_obj = {}
        for kwargs in metadata["rotators"]:
            rotator_id = kwargs.pop("id")
            rotator_id_to_obj[rotator_id] = Rotator.objects.create(created_by=created_by, **kwargs)
            stats["rotators"] += 1

        logger.info(f"Imported {stats['rotators']} rotators.")

        for kwargs in metadata["stopsets"]:
            rotators = [rotator_id_to_obj[rotator_id] for rotator_id in kwargs.pop("rotators")]
            stopset = Stopset.objects.create(created_by=created_by, **kwargs)
            for rotator in rotators:
                StopsetRotator.objects.create(stopset=stopset, rotator=rotator)
            stats["stopsets"] += 1

        logger.info(f"Imported {stats['stopsets']} stop sets.")

        assets_to_process = []
        for kwargs in metadata["assets"]:
            for file in itertools.chain((kwargs,), kwargs["alternates"]):
                destination_path = media_root / file["file"]
                destination_path.parent.mkdir(parents=True, exist_ok=True)  # Make sure parent dir exists
                shutil.move(assets_prefix / file["file"], destination_path)
                logger.info(f"Copying file for import: {file['file']}")

            kwargs.update(
                {
                    "md5sum": bytes.fromhex(kwargs["md5sum"]),
                    "duration": datetime.timedelta(seconds=kwargs["duration"]),
                }
            )
            alternates = kwargs.pop("alternates")
            rotators = [rotator_id_to_obj[rotator_id] for rotator_id in kwargs.pop("rotators")]
            asset = Asset(created_by=created_by, **kwargs)
            asset.clean()
            asset.save(dont_overwrite_original_filename=True)
            asset.rotators.add(*rotators)
            assets_to_process.append(asset)
            stats["assets"] += 1

            if alternates:
                for alternate_kwargs in alternates:
                    alternate_kwargs.update(
                        {
                            "md5sum": bytes.fromhex(alternate_kwargs["md5sum"]),
                            "duration": datetime.timedelta(seconds=alternate_kwargs["duration"]),
                        }
                    )
                    alternate = AssetAlternate(created_by=created_by, asset=asset, **alternate_kwargs)
                    alternate.clean()
                    alternate.save(dont_overwrite_original_filename=True)
                    assets_to_process.append(alternate)
                    stats["assets"] += 1

        bulk_process_assets(assets_to_process, user=created_by, skip_trim=True)

        return stats
