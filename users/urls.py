from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "users"

urlpatterns = [
    # Auth
    path("register/", views.register, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name="users/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # Password reset (mot de passe oublié)
    path("password-reset/", auth_views.PasswordResetView.as_view(
        template_name="users/password_reset.html",
        email_template_name="users/password_reset_email.txt",
        success_url="/users/password-reset/done/"
    ), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(
        template_name="users/password_reset_done.html"
    ), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="users/password_reset_confirm.html",
        success_url="/users/reset/done/"
    ), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(
        template_name="users/password_reset_complete.html"
    ), name="password_reset_complete"),

    # Password change (connecté)
    path("password-change/", views.change_password, name="password_change"),

    # Espace utilisateur
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),

    # Console admin (superuser/admin role)
    path("manage/", views.user_list, name="user_list"),
    path("manage/create/", views.user_create, name="user_create"),
    path("manage/<int:user_id>/", views.user_detail, name="user_detail"),
    path("manage/<int:user_id>/edit/", views.user_edit, name="user_edit"),
    path("manage/<int:user_id>/password/", views.user_set_password, name="user_set_password"),
]
