# sigep/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os
from django.db.models.signals import post_save
from django.dispatch import receiver

# ============================================
# FONCTIONS POUR GÉNÉRER LES CHEMINS DE FICHIERS
# ============================================

def chemin_photo_profil(instance, filename):
    """
    Génère le chemin pour les photos de profil
    Ex: medias/upload_profils/user_1_profil_20250319_143022.jpg
    """
    ext = filename.split('.')[-1]
    filename = f"user_{instance.user.id}_profil_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
    return os.path.join('upload_profils', filename)

def chemin_photo_projet(instance, filename):
    """
    Génère le chemin pour les photos de projet
    Ex: medias/upload_projets/projet_15_20250319_143022.jpg
    """
    ext = filename.split('.')[-1]
    filename = f"projet_{instance.id_projet}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
    return os.path.join('upload_projets', filename)

def chemin_photo_phase(instance, filename):
    """
    Génère le chemin pour les photos de phase
    Ex: medias/upload_phases/phase_8_20250319_143022.jpg
    """
    ext = filename.split('.')[-1]
    filename = f"phase_{instance.id_phase}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
    return os.path.join('upload_phases', filename)


# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     """Crée automatiquement un profil lors de la création d'un utilisateur"""
#     if created:
#         UserProfile.objects.get_or_create(
#             user=instance,
#             defaults={
#                 'role': 'observateur',
#                 'date_inscription': instance.date_joined
#             }
#         )

# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
#     """Sauvegarde le profil quand l'utilisateur est sauvegardé"""
#     try:
#         if hasattr(instance, 'profile'):
#             instance.profile.save()
#     except:
#         pass


# ============================================
# MODÈLE ENTREPRISE
# ============================================
class Entreprise(models.Model):
    """
    Modèle pour les entreprises exécutantes
    Table: entreprises
    """
    id_entreprise = models.AutoField(primary_key=True)
    
    nom = models.CharField(
        max_length=150, 
        verbose_name="Nom de l'entreprise"
    )
    
    adresse = models.TextField(
        verbose_name="Adresse"
    )
    
    email = models.CharField(
        max_length=150, 
        verbose_name="Email"
    )
    
    telephone = models.CharField(
        max_length=20, 
        verbose_name="Téléphone"
    )
    
    domaine_activite = models.CharField(
        max_length=100, 
        verbose_name="Domaine d'activité"
    )
    
    representant = models.OneToOneField(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='entreprise_representee',
        verbose_name="Représentant principal"
    )
    
    def __str__(self):
        return self.nom
    
    def get_employes(self):
        """Récupère tous les employés (hors représentant)"""
        return User.objects.filter(
            profile__entreprise=self,
            profile__est_employe=True
        )
    
    def get_tous_utilisateurs(self):
        """Récupère tous les utilisateurs (représentant + employés)"""
        return User.objects.filter(profile__entreprise=self)
    
    class Meta:
        db_table = 'entreprises'
        verbose_name = "Entreprise"
        verbose_name_plural = "Entreprises"


