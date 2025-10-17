from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth
from django.urls import include, path, re_path

from .admin import admin_site
from .submit.constants import SUBMIT_URL_PREFIX
from .views import debug_json, dismiss_message, server_logs


SUBMIT_URL_PREFIX_RE = rf"(?:{SUBMIT_URL_PREFIX}/)?"


urlpatterns = [
    path("dismiss_message", dismiss_message, name="dismiss_message"),
    re_path(rf"{SUBMIT_URL_PREFIX_RE}upload/", include("django_file_form.urls")),
    re_path(rf"{SUBMIT_URL_PREFIX_RE}captcha/", include("captcha.urls")),
    re_path("^server_logs/", server_logs, name="server_logs"),
]

if settings.EMAIL_ENABLED:
    kwargs = {"extra_context": {"site_header": lambda: admin_site.site_header}}  # lambda since it'll call constance
    urlpatterns.extend([
        path("password_reset/", auth.PasswordResetView.as_view(**kwargs), name="admin_password_reset"),
        path("password_reset/done/", auth.PasswordResetDoneView.as_view(**kwargs), name="password_reset_done"),
        path("reset/<uidb64>/<token>/", auth.PasswordResetConfirmView.as_view(**kwargs), name="password_reset_confirm"),
        path("reset/done/", auth.PasswordResetCompleteView.as_view(**kwargs), name="password_reset_complete"),
    ])
    del kwargs

if settings.DEBUG:
    urlpatterns.extend([
        path("json/", debug_json, name="debug_json"),
        re_path(rf"{SUBMIT_URL_PREFIX_RE}__debug__/", include("debug_toolbar.urls")),
    ])
    urlpatterns.extend(static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))

# Catch-all in admin, so it should be last
urlpatterns.extend([
    path(rf"{SUBMIT_URL_PREFIX}/", include("tomato.submit.urls")),
    path("", admin_site.urls),
])
