from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path, re_path

from tomato import views
from tomato.admin import admin_site


urlpatterns = [
    path("dismiss_message", views.dismiss_message, name="dismiss_message"),
    path("upload/", include("django_file_form.urls")),
    re_path("^server_logs/", views.server_logs, name="server_logs"),
]

if settings.DEBUG:
    urlpatterns.append(path("json/", views.debug_json, name="debug_json")),
    urlpatterns.append(path("__debug__/", include("debug_toolbar.urls")))
    urlpatterns.extend(static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))

# Catch-all in admin, so it should be last
urlpatterns.append(path("", admin_site.urls))
