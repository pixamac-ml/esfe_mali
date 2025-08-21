from django.shortcuts import render, get_object_or_404
from .models import HomeHero, SimplePage
from programs.models import Program



# core/views.py
from django.shortcuts import render
from django.urls import reverse, NoReverseMatch

from .models import HomeHero, SimplePage
from programs.models import Program

# Optionnels selon ton projet
try:
    from blog.models import Post
except Exception:
    Post = None

try:
    from campuses.models import Campus
except Exception:
    Campus = None




def home(request):
    heros = HomeHero.objects.filter(is_active=True).order_by("order")
    featured_programs = Program.objects.filter(is_active=True, featured=True)[:3]
    # URL Admission sécurisée
    try:
        apply_url = reverse("admissions:apply")
    except NoReverseMatch:
        apply_url = "#admission"

    # Blog
    latest_posts = Post.objects.filter(is_published=True).order_by("-published_at")[:3] if Post else []

    # Campuses
    campuses = Campus.objects.filter(is_active=True).order_by("name")[:6] if Campus else []
    context = {
        "apply_url": apply_url,
        "latest_posts": latest_posts,
        "campuses": campuses,

        "heros": heros,
        "featured_programs": featured_programs,
        # Optionnel SEO basique :
        "seo_title": "Accueil",
        "seo_description": "École de Santé Félix Houphouët-Boigny (ESFé) — enseignement, pratique et insertion.",
    }
    return render(request, "core/home.html", context)



def simple_page(request, slug):
    page = get_object_or_404(SimplePage, slug=slug, is_published=True)
    return render(request, "core/page.html", {"page": page, "seo_title": page.title})
