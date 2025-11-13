from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(("comissoes.urls", "comissoes"), namespace="comissoes_sf")),
]
