from asgiref.sync import async_to_sync

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.http.request import split_domain_port
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from user_messages.models import Message

from .models import serialize_for_api


def server_logs(request):
    if request.user.is_superuser:
        if settings.DEBUG and not request.is_secure():
            domain, _ = split_domain_port(request.get_host())
            return HttpResponseRedirect(f"http://{domain}:{settings.DEBUG_LOGS_PORT}/server-logs/")
        else:
            return HttpResponse(headers={"X-Accel-Redirect": f"/_internal{request.get_full_path()}"})
    else:
        return HttpResponseForbidden()


@require_POST
def dismiss_message(request):
    if not request.user.is_authenticated:
        raise HttpResponseForbidden()

    message = get_object_or_404(Message, user=request.user, id=request.POST.get("id"))
    message.delivered_at = timezone.now()
    message.save()

    return HttpResponse(status=204)  # No content


def debug_json(request):
    if request.user.is_superuser:
        return JsonResponse(async_to_sync(serialize_for_api)())
    else:
        return HttpResponseForbidden()
