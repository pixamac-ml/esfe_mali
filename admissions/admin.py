from django.contrib import admin
from .models import Admission, PaymentTransaction, WebhookEvent, AdmissionAttachment

class AttachmentInline(admin.TabularInline):
    model = AdmissionAttachment
    extra = 0

class PaymentInline(admin.TabularInline):
    model = PaymentTransaction
    extra = 0
    readonly_fields = ("provider", "status", "amount", "currency", "provider_ref", "created_at", "updated_at")

@admin.register(Admission)
class AdmissionAdmin(admin.ModelAdmin):
    list_display = ("ref_code", "nom", "prenom", "program", "annexe", "status", "submitted_at")
    list_filter = ("status", "annexe", "program__cycle")
    search_fields = ("ref_code", "nom", "prenom", "telephone", "email", "program__title")
    readonly_fields = ("submitted_at", "paid_at", "enrolled_at")
    inlines = [AttachmentInline, PaymentInline]

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ("admission", "provider", "amount", "currency", "status", "created_at")
    list_filter = ("provider", "status", "currency")
    search_fields = ("admission__ref_code", "provider_ref")

@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ("provider", "event_type", "external_id", "received_at", "processed")
    list_filter = ("provider", "event_type", "processed")
    search_fields = ("external_id", "payload")
