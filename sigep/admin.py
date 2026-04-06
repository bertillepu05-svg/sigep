# sigep/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group
from django.utils.html import format_html
from .models import (
    UserProfile, ChefProjet, Entreprise, Projet, Phase, 
    SuiviBudget, Commentaire, Avis, ProjetSuivi
)

from .models import *


# ============================================
# ADMIN POUR UserProfile (Intégré à User)
# ============================================

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profil SIGEP'
    fk_name = 'user'  # Important car il y a plusieurs clés vers User
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('telephone', 'profession', 'sexe', 'photo', 'date_inscription')
        }),
        ('Adresse', {
            'fields': ('commune', 'quartier', 'avenue'),
            'classes': ('collapse',)
        }),
        ('Entreprise', {
            'fields': ('entreprise', 'est_employe'),
            'description': 'Pour les employés d\'entreprise'
        }),
        ('Rôle dans SIGEP', {
            'fields': ('role',),
            'description': '⚠️ Ce rôle détermine les accès et les menus visibles'
        }),
    )
    readonly_fields = ('date_inscription',)
    
    def apercu_photo(self, obj):
        if obj and obj.photo:
            return format_html(
                '<img src="{}" style="max-height: 50px; border-radius: 5px;" />',
                obj.photo.url
            )
        return "Aucune photo"
    apercu_photo.short_description = "Aperçu"


class CustomUserAdmin(UserAdmin):
    inlines = [UserProfileInline]
    list_display = [
        'username', 
        'email', 
        'get_full_name', 
        'get_role', 
        'get_entreprise',
        'get_type_utilisateur',
        'is_active',
        'date_joined'
    ]
    list_filter = [
        'profile__role', 
        'profile__est_employe',
        'profile__entreprise',
        'is_active', 
        'is_staff',
        'date_joined'
    ]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        ('Dates importantes', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',),
        }),
    )
    
    def get_role(self, obj):
        try:
            return obj.profile.get_role_display()
        except:
            return "Non défini"
    get_role.short_description = 'Rôle'
    get_role.admin_order_field = 'profile__role'
    
    def get_entreprise(self, obj):
        try:
            if obj.profile.entreprise:
                return obj.profile.entreprise.nom
            return "—"
        except:
            return "—"
    get_entreprise.short_description = 'Entreprise'
    
    def get_type_utilisateur(self, obj):
        try:
            if hasattr(obj, 'entreprise_representee'):
                return format_html(
                    '<span class="badge bg-success">🏢 Représentant</span>'
                )
            elif obj.profile.est_employe:
                return format_html(
                    '<span class="badge bg-info">👥 Employé</span>'
                )
            else:
                return format_html(
                    '<span class="badge bg-secondary">👤 Autre</span>'
                )
        except:
            return "—"
    get_type_utilisateur.short_description = 'Type'


# Désenregistrer et réenregistrer User
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# ============================================
# ADMIN POUR Group
# ============================================

class CustomGroupAdmin(GroupAdmin):
    list_display = ['name', 'get_user_count', 'get_permission_count']
    search_fields = ['name']
    
    def get_user_count(self, obj):
        return obj.user_set.count()
    get_user_count.short_description = "Utilisateurs"
    
    def get_permission_count(self, obj):
        return obj.permissions.count()
    get_permission_count.short_description = "Permissions"

admin.site.unregister(Group)
admin.site.register(Group, CustomGroupAdmin)


# ============================================
# ADMIN POUR ChefProjet (Ministères)
# ============================================

