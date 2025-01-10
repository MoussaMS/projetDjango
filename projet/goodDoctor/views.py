from django.shortcuts import render, redirect
#from django.contrib.auth.hashers import check_password
from django.contrib import messages
from .models import Utilisateurs, RendezVous, HistoriqueMedical, DisponibiliteMedecin
from .models import Medecin
#from django.contrib.auth.hashers import make_password
#from django.shortcuts import HttpResponse
#from django.http import HttpResponse

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
#from django.contrib.auth import authenticate
from django.contrib.auth import login, logout
# import 06/01
from django.db.models import Q, Count
from django.db.models import Prefetch
import re
from django.views.decorators.cache import never_cache

# Create your views here.
def home(request):
    medecins = Medecin.objects.select_related('utilisateurs')  # Optimisation pour éviter les requêtes multiples
    return render(request, 'home.html', {'medecins': medecins})


@never_cache
@login_required
def patient_dashboard(request):
    utilisateur = request.user  # Utilisateur connecté via @login_required

    # Vérifiez que l'utilisateur est un patient
    if utilisateur.role != 'patient':
        messages.error(request, "Accès réservé aux patients.")
        return redirect('login')

    # Récupérer les rendez-vous actuels de l'utilisateur (patient)
    rendez_vous = RendezVous.objects.filter(patient=utilisateur).order_by('-date_heure')

    # Vérifier si un médecin a été sélectionné avant la connexion
    medecin_id = request.session.get('selected_medecin_id')
    if medecin_id:
        try:
            medecin = Medecin.objects.get(id=medecin_id)
            medecins = [medecin]
            confirmation_message = f"Veuillez confirmer votre prise de rendez-vous avec Dr. {medecin.utilisateurs.prenom} {medecin.utilisateurs.nom}"
        except Medecin.DoesNotExist:
            messages.error(request, "Médecin sélectionné introuvable.")
            medecins = Medecin.objects.all()
            confirmation_message = None
    else:
        medecins = Medecin.objects.all()
        confirmation_message = None

    # Récupérer les disponibilités des médecins
    disponibilites = DisponibiliteMedecin.objects.filter(medecin__in=medecins)

    context = {
        'utilisateur': utilisateur,
        'rendez_vous': rendez_vous,
        'medecins': medecins,
        'disponibilites': disponibilites,
        'confirmation_message': confirmation_message,
    }

    return render(request, 'patient_dashboard.html', context)


@never_cache # Cela permet d'empêcher la mise en cache des réponses HTTP pour quand se déconnecte, on ne plus retourner à la page
@login_required
def medecin_dashboard(request):
    # Vérifier que l'utilisateur connecté est un médecin
    utilisateur = request.user
    if utilisateur.role != 'medecin':
        return HttpResponseForbidden("Accès réservé aux médecins.")

    try:
        # Récupérer les informations du médecin
        medecin = Medecin.objects.get(utilisateurs=utilisateur)
    except Medecin.DoesNotExist:
        messages.error(request, "Profil médecin introuvable.")
        return redirect('login')

    # Récupérer les rendez-vous et historiques médicaux
    rendez_vous = RendezVous.objects.filter(medecin=medecin).order_by('-date_heure')
    historiques_medicaux = (
        HistoriqueMedical.objects.filter(patient__rendez_vous_patient__medecin=medecin)
        .distinct()
        .order_by('-date')
    )

    if request.method == 'POST':
        # Gestion de la mise à jour du téléphone
        telephone = request.POST.get('telephone')
        if telephone:
            if not re.match(r'^\+?\d{7,15}$', telephone):
                messages.error(request, "Veuillez entrer un numéro de téléphone valide.")
            else:
                utilisateur.telephone = telephone
                utilisateur.save()
                messages.success(request, "Votre numéro de téléphone a été mis à jour avec succès.")

        # Gestion de l'ajout d'une disponibilité
        jour = request.POST.get('jour')
        heure_de_debut = request.POST.get('heure_de_debut')
        heure_de_fin = request.POST.get('heure_de_fin')

        if jour and heure_de_debut and heure_de_fin:
            try:
                DisponibiliteMedecin.objects.create(
                    medecin=medecin,
                    jour=jour,
                    heure_de_debut=heure_de_debut,
                    heure_de_fin=heure_de_fin
                )
                messages.success(request, "Votre disponibilité a été ajoutée avec succès.")
            except Exception as e:
                messages.error(request, f"Erreur lors de l'ajout de la disponibilité: {str(e)}")

    context = {
        'medecin': medecin,
        'rendez_vous': rendez_vous,
        'historiques_medicaux': historiques_medicaux,
    }

    return render(request, 'medecin_dashboard.html', context)