# ============================================
# MODÈLE PROFIL UTILISATEUR (extension de User)
# ============================================
class UserProfile(models.Model):
    """
    Extension du modèle User de Django avec les informations supplémentaires
    """
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('chef', 'Chef de projet (Ministère)'),
        ('entreprise', 'Entreprise exécutante'),
        ('observateur', 'Observateur public'),
    ]
    
    SEXE_CHOIX = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
        ('A', 'Autre'),
    ]
    
    # Lien avec l'utilisateur Django
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile'
    )
    
    # Informations personnelles
    telephone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        verbose_name="Téléphone"
    )
    
    profession = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="Profession"
    )
    
    sexe = models.CharField(
        max_length=1, 
        choices=SEXE_CHOIX, 
        blank=True, 
        null=True,
        verbose_name="Sexe"
    )
    
    date_inscription = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date d'inscription"
    )
    
    # 📸 PHOTO DE PROFIL
    photo = models.ImageField(
        upload_to=chemin_photo_profil,
        verbose_name="Photo de profil",
        blank=True,
        null=True,
        help_text="Photo de profil (formats acceptés: JPG, PNG)"
    )
    
    # Adresse
    commune = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="Commune"
    )
    
    quartier = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="Quartier"
    )
    
    avenue = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="Avenue"
    )
    
    # Rôle dans SIGEP
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='observateur',
        verbose_name="Rôle"
    )
    
    entreprise = models.ForeignKey(
        Entreprise,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employes',
        verbose_name="Entreprise"
    )
    
    est_employe = models.BooleanField(
        default=False,
        verbose_name="Est un employé"
    )
    
    # Pour savoir qui a ajouté cet employé
    ajoute_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employes_ajoutes',
        verbose_name="Ajouté par"
    )
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    def est_representant(self):
        """Vérifie si l'utilisateur est le représentant d'une entreprise"""
        return hasattr(self.user, 'entreprise_representee')
    
    def est_employe_de_entreprise(self):
        """Vérifie si l'utilisateur est un employé"""
        return self.est_employe and self.entreprise is not None
    
    
    def est_chef(self):
        return self.role == 'chef'
    
    def est_entreprise(self):
        return self.role == 'entreprise'
    
    def est_observateur(self):
        return self.role == 'observateur'
    
    def est_admin(self):
        return self.role == 'admin' or self.user.is_superuser
    class Meta:
        db_table = 'sigep_userprofile'
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateurs"


# ============================================
# MODÈLE MINISTÈRE (Chef de projet)
# ============================================
class ChefProjet(models.Model):
    """
    Modèle pour les ministères (chefs de projet)
    Table: chefs_projet
    """
    id_chef = models.AutoField(primary_key=True)
    
    nom_ministere = models.CharField(
        max_length=150, 
        verbose_name="Nom du ministère"
    )
    
    description = models.TextField(
        blank=True, 
        verbose_name="Description"
    )
    
    # Lien avec l'utilisateur (optionnel)
    user = models.OneToOneField(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='chef_projet',
        verbose_name="Utilisateur associé"
    )
    
    class Meta:
        db_table = 'chefs_projet'
        verbose_name = "Ministère (Chef de projet)"
        verbose_name_plural = "Ministères (Chefs de projet)"
    
    def __str__(self):
        return self.nom_ministere




