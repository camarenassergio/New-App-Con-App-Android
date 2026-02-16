
import os
import django
import random
from datetime import date, timedelta
from django.utils import timezone
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from dashboard.models import Unidad, RegistroCombustible
from django.contrib.auth import get_user_model

User = get_user_model()

def generar_datos_combustible_2025_2026():
    print("--- INICIANDO GENERACIÓN DE DATOS DE COMBUSTIBLE (2025-2026) ---")
    
    # 1. Limpiar registros existentes
    print("Eliminando registros anteriores...")
    RegistroCombustible.objects.all().delete()
    
    # 2. Configuración Base
    unidades = Unidad.objects.all()
    usuarios = User.objects.filter(is_active=True)
    if not usuarios.exists():
        print("Error: No hay usuarios activos para asignar como chofer.")
        return

    usuario_default = usuarios.first() # Fallback
    
    # Rango de Fechas: Enero 2025 -> Hoy (Feb 2026)
    fecha_inicio = date(2025, 1, 1)
    fecha_fin = timezone.now().date()
    # Asegurarnos de cubrir hasta hoy
    
    # Precios Aprox por Litro (Variación mensual ligera)
    precio_base = 24.50 
    
    for unidad in unidades:
        print(f"\nProcesando Unidad: {unidad.nUnidad} - {unidad.marca}")
        
        # Kilometraje Inicial para 2025 (Simulado)
        # Asumimos que empezaron el año con algo razonable, ej. 150,000 km
        km_actual = 150000 + random.randint(0, 50000)
        
        current_date = fecha_inicio
        
        # Iterar mes a mes hasta la fecha actual
        while current_date <= fecha_fin:
            year = current_date.year
            month = current_date.month
            
            # Determinar el último día del mes actual o la fecha_fin si es el mes actual
            import calendar
            last_day = calendar.monthrange(year, month)[1]
            month_end_date = date(year, month, last_day)
            
            if month_end_date > fecha_fin:
                month_end_date = fecha_fin
            
            # Determinar Nivel de Actividad del Mes (Aleatorio)
            # 20% Probabilidad de "Baja Actividad/Taller" (0-2 cargas)
            # 80% Probabilidad de "Actividad Normal" (4-10 cargas)
            actividad = random.choices(['BAJA', 'NORMAL'], weights=[20, 80])[0]
            
            if actividad == 'BAJA':
                num_cargas = random.randint(0, 2)
            else:
                num_cargas = random.randint(4, 10)
                
            if num_cargas == 0:
                print(f"  {current_date.strftime('%B %Y')}: SIN ACTIVIDAD")
                # Avanzar al siguiente mes
                if month == 12:
                    current_date = date(year + 1, 1, 1)
                else:
                    current_date = date(year, month + 1, 1)
                continue
                
            print(f"  {current_date.strftime('%B %Y')}: {num_cargas} cargas ({actividad})")
            
            # Generar fechas aleatorias dentro del mes para las cargas
            # Simplemente distribuimos los días uniformemente o random
            dias_disponibles = list(range(1, month_end_date.day + 1))
            dias_cargas = sorted(random.sample(dias_disponibles, k=min(num_cargas, len(dias_disponibles))))
            
            for dia in dias_cargas:
                fecha_carga = date(year, month, dia)
                
                # Simular KM recorrido desde la última carga
                # Promedio diario aprox 100-300 km? Depende de la unidad
                # Entre cargas (aprox 3-7 días) -> 300-1000 km
                km_recorrido = random.randint(200, 800)
                
                # Actualizar KM total
                km_actual += km_recorrido
                
                # Calcular Litros necesarios (Rendimiento aprox 3-6 km/l para camiones)
                rendimiento_esperado = random.uniform(2.5, 4.5) 
                litros_necesarios = km_recorrido / rendimiento_esperado
                
                # Variación de llenado (No siempre es full exacto)
                litros_reales = round(litros_necesarios * random.uniform(0.95, 1.05), 2)
                
                # Calcular Precio
                # Variación de precio +/- 5%
                precio_litro = round(precio_base * random.uniform(0.98, 1.05), 2)
                
                # Calcular Total
                costo_combustible = round(litros_reales * float(precio_litro), 2)
                
                # Propina (Ocasional)
                propina = 0
                if random.random() < 0.3: # 30% de las veces dan propina
                    propina = random.choice([20, 30, 50])
                
                total_final = costo_combustible + propina
                
                # Crear Registro
                RegistroCombustible.objects.create(
                    unidad=unidad,
                    chofer=usuario_default, # O random choice de usuarios
                    fecha=fecha_carga,
                    kilometraje_actual=km_actual,
                    litros=Decimal(litros_reales),
                    precio_litro=Decimal(precio_litro),
                    total=Decimal(total_final),
                    propina=Decimal(propina),
                    observaciones="Carga generada automáticamante"
                )
                
            # Avanzar al siguiente mes
            if month == 12:
                current_date = date(year + 1, 1, 1)
            else:
                current_date = date(year, month + 1, 1)

        # Al terminar, actualizar la Unidad con el último kilometraje
        unidad.kilometraje_actual = km_actual
        unidad.save()
        print(f" -> Finalizado {unidad.nUnidad}: {km_actual} Km")

    print("\n--- PROCESO TERMINADO ---")

if __name__ == '__main__':
    generar_datos_combustible_2025_2026()
