from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("page/<slug:slug>/", views.simple_page, name="page"),
    path("confidentialite/", views.privacy, name="privacy"),
    path("mentions-legales/", views.legal, name="legal"),
    path("plan-du-site/", views.sitemap_page, name="sitemap"),

]
