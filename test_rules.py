import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from dashboard.models import Unidad, ConfiguracionLogistica
import datetime

config = ConfiguracionLogistica.objects.first()
if not config:
    config = ConfiguracionLogistica.objects.create()

config.estado_contingencia = 'FASE_1'
config.restringir_h1 = 'PAR' # Testing con PAR 
config.save()

hoy = datetime.date.today()
dia_semana = hoy.weekday()
dias_nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
dia_actual = dias_nombres[dia_semana]

# Determinar un dígito que deba descansar hoy (basado en el calendario ordinario)
digitos_descanso = {
    0: '5', # Lunes: Amarillo 5-6
    1: '7', # Martes: Rosa 7-8
    2: '3', # Miércoles: Rojo 3-4
    3: '1', # Jueves: Verde 1-2
    4: '9', # Viernes: Azul 9-0
}
digito_restringido_hoy = digitos_descanso.get(dia_semana, '5') # fallback 5 para sabado/domingo
digito_libre_hoy = '2' if digito_restringido_hoy != '2' else '5' # garantizar uno diferente

print(f"Estado DB: {config.estado_contingencia} | Restricción H1: {config.restringir_h1}")
print(f"Hoy es {dia_actual} -> Placas terminación {digito_restringido_hoy} NO deben circular (doble hoy no circula).")

tests = [
    # 00 - Mismo color del día (Debe ser bloqueado por Doble Hoy No Circula)
    Unidad(holograma='00', placas=f'XY123{digito_restringido_hoy}'), 
    # 00 - Diferente color del día (Debe pasar como exento)
    Unidad(holograma='00', placas=f'XY123{digito_libre_hoy}'), 
    
    # 2 - Nunca circula en Fase 1/2
    Unidad(holograma='2', placas='XY1234'),
    
    # 1 - Par (Debería bloquearse por Fase 1 - PAR)
    Unidad(holograma='1', placas='ABC1234'), # Termina en 4
    
    # 1 - Non (Debería circular, A MENOS que sea su día de restricción ordinario)
    Unidad(holograma='1', placas='ABC1235'), # Termina en 5
]

print("\n--- RESULTADOS FASE 1 ---")
for u in tests:
    print(f"Holo {u.holograma} | Placa {u.placas} (Fin {u.ultimo_digito}): {u.alerta_circulacion}")
