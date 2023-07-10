from .utils import mark_models_dirty


class DirtyModelsToRedisMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request._models_dirty = False
        response = self.get_response(request)

        if request._models_dirty:
            mark_models_dirty()

        return response