@never_cache
@login_required
def dashboard_responsable(request):
    if request.user.role != 'responsable':
        return HttpResponseForbidden("Accès réservé aux responsables.")
    
    utilisateur = request.user
    context = {
        'prenom_responsable': utilisateur.prenom,
    }
    return render(request, 'dashboard_responsable.html', context)



def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        mot_de_passe = request.POST.get('mot_de_passe')

        # Authentification avec le backend personnalisé
        from django.contrib.auth import authenticate
        utilisateur = authenticate(request, email=email, password=mot_de_passe)

        if utilisateur is not None:
            # Stocker des données supplémentaires dans la session
            request.session['utilisateur_id'] = utilisateur.id
            request.session['utilisateur_role'] = utilisateur.role

            # Connecter l'utilisateur
            login(request, utilisateur)

            # Redirection selon le rôle
            if utilisateur.role == 'medecin':
                return redirect('medecin_dashboard')
            elif utilisateur.role == 'patient':
                return redirect('patient_dashboard')
            elif utilisateur.role == 'responsable':
                return redirect('dashboard_responsable')
        else:
            messages.error(request, "Email ou mot de passe incorrect.")

    return render(request, 'login.html')


# Pour la déconnexion
def logout_view(request):
    logout(request)
    return redirect('home')


def register_patient(request):
    if request.method == "POST":
        nom = request.POST['nom']
        prenom = request.POST['prenom']
        email = request.POST['email']
        mot_de_passe = request.POST['mot_de_passe']
        mot_de_passe_repeat = request.POST['mot_de_passe_repeat']

        if mot_de_passe != mot_de_passe_repeat:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return redirect('register')

        try:
            # Utiliser create_user qui gère automatiquement le hachage du mot de passe
            utilisateur = Utilisateurs.objects.create_user(
                email=email,
                mot_de_passe=mot_de_passe,
                nom=nom,
                prenom=prenom,
                role='patient'
            )
            utilisateur.save()
            messages.success(request, "Compte créé avec succès !")
            return redirect('login')  # À rediriger vers la page de login
        except Exception as e:
            messages.error(request, f"Erreur : {e}")
            return redirect('register')

    return render(request, 'register.html')

@login_required
def register_medecin(request):
    if request.user.role != 'responsable':
        return HttpResponseForbidden("Accès réservé aux responsables.")

    if request.method == "POST":
        nom = request.POST['nom']
        prenom = request.POST['prenom']
        email = request.POST['email']
        specialite = request.POST['specialite']
        numero_de_licence = request.POST['numero_de_licence']
        mot_de_passe = request.POST['mot_de_passe']

        try:
            # Utiliser create_user qui gère automatiquement le hachage du mot de passe
            utilisateur = Utilisateurs.objects.create_user(
                email=email,
                mot_de_passe=mot_de_passe,
                nom=nom,
                prenom=prenom,
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


# Modif pris sur la branche de Fodé 06/01
# modif du 29/12
def recherche_medecin(request):
    query = request.POST.get('query', None)
    medecins = []

    if query:
        # Rechercher dans les noms et les spécialités
        medecins = Medecin.objects.filter(
            Q(utilisateurs__nom__icontains=query) |
            Q(utilisateurs__prenom__icontains=query) |
            Q(specialite__icontains=query)
        ).annotate(num_rendez_vous=Count('rendez_vous_medecin')).order_by('num_rendez_vous', 'rendez_vous_medecin__date_heure')
    return render(request, 'recherche_medecin.html', {
        'medecins': medecins,
        'query': query
    })


@login_required
def prendre_rendez_vous(request, medecin_id):
    if request.method == 'POST':
        medecin = Medecin.objects.get(id=medecin_id)
        patient = request.user
        date = request.POST.get('date')
        heure = request.POST.get('heure')
        motif = request.POST.get('motif')

        # Combiner la date et l'heure
        date_heure = f"{date} {heure}"

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

    return redirect('patient_dashboard')


#modif du 30/12
@login_required
def get_medecins_by_specialite(request):
    specialite_id = request.GET.get('specialite_id')
    if not specialite_id:
        return JsonResponse({'error': 'Spécialité invalide.'}, status=400)

    medecins = Medecin.objects.filter(specialite=specialite_id).values('id', 'nom')
    return JsonResponse({'medecins': list(medecins)})

from django.http import JsonResponse

@login_required
def get_medecins(request):
    specialite_id = request.GET.get('specialite_id')  # Récupérer l'ID de la spécialité
    if not specialite_id:
        return JsonResponse({'error': 'Spécialité non spécifiée'}, status=400)

    # Récupérer les médecins correspondant à cette spécialité
    medecins = Medecin.objects.filter(specialite=specialite_id).values('id', 'nom')

    if not medecins.exists():
        return JsonResponse({'error': 'Aucun médecin trouvé'}, status=404)

    return JsonResponse({'medecins': list(medecins)})