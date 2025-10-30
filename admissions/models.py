from django.db import models
from django.conf import settings
from django.utils import timezone
from programs.models import Program
from campuses.models import Campus

# --- Choix globaux ---
GENDER = [
    ("M", "Masculin"),
    ("F", "Féminin"),
    ("A", "Autre / Préfère ne pas dire"),
]

APPLICATION_STATUS = [
    ("RECU", "Reçu"),
    ("VALIDE", "Validé par le staff"),
    ("A_COMPLETER", "À compléter"),
    ("PRET_PAIEMENT", "Prêt pour paiement"),
    ("PAIEMENT_OK", "Paiement confirmé"),
    ("ADMIS", "Admis / Inscrit"),
    ("REFUSE", "Refusé"),
    ("ANNULE", "Annulé"),
]

PAYMENT_STATUS = [
    ("INITIE", "Initié"),
    ("EN_ATTENTE", "En attente"),
    ("SUCCES", "Succès"),
    ("ECHEC", "Échec"),
    ("ANNULE", "Annulé"),
    ("REMBOURSE", "Remboursé"),
]

CURRENCY = [
    ("XOF", "Franc CFA"),
    ("EUR", "Euro"),
    ("USD", "Dollar US"),
]


# --- Admissions ---
class Admission(models.Model):
    ref_code = models.CharField(max_length=32, unique=True, editable=False)
    program = models.ForeignKey(Program, on_delete=models.PROTECT, related_name="admissions")
    campus = models.ForeignKey(Campus, on_delete=models.PROTECT, related_name="admissions")

    # tracking source
    source_page = models.CharField(max_length=20, default="detail")  # "detail" | "apply"
    utm_source = models.CharField(max_length=64, blank=True)
    utm_campaign = models.CharField(max_length=64, blank=True)

    # infos personnelles
    nom = models.CharField(max_length=120)
    prenom = models.CharField(max_length=120)
    genre = models.CharField(max_length=1, choices=GENDER, blank=True)
    date_naissance = models.DateField(null=True, blank=True)
    lieu_naissance = models.CharField(max_length=120, blank=True)
    nationalite = models.CharField(max_length=80, blank=True)

    telephone = models.CharField(max_length=32)
    email = models.EmailField(blank=True)
    adresse = models.CharField(max_length=255, blank=True)

    # tuteur
    tuteur_nom = models.CharField(max_length=120, blank=True)
    tuteur_tel = models.CharField(max_length=32, blank=True)

    # fichiers
    diplome = models.FileField(upload_to="admissions/diplomes/", blank=True, null=True)
    releves = models.FileField(upload_to="admissions/releves/", blank=True, null=True)
    cni = models.FileField(upload_to="admissions/cni/", blank=True, null=True)
    photo_identite = models.ImageField(upload_to="admissions/photos/", blank=True, null=True)

    # frais snapshots
    fees_total_snapshot = models.PositiveIntegerField(default=0)
    fees_first_tranche_snapshot = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=3, choices=CURRENCY, default="XOF")

    # statut
    status = models.CharField(max_length=24, choices=APPLICATION_STATUS, default="RECU")
    auto_score = models.PositiveIntegerField(default=0)
    rules_passed = models.BooleanField(default=False)
    notes_admin = models.TextField(blank=True)

    optin_whatsapp = models.BooleanField(default=True)
    privacy_accepted_at = models.DateTimeField(null=True, blank=True)

    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    enrolled_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="admissions_assigned"
    )

    student_number = models.CharField(max_length=32, blank=True)
    extra = models.JSONField(default=dict, blank=True)

    def save(self, *args, **kwargs):
        if not self.ref_code:
            year = timezone.now().year
            import uuid
            self.ref_code = f"ESFE-{year}-" + uuid.uuid4().hex[:6].upper()

        if not self.pk and self.program_id:
            if not self.fees_total_snapshot:
                self.fees_total_snapshot = getattr(self.program, "tuition_total", 0) or 0
            if not self.fees_first_tranche_snapshot:
                self.fees_first_tranche_snapshot = getattr(self.program, "tranche_amount", 0) or 0

        super().save(*args, **kwargs)

    # --- Business logic ---
    def mark_validated(self, user=None):
        self.status = "VALIDE"
        self.reviewed_at = timezone.now()
        self.save(update_fields=["status", "reviewed_at", "updated_at"])

    def mark_ready_for_payment(self):
        if self.status != "VALIDE":
            raise ValueError("Impossible: candidature non validée.")
        self.status = "PRET_PAIEMENT"
        self.save(update_fields=["status", "updated_at"])

    def mark_paid(self):
        self.status = "PAIEMENT_OK"
        self.paid_at = timezone.now()
        self.save(update_fields=["status", "paid_at", "updated_at"])

    def mark_enrolled(self, student_number: str = ""):
        self.status = "ADMIS"
        self.enrolled_at = timezone.now()
        if student_number:
            self.student_number = student_number
        self.save(update_fields=["status", "enrolled_at", "student_number", "updated_at"])

    def __str__(self):
        return f"{self.ref_code} · {self.nom} {self.prenom} → {self.program.title}"


# --- Transactions ---
class PaymentTransaction(models.Model):
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, related_name="payments")
    provider = models.CharField(max_length=40)
    provider_ref = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=16, choices=PAYMENT_STATUS, default="INITIE")
    amount = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, choices=CURRENCY, default="XOF")
    tranche_label = models.CharField(max_length=40, default="1ere_tranche")

    checkout_url = models.URLField(blank=True)
    return_url = models.URLField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    raw_request = models.JSONField(default=dict, blank=True)
    raw_response = models.JSONField(default=dict, blank=True)
    raw_webhook = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def mark_success(self, provider_ref=None):
        self.status = "SUCCES"
        if provider_ref:
            self.provider_ref = provider_ref
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "provider_ref", "completed_at", "updated_at"])
        self.admission.mark_paid()

    def mark_failure(self):
        self.status = "ECHEC"
        self.save(update_fields=["status", "updated_at"])

    def __str__(self):
        return f"{self.provider} {self.amount}{self.currency} → {self.get_status_display()}"


class WebhookEvent(models.Model):
    provider = models.CharField(max_length=40)
    event_type = models.CharField(max_length=60)
    external_id = models.CharField(max_length=120, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    related_admission = models.ForeignKey(Admission, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["-received_at"]


class AdmissionAttachment(models.Model):
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, related_name="attachments")
    label = models.CharField(max_length=120)
    file = models.FileField(upload_to="admissions/attachments/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.admission.ref_code} · {self.label}"
