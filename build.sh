#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Script em Python para criar o Superuser e o Restaurante inicial
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from tenants.models import Restaurant

User = get_user_model()
if not User.objects.filter(username='fabio').exists():
    User.objects.create_superuser('fabio', '', '1234')
    print('✅ Usuário fabio criado com sucesso!')

if not Restaurant.objects.filter(slug='doceria-vida-doce').exists():
    Restaurant.objects.create(name='Doceria Vida Doce', slug='doceria-vida-doce', whatsapp_number='11969603611', is_active=True)
    print('✅ Restaurante doceria-vida-doce criado com sucesso!')
"
