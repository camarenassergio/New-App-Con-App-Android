from django.conf import settings
from django.db import models
# from django.contrib.auth.models import User  <-- REMOVED

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from datetime import date, timedelta
import datetime
import calendar
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from math import ceil

class Unidad(models.Model):
    TIPO_CHOICES = [
        ('CAMION', 'Camión (Ruta Pesada)'),
        ('CAMIONETA_3_5', 'Camioneta 3.5 Ton'),
        ('CAMIONETA_1_5', 'Camioneta 1.5 Ton'),
        ('AUTO', 'Auto / Sedán'),
        ('MOTO', 'Motocicleta (Express)'),
    ]

    # Identificadores
    nUnidad = models.CharField(max_length=20, unique=True, verbose_name="No. Unidad (U#)", editable=False)
    nombre_corto = models.CharField(max_length=50, verbose_name="Nombre Interno", null=True, blank=True, help_text="Identificador rápido para modales y listas (ej. 'Rojita')")
    placas = models.CharField(max_length=15, unique=True, verbose_name="Placas")
    
    # Descripción & Detalles
    descripcion_vehiculo = models.CharField(max_length=200, verbose_name="Descripción del Vehículo", help_text="Ej. Camión Freightliner Blanco 10 Ton", default="Sin descripción")
    no_serie = models.CharField(max_length=50, verbose_name="No. de Serie", unique=True, null=True, blank=True)
    no_motor = models.CharField(max_length=50, verbose_name="No. de Motor", null=True, blank=True)
    
    # --- CAMPOS NORMALIZADOS ---
    marca = models.CharField(max_length=50, verbose_name="Marca")
    submarca = models.CharField(max_length=50, verbose_name="Submarca")
    modelo_anio = models.PositiveIntegerField(verbose_name="Modelo (Año)")
    
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='CAMIONETA')
    capacidad_kg = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Capacidad (kg)")
    capacidad_tanque = models.PositiveIntegerField(default=100, verbose_name="Capacidad Tanque (Litros)")
    numero_llantas = models.PositiveIntegerField(choices=[(4, '4 Llantas'), (6, '6 Llantas')], default=6, verbose_name="Número de Llantas")
    
    COMBUSTIBLE_UNIDAD_CHOICES = [
        ('DIESEL', 'Diesel'),
        ('GASOLINA', 'Gasolina'),
    ]
    tipo_combustible_unidad = models.CharField(
        max_length=10, 
        choices=COMBUSTIBLE_UNIDAD_CHOICES, 
        default='GASOLINA',
        verbose_name="Tipo de Motor"
    )
    # Legal & Documentación
    tarjeta_circulacion = models.CharField(max_length=50, verbose_name="Tarjeta de Circulación", null=True, blank=True)
    vencimiento_placa = models.DateField(verbose_name="Vencimiento de Placa", null=True, blank=True)
    tipo_permiso_stc = models.CharField(max_length=100, verbose_name="Permiso STC", default="N/A", null=True, blank=True)
    
    # Seguro
    nombre_aseguradora = models.CharField(max_length=100, verbose_name="Aseguradora", null=True, blank=True)
    tipo_cobertura_seguro = models.CharField(max_length=100, verbose_name="Tipo de Cobertura", null=True, blank=True)
    poliza_seguro = models.CharField(max_length=50, verbose_name="Número de Póliza", null=True, blank=True)
    titular_poliza = models.CharField(max_length=150, verbose_name="Titular de la Póliza", null=True, blank=True)
    vencimiento_poliza = models.DateField(verbose_name="Vencimiento de Póliza", null=True, blank=True)

    # Expediente Construrama SDC (Documentación Digital)
    doc_factura = models.FileField(upload_to='unidades/docs/', null=True, blank=True, verbose_name="Copia Factura (PDF/IMG)")
    doc_tarjeta_circulacion = models.FileField(upload_to='unidades/docs/', null=True, blank=True, verbose_name="Tarjeta Circulación (PDF/IMG)")
    doc_poliza = models.FileField(upload_to='unidades/docs/', null=True, blank=True, verbose_name="Póliza Seguro (PDF/IMG)")
    doc_permisos = models.FileField(upload_to='unidades/docs/', null=True, blank=True, verbose_name="Permisos Federales/STC (PDF/IMG)")

    

    en_servicio = models.BooleanField(default=True , verbose_name="¿En servicio?")
    fecha_adquisicion = models.DateField(verbose_name="Fecha Adquisición", null=True, blank=True)

    kilometraje_actual = models.PositiveIntegerField(default=0, verbose_name="Km Actual")
    ultimo_pago_tenencia = models.DateField(verbose_name="Último pago Tenencia", null=True, blank=True)
    
    HOLOGRAMA_CHOICES = [('00', '00'), ('0', '0'), ('1', '1'), ('2', '2')]
    holograma = models.CharField(max_length=2, choices=HOLOGRAMA_CHOICES, default='00', editable=False)
    vencimiento_verificacion = models.DateField(null=True, blank=True)
    observaciones = models.TextField(verbose_name="Observaciones", null=True, blank=True)

    def __str__(self):
        return f"{self.nUnidad} - {self.marca} {self.submarca} ({self.modelo_anio})"

    def clean(self):
        super().clean()
        if self.vencimiento_poliza:
            if self.vencimiento_poliza < timezone.now().date():
                raise ValidationError({
                    'vencimiento_poliza': 'La fecha de vencimiento no puede ser anterior al día de hoy.'
                })

    @property
    def ultimo_digito(self):
        """Extrae el último dígito numérico de la placa"""
        import re
        numeros = re.findall(r'\d', self.placas)
        return int(numeros[-1]) if numeros else None

    @property
    def color_engomado(self):
        """Calcula el color según la tabla del Edomex"""
        digito = self.ultimo_digito
        if digito in [5, 6]: return "Amarillo"
        if digito in [7, 8]: return "Rosa"
        if digito in [3, 4]: return "Rojo"
        if digito in [1, 2]: return "Verde"
        if digito in [9, 0]: return "Azul"
        return "Desconocido"
    
    @property
    def color_engomado_hex(self):
        colores = {
            "Amarillo": "#f1c40f",
            "Rosa": "#e84393",
            "Rojo": "#e74c3c",
            "Verde": "#2ecc71",
            "Azul": "#3498db"
        }
        return colores.get(self.color_engomado, "#ccc")
        
    @property
    def dia_no_circula(self):
        """Calcula el día de restricción semanal"""
        color = self.color_engomado
        restricciones = {
            "Amarillo": "Lunes", "Rosa": "Martes", "Rojo": "Miércoles",
            "Verde": "Jueves", "Azul": "Viernes"
        }
        return restricciones.get(color, "N/A")

    def get_numero_sabado(self, fecha):
        """Calcula si es el 1er, 2do, 3er o 4to sábado del mes"""
        primer_dia = fecha.replace(day=1)
        ajuste = (primer_dia.weekday() + 1) % 7
        return ceil((fecha.day + ajuste) / 7)

    @property
    def alerta_circulacion(self):
        hoy = datetime.date.today()
        dia_semana = hoy.weekday() # 0=Lunes, 5=Sábado
        digito = self.ultimo_digito
        
        restricciones = {
            'Lunes': [5, 6], 'Martes': [7, 8], 'Miércoles': [3, 4],
            'Jueves': [1, 2], 'Viernes': [9, 0]
        }
        dias_nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        dia_actual = dias_nombres[dia_semana]
        
        # ¿Es su día de descanso habitual?
        es_dia_descanso = False
        if dia_semana < 5:
            es_dia_descanso = (digito in restricciones.get(dia_actual, []))

        # 1. REVISAR CONTINGENCIA (Botón Global)
        config = ConfiguracionLogistica.objects.first()
        if config and config.estado_contingencia in ['FASE_1', 'FASE_2']:
            
            # REGLA DE ORO FASE 1/2: NINGÚN holograma circula si cae en su día de color
            if es_dia_descanso:
                return f"🚨 NO CIRCULA (Doble Hoy No Circula: Aplica para {dia_actual})"
                
            # Si pasaron su filtro de color, revisamos reglas adicionales:
            
            # 0 y 00 se salvan si no fue su día
            if self.holograma in ['0', '00']:
                 return "✅ CIRCULA (Exento 0/00)"
            
            # Holograma 2: NUNCA circula en Contingencia
            if self.holograma == '2':
                return "🚨 NO CIRCULA (Contingencia Fase 1/2)"
                
            # Holograma 1: Depende de la Paridad dictada por SEDEMA
            if self.holograma == '1' and config.estado_contingencia == 'FASE_1':
                es_par = (digito % 2 == 0)
                if config.restringir_h1 == 'PAR' and es_par:
                    return "🚨 NO CIRCULA (Contingencia: Placas Pares)"
                if config.restringir_h1 == 'NON' and not es_par:
                    return "🚨 NO CIRCULA (Contingencia: Placas Nones)"
            
            # Fase 2 Extrema
            if self.holograma == '1' and config.estado_contingencia == 'FASE_2':
                return "🚨 NO CIRCULA (Contingencia Fase 2)"

        # 2. SIN CONTINGENCIA ACTIVA (O pasaron filtro en días de fin de semana)
        
        # Holograma 0 y 00 circulan diario normalmente
        if self.holograma in ['0', '00']:
            return "✅ CIRCULA (Exento)"

        # Resto (Holograma 1 y 2) en Semana Ordinaria
        if es_dia_descanso:
            return f"🚨 NO CIRCULA ({dia_actual})"

        # 3. RESTRICCIÓN SÁBADOS
        if dia_semana == 5:
            if self.holograma == '2':
                return "🚨 NO CIRCULA (Holograma 2 descansa todos los sábados)"
            
            if self.holograma == '1':
                num_sabado = self.get_numero_sabado(hoy)
                if digito % 2 != 0 and num_sabado in [1, 3, 5]:
                    return "🚨 NO CIRCULA (1er/3er Sábado - Placa Impar)"
                if digito % 2 == 0 and num_sabado in [2, 4]:
                    return "🚨 NO CIRCULA (2do/4to Sábado - Placa Par)"

        return "✅ CIRCULA"

    @property
    def alerta_verificacion(self):
        if not self.vencimiento_verificacion:
            return None
        today = date.today()
        if self.vencimiento_verificacion < today:
            return "VENCIDA"
        if self.vencimiento_verificacion <= today + timedelta(days=30):
            return "POR VENCER"
        return "OK"

    @property
    def alerta_tenencia(self):
        # Tenencia es anual, se asume que vence el 31 de marzo de cada año o 1 año después del último pago
        if not self.ultimo_pago_tenencia:
            return "PENDIENTE"
        
        today = date.today()
        # Logica simple: Si el año del ultimo pago es menor al actual, ya debe pagarse (ajustar según regla fiscal real)
        if self.ultimo_pago_tenencia.year < today.year:
             # Si estamos despues de marzo, ya venció
             if today.month > 3:
                 return "VENCIDA"
             else:
                 return "POR VENCER"
        return "OK"

    @property
    def alerta_placa(self):
        if not self.vencimiento_placa:
            return None
        today = date.today()
        if self.vencimiento_placa < today:
            return "VENCIDA"
        if self.vencimiento_placa <= today + timedelta(days=60): # 60 días antes
            return "POR VENCER"
        return "OK"

    @property
    def alerta_seguro(self):
        if not self.vencimiento_poliza:
            return None
        today = date.today()
        if self.vencimiento_poliza < today:
            return "VENCIDA"
        if self.vencimiento_poliza <= today + timedelta(days=30): # 30 días antes
            return "POR VENCER"
        return "OK"

    def save(self, *args, **kwargs):
        # Auto-generate nUnidad if it doesn't exist
        if not self.nUnidad:
            last = Unidad.objects.all().order_by('id').last()
            if not last:
                self.nUnidad = 'U1'
            else:
                # Try to extract the number from the last unit string
                try:
                    # Assuming format U1, U2...
                    last_id_str = last.nUnidad.replace('U', '')
                    new_id = int(last_id_str) + 1
                    self.nUnidad = f'U{new_id}'
                except ValueError:
                    # Fallback if format is broken
                    self.nUnidad = f'U{last.id + 1}'

        # Lógica de cálculo del holograma (Regla 2026)
        anio_actual = date.today().year
        
        if self.modelo_anio >= (anio_actual - 2):
            self.holograma = "00"
        elif self.modelo_anio >= 2006:
            self.holograma = "0"
        else:
            self.holograma = "2"
            
        super().save(*args, **kwargs)

    @property
    def costo_combustible_por_km(self):
        """Calcula el costo por km en base al último precio de carga y el rendimiento histórico"""
        from decimal import Decimal
        
        ultimo_registro = self.registrocombustible_set.order_by('-fecha', '-id').first() # Changed from registros_combustible to registrocombustible_set
        precio_litro = ultimo_registro.precio_litro if ultimo_registro else Decimal('23.50') # default diesel
        
        # Para unidades particulares (personal), usar estimación
        if self.tipo in ['AUTO', 'MOTO']:
            rendimientos_fijos = {
                'AUTO': Decimal('9.0'),
                'MOTO': Decimal('16.0')
            }
            return precio_litro / rendimientos_fijos[self.tipo]
        
        # Calcular rendimiento real
        registros = self.registrocombustible_set.order_by('fecha', 'id') # Changed from registros_combustible to registrocombustible_set
        if registros.count() > 1:
            km_inicial = registros.first().kilometraje_actual
            km_final = registros.last().kilometraje_actual
            litros_totales = sum([r.litros for r in registros])
            if litros_totales > 0 and km_final > km_inicial:
                rendimiento = Decimal(km_final - km_inicial) / litros_totales
            else:
                rendimiento = Decimal('4.0') # Rendimiento promedio Camión
        else:
            # Rendimientos por default basados en el tipo de unidad
            rendimientos_default = {
                'CAMIONETA': Decimal('6.5'),
                'CAMION': Decimal('4.0')
            }
            rendimiento = rendimientos_default.get(self.tipo, Decimal('4.0'))
            
        return precio_litro / rendimiento

    @property
    def costo_mantenimiento_por_km(self):
        """Costo de mtto dividido entre kilometraje histórico en la plataforma"""
        from django.db.models import Sum
        from decimal import Decimal
        
        # Para unidades particulares (personal), usar estimación: Auto: 1500 / 10000 = 0.15, Moto: 1000 / 4000 = 0.25
        if self.tipo in ['AUTO', 'MOTO']:
            default_mto_km = {
                'AUTO': Decimal('0.15'),
                'MOTO': Decimal('0.25')
            }
            return default_mto_km[self.tipo]
        
        gastos = self.gastos_generales.filter(tipo='Mantenimiento').aggregate(Sum('costo'))['costo__sum']
        total_mantenimiento = gastos if gastos else Decimal('0.00')
        
        km_actual = self.kilometraje_actual
        if km_actual > 1000:
            return total_mantenimiento / Decimal(km_actual)
        
        default_mto_km = {
            'CAMION': Decimal('2.00'),
            'CAMIONETA': Decimal('1.20'),
        }
        return default_mto_km.get(self.tipo, Decimal('1.00'))
        
    @property
    def costo_llantas_por_km(self):
        """Csuma precio llantas activas / vida útil estimada"""
        from decimal import Decimal
        
        # Para unidades particulares (personal)
        if self.tipo in ['AUTO', 'MOTO']:
            default_llanta_km = {
                'AUTO': Decimal('0.12'), # 6000 / 50000 km
                'MOTO': Decimal('0.08')  # 1600 / 20000 km
            }
            return default_llanta_km[self.tipo]
        
        config = ConfiguracionGeneral.get_solo()
        vida_util_km = Decimal(config.vida_util_estimada_llanta_km) if config.vida_util_estimada_llanta_km else Decimal('100000')
        
        llantas_activas = self.llantas.filter(activa=True)
        if not llantas_activas.exists():
            default_precio_llanta = {
                'CAMION': Decimal('5500.00') * Decimal(self.numero_llantas or 6),
                'CAMIONETA': Decimal('2500.00') * Decimal(self.numero_llantas or 4),
            }
            costo_total = default_precio_llanta.get(self.tipo, Decimal('1000.00'))
        else:
            costo_total = sum([ll.costo for ll in llantas_activas if ll.costo])
            
        return Decimal(costo_total) / vida_util_km

    @property
    def costo_operativo_total_por_km(self):
        """Suma Mantenimiento + Combustible + Llantas por KM recorrido"""
        return self.costo_combustible_por_km + self.costo_mantenimiento_por_km + self.costo_llantas_por_km

    class Meta:
        verbose_name = "Unidad"
        verbose_name_plural = "Unidades"
