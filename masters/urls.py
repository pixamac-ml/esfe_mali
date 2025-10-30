# masters/urls.py
from django.urls import path, include
from .views import (
    dashboard, fragments, auth, staff,
    api, fragments_director, media_proxy
)
from .views.api_lessons_json import LessonAPIView
from .views.api_chapters import ChapterView
from .views.fragments import student_course_view
from .views.media_proxy import video_proxy

app_name = "masters"

urlpatterns = [
    # 🔐 Authentification
    path("login/", auth.MasterLoginView.as_view(), name="login"),
    path("logout/", auth.master_logout, name="logout"),
    path("change-password/", auth.change_password, name="change_password"),
    path("force-password-change/", auth.force_password_change, name="force_password_change"),

    # 🧭 Dashboards
    path("dashboard/", dashboard.dashboard_router, name="dashboard"),
    path("student/dashboard/", dashboard.student_dashboard, name="student_dashboard"),
    path("teacher/dashboard/", dashboard.teacher_dashboard, name="teacher_dashboard"),
    path("staff/dashboard/", dashboard.staff_dashboard, name="staff_dashboard"),
    path("director/dashboard/", dashboard.director_dashboard, name="director_dashboard"),

    # 🧩 Fragments
    path("student/fragment/<str:section>/", fragments.student_fragment_switch, name="student_fragment"),
    path("student/fragment/course/<int:course_id>/", student_course_view, name="student_course_view"),
    path("teacher/fragment/<str:section>/", fragments.teacher_fragment_switch, name="teacher_fragment"),
    path("director/fragment/<str:section>/", fragments_director.director_fragment_switch, name="director_fragment"),

    # ⚙️ APIs internes
    path("api/student/overview/", api.api_student_overview, name="api_student_overview"),
    path("api/student/modules/", api.api_student_modules, name="api_student_modules"),
    path("api/student/lessons/<int:module_id>/", api.api_student_lessons, name="api_student_lessons"),
    path("api/student/progress/", api.mark_lesson_complete, name="api_student_progress"),
    path("api/teacher/", include("masters.api_teacher.urls")),
    path("api/director/", include("masters.api_director.urls")),
    path("api/chapters/<int:module_id>/", ChapterView.as_view(), name="api_chapters"),
    path("api/lessons/<int:module_id>/", LessonAPIView.as_view(), name="api_lessons"),

    # 🎥 Vidéos
    path("proxy/video/", video_proxy, name="video_proxy"),

    # 👩‍💼 Staff
    path("staff/create-teacher/", staff.create_teacher, name="create_teacher"),

    # 💬 Messagerie interne (✅ Intégration stable)
    path("messenger/", include("messenger.urls", namespace="messenger")),
]
