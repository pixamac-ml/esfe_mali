from pathlib import Path
from PIL import Image
from pillow_avif import AvifImagePlugin  # noqa

SIZES = (320, 480, 768, 1024, 1440, 1920)

def build_variants(image_path: Path):
    """Crée des dérivés AVIF+WebP aux tailles SIZES, à côté de l’original."""
    image_path = Path(image_path)
    stem = image_path.with_suffix("").as_posix()
    with Image.open(image_path) as im:
        im = im.convert("RGB")
        for w in SIZES:
            r = im.copy()
            r.thumbnail((w, 10_000))
            r.save(f"{stem}-{w}.avif", format="AVIF", quality=45, speed=6)
            r.save(f"{stem}-{w}.webp", format="WEBP", quality=70, method=6)
