import logging

from .utils import notify_api_multiple, tomato_thread_local


logger = logging.getLogger(__name__)


class RequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request._notify_api_messages = []
        tomato_thread_local.request = request
        response = self.get_response(request)
        tomato_thread_local.request = None

        if request._notify_api_messages:
            notify_api_multiple(request._notify_api_messages, force=True)

        return response
