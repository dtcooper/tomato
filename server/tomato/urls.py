import re

from django.conf import settings
from django.urls import include, path, re_path
from django.views.static import serve

from tomato import views
from tomato.admin import admin_site


urlpatterns = [
    path("dismiss-message", views.dismiss_message, name="dismiss_message"),
    path("upload/", include("django_file_form.urls")),
    re_path("^server-logs/", views.server_logs, name="server_logs"),
]

if settings.DEBUG:
    urlpatterns.append(path("__debug__/", include("debug_toolbar.urls")))

if settings.DEBUG or settings.STANDALONE:
    urlpatterns.append(
        re_path(
            r"^%s(?P<path>.*)$" % re.escape(settings.MEDIA_URL.lstrip("/")),
            serve,
            {"document_root": settings.MEDIA_ROOT},
        )
    )

# Catch-all in admin, so it should be last
urlpatterns.append(path("", admin_site.urls))