# ============================================
# MODÈLE PROJET
# ============================================
class Projet(models.Model):
    """
    Modèle pour les projets publics
    Table: projets
    """
    STATUT_CHOIX = [
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('a_venir', 'À venir'),
        ('suspendu', 'Suspendu'),
         ('annule', 'Annulé')
    ]
    
    id_projet = models.AutoField(primary_key=True)
    
    titre = models.CharField(
        max_length=150, 
        verbose_name="Titre du projet"
    )
    
    description = models.TextField(
        verbose_name="Description"
    )
    
    budget_previsionnel = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        verbose_name="Budget prévisionnel"
    )
    
    date_debut = models.DateField(
        verbose_name="Date de début"
    )
    
    date_fin_prevue = models.DateField(
        verbose_name="Date de fin prévue"
    )
    
    statut = models.CharField(
        max_length=20, 
        choices=STATUT_CHOIX, 
        default='a_venir',
        verbose_name="Statut"
    )
    
    province = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Province"
    )
    
    # 📸 PHOTO DU PROJET
    photo = models.ImageField(
        upload_to=chemin_photo_projet,
        verbose_name="Photo du projet",
        blank=True,
        null=True,  # True pour permettre les projets sans photo
        help_text="Image principale du projet (formats: JPG, PNG)"
    )
    
    # Relations
    createur = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='projets_crees',
        verbose_name="Créateur"
    )
    
    chef_projet = models.ForeignKey(
        ChefProjet, 
        on_delete=models.SET_NULL,
        null=True,
        related_name='projets',
        verbose_name="Ministère responsable"
    )
    
    entreprise = models.ForeignKey(
        Entreprise, 
        on_delete=models.SET_NULL,
        null=True,
        related_name='projets',
        verbose_name="Entreprise exécutante"
    )

    # Domaine d'activité
    domaine_activite = models.CharField(
        max_length=100,
        verbose_name="Domaine d'activité",
        help_text="Ex: Construction, Éducation, Santé, Infrastructures..."
    )
    
    def peut_ajouter_phase(self):
        """Vérifie si on peut ajouter une phase à ce projet"""
        return self.statut == 'en_cours'
    
    def peut_modifier_phase(self):
        """Vérifie si on peut modifier une phase"""
        return self.statut == 'en_cours'
    
    def peut_changer_statut(self, nouveau_statut):
        """Vérifie si le changement de statut est autorisé"""
        # Un projet terminé ne peut plus changer de statut
        if self.statut == 'termine':
            return False
        # Un projet annulé ne peut plus changer de statut (sauf admin)
        if self.statut == 'annule':
            return False
        return True
    
    class Meta:
        db_table = 'projets'
        verbose_name = "Projet"
        verbose_name_plural = "Projets"
        ordering = ['-date_debut']
    
    def __str__(self):
        return self.titre
    
    def budget_consomme_total(self):
        """Calcule le budget total consommé"""
        return self.suivis_budget.aggregate(
            total=models.Sum('budget_consomme')
        )['total'] or 0
    
    def avancement_moyen(self):
        """Calcule l'avancement moyen basé sur les phases"""
        return self.phases.aggregate(
            avg=models.Avg('pourcentage_avancement')
        )['avg'] or 0
    
    def note_moyenne(self):
        """Calcule la note moyenne du projet"""
        return self.avis.aggregate(
            avg=models.Avg('note')
        )['avg'] or 0


# ============================================
# MODÈLE PHASE
# ============================================
class Phase(models.Model):
    """
    Modèle pour les phases d'un projet
    Table: phases
    """
    id_phase = models.AutoField(primary_key=True)
    
    nom_phase = models.CharField(
        max_length=100, 
        verbose_name="Nom de la phase"
    )
    
    description = models.TextField(
        blank=True, 
        verbose_name="Description"
    )
    
    date_debut = models.DateField(
        verbose_name="Date de début"
    )
    
    date_fin = models.DateField(
        null=True, 
        blank=True, 
        verbose_name="Date de fin"
    )
    
    pourcentage_avancement = models.IntegerField(
        default=0,
        verbose_name="Pourcentage d'avancement"
    )
    
    # 📸 PHOTO DE PHASE
    photo = models.ImageField(
        upload_to=chemin_photo_phase,
        verbose_name="Photo de la phase",
        blank=True,
        null=True,
        help_text="Photo illustrant l'avancement (optionnelle)"
    )
    
    # Relation avec le projet
    projet = models.ForeignKey(
        Projet, 
        on_delete=models.CASCADE,
        related_name='phases',
        verbose_name="Projet"
    )
    
    class Meta:
        db_table = 'phases'
        verbose_name = "Phase"
        verbose_name_plural = "Phases"
        ordering = ['date_debut']
    
    def __str__(self):
        return f"{self.projet.titre} - {self.nom_phase}"
    
    def est_terminee(self):
        return self.pourcentage_avancement >= 100


