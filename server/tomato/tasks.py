import logging
import time

from huey import crontab

from django_file_form.models import TemporaryUploadedFile
from huey.contrib import djhuey
from user_messages import api as user_messages_api

from .utils import once_at_startup, pretty_delta


logger = logging.getLogger(__name__)


# TODO: retry?
@djhuey.db_task()
def process_asset(asset, user=None):
    begin = time.time()

    asset.refresh_from_db()
    asset.status = asset.Status.PROCESSING
    asset.save()

    asset.generate_md5sum()

    asset.status = asset.Status.READY
    asset.save()

    # TODO: delete asset if it doesn't process properly, error message
    # # "try again, or if the problem persists the have an administrator check the server logs"

    if user is not None:
        elapsed = time.time() - begin
        user_messages_api.success(user, f'Audio asset "{asset.name}" processed after {pretty_delta(elapsed)}!')

    return True


@djhuey.db_task()
def bulk_process_assets(assets, user=None):
    begin = time.time()
    process_calls = process_asset.map((asset, user) for asset in assets)
    print(process_calls.get(blocking=True))
    elapsed = time.time() - begin
    if user:
        user_messages_api.success(
            user, f"Bulk processed {len(assets)} audio assets processed after {pretty_delta(elapsed)}!"
        )


@djhuey.db_periodic_task(once_at_startup(crontab(hour="*/6", minute="5")))
def delete_unused_uploaded_files():
    deleted_files = TemporaryUploadedFile.objects.delete_unused_files()
    if not deleted_files:
        logger.info("No files deleted")
    else:
        logger.info("Deleted files: {', '.join(deleted_files)}")
