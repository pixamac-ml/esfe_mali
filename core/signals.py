from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SiteSettings, HomeHero, SimplePage
from .utils.images import build_variants
from pathlib import Path

def _proc(field):
    try:
        f = field.file
    except Exception:
        return
    if f and Path(f.path).exists():
        build_variants(Path(f.path))

@receiver(post_save, sender=SiteSettings)
def site_assets_variants(sender, instance, **kwargs):
    for field in ("logo", "favicon", "og_image"):
        f = getattr(instance, field)
        if f:
            _proc(f)

@receiver(post_save, sender=SimplePage)
def page_og_variants(sender, instance, **kwargs):
    if instance.og_image:
        _proc(instance.og_image)

@receiver(post_save, sender=HomeHero)
def hero_variants(sender, instance, **kwargs):
    if instance.background:
        _proc(instance.background)
