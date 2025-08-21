from django import template
from pathlib import Path

register = template.Library()

@register.simple_tag
def picture_sources(image_url: str, widths="320 480 768 1024 1440 1920"):
    """Génère les `source` AVIF/WebP + src fallback JPEG/PNG."""
    if not image_url:
        return ""
    p = Path(image_url)
    stem = "/" + p.as_posix().lstrip("/").rsplit(".", 1)[0]
    widths = [w.strip() for w in widths.split() if w.strip().isdigit()]
    avif = ", ".join([f"{stem}-{w}.avif {w}w" for w in widths])
    webp = ", ".join([f"{stem}-{w}.webp {w}w" for w in widths])
    return (
        f'<source type="image/avif" srcset="{avif}">\n'
        f'<source type="image/webp" srcset="{webp}">\n'
    )
