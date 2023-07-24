from django.conf import settings
from django.conf.urls.static import static
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
    urlpatterns.extend(static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))

if settings.STANDALONE:
    urlpatterns.append(re_path(r'^assets/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}))

# Catch-all in admin, so it should be last
urlpatterns.append(path("", admin_site.urls))