# ============================================
# MODÈLE SUIVI BUDGÉTAIRE
# ============================================
class SuiviBudget(models.Model):
    """
    Modèle pour le suivi du budget consommé
    Table: suivi_budget
    """
    id_suivi = models.AutoField(primary_key=True)
    
    budget_consomme = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        verbose_name="Budget consommé"
    )
    
    date_mise_a_jour = models.DateField(
        verbose_name="Date de mise à jour"
    )
    
    # Relation avec le projet
    projet = models.ForeignKey(
        'Projet', 
        on_delete=models.CASCADE,
        related_name='suivis_budget',
        verbose_name="Projet"
    )
    
    # Lien avec la phase (optionnel)
    phase = models.ForeignKey(
        'Phase',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='depenses',
        verbose_name="Phase"
    )
    
    # Commentaire optionnel
    commentaire = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Commentaire"
    )
    
    class Meta:
        db_table = 'suivi_budget'
        verbose_name = "Suivi budgétaire"
        verbose_name_plural = "Suivis budgétaires"
        ordering = ['-date_mise_a_jour']
    
    def __str__(self):
        return f"{self.projet.titre} - {self.date_mise_a_jour}"
# ============================================
# MODÈLE COMMENTAIRE
# ============================================
class Commentaire(models.Model):
    """
    Modèle pour les commentaires sur les projets
    Table: commentaires
    """
    id_commentaire = models.AutoField(primary_key=True)
    
    contenu = models.TextField(
        verbose_name="Commentaire"
    )
    
    date_commentaire = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date du commentaire"
    )
    
    # Relations
    utilisateur = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='commentaires',
        verbose_name="Utilisateur"
    )
    
    projet = models.ForeignKey(
        Projet, 
        on_delete=models.CASCADE,
        related_name='commentaires',
        verbose_name="Projet"
    )
    
    class Meta:
        db_table = 'commentaires'
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
        ordering = ['-date_commentaire']
    
    def __str__(self):
        return f"{self.utilisateur.username} - {self.projet.titre[:30]}..."



# ============================================
# MODÈLE AVIS (NOTE) AVEC COMMENTAIRE
# ============================================
class Avis(models.Model):
    """
    Modèle pour les notes/avis sur les projets
    Table: avis
    """
    NOTE_CHOIX = [(i, f"{i} étoile{'s' if i > 1 else ''}") for i in range(1, 6)]
    
    id_avis = models.AutoField(primary_key=True)
    
    note = models.IntegerField(
        choices=NOTE_CHOIX,
        verbose_name="Note"
    )
    
    # ✅ NOUVEAU CHAMP : commentaire optionnel
    commentaire = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaire (optionnel)"
    )
    
    date_avis = models.DateField(
        default=timezone.now,
        verbose_name="Date de l'avis"
    )
    
    # Relations
    utilisateur = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='avis',
        verbose_name="Utilisateur"
    )
    
    projet = models.ForeignKey(
        Projet, 
        on_delete=models.CASCADE,
        related_name='avis',
        verbose_name="Projet"
    )
    
    class Meta:
        db_table = 'avis'
        verbose_name = "Avis"
        verbose_name_plural = "Avis"
        unique_together = (('utilisateur', 'projet'),)  # Un avis par utilisateur par projet
        ordering = ['-date_avis']
    
    def __str__(self):
        return f"{self.utilisateur.username} - {self.projet.titre} - {self.note}★"
    

# ============================================
# MODÈLE PROJET SUIVI (FAVORIS)
# ============================================
class ProjetSuivi(models.Model):
    """
    Modèle pour les projets suivis par les utilisateurs (favoris)
    Table: projets_suivis
    """
    id_suivi = models.AutoField(primary_key=True)
    
    date_suivi = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date du suivi"
    )
    
    # Relations
    utilisateur = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='projets_suivis',
        verbose_name="Utilisateur"
    )
    
    projet = models.ForeignKey(
        Projet, 
        on_delete=models.CASCADE,
        related_name='suivi_par',
        verbose_name="Projet"
    )
    
    class Meta:
        db_table = 'projets_suivis'
        verbose_name = "Projet suivi"
        verbose_name_plural = "Projets suivis"
        unique_together = (('utilisateur', 'projet'),)  # Un utilisateur ne peut suivre qu'une fois
        ordering = ['-date_suivi']
    
    def __str__(self):
        return f"{self.utilisateur.username} suit {self.projet.titre}"