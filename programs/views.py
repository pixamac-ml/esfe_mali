from django.shortcuts import render, get_object_or_404
from .models import Program

def program_list(request):
    programs = Program.objects.filter(is_active=True)
    return render(request, "programs/program_list.html", {"programs": programs})


from django.shortcuts import render, get_object_or_404
from django.urls import reverse, NoReverseMatch
from .models import Program

def program_detail(request, slug):
    program = get_object_or_404(Program, slug=slug, is_active=True)

    opportunities = [
        {"seed": "hopital", "title": "Hôpitaux & cliniques"},
        {"seed": "lab", "title": "Laboratoires & recherche"},
        {"seed": "ong", "title": "Organisations de santé publique"},
    ]
    # Lien "Candidater" avec fallback si le namespace admissions n'existe pas encore
    try:
        apply_url = reverse("admissions:apply")
    except NoReverseMatch:
        apply_url = "#admission"

    return render(request, "programs/program_detail.html", {
        "program": program,
        "apply_url": apply_url,
        "opportunities": opportunities
    })





