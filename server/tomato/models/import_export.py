import itertools
import json
import logging
import shutil
from pathlib import Path
import tempfile
import zipfile
import datetime

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone

from ..tasks import bulk_process_assets

from .asset import Asset, AssetAlternate
from .rotator import Rotator
from .serialize import serialize_for_api_sync
from .stopset import Stopset, StopsetRotator


EXPORT_FOLDER_NAME_PREFIX = "tomato-export-data"
REQUIRED_EMPTY_FOR_IMPORT_MODEL_CLASSES = (Asset, AssetAlternate, Rotator, Stopset, StopsetRotator)
logger = logging.getLogger(__name__)


class ImportTomatoDataException(Exception):
    pass


def generate_metadata():
    rotators_id_to_names = {}
    metadata = {"rotators": {}, "stopsets": {}, "assets": []}

    data = serialize_for_api_sync()
    for entity in ("rotators", "stopsets"):
        for obj in data[entity]:
            name = obj.pop("name")
            if entity == "rotators":
                rotators_id_to_names[obj["id"]] = name
            else:
                obj["rotators"] = [rotators_id_to_names[id] for id in obj["rotators"]]
            del obj["id"]
            metadata[entity][name] = obj

    for asset in data["assets"]:
        asset["rotators"] = [rotators_id_to_names[id] for id in asset["rotators"]]
        del asset["file"]["url"]
        for alternate in asset["alternates"]:
            del alternate["url"]

        del asset["id"]
        metadata["assets"].append(asset)

    return metadata


def export_data_as_zip(file):
    export_folder_name = Path(f"{EXPORT_FOLDER_NAME_PREFIX}-{timezone.localtime().strftime('%Y%m%d-%H%M%S')}")

    zip = zipfile.ZipFile(file, "w")

    metadata = generate_metadata()
    zip.writestr(
        str(export_folder_name / "metadata.json"),
        f"{json.dumps(metadata, indent=2, sort_keys=True, cls=DjangoJSONEncoder)}\n",
    )

    media_root = Path(settings.MEDIA_ROOT)

    for n, asset in enumerate(metadata["assets"], 1):
        logger.info(f"Exporting {n}/{len(metadata['assets'])} assets...")
        for file in itertools.chain((asset["file"],), asset["alternates"]):
            local_file_path = media_root / file["filename"]
            export_file_path = export_folder_name / "assets" / file["filename"]
            zip.write(str(local_file_path), str(export_file_path))

    zip.close()
    logger.info("Export done!")
    return f"{export_folder_name}.zip"


def import_data_from_zip(file, created_by=None):
    # XXXXXXX
    for model_cls in REQUIRED_EMPTY_FOR_IMPORT_MODEL_CLASSES:
        model_cls.objects.all().delete()

    for model_cls in REQUIRED_EMPTY_FOR_IMPORT_MODEL_CLASSES:
        if model_cls.objects.exists():
            raise ImportTomatoDataException(f"can't import data when {model_cls._meta.verbose_name_plural} exist!")

    try:
        zip = zipfile.ZipFile(file)
    except zipfile.BadZipFile:
        raise ImportTomatoDataException("bad archive format!")
    
    import_info = {"rotators": 0, "assets": 0, "stopsets": 0}

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
        
        rotator_names_to_objs = {}
        for name, kwargs in metadata["rotators"].items():
            rotator = Rotator.objects.create(name=name, created_by=created_by, **kwargs)
            rotator_names_to_objs[name] = rotator
            import_info["rotators"] += 1
        
        logger.info(f"Imported {import_info['rotators']} rotators.")

        for name, kwargs in metadata["stopsets"].items():
            rotators = [rotator_names_to_objs[rotator_name] for rotator_name in kwargs.pop("rotators")]
            stopset = Stopset.objects.create(name=name, created_by=created_by, **kwargs)
            for rotator in rotators:
                StopsetRotator.objects.create(stopset=stopset, rotator=rotator)
            import_info["stopsets"] += 1

        logger.info(f"Imported {import_info['stopsets']} stop sets.")

        assets = []
        for kwargs in metadata["assets"]:
            for file in itertools.chain((kwargs["file"],), kwargs["alternates"]):
                shutil.move(assets_prefix / file["filename"], media_root / file["filename"])
                logger.info(f"Copying file for import: {file['filename']}")
            
            file = kwargs.pop("file")
            kwargs.update({
                "file": file["filename"],
                "filesize": file["size"],
                "md5sum": bytes.fromhex(file["md5sum"]),
                "original_filename": file["original_filename"],
                "duration": datetime.timedelta(seconds=kwargs["duration"]),
            })
            alternates = kwargs.pop("alternates")
            rotators = [rotator_names_to_objs[rotator_name] for rotator_name in kwargs.pop("rotators")]
            asset = Asset(created_by=created_by, **kwargs)
            asset.clean()
            asset.save(dont_overwrite_original_filename=True)
            asset.rotators.add(*rotators)
            assets.append(asset)

            if alternates:
                for alternate_kwargs in alternates:
                    alternate = AssetAlternate(
                        created_by=created_by,
                        asset=asset,
                        duration=datetime.timedelta(seconds=alternate_kwargs["duration"]),
                        file=alternate_kwargs["filename"],
                        filesize=alternate_kwargs["size"],
                        md5sum=bytes.fromhex(alternate_kwargs["md5sum"]),
                        original_filename=alternate_kwargs["original_filename"],
                    )
                    alternate.clean()
                    alternate.save(dont_overwrite_original_filename=True)
                    assets.append(alternate)


            

        bulk_process_assets(assets, user=created_by, skip_trim=True)

        return import_info
    
