from django.urls import path
from .views import (
    ModuleListCreateView, ModuleDeleteView,
    ChapterListCreateView, ChapterDeleteView,
    LessonListCreateView, LessonUpdateDeleteView,TeacherOverviewAPI
)

urlpatterns = [
    path("modules/", ModuleListCreateView.as_view(), name="api_teacher_modules"),
    path("modules/<int:pk>/", ModuleDeleteView.as_view(), name="api_teacher_delete_module"),
# masters/api_teacher/urls.py
    path("overview/", TeacherOverviewAPI.as_view(), name="api_teacher_overview"),

    path("chapters/<int:module_id>/", ChapterListCreateView.as_view(), name="api_teacher_chapters"),
    path("chapters/<int:module_id>/<int:pk>/", ChapterDeleteView.as_view(), name="api_teacher_delete_chapter"),

    path("lessons/<int:module_id>/", LessonListCreateView.as_view(), name="api_teacher_lessons"),
    path("lessons/<int:module_id>/<int:pk>/", LessonUpdateDeleteView.as_view(), name="api_teacher_edit_lesson"),
]
