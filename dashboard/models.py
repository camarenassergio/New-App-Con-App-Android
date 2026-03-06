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
        ('CAMION', 'Camión'),
        ('CAMIONETA', 'Camioneta'),
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
        elif self.modelo_anio >= (anio_actual - 25):
            self.holograma = "1"
        else:
            self.holograma = "2"
            
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Unidad"
        verbose_name_plural = "Unidades"

class Operador(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre Completo")
    telefono = models.CharField(max_length=15, verbose_name="Teléfono")
    licencia = models.CharField(max_length=50, unique=True, verbose_name="No. de Licencia")
    vigencia_licencia = models.DateField(verbose_name="Vigencia de Licencia")
    activo = models.BooleanField(default=True, verbose_name="¿Está activo?")

    def __str__(self):
        return self.nombre

    @property
    def licencia_vencida(self):
        return self.vigencia_licencia and self.vigencia_licencia < timezone.now().date()
        
    @property
    def licencia_por_vencer(self):
        if not self.vigencia_licencia: return False
        days = (self.vigencia_licencia - timezone.now().date()).days
        return 0 <= days <= 30

    class Meta:
        verbose_name_plural = "Operadores"

class ZonaEntrega(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la Zona (Ej. Norte, Sur, Centro)")
    codigos_postales = models.TextField(verbose_name="Códigos Postales", help_text="Separados por coma", null=True, blank=True)
    colonias = models.TextField(verbose_name="Colonias que Abarca", help_text="Listado de colonias principales", null=True, blank=True)
    tiempo_traslado_minutos = models.PositiveIntegerField(verbose_name="Tiempo Medio Traslado (mins)")
    distancia_km = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Distancia Media (Km) desde Sucursal")
    tarifa_flete = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Costo Base de Flete ($)", default=0.00)
    costo_maniobra = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Costo Maniobra Adicional ($)", default=0.00)
    color_hex = models.CharField(max_length=7, default="#3388ff", verbose_name="Color en Mapa", help_text="Color para identificar la zona en el mapa")
    geojson_data = models.TextField(blank=True, null=True, verbose_name="Polígonos de la Zona (GeoJSON)", help_text="Información geográfica de la zona")

    class Meta:
        verbose_name = "Zona de Entrega"
        verbose_name_plural = "Zonas de Entrega"
        ordering = ['nombre']

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
                # According to logs, the file is at: /home/sscamarenas/Proyectos/Logistica Casa Lupita/App_Stealth/dashboard/data/zonas_texcoco.json
                data_path = os.path.join(settings.BASE_DIR, 'dashboard', 'data', 'zonas_texcoco.json')
                
                features = []
                with open(data_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            feature = json.loads(line)
                            # the json property is "d_cp" based on the uploaded file
                            cp_value = feature.get('properties', {}).get('d_cp', '').strip()
                            if cp_value in cps_limpios:
                                # We keep the raw geometry
                                features.append(feature)
                        except json.JSONDecodeError:
                            continue
                            
                if features:
                    # Package them into a FeatureCollection for this specific zone
                    geo_collection = {
                        "type": "FeatureCollection",
                        "features": features
                    }
                    self.geojson_data = json.dumps(geo_collection)
                else:
                     self.geojson_data = "" # No features matched
                     
            except Exception as e:
                # We catch exceptions to prevent preventing save on missing file
                print(f"Error loading GeoJSON for zone {self.nombre}: {e}")
                
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Zona: {self.nombre} ({self.tiempo_traslado_minutos} min)"


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
    chofer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Chofer Responsable")
    motivo_multa = models.CharField(max_length=200, null=True, blank=True, verbose_name="Motivo de Multa")

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
    profundidad_piso_mm = models.DecimalField(max_digits=4, decimal_places=1, verbose_name="Profundidad de Piso (mm)")
    fecha_instalacion = models.DateField(default=timezone.now, verbose_name="Fecha Instalación")
    km_instalacion = models.PositiveIntegerField(verbose_name="Km al Instalar")
    activa = models.BooleanField(default=True, verbose_name="Instalada Actualmente")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Condición / Observaciones")

    class Meta:
        verbose_name = "Inventario de Llanta"
        verbose_name_plural = "Inventario de Llantas"
        unique_together = ('unidad', 'posicion', 'activa') # Solo una llanta activa por posición

    def __str__(self):
        return f"Llanta {self.numero_serie} ({self.posicion}) - {self.unidad.nUnidad}"

