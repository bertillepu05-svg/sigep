import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projet_sigep.settings')
django.setup()

from django.contrib.auth.models import User
from sigep.models import UserProfile

def creer_profils_manquants():
    """Crée des profils pour tous les utilisateurs qui n'en ont pas"""
    users = User.objects.all()
    compteur = 0
    
    print(" Vérification des profils utilisateurs...")
    print("-" * 40)
    
    for user in users:
        try:
            profile = user.profile
            print(f"{user.username} - Profil existant")
        except:
            # Profil inexistant, on le crée
            UserProfile.objects.create(
                user=user,
                role='observateur',  # Rôle par défaut
                date_inscription=user.date_joined
            )
            compteur += 1
            print(f"Profil créé pour {user.username} (email: {user.email})")
    
    print("-" * 40)
    print(f"\n Résultat : {compteur} profil(s) créé(s) sur {users.count()} utilisateur(s)")

if __name__ == '__main__':
    print("Lancement de la correction des profils...\n")
    creer_profils_manquants()
    print("\n Correction terminée !")