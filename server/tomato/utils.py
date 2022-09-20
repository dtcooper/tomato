import datetime

from huey import PriorityRedisExpireHuey

from django.conf import settings

from django_redis import get_redis_connection
from s3file.storages_optimized import S3OptimizedUploadStorage

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


def json_data_context_processor(request):
    return {"COLORS": COLORS_DICT}


class DjangoPriorityRedisExpiryHuey(PriorityRedisExpireHuey):
    def __init__(self, *args, **kwargs):
        connection = get_redis_connection()
        kwargs["connection_pool"] = connection.connection_pool
        super().__init__(*args, **kwargs)


class PrivateMediaS3OptimizedUploadStorage(S3OptimizedUploadStorage):
    custom_domain = False

    def minio_url(self, name, parameters=None, expire=None, http_method=None):
        return super().url(name, parameters, expire, http_method)

    def url(self, name, parameters=None, expire=None, http_method=None):
        url = super().url(name, parameters, expire, http_method)
        # TODO use urllib.parse to do the swap here, like in monkey patching
        custom_url = url.replace(settings.AWS_S3_ENDPOINT_URL, f"https://{settings.DOMAIN_NAME}/s3")
        return custom_url
