from django.urls import path

from . import views

app_name = "portal"

urlpatterns = [
    path("healthz", views.healthz_view, name="healthz"),
    path("login", views.login_view, name="login"),
    path("login/", views.login_view, name="login_slash"),
    path("logout", views.logout_view, name="logout"),
    path("manual", views.manual_view, name="manual"),
    path("documentacao", views.documentation_view, name="documentacao"),
    path("configuracao", views.configuration_view, name="configuracao"),
    path("redirect/<str:page_name>", views.redirect_view, name="redirect"),
    path("", views.portal_home, name="home"),
]
