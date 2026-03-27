import os
import sys
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.conf import settings
from datetime import datetime
from dashboard.models import Unidad, Personal, Operador, ConfiguracionGeneral, ConfiguracionLogistica

class Command(BaseCommand):
    help = 'Carga los valores reales del negocio desde BUSINESS_VALUES.py'

    def handle(self, *args, **options):
        # 1. Importar el archivo BUSINESS_VALUES.py desde la raíz
        sys.path.append(str(settings.BASE_DIR))
        try:
            import BUSINESS_VALUES
        except ImportError:
            self.stdout.write(self.style.ERROR("No se encontró el archivo BUSINESS_VALUES.py en la raíz."))
            return

        conf_carga = BUSINESS_VALUES.CONFIG_CARGA
        
        # 2. Limpieza si se solicita
        if conf_carga.get('limpiar_base_datos'):
            self.stdout.write(self.style.WARNING("Limpiando base de datos..."))
            call_command('flush', '--no-input')

        # 3. Superuser por defecto
        User = get_user_model()
        if conf_carga.get('crear_superuser_por_defecto'):
             if not User.objects.filter(username='sergio').exists():
                 User.objects.create_superuser('sergio', 'sergio@casalupita.com', 'password123')
                 self.stdout.write(self.style.SUCCESS("Superusuario 'sergio' creado."))

        # 4. Carga de Catálogos CSV
        if conf_carga.get('cargar_catalogos_csv'):
            self.stdout.write(self.style.NOTICE("Cargando Catálogo de CP (México.csv)..."))
            call_command('load_cp_data')
            self.stdout.write(self.style.NOTICE("Cargando Catálogo de Clientes (Clientes.csv)..."))
            call_command('load_clientes_data')

        # 5. Carga de Unidades
        self.stdout.write(self.style.NOTICE("Cargando Unidades Reales..."))
        for u_data in BUSINESS_VALUES.UNIDADES:
            # Convertir fecha si existe
            venc_poliza = None
            if u_data.get('vigencia_poliza'):
                try:
                    venc_poliza = datetime.strptime(u_data['vigencia_poliza'], "%Y-%m-%d").date()
                except:
                    pass

            unidad, created = Unidad.objects.update_or_create(
                nUnidad=u_data['nUnidad'],
                defaults={
                    'nombre_corto': u_data.get('nombre_interno'),
                    'placas': u_data['placas'],
                    'marca': u_data['marca'],
                    'submarca': u_data['submarca'],
                    'modelo_anio': u_data['modelo'],
                    'tipo': u_data['tipo'],
                    'capacidad_kg': u_data['capacidad_kg'],
                    'capacidad_tanque': u_data.get('tanque_lts', 100),
                    'no_serie': u_data.get('serie'),
                    'no_motor': u_data.get('motor'),
                    'descripcion_vehiculo': u_data.get('descripcion', 'Sin descripción'),
                    'tarjeta_circulacion': u_data.get('tarjeta_circulacion'),
                    'tipo_combustible_unidad': u_data.get('combustible', 'GASOLINA'),
                    'numero_llantas': u_data.get('num_llantas', 6),
                    'poliza_seguro': u_data.get('poliza_seguro'),
                    'vencimiento_poliza': venc_poliza,
                    'titular_poliza': u_data.get('titular_poliza'),
                    'tipo_cobertura_seguro': u_data.get('cobertura_poliza'),
                }
            )
            verb = "Creada" if created else "Actualizada"
            self.stdout.write(f"  - {verb} Unidad: {unidad.nUnidad}")

        # 6. Carga de Equipo (Usuarios y Personal)
        self.stdout.write(self.style.NOTICE("Cargando Equipo Operativo..."))
        for p_data in BUSINESS_VALUES.EQUIPO:
            user, created = User.objects.get_or_create(
                username=p_data['username'],
                defaults={'email': f"{p_data['username']}@casalupita.com"}
            )
            if created:
                user.set_password('password123')
                user.save()
            
            # Procesar apellidos
            ap_p = p_data['apellidos'].split(' ')[0] if p_data['apellidos'] else ''
            ap_m = ' '.join(p_data['apellidos'].split(' ')[1:]) if ' ' in p_data['apellidos'] else ''

            # Personal
            personal, p_created = Personal.objects.update_or_create(
                usuario=user,
                defaults={
                    'puesto': p_data['puesto'],
                    'nombre': p_data['nombre'],
                    'apellido_paterno': ap_p,
                    'apellido_materno': ap_m
                }
            )
            
            # Si es CHOFER o tiene perfil de chofer, también necesita registro en Operador (Directorio)
            if p_data['puesto'] == 'CHOFER':
                 Operador.objects.update_or_create(
                     usuario_asociado=user,
                     defaults={
                         'nombre': f"{p_data['nombre']} {p_data['apellidos']}",
                         'puesto': 'CHOFER',
                         'telefono': '5500000000', # Placeholder real requerido
                         'activo': True
                     }
                 )

            verb_user = "Nuevo" if created else "Existente"
            self.stdout.write(f"  - Usuario {verb_user}: {user.username} ({p_data['puesto']})")

        # 7. Configuración General
        conf_neg = BUSINESS_VALUES.CONFIG_NEGOCIO
        cg = ConfiguracionGeneral.get_solo()
        cg.sueldo_semanal_chofer = conf_neg['sueldo_semanal_chofer']
        cg.sueldo_semanal_chalan = conf_neg['sueldo_semanal_chalan']
        cg.tiempo_descarga_promedio_min = conf_neg['tiempo_descarga_promedio_min']
        cg.limite_seguridad_llanta_mm = conf_neg['limite_mm_llanta_seguridad']
        cg.vida_util_estimada_llanta_km = conf_neg['vida_util_estimada_llanta_km']
        cg.save()
        
        # 8. Configuración Logística (Default)
        ConfiguracionLogistica.objects.get_or_create(pk=1)

        self.stdout.write(self.style.SUCCESS("\n¡Éxito! Carga maestra completada con valores reales."))
