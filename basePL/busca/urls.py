from django.urls import path

from . import views

app_name = "busca"

urlpatterns = [
    path("", views.index, name="index"),
]
