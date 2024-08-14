import decimal
import logging

from asgiref.sync import async_to_sync

from django.conf import settings
from django.db.models import Prefetch

from constance import config as constance_config
from constance.models import Constance

from .asset import Asset, AssetAlternate
from .rotator import Rotator
from .stopset import Stopset


logger = logging.getLogger(__name__)


async def get_config_async(key):
    try:
        obj = await Constance.objects.aget(key=key)
    except Constance.DoesNotExist:
        return settings.CONSTANCE_CONFIG[key][0]  # Default value
    else:
        return obj.value


async def get_constance_config_for_api():
    config = {
        key: await get_config_async(key)
        for key in dir(constance_config)
        if key not in settings.CONSTANCE_SERVER_ONLY_SETTINGS
    }

    reset_times = []
    try:
        if config["UI_MODE_RESET_TIMES"].strip() != "0":
            for reset_time in config["UI_MODE_RESET_TIMES"].strip().split("\n"):
                reset_time = reset_time.strip()
                if reset_time:
                    hour, minute = reset_time.split(":")
                    reset_times.append((int(hour), int(minute)))
    except Exception:
        logger.exception("Error parsing UI_MODE_RESET_TIMES. Sending empty list.")

    config.update({
        "UI_MODES": list(map(int, config["UI_MODES"])),
        "UI_MODE_RESET_TIMES": reset_times,
        "CLOCK": config["CLOCK"] or False,
    })
    config["_numeric"] = [key for key, value in config.items() if isinstance(value, decimal.Decimal)]
    return config


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
