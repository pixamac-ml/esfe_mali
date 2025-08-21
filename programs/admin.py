from django.contrib import admin
from .models import Program, Session

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("name", "order")
    list_editable = ("order",)
    search_fields = ("name",)

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = (
        "title", "cycle", "duration", "entry_requirement",
        "inscription_fee", "tranche_count", "tranche_amount",
        "tuition_total", "featured", "is_active"
    )
    list_filter = ("cycle", "featured", "is_active", "sessions")
    search_fields = ("title", "diploma", "short_description", "description")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("sessions",)
    fieldsets = (
        (None, {
            "fields": ("title", "slug", "cycle", "duration", "entry_requirement", "diploma", "featured", "is_active")
        }),
        ("Contenus", {
            "fields": ("short_description", "description", "image")
        }),
        ("Frais & Paiements (XOF)", {
            "fields": ("inscription_fee", "tranche_count", "tranche_amount", "tuition_total")
        }),
        ("Sessions d'entrée", {
            "fields": ("sessions",)
        }),
    )