@admin.register(ChefProjet)
class ChefProjetAdmin(admin.ModelAdmin):
    list_display = ['nom_ministere', 'get_user', 'get_projets_count', 'get_budget_total']
    list_filter = ['user__profile__role']
    search_fields = ['nom_ministere', 'description', 'user__email']
    raw_id_fields = ['user']
    
    def get_user(self, obj):
        if obj.user:
            return format_html(
                '{} <br><small>',
                obj.user.username)
        return "—"
    get_user.short_description = "Chef projet"
    
    def get_projets_count(self, obj):
        return obj.projets.count()
    get_projets_count.short_description = "Projets"
    
    def get_budget_total(self, obj):
        from django.db.models import Sum
        total = obj.projets.aggregate(total=Sum('budget_previsionnel'))['total'] or 0
        return f"{total:,.0f} CDF".replace(',', ' ')
    get_budget_total.short_description = "Budget total"
    
    actions = ['creer_utilisateur_pour_ministere']
    
    def creer_utilisateur_pour_ministere(self, request, queryset):
        from django.contrib.auth.models import User
        import random
        import string
        
        for ministere in queryset:
            if not ministere.user:
                base_username = ministere.nom_ministere.lower().replace(' ', '_')[:15]
                username = base_username
                compteur = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}_{compteur}"
                    compteur += 1
                
                user = User.objects.create_user(
                    username=username,
                    email=f"{username}@sigep.cd",
                    password=''.join(random.choices(string.ascii_letters + string.digits, k=12)),
                    first_name="Chef",
                    last_name=ministere.nom_ministere[:20]
                )
                
                UserProfile.objects.create(
                    user=user,
                    role='chef'
                )
                
                ministere.user = user
                ministere.save()
                
                self.message_user(
                    request, 
                    f"✅ Utilisateur '{username}' créé pour {ministere.nom_ministere}"
                )
    creer_utilisateur_pour_ministere.short_description = "Créer un utilisateur pour ce(s) ministère(s)"


# ============================================
# ADMIN POUR Entreprise
# ============================================

@admin.register(Entreprise)
class EntrepriseAdmin(admin.ModelAdmin):
    list_display = [
        'nom', 
        'get_representant', 
        'get_nb_employes', 
        'email', 
        'telephone',
        'domaine_activite'
    ]
    list_filter = ['domaine_activite']
    search_fields = ['nom', 'email', 'representant__username']
    raw_id_fields = ['representant']
    
    fieldsets = (
        ('Informations de l\'entreprise', {
            'fields': ('nom', 'adresse', 'email', 'telephone', 'domaine_activite')
        }),
        ('Représentant principal', {
            'fields': ('representant',),
            'description': 'Le représentant peut gérer les employés de l\'entreprise'
        }),
    )
    
    def get_representant(self, obj):
        if obj.representant:
            return format_html(
                '<strong>{}</strong><br>',
                obj.representant.get_full_name() or obj.representant.username)
        return '<span style="color: red;">⚠️ Non défini</span>'
    get_representant.short_description = "Représentant"
    
    def get_nb_employes(self, obj):
        nb = obj.get_employes().count()
        if nb > 0:
            return format_html('<span class="badge bg-info">{}</span>', nb)
        return 0
    get_nb_employes.short_description = "Employés"
    
    actions = ['creer_representant']
    
    def creer_representant(self, request, queryset):
        from django.contrib.auth.models import User
        import random
        import string
        
        for entreprise in queryset:
            if not entreprise.representant:
                base_username = entreprise.nom.lower().replace(' ', '_')[:15]
                username = base_username
                compteur = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}_{compteur}"
                    compteur += 1
                
                user = User.objects.create_user(
                    username=username,
                    email=entreprise.email,
                    password=''.join(random.choices(string.ascii_letters + string.digits, k=12)),
                    first_name="Représentant",
                    last_name=entreprise.nom[:20]
                )
                
                UserProfile.objects.create(
                    user=user,
                    role='entreprise',
                    est_employe=False,
                    entreprise=entreprise
                )
                
                entreprise.representant = user
                entreprise.save()
                
                self.message_user(
                    request, 
                    f"✅ Représentant créé pour {entreprise.nom}. Username: {username}"
                )
    creer_representant.short_description = "Créer un représentant"


# ============================================
# INLINE POUR LES PHASES
# ============================================
class PhaseInline(admin.TabularInline):
    """
    Affiche les phases directement dans la page du projet
    """
    model = Phase
    extra = 1
    fields = ['nom_phase', 'date_debut', 'date_fin', 'pourcentage_avancement', 'photo']
    ordering = ['date_debut']
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        """Ajouter des attributs personnalisés aux champs"""
        if db_field.name == 'pourcentage_avancement':
            kwargs['widget'] = admin.widgets.AdminIntegerFieldWidget(attrs={'min': 0, 'max': 100})
        return super().formfield_for_dbfield(db_field, **kwargs)
    
    def get_extra(self, request, obj=None, **kwargs):
        """Limiter le nombre de lignes vides"""
        return 1 if obj else 0

