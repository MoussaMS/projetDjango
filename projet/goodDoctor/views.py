from django.shortcuts import render, redirect
# from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import check_password
from django.contrib import messages
from .models import Utilisateurs, RendezVous
from .models import Medecin
from django.contrib.auth.hashers import make_password
#from django.shortcuts import HttpResponse
#from django.http import HttpResponse

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

# Create your views here.
def home(request):
    return render(request, 'home.html')

@login_required
def patient_dashboard(request):
    print("Email utilisateur connecté :", request.user.email)  # Debug
    utilisateur = Utilisateurs.objects.get(email=request.user.email)  # Ligne problématique
    rendez_vous = RendezVous.objects.filter(patient=utilisateur).order_by('-date_heure')
    medecins = Medecin.objects.all()

    # Gestion du formulaire
    if request.method == 'POST':
        specialite = request.POST.get('specialite')
        date = request.POST.get('date')
        heure = request.POST.get('heure')
        motif = request.POST.get('motif')

        try:
            medecin = Medecin.objects.get(id=specialite)
            RendezVous.objects.create(
                patient=utilisateur,
                medecin=medecin,
                date_heure=f"{date} {heure}",
                motif=motif,
                statut='en attente'
            )
            messages.success(request, "Rendez-vous pris avec succès.")
        except Medecin.DoesNotExist:
            messages.error(request, "Médecin ou spécialité invalide.")

        return redirect('patient_dashboard')

    return render(request, 'patient_dashboard.html', {
        'rendez_vous': rendez_vous,
        'medecins': medecins,
    })


@login_required
def medecin_dashboard(request):
    if request.session.get('utilisateur_role') != 'medecin':
        return HttpResponseForbidden("Accès réservé aux médecins.")

    # Récupérer l'utilisateur connecté
    utilisateur_id = request.session.get('utilisateur_id')
    utilisateur = Utilisateurs.objects.get(id=utilisateur_id)

    # Récupérer les informations du médecin
    medecin = Medecin.objects.get(utilisateurs=utilisateur)

    # Récupérer les rendez-vous du médecin
    rendez_vous = RendezVous.objects.filter(medecin=medecin).order_by('-date_heure')

    context = {
        'medecin': medecin,
        'rendez_vous': rendez_vous,
    }

    return render(request, 'medecin_dashboard.html', context)


@login_required
def dashboard_responsable(request):
    # if request.Utilisateurs.role != 'responsable':
    #     return HttpResponseForbidden("Accès réservé aux responsables.")
    utilisateur_id = request.session.get('utilisateur_id')
    utilisateur = Utilisateurs.objects.get(id=utilisateur_id)
    context = {
        'prenom_responsable': utilisateur.prenom,
    }
    return render(request, 'dashboard_responsable.html', context)


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        mot_de_passe = request.POST.get('mot_de_passe')

        try:
            # Vérifie si l'utilisateur existe dans la table `Utilisateurs`
            utilisateur = Utilisateurs.objects.get(email=email)
            
            # Vérifie le mot de passe
            if check_password(mot_de_passe, utilisateur.mot_de_passe):
                # Stocke les données utilisateur dans la session
                request.session['utilisateur_id'] = utilisateur.id
                request.session['utilisateur_role'] = utilisateur.role
                
                # Redirection basée sur le rôle
                if utilisateur.role == 'medecin':
                    return redirect('medecin_dashboard')  # Créez cette vue
                elif utilisateur.role == 'patient':
                    return redirect('patient_dashboard')  # Créez cette vue
                elif utilisateur.role == 'responsable':
                    return redirect('dashboard_responsable')  # Vue pour responsables
                else:
                    return redirect('home')  # Page d'accueil par défaut
            else:
                messages.error(request, "Mot de passe incorrect.")
        except Utilisateurs.DoesNotExist:
            messages.error(request, "Aucun compte trouvé avec cet email.")
    return render(request, 'login.html')

def register_patient(request):
    if request.method == "POST":
        nom = request.POST['nom']
        prenom = request.POST['prenom']
        email = request.POST['email']
        mot_de_passe = request.POST['mot_de_passe']
        mot_de_passe_repeat = request.POST['mot_de_passe_repeat']
        # role = request.POST['role']

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
                role='patient'
            )
            utilisateur.save()
            messages.success(request, "Compte créé avec succés !!")
            return redirect('login') # a creer
        except Exception as e:
            messages.error(request, f"Erreur : {e}")
            return redirect ('register')
            
    return render(request, 'register.html')


@login_required
def register_medecin(request):
    # if request.user.role != 'responsable':
    #     return HttpResponseForbidden("Accès réservé aux responsables.")

    if request.method == "POST":
        nom = request.POST['nom']
        prenom = request.POST['prenom']
        email = request.POST['email']
        specialite = request.POST['specialite']
        numero_de_licence = request.POST['numero_de_licence']
        mot_de_passe = request.POST['mot_de_passe']

        try:
            mot_de_passe_hache = make_password(mot_de_passe)
            utilisateur = Utilisateurs.objects.create(
                nom=nom,
                prenom=prenom,
                email=email,
                mot_de_passe=mot_de_passe_hache,
                role='medecin'
            )
            utilisateur.save()
            
            # Créez les informations spécifiques du médecin
            Medecin.objects.create(
                utilisateurs=utilisateur,
                specialite=specialite,
                numero_de_licence=numero_de_licence
            )
            
            messages.success(request, "Compte médecin créé avec succès.")
            return redirect('dashboard_responsable')  # Tableau de bord du responsable
        except Exception as e:
            messages.error(request, f"Erreur : {e}")
            return redirect('register_medecin')

    return render(request, 'register_medecin.html')

def recherche_medecin(request):
    if request.method == 'POST':
        specialite = request.POST.get('specialite')
        medecins = Medecin.objects.filter(specialite__icontains=specialite)
        context = {
            'medecins': medecins,
            'specialite': specialite,
        }
        return render(request, 'recherche_medecin.html', context)
    return redirect('home')

@login_required
def prendre_rendez_vous(request, medecin_id):
    if request.method == 'POST':
        medecin = Medecin.objects.get(id=medecin_id)
        patient = Utilisateurs.objects.get(id=request.session['utilisateur_id'])
        date_heure = request.POST.get('date_heure')
        motif = request.POST.get('motif')

        rendez_vous = RendezVous.objects.create(
            patient=patient,
            medecin=medecin,
            date_heure=date_heure,
            motif=motif,
            statut='en attente'
        )
        rendez_vous.save()
        messages.success(request, "Rendez-vous pris avec succès.")
        return redirect('patient_dashboard')

    medecin = Medecin.objects.get(id=medecin_id)
    context = {
        'medecin': medecin,
    }
    return render(request, 'prendre_rendez_vous.html', context)
