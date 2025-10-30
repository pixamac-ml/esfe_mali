from django.contrib import admin
from .models import Program, Session


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("name", "order")
    ordering = ("order",)
    search_fields = ("name",)


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "cycle",
        "level",
        "specialization",
        "diploma",
        "duration",
        "featured",
        "is_active",
    )
    list_filter = ("cycle", "featured", "is_active", "sessions")
    search_fields = ("title", "diploma", "specialization", "description")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("sessions",)
    ordering = ("cycle", "title")

    fieldsets = (
        ("Informations générales", {
            "fields": (
                "title", "slug", "cycle", "level", "specialization",
                "duration", "entry_requirement", "diploma",
                "short_description", "description", "image",
                "featured", "is_active"
            )
        }),
        ("Frais & Scolarité", {
            "fields": (
                "inscription_fee", "tranche_count", "tranche_amount",
                "tuition_per_month", "tuition_total",
            )
        }),
        ("Sessions d'entrée", {
            "fields": ("sessions",)
        }),
        ("Suivi", {
            "fields": ("created_at", "updated_at"),
        }),
    )
    readonly_fields = ("created_at", "updated_at")