class ZonaEntrega(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la Zona (Ej. Norte, Sur, Centro)")
    codigos_postales = models.TextField(verbose_name="Códigos Postales", help_text="Separados por coma", null=True, blank=True)
    colonias = models.TextField(verbose_name="Colonias que Abarca", help_text="Listado de colonias principales", null=True, blank=True)
    municipio = models.CharField(max_length=100, verbose_name="Municipio", null=True, blank=True)
    tiempo_traslado_minutos = models.PositiveIntegerField(verbose_name="Tiempo Medio Traslado (mins)")
    distancia_km = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Distancia Media (Km) desde Sucursal")
    tarifa_flete = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Costo Base de Flete ($)", default=0.00)
    costo_maniobra = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Costo Maniobra Adicional ($)", default=0.00)
    color_hex = models.CharField(max_length=7, default="#3388ff", verbose_name="Color en Mapa", help_text="Color para identificar la zona en el mapa")
    geojson_data = models.TextField(blank=True, null=True, verbose_name="Polígonos de la Zona (GeoJSON)", help_text="Información geográfica de la zona")
    route_geojson = models.TextField(blank=True, null=True, verbose_name="Ruta Oficial (GeoJSON)")
    route_waypoints = models.TextField(blank=True, null=True, verbose_name="Waypoints de la Ruta (JSON)")

    class Meta:
        verbose_name = "Zona de Entrega"
        verbose_name_plural = "Zonas de Entrega"

    @property
    def text_color(self):
        """Calcula si el texto debe ser blanco o negro para mejor contraste con color_hex"""
        if not self.color_hex or not self.color_hex.startswith('#'):
            return "#ffffff"
        
        color = self.color_hex.lstrip('#')
        if len(color) != 6:
            return "#ffffff"
            
        try:
            r = int(color[0:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:6], 16)
            # Algoritmo de luminancia (YIQ)
            luminance = (r * 299 + g * 587 + b * 114) / 1000
            return "#000000" if luminance > 125 else "#ffffff"
        except ValueError:
            return "#ffffff"

    def limpiar_codigos(self):
        """Limpia la cadena de CP, eliminando espacios y duplicados vacíos"""
        if not self.codigos_postales: return []
        cps = [cp.strip() for cp in self.codigos_postales.split(',') if cp.strip()]
        return list(set(cps)) # Asegurar únicos de origen

    def save(self, *args, **kwargs):
        import json
        import os
        from django.conf import settings
        
        cps_limpios = self.limpiar_codigos()
        
        # Opcional: Desvincular CPs que ya existan en OTRAS zonas
        if cps_limpios:
            otras_zonas = ZonaEntrega.objects.exclude(id=self.id)
            for zona in otras_zonas:
                cps_ajena = zona.limpiar_codigos()
                cambio = False
                for cp in cps_limpios:
                    if cp in cps_ajena:
                        cps_ajena.remove(cp)
                        cambio = True
                if cambio:
                    zona.codigos_postales = ", ".join(cps_ajena)
                    # Use update to avoid calling save to prevent recursive loop
                    ZonaEntrega.objects.filter(id=zona.id).update(codigos_postales=zona.codigos_postales)

        self.codigos_postales = ", ".join(cps_limpios)
        
        # Auto-calculate geojson from CPs
        if cps_limpios:
            try:
                # Get path to the local data 
                data_path = os.path.join(settings.BASE_DIR, 'dashboard', 'data', 'zonas_texcoco.json')
                
                if not os.path.exists(data_path):
                    print(f"CRITICAL: GeoJSON source file not found at {data_path}")
                
                features = []
                # Pre-clean search CPs to ensure exact matching with strings in JSON
                search_cps = [str(cp).strip().zfill(5) for cp in cps_limpios]
                
                detect_municipio = None
                
                with open(data_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line: continue
                        try:
                            feature = json.loads(line)
                            # The json property is "d_cp" based on the uploaded file
                            # It might be in properties or directly in the feature
                            props = feature.get('properties', {})
                            cp_value = str(props.get('d_cp', '')).strip().zfill(5)
                            
                            if cp_value in search_cps:
                                features.append(feature)
                                # Try to detect municipio if not already detected
                                if not detect_municipio:
                                    detect_municipio = props.get('D_mnpio') or props.get('municipio')
                        except json.JSONDecodeError:
                            continue
                
                # Update municipio if detected and NOT already set manually
                if detect_municipio and not self.municipio:
                    self.municipio = detect_municipio
                    print(f"Detected municipio for {self.nombre}: {detect_municipio}")
                            
                if features:
                    print(f"Found {len(features)} polygons for zone {self.nombre} (CPs: {search_cps})")
                    # Dissolve geometries to remove internal lines
                    try:
                        from shapely.geometry import shape, mapping
                        from shapely.ops import unary_union
                        
                        # buffer(0) fixes minor topology errors before union
                        polygons = [shape(f['geometry']).buffer(0) for f in features]
                        unified_geom = unary_union(polygons)
                        
                        # Package as a single feature with the unioned geometry
                        geo_collection = {
                            "type": "FeatureCollection",
                            "features": [{
                                "type": "Feature",
                                "geometry": mapping(unified_geom),
                                "properties": {"nombre": self.nombre, "municipio": self.municipio}
                            }]
                        }
                        self.geojson_data = json.dumps(geo_collection)
                    except Exception as geo_err:
                        # Fallback to multiple features if union fails or shapely missing
                        print(f"Geo-union fallback for {self.nombre}: {geo_err}")
                        self.geojson_data = json.dumps({
                            "type": "FeatureCollection",
                            "features": features
                        })
                else:
                     print(f"WARNING: No polygons matched CPs {search_cps} for zone {self.nombre}")
                     # Do not overwrite if we already have data, but if it was a new save and failed, leave empty
                     if not self.geojson_data:
                         self.geojson_data = "" 
                     
            except Exception as e:
                print(f"Error loading GeoJSON for zone {self.nombre}: {e}")
                
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Zona: {self.nombre} ({self.tiempo_traslado_minutos} min)"

class Operador(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre Completo")
    puesto = models.CharField(max_length=100, default="Operador", verbose_name="Puesto / Departamento")
    telefono = models.CharField(max_length=15, verbose_name="Teléfono")
    email = models.EmailField(null=True, blank=True, verbose_name="Correo Electrónico")
    
    # Datos de Licencia (Opcionales para personal administrativo)
    licencia = models.CharField(max_length=50, null=True, blank=True, verbose_name="No. de Licencia")
    vigencia_licencia = models.DateField(null=True, blank=True, verbose_name="Vigencia de Licencia")
    
    # Vinculación con el sistema
    usuario_asociado = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='perfil_directorio')
    usa_sistema = models.BooleanField(default=False, verbose_name="¿Usa el sistema operativo regularmente?")
    
    activo = models.BooleanField(default=True, verbose_name="¿Está activo?")

    def __str__(self): 
        return f"{self.nombre} - {self.puesto}"
    @property
    def licencia_vencida(self):
        return self.vigencia_licencia and self.vigencia_licencia < timezone.now().date()
    @property
    def licencia_por_vencer(self):
        if not self.vigencia_licencia: return False
        days = (self.vigencia_licencia - timezone.now().date()).days
        return 0 <= days <= 30
    class Meta:
        verbose_name = "Operador"
        verbose_name_plural = "Operadores"
class Obra(models.Model):
    alias = models.CharField(max_length=100, verbose_name="Alias de la Obra (Ej. Casa Blanca)")
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE, related_name='obras')
    zona = models.ForeignKey(ZonaEntrega, on_delete=models.PROTECT, verbose_name="Zona de Entrega")
    
    # Dirección Detallada
    calle_numero = models.CharField(max_length=255, verbose_name="Calle y Número Ext/Int")
    entre_calles = models.CharField(max_length=255, blank=True, null=True, verbose_name="Entre Calles")
    colonia = models.CharField(max_length=150, blank=True, null=True, verbose_name="Colonia")
    municipio = models.CharField(max_length=150, blank=True, null=True, verbose_name="Municipio")
    cp = models.CharField(max_length=10, blank=True, null=True, verbose_name="Código Postal")
    referencias = models.TextField(blank=True, null=True, verbose_name="Referencias Visuales (Color de fachada, portón, etc.)")
    
    # Receptor (Contacto Secundario)
    nombre_receptor = models.CharField(max_length=150, verbose_name="Nombre de quien recibe (Residente/Maestro/Cliente)")
    telefono_receptor = models.CharField(max_length=15, verbose_name="Teléfono del Receptor")
    
    # Reglas de Negocio
    esta_activa = models.BooleanField(default=True, verbose_name="Obra Activa")
    zona_aprobada = models.BooleanField(default=True, verbose_name="¿Zona autorizada por Logística?", help_text="Si se desmarca, el pedido quedará bloqueado hasta revisión.")
    fecha_ultimo_pedido = models.DateTimeField(null=True, blank=True, verbose_name="Fecha del último pedido")
    
    class Meta:
        verbose_name = "Obra / Dirección de Entrega"
        verbose_name_plural = "Obras / Directorio de Obras"
        ordering = ['-fecha_ultimo_pedido', 'alias']

    def __str__(self):
        return f"{self.alias} - {self.cliente.razon_social}"

    @property
    def es_reciente(self):
        """Regla de los 12 meses (365 días)"""
        if not self.fecha_ultimo_pedido:
            # Si nunca ha tenido pedidos, se considera inactiva tras 1 año de creación si no tiene pedidos
            return self.esta_activa 
        limite = timezone.now() - timedelta(days=365)
        return self.esta_activa and self.fecha_ultimo_pedido >= limite
    
class Cliente(models.Model):
    id_sae = models.CharField(max_length=20, unique=True, verbose_name="ID SAE (ERP)", null=True, blank=True)
    razon_social = models.CharField(max_length=255, verbose_name="Razón Social / Nombre Completo")
    telefono_principal = models.CharField(max_length=15, verbose_name="Teléfono Principal", null=True, blank=True)
    es_mostrador = models.BooleanField(default=False, verbose_name="¿Es Cliente Mostrador?")
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return f"{self.id_sae or 'S/C'} - {self.razon_social}"

    def save(self, *args, **kwargs):
        # Si no tiene ID SAE, se marca automáticamente como cliente mostrador
        if not self.id_sae:
            self.es_mostrador = True
        else:
            self.es_mostrador = False
        super().save(*args, **kwargs)

class Pedido(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente / Registrado'),
        ('CREADO', 'Pedido Creado / Ingestado'),
        ('DESPACHOS_GENERADOS', 'Despachos Generados'),
        ('EN_PROCESO', 'En Proceso (Múltiples Despachos)'),
        ('PARCIAL', 'Entregado Parcial (Queda Saldo)'),
        ('ENTREGADO', 'Entregado Totalmente'),
        ('CERRADO', 'Cerrado Administrativamente'),
    ]

    METODO_PAGO_CHOICES = [
        ('EFECTIVO', 'Efectivo'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('TARJETA', 'Tarjeta (Débito/Crédito)'),
        ('POR_COBRAR', 'Por Cobrar (Contra entrega)'),
        ('CREDITO', 'Crédito SAE'),
    ]

    folio_sae = models.CharField(max_length=50, unique=True, verbose_name="Folio SAE / Ticket")
    
    # Relación con Cliente (Opcional si es Cliente Mostrador genérico)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='pedidos', null=True, blank=True)
    obra = models.ForeignKey(Obra, on_delete=models.PROTECT, related_name='pedidos', null=True, blank=True, help_text="Opcional para entregas rápidas en mostrador")
    
    # Captura Manual (Para cuando NO hay ID SAE o es cliente nuevo/rápido)
    cliente_nombre_manual = models.CharField(max_length=255, null=True, blank=True, verbose_name="Nombre Cliente (Manual)")
    cliente_telefono_manual = models.CharField(max_length=15, null=True, blank=True, verbose_name="Teléfono Cliente (Manual)")
    cliente_direccion_manual = models.TextField(null=True, blank=True, verbose_name="Dirección de Entrega (Manual)")
    
    peso_total_estimado_kg = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Peso Total (kg)", default=0)
    articulos_totales = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Artículos Totales (pzas/m/etc)", default=0)
    evidencia_ticket = models.FileField(upload_to='pedidos/tickets/', null=True, blank=True, verbose_name="Evidencia Ticket (PDF/IMG)")
    
    estado = models.CharField(max_length=30, choices=ESTADO_CHOICES, default='PENDIENTE')
    
    es_urgente = models.BooleanField(default=False, verbose_name="¿Es Urgente / Flete Pagado?")
    maniobra_aceptada = models.BooleanField(default=False, verbose_name="Maniobra a pie de camión aceptada")
    
    # Finanzas y Observaciones
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, default='EFECTIVO', verbose_name="Forma de Pago")
    observaciones_mostrador = models.TextField(null=True, blank=True, verbose_name="Observaciones General / Campo Extra")
    
    # Metadatos de control
    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='pedidos_registrados')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-fecha_registro']

    @property
    def saldo_articulos(self):
        from decimal import Decimal
        if not self.articulos_totales: return Decimal('0.00')
        # Despachos en CANCELADO devuelven su saldo. Usa getattr previendo si aun no existen los campos en la migración de Despacho
        despachos = self.despachos.exclude(estado='CANCELADO')
        asignado = sum((getattr(d, 'cantidad_articulos_asignados', Decimal('0')) or Decimal('0')) - (getattr(d, 'cantidad_articulos_rechazados', Decimal('0')) or Decimal('0')) for d in despachos)
        return max(Decimal('0.00'), self.articulos_totales - asignado)

    @property
    def saldo_peso_kg(self):
        from decimal import Decimal
        if not self.peso_total_estimado_kg: return Decimal('0.00')
        despachos = self.despachos.exclude(estado='CANCELADO')
        
        asignado_kg = Decimal('0')
        for d in despachos:
            peso = getattr(d, 'peso_asignado_kg', Decimal('0')) or Decimal('0')
            art_asign = getattr(d, 'cantidad_articulos_asignados', Decimal('0')) or Decimal('0')
            art_rechazo = getattr(d, 'cantidad_articulos_rechazados', Decimal('0')) or Decimal('0')
            
            # Si hay rechazo parcial, devolver proporcionalmente el peso al saldo para no perder capacidad viva
            if art_asign > 0 and art_rechazo > 0:
                proporcion_valida = (art_asign - art_rechazo) / art_asign
                peso = peso * proporcion_valida
                
            asignado_kg += peso
            
        return max(Decimal('0.00'), self.peso_total_estimado_kg - asignado_kg)

    def __str__(self):
        cliente_nombre = self.cliente.razon_social if self.cliente else self.cliente_nombre_manual
        return f"{self.folio_sae} - {cliente_nombre}"

    def save(self, *args, **kwargs):
        # Actualizar fecha de último pedido en la obra vinculada si existe
        if self.obra:
            # Usar update para evitar disparar señales de save() de Obra innecesariamente si se prefiere,
            # pero aquí el diseño original pide actualizar la fecha.
            self.obra.fecha_ultimo_pedido = timezone.now()
            self.obra.save()
        super().save(*args, **kwargs)

