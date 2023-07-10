import pickle

from django.conf import settings
from django.db.models import Prefetch

from constance import config as constance_config

from ..constants import PROTOCOL_VERSION
from .asset import Asset
from .rotator import Rotator
from .stopset import Stopset


CONSTANCE_KEYS = dir(constance_config)
CONSTANCE_DEFAULTS = {key: settings.CONSTANCE_CONFIG[key][0] for key in CONSTANCE_KEYS}


async def serialize_for_api(async_redis_conn=None):
    if async_redis_conn is None:  # For testing only
        import redis.asyncio as redis

        async_redis_conn = redis.Redis(host="redis")

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

    # Manually get constance values asynchronously
    constance_values = await async_redis_conn.mget(*CONSTANCE_KEYS)
    config = {
        key: pickle.loads(value) if value is not None else CONSTANCE_DEFAULTS[key]
        for key, value in zip(CONSTANCE_KEYS, constance_values)
    }
    config["SINGLE_PLAY_ROTATORS"] = sorted(set(map(int, config["SINGLE_PLAY_ROTATORS"])) & set(rotator_ids))

    return {
        "assets": [a.serialize() async for a in assets],
        "rotators": [r.serialize() for r in rotators],
        "stopsets": [s.serialize() async for s in stopsets],
        "PROTOCOL_VERSION": PROTOCOL_VERSION,
        "config": config,
    }
