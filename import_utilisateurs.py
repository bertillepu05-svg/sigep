# import_utilisateurs.py
import os
import django
from django.contrib.auth.hashers import make_password

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projet_sigep.settings')
django.setup()

from django.contrib.auth.models import User
from sigep.models import Utilisateur as OldUser
from sigep.models import Role

def migrer_utilisateurs():
    """
    Migre les utilisateurs de la table 'utilisateurs' vers 'auth_user'
    """
    print(" Début de la migration des utilisateurs...")
    
    # Récupérer tous les anciens utilisateurs
    anciens_utilisateurs = OldUser.objects.all()
    print(f" {anciens_utilisateurs.count()} utilisateurs trouvés")
    
    compteur = 0
    for ancien in anciens_utilisateurs:
        # Vérifier si l'email existe déjà
        if User.objects.filter(email=ancien.email).exists():
            print(f"Email déjà existant: {ancien.email} - Ignoré")
            continue
        
        # Déterminer le rôle
        role_nom = ancien.id_role.nom_role if ancien.id_role else 'Observateur'
        
        # Créer le nouvel utilisateur Django
        nouveau = User.objects.create_user(
            username=ancien.email.split('@')[0],  # ou utilise ancien.email
            email=ancien.email,
            password=ancien.mot_de_passe or 'changeme123',  # mot de passe temporaire
            first_name=ancien.prenom or '',
            last_name=ancien.nom or '',
            is_active=(ancien.statut == 'actif')
        )
        
        # Ajouter les infos supplémentaires dans le profil
        # (si tu utilises UserProfile)
        from sigep.models import UserProfile
        UserProfile.objects.update_or_create(
            user=nouveau,
            defaults={
                'telephone': ancien.telephone,
                'profession': ancien.profession,
                'commune': ancien.commune,
                'quartier': ancien.quartier,
                'avenue': ancien.avenue,
                'sexe': ancien.sexe,
                'photo': ancien.photo,
                'date_inscription': ancien.date_inscription,
                'role': role_nom.lower().replace(' ', '_')
            }
        )
        
        # Ajouter aux groupes selon le rôle
        from django.contrib.auth.models import Group
        if role_nom == 'Admin':
            nouveau.is_superuser = True
            nouveau.is_staff = True
            nouveau.save()
        elif role_nom == 'Chef de projet':
            group, _ = Group.objects.get_or_create(name='Chefs de projet')
            nouveau.groups.add(group)
        elif role_nom == 'Entreprise':
            group, _ = Group.objects.get_or_create(name='Entreprises')
            nouveau.groups.add(group)
        
        compteur += 1
        print(f" Utilisateur migré: {ancien.email} -> {nouveau.username}")
    
    print(f"\n Migration terminée: {compteur} utilisateurs migrés!")

def lier_ministères_entreprises():
    """
    Lie les ministères et entreprises aux nouveaux utilisateurs
    """
    print("\n Liaison des ministères et entreprises...")
    
    from sigep.models import ChefProjet, Entreprise
    from django.contrib.auth.models import User
    
    # Lier les ministères
    for ministere in ChefProjet.objects.all():
        if ministere.id_user:
            try:
                old_user = ministere.id_user
                new_user = User.objects.get(email=old_user.email)
                ministere.user = new_user
                ministere.save()
                print(f"Ministère '{ministere.nom_ministere}' lié à {new_user.email}")
            except:
                print(f"Ministère '{ministere.nom_ministere}' non lié")
    
    # Lier les entreprises
    for entreprise in Entreprise.objects.all():
        if entreprise.id_user:
            try:
                old_user = entreprise.id_user
                new_user = User.objects.get(email=old_user.email)
                entreprise.user = new_user
                entreprise.save()
                print(f" Entreprise '{entreprise.nom}' liée à {new_user.email}")
            except:
                print(f" Entreprise '{entreprise.nom}' non liée")

if __name__ == '__main__':
    print("=" * 50)
    print("MIGRATION DES UTILISATEURS VERS AUTH_USER")
    print("=" * 50)
    
    # Demander confirmation
    reponse = input("Cette opération va migrer les utilisateurs. Continuer? (oui/non): ")
    
    if reponse.lower() == 'oui':
        migrer_utilisateurs()
        lier_ministères_entreprises()
        print("\n✨ Migration terminée avec succès!")
    else:
        print("Migration annulée")