from django import forms
from .models import Admission, AdmissionAttachment

class AdmissionForm(forms.ModelForm):
    class Meta:
        model = Admission
        fields = [
            "program", "source_page",
            "nom", "prenom", "genre", "date_naissance", "lieu_naissance", "nationalite",
            "telephone", "email", "adresse",
            "tuteur_nom", "tuteur_tel",
            "annexe",
            "diplome", "releves", "cni", "photo_identite",
            "optin_whatsapp",
        ]
        widgets = {
            "program": forms.HiddenInput(),
            "source_page": forms.HiddenInput(),
            "date_naissance": forms.DateInput(attrs={"type": "date"}),
        }

    def clean_telephone(self):
        tel = self.cleaned_data.get("telephone", "").strip().replace(" ", "")
        if not tel.startswith("+"):
            tel = "+223" + tel  # normalisation Mali par défaut
        return tel

class AdmissionAttachmentForm(forms.ModelForm):
    class Meta:
        model = AdmissionAttachment
        fields = ["label", "file"]