class Despacho(models.Model):
    TIPO_CHOICES = [
        ('INTERNO_FLOTILLA', 'Ruta A: Unidad Flotilla'),
        ('INTERNO_PERSONAL', 'Ruta B: Vehículo Personal'),
        ('PROVEEDOR_EXTERNO', 'Ruta C: Proveedor Externo'),
    ]
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente de Surtido'),
        ('ASIGNADO_SURTIDO', 'Surtido en Proceso'),
        ('SURTIDO_COMPLETO', 'Surtido Físico Completo'),
        ('LISTO_PARA_RUTA', 'Listo para Ruta'),
        ('EN_RUTA', 'En Ruta de Entrega'),
        ('CONFIRMADO', 'Entregado / Confirmado'),
        ('RECHAZO_PARCIAL', 'Entregado Parcialmente'),
        ('CANCELADO', 'Cancelado / Rechazo Total'),
    ]

    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='despachos')
    viaje = models.ForeignKey('ViajeNuevo', on_delete=models.SET_NULL, null=True, blank=True, related_name='despachos')
    
    tipo_envio = models.CharField(max_length=20, choices=TIPO_CHOICES, default='INTERNO_FLOTILLA')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    
    peso_asignado_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Peso Asignado (kg)")
    cantidad_articulos_asignados = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Artículos Asignados")
    cantidad_articulos_rechazados = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Artículos Rechazados")
    
    # Datos de entrega (App Chofer)
    hora_llegada = models.DateTimeField(null=True, blank=True)
    hora_entrega = models.DateTimeField(null=True, blank=True)
    
    maniobra_especial = models.BooleanField(default=False, verbose_name="¿Se realizó maniobra especial?")
    descripcion_maniobra = models.TextField(blank=True, null=True, verbose_name="Detalle de maniobra/propina")
    observaciones_entrega = models.TextField(blank=True, null=True, verbose_name="Observaciones del chofer")
    
    # Evidencia obligatoria única
    foto_ticket_firmado = models.ImageField(upload_to='entregas/tickets/', null=True, blank=True, verbose_name="Foto Ticket Firmado")

    def __str__(self):
        return f"Despacho {self.id} - {self.pedido.folio_sae}"

