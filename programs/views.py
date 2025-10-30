from collections import defaultdict
from django import forms
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone

from .models import Program, Cycle
from admissions.forms import AdmissionForm

ICON_MAP = {
    "pharma": "icons/pharmacie.svg",
    "biologie": "icons/biologie.svg",
    "laboratoire": "icons/biologie.svg",
    "infirm": "icons/infirmier.svg",
    "sage": "icons/sagefemme.svg",
    "med": "icons/medecine.svg",
    "nutrition": "icons/nutrition.svg",
    "gestion": "icons/gestion.svg",
    "secrétariat": "icons/gestion.svg",
    "default": "icons/default.svg",
}


def _guess_icon_path(specialization: str) -> str:
    spec = (specialization or "").lower()
    for key, icon_path in ICON_MAP.items():
        if key != "default" and key in spec:
            return icon_path
    return ICON_MAP["default"]


def program_list(request):
    programs = Program.objects.filter(is_active=True)

    grouped = defaultdict(list)
    for p in programs:
        grouped[p.get_cycle_display()].append({
            "obj": p,
            "icon": _guess_icon_path(p.specialization),
        })

    cycles = [
        {"label": "Cycle primaire", "items": grouped.get(Cycle.PRIMAIRE.label, [])},
        {"label": "Cycle secondaire", "items": grouped.get(Cycle.SECONDAIRE.label, [])},
        {"label": "Cycle supérieur – Licence", "items": grouped.get(Cycle.LICENCE.label, [])},
        {"label": "Cycle supérieur – Master", "items": grouped.get(Cycle.MASTER.label, [])},
    ]

    return render(request, "programs/program_list.html", {"cycles": cycles})


from django.contrib.auth import get_user_model
from notifications.models import Notification

User = get_user_model()


def program_detail(request, slug):
    program = get_object_or_404(Program, slug=slug, is_active=True)

    if request.method == "POST":
        form = AdmissionForm(request.POST, request.FILES)
        if form.is_valid():
            admission = form.save(commit=False)
            admission.program = program
            admission.source_page = "detail"
            admission.privacy_accepted_at = timezone.now()
            admission.save()

            # notifier le premier staff trouvé
            recipient = User.objects.filter(is_staff=True).first()
            if recipient:
                Notification.objects.create(
                    recipient=recipient,
                    notif_type="info",
                    message=f"Nouvelle candidature : {admission.nom} {admission.prenom} pour {admission.program}",
                    url=f"/admissions/{admission.ref_code}/"
                )

            messages.success(request, "✅ Votre candidature a été enregistrée avec succès.")
            return redirect("admissions:thanks", ref_code=admission.ref_code)
        else:
            messages.error(request, "⚠️ Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = AdmissionForm(initial={
            "program": program.id,
            "source_page": "detail",
        })
        form.fields["program"].widget = forms.HiddenInput()

    # ✅ Toujours un return
    return render(request, "programs/program_detail.html", {
        "program": program,
        "form": form,
    })
