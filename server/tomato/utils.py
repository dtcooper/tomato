import datetime

from huey import PriorityRedisExpireHuey

from django_redis import get_redis_connection

from .constants import COLORS_DICT


def pretty_delta(td):
    if isinstance(td, (float, int)):
        td = datetime.timedelta(seconds=round(td))

    d = dict(days=td.days)
    d["hrs"], rem = divmod(td.seconds, 3600)
    d["min"], d["sec"] = divmod(rem, 60)

    if d["min"] == 0:
        fmt = "{sec} sec"
    elif d["hrs"] == 0:
        fmt = "{min} min {sec} sec"
    elif d["days"] == 0:
        fmt = "{hrs} hr(s) {min} min {sec} sec"
    else:
        fmt = "{days} day(s) {hrs} hr(s) {min} min {sec} sec"

    return fmt.format(**d)


def extra_context(request):
    return {"COLORS": COLORS_DICT}


class DjangoPriorityRedisExpiryHuey(PriorityRedisExpireHuey):
    def __init__(self, *args, **kwargs):
        connection = get_redis_connection()
        kwargs["connection_pool"] = connection.connection_pool
        super().__init__(*args, **kwargs)
