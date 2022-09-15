from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.utils.safestring import mark_safe

from constance.apps import ConstanceConfig

from tomato import views


admin.site.site_url = None
admin.site.site_title = admin.site.site_header = "Tomato Administration"
admin.site.index_title = None
admin.site.empty_value_display = mark_safe("<em>None</em>")
ConstanceConfig.verbose_name = "Settings"

urlpatterns = [
    path("auth/", views.auth_token),
    path("sync/", views.sync),
]

if settings.DEBUG:
    urlpatterns.append(path("__debug__/", include("debug_toolbar.urls")))

# Catch-all in admin, so it should be last
urlpatterns.append(path("", admin.site.urls))
