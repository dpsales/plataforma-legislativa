from django.urls import path

from . import views

app_name = "pesos"

urlpatterns = [
    path("configurar/", views.index, name="index"),
]
