# programs/urls.py
from django.urls import path
from . import views

app_name = "programs"   # ⚠️ important

urlpatterns = [
    path("", views.program_list, name="program_list"),   # ← name doit être "program_list"
    path("<slug:slug>/", views.program_detail, name="program_detail"),
]
