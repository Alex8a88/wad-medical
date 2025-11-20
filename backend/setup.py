#!/usr/bin/env python
import os
import sys
import django
from django.core.management import execute_from_command_line

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical_system.settings')
django.setup()

from users.models import Usuario, CatalogoEstados, Grupos

def setup_database():
    print("Setting up Medical Prescription Database (mpd.db)...")
    
    # Run migrations
    print("1. Running migrations...")
    execute_from_command_line(['manage.py', 'makemigrations'])
    execute_from_command_line(['manage.py', 'migrate'])
    
    # Create Mexican States
    print("2. Populating Mexican States...")
    estados_mexico = [
        'Aguascalientes', 'Baja California', 'Baja California Sur', 'Campeche',
        'Chiapas', 'Chihuahua', 'Ciudad de México', 'Coahuila', 'Colima',
        'Durango', 'Guanajuato', 'Guerrero', 'Hidalgo', 'Jalisco', 'México',
        'Michoacán', 'Morelos', 'Nayarit', 'Nuevo León', 'Oaxaca', 'Puebla',
        'Querétaro', 'Quintana Roo', 'San Luis Potosí', 'Sinaloa', 'Sonora',
        'Tabasco', 'Tamaulipas', 'Tlaxcala', 'Veracruz', 'Yucatán', 'Zacatecas'
    ]
    
    for estado in estados_mexico:
        CatalogoEstados.objects.get_or_create(nombre_estado=estado)
    
    # Create Groups
    print("3. Creating user groups...")
    grupos = ['Doctor', 'Mesa de Servicio', 'Administrador']
    for grupo in grupos:
        Grupos.objects.get_or_create(nombre_grupo=grupo)
    
    # Create superuser
    print("4. Creating superuser...")
    mesa_servicio_grupo = Grupos.objects.get(nombre_grupo='Mesa de Servicio')
    
    if not Usuario.objects.filter(email_usuario='admin@medicalsystem.com').exists():
        superuser = Usuario.objects.create_superuser(
            email_usuario='admin@medicalsystem.com',
            password='admin123',
            primer_nombre='Admin',
            primer_apellido='System',
            edad=30,
            genero='X',
            numero_telefono='1234567890',
            grupos=mesa_servicio_grupo
        )
        print(f"Superuser created: {superuser.email_usuario}")
    else:
        print("Superuser already exists")
    
    print("\n✅ Database setup complete!")
    print("📧 Login: admin@medicalsystem.com")
    print("🔑 Password: admin123")
    print("🗄️ Database: mpd.db")

if __name__ == '__main__':
    setup_database()