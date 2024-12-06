from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Utilisateurs
from django.contrib.auth.hashers import make_password
from django.shortcuts import HttpResponse
from django.http import HttpResponse

# Create your views here.
def index(request):
    return HttpResponse("Bienvenue sur mon site de Planification santé !!")

def register(request):
    if request.method == "POST":
        nom = request.POST['nom']
        prenom = request.POST['prenom']
        email = request.POST['email']
        mot_de_passe = request.POST['mot_de_passe']
        mot_de_passe_repeat = request.POST['mot_de_passe_repeat']
        role = request.POST['role']

        if mot_de_passe != mot_de_passe_repeat:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return redirect('register')
        
        try:
            mot_de_passe_hache = make_password(mot_de_passe)
            utilisateur = Utilisateurs.objects.create(
                nom=nom, 
                prenom=prenom, 
                email=email, 
                mot_de_passe=mot_de_passe_hache,
                role=role
            )
            utilisateur.save()
            messages.success(request, "Compte créé avec succés !!")
            return redirect('login') # a creer
        except Exception as e:
            messages.error(request, f"Erreur : {e}")
            return redirect ('register')
            
    return render(request, 'register.html')