class EvidenciaMaterial(models.Model):
    despacho = models.ForeignKey(Despacho, on_delete=models.CASCADE, related_name='evidencias_material')
    foto = models.ImageField(upload_to='entregas/material/', verbose_name="Foto Material en Sitio")
    fecha_registro = models.DateTimeField(auto_now_add=True)

class ViajeNuevo(models.Model):
    ESTADO_VIAJE_CHOICES = [
        ('CREADO', 'Creado / Programado'),
        ('EN_CURSO', 'En Curso / Salida'),
        ('REPROGRAMADO', 'Reprogramado (Vencido)'),
        ('FINALIZADO', 'Finalizado'),
    ]

    # Sustituirá al Viaje anterior conforme migremos
    unidad = models.ForeignKey(Unidad, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Unidad Flotilla")
    vehiculo_personal_info = models.CharField(max_length=150, null=True, blank=True, verbose_name="Info Vehículo Personal (Motos/Particular)")
    
    chofer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='viajes_asignados')
    chalan = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='viajes_ayuda', verbose_name="Chalán")
    usuario_creacion = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='viajes_creados', verbose_name="Creado por")

    
    proveedor_externo = models.CharField(max_length=150, null=True, blank=True, verbose_name="Proveedor Externo (Ej. Sergio Almacen)")
    
    def get_local_date():
        return timezone.localtime(timezone.now()).date()

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_viaje = models.DateField(default=get_local_date, verbose_name="Fecha Programada")
    
    estado = models.CharField(max_length=20, choices=ESTADO_VIAJE_CHOICES, default='CREADO')
    completado = models.BooleanField(default=False)
    
    hora_salida = models.TimeField(null=True, blank=True, verbose_name="Hora Salida")
    hora_llegada = models.TimeField(null=True, blank=True, verbose_name="Hora Llegada")

    def save(self, *args, **kwargs):
        # Sincronizar completado con FINALIZADO
        if self.estado == 'FINALIZADO':
            self.completado = True
        elif self.completado:
            self.estado = 'FINALIZADO'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Viaje {self.id} ({self.estado}) - {self.fecha_viaje}"

class AlertaLogistica(models.Model):
    TIPO_ALERTA_CHOICES = [
        ('RECHAZO_PARCIAL', 'Rechazo Parcial en Sitio'),
        ('RECHAZO_TOTAL', 'Rechazo Total en Sitio'),
        ('DIRECCION_INCORRECTA', 'Dirección Incorrecta / No Localizada'),
        ('AUSENCIA_CLIENTE', 'Cliente Ausente / Local Cerrado'),
        ('OTRO', 'Incidencia General'),
    ]

    despacho = models.ForeignKey(Despacho, on_delete=models.CASCADE, related_name='alertas')
    chofer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='alertas_levantadas')
    
    tipo_alerta = models.CharField(max_length=25, choices=TIPO_ALERTA_CHOICES)
    comentarios = models.TextField(verbose_name="Descripción de la incidencia")
    resuelta = models.BooleanField(default=False, verbose_name="¿Alerta Gestionada?")
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Alerta {self.get_tipo_alerta_display()} - Despacho {self.despacho.id}"

