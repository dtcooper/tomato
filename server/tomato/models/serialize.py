from asgiref.sync import sync_to_async

from django.conf import settings
from django.db.models import Prefetch

from constance import config as constance_config

from .asset import Asset
from .rotator import Rotator
from .stopset import Stopset


def get_constance_config(valid_rotator_ids):
    config = {key: getattr(constance_config, key) for key in dir(constance_config)}
    config["SINGLE_PLAY_ROTATORS"] = sorted(set(map(int, config["SINGLE_PLAY_ROTATORS"])) & set(valid_rotator_ids))
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
        "config": await sync_to_async(get_constance_config)(rotator_ids),
    }
