from tomato.models import User


class AlwaysLoggedInMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user, _ = User.objects.get_or_create(username="admin", defaults={"password": "admin", "is_superuser": True})
        request.user = user
        return self.get_response(request)
