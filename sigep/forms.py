# sigep/forms.py
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import UserProfile, ChefProjet, Entreprise, Projet, Phase, Commentaire, Avis, SuiviBudget

# ============================================
# CHOIX POUR LES CHAMPS
# ============================================
SEXE_CHOIX = [
    ('M', 'Masculin'),
    ('F', 'Féminin'),
    ('A', 'Autre'),
]

COMMUNE_CHOIX = [
    ('kinshasa', 'Kinshasa'),
    ('lubumbashi', 'Lubumbashi'),
    ('mbujimayi', 'Mbuji-Mayi'),
    ('kananga', 'Kananga'),
    ('kisangani', 'Kisangani'),
    ('goma', 'Goma'),
    ('bukavu', 'Bukavu'),
]


# ============================================
# FORMULAIRE D'INSCRIPTION
# ============================================
class InscriptionForm(UserCreationForm):
    """
    Formulaire d'inscription - Crée un utilisateur avec profil observateur
    """
    # Champs de base
    nom = forms.CharField(
        max_length=100,
        required=True,
        label="Nom",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez votre nom'
        })
    )
    
    prenom = forms.CharField(
        max_length=100,
        required=True,
        label="Prénom",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez votre prénom'
        })
    )
    
    email = forms.EmailField(
        required=True,
        label="Adresse email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'exemple@email.com'
        })
    )
    
    telephone = forms.CharField(
        max_length=20,
        required=True,
        label="Téléphone",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+243 XXX XXX XXX'
        })
    )
    
    sexe = forms.ChoiceField(
        choices=SEXE_CHOIX,
        required=True,
        label="Sexe",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    commune = forms.ChoiceField(
        choices=COMMUNE_CHOIX,
        required=True,
        label="Commune",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    quartier = forms.CharField(
        max_length=100,
        required=True,
        label="Quartier",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez votre quartier'
        })
    )
    
    avenue = forms.CharField(
        max_length=100,
        required=True,
        label="Avenue",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez votre avenue'
        })
    )
    
    profession = forms.CharField(
        max_length=100,
        required=True,
        label="Profession",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez votre profession'
        })
    )
    
    date_inscription = forms.DateTimeField(
        initial=timezone.now,
        required=False,
        widget=forms.HiddenInput()
    )
    
    class Meta:
        model = User
        fields = ('username', 'nom', 'prenom', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Styliser les champs de UserCreationForm
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': "Nom d'utilisateur"
        })
        
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Mot de passe'
        })
        
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmer le mot de passe'
        })
        
        # Labels
        self.fields['username'].label = "Nom d'utilisateur"
        self.fields['password1'].label = "Mot de passe"
        self.fields['password2'].label = "Confirmation"
    
    def clean_email(self):
        """Vérifie que l'email n'est pas déjà utilisé"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cet email est déjà utilisé.")
        return email
    
    def save(self, commit=True):
        """Sauvegarde l'utilisateur et crée son profil (observateur par défaut)"""
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['prenom']
        user.last_name = self.cleaned_data['nom']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            # Créer le profil utilisateur avec rôle observateur par défaut
            UserProfile.objects.create(
                user=user,
                telephone=self.cleaned_data['telephone'],
                sexe=self.cleaned_data['sexe'],
                commune=self.cleaned_data['commune'],
                quartier=self.cleaned_data['quartier'],
                avenue=self.cleaned_data['avenue'],
                profession=self.cleaned_data['profession'],
                role='observateur',  # Toujours observateur à l'inscription
                date_inscription=timezone.now()
            )
        return user


