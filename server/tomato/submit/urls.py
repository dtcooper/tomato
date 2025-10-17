from django.http import Http404
from django.urls import path, re_path

from . import views


def catch_all_view(request, url):
    raise Http404(f"URL {url} not found in submit app!")  # Needed to prevent admin from matching our views


app_name = "submit"
urlpatterns = [
    path("", views.LandingView.as_view(), name="landing"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("verify/<token>/", views.VerifyView.as_view(), name="verify"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("create/", views.CreateView.as_view(), name="create"),
    re_path(r"(?P<url>.*)$", catch_all_view),
]
