import json

from django.conf import settings
from django.contrib.auth import authenticate
from django.db.models import Prefetch
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.http.request import split_domain_port
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from constance import config as constance_config

from .constants import SCHEMA_VERSION
from .models import Asset, Rotator, Stopset, User


def user_from_request(request):
    auth_token = request.headers.get("X-Access-Token") or request.GET.get("access_token")
    if auth_token is not None:
        return User.validate_access_token(auth_token)


@csrf_exempt
@require_POST
def access_token(request):
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


@csrf_exempt
def sync(request):
    user = user_from_request(request)
    if not user and not settings.DEBUG:
        return HttpResponseForbidden()

    error = None

    if request.method == "POST":
        try:
            json_data = json.loads(request.body)
        except json.JSONDecodeError:
            error = "Invalid JSON body."
        else:
            if isinstance(json_data, list):
                for client_log_entry in json_data:
                    pass  # TODO process log entries
            else:
                error = "Invalid JSON body."

    log_status = {"success": True} if error is None else {"success": False, "error": error}

    rotators = list(Rotator.objects.order_by("id"))
    rotator_ids = [r.id for r in rotators]
    # Only select from rotators that existed at time query was made
    prefetch_qs = Rotator.objects.only("id").filter(id__in=rotator_ids)
    assets = (
        Asset.objects.prefetch_related(Prefetch("rotators", prefetch_qs.order_by("id")))
        .filter(status=Asset.Status.READY)
        .order_by("id")
    )
    stopsets = Stopset.objects.prefetch_related(
        Prefetch("rotators", prefetch_qs.order_by("stopsetrotator__id"))
    ).order_by("id")

    config = {key: getattr(constance_config, key) for key in dir(constance_config)}
    config["SINGLE_PLAY_ROTATORS"] = sorted(set(map(int, config["SINGLE_PLAY_ROTATORS"])) & set(rotator_ids))

    return JsonResponse(
        {
            **log_status,
            "assets": [a.serialize() for a in assets],
            "rotators": [r.serialize() for r in rotators],
            "stopsets": [s.serialize() for s in stopsets],
            "schema_version": SCHEMA_VERSION,
            "config": config,
        }
    )


def ping(request):
    user = user_from_request(request)
    return JsonResponse({"success": True, "access_token_valid": user is not None, "username": user and user.username})


def server_logs(request):
    if request.user.is_superuser:
        if settings.DEBUG:
            domain, _ = split_domain_port(request.get_host())
            return HttpResponseRedirect(f"http://{domain}:{settings.DEBUG_LOGS_PORT}/server-logs")
        else:
            return HttpResponse(headers={"X-Accel-Redirect": f"/_internal{request.get_full_path()}"})
    else:
        return HttpResponseForbidden()
