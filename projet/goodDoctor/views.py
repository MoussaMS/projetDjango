from django.shortcuts import render, redirect
#from django.contrib.auth.hashers import check_password
from django.contrib import messages
from .models import Utilisateurs, RendezVous
from .models import Medecin
#from django.contrib.auth.hashers import make_password
#from django.shortcuts import HttpResponse
#from django.http import HttpResponse

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
#from django.contrib.auth import authenticate
from django.contrib.auth import login
# import 06/01
from django.db.models import Q, Count


# Create your views here.
def home(request):
    medecins = Medecin.objects.select_related('utilisateurs')  # Optimisation pour éviter les requêtes multiples
    return render(request, 'home.html', {'medecins': medecins})

@login_required
def patient_dashboard(request):
    try:
        utilisateur_id = request.session.get('utilisateur_id')
        utilisateur = Utilisateurs.objects.get(id=utilisateur_id)

    #utilisateur = Utilisateurs.objects.get(email=request.user.email)  # Utilisateur connecté
    except Utilisateurs.DoesNotExist:
        messages.error(request, "Utilisateur non trouvé.")
        return redirect('login')

    # Récupérer les spécialités uniques à partir des médecins
    specialites = Medecin.objects.values_list('specialite', flat=True).distinct()

    # Récupérer l'ID du médecin depuis la requête GET (si disponible)
    medecin_id = request.session.get('medecin_id')
    medecin = None
    if medecin_id:
        try:
            medecin=Medecin.objects.get(id=medecin_id)
        except Medecin.DoesNotExist:
            messages.error(request, "médecin non trouvé")
            return redirect('recherche_medecin')

    # Récupérer les rendez-vous actuels de l'utilisateur
    rendez_vous = RendezVous.objects.filter(patient=utilisateur).order_by('-date_heure')

    # Vérifier si une spécialité est sélectionnée
    specialite_selected = request.GET.get('specialite')
    if specialite_selected:
        # Filtrer les médecins par spécialité
        medecins = Medecin.objects.filter(specialite=specialite_selected)
    else:
        # Si aucune spécialité n'est sélectionnée, afficher tous les médecins
        medecins = Medecin.objects.all()

    if request.method == 'POST':
        # Récupérer les informations du formulaire
        specialite = request.POST.get('specialite')
        date = request.POST.get('date')
        heure = request.POST.get('heure')
        motif = request.POST.get('motif')
        medecin_id = request.POST.get('medecin_id')

        # Vérifier que tous les champs sont remplis
        if not all([specialite, date, heure, motif, medecin_id]):
            messages.error(request, "Veuillez remplir tous les champs.")
        else:
            try:
                # Récupérer le médecin sélectionné
                medecin = Medecin.objects.get(id=medecin_id)
                date_heure = f"{date} {heure}"
                RendezVous.objects.create(
                    patient=utilisateur,
                    medecin=medecin,
                    date_heure=date_heure,
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
        'specialites': specialites,
        'utilisateur': utilisateur,
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