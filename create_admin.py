import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projet_sigep.settings')
django.setup()

from django.contrib.auth.models import User

if not User.objects.filter(username='sigep').exists():
    User.objects.create_superuser('sigep', 'sigep@gmail.com', 'sigep')
    print("✅ Super-utilisateur créé avec succès !")
else:
    print("⚠️ Le super-utilisateur existe déjà.")
