from django.db import models

#Table Utilisateurs
class Utilisateurs(models.Model):
    ROLE_CHOICES = [
        ('patient', 'Patient'),
        ('medecin', 'Médecin'),
    ]
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    mot_de_passe = models.CharField(max_length=255)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    numero_de_telephone = models.CharField(max_length=20, blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)
    date_de_naissance = models.DateField(blank=True, null=True)

    def __str__(self) :
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