from django.urls import path

from . import views


urlpatterns = [
    path("", views.LoginView.as_view(), name="user_submission_login"),
    path("create/", views.CreateView.as_view(), name="user_submission_create"),
    path("logout/", views.LogoutView.as_view(), name="user_submission_logout"),
    path("validate/<str:token>/", views.ValidateView.as_view(), name="user_submission_validate_token"),
]
