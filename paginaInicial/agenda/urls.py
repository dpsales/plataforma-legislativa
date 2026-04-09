from django.urls import path
from . import views

app_name = 'agenda'

urlpatterns = [
    path('semanal/', views.AgendaSemanalView.as_view(), name='semanal'),
    path('favorito/adicionar/', views.AdicionarFavoritoView.as_view(), name='adicionar_favorito'),
    path('favorito/remover/', views.RemoverFavoritoView.as_view(), name='remover_favorito'),
]
