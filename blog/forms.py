from django import forms
from .models import Comment

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["display_name", "message"]
        widgets = {
            "display_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Votre nom"}),
            "message": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Votre commentaire..."}),
        }
