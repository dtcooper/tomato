from django.contrib import admin
from django.urls import path


admin.site.site_url = None

urlpatterns = [
    path("", admin.site.urls),
]
