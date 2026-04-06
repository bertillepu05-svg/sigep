from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Sum
from django.http import JsonResponse
from .forms import ( AjoutEmployeForm, SuiviBudgetForm, ModifierEmployeForm, InscriptionForm, ConnexionForm, UserProfileForm, UserForm, ProjetForm, PhaseForm, CommentaireForm, AvisForm)
from .models import ( UserProfile, ChefProjet, Entreprise, Projet, Phase, SuiviBudget, Commentaire, Avis, ProjetSuivi)
from django.contrib.auth.hashers import make_password
import random
import string
from django.utils import timezone
from functools import wraps


# ============================================
# DÉCORATEURS PERSONNALISÉS
# ============================================

def role_required(allowed_roles):
    """
    Décorateur robuste qui crée automatiquement le profil si manquant
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Vous devez être connecté.")
                return redirect('login')
            
            # Création automatique du profil s'il n'existe pas
            try:
                profile = request.user.profile
            except:
                from .models import UserProfile
                profile = UserProfile.objects.create(
                    user=request.user,
                    role='observateur',
                    date_inscription=request.user.date_joined
                )
                # Message silencieux pour ne pas gêner l'utilisateur
                # messages.info(request, "Votre profil a été initialisé.")
            
            # Superuser peut tout voir
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Vérification du rôle
            if profile.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(
                    request, 
                    f"Accès refusé. Cette page nécessite le rôle: {', '.join(allowed_roles)}"
                )
                return redirect('index')
        return wrapper
    return decorator

# ============================================
# VUES D'AUTHENTIFICATION
# ============================================

def index(request):
    """Page d'accueil publique"""
    projets_recents = Projet.objects.all().order_by('-date_debut')[:6]
    stats = {
        'total_projets': Projet.objects.count(),
        'en_cours': Projet.objects.filter(statut='en_cours').count(),
        'termines': Projet.objects.filter(statut='termine').count(),
    }
    return render(request, "pages/index.html", {
        'projets_recents': projets_recents,
        'stats': stats
    })


def register(request):
    """Inscription - Crée un compte observateur"""
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        form = InscriptionForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Bienvenue {user.first_name} ! Votre inscription a réussi.')
            return redirect('index')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = InscriptionForm()
    
    return render(request, 'pages/auth/register.html', {'form': form})


def login_view(request):
    """Connexion utilisateur"""
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        form = ConnexionForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            remember_me = form.cleaned_data.get('remember_me', False)
            
            login(request, user)
            
            if not remember_me:
                request.session.set_expiry(0)
            
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('index')
        else:
            messages.error(request, 'Nom d\'utilisateur/email ou mot de passe incorrect.')
    else:
        form = ConnexionForm()
    
    return render(request, 'pages/auth/login.html', {'form': form})


def logout_view(request):
    """Déconnexion"""
    logout(request)
    messages.info(request, "Vous avez été déconnecté.")
    return redirect('index')


# ============================================
# VUES PROFIL UTILISATEUR
# ============================================



