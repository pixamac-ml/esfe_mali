from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username", "email", "role", "annexe", "is_staff", "is_superuser", "last_login"
    )
    list_filter = ("role", "annexe", "is_staff", "is_superuser")
    search_fields = ("username", "email", "first_name", "last_name")

    fieldsets = UserAdmin.fieldsets + (
        ("Rôle et Annexe", {"fields": ("role", "annexe")}),
    )

    # ✅ Forcer l’admin principal à garder ses super-pouvoirs
    def save_model(self, request, obj, form, change):
        if obj.is_superuser:
            obj.role = "ADMIN"
        super().save_model(request, obj, form, change)
