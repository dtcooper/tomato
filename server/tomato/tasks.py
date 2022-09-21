import logging
import time

from huey import crontab

from django_file_form.models import TemporaryUploadedFile
from huey.contrib import djhuey
from user_messages import api as user_messages_api

from .utils import once_at_startup, pretty_delta


logger = logging.getLogger(__name__)


@djhuey.db_task()
def process_asset(asset, user=None):
    begin = time.time()

    asset.status = asset.Status.PROCESSING
    asset.save()

    time.sleep(3)

    asset.status = asset.Status.READY
    asset.save()

    if user is not None:
        elapsed = time.time() - begin
        user_messages_api.success(user, f'Audio asset "{asset.name}" processed after {pretty_delta(elapsed)}!')


@djhuey.db_periodic_task(once_at_startup(crontab(hour="*/6", minute="5")))
def delete_unused_uploaded_files():
    deleted_files = TemporaryUploadedFile.objects.delete_unused_files()
    if not deleted_files:
        logger.info("No files deleted")
    else:
        logger.info("Deleted files: {', '.join(deleted_files)}")