@login_required
def profil(request):
    """Page de profil utilisateur"""
    user = request.user
    stats = {}
    activites = []  # ← Initialiser la liste des activités
    
    try:
        profile = user.profile
    except:
        profile = None
    
    # ============================================
    # STATISTIQUES SELON LE RÔLE
    # ============================================
    
    if profile:
        if profile.role == 'observateur':
            stats['projets_suivis'] = ProjetSuivi.objects.filter(utilisateur=user).count()
            stats['commentaires'] = Commentaire.objects.filter(utilisateur=user).count()
            stats['avis'] = Avis.objects.filter(utilisateur=user).count()
            
            # ✅ ACTIVITÉS POUR OBSERVATEUR
            # Commentaires récents
            for c in Commentaire.objects.filter(utilisateur=user).order_by('-date_commentaire')[:5]:
                activites.append({
                    'titre': f"Commentaire sur {c.projet.titre}",
                    'date': c.date_commentaire,
                    'icon': 'comment',
                    'message': c.contenu[:50],
                    'statut': 'success'
                })
            
            # Projets suivis récents
            for s in ProjetSuivi.objects.filter(utilisateur=user).order_by('-date_suivi')[:5]:
                activites.append({
                    'titre': f"Suivi du projet {s.projet.titre}",
                    'date': s.date_suivi,
                    'icon': 'heart',
                    'message': f"Vous avez commencé à suivre ce projet",
                    'statut': 'info'
                })
        
        elif profile.role == 'chef':
            stats['projets_crees'] = Projet.objects.filter(createur=user).count()
            
            # ✅ ACTIVITÉS POUR CHEF DE PROJET
            # Projets créés récemment
            for p in Projet.objects.filter(createur=user).order_by('-date_debut')[:5]:
                activites.append({
                    'titre': f"Projet créé : {p.titre}",
                    'date': p.date_debut,
                    'icon': 'plus-circle',
                    'message': f"Budget: {p.budget_previsionnel:,.0f} CDF",
                    'statut': 'success'
                })
            
            # Projets modifiés récemment
            for p in Projet.objects.filter(createur=user).order_by('-date_debut')[:5]:
                activites.append({
                    'titre': f"Modification projet {p.titre}",
                    'date': p.date_debut,
                    'icon': 'edit',
                    'message': f"Statut actuel: {p.get_statut_display()}",
                    'statut': 'warning'
                })
        
        elif profile.role == 'entreprise':
            # Déterminer l'entreprise
            if hasattr(user, 'entreprise_representee'):
                entreprise = user.entreprise_representee
                stats['employes'] = UserProfile.objects.filter(entreprise=entreprise, est_employe=True).count()
                stats['projets_assignes'] = Projet.objects.filter(entreprise=entreprise).count()
                stats['phases'] = Phase.objects.filter(projet__entreprise=entreprise).count()
                
                # ✅ ACTIVITÉS POUR REPRÉSENTANT
                # Phases ajoutées récemment
                for phase in Phase.objects.filter(projet__entreprise=entreprise).order_by('-date_debut')[:5]:
                    activites.append({
                        'titre': f"Phase ajoutée : {phase.nom_phase}",
                        'date': phase.date_debut,
                        'icon': 'tasks',
                        'message': f"Projet: {phase.projet.titre}",
                        'statut': 'info'
                    })
                
                # Dépenses enregistrées récemment
                for depense in SuiviBudget.objects.filter(projet__entreprise=entreprise).order_by('-date_mise_a_jour')[:5]:
                    activites.append({
                        'titre': f"Dépense enregistrée",
                        'date': depense.date_mise_a_jour,
                        'icon': 'coins',
                        'message': f"{depense.budget_consomme:,.0f} CDF - {depense.projet.titre}",
                        'statut': 'warning'
                    })
            
            elif profile.est_employe and profile.entreprise:
                entreprise = profile.entreprise
                stats['projets_assignes'] = Projet.objects.filter(entreprise=entreprise).count()
                stats['mes_phases'] = Phase.objects.filter(projet__entreprise=entreprise).count()
                stats['employes'] = 0
                
                # ✅ ACTIVITÉS POUR EMPLOYÉ
                # Phases ajoutées récemment
                for phase in Phase.objects.filter(projet__entreprise=entreprise).order_by('-date_debut')[:5]:
                    activites.append({
                        'titre': f"Phase ajoutée : {phase.nom_phase}",
                        'date': phase.date_debut,
                        'icon': 'tasks',
                        'message': f"Projet: {phase.projet.titre}",
                        'statut': 'info'
                    })
                
                # Dépenses enregistrées récemment
                for depense in SuiviBudget.objects.filter(projet__entreprise=entreprise).order_by('-date_mise_a_jour')[:5]:
                    activites.append({
                        'titre': f"Dépense enregistrée",
                        'date': depense.date_mise_a_jour,
                        'icon': 'coins',
                        'message': f"{depense.budget_consomme:,.0f} CDF - {depense.projet.titre}",
                        'statut': 'warning'
                    })
    
    # Trier les activités par date (plus récentes d'abord)
    activites.sort(key=lambda x: x['date'], reverse=True)
    activites = activites[:10]  # Garder les 10 plus récentes
    
    # ============================================
    # CONTEXTE
    # ============================================
    context = {
        'profile': profile,
        'stats': stats,
        'activites': activites,  # ← PASSER LES ACTIVITÉS AU TEMPLATE
    }
    
    return render(request, 'pages/auth/profil.html', context)

