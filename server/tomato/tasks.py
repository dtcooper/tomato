import logging
import os
from pathlib import Path
import tempfile

from huey import crontab

from django.core.files import File

from constance import config
from django_file_form.models import TemporaryUploadedFile
from huey.contrib import djhuey
from user_messages import api as user_messages_api
from user_messages.models import Message as UserMessage

from .ffmpeg import ffmpeg_convert, ffprobe
from .models import SavedAssetFile
from .utils import (
    block_pending_notify_api_messages,
    once_at_startup,
    unblock_and_flush_blocked_pending_notify_api_messages,
)


logger = logging.getLogger(__name__)


@djhuey.db_task(context=True, retries=3, retry_delay=5)
def process_asset(asset, empty_name=False, user=None, from_bulk=False, skip_trim=False, task=None):
    def error(message):
        if user is not None:
            user_messages_api.error(
                user,
                f"{asset.name} {message} and was deleted. Check the file and try again. If this keeps happening,"
                " check the server logs.",
                deliver_once=False,
            )
        # Actually delete it from DB
        asset.delete()

    try:
        if not from_bulk:
            block_pending_notify_api_messages()

        asset.refresh_from_db()
        logger.info(f"Processing {asset.name}")
        asset.status = asset.Status.PROCESSING
        asset.save()
        asset.pre_process_md5sum = asset.generate_md5sum()
        asset.save()

        ffprobe_data = ffprobe(asset.file.real_path)
        if not ffprobe_data:
            error("does not appear to contain any audio")
            return

        asset.duration = ffprobe_data.duration

        if config.EXTRACT_METADATA_FROM_FILE and empty_name:
            if ffprobe_data.title:
                asset.name = ffprobe_data.title

        infile = asset.file.real_path
        if ffprobe_data.format != "mp3" or (config.TRIM_SILENCE and not skip_trim):
            with tempfile.TemporaryDirectory() as temp_dir:
                outfile = Path(temp_dir) / "out.mp3"
                if not ffmpeg_convert(infile, outfile):
                    raise Exception("ffmpeg threw an error!")

                infile.unlink(missing_ok=True)
                with open(outfile, "rb") as f:
                    asset.file.save(Path(asset.file.name).with_suffix(".mp3"), File(f), save=False)

            ffprobe_data = ffprobe(asset.file.real_path)

        asset.duration = ffprobe_data.duration
        asset.md5sum = asset.generate_md5sum()
        asset.filesize = os.path.getsize(asset.file.real_path)

        asset.status = asset.Status.READY
        asset.save(dont_overwrite_original_filename=True)
        try:
            SavedAssetFile.objects.update_or_create(
                file=asset.file, defaults={"original_filename": asset.original_filename}
            )
        except SavedAssetFile.MultipleObjectsReturned:
            logger.exception("Multiple SaveAssetFile objects returned")

        if not from_bulk and user is not None:
            user_messages_api.success(user, f'Audio asset "{asset.name}" successfully processed!')

    except Exception:
        logger.exception("process_asset threw exception")
        if task is None or task.retries == 0:
            error("could not be processed")
        raise
    finally:
        if not from_bulk:
            unblock_and_flush_blocked_pending_notify_api_messages()


@djhuey.db_task()
def bulk_process_assets(assets, user=None, skip_trim=False):
    try:
        block_pending_notify_api_messages()

        for n, asset in enumerate(assets):
            logger.info(f"Bulk processing {n}/{len(assets)} assets...")
            try:
                process_asset.call_local(asset, empty_name=True, user=user, from_bulk=True, skip_trim=skip_trim)
            except Exception:
                pass

        if user is not None:
            user_messages_api.success(user, f"Finished processing {len(assets)} audio assets.")
    finally:
        unblock_and_flush_blocked_pending_notify_api_messages()


@djhuey.db_periodic_task(once_at_startup(crontab(hour="*/6", minute="5")))
def cleanup():
    # Delete unused uploaded files
    deleted_files = TemporaryUploadedFile.objects.delete_unused_files()
    logger.info(
        f"Deleted temporary files: {', '.join(deleted_files)}" if deleted_files else "No temporary files deleted"
    )

    # Cleanup read messages
    deleted_messages, _ = UserMessage.objects.filter(delivered_at__isnull=False).delete()
    logger.info(f"Deleted {deleted_messages} already delivered user messages")

    SavedAssetFile.cleanup_unreferenced_files()