# ============================================
# INLINE POUR LES SUIVIS BUDGÉTAIRES
# ============================================
class SuiviBudgetInline(admin.TabularInline):
    """
    Affiche les suivis budgétaires directement dans la page du projet
    """
    model = SuiviBudget
    extra = 1
    fields = ['budget_consomme', 'date_mise_a_jour', 'phase', 'commentaire']
    ordering = ['-date_mise_a_jour']
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Limiter les phases au projet en cours"""
        if db_field.name == 'phase' and hasattr(request, '_obj_'):
            kwargs["queryset"] = request._obj_.phases.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def get_extra(self, request, obj=None, **kwargs):
        """Mémoriser le projet pour le filtre des phases"""
        request._obj_ = obj
        return 1 if obj else 0


# ============================================
# ADMIN POUR PROJET
# ============================================
@admin.register(Projet)
class ProjetAdmin(admin.ModelAdmin):
    """
    Administration complète des projets
    """
    # ============================================
    # CONFIGURATION DE BASE
    # ============================================
    inlines = [PhaseInline, SuiviBudgetInline]
    
    list_display = [
        'titre',
        'apercu_photo',
        'domaine_activite',
        'get_ministere',
        'get_entreprise',
        'budget_formate',
        'budget_consomme_formate',
        'statut',
        'get_avancement',
        'get_pourcentage_budget'
    ]
    
    list_filter = [
        'statut',
        'domaine_activite',
        'chef_projet',
        'entreprise',
        'date_debut'
    ]
    
    search_fields = ['titre', 'description', 'province']
    list_per_page = 25
    date_hierarchy = 'date_debut'
    
    # ============================================
    # ORGANISATION DES CHAMPS
    # ============================================
    fieldsets = (
        ('Informations générales', {
            'fields': (
                ('titre', 'statut'),
                ('domaine_activite', 'province'),
                ('photo', 'apercu_photo_detail'),
                'description'
            )
        }),
        ('Budget et dates', {
            'fields': (
                ('budget_previsionnel', 'budget_consomme_total'),
                ('date_debut', 'date_fin_prevue')
            )
        }),
        ('Suivi budgétaire détaillé', {
            'fields': ('repartition_budget',),
            'classes': ('collapse',),
            'description': 'Détail des dépenses par phase'
        }),
        ('Acteurs du projet', {
            'fields': ('createur', 'chef_projet', 'entreprise'),
            'classes': ('wide',),
        }),
    )
    
    readonly_fields = [
        'apercu_photo_detail',
        'get_avancement',
        'budget_consomme_total',
        'repartition_budget'
    ]
    
    raw_id_fields = ['createur', 'chef_projet', 'entreprise']
    
    # ============================================
    # MÉTHODES D'AFFICHAGE
    # ============================================
    
    def apercu_photo(self, obj):
        """Miniature de la photo pour la liste"""
        if obj.photo:
            return format_html(
                '<img src="{}" style="max-height: 40px; width: auto; border-radius: 5px;" />',
                obj.photo.url
            )
        return "—"
    apercu_photo.short_description = "Photo"
    
    def apercu_photo_detail(self, obj):
        """Aperçu de la photo pour la page de détail"""
        if obj.photo:
            return format_html(
                '<img src="{}" style="max-height: 150px; border-radius: 10px;" />',
                obj.photo.url
            )
        return "Aucune photo"
    apercu_photo_detail.short_description = "Aperçu"
    
    def budget_formate(self, obj):
        """Formatage du budget prévisionnel"""
        return f"{obj.budget_previsionnel:,.0f} CDF".replace(',', ' ')
    budget_formate.short_description = "Budget"
    budget_formate.admin_order_field = 'budget_previsionnel'
    
    def budget_consomme_total(self, obj):
        """Total du budget consommé"""
        total = obj.suivis_budget.aggregate(total=models.Sum('budget_consomme'))['total'] or 0
        return f"{total:,.0f} CDF".replace(',', ' ')
    budget_consomme_total.short_description = "Dépensé"
    
    def budget_consomme_formate(self, obj):
        """Formatage court pour la liste"""
        total = obj.suivis_budget.aggregate(total=models.Sum('budget_consomme'))['total'] or 0
        return f"{total:,.0f} CDF".replace(',', ' ')
    budget_consomme_formate.short_description = "Dépensé"
    
    def get_ministere(self, obj):
        """Nom du ministère responsable"""
        return obj.chef_projet.nom_ministere if obj.chef_projet else "—"
    get_ministere.short_description = "Ministère"
    get_ministere.admin_order_field = 'chef_projet__nom_ministere'
    
    def get_entreprise(self, obj):
        """Nom de l'entreprise exécutante"""
        return obj.entreprise.nom if obj.entreprise else "—"
    get_entreprise.short_description = "Entreprise"
    get_entreprise.admin_order_field = 'entreprise__nom'
    
    def get_avancement(self, obj):
        """Calcul de l'avancement moyen du projet"""
        from django.db.models import Avg
        avg = obj.phases.aggregate(avg=Avg('pourcentage_avancement'))['avg'] or 0
        return f"{avg:.0f}%"
    get_avancement.short_description = "Avancement"
    
    def get_pourcentage_budget(self, obj):
        """Pourcentage du budget consommé avec barre de progression"""
        from django.db.models import Sum
        consomme = obj.suivis_budget.aggregate(total=Sum('budget_consomme'))['total'] or 0
        if obj.budget_previsionnel > 0:
            pourcent = (consomme / obj.budget_previsionnel) * 100
            color = "red" if pourcent > 100 else "green" if pourcent > 80 else "blue"
            return format_html(
                '<div style="width: 100px;">'
                '<div style="width: {}%; background: {}; height: 8px; border-radius: 4px;"></div>'
                '<span style="color: {}; font-size: 11px;">{:.1f}%</span>'
                '</div>',
                min(pourcent, 100), color, color, pourcent
            )
        return "—"
    get_pourcentage_budget.short_description = "Budget utilisé"
    
    def repartition_budget(self, obj):
        """Affiche la répartition du budget par phase"""
        from django.db.models import Sum
        
        html = '<div style="margin-top: 10px;">'
        total_consomme = obj.suivis_budget.aggregate(total=Sum('budget_consomme'))['total'] or 0
        
        if total_consomme == 0:
            html += '<p class="text-muted">Aucune dépense enregistrée</p>'
        else:
            # Dépenses par phase
            for phase in obj.phases.all():
                depenses = phase.depenses.aggregate(total=Sum('budget_consomme'))['total'] or 0
                if depenses > 0:
                    pourcent = (depenses / total_consomme) * 100
                    html += f'''
                    <div style="margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between;">
                            <span><strong>{phase.nom_phase}</strong></span>
                            <span>{depenses:,.0f} CDF ({pourcent:.1f}%)</span>
                        </div>
                        <div style="background: #e9ecef; height: 6px; border-radius: 3px;">
                            <div style="width: {pourcent:.1f}%; background: #27bfd4; height: 6px; border-radius: 3px;"></div>
                        </div>
                    </div>
                    '''
            
            # Dépenses sans phase
            depenses_sans_phase = obj.suivis_budget.filter(phase__isnull=True).aggregate(total=Sum('budget_consomme'))['total'] or 0
            if depenses_sans_phase > 0:
                pourcent = (depenses_sans_phase / total_consomme) * 100
                html += f'''
                <div style="margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between;">
                        <span><strong>Non affecté</strong></span>
                        <span>{depenses_sans_phase:,.0f} CDF ({pourcent:.1f}%)</span>
                    </div>
                    <div style="background: #e9ecef; height: 6px; border-radius: 3px;">
                        <div style="width: {pourcent:.1f}%; background: #6c757d; height: 6px; border-radius: 3px;"></div>
                    </div>
                </div>
                '''
        
        html += '</div>'
        return format_html(html)
    repartition_budget.short_description = "Répartition du budget"
    
    # ============================================
    # ACTIONS GROUPÉES
    # ============================================
    actions = ['marquer_en_cours', 'marquer_termine', 'marquer_annule', 'exporter_projets_csv']
    
    def marquer_en_cours(self, request, queryset):
        updated = queryset.update(statut='en_cours')
        self.message_user(request, f"✅ {updated} projet(s) marqué(s) en cours.")
    marquer_en_cours.short_description = "Marquer comme en cours"
    
    def marquer_termine(self, request, queryset):
        updated = queryset.update(statut='termine')
        self.message_user(request, f"✅ {updated} projet(s) marqué(s) terminé(s).")
    marquer_termine.short_description = "Marquer comme terminé"
    
    def marquer_annule(self, request, queryset):
        updated = queryset.update(statut='annule')
        self.message_user(request, f"✅ {updated} projet(s) marqué(s) annulé(s).")
    marquer_annule.short_description = "Marquer comme annulé"
    
    def exporter_projets_csv(self, request, queryset):
        """Exporte les projets sélectionnés en CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="projets.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Titre', 'Statut', 'Budget prévisionnel', 'Budget consommé',
            'Ministère', 'Entreprise', 'Date début', 'Date fin', 'Province'
        ])
        
        for projet in queryset:
            consomme = projet.suivis_budget.aggregate(total=models.Sum('budget_consomme'))['total'] or 0
            writer.writerow([
                projet.id_projet,
                projet.titre,
                projet.get_statut_display(),
                projet.budget_previsionnel,
                consomme,
                projet.chef_projet.nom_ministere if projet.chef_projet else '',
                projet.entreprise.nom if projet.entreprise else '',
                projet.date_debut,
                projet.date_fin_prevue,
                projet.province
            ])
        
        self.message_user(request, "✅ Export CSV effectué avec succès")
        return response
    exporter_projets_csv.short_description = "Exporter en CSV"
    
    # ============================================
    # PERSONNALISATION DE L'AFFICHAGE
    # ============================================
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }



# ============================================
# ADMIN POUR Phase
# ============================================

@admin.register(Phase)
class PhaseAdmin(admin.ModelAdmin):
    list_display = [
        'nom_phase', 
        'get_projet', 
        'date_debut', 
        'date_fin', 
        'pourcentage_avancement', 
        'progress_bar',
        'apercu_photo'
    ]
    list_filter = ['projet__statut', 'date_debut']
    search_fields = ['nom_phase', 'projet__titre']
    raw_id_fields = ['projet']
    
    def get_projet(self, obj):
        return obj.projet.titre
    get_projet.short_description = "Projet"
    
    def progress_bar(self, obj):
        color = "#28a745" if obj.pourcentage_avancement >= 100 else "#007bff"
        return format_html(
            '<div style="width: 100px; height: 20px; background: #e9ecef; border-radius: 10px;">'
            '<div style="width: {}%; height: 100%; background: {}; border-radius: 10px; text-align: center; color: white; font-size: 11px; line-height: 20px;">{}%</div>'
            '</div>',
            obj.pourcentage_avancement, color, obj.pourcentage_avancement
        )
    progress_bar.short_description = "Progression"
    
    def apercu_photo(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="max-height: 30px;" />',
                obj.photo.url
            )
        return "—"
    apercu_photo.short_description = "Photo"


# ============================================
# ADMIN POUR SuiviBudget
# ============================================

@admin.register(SuiviBudget)
class SuiviBudgetAdmin(admin.ModelAdmin):
    """
    Administration des suivis budgétaires
    """
    list_display = [
        'get_projet_titre',
        'budget_consomme_formate',
        'date_mise_a_jour',
        'get_phase_nom',
        'commentaire_court',
        'date_creation'
    ]
    
    list_filter = [
        'date_mise_a_jour',
        'projet__statut',
        'projet__chef_projet',
        'phase'
    ]
    
    search_fields = [
        'projet__titre',
        'commentaire',
        'phase__nom_phase'
    ]
    
    date_hierarchy = 'date_mise_a_jour'
    
    fieldsets = (
        ('Informations générales', {
            'fields': (
                'projet',
                'phase',
                ('budget_consomme', 'date_mise_a_jour')
            )
        }),
        ('Détails', {
            'fields': ('commentaire',),
            'classes': ('wide',)
        }),
    )
    
    raw_id_fields = ['projet', 'phase']
    list_per_page = 25
    list_select_related = ['projet', 'phase']
    
    def get_projet_titre(self, obj):
        """Affiche le titre du projet"""
        return obj.projet.titre
    get_projet_titre.short_description = "Projet"
    get_projet_titre.admin_order_field = 'projet__titre'
    
    def budget_consomme_formate(self, obj):
        """Formatage du budget avec séparateurs"""
        return f"{obj.budget_consomme:,.0f} CDF".replace(',', ' ')
    budget_consomme_formate.short_description = "Montant"
    budget_consomme_formate.admin_order_field = 'budget_consomme'
    
    def get_phase_nom(self, obj):
        """Affiche le nom de la phase"""
        return obj.phase.nom_phase if obj.phase else "—"
    get_phase_nom.short_description = "Phase"
    get_phase_nom.admin_order_field = 'phase__nom_phase'
    
    def commentaire_court(self, obj):
        """Affiche un extrait du commentaire"""
        return obj.commentaire[:50] + "..." if len(obj.commentaire) > 50 else obj.commentaire
    commentaire_court.short_description = "Commentaire"
    
    def date_creation(self, obj):
        """Affiche la date de création"""
        return obj.date_mise_a_jour
    date_creation.short_description = "Date"
    
    # Actions groupées
    actions = ['exporter_csv', 'calculer_total']
    
    def exporter_csv(self, request, queryset):
        """Exporte les suivis budgétaires en CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="suivis_budget.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Projet', 'Phase', 'Montant', 'Date', 'Commentaire'])
        
        for suivi in queryset:
            writer.writerow([
                suivi.projet.titre,
                suivi.phase.nom_phase if suivi.phase else 'Global',
                suivi.budget_consomme,
                suivi.date_mise_a_jour,
                suivi.commentaire
            ])
        
        self.message_user(request, "Export CSV effectué avec succès")
        return response
    exporter_csv.short_description = "Exporter en CSV"
    
    def calculer_total(self, request, queryset):
        """Calcule le total des dépenses sélectionnées"""
        total = queryset.aggregate(total=models.Sum('budget_consomme'))['total'] or 0
        self.message_user(request, f"Total des dépenses sélectionnées : {total:,.0f} CDF".replace(',', ' '))
    calculer_total.short_description = "Calculer le total"

