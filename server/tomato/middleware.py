import logging

from .utils import notify_api_local, notify_api_multiple


logger = logging.getLogger(__name__)


class DBNotifyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request._notify_api_messages = []
        notify_api_local.request = request
        response = self.get_response(request)
        notify_api_local.request = None

        if request._notify_api_messages:
            notify_api_multiple(request._notify_api_messages, force=True)

        return response
