from django import forms
from .models import Admission, AdmissionAttachment
from campuses.models import Campus
from programs.models import Program


class AdmissionForm(forms.ModelForm):
    # Champ Formation
    program = forms.ModelChoiceField(
        queryset=Program.objects.filter(is_active=True),
        empty_label="Sélectionnez une formation",
        label="Formation",
        widget=forms.Select(attrs={
            "class": "w-full rounded-lg border border-slate-300 py-3 px-4 bg-white focus:ring-primary-500 focus:border-primary-500"
        })
    )

    # Champ Campus
    campus = forms.ModelChoiceField(
        queryset=Campus.objects.filter(is_active=True),
        empty_label="Sélectionnez un campus",
        label="Campus",
        widget=forms.Select(attrs={
            "class": "w-full rounded-lg border border-slate-300 py-3 px-4 bg-white focus:ring-primary-500 focus:border-primary-500"
        })
    )

    class Meta:
        model = Admission
        fields = [
            "program", "source_page",
            # Étudiant
            "nom", "prenom", "genre", "date_naissance", "lieu_naissance", "nationalite",
            "telephone", "email", "adresse",
            # Tuteur
            "tuteur_nom", "tuteur_tel",
            # Campus
            "campus",
            # Pièces jointes
            "diplome", "releves", "cni", "photo_identite",
            # Opt-in
            "optin_whatsapp",
        ]
        widgets = {
            "source_page": forms.HiddenInput(),

            # Étudiant
            "nom": forms.TextInput(attrs={
                "placeholder": "Nom complet",
                "class": "w-full rounded-lg border border-slate-300 py-3 px-4 focus:ring-primary-500 focus:border-primary-500"
            }),
            "prenom": forms.TextInput(attrs={
                "placeholder": "Prénom",
                "class": "w-full rounded-lg border border-slate-300 py-3 px-4 focus:ring-primary-500 focus:border-primary-500"
            }),
            "genre": forms.Select(attrs={
                "class": "w-full rounded-lg border border-slate-300 py-3 px-4 bg-white focus:ring-primary-500 focus:border-primary-500"
            }),
            "date_naissance": forms.DateInput(attrs={
                "type": "date",
                "class": "w-full rounded-lg border border-slate-300 py-3 px-4 focus:ring-primary-500 focus:border-primary-500"
            }),
            "lieu_naissance": forms.TextInput(attrs={
                "placeholder": "Lieu de naissance",
                "class": "w-full rounded-lg border border-slate-300 py-3 px-4 focus:ring-primary-500 focus:border-primary-500"
            }),
            "nationalite": forms.TextInput(attrs={
                "placeholder": "Nationalité",
                "class": "w-full rounded-lg border border-slate-300 py-3 px-4 focus:ring-primary-500 focus:border-primary-500"
            }),
            "telephone": forms.TextInput(attrs={
                "placeholder": "Numéro WhatsApp",
                "class": "w-full rounded-lg border border-slate-300 py-3 px-4 focus:ring-primary-500 focus:border-primary-500"
            }),
            "email": forms.EmailInput(attrs={
                "placeholder": "Adresse email",
                "class": "w-full rounded-lg border border-slate-300 py-3 px-4 focus:ring-primary-500 focus:border-primary-500"
            }),
            "adresse": forms.Textarea(attrs={
                "placeholder": "Adresse complète",
                "rows": 3,
                "class": "w-full rounded-lg border border-slate-300 py-3 px-4 focus:ring-primary-500 focus:border-primary-500"
            }),

            # Tuteur
            "tuteur_nom": forms.TextInput(attrs={
                "placeholder": "Nom complet du tuteur",
                "class": "w-full rounded-lg border border-slate-300 py-3 px-4 focus:ring-primary-500 focus:border-primary-500"
            }),
            "tuteur_tel": forms.TextInput(attrs={
                "placeholder": "Téléphone du tuteur",
                "class": "w-full rounded-lg border border-slate-300 py-3 px-4 focus:ring-primary-500 focus:border-primary-500"
            }),

            # Pièces jointes
            "diplome": forms.ClearableFileInput(attrs={
                "class": "block w-full text-sm text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
            }),
            "releves": forms.ClearableFileInput(attrs={
                "class": "block w-full text-sm text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
            }),
            "cni": forms.ClearableFileInput(attrs={
                "class": "block w-full text-sm text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
            }),
            "photo_identite": forms.ClearableFileInput(attrs={
                "class": "block w-full text-sm text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
            }),

            # Opt-in
            "optin_whatsapp": forms.CheckboxInput(attrs={
                "class": "rounded border-slate-300 text-primary-600 focus:ring-primary-500"
            }),
        }

    def clean_telephone(self):
        tel = self.cleaned_data.get("telephone", "").strip().replace(" ", "")
        if not tel.startswith("+"):
            tel = "+223" + tel  # par défaut Mali
        return tel


class AdmissionAttachmentForm(forms.ModelForm):
    class Meta:
        model = AdmissionAttachment
        fields = ["label", "file"]
        widgets = {
            "label": forms.TextInput(attrs={
                "placeholder": "Type de document (ex: Bac, CNI)",
                "class": "w-full rounded-lg border border-slate-300 py-3 px-4 focus:ring-primary-500 focus:border-primary-500"
            }),
            "file": forms.ClearableFileInput(attrs={
                "class": "block w-full text-sm text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
            }),
        }
