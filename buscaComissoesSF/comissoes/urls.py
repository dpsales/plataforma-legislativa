from django.urls import path

from . import views

app_name = "comissoes"

urlpatterns = [
    path("", views.index, name="index"),
    path("api/proposicoes/", views.propositions_api, name="propositions-api"),
    path("export/xlsx/", views.export_xlsx, name="export-xlsx"),
    path("configurar/", views.configure_commissions, name="configure"),
]
