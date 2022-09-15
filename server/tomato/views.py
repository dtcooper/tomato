from functools import wraps
import json

from django.contrib.auth import authenticate
from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .constants import SCHEMA_VERSION
from .models import Asset, Rotator, User


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


def require_auth_token(view_func):
    @wraps(view_func)
    def view(request, *args, **kwargs):
        auth_token = request.headers.get("X-Auth-Token") or request.GET.get("auth_token")
        if auth_token:
            user = User.get_user_for_auth_token(auth_token)
            if user is not None:
                return view_func(request, *args, **kwargs)
        return HttpResponseForbidden()

    return view


@json_post_view
def auth_token(request, json_data):
    username, password = json_data.get("username"), json_data.get("password")
    if username is not None and password is not None:
        user = authenticate(username=username, password=password)
        if user is not None:
            return {"auth_token": user.generate_auth_token()}
        else:
            return {"error": "Invalid username and password combination."}
    else:
        return {"error": "Please provide a username and password."}


@require_auth_token
def sync(request):
    response = {"schema_version": SCHEMA_VERSION}
    models = {
        "assets": Asset.objects.filter(enabled=True, status=Asset.Status.READY),
        "rotators": Rotator.objects.all(),
    }
    response = {key: [obj.serialize() for obj in objs] for key, objs in models.items()}
    response["schema_version"] = SCHEMA_VERSION
    return JsonResponse(response)
