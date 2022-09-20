from functools import wraps
import json

from django.conf import settings
from django.contrib.auth import authenticate
from django.db.models import Prefetch
from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .constants import SCHEMA_VERSION
from .models import Asset, Rotator, Stopset, User


def json_post_view(view_func):
    @wraps(view_func)
    @csrf_exempt
    @require_POST
    def view(request, *args, **kwargs):
        try:
            json_data = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponseBadRequest()

        response = view_func(request, json_data, *args, **kwargs)
        response["status"] = "error" if "error" in response else "ok"
        return JsonResponse(response)

    return view


def require_access_token(view_func):
    @wraps(view_func)
    def view(request, *args, **kwargs):
        auth_token = request.headers.get("X-access-Token") or request.GET.get("access_token")
        if auth_token:
            user = User.get_user_for_auth_token(auth_token)
            if user is not None:
                return view_func(request, *args, **kwargs)
        elif settings.DEBUG and request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden()

    return view


@json_post_view
def access_token(request, json_data):
    username, password = json_data.get("username"), json_data.get("password")
    if username is not None and password is not None:
        user = authenticate(username=username, password=password)
        if user is not None:
            return {"access_token": user.generate_access_token()}
        else:
            return {"error": "Invalid username and password combination."}
    else:
        return {"error": "Please provide a username and password."}


@require_access_token
def sync(request):
    # TODO: gaurantee referential integrity... possibly with prefetch_related limiting an ID of rotators
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
