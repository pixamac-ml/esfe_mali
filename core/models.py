from django.db import models
from django.urls import reverse, NoReverseMatch
from django.utils import timezone

# --- Mixins SEO ---
class SEOFields(models.Model):
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    og_image = models.ImageField(upload_to="og/", blank=True, null=True)

    class Meta:
        abstract = True

# --- Réglages globaux du site (singleton logique) ---
class SiteSettings(SEOFields):
    site_name = models.CharField(max_length=120, default="ESFé Mali")
    tagline = models.CharField(max_length=160, blank=True)
    logo = models.ImageField(upload_to="brand/", blank=True, null=True)
    favicon = models.ImageField(upload_to="brand/", blank=True, null=True)

    # Contacts globaux
    email = models.EmailField(blank=True)
    phone_main = models.CharField(max_length=40, blank=True)
    whatsapp = models.CharField(max_length=40, blank=True)
    address = models.CharField(max_length=255, blank=True)
    map_embed = models.TextField(blank=True)

    # Intégrations
    ga4_id = models.CharField(max_length=30, blank=True)  # ex: G-XXXX
    meta_pixel_id = models.CharField(max_length=30, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Réglages du site"
        verbose_name_plural = "Réglages du site"

    def __str__(self):
        return "Réglages du site"

# --- Réseaux sociaux ---
class SocialLink(models.Model):
    KIND_CHOICES = [
        ("fb", "Facebook"), ("ig", "Instagram"), ("yt", "YouTube"),
        ("wa", "WhatsApp"), ("x", "X/Twitter"), ("ln", "LinkedIn"),
    ]
    settings = models.ForeignKey(SiteSettings, on_delete=models.CASCADE, related_name="socials")
    kind = models.CharField(max_length=3, choices=KIND_CHOICES)
    url = models.URLField()

    def __str__(self):
        return f"{self.get_kind_display()}"

# --- Menus / Footer ---
class Menu(models.Model):
    LOCATION = [("header", "Header"), ("footer", "Footer")]
    title = models.CharField(max_length=80)
    slug = models.SlugField(unique=True)
    location = models.CharField(max_length=10, choices=LOCATION)

    def __str__(self):
        return f"{self.title} ({self.location})"

class MenuItem(models.Model):
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name="items")
    parent = models.ForeignKey("self", on_delete=models.CASCADE, related_name="children",
                               null=True, blank=True)
    label = models.CharField(max_length=80)
    # 3 façons de pointer: URL absolue, named url, page CMS
    url = models.CharField(max_length=255, blank=True)
    named_url = models.CharField(max_length=100, blank=True)
    order = models.PositiveIntegerField(default=0)
    new_tab = models.BooleanField(default=False)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.label

    def resolved_url(self):
        if self.named_url:
            try:
                return reverse(self.named_url)
            except NoReverseMatch:
                return "#"
        return self.url or "#"

# --- Page CMS simple (pour Présentation, International, etc.) ---
class SimplePage(SEOFields):
    title = models.CharField(max_length=160)
    slug = models.SlugField(unique=True)
    body = models.TextField(blank=True)  # HTML/Markdown converti côté template si besoin
    is_published = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("core:page", args=[self.slug])

# --- Hero / Accueil contrôlé par admin ---
class HomeHero(models.Model):
    headline = models.CharField(max_length=120)
    subheadline = models.CharField(max_length=200, blank=True)
    cta_primary_text = models.CharField(max_length=40, blank=True)
    cta_primary_url = models.CharField(max_length=200, blank=True)
    cta_secondary_text = models.CharField(max_length=40, blank=True)
    cta_secondary_url = models.CharField(max_length=200, blank=True)
    background = models.ImageField(upload_to="hero/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Hero d'accueil"
        verbose_name_plural = "Heros d'accueil"

    def __str__(self):
        return self.headline

# --- Bandeau d'annonce global ---
class SiteAnnouncement(models.Model):
    LEVELS = [("info","Info"),("success","Succès"),("warning","Alerte"),("danger","Urgent")]
    message = models.CharField(max_length=200)
    level = models.CharField(max_length=7, choices=LEVELS, default="info")
    is_active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(blank=True, null=True)
    ends_at = models.DateTimeField(blank=True, null=True)

    def active_now(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.starts_at and now < self.starts_at:
            return False
        if self.ends_at and now > self.ends_at:
            return False
        return True

    def __str__(self):
        return f"[{self.level}] {self.message[:30]}"

# --- Redirections 301 ---
class RedirectRule(models.Model):
    old_path = models.CharField(max_length=255, unique=True)   # ex: /ancienne-page/
    new_path = models.CharField(max_length=255)                # ex: /nouvelle-page/
    permanent = models.BooleanField(default=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.old_path} -> {self.new_path}"
