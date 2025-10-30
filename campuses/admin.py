from django.contrib import admin
from .models import Campus


@admin.register(Campus)
class CampusAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "city", "phone", "email", "manager", "is_active")
    list_filter = ("is_active", "city")
    search_fields = ("code", "name", "city", "manager__username", "manager__first_name", "manager__last_name")
    ordering = ("name",)
    readonly_fields = ("created_at",)

    fieldsets = (
        ("Informations générales", {
            "fields": ("code", "name", "city", "address")
        }),
        ("Responsable", {
            "fields": ("manager", "phone", "email")
        }),
        ("Statut", {
            "fields": ("is_active", "created_at")
        }),
    )