@login_required
def modifier_profil(request):
    """Modification du profil"""
    try:
        profile = request.user.profile
    except:
        profile = None
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Votre profil a été mis à jour avec succès.")
            return redirect('profil')
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)
    
    return render(request, 'pages/auth/modification_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })


# ============================================
# VUES PROJETS (PUBLIQUES)
# ============================================

def liste_projets(request):
    """Liste de tous les projets"""
    projets = Projet.objects.all().order_by('-date_debut')
    
    # Filtres
    statut = request.GET.get('statut')
    province = request.GET.get('province')
    
    if statut:
        projets = projets.filter(statut=statut)
    if province:
        projets = projets.filter(province=province)
    
    context = {
        'projets': projets,
        'statuts': Projet.STATUT_CHOIX,
        'provinces': Projet.objects.values_list('province', flat=True).distinct(),
        'statut_actuel': statut,
        'province_actuelle': province,
    }
    return render(request, 'pages/liste_projets.html', context)


def details_projets(request, projet_id):
    """Détail d'un projet"""
    projet = get_object_or_404(Projet, id_projet=projet_id)
   
    
    # Statistiques
    phases = projet.phases.all()
    suivis = projet.suivis_budget.all()
    commentaires = projet.commentaires.select_related('utilisateur').all()
    avis = projet.avis.all()
    
    # Calculs
    note_moyenne = avis.aggregate(Avg('note'))['note__avg'] or 0
    nb_avis = avis.count()
    budget_consomme = suivis.aggregate(Sum('budget_consomme'))['budget_consomme__sum'] or 0
    budget_restant = projet.budget_previsionnel - budget_consomme
    
    # Vérifier si l'utilisateur connecté suit ce projet
    est_suivi = False
    avis_utilisateur = None
    if request.user.is_authenticated:
        est_suivi = ProjetSuivi.objects.filter(
            utilisateur=request.user,
            projet=projet
        ).exists()
        avis_utilisateur = avis.filter(utilisateur=request.user).first()
    
    context = {
        'projet': projet,
        'phases': phases,
        'suivis': suivis,
        'commentaires': commentaires,
        'avis': avis,
        'note_moyenne': round(note_moyenne, 1),
        'nb_avis': nb_avis,
        'budget_consomme': budget_consomme,
        'est_suivi': est_suivi,
        'avis_utilisateur': avis_utilisateur,
        'budget_restant' : budget_restant,
    }
    return render(request, 'pages/details_projets.html', context)


# ============================================
# VUES POUR OBSERVATEUR (CONNECTÉ)
# ============================================

@login_required
def toggle_suivre_projet(request, projet_id):
    """Suivre ou ne plus suivre un projet"""
    projet = get_object_or_404(Projet, id_projet=projet_id)
    
    suivi = ProjetSuivi.objects.filter(
        utilisateur=request.user,
        projet=projet
    ).first()
    
    if suivi:
        suivi.delete()
        messages.success(request, f"Vous ne suivez plus le projet '{projet.titre}'")
    else:
        ProjetSuivi.objects.create(
            utilisateur=request.user,
            projet=projet
        )
        messages.success(request, f"Vous suivez maintenant le projet '{projet.titre}'")
    
    return redirect('details_projets', projet_id=projet_id)


@login_required
def projets_suivis(request):
    """Liste des projets suivis par l'utilisateur"""
    projets_suivis = ProjetSuivi.objects.filter(
        utilisateur=request.user
    ).select_related('projet').order_by('-date_suivi')
    
    return render(request, 'pages/projets_suivis.html', {
        'projets_suivis': projets_suivis
    })


def projets_a_venir(request):
    """Liste des projets à venir"""
    projets = Projet.objects.filter(statut='a_venir').order_by('date_debut')
    
    context = {
        'projets': projets,
        'titre_page': 'Projets à venir',
        'statut_actuel': 'a_venir'
    }
    return render(request, 'pages/projets_avenirs.html', context)


def projets_en_cours(request):
    """Liste des projets en cours"""
    projets = Projet.objects.filter(statut='en_cours').order_by('-date_debut')
    
    context = {
        'projets': projets,
        'titre_page': 'Projets en cours',
        'statut_actuel': 'en_cours'
    }
    return render(request, 'pages/projets_en_cours.html', context)


def projets_termines(request):
    """Liste des projets terminés"""
    projets = Projet.objects.filter(statut='termine').order_by('-date_fin_prevue')
    
    context = {
        'projets': projets,
        'titre_page': 'Projets terminés',
        'statut_actuel': 'termine'
    }
    return render(request, 'pages/projets_termines.html', context)



@login_required
def ajouter_commentaire(request, projet_id):
    """Ajouter un commentaire à un projet"""
    projet = get_object_or_404(Projet, id_projet=projet_id)
    
    if request.method == 'POST':
        form = CommentaireForm(request.POST)
        if form.is_valid():
            commentaire = form.save(commit=False)
            commentaire.utilisateur = request.user
            commentaire.projet = projet
            commentaire.save()
            messages.success(request, "Commentaire ajouté avec succès !")
            return redirect('details_projets', projet_id=projet_id)
    else:
        form = CommentaireForm()
    
    return render(request, 'pages/ajouter_commentaire.html', {
        'form': form,
        'projet': projet
    })


@login_required
def modifier_commentaire(request, commentaire_id):
    """Modifier son propre commentaire"""
    commentaire = get_object_or_404(Commentaire, id_commentaire=commentaire_id)
    
    if commentaire.utilisateur != request.user:
        messages.error(request, "Vous n'êtes pas autorisé à modifier ce commentaire.")
        return redirect('details_projets', projet_id=commentaire.projet.id_projet)
    
    if request.method == 'POST':
        form = CommentaireForm(request.POST, instance=commentaire)
        if form.is_valid():
            form.save()
            messages.success(request, "Commentaire modifié avec succès !")
            return redirect('details_projets', projet_id=commentaire.projet.id_projet)
    else:
        form = CommentaireForm(instance=commentaire)
    
    return render(request, 'pages/modifier_commentaire.html', {
        'form': form,
        'commentaire': commentaire
    })


@login_required
def supprimer_commentaire(request, commentaire_id):
    """Supprimer son propre commentaire"""
    commentaire = get_object_or_404(Commentaire, id_commentaire=commentaire_id)
    
    if commentaire.utilisateur != request.user:
        messages.error(request, "Vous n'êtes pas autorisé à supprimer ce commentaire.")
        return redirect('details_projets', projet_id=commentaire.projet.id_projet)
    
    projet_id = commentaire.projet.id_projet
    commentaire.delete()
    messages.success(request, "Commentaire supprimé.")
    
    return redirect('details_projets', projet_id=projet_id)



# @login_required
# def donner_avis1(request, projet_id):
#     """Donner ou modifier une note sur un projet avec commentaire"""
#     projet = get_object_or_404(Projet, id_projet=projet_id)
    
#     avis_existant = Avis.objects.filter(
#         utilisateur=request.user,
#         projet=projet
#     ).first()
    
#     if request.method == 'POST':
#         form = AvisForm(request.POST, instance=avis_existant)
#         if form.is_valid():
#             avis = form.save(commit=False)
#             avis.utilisateur = request.user
#             avis.projet = projet
#             avis.save()
            
#             msg = "Avis mis à jour !" if avis_existant else "Avis ajouté !"
#             messages.success(request, msg)
#             return redirect('details_projets', projet_id=projet_id)
#     else:
#         form = AvisForm(instance=avis_existant)
    
#     return render(request, 'pages/avis.html', {
#         'form': form,
#         'projet': projet,
#         'existant': avis_existant
#     })


@login_required
def avis(request, projet_id):
    """Donner ou modifier une note sur un projet avec commentaire"""
    projet = get_object_or_404(Projet, id_projet=projet_id)
    
    avis_existant = Avis.objects.filter(
        utilisateur=request.user,
        projet=projet
    ).first()
    
    if request.method == 'POST':
        form = AvisForm(request.POST, instance=avis_existant)
        if form.is_valid():
            avis = form.save(commit=False)
            avis.utilisateur = request.user
            avis.projet = projet
            avis.save()
            
            msg = "Avis mis à jour !" if avis_existant else "Avis ajouté !"
            messages.success(request, msg)
            return redirect('details_projets', projet_id=projet_id)
    else:
        form = AvisForm(instance=avis_existant)
    
    return render(request, 'pages/avis.html', {
        'form': form,
        'projet': projet,
        'existant': avis_existant
    })

# ============================================
# VUES POUR CHEF DE PROJET
# ============================================

@login_required
@role_required(['chef'])
def mes_projets(request):
    """Liste des projets créés par le chef connecté"""
    try:
        chef_projet = request.user.chef_projet
        projets = Projet.objects.filter(chef_projet=chef_projet).order_by('-date_debut')
    except:
        projets = []
        messages.warning(request, "Vous n'êtes pas associé à un ministère.")
    
    return render(request, 'pages/chefs/mes_projets.html', {'projets': projets})


@login_required
@role_required(['chef'])
def initialiser_projet(request):
    """Créer un nouveau projet"""
    if request.method == 'POST':
        form = ProjetForm(request.POST, request.FILES)
        if form.is_valid():
            projet = form.save(commit=False)
            projet.createur = request.user
            try:
                projet.chef_projet = request.user.chef_projet
            except:
                pass
            projet.save()
            messages.success(request, "Projet créé avec succès !")
            return redirect('mes_projets')
    else:
        form = ProjetForm()
    
    return render(request, 'pages/chefs/initialiser_projet.html', {'form': form})


@login_required
@role_required(['chef'])
def modifier_projet(request, projet_id):
    """Modifier un projet existant"""
    projet = get_object_or_404(Projet, id_projet=projet_id)
    
    # Vérifier que le chef est bien responsable
    try:
        if projet.chef_projet != request.user.chef_projet and not request.user.is_superuser:
            messages.error(request, "Vous n'êtes pas autorisé à modifier ce projet.")
            return redirect('mes_projets')
    except:
        pass
    
    if request.method == 'POST':
        form = ProjetForm(request.POST, request.FILES, instance=projet)
        if form.is_valid():
            form.save()
            messages.success(request, "Projet mis à jour avec succès !")
            return redirect('details_projets', projet_id=projet_id)
    else:
        form = ProjetForm(instance=projet)
    
    return render(request, 'pages/modifier_projet.html', {
        'form': form,
        'projet': projet
    })


# @login_required
# @role_required(['chef'])
# def ajouter_phase(request, projet_id):
#     """Ajouter une phase à un projet"""
#     projet = get_object_or_404(Projet, id_projet=projet_id)
    
#     if request.method == 'POST':
#         form = PhaseForm(request.POST, request.FILES)
#         if form.is_valid():
#             phase = form.save(commit=False)
#             phase.projet = projet
#             phase.save()
#             messages.success(request, "Phase ajoutée avec succès !")
#             return redirect('details_projets', projet_id=projet_id)
#     else:
#         form = PhaseForm()
    
#     return render(request, 'pages/ajouter_phase.html', {
#         'form': form,
#         'projet': projet
#     })


# @login_required
# @role_required(['chef'])
# def modifier_phase(request, phase_id):
#     """Modifier une phase"""
#     phase = get_object_or_404(Phase, id_phase=phase_id)
    
#     if request.method == 'POST':
#         form = PhaseForm(request.POST, request.FILES, instance=phase)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Phase mise à jour avec succès !")
#             return redirect('details_projets', projet_id=phase.projet.id_projet)
#     else:
#         form = PhaseForm(instance=phase)
    
#     return render(request, 'pages/modifier_phase.html', {
#         'form': form,
#         'phase': phase
#     })


# ============================================
# VUES POUR ENTREPRISE
# ============================================


@login_required
@role_required(['entreprise'])
def projets_assignes(request):
    """
    Liste des projets assignés à l'entreprise
    Accessible par : REPRÉSENTANT et EMPLOYÉ
    """
    
    # ============================================
    # DÉTERMINER L'ENTREPRISE
    # ============================================
    entreprise = None
    
    try:
        # Cas 1 : L'utilisateur est un REPRÉSENTANT
        if hasattr(request.user, 'entreprise_representee'):
            entreprise = request.user.entreprise_representee
            print(f"Représentant de: {entreprise.nom}")
        
        # Cas 2 : L'utilisateur est un EMPLOYÉ
        elif request.user.profile.est_employe and request.user.profile.entreprise:
            entreprise = request.user.profile.entreprise
            print(f"Employé de: {entreprise.nom}")
        
        else:
            messages.error(request, "Vous n'êtes pas associé à une entreprise.")
            return redirect('index')
            
    except Exception as e:
        messages.error(request, f"Erreur: {str(e)}")
        return redirect('index')
    
    if not entreprise:
        messages.error(request, "Aucune entreprise associée.")
        return redirect('index')
    
    # ============================================
    # RÉCUPÉRER LES PROJETS
    # ============================================
    projets = Projet.objects.filter(entreprise=entreprise).order_by('-date_debut')
    
    print(f"Projets trouvés pour {entreprise.nom}: {projets.count()}")
    for p in projets:
        print(f"  - {p.titre} (statut: {p.statut})")
    
    context = {
        'projets': projets,
        'entreprise': entreprise,
        'est_representant': hasattr(request.user, 'entreprise_representee')
    }
    
    return render(request, 'pages/entreprise/assignes.html', context)

# ============================================
# AJOUTER UNE DÉPENSE
# ============================================
@login_required
@role_required(['entreprise'])
def ajouter_suivi_budget(request, projet_id):
    """Ajouter un suivi budgétaire"""
    projet = get_object_or_404(Projet, id_projet=projet_id)
    
    # Vérifier que l'utilisateur est associé à l'entreprise
    est_autorise = False
    
    if hasattr(request.user, 'entreprise_representee'):
        if request.user.entreprise_representee == projet.entreprise:
            est_autorise = True
    
    if request.user.profile.est_employe and request.user.profile.entreprise:
        if request.user.profile.entreprise == projet.entreprise:
            est_autorise = True
    
    if request.user.is_superuser:
        est_autorise = True
    
    if not est_autorise:
        messages.error(request, "Vous n'êtes pas autorisé à modifier ce projet.")
        return redirect('details_projets', projet_id=projet_id)
    
    if request.method == 'POST':
        form = SuiviBudgetForm(request.POST, projet_id=projet.id_projet)
        if form.is_valid():
            suivis = form.save(commit=False)
            suivis.projet = projet
            suivis.save()
            messages.success(request, f"✅ Dépense de {suivis.budget_consomme} CDF enregistrée.")
            return redirect('details_projets', projet_id=projet_id)
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = SuiviBudgetForm(projet_id=projet.id_projet)
    
    return render(request, 'pages/entreprise/employes/ajouter_depense.html', {
        'form': form,
        'projet': projet
    })


@login_required
@role_required(['entreprise'])
def modifier_suivi_budget(request, suivi_id):
    """Modifier une dépense (uniquement pour le représentant)"""
    suivi = get_object_or_404(SuiviBudget, id_suivi=suivi_id)
    projet = suivi.projet
    
    # ============================================
    # VÉRIFICATION : SEUL LE REPRÉSENTANT PEUT MODIFIER
    # ============================================
    est_autorise = False
    
    if hasattr(request.user, 'entreprise_representee'):
        if request.user.entreprise_representee == projet.entreprise:
            est_autorise = True
    
    if request.user.is_superuser:
        est_autorise = True
    
    if not est_autorise:
        messages.error(request, "Seul le représentant de l'entreprise peut modifier les dépenses.")
        return redirect('details_projets', projet_id=projet.id_projet)
    
    # ============================================
    # CALCUL DES STATISTIQUES BUDGÉTAIRES
    # ============================================
    # Budget total déjà consommé
    budget_consomme = projet.suivis_budget.aggregate(total=Sum('budget_consomme'))['total'] or 0
    
    # Pourcentage du budget utilisé
    pourcentage_budget = 0
    if projet.budget_previsionnel > 0:
        pourcentage_budget = (budget_consomme / projet.budget_previsionnel) * 100
    
    # ============================================
    # TRAITEMENT DU FORMULAIRE
    # ============================================
    if request.method == 'POST':
        form = SuiviBudgetForm(request.POST, instance=suivi, projet_id=projet.id_projet)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Dépense modifiée avec succès.")
            return redirect('details_projets', projet_id=projet.id_projet)
    else:
        form = SuiviBudgetForm(instance=suivi, projet_id=projet.id_projet)
    
    context = {
        'form': form,
        'suivi': suivi,
        'projet': projet,
        'budget_consomme': budget_consomme,          # ← Total consommé
        'pourcentage_budget': pourcentage_budget,    # ← Pourcentage calculé
    }
    
    return render(request, 'pages/entreprise/modifier_depense.html', context)

# ============================================
# SUPPRIMER UNE DÉPENSE
# ============================================
@login_required
@role_required(['entreprise'])
def supprimer_suivi_budget(request, suivi_id):
    """Supprimer une dépense (uniquement pour le représentant)"""
    suivi = get_object_or_404(SuiviBudget, id_suivi=suivi_id)
    projet_id = suivi.projet.id_projet
    
    # ============================================
    # VÉRIFICATION : SEUL LE REPRÉSENTANT PEUT SUPPRIMER
    # ============================================
    est_autorise = False
    
    # Cas 1 : L'utilisateur est le REPRÉSENTANT
    if hasattr(request.user, 'entreprise_representee'):
        if request.user.entreprise_representee == suivi.projet.entreprise:
            est_autorise = True
    
    # Cas 2 : Superuser
    if request.user.is_superuser:
        est_autorise = True
    
    if not est_autorise:
        messages.error(request, "❌ Seul le représentant de l'entreprise peut supprimer les dépenses.")
        return redirect('details_projets', projet_id=projet_id)
    
    suivi.delete()
    messages.success(request, "✅ Dépense supprimée avec succès.")
    
    return redirect('details_projets', projet_id=projet_id)






@login_required
@role_required(['entreprise'])
def ajouter_phase_entreprise(request, projet_id):
    """
    Ajouter une phase à un projet
    VALIDATION : Un projet doit être EN COURS pour ajouter des phases
    """
    projet = get_object_or_404(Projet, id_projet=projet_id)
    
    # ============================================
    # VÉRIFICATION DES DROITS ENTREPRISE
    # ============================================
    try:
        profile = request.user.profile
    except:
        messages.error(request, "Profil utilisateur invalide.")
        return redirect('projets_assignes')
    
    # Déterminer l'entreprise
    entreprise = None
    if hasattr(request.user, 'entreprise_representee'):
        entreprise = request.user.entreprise_representee
    elif profile.est_employe:
        entreprise = profile.entreprise
    
    if not entreprise:
        messages.error(request, "Vous n'êtes pas associé à une entreprise.")
        return redirect('projets_assignes')
    
    if projet.entreprise != entreprise:
        messages.error(request, "Ce projet n'est pas assigné à votre entreprise.")
        return redirect('projets_assignes')
    
    # ============================================
    # VALIDATION DU STATUT DU PROJET
    # ============================================
    
    # Règle 1: Un projet terminé ne peut plus avoir de phases
    if projet.statut == 'termine':
        messages.error(
            request, 
            "Ce projet est terminé. Impossible d'ajouter de nouvelles phases."
        )
        return redirect('details_projets', projet_id=projet_id)
    
    # Règle 2: Un projet annulé ne peut plus avoir de phases
    if projet.statut == 'annule':
        messages.error(
            request, 
            "Ce projet est annulé. Impossible d'ajouter de nouvelles phases."
        )
        return redirect('details_projets', projet_id=projet_id)
    
    # Règle 3: Un projet "à venir" doit d'abord passer en "en cours"
    if projet.statut == 'a_venir':
        messages.warning(
            request, 
            "Ce projet est encore 'À venir'. Pour ajouter des phases, "
            "le chef de projet doit d'abord le passer en 'En cours'."
        )
        return redirect('details_projets', projet_id=projet_id)
    
    # ============================================
    # TRAITEMENT DU FORMULAIRE
    # ============================================
    
    if request.method == 'POST':
        form = PhaseForm(request.POST, request.FILES)
        if form.is_valid():
            phase = form.save(commit=False)
            phase.projet = projet
            phase.save()
            messages.success(request, f"Phase '{phase.nom_phase}' ajoutée avec succès !")
            return redirect('details_projets', projet_id=projet_id)
    else:
        form = PhaseForm()
    
    return render(request, 'pages/entreprise/employes/ajouter_phase.html', {
        'form': form,
        'projet': projet,
        'est_representant': hasattr(request.user, 'entreprise_representee'),
        'est_employe': profile.est_employe
    })

@login_required
@role_required(['entreprise'])
def modifier_phase_entreprise(request, phase_id):
    """
    Modifier une phase existante
    Accessible par : REPRÉSENTANT et EMPLOYÉS
    """
    phase = get_object_or_404(Phase, id_phase=phase_id)
    projet = phase.projet
    
    # ============================================
    # VÉRIFICATION DES DROITS 
    # ============================================
    
    try:
        profile = request.user.profile
    except:
        messages.error(request, "Profil utilisateur invalide.")
        return redirect('projets_assignes')
    
    est_representant = hasattr(request.user, 'entreprise_representee')
    est_employe = profile.est_employe and profile.entreprise is not None
    est_admin = request.user.is_superuser
    
    entreprise = None
    if est_representant:
        entreprise = request.user.entreprise_representee
    elif est_employe:
        entreprise = profile.entreprise
    
    if not entreprise:
        messages.error(request, "Vous n'êtes pas associé à une entreprise.")
        return redirect('projets_assignes')
    
    if projet.entreprise != entreprise:
        messages.error(request, "Ce projet n'est pas assigné à votre entreprise.")
        return redirect('projets_assignes')
    
    # ============================================
    # VALIDATION DU STATUT
    # ============================================
    if projet.statut in ['termine', 'annule']:
        messages.error(
            request, 
            f"Ce projet est {projet.get_statut_display()}. "
            f"Impossible de modifier les phases."
        )
        return redirect('details_projets', projet_id=projet.id_projet)
    
    if projet.statut == 'a_venir':
        messages.warning(
            request, 
            "Ce projet est encore 'À venir'. Pour modifier les phases, "
            "le chef de projet doit d'abord le passer en 'En cours'."
        )
        return redirect('details_projets', projet_id=projet.id_projet)
    
    # ============================================
    # TRAITEMENT DU FORMULAIRE
    # ============================================
    
    if request.method == 'POST':
        form = PhaseForm(request.POST, request.FILES, instance=phase)
        if form.is_valid():
            form.save()
            messages.success(request, f"Phase '{phase.nom_phase}' mise à jour !")
            return redirect('details_projets', projet_id=projet.id_projet)
    else:
        form = PhaseForm(instance=phase)
    
    return render(request, 'pages/entreprise/employes/modifier_phase.html', {
        'form': form,
        'phase': phase,
        'projet': projet,
        'est_representant': est_representant,
        'est_employe': est_employe
    })


@login_required
@role_required(['chef'])
def changer_statut_projet(request, projet_id):
    """
    Permet au chef de projet de changer le statut du projet
    Validation spéciale pour passer de "À venir" à "En cours"
    """
    projet = get_object_or_404(Projet, id_projet=projet_id)
    
    # Vérifier que le chef est bien responsable
    if projet.chef_projet.user != request.user and not request.user.is_superuser:
        messages.error(request, "Vous n'êtes pas autorisé à modifier ce projet.")
        return redirect('details_projets', projet_id=projet_id)
    
    if request.method == 'POST':
        nouveau_statut = request.POST.get('statut')
        
        # Validation : un projet terminé ne peut plus changer de statut
        if projet.statut == 'termine':
            messages.error(request, "Ce projet est terminé. Impossible de changer son statut.")
            return redirect('details_projets', projet_id=projet_id)
        
        # Validation : un projet annulé ne peut plus changer de statut
        if projet.statut == 'annule':
            messages.error(request, "Ce projet est annulé. Impossible de changer son statut.")
            return redirect('details_projets', projet_id=projet_id)
        
        # Validation spéciale : passer de "À venir" à "En cours" nécessite une entreprise assignée
        if projet.statut == 'a_venir' and nouveau_statut == 'en_cours':
            if not projet.entreprise:
                messages.error(
                    request, 
                    "Impossible de démarrer le projet. "
                    "Veuillez d'abord assigner une entreprise exécutante."
                )
                return redirect('details_projets', projet_id=projet_id)
        
        # Appliquer le changement
        projet.statut = nouveau_statut
        projet.save()
        
        messages.success(
            request, 
            f"✅ Statut du projet changé : {projet.get_statut_display()}"
        )
        return redirect('details_projets', projet_id=projet_id)
    
    return render(request, 'pages/projets/changer_statut.html', {
        'projet': projet,
        'statuts': Projet.STATUT_CHOIX
    })


@login_required
@role_required(['entreprise'])
def mes_phases(request):
    """
    Liste toutes les phases des projets assignés à l'entreprise
    Accessible par : EMPLOYÉS et REPRÉSENTANT
    """
    try:
        profile = request.user.profile
    except:
        messages.error(request, "Profil utilisateur invalide.")
        return redirect('index')
    
    # Déterminer l'entreprise
    if hasattr(request.user, 'entreprise_representee'):
        entreprise = request.user.entreprise_representee
    elif profile.est_employe:
        entreprise = profile.entreprise
    else:
        messages.error(request, "Vous n'êtes pas associé à une entreprise.")
        return redirect('index')
    
    if not entreprise:
        messages.error(request, "Aucune entreprise associée.")
        return redirect('index')
    
    # Récupérer toutes les phases des projets assignés
    phases = Phase.objects.filter(
        projet__entreprise=entreprise
    ).select_related('projet').order_by('-date_debut')
    
    context = {
        'phases': phases,
        'entreprise': entreprise,
        'est_representant': hasattr(request.user, 'entreprise_representee')
    }
    return render(request, 'pages/entreprise/employes/mes_phases.html', context)


# ============================================
# VUES POUR CHEF
# ============================================

@login_required
@role_required(['chef'])
def annuler_projet(request, projet_id):
    """Annuler un projet (change simplement le statut)"""
    projet = get_object_or_404(Projet, id_projet=projet_id)
    
    # Vérifier que l'utilisateur a le droit
    if not (request.user.is_superuser or 
            (request.user.profile.role == 'chef' and 
             projet.chef_projet and 
             projet.chef_projet.user == request.user)):
        messages.error(request, "Vous n'avez pas les droits pour annuler ce projet.")
        return redirect('details_projets', projet_id=projet_id)
    
    # Changer le statut
    projet.statut = 'annule'
    projet.save()
    
    messages.success(request, f"Le projet '{projet.titre}' a été annulé.")
    return redirect('mes_projets')


@login_required
@role_required(['chef'])
def reactiver_projet(request, projet_id):
    """Réactiver un projet annulé"""
    projet = get_object_or_404(Projet, id_projet=projet_id)
    
    if projet.statut != 'annule':
        messages.error(request, "Ce projet n'est pas annulé.")
        return redirect('mes_projets')
    
    # Remettre le statut précédent ou par défaut
    projet.statut = 'a_venir'  # ou 'en_cours' selon le contexte
    projet.save()
    
    messages.success(request, f"Le projet '{projet.titre}' a été réactivé.")
    return redirect('mes_projets')



# ============================================
# GESTION DES EMPLOYÉS PAR LE REPRÉSENTANT
# ============================================

@login_required
@role_required(['entreprise'])
def gestion_employes(request):
    """Liste et gestion des employés par le représentant"""
    
    # Vérifier que l'utilisateur est bien un représentant
    try:
        entreprise = request.user.entreprise_representee
    except:
        messages.error(request, "Vous n'êtes pas le représentant d'une entreprise.")
        return redirect('projets_assignes')
    
    # Récupérer tous les employés (hors représentant)
    employes = User.objects.filter(
        profile__entreprise=entreprise,
        profile__est_employe=True
    ).select_related('profile')
    
    context = {
        'entreprise': entreprise,
        'employes': employes,
        'representant': request.user,
        'total_employes': employes.count()
    }
    return render(request, 'pages/entreprise/gestion_employes.html', context)


@login_required
@role_required(['entreprise'])
def ajouter_employe(request):
    """Ajouter un employé à l'entreprise (par le représentant)"""
    
    try:
        entreprise = request.user.entreprise_representee
    except:
        messages.error(request, "Vous n'êtes pas le représentant d'une entreprise.")
        return redirect('projets_assignes')
    
    if request.method == 'POST':
        form = AjoutEmployeForm(request.POST)
        if form.is_valid():
            # Récupérer les données
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            prenom = form.cleaned_data['prenom']
            nom = form.cleaned_data['nom']
            telephone = form.cleaned_data.get('telephone')
            profession = form.cleaned_data.get('profession')
            
            # Créer l'utilisateur
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=prenom,
                last_name=nom,
                is_active=True
            )
            
            # Créer le profil
            profile = UserProfile.objects.create(
                user=user,
                role='entreprise',
                entreprise=entreprise,
                est_employe=True,
                ajoute_par=request.user,
                telephone=telephone,
                profession=profession,
                date_inscription=timezone.now()
            )
            
            # Ajouter au groupe
            from django.contrib.auth.models import Group
            groupe_entreprise, _ = Group.objects.get_or_create(name='Entreprises')
            user.groups.add(groupe_entreprise)
            
            messages.success(
                request, 
                f"L'employé {username} a été ajouté à {entreprise.nom}."
            )
            return redirect('gestion_employes')
    else:
        form = AjoutEmployeForm()
    
    return render(request, 'pages/entreprise/ajouter_employe.html', {
        'form': form,
        'entreprise': entreprise
    })


