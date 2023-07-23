from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.http.request import split_domain_port
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from user_messages.models import Message


def server_logs(request):
    if request.user.is_superuser and settings.DEBUG_LOGS_PORT is not None:
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
