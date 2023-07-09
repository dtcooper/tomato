import datetime

from django_redis import get_redis_connection

from .constants import MODELS_DIRTY_REDIS_KEY


class DirtyModelsToRedisMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request._models_dirty = False
        response = self.get_response(request)

        if request._models_dirty:
            conn = get_redis_connection()
            conn.lpush(MODELS_DIRTY_REDIS_KEY, str(datetime.datetime.now()))

        return response