@login_required
@role_required(['entreprise'])
def modifier_employe(request, user_id):
    """Modifier un employé de l'entreprise (par le représentant)"""
    
    try:
        entreprise = request.user.entreprise_representee
    except:
        messages.error(request, "Action non autorisée.")
        return redirect('projets_assignes')
    
    employe = get_object_or_404(User, id=user_id)
    
    # Vérifier que l'employé appartient à l'entreprise
    if not hasattr(employe, 'profile') or employe.profile.entreprise != entreprise or not employe.profile.est_employe:
        messages.error(request, "Cet employé n'appartient pas à votre entreprise.")
        return redirect('gestion_employes')
    
    if request.method == 'POST':
        form = ModifierEmployeForm(request.POST, instance=employe)
        if form.is_valid():
            # Modifier les infos de base
            employe.first_name = form.cleaned_data['first_name']
            employe.last_name = form.cleaned_data['last_name']
            employe.email = form.cleaned_data['email']
            
            # Modifier le mot de passe si fourni
            new_password = form.cleaned_data.get('new_password')
            if new_password:
                employe.set_password(new_password)
            
            employe.save()
            
            # Modifier le profil
            employe.profile.telephone = form.cleaned_data.get('telephone')
            employe.profile.profession = form.cleaned_data.get('profession')
            employe.profile.save()
            
            messages.success(request, f"Informations de {employe.username} mises à jour.")
            return redirect('gestion_employes')
    else:
        form = ModifierEmployeForm(instance=employe, initial={
            'telephone': employe.profile.telephone,
            'profession': employe.profile.profession
        })
    
    return render(request, 'pages/entreprise/modifier_employe.html', {
        'form': form,
        'employe': employe,
        'entreprise': entreprise
    })


