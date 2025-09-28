import json
import logging

from django.core.management.base import BaseCommand
from django.db import connection

from ...constants import POSTGRES_MESSAGES_CHANNEL
from ...utils import notify_api


SAMPLE_DATA_URL = "https://tomato.nyc3.digitaloceanspaces.com/bmir-sample-data-20240728-185614.zip"

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Test the DB changes notification that get published to the websocket API"

    def add_arguments(self, parser):
        parser.add_argument("--send", "-s", action="store_true", help="Send a notification instead of receiving them")
        parser.add_argument("--message", "-t", default="db-change", help="Message to send (default: db-change)")
        parser.add_argument("--data", default="null", help="Extra JSON data to send with test message (default: null)")

    def handle(self, *args, **options):
        if options["send"]:
            data = json.loads(options["data"])
            message = (options["message"], data)
            logger.info(f"Sending test message: {message}")
            notify_api(*message, force=True)
        else:
            cursor = connection.cursor()
            cursor.execute(f"LISTEN {POSTGRES_MESSAGES_CHANNEL}")
            logger.info(f"Listening to Postgres channel: {POSTGRES_MESSAGES_CHANNEL}")
            try:
                for notification in connection.connection.notifies():
                    try:
                        payload = json.loads(notification.payload)
                    except Exception:
                        logger.warning("Got exception parsing paylot", exc_info=True)
                    else:
                        logger.info(f"Received message payload: {payload}")
            except KeyboardInterrupt:
                logger.warning("Got keyboard interrupt. Exiting.")
