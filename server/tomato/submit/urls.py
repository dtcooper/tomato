from django.urls import path

from . import views


urlpatterns = [
    path("", views.LoginView.as_view(), name="user_submission_login"),
    path("logout/", views.LogoutView.as_view(), name="user_submission_logout"),
    path("validate/<str:token>/", views.ValidateView.as_view(), name="user_submission_validate_token"),
]
