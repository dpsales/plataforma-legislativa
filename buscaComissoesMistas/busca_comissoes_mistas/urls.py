from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(("comissoes_mistas.urls", "comissoes_mistas"), namespace="comissoes_mistas")),
]
