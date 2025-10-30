# masters/api_director/urls.py
from django.urls import path
from .views import (
    DirectorOverviewAPI,
    DirectorTeacherListAPI,
    DirectorStudentListAPI,
    DirectorModuleListAPI,
    DirectorExamListAPI,
    DirectorResultsAPI,
)

from .import_export_views import DirectorImportAPI, DirectorExportAPI

urlpatterns = [
    path("overview/", DirectorOverviewAPI.as_view(), name="api_director_overview"),
    path("teachers/", DirectorTeacherListAPI.as_view(), name="api_director_teachers"),
    path("students/", DirectorStudentListAPI.as_view(), name="api_director_students"),
    path("modules/", DirectorModuleListAPI.as_view(), name="api_director_modules"),
    path("exams/", DirectorExamListAPI.as_view(), name="api_director_exams"),
    path("results/", DirectorResultsAPI.as_view(), name="api_director_results"),
    path("import/", DirectorImportAPI.as_view(), name="api_director_import"),
    path("export/<str:format>/", DirectorExportAPI.as_view(), name="api_director_export"),
]
