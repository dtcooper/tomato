from functools import wraps
import json
import time
import random

from django.conf import settings
from django.contrib.auth import authenticate
from django.db.models import Prefetch
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseRedirect, JsonResponse, HttpResponseNotAllowed
from django.http.request import split_domain_port
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .constants import SCHEMA_VERSION
from .models import Asset, Rotator, Stopset, User


def user_from_request(request):
    auth_token = request.headers.get("X-access-Token") or request.GET.get("access_token")
    if auth_token:
        return User.validate_access_token(auth_token)


@csrf_exempt
def access_token(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed()

    try:
        json_data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest()

    username, password = json_data.get("username"), json_data.get("password")
    if username is not None and password is not None:
        user = authenticate(username=username, password=password)
        if user is not None:
            response = {"success": True, "access_token": user.generate_access_token()}
        else:
            response = {"success": False, "error": "Invalid username or password."}
    else:
        response = {"success": False, "error": "Invalid request."}
    return JsonResponse(response)


def sync(request):
    user = user_from_request(request)
    if not user and not settings.DEBUG:
        return HttpResponseForbidden()

    response = {"schema_version": SCHEMA_VERSION}
    models = {
        "assets": Asset.objects.prefetch_related("rotators").filter(status=Asset.Status.READY),
        "rotators": Rotator.objects.all(),
        "stopsets": Stopset.objects.prefetch_related(
            Prefetch("rotators", queryset=Rotator.objects.order_by("stopsetrotator__id"))
        ).all(),
    }
    response.update({key: [obj.serialize() for obj in qs] for key, qs in models.items()})
    return JsonResponse(response)


def ping(request):
    user = user_from_request(request)
    return JsonResponse({"success": True, "access_token_valid": user is not None})


def server_logs(request):
    if request.user.is_superuser:
        if settings.DEBUG:
            domain, _ = split_domain_port(request.get_host())
            return HttpResponseRedirect(f"http://{domain}:{settings.DEBUG_LOGS_PORT}/server-logs")
        else:
            return HttpResponse(headers={"X-Accel-Redirect": f"/_internal{request.get_full_path()}"})
    else:
        return HttpResponseForbidden()
