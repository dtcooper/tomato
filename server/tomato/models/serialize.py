import decimal
import logging

from asgiref.sync import async_to_sync, sync_to_async

from django.conf import settings
from django.db.models import Prefetch

from constance import config

from .asset import Asset, AssetAlternate
from .rotator import Rotator
from .stopset import Stopset


logger = logging.getLogger(__name__)


async def get_constance_config_for_api():
    # Get constance config values asynchronously
    all_config = await sync_to_async(
        lambda: {k: getattr(config, k) for k in dir(config) if k not in settings.CONSTANCE_SERVER_ONLY_SETTINGS}
    )()

    reset_times = []
    try:
        if all_config["UI_MODE_RESET_TIMES"].strip() != "0":
            for reset_time in all_config["UI_MODE_RESET_TIMES"].strip().split("\n"):
                reset_time = reset_time.strip()
                if reset_time:
                    hour, minute = reset_time.split(":")
                    reset_times.append((int(hour), int(minute)))
    except Exception:
        logger.exception("Error parsing UI_MODE_RESET_TIMES. Sending empty list.")

    all_config.update({
        "UI_MODES": list(map(int, all_config["UI_MODES"])),
        "UI_MODE_RESET_TIMES": reset_times,
        "CLOCK": all_config["CLOCK"] or False,
    })
    all_config["_numeric"] = [key for key, value in all_config.items() if isinstance(value, decimal.Decimal)]
    return all_config


async def serialize_for_api(*, skip_config=False, include_archived=False):
    rotators = [rotator async for rotator in Rotator.objects.order_by("id")]
    rotator_ids = [r.id for r in rotators]
    # Only select from rotators that existed at time query was made
    prefetch_qs = Rotator.objects.only("id").filter(id__in=rotator_ids)
    assets = (
        Asset.objects.prefetch_related(Prefetch("rotators", prefetch_qs.order_by("id")))
        .prefetch_related(
            Prefetch("alternates", AssetAlternate.objects.filter(status=AssetAlternate.Status.READY).order_by("id"))
        )
        .filter(status=Asset.Status.READY)
        .order_by("id")
    )
    if not include_archived:
        assets = assets.filter(archived=False)

    stopsets = Stopset.objects.prefetch_related(
        Prefetch("rotators", prefetch_qs.order_by("stopsetrotator__id"))
    ).order_by("id")

    data = {
        "assets": [a.serialize(alternates_already_filtered_by_prefetch=True) async for a in assets],
        "rotators": [r.serialize() for r in rotators],
        "stopsets": [s.serialize() async for s in stopsets],
    }
    if not skip_config:
        data["config"] = await get_constance_config_for_api()
    return data


serialize_for_api_sync = async_to_sync(serialize_for_api)
