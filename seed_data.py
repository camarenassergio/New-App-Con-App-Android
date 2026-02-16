import os
import django
import sys

# Add project root to path
sys.path.append('/home/sscamarenas/Proyectos/Logistica Casa Lupita/New App Con App Android')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import datetime

import random
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth import get_user_model
from dashboard.models import Unidad, RegistroCombustible, GastoUnidad, Viaje, Operador

User = get_user_model()

def run():
    print("--- INICIANDO RESET DE BASE DE DATOS (MÓDULO DASHBOARD) ---")

    # 1. Limpiar datos existentes
    print("Eliminando registros antiguos...")
    RegistroCombustible.objects.all().delete()
    GastoUnidad.objects.all().delete()
    Viaje.objects.all().delete()
    Unidad.objects.all().delete()
    Operador.objects.all().delete()

    # 2. Obtener o crear Usuario Chofer/Admin
    # Intentamos obtener un superusuario o el primer usuario
    usuario = User.objects.filter(is_superuser=True).first()
    if not usuario:
        usuario = User.objects.first()
    
    if not usuario:
        print("Creando usuario de prueba...")
        usuario = User.objects.create_user('admin_test', 'admin@test.com', 'password123')
        usuario.is_superuser = True
        usuario.is_staff = True
        usuario.save()

    print(f"Usando usuario: {usuario.username}")

    # 3. Crear Unidades
    print("Creando 4 unidades de prueba...")
    unidades_data = [
        {"placas": "LF-10-234", "marca": "Freightliner", "submarca": "M2", "modelo": 2018, "km_inicial": 120000},
        {"placas": "XD-99-001", "marca": "Nissan", "submarca": "NP300", "modelo": 2020, "km_inicial": 85000},
        {"placas": "AB-12-345", "marca": "Isuzu", "submarca": "ELF 400", "modelo": 2022, "km_inicial": 45000},
        {"placas": "ZZ-88-777", "marca": "Hino", "submarca": "Series 300", "modelo": 2019, "km_inicial": 98000},
    ]

    unidades_objs = []
    for data in unidades_data:
        u = Unidad.objects.create(
            placas=data["placas"],
            marca=data["marca"],
            submarca=data["submarca"],
            modelo_anio=data["modelo"],
            kilometraje_actual=data["km_inicial"], # Se actualizará al final
            capacidad_kg=5000,
            tipo_combustible_unidad='DIESEL'
        )
        # Hack para guardar el km inicial en el objeto python para referencia
        u.km_referencia = data["km_inicial"] 
        unidades_objs.append(u)
        print(f"Unidad creada: {u}")

    # 4. Generar Registros de Combustible
    # Fechas: Diciembre 2025, Enero 2026, Febrero 2026
    # Generaremos ~4-6 cargas por mes por unidad
    
    meses = [
        (2025, 12),
        (2026, 1),
        (2026, 2)
    ]
    
    precio_diesel_base = 24.50

    for u in unidades_objs:
        km_actual = u.km_referencia
        
        for anio, mes in meses:
            # Determinar días en el mes
            if mes == 12:
                dias_mes = 31
            elif mes == 2:
                dias_mes = 28 # 2026 no es bisiesto
            else:
                dias_mes = 31 # Enero
            
            # Generar fechas aleatorias ordenadas dentro del mes
            dias_carga = sorted(random.sample(range(1, dias_mes + 1), k=random.randint(4, 6)))
            
            for dia in dias_carga:
                fecha = datetime.date(anio, mes, dia)
                
                # Simular kilometraje recorrido (entre 300 y 600 km por carga)
                km_recorridos = random.randint(300, 600)
                km_actual += km_recorridos
                
                # Simular rendimiento (Km/L) entre 3.0 y 5.5 para camiones
                rendimiento = random.uniform(3.5, 5.0)
                litros = round(km_recorridos / rendimiento, 2)
                
                # Variacion precio
                precio = precio_diesel_base + random.uniform(-0.5, 0.5)
                total = round(litros * precio, 2)
                
                RegistroCombustible.objects.create(
                    unidad=u,
                    fecha=fecha,
                    chofer=usuario,
                    kilometraje_actual=km_actual,
                    litros=litros,
                    precio_litro=round(precio, 2),
                    total=total,
                    tipo_combustible='DIESEL',
                    propina=0 # Opcional
                )
        
        # Actualizar el kilometraje final de la unidad
        u.kilometraje_actual = km_actual
        u.save()
        print(f"  -> Registros generados para {u.nUnidad}. Km Final: {km_actual}")

    print("--- CARGA DE DATOS COMPLETADA EXITOSAMENTE ---")

if __name__ == '__main__':
    run()
