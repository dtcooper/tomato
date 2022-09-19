from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from tomato import views


urlpatterns = [
    path("auth/", views.access_token, name="access_token"),
    path("sync/", views.sync),
]

if settings.DEBUG:
    urlpatterns.append(path("__debug__/", include("debug_toolbar.urls")))

# Catch-all in admin, so it should be last
urlpatterns.append(path("", admin.site.urls))
