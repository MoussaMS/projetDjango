from django import forms
from .models import Utilisateurs

class PatientSignupForm(forms.ModelForm):
    mot_de_passe = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Utilisateurs
        fields = ['nom', 'prenom', 'email', 'mot_de_passe', 'numero_de_telephone', 'adresse', 'date_de_naissance']