class MensajeInterno(models.Model):
    remitente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mensajes_enviados')
    destinatario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='mensajes_recibidos', help_text="Nulo para avisos globales")
    
    contenido = models.TextField()
    leido = models.BooleanField(default=False)
    fecha_envio = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_envio']

    def __str__(self):
        return f"De: {self.remitente} - {self.fecha_envio.strftime('%d/%m %H:%M')}"

class Notificacion(models.Model):
    TIPOS = [
        ('SISTEMA', 'Sistema'),
        ('PEDIDO', 'Pedido'),
        ('MANTENIMIENTO', 'Mantenimiento'),
        ('ALERTA', 'Alerta / Urgente'),
    ]
    ICONOS = {
        'SISTEMA': 'fas fa-cog',
        'PEDIDO': 'fas fa-shopping-cart',
        'MANTENIMIENTO': 'fas fa-tools',
        'ALERTA': 'fas fa-exclamation-triangle',
    }
    
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notificaciones')
    tipo = models.CharField(max_length=20, choices=TIPOS, default='SISTEMA')
    titulo = models.CharField(max_length=150)
    descripcion = models.TextField()
    link = models.CharField(max_length=255, null=True, blank=True)
    leido = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ['-fecha_creacion']

    @property
    def icono(self):
        return self.ICONOS.get(self.tipo, 'fas fa-bell')

    def __str__(self):
        return f"{self.usuario.username} - {self.titulo} ({self.tipo})"



class CodigoPostalCat(models.Model):
    codigo = models.CharField(max_length=10, db_index=True, verbose_name="Código Postal")
    asentamiento = models.CharField(max_length=200, verbose_name="Colonia/Asentamiento")
    tipo_asentamiento = models.CharField(max_length=100, null=True, blank=True)
    municipio = models.CharField(max_length=100)
    estado = models.CharField(max_length=100)
    ciudad = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        verbose_name = "Código Postal"
        verbose_name_plural = "Códigos Postales"
        ordering = ['codigo', 'asentamiento']

    def __str__(self):
        return f"{self.codigo} - {self.asentamiento}"


class Viaje(models.Model):
    TIPO_VIAJE_CHOICES = [
        ('VENTA', 'Venta Normal'),
        ('TALLER', 'Taller / Mantenimiento'),
        ('COMBUSTIBLE', 'Cargar Combustible'),
        ('RECOLECCION', 'Recoger Mercancía'),
    ]
    ESTADO_CHOICES = [
        ('ESPERA', 'En Espera (Programado)'),
        ('TRANSITO', 'En Tránsito (Validado)'),
        ('FINALIZADO', 'Finalizado (Llegada a CMA)'),
    ]

    n_viaje = models.PositiveIntegerField(verbose_name="No. de Viaje", editable=False)
    fecha = models.DateField(auto_now_add=True)
    unidad = models.ForeignKey(Unidad, on_delete=models.PROTECT)
    operador = models.ForeignKey(Operador, on_delete=models.PROTECT)
    tipo_viaje = models.CharField(max_length=20, choices=TIPO_VIAJE_CHOICES, default='VENTA')
    estado_actual = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='ESPERA')
    
    # SDC: Zonas y Logística
    zona = models.ForeignKey(ZonaEntrega, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Zona de Entrega Principal")
    folio_nota_factura = models.CharField(max_length=100, null=True, blank=True, verbose_name="Folios (Facturas/Notas)")
    
    hora_salida_cedis = models.TimeField(null=True, blank=True, verbose_name="Salida CMA")
    hora_llegada_cedis = models.TimeField(null=True, blank=True, verbose_name="Regreso CMA")
    
    # SDC: Tracking de Kilometraje en el viaje
    km_salida = models.PositiveIntegerField(null=True, blank=True, verbose_name="Km Salida")
    km_llegada = models.PositiveIntegerField(null=True, blank=True, verbose_name="Km Llegada")
    
    mercancia_revisada = models.BooleanField(default=False, verbose_name="¿Mercancía Revisada?")
    revisado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, 
        related_name='validaciones', verbose_name="Validado por"
    )

    class Meta:
        permissions = [
            ("can_validate_merchandise", "Puede validar salida de mercancía"),
        ]

    def save(self, *args, **kwargs):
        if self.mercancia_revisada and self.estado_actual == 'ESPERA':
            self.estado_actual = 'TRANSITO'
        if not self.n_viaje:
             # Basic logical auto-increment per day or global - defaulting to global for now
             last = Viaje.objects.all().order_by('n_viaje').last()
             self.n_viaje = last.n_viaje + 1 if last else 1
        super().save(*args, **kwargs)

    def clean(self):
        viajes_activos = Viaje.objects.filter(
         operador=self.operador, 
         estado_actual='TRANSITO'
        ).exclude(id=self.id)
    
        if viajes_activos.exists():
            raise ValidationError(f"El operador {self.operador} ya tiene un viaje en curso.")

    @property
    def tiene_evaluacion(self):
        return hasattr(self, 'evaluacion')

    def __str__(self):
        return f"Viaje {self.n_viaje} - {self.unidad} ({self.fecha})"

class EvaluacionEntrega(models.Model):
    MOTIVO_CHOICES = [
        ('OK', 'Entregado sin problemas'),
        ('MERCANCIA_DANADA', 'Mercancía Dañada / Faltante'),
        ('TIEMPO_ALTO', 'Tardanza en entrega'),
        ('MALA_ATENCION', 'Mala atención del personal'),
        ('CLIENTE_AUSENTE', 'Cliente no se encontraba / Local cerrado'),
        ('OTRO', 'Otro (Especificar en observaciones)'),
    ]

    viaje = models.OneToOneField(Viaje, on_delete=models.CASCADE, related_name="evaluacion", verbose_name="Viaje Asociado")
    fecha_evaluacion = models.DateTimeField(auto_now_add=True)
    
    # 3.3.2.1 Encuesta y Requerimientos de Calidad
    cliente_satisfecho = models.BooleanField(default=True, verbose_name="¿Cliente Satisfecho con la Entrega?")
    motivo_insatisfaccion = models.CharField(max_length=50, choices=MOTIVO_CHOICES, default='OK', verbose_name="Motivo Principal (Si aplica)")
    
    # 3.3.2.2 Tiempo de Espera (Eficiencia)
    tiempo_espera_cliente_minutos = models.PositiveIntegerField(default=0, verbose_name="Tiempo de descarga/espera con cliente (minutos)")
    
    # 3.3.2.3 Registro de Errores Operativos e Incidencias en Transporte
    hubo_incidencia_transporte = models.BooleanField(default=False, verbose_name="¿Hubo incidente de transporte?")
    desc_incidencia_transporte = models.TextField(blank=True, null=True, verbose_name="Describa falla mecánica o imprevisto en ruta")
    
    # Firma / Validacion (Se sustituye con nombre de quien recibe por el momento)
    nombre_quien_recibe = models.CharField(max_length=150, blank=True, null=True, verbose_name="Nombre de quien recibe la mercancía")
    comentarios = models.TextField(blank=True, null=True, verbose_name="Comentarios adicionales / Detalle del problema")

    class Meta:
        verbose_name = "Evaluación de Entrega"
        verbose_name_plural = "Evaluaciones de Entregas"

    def __str__(self):
        return f"Evaluación Viaje #{self.viaje.n_viaje} - {'OK' if self.cliente_satisfecho else 'INCIDENCIA'}"

class PedidoRuta(models.Model):
    TIPO_PAGO_CHOICES = [('PAGADO', 'Pagado'), ('POR_COBRAR', 'Por Cobrar')]
    ESTATUS_CHOICES = [('PENDIENTE', 'Pendiente'), ('ENTREGADO', 'Entregado'), ('CANCELADO', 'Cancelado')]

    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE, related_name='pedidos')
    documento_aspel = models.CharField(max_length=50, verbose_name="Nota/Factura/Cotización")
    cliente_nombre = models.CharField(max_length=200, verbose_name="Cliente")
    zona = models.IntegerField(verbose_name="Zona")
    importe = models.DecimalField(max_digits=12, decimal_places=2)
    tipo_pago = models.CharField(max_length=20, choices=TIPO_PAGO_CHOICES)
    peso_kg = models.IntegerField(default=0)
    
    hora_llegada_cliente = models.TimeField(null=True, blank=True)
    hora_salida_cliente = models.TimeField(null=True, blank=True)
    estatus = models.CharField(max_length=20, choices=ESTATUS_CHOICES, default='PENDIENTE')
    comentarios = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.documento_aspel} - {self.cliente_nombre}"

class Personal(models.Model):
    PUESTO_CHOICES = [
        ('MOSTRADOR', 'Mostrador'),
        ('ALMACEN', 'Almacén'),
        ('RUTAS', 'Rutas / Logística'),
        ('ADMIN', 'Administrador'),
        ('CHOFER', 'Chofer'),
    ]
    
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    puesto = models.CharField(max_length=20, choices=PUESTO_CHOICES)
    roles_secundarios = models.CharField(max_length=255, blank=True, null=True, help_text="Separados por coma (Ej. MOSTRADOR,CAJA,LOGISTICA)")
    
    
    nombre = models.CharField(max_length=100, verbose_name="Nombre(s)")
    apellido_paterno = models.CharField(max_length=100, verbose_name="Apellido Paterno")
    apellido_materno = models.CharField(max_length=100, verbose_name="Apellido Materno", null=True, blank=True)
    foto = models.ImageField(upload_to='perfiles/', null=True, blank=True, verbose_name="Foto de Perfil")

    def __str__(self):
        return f"{self.nombre} {self.apellido_paterno} ({self.puesto})"
    class Meta:
        verbose_name = "Personal"
        verbose_name_plural = "Personal" 

