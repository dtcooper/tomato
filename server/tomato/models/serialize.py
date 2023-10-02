import decimal

from asgiref.sync import sync_to_async

from django.conf import settings
from django.db.models import Prefetch

from constance import config as constance_config

from .asset import Asset
from .rotator import Rotator
from .stopset import Stopset


def get_constance_config():
    config = {
        key: getattr(constance_config, key)
        for key in dir(constance_config)
        if key not in settings.CONSTANCE_SERVER_ONLY_SETTINGS
    }

    reset_times = []
    if config["UI_MODE_RESET_TIMES"].strip() != "0":
        for reset_time in config["UI_MODE_RESET_TIMES"].strip().split("\n"):
            reset_time = reset_time.strip()
            if reset_time:
                hour, minute = reset_time.split(":")
                reset_times.append({"hour": int(hour), "minute": int(minute)})

    config.update({"UI_MODES": list(map(int, config["UI_MODES"])), "UI_MODE_RESET_TIMES": reset_times})
    config["_numeric"] = [key for key, value in config.items() if isinstance(value, decimal.Decimal)]
    return config


async def serialize_for_api():
    rotators = [rotator async for rotator in Rotator.objects.order_by("id")]
    rotator_ids = [r.id for r in rotators]
    # Only select from rotators that existed at time query was made
    prefetch_qs = Rotator.objects.only("id").filter(id__in=rotator_ids)
    assets = (
        Asset.objects.prefetch_related(Prefetch("rotators", prefetch_qs.order_by("id")))
        .filter(status=Asset.Status.READY)
        .order_by("id")
    )
    stopsets = Stopset.objects.prefetch_related(
        Prefetch("rotators", prefetch_qs.order_by("stopsetrotator__id"))
    ).order_by("id")

    return {
        "assets": [a.serialize() async for a in assets],
        "rotators": [r.serialize() for r in rotators],
        "stopsets": [s.serialize() async for s in stopsets],
        "config": await sync_to_async(get_constance_config)(),
    }
