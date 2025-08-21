from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import HttpRequest, HttpResponse
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, user_passes_test

from .models import Admission, PaymentTransaction
from .forms import AdmissionForm
from programs.models import Program

# --- Helpers permissions simples (à adapter à ton RBAC) ---
def staff_required(user):
    return user.is_staff or user.is_superuser

# --- Public: Apply depuis une formation ---
def apply_from_program(request: HttpRequest, slug: str) -> HttpResponse:
    program = get_object_or_404(Program, slug=slug)
    if request.method == "POST":
        form = AdmissionForm(request.POST, request.FILES)
        if form.is_valid():
            adm = form.save(commit=False)
            adm.program = program
            adm.source_page = "detail"
            # Règle simple de pré-qualification
            adm.status = "PRET_PAIEMENT" if adm.diplome else "A_COMPLETER"
            adm.save()
            messages.success(request, "Votre demande a été enregistrée. Vous allez être redirigé.")
            # Placeholder: redirection WhatsApp ou checkout (au choix)
            return redirect(reverse("admissions:thanks", args=[adm.ref_code]))
    else:
        form = AdmissionForm(initial={"program": program.id, "source_page": "detail"})
    return render(request, "admissions/apply_form.html", {"form": form, "program": program})

# --- Public: Apply générique (sans passer par une page program) ---
def apply_generic(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = AdmissionForm(request.POST, request.FILES)
        if form.is_valid():
            adm = form.save(commit=False)
            # Ici, 'program' doit être envoyé depuis le formulaire (pas hidden)
            adm.source_page = "apply"
            adm.status = "PRET_PAIEMENT" if adm.diplome else "A_COMPLETER"
            adm.save()
            messages.success(request, "Votre demande a été enregistrée.")
            return redirect(reverse("admissions:thanks", args=[adm.ref_code]))
    else:
        form = AdmissionForm()
    return render(request, "admissions/apply_form_generic.html", {"form": form})

# --- Page de remerciement simple ---
def thanks(request: HttpRequest, ref_code: str) -> HttpResponse:
    admission = get_object_or_404(Admission, ref_code=ref_code)
    return render(request, "admissions/thanks.html", {"admission": admission})

# --- CRUD Admin (exemples basiques) ---
@method_decorator([login_required, user_passes_test(staff_required)], name="dispatch")
class AdmissionListView(ListView):
    model = Admission
    template_name = "admissions/admin/list.html"
    context_object_name = "admissions"
    paginate_by = 25

    def get_queryset(self):
        qs = Admission.objects.select_related("program").order_by("-submitted_at")
        status = self.request.GET.get("status")
        program = self.request.GET.get("program")
        if status:
            qs = qs.filter(status=status)
        if program:
            qs = qs.filter(program__id=program)
        return qs

@method_decorator([login_required, user_passes_test(staff_required)], name="dispatch")
class AdmissionDetailView(DetailView):
    model = Admission
    template_name = "admissions/admin/detail.html"
    context_object_name = "admission"
    slug_field = "ref_code"
    slug_url_kwarg = "ref_code"

@method_decorator([login_required, user_passes_test(staff_required)], name="dispatch")
class AdmissionCreateView(CreateView):
    model = Admission
    form_class = AdmissionForm
    template_name = "admissions/admin/form.html"

    def get_success_url(self):
        return reverse("admissions:admin_detail", args=[self.object.ref_code])

@method_decorator([login_required, user_passes_test(staff_required)], name="dispatch")
class AdmissionUpdateView(UpdateView):
    model = Admission
    form_class = AdmissionForm
    template_name = "admissions/admin/form.html"
    slug_field = "ref_code"
    slug_url_kwarg = "ref_code"

    def get_success_url(self):
        return reverse("admissions:admin_detail", args=[self.object.ref_code])

@method_decorator([login_required, user_passes_test(staff_required)], name="dispatch")
class AdmissionDeleteView(DeleteView):
    model = Admission
    template_name = "admissions/admin/confirm_delete.html"
    slug_field = "ref_code"
    slug_url_kwarg = "ref_code"

    def get_success_url(self):
        return reverse("admissions:admin_list")
