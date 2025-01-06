from django.contrib.auth.backends import BaseBackend
from .models import Utilisateurs
from django.contrib.auth.hashers import check_password

class EmailBackend(BaseBackend):
    def authenticate(self, request, email=None, password=None):
        try:
            utilisateur = Utilisateurs.objects.get(email=email)
            if utilisateur and check_password(password, utilisateur.password):
                return utilisateur
        except Utilisateurs.DoesNotExist:
            return None