# ============================================
# FORMULAIRE DE CONNEXION
# ============================================
class ConnexionForm(forms.Form):
    """
    Formulaire de connexion personnalisé (username ou email)
    """
    username = forms.CharField(
        max_length=100,
        required=True,
        label="Nom d'utilisateur ou Email",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom d\'utilisateur ou email'
        })
    )
    
    password = forms.CharField(
        required=True,
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mot de passe'
        })
    )
    
    remember_me = forms.BooleanField(
        required=False,
        label="Se souvenir de moi",
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        
        if username and password:
            # Essayer avec username
            user = authenticate(username=username, password=password)
            
            # Si échec, essayer avec email
            if user is None:
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass
            
            if user is None:
                raise forms.ValidationError(
                    "Nom d'utilisateur/email ou mot de passe incorrect."
                )
            
            if not user.is_active:
                raise forms.ValidationError("Ce compte est désactivé.")
            
            cleaned_data['user'] = user
        
        return cleaned_data


# ============================================
# FORMULAIRE DE MODIFICATION DU PROFIL
# ============================================
class UserProfileForm(forms.ModelForm):
    """Formulaire pour modifier le profil utilisateur"""
    
    class Meta:
        model = UserProfile
        fields = ['telephone', 'sexe', 'commune', 'quartier', 'avenue', 'profession', 'photo']
        widgets = {
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'sexe': forms.Select(attrs={'class': 'form-control'}),
            'commune': forms.Select(attrs={'class': 'form-control'}),
            'quartier': forms.TextInput(attrs={'class': 'form-control'}),
            'avenue': forms.TextInput(attrs={'class': 'form-control'}),
            'profession': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }


class UserForm(forms.ModelForm):
    """Formulaire pour modifier les infos de base de l'utilisateur"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    
    def clean_email(self):
        """Vérifie que l'email n'est pas déjà pris par un autre utilisateur"""
        email = self.cleaned_data.get('email')
        if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise forms.ValidationError("Cet email est déjà utilisé.")
        return email


# ============================================
# FORMULAIRE POUR PROJET
# ============================================
class ProjetForm(forms.ModelForm):
    """Formulaire pour créer/modifier un projet"""
    
    class Meta:
        model = Projet
        fields = [
            'titre', 'description', 'domaine_activite',  # ← Ajouter domaine_activite
            'budget_previsionnel', 'date_debut', 'date_fin_prevue', 
            'statut', 'chef_projet', 'entreprise', 'province', 'photo'
        ]
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'domaine_activite': forms.Select(attrs={'class': 'form-control'}),  # ← Sélecteur
            'budget_previsionnel': forms.NumberInput(attrs={'class': 'form-control'}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin_prevue': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
            'chef_projet': forms.Select(attrs={'class': 'form-control'}),
            'entreprise': forms.Select(attrs={'class': 'form-control'}),
            'province': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
    
    def _init_(self, *args, **kwargs):
        super()._init_(*args, **kwargs)
        
        # Domaines d'activité prédéfinis
        DOMAINES_CHOIX = [
            ('', '-------- Sélectionnez un domaine --------'),
            ('construction', 'Construction / Infrastructures'),
            ('education', 'Éducation / Formation'),
            ('sante', 'Santé / Social'),
            ('agriculture', 'Agriculture / Élevage'),
            ('energie', 'Énergie / Électrification'),
            ('eau', 'Eau / Assainissement'),
            ('transport', 'Transport / Mobilité'),
            ('numerique', 'Numérique / Télécommunications'),
            ('environnement', 'Environnement / Écologie'),
            ('autre', 'Autre'),
        ]
        
        self.fields['domaine_activite'].widget = forms.Select(attrs={'class': 'form-control'})
        self.fields['domaine_activite'].choices = DOMAINES_CHOIX
        self.fields['domaine_activite'].required = True
        self.fields['domaine_activite'].help_text = "Choisissez le domaine d'activité du projet"
        
        self.fields['chef_projet'].queryset = ChefProjet.objects.all()
        self.fields['chef_projet'].label = "Ministère responsable"
        
        self.fields['entreprise'].queryset = Entreprise.objects.all()
        self.fields['entreprise'].label = "Entreprise exécutante"
        self.fields['entreprise'].required = True  
        self.fields['entreprise'].help_text = "Sélectionnez l'entreprise qui exécutera le projet"
        
        self.fields['photo'].required = False



# ============================================
# FORMULAIRES POUR LA GESTION DES EMPLOYÉS
# ============================================

class AjoutEmployeForm(forms.Form):
    """
    Formulaire pour ajouter un employé (par le représentant)
    """
    username = forms.CharField(
        max_length=150,
        label="Nom d'utilisateur",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ex: paul.nzola'
        })
    )
    
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'paul@entreprise.com'
        })
    )
    
    prenom = forms.CharField(
        max_length=100,
        label="Prénom",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Paul'
        })
    )
    
    nom = forms.CharField(
        max_length=100,
        label="Nom",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nzola'
        })
    )
    
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mot de passe temporaire'
        })
    )
    
    confirm_password = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmez le mot de passe'
        })
    )
    
    telephone = forms.CharField(
        max_length=20,
        required=False,
        label="Téléphone",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+243 XXX XXX XXX'
        })
    )
    
    profession = forms.CharField(
        max_length=100,
        required=False,
        label="Profession",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingénieur, technicien, etc.'
        })
    )
    
    def clean_username(self):
        """Vérifie que le nom d'utilisateur n'existe pas"""
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return username
    
    def clean_email(self):
        """Vérifie que l'email n'existe pas"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cet email est déjà utilisé.")
        return email
    
    def clean(self):
        """Vérifie que les mots de passe correspondent"""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        
        return cleaned_data


