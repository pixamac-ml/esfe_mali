from django import forms
from django.contrib.auth.forms import (
    UserCreationForm, UserChangeForm, PasswordChangeForm, SetPasswordForm
)
from .models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "phone", "role", "annexe", "is_staff")

class CustomUserChangeForm(UserChangeForm):
    password = None  # on ne montre pas le hash
    class Meta:
        model = User
        fields = ("username", "email", "phone", "role", "annexe", "is_active", "is_staff")

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("email", "phone", "annexe")

class AdminSetPasswordForm(SetPasswordForm):
    """Forme standard Django pour définir un nouveau mot de passe par l'admin sur un utilisateur."""
    pass


from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class PublicRegisterForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("username", "email", "phone")  # on garde simple
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "Nom d’utilisateur"}),
            "email": forms.EmailInput(attrs={"placeholder": "Email"}),
            "phone": forms.TextInput(attrs={"placeholder": "Téléphone"}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False   # ⚠️ Inactif tant que tu n’as pas validé
        user.role = None         # rôle non attribué
        if commit:
            user.save()
        return user
