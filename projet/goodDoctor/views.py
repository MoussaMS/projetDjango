from django.shortcuts import render, redirect
# from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import check_password
from django.contrib import messages
from .models import Utilisateurs
from django.contrib.auth.hashers import make_password
#from django.shortcuts import HttpResponse
#from django.http import HttpResponse

# Create your views here.
def home(request):
    return render(request, 'home.html')

def medecin_dashboard(request):
    return render(request, 'medecin_dashboard.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        mot_de_passe = request.POST.get('mot_de_passe')

        # Vérifie si l'utilisateur existe
        try:
            utilisateur = Utilisateurs.objects.get(email=email)
            if check_password(mot_de_passe, utilisateur.mot_de_passe):  # Vérifie le mot de passe
                # Stocke l'utilisateur dans la session
                request.session['utilisateur_id'] = utilisateur.id
                request.session['utilisateur_role'] = utilisateur.role

                # Redirige en fonction du rôle
                if utilisateur.role == 'medecin':
                    return redirect('medecin_dashboard') # à faire
                elif utilisateur.role == 'patient':
                    return redirect('patient_dashboard') # à faire
                else:
                    return redirect('home')
            else:
                messages.error(request, 'Mot de passe incorrect.')
        except Utilisateurs.DoesNotExist:
            messages.error(request, 'Aucun compte trouvé avec cet email.')

    return render(request, 'login.html')

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
