import logging
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
from .utils import mark_models_dirty, once_at_startup


logger = logging.getLogger(__name__)


@djhuey.db_task(context=True, retries=3, retry_delay=5)
def process_asset(
    asset, empty_name=False, user=None, no_success_message=False, skip_trim=False, mark_dirty=True, task=None
):
    def error(message):
        if user is not None:
            user_messages_api.error(
                user,
                f"{asset.name} {message} and was deleted. Check the file and try again. If this keeps happening,"
                " check the server logs.",
                deliver_once=False,
            )
        asset.delete()

    try:
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

        asset.status = asset.Status.READY
        asset.save(dont_overwrite_original_filename=True)
        if mark_dirty:
            mark_models_dirty()

        if not no_success_message and user is not None:
            user_messages_api.success(user, f'Audio asset "{asset.file.real_path.name}" processed!')

    except Exception:
        logger.exception("process_asset threw exception")
        if task is None or task.retries == 0:
            error("could not be processed")
        raise


@djhuey.db_task()
def bulk_process_assets(assets, user=None, skip_trim=False):
    for asset in assets:
        try:
            process_asset.call_local(
                asset, empty_name=True, user=user, no_success_message=True, skip_trim=skip_trim, mark_dirty=False
            )
        except Exception:
            pass

    mark_models_dirty()

    if user is not None:
        user_messages_api.success(user, f"Finished processing {len(assets)} audio assets.")


@djhuey.db_periodic_task(once_at_startup(crontab(hour="*/6", minute="5")))
def cleanup():
    # Delete unused uploaded files
    deleted_files = TemporaryUploadedFile.objects.delete_unused_files()
    if not deleted_files:
        logger.info("No files deleted")
    else:
        logger.info(f"Deleted files: {', '.join(deleted_files)}")

    # Cleanup read messages
    deleted_messages, _ = UserMessage.objects.filter(delivered_at__isnull=False).delete()
    logger.info(f"Deleted {deleted_messages} already delievered user message(s)")