class ServicioMantenimiento(models.Model):
    unidad = models.ForeignKey(Unidad, on_delete=models.CASCADE, related_name='servicios')
    tipo_servicio = models.CharField(max_length=100, verbose_name="Tipo de Servicio (ej. Preventivo)")
    fecha_realizado = models.DateField(auto_now_add=True)
    km_en_servicio = models.PositiveIntegerField(verbose_name="Kilometraje en ese momento")
    
    proximo_km = models.PositiveIntegerField(verbose_name="Próximo servicio (Kilómetros)")
    proxima_fecha = models.DateField(verbose_name="Próximo servicio (Fecha)")
    completado = models.BooleanField(default=False)

    def dias_restantes(self):
        return (self.proxima_fecha - date.today()).days

class RegistroCombustible(models.Model):
    unidad = models.ForeignKey(Unidad, on_delete=models.CASCADE)
    fecha = models.DateField()
    chofer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    kilometraje_actual = models.PositiveIntegerField()
    litros = models.DecimalField(max_digits=7, decimal_places=2, verbose_name="Litros")
    precio_litro = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Precio por Litro")
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total ($)")
    
    TIPO_COMBUSTIBLE_CHOICES = [
        ('MAGNA', 'Magna (Verde)'),
        ('PREMIUM', 'Premium (Roja)'),
        ('DIESEL', 'Diesel (Negro)'),
    ]
    tipo_combustible = models.CharField(
        max_length=20, 
        choices=TIPO_COMBUSTIBLE_CHOICES, 
        default='MAGNA',
        verbose_name="Tipo de Combustible"
    )
    
    propina = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="Propina (Opcional)")
    
    # Nuevos campos de evidencia y observaciones
    observaciones = models.TextField(null=True, blank=True, verbose_name="Observaciones")
    evidencia_antes = models.ImageField(upload_to='evidencias_combustible/', null=True, blank=True, verbose_name="Evidencia Antes (Tablero)")
    evidencia_despues = models.ImageField(upload_to='evidencias_combustible/', null=True, blank=True, verbose_name="Evidencia Después (Tablero)")

    class Meta:
        verbose_name = "Registro de Combustible"
        verbose_name_plural = "Registros de Combustible"
        ordering = ['-fecha']

    def save(self, *args, **kwargs):
        from .utils import compress_image
        from django.core.files.uploadedfile import UploadedFile

        # Comprimir Evidencia Antes
        if self.evidencia_antes:
            try:
                # Solo comprimir si es un archivo subido (no uno ya guardado)
                if isinstance(self.evidencia_antes.file, UploadedFile):
                    compressed = compress_image(self.evidencia_antes)
                    if compressed:
                        self.evidencia_antes = compressed
            except Exception:
                pass # Si falla, guardar original

        # Comprimir Evidencia Después
        if self.evidencia_despues:
            try:
                if isinstance(self.evidencia_despues.file, UploadedFile):
                    compressed = compress_image(self.evidencia_despues)
                    if compressed:
                        self.evidencia_despues = compressed
            except Exception:
                pass

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.unidad} - {self.total} ({self.fecha})"

class CheckListDiario(models.Model):
    unidad = models.ForeignKey(Unidad, on_delete=models.CASCADE)
    chofer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    fecha = models.DateField(auto_now_add=True)
    km_salida = models.PositiveIntegerField()
    km_llegada = models.PositiveIntegerField(null=True, blank=True)
    
    nivel_aceite = models.BooleanField(default=True, verbose_name="Aceite OK")
    nivel_anticongelante = models.BooleanField(default=True, verbose_name="Anticongelante OK")
    presion_llantas = models.BooleanField(default=True, verbose_name="Llantas OK")
    luces_funcionan = models.BooleanField(default=True, verbose_name="Luces OK")
    limpieza_vidrios = models.BooleanField(default=True, verbose_name="Limpiaparabrisas OK")
    combustible_inicial = models.CharField(max_length=20, verbose_name="Nivel Combustible (ej. 1/4)")
    observaciones = models.TextField(null=True, blank=True)

class ConfiguracionLogistica(models.Model):
    ESTADOS_CONTINGENCIA = [
        ('NORMAL', '🟢 Normal - Sin Restricciones'),
        ('PREVENTIVA', '⚪ Preventiva - Alerta '),
        ('FASE_1', '🟡 Fase 1 - Restricción 20% Vehículos'),
        ('FASE_2', '🔴 Fase 2 - Restricción 50% Vehículos'),
    ]

    PARIDAD_CHOICES = [
        ('PAR', 'Pares Restringidos'),
        ('NON', 'Nones Restringidos'),
        ('NA', 'No Aplica')
    ]

    estado_contingencia = models.CharField(
        max_length=10, 
        choices=ESTADOS_CONTINGENCIA, 
        default='NORMAL',
        verbose_name="Estado de Contingencia Ambiental"
    )
    
    restringir_h1 = models.CharField(
        max_length=3,
        choices=PARIDAD_CHOICES,
        default='NA',
        verbose_name="Paridad Restringida (Holograma 1)"
    )
    
    mensaje_alerta = models.TextField(
        blank=True, 
        help_text="Mensaje que aparecerá en el panel de los choferes y administración."
    )
    
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración Estado de Contingencia"
        verbose_name_plural = "Configuración Estado de Contingencia"

    def __str__(self):
        return f"Configuración Actual: {self.get_estado_contingencia_display()}"

    def save(self, *args, **kwargs):
        if not self.pk and ConfiguracionLogistica.objects.exists():
            return 
        super(ConfiguracionLogistica, self).save(*args, **kwargs)