# ============================================
# ADMIN POUR Commentaire
# ============================================

@admin.register(Commentaire)
class CommentaireAdmin(admin.ModelAdmin):
    list_display = ['get_utilisateur', 'get_projet', 'extrait_commentaire', 'date_commentaire']
    list_filter = ['date_commentaire', 'projet']
    search_fields = ['contenu', 'utilisateur__username', 'projet__titre']
    date_hierarchy = 'date_commentaire'
    raw_id_fields = ['utilisateur', 'projet']
    
    def get_utilisateur(self, obj):
        return obj.utilisateur.username
    get_utilisateur.short_description = "Utilisateur"
    
    def get_projet(self, obj):
        return obj.projet.titre
    get_projet.short_description = "Projet"
    
    def extrait_commentaire(self, obj):
        return obj.contenu[:50] + "..." if len(obj.contenu) > 50 else obj.contenu
    extrait_commentaire.short_description = "Commentaire"


# ============================================
# ADMIN POUR Avis
# ============================================

@admin.register(Avis)
class AvisAdmin(admin.ModelAdmin):
    list_display = ['get_utilisateur', 'get_projet', 'etoiles', 'date_avis']
    list_filter = ['note', 'date_avis']
    search_fields = ['utilisateur__username', 'projet__titre']
    date_hierarchy = 'date_avis'
    raw_id_fields = ['utilisateur', 'projet']
    
    def get_utilisateur(self, obj):
        return obj.utilisateur.username
    get_utilisateur.short_description = "Utilisateur"
    
    def get_projet(self, obj):
        return obj.projet.titre
    get_projet.short_description = "Projet"
    
    def etoiles(self, obj):
        return "★" * obj.note + "☆" * (5 - obj.note)
    etoiles.short_description = "Note"


# ============================================
# ADMIN POUR ProjetSuivi
# ============================================

@admin.register(ProjetSuivi)
class ProjetSuiviAdmin(admin.ModelAdmin):
    list_display = ['get_utilisateur', 'get_projet', 'date_suivi']
    list_filter = ['date_suivi']
    search_fields = ['utilisateur__username', 'projet__titre']
    date_hierarchy = 'date_suivi'
    raw_id_fields = ['utilisateur', 'projet']
    
    def get_utilisateur(self, obj):
        return obj.utilisateur.username
    get_utilisateur.short_description = "Utilisateur"
    
    def get_projet(self, obj):
        return obj.projet.titre
    get_projet.short_description = "Projet"


# ============================================
# PERSONNALISATION DU SITE ADMIN
# ============================================

admin.site.site_header = "SIGEP - Administration"
admin.site.site_title = "SIGEP Admin"
admin.site.index_title = "Bienvenue dans l'administration de SIGEP"