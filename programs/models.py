from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse


class Cycle(models.TextChoices):
    PRIMAIRE = "PRIMAIRE", _("Cycle primaire")
    SECONDAIRE = "SECONDAIRE", _("Cycle secondaire")
    LICENCE = "LICENCE", _("Cycle supérieur – Licence")
    MASTER = "MASTER", _("Cycle supérieur – Master")


class Session(models.Model):
    """Ex: Janvier, Mars (intakes)."""
    name = models.CharField(max_length=50, unique=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Program(models.Model):
    title = models.CharField("Intitulé de la formation", max_length=200)
    slug = models.SlugField(unique=True)
    cycle = models.CharField(max_length=15, choices=Cycle.choices)
    level = models.CharField("Niveau (ex: Licence 1, Master 2, etc.)", max_length=50, blank=True)
    specialization = models.CharField("Spécialisation / Domaine", max_length=150, blank=True)

    duration = models.CharField("Durée", max_length=50, help_text="Ex: 2 ans, 1 an, 3 ans")
    entry_requirement = models.CharField("Niveau requis", max_length=120, help_text="Ex: DEF / BEPC / BAC / TSS / BT")
    diploma = models.CharField("Diplôme obtenu", max_length=180, blank=True)

    short_description = models.TextField("Description courte", max_length=350, blank=True)
    description = models.TextField("Description détaillée", blank=True)
    image = models.ImageField(upload_to="programs/", blank=True)

    featured = models.BooleanField("Mettre en avant (Accueil)", default=False)
    is_active = models.BooleanField("Formation active", default=True)

    # Frais
    inscription_fee = models.DecimalField("Frais d'inscription (XOF)", max_digits=10, decimal_places=0, null=True, blank=True)
    tranche_count = models.PositiveSmallIntegerField("Nombre de tranches", default=0)
    tranche_amount = models.DecimalField("Montant par tranche (XOF)", max_digits=10, decimal_places=0, null=True, blank=True)
    tuition_per_month = models.DecimalField("Mensualité (XOF)", max_digits=10, decimal_places=0, null=True, blank=True)
    tuition_total = models.DecimalField("Total scolarité (XOF)", max_digits=11, decimal_places=0, null=True, blank=True)

    # Sessions d'entrée
    sessions = models.ManyToManyField(Session, related_name="programs", blank=True)

    # Campus reliés
    campuses = models.ManyToManyField("campuses.Campus", related_name="programs", blank=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ["cycle", "title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("programs:program_detail", args=[self.slug])