class GastoUnidad(models.Model):
    TIPO_GASTO_CHOICES = [
        ('Verificación', '🔍 Verificación'),
        ('Tenencia', '💰 Tenencia'),
        ('Seguro', '🛡️ Seguro'),
        ('Mantenimiento', '🛠️ Mantenimiento (Preventivo/Correctivo)'),
        ('Multa', '👮 Multa'),
        ('Permiso', '📄 Permiso'),
        ('Peaje', '🛣️ Peaje'),
        ('Placas', '🚗 Placas'),
        ('Otro', '📦 Otro'),
    ]

    unidad = models.ForeignKey('Unidad', on_delete=models.CASCADE, related_name='gastos_generales')
    fecha = models.DateField(default=timezone.now, verbose_name="Fecha del Gasto")
    tipo = models.CharField(max_length=20, choices=TIPO_GASTO_CHOICES, verbose_name="Tipo de Gasto")
    detalle = models.CharField(max_length=255, verbose_name="Detalle del Gasto", help_text="Ej: Verificación 1er Semestre, Multa por velocidad")
    costo = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Costo ($)")
    evidencia = models.FileField(upload_to='gastos_evidencias/', null=True, blank=True, verbose_name="Evidencia (PDF/Foto)")

    # Campos específicos condicionales
    # Seguro
    poliza_seguro = models.CharField(max_length=50, null=True, blank=True, verbose_name="Nueva Póliza")
    aseguradora = models.CharField(max_length=100, null=True, blank=True, verbose_name="Aseguradora")
    tipo_cobertura = models.CharField(max_length=100, null=True, blank=True, verbose_name="Cobertura")
    
    # Multas
    chofer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Chofer Responsable", related_name='gastos_chofer')
    motivo_multa = models.CharField(max_length=200, null=True, blank=True, verbose_name="Motivo de Multa")
    acompanante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Acompañante/Chalán", related_name='gastos_acompanante')
    responsabilidad_compartida = models.BooleanField(default=False, verbose_name="¿Es responsabilidad compartida?")

    # Permisos / Placas
    tipo_permiso = models.CharField(max_length=100, null=True, blank=True, verbose_name="Tipo de Permiso")
    vigencia_permiso = models.DateField(null=True, blank=True, verbose_name="Nueva Vigencia")
    
    # Mantenimiento
    kilometraje = models.PositiveIntegerField(null=True, blank=True, verbose_name="Km al momento del gasto")

    class Meta:
        verbose_name = "Gasto de Unidad"
        verbose_name_plural = "Control de Gastos de Unidades"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.unidad.nUnidad} - {self.tipo} - {self.fecha}"

    def calcular_vencimiento_verificacion_edomex(self, fecha_verificacion):
        # Calendario Edomex 1er Semestre (Ene-Jun) -> Vence en 2do Semestre
        # Calendario Edomex 2do Semestre (Jul-Dic) -> Vence en 1er Semestre sgte año
        
        # Terminación Placa -> Mes Inicio, Mes Fin (Tupla del periodo siguiente)
        # 5-6 (Amarillo): Ene-Feb (1) / Jul-Ago (2)
        # 7-8 (Rosa): Feb-Mar (1) / Ago-Sep (2)
        # 3-4 (Rojo): Mar-Abr (1) / Sep-Oct (2)
        # 1-2 (Verde): Abr-May (1) / Oct-Nov (2)
        # 9-0 (Azul): May-Jun (1) / Nov-Dic (2)
        
        ultimo_digito = self.unidad.ultimo_digito
        sm = fecha_verificacion.month
        year = fecha_verificacion.year
        
        # Determinar semestre actual del gasto
        semestre_actual = 1 if sm <= 6 else 2
        
        # Determinar periodo objetivo (el siguiente semestre)
        if semestre_actual == 1:
            target_year = year
            target_semestre = 2 # Jul-Dic
        else:
            target_year = year + 1
            target_semestre = 1 # Ene-Jun
            
        # Mapeo de terminación a mes final del periodo objetivo
        # Si target es Semestre 2 (Jul-Dic):
        # 5-6: Ago (8), 7-8: Sep (9), 3-4: Oct (10), 1-2: Nov (11), 9-0: Dic (12)
        
        # Si target es Semestre 1 (Ene-Jun):
        # 5-6: Feb (2), 7-8: Mar (3), 3-4: Abr (4), 1-2: May (5), 9-0: Jun (6)
        
        mapa_semestre_1 = { # Mes fin
            5: 2, 6: 2,
            7: 3, 8: 3,
            3: 4, 4: 4,
            1: 5, 2: 5,
            9: 6, 0: 6
        }
        
        mapa_semestre_2 = { # Mes fin
            5: 8, 6: 8,
            7: 9, 8: 9,
            3: 10, 4: 10,
            1: 11, 2: 11,
            9: 12, 0: 12
        }
        
        target_month = None
        if target_semestre == 1:
            target_month = mapa_semestre_1.get(ultimo_digito)
        else:
            target_month = mapa_semestre_2.get(ultimo_digito)
            
        if target_month:
            # Vence el último día del mes objetivo del año objetivo
            import calendar
            last_day = calendar.monthrange(target_year, target_month)[1]
            return date(target_year, target_month, last_day)
            
        # Fallback genérico: 6 meses
        return fecha_verificacion + relativedelta(months=6)

    def save(self, *args, **kwargs):
        # 1. Compresión de Evidencia (Solo si es imagen)
        if self.evidencia:
            try:
                name = self.evidencia.name.lower() if self.evidencia.name else ''
                if name.endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp')):
                    from .utils import compress_image
                    from django.core.files.uploadedfile import UploadedFile
                    
                    # Verificar si es un archivo nuevo subido
                    if isinstance(self.evidencia.file, UploadedFile):
                        compressed = compress_image(self.evidencia)
                        if compressed:
                            self.evidencia = compressed
            except Exception:
                pass # Si falla o no es imagen soportada, continuar sin cambios

        super().save(*args, **kwargs)
        
        unidad = self.unidad
        fecha_gasto = self.fecha

        # Lógica de actualización automática de fechas
        if self.tipo == 'Seguro':
            # Seguro vence en 1 año
            # Si hay nueva vigencia explícita en el futuro (campo vigencia_permiso reutilizado o lógica dura)
            # Regla: Sumar 1 año a la fecha del gasto de pago
            unidad.vencimiento_poliza = fecha_gasto + relativedelta(years=1)
            
            # Actualizar datos de póliza si se proporcionaron
            if self.poliza_seguro: unidad.poliza_seguro = self.poliza_seguro
            if self.aseguradora: unidad.nombre_aseguradora = self.aseguradora
            if self.tipo_cobertura: unidad.tipo_cobertura_seguro = self.tipo_cobertura
        
        elif self.tipo == 'Verificación':
            # Calcular siguiente vencimiento basado en calendario Edomex
            nueva_fecha = self.calcular_vencimiento_verificacion_edomex(fecha_gasto)
            unidad.vencimiento_verificacion = nueva_fecha
            
        elif self.tipo == 'Tenencia':
            # Tenencia es anual, actualizar registro de último pago
            unidad.ultimo_pago_tenencia = fecha_gasto
            
        elif self.tipo == 'Placas':
            # Actualizar vigencia de placa si se proporciona
            if self.vigencia_permiso:
                unidad.vencimiento_placa = self.vigencia_permiso
        
        elif self.tipo == 'Permiso':
            # Actualizar vigencia del permiso si se proporciona y coincide tipo (opcional, requeriría campo en unidad)
            # Por ahora solo registramos el gasto
            pass

        unidad.save()


class OrdenServicio(models.Model):
    NIVEL_GASOLINA_CHOICES = [
        (25, '25%'),
        (50, '50%'),
        (75, '75%'),
        (100, '100%'),
    ]
    RESPONSABLE_CHOICES = [
        ('INTERNO', 'Interno'),
        ('EXTERNO', 'Externo'),
    ]
    TIPO_MANTENIMIENTO_CHOICES = [
        ('PREVENTIVO', 'Preventivo (Afinación, Cambio de aceite, etc.)'),
        ('CORRECTIVO', 'Correctivo (Reparación de falla/siniestro)'),
    ]
    
    fecha = models.DateField(default=timezone.now, verbose_name="Fecha")
    chofer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name="Chofer")
    unidad = models.ForeignKey('Unidad', on_delete=models.CASCADE, verbose_name="Unidad")
    kilometraje = models.PositiveIntegerField(verbose_name="Kilometraje")
    nivel_gasolina = models.IntegerField(choices=NIVEL_GASOLINA_CHOICES, verbose_name="Nivel de Gasolina")
    
    hora_entrada = models.TimeField(null=True, blank=True, verbose_name="Hora de Entrada")
    hora_salida = models.TimeField(null=True, blank=True, verbose_name="Hora de Salida")
    
    tipo_mantenimiento = models.CharField(max_length=15, choices=TIPO_MANTENIMIENTO_CHOICES, default='CORRECTIVO', verbose_name="Tipo de Mantenimiento")
    descripcion_detallada = models.TextField(verbose_name="Descripción detallada del servicio")
    responsable_mantenimiento = models.CharField(max_length=10, choices=RESPONSABLE_CHOICES, verbose_name="Responsable de mantenimiento")
    nombre_responsable_externo = models.CharField(max_length=150, null=True, blank=True, verbose_name="Nombre del externo (si aplica)")

    # SDC: Tracker Mantenimiento Preventivo (3.5.1.1)
    proximo_servicio_km = models.PositiveIntegerField(null=True, blank=True, verbose_name="Próximo Servicio Recomendado (Km)")
    proximo_servicio_fecha = models.DateField(null=True, blank=True, verbose_name="Próximo Servicio Recomendado (Fecha)")

    nombre_solicitante = models.CharField(max_length=150, verbose_name="Nombre de solicitante")
    firma_solicitante_base64 = models.TextField(verbose_name="Firma Solicitante (Base64)", null=True, blank=True)
    
    nombre_autorizante = models.CharField(max_length=150, null=True, blank=True, verbose_name="Nombre de autorizante")
    firma_autorizante_base64 = models.TextField(verbose_name="Firma Autorizante (Base64)", null=True, blank=True)
    
    comentarios = models.TextField(null=True, blank=True, verbose_name="Comentarios")

    class Meta:
        verbose_name = "Orden de Servicio"
        verbose_name_plural = "Órdenes de Servicio"
        ordering = ['-fecha', '-id']

    def __str__(self):
        return f"OS-{self.id} | {self.unidad.nUnidad} - {self.fecha}"


class ChecklistUnidad(models.Model):
    unidad = models.ForeignKey(Unidad, on_delete=models.CASCADE, verbose_name="Unidad")
    chofer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name="Chofer")
    fecha = models.DateField(default=timezone.now, verbose_name="Fecha")
    hora_registro = models.TimeField(auto_now_add=True, verbose_name="Hora de Registro")
    km_actual = models.PositiveIntegerField(default=0, verbose_name="Kilometraje Actual")

    # Módulo 3.5.1.3 - Aspectos a revisar
    nivel_combustible = models.IntegerField(choices=[(25, '25%'), (50, '50%'), (75, '75%'), (100, '100%')], verbose_name="Nivel Combustible")
    
    # Toggles binarios de verificación (True = OK, False = Requiere atención / No verificado)
    aceite_motor = models.BooleanField(default=False, verbose_name="Nivel Aceite Motor OK")
    anticongelante = models.BooleanField(default=False, verbose_name="Nivel Anticongelante/Agua OK")
    llantas_birlos = models.BooleanField(default=False, verbose_name="Presión Llantas y Ajuste Birlos OK")
    carroceria_golpes = models.BooleanField(default=False, verbose_name="Carrocería sin golpes evidentes")
    luces = models.BooleanField(default=False, verbose_name="Luces (altas, bajas, cuartos, dir.) OK")
    cinturon = models.BooleanField(default=False, verbose_name="Cinturón de seguridad OK")
    equipo_seguridad = models.BooleanField(default=False, verbose_name="Gato, palanca, cruceta, refacción, triángulo OK")
    documentacion = models.BooleanField(default=False, verbose_name="Circulación, Póliza, Licencia OK")
    frenos = models.BooleanField(default=False, verbose_name="Freno pie y mano OK")
    bateria_arranque = models.BooleanField(default=False, verbose_name="Batería y Arranque OK")
    limpiaparabrisas = models.BooleanField(default=False, verbose_name="Limpiaparabrisas OK")
    claxon = models.BooleanField(default=False, verbose_name="Claxon OK")

    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones / Falla reportada")

    class Meta:
        verbose_name = "Checklist Diario de Unidad"
        verbose_name_plural = "Checklists Diarios"
        ordering = ['-fecha', '-hora_registro']

    def __str__(self):
        return f"Checklist {self.unidad.nUnidad} - {self.fecha} - {self.chofer.username}"

