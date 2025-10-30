from django.urls import path
from .views import (
    apply_from_program, apply_generic, thanks,
    admissions_json, admissions_partial,
    AdmissionListView, AdmissionDetailView,
    AdmissionCreateView, AdmissionUpdateView, AdmissionDeleteView
)

app_name = "admissions"

urlpatterns = [
    # Public
    path("apply/<slug:slug>/", apply_from_program, name="apply_from_program"),
    path("apply/", apply_generic, name="apply_generic"),
    path("thanks/<str:ref_code>/", thanks, name="thanks"),

    # API / AJAX
    path("json/", admissions_json, name="admissions_json"),
    path("partial/", admissions_partial, name="admissions_partial"),

    # Admin CRUD
    path("admin/list/", AdmissionListView.as_view(), name="admin_list"),
    path("admin/create/", AdmissionCreateView.as_view(), name="admin_create"),
    path("admin/<str:ref_code>/", AdmissionDetailView.as_view(), name="admin_detail"),
    path("admin/<str:ref_code>/edit/", AdmissionUpdateView.as_view(), name="admin_edit"),
    path("admin/<str:ref_code>/delete/", AdmissionDeleteView.as_view(), name="admin_delete"),
]
