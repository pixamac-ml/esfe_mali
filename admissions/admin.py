from django.contrib import admin
from .models import Admission, PaymentTransaction, WebhookEvent, AdmissionAttachment

# --- Inlines ---
class AttachmentInline(admin.TabularInline):
    model = AdmissionAttachment
    extra = 0


class PaymentInline(admin.TabularInline):
    model = PaymentTransaction
    extra = 0
    readonly_fields = (
        "provider", "status", "amount", "currency", "provider_ref",
        "created_at", "updated_at"
    )


# --- Admission ---
@admin.register(Admission)
class AdmissionAdmin(admin.ModelAdmin):
    list_display = ["ref_code", "nom", "prenom", "campus", "status", "submitted_at"]
    list_filter = ["status", "campus", "program"]
    search_fields = ("ref_code", "nom", "prenom", "telephone", "email", "program__title")

    readonly_fields = ("submitted_at", "paid_at", "enrolled_at")

    inlines = [AttachmentInline, PaymentInline]

    fieldsets = (
        ("Informations personnelles", {
            "fields": ("nom", "prenom", "genre", "date_naissance", "lieu_naissance", "nationalite"),
        }),
        ("Coordonnées", {
            "fields": ("telephone", "email", "adresse"),
        }),
        ("Représentant légal", {
            "fields": ("tuteur_nom", "tuteur_tel"),
        }),
        ("Formation", {
            "fields": ("program", "campus"),
        }),
        ("Pièces jointes", {
            "fields": ("diplome", "releves", "cni", "photo_identite"),
        }),
        ("Statut", {
            "fields": ("status", "optin_whatsapp", "privacy_accepted_at"),
        }),
        ("Dates et suivi", {
            "fields": ("submitted_at", "paid_at", "enrolled_at"),
        }),
    )


# --- PaymentTransaction ---
@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ("admission", "provider", "amount", "currency", "status", "created_at")
    list_filter = ("provider", "status", "currency")
    search_fields = ("admission__ref_code", "provider_ref")


# --- WebhookEvent ---
@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ("provider", "event_type", "external_id", "received_at", "processed")
    list_filter = ("provider", "event_type", "processed")
    search_fields = ("external_id", "payload")