class InventarioLlanta(models.Model):
    POSICION_CHOICES = [
        ('DI1', 'Delantera Izquierda 1'), ('DD1', 'Delantera Derecha 1'),
        ('TI1', 'Trasera Izquierda 1'), ('TD1', 'Trasera Derecha 1'),
        ('TI2', 'Trasera Izquierda 2 (Doble)'), ('TD2', 'Trasera Derecha 2 (Doble)'),
        ('REFACCION', 'Refacción'),
    ]
    
    unidad = models.ForeignKey(Unidad, on_delete=models.CASCADE, related_name="llantas", verbose_name="Unidad Asignada")
    marca = models.CharField(max_length=50, verbose_name="Marca de Llanta")
    medida = models.CharField(max_length=50, verbose_name="Medida (Ej. 295/80R22.5)")
    numero_serie = models.CharField(max_length=100, unique=True, verbose_name="Número de Serie/DOT")
    posicion = models.CharField(max_length=20, choices=POSICION_CHOICES, verbose_name="Posición en Unidad")
    
    # SDC: Profundidad mínima de piso (3.5.3.1)
    profundidad_inicial_mm = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, verbose_name="Profundidad Inicial (mm)")
    profundidad_piso_mm = models.DecimalField(max_digits=4, decimal_places=1, verbose_name="Profundidad de Piso Actual (mm)")
    costo = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Costo de la Llanta ($)")
    fecha_instalacion = models.DateField(default=timezone.now, verbose_name="Fecha Instalación")
    km_instalacion = models.PositiveIntegerField(verbose_name="Km al Instalar")
    activa = models.BooleanField(default=True, verbose_name="Instalada Actualmente")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Condición / Observaciones")
    fecha_vencimiento = models.DateField(blank=True, null=True, verbose_name="Fecha de Vencimiento (por DOT)")

    class Meta:
        verbose_name = "Inventario de Llanta"
        verbose_name_plural = "Inventario de Llantas"
        unique_together = ('unidad', 'posicion', 'activa') # Solo una llanta activa por posición

    def save(self, *args, **kwargs):
        if not self.pk and not self.profundidad_inicial_mm:
            self.profundidad_inicial_mm = self.profundidad_piso_mm
        elif self.pk and not self.profundidad_inicial_mm:
            # Para registros existentes antes de la migración
            self.profundidad_inicial_mm = self.profundidad_piso_mm
            
        # Calcular fecha vencimiento a partir del DOT (últimos 4 dígitos = Semana/Año)
        import re, datetime
        serie_val = self.numero_serie.strip()
        match = re.search(r'(\d{4})$', serie_val)
        if match:
            dot_code = match.group(1)
            semana_str = dot_code[:2]
            anio_str = dot_code[2:]
            try:
                semana = int(semana_str)
                anio = int(anio_str)
                anio_completo = 2000 + anio
                
                if 1 <= semana <= 53:
                    primer_dia_anio = datetime.date(anio_completo, 1, 1)
                    fecha_fabricacion = primer_dia_anio + datetime.timedelta(weeks=semana-1)
                    # Vencimiento estimado de llanta: 5 años
                    try:
                        self.fecha_vencimiento = fecha_fabricacion.replace(year=fecha_fabricacion.year + 5)
                    except ValueError:
                        # Si es 29 de febrero, retrocedemos a 28 de feb
                        self.fecha_vencimiento = fecha_fabricacion + datetime.timedelta(days=5*365+1)
            except ValueError:
                pass
                
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Llanta {self.numero_serie} ({self.posicion}) - {self.unidad.nUnidad}"

class ConfiguracionGeneral(models.Model):
    sueldo_semanal_chofer = models.DecimalField(max_digits=10, decimal_places=2, default=2500.00, verbose_name="Sueldo Semanal Chofer ($)")
    sueldo_semanal_chalan = models.DecimalField(max_digits=10, decimal_places=2, default=1500.00, verbose_name="Sueldo Semanal Chalán ($)")
    tiempo_descarga_promedio_min = models.PositiveIntegerField(default=30, verbose_name="Tiempo de Descarga Promedio (min)", help_text="Tiempo fijo agregado a cada viaje por maniobras.")
    limite_seguridad_llanta_mm = models.DecimalField(max_digits=4, decimal_places=1, default=3.0, verbose_name="Límite Seguridad Llanta (mm)")
    vida_util_estimada_llanta_km = models.PositiveIntegerField(default=100000, verbose_name="Vida Útil Estimada Llanta (km)")
    
    # Fase 2: Pesos y Tolerancias
    limite_peso_vehiculo_personal_kg = models.DecimalField(max_digits=10, decimal_places=2, default=200.00, verbose_name="Límite Peso Vehículo Personal (kg)")
    tolerancia_peso_ruta_kg = models.DecimalField(max_digits=10, decimal_places=2, default=50.00, verbose_name="Tolerancia de Peso en Ruta (kg)")
    
    # Prefijos de Ticket (Fase 2+: Configuración Mostrador)
    tipos_ticket_json = models.JSONField(
        default=list, 
        blank=True, 
        null=True, 
        verbose_name="Tipos de Ticket (Prefijos)",
        help_text="Formato: [{'nombre': '...', 'prefijo': '...'}, ...]"
    )
    
    @property
    def costo_minuto_chofer(self):
        # 53 hrs a la semana = 3180 minutos a la semana laborables
        from decimal import Decimal
        return Decimal(str(self.sueldo_semanal_chofer)) / Decimal('3180.0')

    @property
    def costo_minuto_chalan(self):
        from decimal import Decimal
        return Decimal(str(self.sueldo_semanal_chalan)) / Decimal('3180.0')
    
    class Meta:
        verbose_name = "Configuración General"
        verbose_name_plural = "Configuraciones Generales"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        self.recalcular_tarifas_flete()

    def recalcular_tarifas_flete(self):
        """Asigna y actualiza masivamente el Costo Base de Flete a cada zona cuando hay cambios en RRHH/Logística"""
        from decimal import Decimal
        import math
        
        zonas = ZonaEntrega.objects.all()
        if not zonas.exists(): return
        
        costo_min_chofer = self.costo_minuto_chofer
        costo_min_chalan = self.costo_minuto_chalan
        t_descarga = Decimal(self.tiempo_descarga_promedio_min)
        
        # Obtener los tipos de unidades base como en la API
        unidades_reales = list(Unidad.objects.filter(en_servicio=True).select_related())
        tipos_existentes = {u.tipo: u for u in unidades_reales}
        tipos_base = ['CAMION', 'CAMIONETA_3_5', 'CAMIONETA_1_5', 'AUTO', 'MOTO']
        unidades_a_evaluar = []
        
        for tb in tipos_base:
            if tb in tipos_existentes:
                unidades_a_evaluar.append(tipos_existentes[tb])
            else:
                virtual_u = Unidad(tipo=tb, nombre_corto=f"Estimado ({tb.title()})", kilometraje_actual=0)
                virtual_u.pk = -1
                unidades_a_evaluar.append(virtual_u)
                
        for zona in zonas:
            if not zona.distancia_km or not zona.tiempo_traslado_minutos:
                continue
                
            dist = Decimal(str(zona.distancia_km))
            tiempo_min = Decimal(str(zona.tiempo_traslado_minutos))
            
            km_totales = dist * 2
            tiempo_total_viaje = (tiempo_min * 2) + t_descarga
            
            max_costo = Decimal('0.0')
            for u in unidades_a_evaluar:
                c_km = u.costo_operativo_total_por_km
                costo_op = km_totales * c_km
                costo_tiempo = tiempo_total_viaje * (costo_min_chofer + costo_min_chalan)
                costo_flete = round(costo_op + costo_tiempo, 2)
                if costo_flete > max_costo:
                    max_costo = costo_flete
            
            # El dashboard frontend aproxima el costo hacia arriba
            nueva_tarifa = Decimal(str(math.ceil(max_costo)))
            if zona.tarifa_flete != nueva_tarifa:
                zona.tarifa_flete = nueva_tarifa
                zona.save(update_fields=['tarifa_flete'])

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Configuración Global"


class MedicionNeumatico(models.Model):
    unidad = models.ForeignKey(Unidad, on_delete=models.CASCADE, related_name="mediciones_neumaticos", verbose_name="Unidad")
    llanta = models.ForeignKey('InventarioLlanta', on_delete=models.CASCADE, related_name="mediciones", verbose_name="Llanta")
    fecha = models.DateField(default=timezone.now, verbose_name="Fecha de Medición")
    km_medicion = models.PositiveIntegerField(verbose_name="Kilometraje al Medir")
    presion_psi = models.DecimalField(max_digits=5, decimal_places=1, verbose_name="Presión (PSI)")
    profundidad_mm = models.DecimalField(max_digits=4, decimal_places=1, verbose_name="Profundidad (mm)")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Causa Probable / Observaciones")
    
    class Meta:
        verbose_name = "Medición de Neumático"
        verbose_name_plural = "Mediciones de Neumáticos"
        ordering = ['-fecha', '-id']

    def __str__(self):
        return f"Medición {self.llanta.get_posicion_display()} - {self.unidad.nUnidad} ({self.fecha})"
