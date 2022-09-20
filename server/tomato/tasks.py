import logging
import time

from huey.contrib import djhuey
from user_messages import api as user_messages_api

from .models import Asset
from .utils import pretty_delta


logger = logging.getLogger(__name__)


@djhuey.db_task()
def process_asset(asset: Asset, user=None):
    begin = time.time()
    asset.refresh_from_db()
    asset.status = Asset.Status.PROCESSING
    asset.save()

    time.sleep(2.65)

    asset.refresh_from_db()
    asset.status = Asset.Status.READY
    asset.save()

    if user is not None:
        elapsed = time.time() - begin
        user_messages_api.success(user, f'Audio asset "{asset.name}" processed after {pretty_delta(elapsed)}!')
