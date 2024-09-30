from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth
from django.urls import include, path, re_path

from tomato.admin import admin_site
from tomato.constants import SUBMIT_URL_PREFIX
from tomato.views import debug_json, dismiss_message, server_logs


urlpatterns = [
    path("dismiss_message", dismiss_message, name="dismiss_message"),
    re_path("(?:submit/)?upload/", include("django_file_form.urls")),
    re_path("^server_logs/", server_logs, name="server_logs"),
]

if settings.EMAIL_ENABLED:
    kwargs = {"extra_context": {"site_header": admin_site.site_header}}
    urlpatterns.extend([
        path(SUBMIT_URL_PREFIX.removeprefix("/"), include("tomato.submit.urls")),
        path("password_reset/", auth.PasswordResetView.as_view(**kwargs), name="admin_password_reset"),
        path("password_reset/done/", auth.PasswordResetDoneView.as_view(**kwargs), name="password_reset_done"),
        path("reset/<uidb64>/<token>/", auth.PasswordResetConfirmView.as_view(**kwargs), name="password_reset_confirm"),
        path("reset/done/", auth.PasswordResetCompleteView.as_view(**kwargs), name="password_reset_complete"),
    ])
    del kwargs

if settings.DEBUG:
    urlpatterns.append(path("json/", debug_json, name="debug_json")),
    urlpatterns.append(re_path("(?:submit/)?__debug__/", include("debug_toolbar.urls")))
    urlpatterns.extend(static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))

# Catch-all in admin, so it should be last
urlpatterns.append(path("", admin_site.urls))
