from tomato.models import User
from django.contrib.auth import login


class AlwaysLoggedInMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            user, _ = User.objects.get_or_create(username="admin", defaults={"password": "admin", "is_superuser": True})
            login(request, user)
        return self.get_response(request)
