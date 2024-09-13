from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.urls import include, path, re_path

from tomato import views
from tomato.admin import admin_site
from tomato.constants import SUBMIT_URL_PREFIX


urlpatterns = [
    path("dismiss_message", views.dismiss_message, name="dismiss_message"),
    path("upload/", include("django_file_form.urls")),
    re_path("^server_logs/", views.server_logs, name="server_logs"),
]

if settings.SUBMIT_ENABLED:
    urlpatterns.append(path(SUBMIT_URL_PREFIX.removeprefix("/"), include("tomato.submit.urls")))

if settings.PASSWORD_RESET_EMAIL_ENABLED:
    urlpatterns.extend([
        path(
            "password_reset/",
            auth_views.PasswordResetView.as_view(extra_context={"site_header": admin_site.site_header}),
            name="admin_password_reset",
        ),
        path(
            "password_reset/done/",
            auth_views.PasswordResetDoneView.as_view(extra_context={"site_header": admin_site.site_header}),
            name="password_reset_done",
        ),
        path(
            "reset/<uidb64>/<token>/",
            auth_views.PasswordResetConfirmView.as_view(extra_context={"site_header": admin_site.site_header}),
            name="password_reset_confirm",
        ),
        path(
            "reset/done/",
            auth_views.PasswordResetCompleteView.as_view(extra_context={"site_header": admin_site.site_header}),
            name="password_reset_complete",
        ),
    ])

if settings.DEBUG:
    urlpatterns.append(path("json/", views.debug_json, name="debug_json")),
    urlpatterns.append(path("__debug__/", include("debug_toolbar.urls")))
    urlpatterns.extend(static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))

# Catch-all in admin, so it should be last
urlpatterns.append(path("", admin_site.urls))
