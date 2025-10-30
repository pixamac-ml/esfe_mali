from collections import defaultdict
from django.shortcuts import render, get_object_or_404
from django.urls import reverse, NoReverseMatch
from django.apps import apps

from .models import HomeHero, SimplePage
from programs.models import Program, Cycle

from collections import defaultdict
from django.shortcuts import render, get_object_or_404
from django.urls import reverse, NoReverseMatch
from django.apps import apps

from .models import HomeHero, SimplePage
from programs.models import Program, Cycle

CYCLES_ORDER = [
    (Cycle.PRIMAIRE,   "Cycle primaire"),
    (Cycle.SECONDAIRE, "Cycle secondaire"),
    (Cycle.LICENCE,    "Licence"),
    (Cycle.MASTER,     "Master"),
]

# Chargement optionnel
try:
    from blog.models import Post
except Exception:
    Post = None

try:
    from campuses.models import Campus
except Exception:
    Campus = None


def _get_model(app_label: str, model_name: str):
    try:
        return apps.get_model(app_label, model_name)
    except Exception:
        return None


def home(request):
    # --- Programmes phares (pour un carrousel/une zone ailleurs si besoin)
    from programs.models import Program, Cycle

    # Programmes limités : Licence & Master, max 6
    featured_programs = Program.objects.filter(
        is_active=True,
        cycle__in=[Cycle.LICENCE, Cycle.MASTER]
    ).order_by("cycle", "title")[:6]

    # Groupement par cycle
    by_cycle = defaultdict(list)
    for prog in featured_programs:
        by_cycle[prog.cycle].append(prog)

    cycles = []
    for slug, label in [(Cycle.LICENCE, "Licence"), (Cycle.MASTER, "Master")]:
        cycles.append({
            "slug": slug.lower(),
            "label": label,
            "items": by_cycle.get(slug, [])
        })

    # --- Hero
    heros = HomeHero.objects.filter(is_active=True).order_by("order")

    # --- URL Admission
    try:
        apply_url = reverse("admissions:apply")
    except NoReverseMatch:
        apply_url = "#admission"

    # --- Blog
    latest_posts = Post.objects.filter(status="published").order_by("-published_at")[:3] if Post else []

    # --- Campuses
    campuses = []
    if Campus:
        fields = [f.name for f in Campus._meta.get_fields()]
        qs = Campus.objects.all().order_by("name")
        campuses = qs.filter(is_active=True) if "is_active" in fields else qs
        campuses = campuses[:6]

    # --- À propos (SchoolProfile)
    SchoolProfile = _get_model("core", "SchoolProfile") or _get_model("sitecore", "SchoolProfile")
    profile = SchoolProfile.objects.first() if SchoolProfile else None

    school_name   = getattr(profile, "school_name", "ESFé")
    about_intro   = getattr(profile, "about_intro", "")
    bullets_raw   = getattr(profile, "about_bullets", "")
    about_bullets = [l.strip() for l in bullets_raw.splitlines() if l.strip()] if bullets_raw else []
    about_image   = getattr(profile, "about_image", None)
    about_cta_url = getattr(profile, "about_cta_url", "")

    # --- KPIs (SiteStat)
    SiteStat = _get_model("core", "SiteStat") or _get_model("stats", "SiteStat")
    if SiteStat:
        stats = {s.key: s.value for s in SiteStat.objects.all()}
        kpi_years    = stats.get("years", "15+")
        kpi_students = stats.get("students", "10k+")
        kpi_partners = stats.get("partners", "30+")
        kpi_annexes  = stats.get("annexes", "12")
    else:
        kpi_years, kpi_students, kpi_partners, kpi_annexes = "15+", "10k+", "30+", "12"

    context = {
        "apply_url": apply_url,
        "latest_posts": latest_posts,
        "campuses": campuses,
        "heros": heros,
        "featured_programs": featured_programs,
        "cycles": cycles,

        # À propos
        "school_name": school_name,
        "about_intro": about_intro,
        "about_bullets": about_bullets,
        "about_image": about_image,
        "about_cta_url": about_cta_url,

        # KPIs
        "kpi_years": kpi_years,
        "kpi_students": kpi_students,
        "kpi_partners": kpi_partners,
        "kpi_annexes": kpi_annexes,

        # SEO
        "seo_title": "Accueil",
        "seo_description": "Université & École de Santé Félix Houphouët-Boigny Mali (ESFé) — enseignement, pratique et insertion professionnelle.",
    }
    return render(request, "core/home.html", context)


def simple_page(request, slug):
    """Affiche une page simple type CMS avec SEO."""
    page = get_object_or_404(SimplePage, slug=slug, status="published")
    return render(
        request,
        "core/page.html",
        {
            "page": page,
            "seo_title": page.title,
            "seo_description": getattr(page, "excerpt", page.title),  # description SEO fallback
        },
    )


def privacy(request):
    """Politique de confidentialité"""
    return render(request, "core/privacy.html", {
        "seo_title": "Politique de confidentialité",
        "seo_description": "Découvrez la politique de confidentialité de l’Université & École de Santé Félix Houphouët-Boigny Mali (ESFé Mali).",
    })


def legal(request):
    """Mentions légales"""
    return render(request, "core/legal.html", {
        "seo_title": "Mentions légales",
        "seo_description": "Mentions légales officielles de l’Université & École de Santé Félix Houphouët-Boigny Mali (ESFé Mali).",
    })


def sitemap_page(request):
    """Plan du site (HTML, accessible depuis le footer)"""
    return render(request, "core/sitemap.html", {
        "seo_title": "Plan du site",
        "seo_description": "Consultez le plan du site ESFé Mali — toutes les rubriques accessibles en un coup d'œil.",
    })
