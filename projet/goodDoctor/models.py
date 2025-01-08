from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UtilisateurManager(BaseUserManager):
    def create_user(self, email, mot_de_passe=None, **extra_fields):
        if not email:
            raise ValueError("L'email est obligatoire")
        email = self.normalize_email(email)
        utilisateur = self.model(email=email, **extra_fields)
        utilisateur.set_password(mot_de_passe)
        utilisateur.save(using=self._db)
        return utilisateur

    def create_superuser(self, email, mot_de_passe=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, mot_de_passe, **extra_fields)

#Table Utilisateurs
class Utilisateurs(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('patient', 'Patient'),
        ('medecin', 'Médecin'),
        ('responsable', 'Responsable')
    ]
    email = models.EmailField(unique=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    role = models.CharField(max_length=11, choices=ROLE_CHOICES)
    telephone = models.CharField(max_length=15, blank=True, null=True)  # Nouveau champ

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UtilisateurManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nom', 'prenom']

    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.role})"
    
# Table Profils_Medicaux
class ProfilMedical(models.Model):
    utilisateurs = models.OneToOneField(Utilisateurs, on_delete=models.CASCADE, related_name='profil_medical')
    antecedents_medicaux = models.TextField(blank=True, null=True)
    medicaments = models.TextField(blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    date_de_mise_a_jour = models.DateTimeField(auto_now=True)

    def _str_(self):
        return f"Profil médical de {self.utilisateurs}"


# Table Medecins
class Medecin(models.Model):
    utilisateurs = models.OneToOneField(Utilisateurs, on_delete=models.CASCADE, related_name='medecin')
    specialite = models.CharField(max_length=100, blank=True, null=True)
    numero_de_licence = models.CharField(max_length=50, unique=True)
    horaires_de_travail = models.JSONField(blank=True, null=True)
    evaluation = models.FloatField(blank=True, null=True)

    def _str_(self):
        return f"Dr. {self.utilisateurs.nom} {self.utilisateurs.prenom}"


# Table Rendez_vous
class RendezVous(models.Model):
    STATUT_CHOICES = [
        ('confirmé', 'Confirmé'),
        ('annulé', 'Annulé'),
        ('en attente', 'En attente'),
    ]

    patient = models.ForeignKey(Utilisateurs, on_delete=models.CASCADE, related_name='rendez_vous_patient')
    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE, related_name='rendez_vous_medecin')
    date_heure = models.DateTimeField()
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en attente')
    motif = models.TextField(blank=True, null=True)
    commentaires = models.TextField(blank=True, null=True)

    def _str_(self):
        return f"Rendez-vous: {self.patient} avec {self.medecin} le {self.date_heure}"


# Table Notifications
class Notification(models.Model):
    TYPE_NOTIFICATION_CHOICES = [
        ('rappel_rdv', 'Rappel Rendez-vous'),
        ('rappel_medicaments', 'Rappel Médicaments'),
    ]

    utilisateurs = models.ForeignKey(Utilisateurs, on_delete=models.CASCADE, related_name='notifications')
    type_notification = models.CharField(max_length=20, choices=TYPE_NOTIFICATION_CHOICES)
    date_heure_envoi = models.DateTimeField(blank=True, null=True)
    contenu = models.TextField(blank=True, null=True)

    def _str_(self):
        return f"Notification pour {self.utilisateurs}"


# Table Evaluations
class Evaluation(models.Model):
    rendez_vous = models.ForeignKey(RendezVous, on_delete=models.CASCADE, related_name='evaluations')
    patient = models.ForeignKey(Utilisateurs, on_delete=models.CASCADE, related_name='evaluations_patient')
    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE, related_name='evaluations_medecin')
    note = models.IntegerField()
    commentaire = models.TextField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return f"Évaluation de {self.medecin} par {self.patient}"


# Table Messages
class Message(models.Model):
    STATUT_CHOICES = [
        ('lu', 'Lu'),
        ('non lu', 'Non lu'),
    ]

    expediteur = models.ForeignKey(Utilisateurs, on_delete=models.CASCADE, related_name='messages_envoyes')
    destinataire = models.ForeignKey(Utilisateurs, on_delete=models.CASCADE, related_name='messages_recus')
    contenu = models.TextField()
    date_heure = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='non lu')

    def _str_(self):
        return f"Message de {self.expediteur} à {self.destinataire}"


# Table Disponibilites_Medecins
class DisponibiliteMedecin(models.Model):
    JOUR_CHOICES = [
        ('lundi', 'Lundi'),
        ('mardi', 'Mardi'),
        ('mercredi', 'Mercredi'),
        ('jeudi', 'Jeudi'),
        ('vendredi', 'Vendredi'),
        ('samedi', 'Samedi'),
        ('dimanche', 'Dimanche'),
    ]

    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE, related_name='disponibilites')
    jour = models.CharField(max_length=10, choices=JOUR_CHOICES)
    heure_de_debut = models.TimeField()
    heure_de_fin = models.TimeField()

    def _str_(self):
        return f"Disponibilité: {self.jour} {self.heure_de_debut} - {self.heure_de_fin}"


# Table Historique_Acces
class HistoriqueAcces(models.Model):
    utilisateurs = models.ForeignKey(Utilisateurs, on_delete=models.CASCADE, related_name='historique_acces')
    date_heure = models.DateTimeField(auto_now_add=True)
    type_acces = models.CharField(max_length=100)
    ip_adresse = models.GenericIPAddressField()

    def _str_(self):
        return f"Accès de {self.utilisateurs} à {self.date_heure}"
    
# Table Historique_Medical
class HistoriqueMedical(models.Model):
    patient = models.ForeignKey(Utilisateurs, on_delete=models.CASCADE, related_name='historique_medical')
    date = models.DateTimeField(auto_now_add=True)
    description = models.TextField()  # Expliquer les éléments médicaux importants
    medecin_responsable = models.ForeignKey(Medecin, on_delete=models.SET_NULL, null=True, related_name='historiques_crees')

    def __str__(self):
        return f"Historique médical de {self.patient.nom} {self.patient.prenom} (par {self.medecin_responsable})"
