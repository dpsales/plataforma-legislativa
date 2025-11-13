from django.urls import path

from . import views

app_name = "monitoramento"

urlpatterns = [
    path("", views.index, name="index"),
    path("api/proposicoes/", views.propositions_api, name="propositions-api"),
    path("export/xlsx/", views.export_xlsx, name="export-xlsx"),
    path("export/docx/", views.export_docx, name="export-docx"),
    path("configurar/", views.configure_document, name="configure"),
    path("configurar/download/", views.download_document, name="download-document"),
    path("configurar/remover/<int:pk>/", views.delete_tracked, name="delete-tracked"),
]
