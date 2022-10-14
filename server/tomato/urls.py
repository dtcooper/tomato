from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path, re_path

from tomato import views
from tomato.admin import admin_site


urlpatterns = [
    path("auth/", views.access_token, name="access_token"),
    path("sync/", views.sync, name="sync"),
    path("ping/", views.ping, name="ping"),
    re_path("^server-logs", views.server_logs, name="server_logs"),
    path("upload/", include("django_file_form.urls")),
]

if settings.DEBUG:
    urlpatterns.append(path("__debug__/", include("debug_toolbar.urls")))
    urlpatterns.extend(static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))

# Catch-all in admin, so it should be last
urlpatterns.append(path("", admin_site.urls))