@login_required
@role_required(['entreprise'])
def desactiver_employe(request, user_id):
    """Désactiver/réactiver un employé"""
    
    try:
        entreprise = request.user.entreprise_representee
    except:
        messages.error(request, "Action non autorisée.")
        return redirect('projets_assignes')
    
    employe = get_object_or_404(User, id=user_id)
    
    # Vérifications
    if employe == request.user:
        messages.error(request, "Vous ne pouvez pas vous désactiver vous-même.")
        return redirect('gestion_employes')
    
    if not hasattr(employe, 'profile') or employe.profile.entreprise != entreprise or not employe.profile.est_employe:
        messages.error(request, "Cet employé n'appartient pas à votre entreprise.")
        return redirect('gestion_employes')
    
    # Désactiver/réactiver
    employe.is_active = not employe.is_active
    employe.save()
    
    status = "activé" if employe.is_active else "désactivé"
    messages.success(request, f"L'employé {employe.username} a été {status}.")
    
    return redirect('gestion_employes')


@login_required
@role_required(['entreprise'])
def supprimer_employe(request, user_id):
    """Supprimer définitivement un employé"""
    
    try:
        entreprise = request.user.entreprise_representee
    except:
        messages.error(request, "Action non autorisée.")
        return redirect('projets_assignes')
    
    employe = get_object_or_404(User, id=user_id)
    
    if employe == request.user:
        messages.error(request, "Vous ne pouvez pas vous supprimer vous-même.")
        return redirect('gestion_employes')
    
    if not hasattr(employe, 'profile') or employe.profile.entreprise != entreprise or not employe.profile.est_employe:
        messages.error(request, "Cet employé n'appartient pas à votre entreprise.")
        return redirect('gestion_employes')
    
    username = employe.username
    employe.delete()
    
    messages.success(request, f"L'employé {username} a été supprimé définitivement.")
    return redirect('gestion_employes')



# ============================================
# API POUR RECHERCHE (AJAX)
# ============================================

def rechercher_projets(request):
    """API de recherche de projets (AJAX)"""
    query = request.GET.get('q', '')
    if query:
        projets = Projet.objects.filter(titre__icontains=query)[:10]
        results = [{'id': p.id_projet, 'text': p.titre} for p in projets]