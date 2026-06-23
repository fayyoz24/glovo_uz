from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    path("api/v1/", include([
        path("", include("apps.accounts.urls")),
        path("", include("apps.locations.urls")),
        path("", include("apps.merchants.urls")),
    ])),
]
