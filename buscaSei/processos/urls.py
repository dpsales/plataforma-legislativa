from django.urls import path
from . import views

app_name = 'processos'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('buscar/', views.BuscaProcessoView.as_view(), name='buscar'),
    path('processo/<int:pk>/', views.DetalheProcessoView.as_view(), name='detalhe'),
    path('api/busca/', views.BuscaProcessoAPIView.as_view(), name='api_busca'),
]
