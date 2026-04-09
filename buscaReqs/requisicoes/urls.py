from django.urls import path

from . import views

app_name = "requisicoes"

urlpatterns = [
    path("", views.homepage, name="index"),
    path("importar/", views.upload_requerimentos, name="importar"),
    path("configurar/", views.configure, name="configure"),
    path("api/config/", views.configuration_detail, name="config-detail"),
]