class ModifierEmployeForm(forms.ModelForm):
    """
    Formulaire pour modifier un employé (par le représentant)
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    
    telephone = forms.CharField(
        max_length=20,
        required=False,
        label="Téléphone",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    profession = forms.CharField(
        max_length=100,
        required=False,
        label="Profession",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    new_password = forms.CharField(
        required=False,
        label="Nouveau mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Laisser vide pour ne pas changer'
        })
    )
    
    confirm_new_password = forms.CharField(
        required=False,
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmez le nouveau mot de passe'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_new_password')
        
        if new_password and new_password != confirm_password:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        
        return cleaned_data


# ============================================
# FORMULAIRE POUR LES PHASES 
# ============================================

class PhaseForm(forms.ModelForm):
    """
    Formulaire pour ajouter/modifier une phase
    """
    class Meta:
        model = Phase
        fields = ['nom_phase', 'description', 'date_debut', 'date_fin', 'pourcentage_avancement', 'photo']
        widgets = {
            'nom_phase': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'pourcentage_avancement': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['photo'].required = False
        self.fields['photo'].help_text = "Photo illustrant l'avancement (optionnelle)"
    
    def clean_pourcentage_avancement(self):
        """Valide que le pourcentage est entre 0 et 100"""
        pourcentage = self.cleaned_data.get('pourcentage_avancement')
        if pourcentage is not None and (pourcentage < 0 or pourcentage > 100):
            raise forms.ValidationError("Le pourcentage doit être entre 0 et 100.")
        return pourcentage


# ============================================
# FORMULAIRE POUR METTRE À JOUR L'AVANCEMENT RAPIDE
# ============================================

class AvancementRapideForm(forms.Form):
    """
    Formulaire pour mettre à jour rapidement l'avancement d'une phase
    """
    pourcentage_avancement = forms.IntegerField(
        min_value=0,
        max_value=100,
        label="Pourcentage d'avancement",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0-100'
        })
    )
    
    commentaire = forms.CharField(
        required=False,
        label="Commentaire",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Ajouter un commentaire sur l\'avancement...'
        })
    )


# ============================================
# FORMULAIRE POUR PHASE
# ============================================
class PhaseForm(forms.ModelForm):
    """Formulaire pour ajouter/modifier une phase"""
    
    class Meta:
        model = Phase
        fields = ['nom_phase', 'description', 'date_debut', 'date_fin', 'pourcentage_avancement', 'photo']
        widgets = {
            'nom_phase': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'pourcentage_avancement': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['photo'].required = False
        self.fields['photo'].help_text = "Photo illustrant l'avancement (optionnelle)"
    
    def clean_pourcentage_avancement(self):
        """Valide que le pourcentage est entre 0 et 100"""
        pourcentage = self.cleaned_data.get('pourcentage_avancement')
        if pourcentage is not None and (pourcentage < 0 or pourcentage > 100):
            raise forms.ValidationError("Le pourcentage doit être entre 0 et 100.")
        return pourcentage


# ============================================
# FORMULAIRE POUR AVIS 
# ============================================
class AvisForm(forms.ModelForm):
    """Formulaire pour donner une note/avis avec commentaire optionnel"""
    
    class Meta:
        model = Avis
        fields = ['note', 'commentaire']  
        widgets = {
            'note': forms.Select(attrs={'class': 'form-control'}),
            'commentaire': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Votre avis (optionnel)...'
            }),
        }
        labels = {
            'note': 'Note',
            'commentaire': 'Commentaire (optionnel)'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personnaliser les choix de note avec des étoiles
        self.fields['note'].choices = [(i, f"{i} ★" + ("s" if i > 1 else "")) for i in range(1, 6)]
        self.fields['commentaire'].required = False  # Optionnel
        self.fields['commentaire'].widget.attrs.update({
            'placeholder': 'Donnez votre avis sur ce projet...'
        })


# ============================================
# FORMULAIRE POUR COMMENTAIRE 
# ============================================
class CommentaireForm(forms.ModelForm):
    """Formulaire pour ajouter un commentaire"""
    
    class Meta:
        model = Commentaire
        fields = ['contenu']
        widgets = {
            'contenu': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Votre commentaire...'
            })
        }
        labels = {
            'contenu': ''
        }
# ============================================
# FORMULAIRES POUR ADMIN (Ministères et Entreprises)
# ============================================

class ChefProjetForm(forms.ModelForm):
    """Formulaire pour ajouter/modifier un ministère"""
    
    class Meta:
        model = ChefProjet
        fields = ['nom_ministere', 'description', 'user']
        widgets = {
            'nom_ministere': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'user': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.filter(profile__role='chef')
        self.fields['user'].label = "Utilisateur associé"
        self.fields['user'].required = False


class SuiviBudgetForm(forms.ModelForm):
    """Formulaire pour ajouter un suivi budgétaire"""
    
    class Meta:
        model = SuiviBudget
        fields = ['budget_consomme', 'date_mise_a_jour', 'phase', 'commentaire']
        widgets = {
            'budget_consomme': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Montant en CDF',
                'step': '1000'
            }),
            'date_mise_a_jour': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'phase': forms.Select(attrs={
                'class': 'form-control'
            }),
            'commentaire': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Description de la dépense (optionnel)'
            }),
        }
        labels = {
            'budget_consomme': 'Montant (CDF)',
            'date_mise_a_jour': 'Date',
            'phase': 'Phase concernée',
            'commentaire': 'Commentaire',
        }
    
    def __init__(self, *args, **kwargs):
        projet_id = kwargs.pop('projet_id', None)
        super().__init__(*args, **kwargs)
        
        if projet_id:
            self.fields['phase'].queryset = Phase.objects.filter(projet_id=projet_id)
            self.fields['phase'].empty_label = "Non spécifié (budget global)"
