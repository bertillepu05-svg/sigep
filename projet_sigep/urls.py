# projet_sigep/urls.py
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from sigep import views


urlpatterns = [
    # ============================================
    # ADMINISTRATION
    # ============================================
    path('admin/', admin.site.urls),
    
    # ============================================
    # AUTHENTIFICATION (PUBLIC)
    # ============================================
    path('', views.index, name='index'),
    path('connexion/', views.login_view, name='login'),
    path('inscription/', views.register, name='register'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='pages/auth/password_reset.html'), name='password_reset'),
    path('deconnexion/', views.logout_view, name='logout'),
    
    # ============================================
    # PROFIL UTILISATEUR (CONNECTÉ)
    # ============================================
    path('profil/', views.profil, name='profil'),
    path('profil/modifier/', views.modifier_profil, name='modifier_profil'),
     path('profil/supprimer/', views.modifier_profil, name='supprimer_compte'),
    
    # ============================================
    # PROJETS (PUBLIC)
    # ============================================
    path('projets/', views.liste_projets, name='liste_projets'),
    path('projets/a-venir/', views.projets_a_venir, name='projets_a_venir'),
    path('projets/en-cours/', views.projets_en_cours, name='projets_en_cours'),
    path('projets/termines/', views.projets_termines, name='projets_termines'),
    path('projets/<int:projet_id>/', views.details_projets, name='details_projets'),
    
    # ============================================
    # PROJETS SUIVIS (OBSERVATEUR)
    # ============================================
    path('projets/suivis/', views.projets_suivis, name='projets_suivis'),
    path('projets/<int:projet_id>/suivre/', views.toggle_suivre_projet, name='toggle_suivre'),
    
    # ============================================
    # COMMENTAIRES (OBSERVATEUR)
    # ============================================
    path('projets/<int:projet_id>/commentaires/ajouter/', views.ajouter_commentaire, name='ajouter_commentaire'),
    path('commentaires/<int:commentaire_id>/modifier/', views.modifier_commentaire, name='modifier_commentaire'),
    path('commentaires/<int:commentaire_id>/supprimer/', views.supprimer_commentaire, name='supprimer_commentaire'),
    
    # ============================================
    # AVIS/NOTES (OBSERVATEUR)
    # ============================================
    path('projets/<int:projet_id>/avis/', views.avis, name='donner_avis'),
    
    # ============================================
    # CHEF DE PROJET (MINISTÈRE)
    # ============================================
    path('chef/projets/', views.mes_projets, name='mes_projets'),
    path('chef/projets/initialiser/', views.initialiser_projet, name='initialiser_projet'),
    path('chef/projets/<int:projet_id>/modifier/', views.modifier_projet, name='modifier_projet'),
    path('chef/projets/<int:projet_id>/annuler/', views.annuler_projet, name='annuler_projet'),
    path('chef/projets/<int:projet_id>/reactiver/', views.reactiver_projet, name='reactiver_projet'),


    # ============================================
    # ENTREPRISE
    # ============================================

    path('entreprise/projets/', views.projets_assignes, name='projets_assignes'),
    # path('entreprise/projets/', views.projets_assignes_v2, name='mes_projets_assignes'),
    # path('entreprise/projets/<int:projet_id>/avancement/', views.mettre_a_jour_avancement, name='mettre_a_jour_avancement'),
    path('entreprise/projets/<int:projet_id>/phases/ajouter/', views.ajouter_phase_entreprise, name='ajouter_phase_entreprise'),
    path('entreprise/phases/<int:phase_id>/modifier/', views.modifier_phase_entreprise, name='modifier_phase_entreprise'),

    # Suivi budgétaire
    path('projets/<int:projet_id>/budget/ajouter/', views.ajouter_suivi_budget, name='ajouter_suivi_budget'),
    path('budget/<int:suivi_id>/modifier/', views.modifier_suivi_budget, name='modifier_suivi_budget'),
    path('budget/<int:suivi_id>/supprimer/', views.supprimer_suivi_budget, name='supprimer_suivi_budget'),


    # ============================================
    # Gestion des employés (représentant)
    # ============================================
    path('entreprise/employes/', views.gestion_employes, name='gestion_employes'),
    path('entreprise/employes/ajouter/', views.ajouter_employe, name='ajouter_employe'),
    path('entreprise/employes/<int:user_id>/modifier/', views.modifier_employe, name='modifier_employe'),
    path('entreprise/employes/<int:user_id>/desactiver/', views.desactiver_employe, name='desactiver_employe'),
    path('entreprise/employes/<int:user_id>/supprimer/', views.supprimer_employe, name='supprimer_employe'),
    

    # Phases (enployes)
    path('entreprise/phases/', views.mes_phases, name='mes_phases'),
    path('entreprise/projets/<int:projet_id>/phases/ajouter/', views.ajouter_phase_entreprise, name='ajouter_phase_entreprise'),
    path('entreprise/phases/<int:phase_id>/modifier/', views.modifier_phase_entreprise, name='modifier_phase_entreprise'),

     
    # Gestion du statut (chef de projet)
    path('chef/projets/<int:projet_id>/statut/', views.changer_statut_projet, name='changer_statut_projet'),

    # ============================================
    # API (RECHERCHE AJAX)
    # ============================================
    path('api/rechercher-projets/', views.rechercher_projets, name='rechercher_projets'),
]

# ============================================
# SERVIR LES FICHIERS MEDIA EN DEVELOPPEMENT
# ============================================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += staticfiles_urlpatterns()