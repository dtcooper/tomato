import datetime

from huey import PriorityRedisHuey

from django_redis import get_redis_connection

from .constants import MODELS_DIRTY_REDIS_PUBSUB_KEY


# XXX unused?
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


def once_at_startup(crontab):
    needs_to_run = True

    def startup_crontab(*args, **kwargs):
        nonlocal needs_to_run
        if needs_to_run:
            needs_to_run = False
            return True
        else:
            return crontab(*args, **kwargs)

    return startup_crontab


def mark_models_dirty():
    conn = get_redis_connection()
    conn.publish(MODELS_DIRTY_REDIS_PUBSUB_KEY, str(datetime.datetime.now()))


class DjangoPriorityRedisHuey(PriorityRedisHuey):
    def __init__(self, *args, **kwargs):
        connection = get_redis_connection()
        kwargs["connection_pool"] = connection.connection_pool
        super().__init__(*args, **kwargs)
