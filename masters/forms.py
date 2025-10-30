# masters/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.contrib.auth.models import Group
from .models import ModuleUE, Chapter, Lesson, LessonResource

User = get_user_model()


# ============================================================
# 👨‍🏫 FORMULAIRE DE CRÉATION D’ENSEIGNANT (déjà existant)
# ============================================================

class TeacherCreateForm(forms.ModelForm):
    """
    Formulaire utilisé dans le dashboard staff pour créer un enseignant.
    - Définit automatiquement role="ENSEIGNANT"
    - Crée un mot de passe temporaire
    - Ajoute l’utilisateur au groupe “Enseignants”
    """
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone", "annexe"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = "ENSEIGNANT"
        user.username = user.email.split("@")[0] if user.email else get_random_string(8)

        temp_password = get_random_string(8)
        user.set_password(temp_password)

        if commit:
            user.save()
            group, _ = Group.objects.get_or_create(name="Enseignants")
            user.groups.add(group)

        return user, temp_password


# ============================================================
# 📘 FORMULAIRES DE TÉLÉVERSEMENT DE COURS (ÉTAPE 1)
# ============================================================

class ModuleForm(forms.ModelForm):
    """Création ou édition d’un module (UE)."""
    class Meta:
        model = ModuleUE
        fields = ["semester", "code", "title", "coefficient", "credits", "is_active"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Titre du module"}),
            "code": forms.TextInput(attrs={"class": "form-control", "placeholder": "Code du module"}),
        }


class ChapterForm(forms.ModelForm):
    """Formulaire de création de chapitre."""
    class Meta:
        model = Chapter
        fields = ["module", "title", "order"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Titre du chapitre"}),
        }


class LessonForm(forms.ModelForm):
    """
    Formulaire de création/téléversement d’une leçon.
    Valide qu’au moins une source vidéo est fournie :
    - soit un fichier local
    - soit une URL externe (YouTube, Drive, etc.)
    """
    class Meta:
        model = Lesson
        fields = [
            "chapter",
            "title",
            "order",
            "video_file",
            "external_url",
            "resource_file",
            "is_published",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Titre de la leçon"}),
            "external_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "Lien vidéo externe"}),
            "video_file": forms.FileInput(attrs={"class": "form-control"}),
            "resource_file": forms.FileInput(attrs={"class": "form-control"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        video_file = cleaned_data.get("video_file")
        external_url = cleaned_data.get("external_url")

        # Vérifie qu'au moins une source vidéo existe
        if not video_file and not external_url:
            raise forms.ValidationError(
                "Veuillez fournir une vidéo (fichier) ou une URL externe."
            )

        # Empêche la double saisie (fichier + URL)
        if video_file and external_url:
            raise forms.ValidationError(
                "Choisissez soit un fichier vidéo, soit un lien externe — pas les deux."
            )

        return cleaned_data


class LessonResourceForm(forms.ModelForm):
    """Formulaire pour ajouter une ressource complémentaire à une leçon."""
    class Meta:
        model = LessonResource
        fields = ["lesson", "title", "file"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Titre de la ressource"}),
            "file": forms.FileInput(attrs={"class": "form-control"}),
        }
