import os
import django
from django.core.files import File

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projet_sigep.settings')
django.setup()

from sigep.models import UserProfile, Projet, Phase
from django.conf import settings

def migrer_photos_profil():
    """Convertit les chemins texte en ImageField"""
    for profil in UserProfile.objects.all():
        if profil.photo and isinstance(profil.photo, str):
            ancien_chemin = profil.photo
            # Si c'est un chemin texte, on le garde comme tel pour l'instant
            # Ou on peut copier le fichier vers le nouvel emplacement
            print(f"Profil {profil.user.username}: {ancien_chemin}")

def migrer_photos_projet():
    for projet in Projet.objects.all():
        if projet.photo and isinstance(projet.photo, str):
            print(f"Projet {projet.titre}: {projet.photo}")

if __name__ == '__main__':
    print("Migration des photos...")
    migrer_photos_profil()
    migrer_photos_projet()
    print("Terminé!")