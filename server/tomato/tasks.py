import logging
import time

from huey.contrib import djhuey

from .models import Asset


logger = logging.getLogger(__name__)


@djhuey.task()
def process_asset(asset: Asset):
    asset.refresh_from_db()
    asset.status = Asset.Status.PROCESSING
    asset.save()


@djhuey.task()
def generate_peaks(asset: Asset):
    for i in range(5):
        logger.info(f"would generate peaks for {asset}...")
        time.sleep(1)
    print("done!")
