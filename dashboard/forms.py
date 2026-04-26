from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django import forms
from django.db.models import Q
from django.utils import timezone
from .models import Unidad, RegistroCombustible, Personal

User = get_user_model()

ROLES_SECUNDARIOS_CHOICES = [
    ('ADMIN', 'Administrador'),
    ('MOSTRADOR', 'Mostrador'),
    ('RUTAS', 'Rutas / Logística'),
    ('ALMACEN', 'Almacén'),
    ('CHOFER', 'Chofer'),
]

class PersonalCreationForm(UserCreationForm):
    # Campos adicionales de Personal
    nombre = forms.CharField(max_length=100, label="Nombre(s)")
    apellido_paterno = forms.CharField(max_length=100, label="Apellido Paterno")
    apellido_materno = forms.CharField(max_length=100, label="Apellido Materno", required=False)
    puesto = forms.ChoiceField(choices=Personal.PUESTO_CHOICES, label="Puesto / Rol Principal")
    roles_secundarios = forms.MultipleChoiceField(
        choices=ROLES_SECUNDARIOS_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Roles Secundarios (Workspace Switcher)"
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('nombre', 'apellido_paterno', 'apellido_materno', 'puesto', 'roles_secundarios')

    def clean_roles_secundarios(self):
        data = self.cleaned_data.get('roles_secundarios')
        puesto_principal = self.cleaned_data.get('puesto')
        
        if data:
            if puesto_principal in data:
                data.remove(puesto_principal)
            return ",".join(data)
        return ""

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['nombre']
        user.last_name = f"{self.cleaned_data['apellido_paterno']} {self.cleaned_data.get('apellido_materno', '')}".strip()
        
        if commit:
            user.save()
            Personal.objects.create(
                usuario=user,
                nombre=self.cleaned_data['nombre'],
                apellido_paterno=self.cleaned_data['apellido_paterno'],
                apellido_materno=self.cleaned_data.get('apellido_materno', ''),
                puesto=self.cleaned_data['puesto'],
                roles_secundarios=self.cleaned_data['roles_secundarios']
            )
        return user

class PersonalUpdateForm(forms.ModelForm):
    # Campos que van directo al User
    username = forms.CharField(max_length=150, label="Nombre de Usuario")
    nombre = forms.CharField(max_length=100, label="Nombre(s)")
    apellido_paterno = forms.CharField(max_length=100, label="Apellido Paterno")
    apellido_materno = forms.CharField(max_length=100, label="Apellido Materno", required=False)

    roles_secundarios = forms.MultipleChoiceField(
        choices=ROLES_SECUNDARIOS_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Roles Secundarios (Workspace Switcher)"
    )

    class Meta:
        model = Personal
        fields = ['nombre', 'apellido_paterno', 'apellido_materno', 'puesto', 'roles_secundarios']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'usuario'):
            self.initial['username'] = self.instance.usuario.username
        if self.instance and getattr(self.instance, 'roles_secundarios', None):
            self.initial['roles_secundarios'] = [r.strip() for r in self.instance.roles_secundarios.split(',') if r.strip()]

    def clean_roles_secundarios(self):
        data = self.cleaned_data.get('roles_secundarios')
        puesto_principal = self.cleaned_data.get('puesto')
        
        if data:
            # Eliminar el puesto principal de los secundarios si se seleccionó por error
            if puesto_principal in data:
                data.remove(puesto_principal)
            return ",".join(data)
        return ""
            
    def save(self, commit=True):
        personal = super().save(commit=False)
        user = personal.usuario
        
        user.username = self.cleaned_data['username']
        user.first_name = self.cleaned_data['nombre']
        user.last_name = f"{self.cleaned_data['apellido_paterno']} {self.cleaned_data.get('apellido_materno', '')}".strip()
        
        if commit:
            user.save()
            personal.save()
        return personal

class UnidadForm(forms.ModelForm):
    supervisor_auth = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
        label="Auth Supervisor"
    )

    class Meta:
        model = Unidad
        fields = [
            'nombre_corto',             # 1. Nombre Interno
            'descripcion_vehiculo',     # 2. Descripción
            'placas',                   # 3. Placas
            'no_serie',                 # 4. No. Serie
            'no_motor',                 # 5. No. Motor
            'marca',                    # 6. Marca
            'submarca',                 # 7. Submarca
            'modelo_anio',              # 8. Modelo
            'tipo',                     # 9. Tipo
            'tipo_combustible_unidad',  # (Extra) Combustible (Requerido por lógica)
            'en_servicio',              # (Activa / Baja Temporal)
            'capacidad_kg',             # 10. Capacidad
            'capacidad_tanque',         # (Extra) Capacidad Tanque
            'numero_llantas',           # (Extra) Número de Llantas
            'responsable_mantenimiento', # (Nuevo) Responsable Asignado
            'tarjeta_circulacion',      # 11. Tarjeta de Circulación
            'vencimiento_placa',        # 12. Vencimiento Placa
            'poliza_seguro',            # 13. Número de Póliza
            'titular_poliza',           # 14. Titular de la Póliza
            'nombre_aseguradora',       # 15. Aseguradora
            'tipo_cobertura_seguro',    # 16. Cobertura
            'vencimiento_poliza',       # 17. Vencimiento Póliza
            'fecha_adquisicion',        # 18. Fecha Adquisición
            'kilometraje_actual',       # 19. Km Actual
            'supervisor_auth',          # (Extra) Autorización
            'ultimo_pago_tenencia',     # 20. Último pago Tenencia
            'vencimiento_verificacion', # 21. Vencimiento Verificación
            'tipo_permiso_stc',         # 22. Permiso STC
            'observaciones',            # 23. Observaciones
            'doc_factura',              # Expediente Digital SDC
            'doc_tarjeta_circulacion',
            'doc_poliza',
            'doc_permisos',
        ]
        widgets = {
            'fecha_adquisicion': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'vencimiento_placa': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'vencimiento_poliza': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'ultimo_pago_tenencia': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'vencimiento_verificacion': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
            'responsable_mantenimiento': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar responsables para que solo aparezcan CHOFERES
        self.fields['responsable_mantenimiento'].queryset = User.objects.filter(
            personal__puesto='CHOFER',
            is_active=True
        ).order_by('first_name', 'last_name')
        self.fields['responsable_mantenimiento'].label_from_instance = lambda obj: f"🚚 {obj.get_full_name() or obj.username}"
        self.fields['responsable_mantenimiento'].required = False
        self.fields['responsable_mantenimiento'].empty_label = "--- Sin Responsable Asignado ---"

        # Campos obligatorios según solicitud del usuario
        for field_name in [
            'nombre_corto', 'descripcion_vehiculo', 'placas',
            'no_serie', 'no_motor', 'marca', 'submarca', 'modelo_anio',
            'tipo', 'tipo_combustible_unidad', 'capacidad_kg',
            'capacidad_tanque', 'numero_llantas',
            'tarjeta_circulacion', 'vencimiento_placa',
            'poliza_seguro', 'titular_poliza', 'nombre_aseguradora',
            'tipo_cobertura_seguro', 'vencimiento_poliza',
            'fecha_adquisicion', 'ultimo_pago_tenencia',
            'vencimiento_verificacion', 'tipo_permiso_stc'
        ]:
            if field_name in self.fields:
                self.fields[field_name].required = True

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        tipo_combustible = cleaned_data.get('tipo_combustible_unidad')

        # 1. Validación de Combustible
        if tipo == 'CAMION' and tipo_combustible != 'DIESEL':
            self.add_error('tipo_combustible_unidad', "Los Camiones solo pueden usar DIESEL.")

        # 2. Validación de Cambio de Kilometraje (Requiere Auth Supervisor)
        # Solo aplica en edición (si self.instance.pk existe)
        if self.instance.pk:
            new_km = cleaned_data.get('kilometraje_actual')
            old_km = self.instance.kilometraje_actual
            
            # Si hubo cambio en el kilometraje
            if new_km is not None and old_km is not None and new_km != old_km:
                supervisor_pwd = cleaned_data.get('supervisor_auth')
                
                if not supervisor_pwd:
                    self.add_error('supervisor_auth', "Se requiere autorización de supervisor para modificar el kilometraje.")
                else:
                    # Validar contraseña contra cualquier superusuario
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    superusers = User.objects.filter(is_superuser=True)
                    
                    auth_success = False
                    for su in superusers:
                        if su.check_password(supervisor_pwd):
                            auth_success = True
                            break
                    
                    if not auth_success:
                        self.add_error('supervisor_auth', "Contraseña de supervisor incorrecta. Cambio no autorizado.")
        
        return cleaned_data

class RegistroCombustibleForm(forms.ModelForm):
    # Field to estimate initial fuel level to validate overflow
    NIVEL_INICIAL_CHOICES = [
        ('0', '0% - Reserva'),
        ('0.25', '25% - 1/4 Tanque'),
        ('0.50', '50% - 1/2 Tanque'),
        ('0.75', '75% - 3/4 Tanque'),
        ('0.90', '90% - Casi Lleno'),
    ]
    nivel_inicial = forms.ChoiceField(
        choices=NIVEL_INICIAL_CHOICES, 
        label="Nivel Inicial (Aprox)",
        help_text="¿Cuánto combustible tenía ANTES de cargar?",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = RegistroCombustible
        exclude = ['chofer', 'fecha'] # Auto-filled in view
        widgets = {
             'unidad': forms.Select(attrs={'class': 'form-select'}),
             'tipo_combustible': forms.Select(attrs={'class': 'form-select'}),
             # Number inputs for better mobile experience
             'kilometraje_actual': forms.NumberInput(attrs={'step': '1'}),
             'litros': forms.NumberInput(attrs={'step': '0.01', 'lang': 'en-US'}),
             'precio_litro': forms.NumberInput(attrs={'step': '0.01', 'lang': 'en-US'}),
             'total': forms.NumberInput(attrs={'step': '0.01', 'lang': 'en-US', 'readonly': 'readonly'}),
             'propina': forms.NumberInput(attrs={'step': '0.01', 'lang': 'en-US'}),
             'observaciones': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
             'evidencia_antes': forms.ClearableFileInput(attrs={'class': 'form-control'}),
             'evidencia_despues': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super(RegistroCombustibleForm, self).__init__(*args, **kwargs)
        # Hacer obligatoria la evidencia fotográfica solo cuando se está creando un nuevo registro
        if not self.instance.pk:
            self.fields['evidencia_antes'].required = True
            self.fields['evidencia_despues'].required = True
    
    def clean(self):
        cleaned_data = super().clean()
        unidad = cleaned_data.get('unidad')
        tipo_combustible = cleaned_data.get('tipo_combustible')
        litros = cleaned_data.get('litros')
        nivel_inicial_str = cleaned_data.get('nivel_inicial')

        if unidad and tipo_combustible:
            # 1. Validate Fuel Type Compatibility
            if unidad.tipo_combustible_unidad == 'DIESEL' and tipo_combustible != 'DIESEL':
                self.add_error('tipo_combustible', f"La unidad {unidad.nUnidad} usa Diesel. No puedes cargar {tipo_combustible}.")
            
            if unidad.tipo_combustible_unidad == 'GASOLINA' and tipo_combustible == 'DIESEL':
                self.add_error('tipo_combustible', f"La unidad {unidad.nUnidad} usa Gasolina. No puedes cargar Diesel.")

        if unidad and litros and nivel_inicial_str:
            # 2. Validate Tank Capacity Overflow
            try:
                capacidad = unidad.capacidad_tanque
                nivel_inicial = float(nivel_inicial_str)
                litros_existentes = capacidad * nivel_inicial
                capacidad_disponible = capacidad - litros_existentes
                
                # Tolerance: 15% overflow allowed for bad estimation/neck expansion
                tolerancia = capacidad * 0.15 
                max_permisible = capacidad_disponible + tolerancia
                
                if float(litros) > max_permisible:
                    self.add_error('litros', f"¡Exceso de Litros! La unidad tiene cap. {capacidad}L y reportaste nivel inicial {nivel_inicial*100}%. Solo cabrían aprox. {capacidad_disponible:.0f}L (+ margen error). Estás intentando meter {litros}L.")
            except (ValueError, TypeError):
                pass
        

from .models import GastoUnidad

class GastoUnidadForm(forms.ModelForm):
    class Meta:
        model = GastoUnidad
        fields = [
            'unidad', 'tipo', 'fecha', 'detalle', 'costo', 'evidencia',
            'poliza_seguro', 'aseguradora', 'tipo_cobertura', 
            'chofer', 'motivo_multa', 'acompanante', 'responsabilidad_compartida',
            'tipo_permiso', 'vigencia_permiso', 
            'kilometraje'
        ]
        widgets = {
            'fecha': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'vigencia_permiso': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'unidad': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo_gasto'}),
            'chofer': forms.Select(attrs={'class': 'form-select'}),
            'detalle': forms.TextInput(attrs={'class': 'form-control'}),
            'costo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'kilometraje': forms.NumberInput(attrs={'class': 'form-control'}),
            'poliza_seguro': forms.TextInput(attrs={'class': 'form-control'}),
            'aseguradora': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_cobertura': forms.TextInput(attrs={'class': 'form-control'}),
            'motivo_multa': forms.TextInput(attrs={'class': 'form-control'}),
            'acompanante': forms.Select(attrs={'class': 'form-select'}),
            'tipo_permiso': forms.TextInput(attrs={'class': 'form-control'}),
            'evidencia': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Eliminar opción vacía y establecer 'Otro' por defecto
        if 'tipo' in self.fields:
            self.fields['tipo'].empty_label = None
            self.fields['tipo'].initial = 'Otro'

        # Campos obligatorios según estandar v2
        for field_name in ['unidad', 'tipo', 'fecha', 'detalle', 'costo']:
            if field_name in self.fields:
                self.fields[field_name].required = True

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        
        # Validaciones Condicionales
        if tipo == 'Seguro':
            if not cleaned_data.get('poliza_seguro'):
                self.add_error('poliza_seguro', 'Debes ingresar el número de la nueva póliza.')
            if not cleaned_data.get('aseguradora'):
                self.add_error('aseguradora', 'Debes ingresar el nombre de la aseguradora.')
                
        if tipo == 'Multa':
            if not cleaned_data.get('chofer'):
                self.add_error('chofer', 'Debes seleccionar al chofer responsable de la multa.')
            if not cleaned_data.get('motivo_multa'):
                self.add_error('motivo_multa', 'Debes indicar el motivo de la infracción.')

        if tipo in ['Placas', 'Permiso']:
             if not cleaned_data.get('vigencia_permiso'):
                 self.add_error('vigencia_permiso', 'Debes indicar la nueva fecha de vigencia.')

        return cleaned_data

class CombustibleDeleteForm(forms.Form):
    admin_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña de Administrador'}),
        label="Contraseña de Administrador"
    )
    nuevo_kilometraje = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Kilometraje Actual Real (Corrección)",
        help_text="Ajusta el kilometraje de la unidad para corregir inconsistencias."
    )

import base64
from django.core.files.base import ContentFile

class UsuarioPerfilForm(forms.ModelForm):
    foto_base64 = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Personal
        fields = ['foto']
        widgets = {
            'foto': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*', 'id': 'foto_input'})
        }

    def clean(self):
        cleaned_data = super().clean()
        foto_base64 = cleaned_data.get('foto_base64')
        if foto_base64 and ';base64,' in foto_base64:
            format, imgstr = foto_base64.split(';base64,') 
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f"perfil_{self.instance.usuario.username}.{ext}")
            cleaned_data['foto'] = data
        return cleaned_data

from .models import OrdenServicio

class OrdenServicioForm(forms.ModelForm):
    # Campos ocultos para capturar datos de la UI personalizada (botones y signature pad)
    firma_solicitante_base64 = forms.CharField(widget=forms.HiddenInput(), required=False)
    firma_autorizante_base64 = forms.CharField(widget=forms.HiddenInput(), required=False)
    nivel_gasolina = forms.IntegerField(widget=forms.HiddenInput(), required=True)
    responsable_mantenimiento = forms.CharField(widget=forms.HiddenInput(), required=True)

    class Meta:
        model = OrdenServicio
        fields = [
            'fecha', 'unidad', 'kilometraje', 'nivel_gasolina',
            'hora_entrada', 'hora_salida', 'tipo_mantenimiento', 'descripcion_detallada',
            'responsable_mantenimiento', 'nombre_responsable_externo',
            'proximo_servicio_km', 'proximo_servicio_fecha',
            'nombre_solicitante', 'firma_solicitante_base64',
            'nombre_autorizante', 'firma_autorizante_base64',
            'comentarios'
        ]
        widgets = {
            'fecha': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'hora_entrada': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'hora_salida': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'tipo_mantenimiento': forms.Select(attrs={'class': 'form-select'}),
            'descripcion_detallada': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'comentarios': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'nombre_responsable_externo': forms.TextInput(attrs={'class': 'form-control'}),
            'proximo_servicio_km': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Km recomendado'}),
            'proximo_servicio_fecha': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'nombre_solicitante': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_autorizante': forms.TextInput(attrs={'class': 'form-control'}),
        }

from .models import ChecklistUnidad

class ChecklistUnidadForm(forms.ModelForm):
    # Campo oculto para manejar el UI de botones grandes
    nivel_combustible = forms.IntegerField(widget=forms.HiddenInput(), required=True)

    class Meta:
        model = ChecklistUnidad
        exclude = ['unidad', 'chofer', 'fecha', 'hora_registro']
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Opcional: Detalles de alguna anomalía...'}),
            'km_actual': forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Ej. 125000', 'required': 'required'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.daily_fields = [
            # Fluidos
            'aceite_motor', 'urea', 'anticongelante', 'liquido_frenos', 'agua_limpiabrisas',
            # Seguridad Activa
            'luces', 'claxon', 'alerta_reversa', 'limpiaparabrisas',
            # Controles Base
            'frenos', 'clutch', 'bateria_arranque',
            # Estado Exterior y Carga
            'llantas_presion', 'carroceria_golpes', 'lona', 'bandas_sujecion',
            # Otros obligatorios (Documentación y Seguridad básica)
            'equipo_seguridad', 'documentacion', 'cinturon'
        ]
        
        self.biweekly_fields = [
            'birlos_ajuste', 'limpieza_interiores', 'limpieza_exteriores',
            'aceite_direccion'
        ]

        # Todos los campos booleanos deben ser required=False para permitir el valor False (Falla)
        for name, field in self.fields.items():
            if isinstance(field, forms.BooleanField):
                field.required = False
            
            # Ajuste de labels según el nuevo protocolo (limpieza de "OK")
            if field.label and ' OK' in field.label:
                field.label = field.label.replace(' OK', '')
            
            if name == 'cinturon':
                field.label = "Cinturón de Seguridad"
            elif name == 'carroceria_golpes':
                field.label = "Carrocería sin golpes nuevos"
            elif name == 'birlos_ajuste':
                field.label = "Ajuste de Birlos"

    def clean(self):
        cleaned_data = super().clean()
        unidad_id = self.data.get('unidad_id')
        km_actual = cleaned_data.get('km_actual')
        
        if not unidad_id or km_actual is None:
            return cleaned_data
            
        from .models import Unidad, MedicionNeumatico, InventarioLlanta
        import datetime
        from django.utils import timezone
        
        try:
            unidad = Unidad.objects.get(id=unidad_id)
        except Unidad.DoesNotExist:
            return cleaned_data

        # VALIDACIÓN SOLICITADA: No puede ser menor al actual de la BD
        if km_actual < unidad.kilometraje_actual:
            self.add_error('km_actual', f"El kilometraje no puede ser menor al último registrado ({unidad.kilometraje_actual} km).")
            
        ultima_medicion = MedicionNeumatico.objects.filter(unidad=unidad).order_by('-fecha').first()
        requiere_inspeccion = False
        
        if ultima_medicion:
            dias_transcurridos = (timezone.now().date() - ultima_medicion.fecha).days
            km_transcurridos = km_actual - ultima_medicion.km_medicion
            
            if dias_transcurridos >= 15 or km_transcurridos >= 5000:
                requiere_inspeccion = True
        else:
            # Si nunca se ha medido, requiere inspección inicial
            requiere_inspeccion = True
            
        if requiere_inspeccion:
            llantas_activas = InventarioLlanta.objects.filter(unidad=unidad, activa=True)
            faltan_datos = False
            for llanta in llantas_activas:
                psi_val = self.data.get(f"psi_{llanta.id}")
                mm_val = self.data.get(f"mm_{llanta.id}")
                if not psi_val or not mm_val:
                    faltan_datos = True
                    break
                    
            if faltan_datos:
                raise forms.ValidationError("Criterio de seguridad alcanzado: Es obligatorio medir profundidad y presión para continuar.")
                
        return cleaned_data

from .models import Viaje

class ViajeForm(forms.ModelForm):
    class Meta:
        model = Viaje
        fields = [
            'unidad', 'operador', 'tipo_viaje', 'estado_actual',
            'zona', 'folio_nota_factura', 'km_salida', 'km_llegada',
            'hora_salida_cedis', 'hora_llegada_cedis'
        ]
        widgets = {
            'unidad': forms.Select(attrs={'class': 'form-select'}),
            'operador': forms.Select(attrs={'class': 'form-select'}),
            'tipo_viaje': forms.Select(attrs={'class': 'form-select'}),
            'estado_actual': forms.Select(attrs={'class': 'form-select'}),
            'zona': forms.Select(attrs={'class': 'form-select'}),
            'folio_nota_factura': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. F-1234, V-9876'}),
            'km_salida': forms.NumberInput(attrs={'class': 'form-control'}),
            'km_llegada': forms.NumberInput(attrs={'class': 'form-control'}),
            'hora_salida_cedis': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'hora_llegada_cedis': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }

from .models import InventarioLlanta

class InventarioLlantaForm(forms.ModelForm):
    class Meta:
        model = InventarioLlanta
        fields = [
            'unidad', 'posicion', 'marca', 'medida', 'numero_serie', 
            'profundidad_piso_mm', 'costo', 'fecha_instalacion', 'km_instalacion',
            'activa', 'observaciones'
        ]
        widgets = {
            'costo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fecha_instalacion': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Campos obligatorios según estandar v2
        for field_name in [
            'unidad', 'posicion', 'marca', 'medida', 'numero_serie', 
            'profundidad_piso_mm', 'fecha_instalacion', 'km_instalacion'
        ]:
            if field_name in self.fields:
                self.fields[field_name].required = True

from .models import EvaluacionEntrega

class EvaluacionEntregaForm(forms.ModelForm):
    class Meta:
        model = EvaluacionEntrega
        fields = [
            'cliente_satisfecho', 'motivo_insatisfaccion', 'tiempo_espera_cliente_minutos',
            'hubo_incidencia_transporte', 'desc_incidencia_transporte',
            'nombre_quien_recibe', 'comentarios'
        ]
        widgets = {
            'motivo_insatisfaccion': forms.Select(attrs={'class': 'form-select'}),
            'tiempo_espera_cliente_minutos': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'desc_incidencia_transporte': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'nombre_quien_recibe': forms.TextInput(attrs={'class': 'form-control'}),
            'comentarios': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            # Booleans can be rendered directly or styled manually in the template.
        }

from .models import ZonaEntrega

class ZonaEntregaForm(forms.ModelForm):
    class Meta:
        model = ZonaEntrega
        fields = [
            'nombre',
            'municipio',
            'codigos_postales',
            'colonias',
            'tiempo_traslado_minutos',
            'distancia_km',
            'tarifa_flete',
            'costo_maniobra',
            'color_hex',
            'geojson_data',
            'route_geojson',
            'route_waypoints',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control bg-light-subtle opacity-75', 
                'placeholder': 'Autogenerado...',
                'readonly': 'readonly'
            }),
            'municipio': forms.TextInput(attrs={
                'class': 'form-control bg-light-subtle opacity-75', 
                'placeholder': 'Autocalculado...',
                'readonly': 'readonly'
            }),
            'codigos_postales': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Ej. 50000, 50010, 50020 (Separados por coma)'}),
            'colonias': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Lista de colonias representativas'}),
            'tiempo_traslado_minutos': forms.NumberInput(attrs={
                'class': 'form-control bg-light-subtle opacity-75',
                'min': 0, 'readonly': 'readonly', 'placeholder': 'Auto'
            }),
            'distancia_km': forms.NumberInput(attrs={
                'class': 'form-control bg-light-subtle opacity-75',
                'min': 0, 'readonly': 'readonly', 'placeholder': 'Auto'
            }),
            'tarifa_flete': forms.NumberInput(attrs={
                'class': 'form-control bg-light-subtle opacity-75',
                'min': 0, 'readonly': 'readonly', 'placeholder': 'Auto'
            }),
            'costo_maniobra': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'color_hex': forms.TextInput(attrs={'class': 'form-control form-control-color', 'type': 'color'}),
            'geojson_data': forms.HiddenInput(attrs={'id': 'id_geojson_data'}),
            'route_geojson': forms.HiddenInput(attrs={'id': 'id_route_geojson'}),
            'route_waypoints': forms.HiddenInput(attrs={'id': 'id_route_waypoints'}),
        }

from .models import ConfiguracionGeneral

class ConfiguracionGeneralForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionGeneral
        fields = [
            'sueldo_semanal_chofer', 
            'sueldo_semanal_chalan', 
            'tiempo_descarga_promedio_min', 
            'limite_seguridad_llanta_mm', 
            'vida_util_estimada_llanta_km',
            'limite_peso_vehiculo_personal_kg',
            'tolerancia_peso_ruta_kg',
            'tipos_ticket_json'
        ]
        widgets = {
            'tipos_ticket_json': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Ej: [{"nombre": "Remisión", "prefijo": "R"}]'}),
            'sueldo_semanal_chofer': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'sueldo_semanal_chalan': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tiempo_descarga_promedio_min': forms.NumberInput(attrs={'class': 'form-control'}),
            'limite_seguridad_llanta_mm': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'vida_util_estimada_llanta_km': forms.NumberInput(attrs={'class': 'form-control'}),
            'limite_peso_vehiculo_personal_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tolerancia_peso_ruta_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

from .models import Cliente, Obra, Pedido, Despacho, ViajeNuevo, MensajeInterno, Operador, Proveedor

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['id_sae', 'razon_social', 'telefono_principal']
        widgets = {
            'id_sae': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ID de SAE (opcional)'}),
            'razon_social': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre Completo o Razón Social'}),
            'telefono_principal': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej. 55-12-34-56-78',
                'id': 'id_telefono_principal',
                'maxlength': '14'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = True
        self.fields['id_sae'].required = False

class ObraForm(forms.ModelForm):
    class Meta:
        model = Obra
        fields = [
            'alias', 'cliente', 'zona', 'cp', 'colonia', 'municipio',
            'calle_numero', 'entre_calles', 'referencias',
            'nombre_receptor', 'telefono_receptor', 'esta_activa',
            # zona_aprobada se gestiona vía <input type="hidden" value="on"> en el template
        ]
        widgets = {
            'alias': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Casa Blanca o Nombre del Despacho'}),
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'zona': forms.Select(attrs={'class': 'form-select', 'disabled': 'disabled'}),
            'cp': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 56200', 'id': 'id_cp', 'readonly': 'readonly'}),
            'colonia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Buscar Colonia...', 'id': 'id_colonia'}),
            # municipio: el JS lo marca readonly, aquí también lo ponemos readonly desde el inicio
            'municipio': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_municipio', 'readonly': 'readonly'}),
            'calle_numero': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Benito Juarez #123'}),
            'entre_calles': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Entre Hidalgo y Morelos'}),
            'referencias': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Ej. Portón negro grande, frente a la tienda, etc.'}),
            'nombre_receptor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la persona que recibe'}),
            'telefono_receptor': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. 55-12-34-56-78',
                'inputmode': 'numeric',
                'id': 'id_telefono_receptor',
                'maxlength': '14',  # 10 dígitos + 4 guiones
            }),
            'esta_activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # referencias es obligatorio
        self.fields['referencias'].required = True
        # nombre_receptor y telefono_receptor son opcionales pero con validaciones si se ingresan
        self.fields['nombre_receptor'].required = True    
        self.fields['telefono_receptor'].required = True

    def clean_nombre_receptor(self):
        import re
        nombre = self.cleaned_data.get('nombre_receptor', '').strip()
        if nombre:
            if len(nombre) < 3:
                raise forms.ValidationError("El nombre debe tener al menos 3 letras.")
            if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚüÜñÑ\s]+$', nombre):
                raise forms.ValidationError("El nombre solo puede contener letras.")
        return nombre

    def clean_telefono_receptor(self):
        import re
        val = self.cleaned_data.get('telefono_receptor') or ''
        telefono = val.strip()
        if telefono:
            # Quitamos cualquier cosa que no sea número
            solo_digitos = re.sub(r'\D', '', telefono)
            if len(solo_digitos) != 10:
                raise forms.ValidationError("El teléfono debe tener exactamente 10 números.")
            return solo_digitos
        return telefono

class PedidoForm(forms.ModelForm):
    tipo_ticket = forms.ChoiceField(
        label="Tipo", 
        required=True,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo_ticket'})
    )
    
    # Campos Virtuales para Nueva Obra (Vienen de la inclusión en pedido_form.html)
    alias = forms.CharField(required=False)
    zona = forms.ModelChoiceField(queryset=ZonaEntrega.objects.all(), required=False)
    calle_numero = forms.CharField(required=False)
    entre_calles = forms.CharField(required=False)
    colonia = forms.CharField(required=False)
    municipio = forms.CharField(required=False)
    cp = forms.CharField(required=False)
    referencias = forms.CharField(required=False, widget=forms.Textarea())
    nombre_receptor = forms.CharField(required=False)
    telefono_receptor = forms.CharField(required=False)

    class Meta:
        model = Pedido
        fields = [
            'tipo_ticket', 'folio_sae', 'cliente', 'obra', 'peso_total_estimado_kg', 'articulos_totales',
            'metodo_pago', 'es_urgente', 'maniobra_aceptada', 
            'cliente_nombre_manual', 'cliente_telefono_manual', 'cliente_direccion_manual',
            'observaciones_mostrador', 'evidencia_ticket'
        ]
        widgets = {
            'folio_sae': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de folio', 'pattern': '[0-9]*'}),
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'obra': forms.Select(attrs={'class': 'form-select'}),
            'peso_total_estimado_kg': forms.NumberInput(attrs={'class': 'form-control', 'min': '0.1', 'step': '0.1', 'required': 'required'}),
            'articulos_totales': forms.NumberInput(attrs={'class': 'form-control', 'min': '0.1', 'step': '0.1', 'required': 'required'}),
            'metodo_pago': forms.Select(attrs={'class': 'form-select', 'required': 'required'}),
            'es_urgente': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'maniobra_aceptada': forms.CheckboxInput(attrs={'class': 'form-check-input', 'required': 'required'}),
            'cliente_nombre_manual': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo'}),
            'cliente_telefono_manual': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
            'cliente_direccion_manual': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Dirección completa'}),
            'observaciones_mostrador': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Notas adicionales...'}),
            'evidencia_ticket': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        
    def _validate_extra_obra(self, cleaned_data):
        # Validaciones de los campos extra si se desea crear obra
        alias = cleaned_data.get('alias', '').strip()
        zona = cleaned_data.get('zona')
        calle = cleaned_data.get('calle_numero', '').strip()
        receptor = cleaned_data.get('nombre_receptor', '').strip()
        tel_receptor = cleaned_data.get('telefono_receptor', '').strip()
        
        if not alias: self.add_error('alias', "Especifique un alias para la dirección.")
        if not zona: self.add_error('zona', "La zona de entrega es obligatoria.")
        if not calle: self.add_error('calle_numero', "La calle y número son obligatorios.")
        if not receptor: self.add_error('nombre_receptor', "El nombre del receptor es obligatorio.")
        if not tel_receptor: self.add_error('telefono_receptor', "El teléfono del receptor es obligatorio.")
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cargar Tipos de Ticket desde Configuración General
        from .models import ConfiguracionGeneral
        config = ConfiguracionGeneral.get_solo()
        tipos = config.tipos_ticket_json or [
            {"nombre": "Remisión", "prefijo": "R"},
            {"nombre": "Nota de Venta", "prefijo": "N"},
            {"nombre": "Factura", "prefijo": "F"},
            {"nombre": "Cotización", "prefijo": "C"},
            {"nombre": "Nota de Block", "prefijo": "NB"}
        ]
        self.fields['tipo_ticket'].choices = [(t['prefijo'], t['nombre']) for t in tipos]

        # Campos obligatorios obligatorios para todos los casos
        self.fields['folio_sae'].required = True
        self.fields['peso_total_estimado_kg'].required = True
        self.fields['articulos_totales'].required = True
        self.fields['metodo_pago'].required = True
        
        # Cliente y Obra deben ser opcionales inicialmente porque 
        # pueden crearse manualmente sobre la marcha (Mostrador/Nuevo SAE)
        self.fields['cliente'].required = False
        self.fields['obra'].required = False
        self.fields['maniobra_aceptada'].required = True
        
        # Campos manuales para Mostrador
        self.fields['cliente_nombre_manual'].required = False
        self.fields['cliente_telefono_manual'].required = False
        self.fields['cliente_direccion_manual'].required = False

    def clean(self):
        cleaned_data = super().clean()
        cliente = cleaned_data.get('cliente')
        obra = cleaned_data.get('obra')
        evidencia = cleaned_data.get('evidencia_ticket')
        
        # Nombre y Teléfonos manuales
        nombre = cleaned_data.get('cliente_nombre_manual')
        telefono = cleaned_data.get('cliente_telefono_manual')
        direccion_manual = cleaned_data.get('cliente_direccion_manual')
        
        # Datos de la "Nueva Dirección" (desde el POST raw o virtuales)
        alias_obra = cleaned_data.get('alias', '').strip()
        colonia_obra = cleaned_data.get('colonia', '').strip()
        
        usar_obra_manual = self.data.get('usar_obra_manual') == 'true'
        
        # 0. VALIDACIÓN DE NUEVA OBRA (Si aplica)
        if usar_obra_manual:
            self._validate_extra_obra(cleaned_data)

        # 1. VALIDACIÓN DE CLIENTE (Si no hay SAE)
        if not cliente:
            id_sae_search = self.data.get('id_sae_search', '').strip()
            if not nombre:
                self.add_error('cliente_nombre_manual', "El nombre es obligatorio para registros sin cliente SAE.")
            if not telefono:
                self.add_error('cliente_telefono_manual', "El teléfono es obligatorio para registros sin cliente SAE.")
            elif nombre:
                # Mínimo 2 palabras si se escribe nombre
                import re
                if not re.match(r'^\s*\S+\s+\S+.*$', nombre):
                    self.add_error('cliente_nombre_manual', "Ingrese el nombre completo (mínimo nombre y un apellido).")
            
            if not telefono and not id_sae_search:
                self.add_error('cliente_telefono_manual', "El teléfono es obligatorio para clientes de Mostrador.")

        # 2. VALIDACIÓN DE OBRA / DIRECCIÓN
        # Permitimos: Una obra del catálogo O un alias de nueva obra O una dirección manual genérica
        if not obra and not alias_obra and not direccion_manual:
            self.add_error('obra', "Debes elegir una dirección, registrar una nueva obra o escribir la dirección manual.")

        # Ya no evaluamos recolección parcial mediante bandera en el form del Pedido.
        # Ahora se creará un Auto-Despacho desde la vista si el usuario elige.


        return cleaned_data

    def clean_cliente_telefono_manual(self):
        import re
        val = self.cleaned_data.get('cliente_telefono_manual') or ''
        tel = val.strip()
        if tel:
            # Quitamos guiones y espacios
            solo_numeros = re.sub(r'\D', '', tel)
            if len(solo_numeros) != 10:
                raise forms.ValidationError("El teléfono debe tener exactamente 10 dígitos.")
            return solo_numeros
        return tel

    def clean_folio_sae(self):
        folio = self.cleaned_data.get('folio_sae')
        prefijo = self.cleaned_data.get('tipo_ticket', '')
        if folio:
            import re
            # El usuario ingresa solo la parte numérica, nosotros concatenamos el prefijo inteligente
            folio_num = re.sub(r'\D', '', folio)
            if not folio_num:
                raise forms.ValidationError("El folio debe contener únicamente números.")
            
            # Concatenamos prefijo + número (Ej: R + 1234 = R1234)
            return f"{prefijo}{folio_num}"
        return folio

    def clean_peso_total_estimado_kg(self):
        peso = self.cleaned_data.get('peso_total_estimado_kg')
        if peso <= 0:
            raise forms.ValidationError("El peso debe ser un valor positivo mayor a cero.")
        return peso

    def clean_articulos_totales(self):
        articulos = self.cleaned_data.get('articulos_totales')
        if articulos <= 0:
            raise forms.ValidationError("Debe haber al menos un artículo en el pedido.")
        return articulos


class DespachoForm(forms.ModelForm):
    class Meta:
        model = Despacho
        fields = ['tipo_envio', 'peso_asignado_kg']
        widgets = {
            'tipo_envio': forms.Select(attrs={'class': 'form-select'}),
            'peso_asignado_kg': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class DespachoEntregaForm(forms.ModelForm):
    """Formulario para que el chofer cierre la entrega"""
    class Meta:
        model = Despacho
        fields = ['maniobra_especial', 'descripcion_maniobra', 'observaciones_entrega', 'foto_ticket_firmado']
        widgets = {
            'maniobra_especial': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'descripcion_maniobra': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'observaciones_entrega': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'foto_ticket_firmado': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class ViajeNuevoForm(forms.ModelForm):
    tipo_ruta_switch = forms.ChoiceField(
        choices=[
            ('INTERNA', 'Ruta Interna (Flotilla)'), 
            ('PERSONAL', 'Vehículo Personal (Moto/Auto)'),
            ('EXTERNA', 'Surtido Externo (Fletera)')
        ],
        widget=forms.RadioSelect(attrs={'class': 'btn-check'}),
        required=True, # v3.5: Obligatorio para evitar caídas en clean()
        initial='INTERNA'
    )
    # Campo temporal para filtro estricto de choferes aptos (Flotilla)
    chofer_flotilla = forms.ModelChoiceField(
        queryset=None, 
        required=False,
        label="Chofer Apto (Flotilla)",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = ViajeNuevo
        fields = ['fecha_viaje', 'unidad', 'vehiculo_personal_info', 'chofer', 'chalan', 'proveedor_servicio', 'proveedor_externo']
        widgets = {
            'fecha_viaje': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'unidad': forms.Select(attrs={'class': 'form-select'}),
            'vehiculo_personal_info': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Moto Honda o Mi Chevy'}),
            'chofer': forms.Select(attrs={'class': 'form-select'}),
            'chalan': forms.Select(attrs={'class': 'form-select'}),
            'proveedor_servicio': forms.Select(attrs={'class': 'form-select'}),
            'proveedor_externo': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth import get_user_model
        from .models import Unidad, Proveedor
        User = get_user_model()
        hoy = timezone.now().date()
        
        # 1. Filtro de Proveedores (Fleteros)
        self.fields['proveedor_servicio'].queryset = Proveedor.objects.filter(
            Q(especialidad='FLETES') | Q(especialidad='MERCANCIAS CON FLETE'),
            activo=True
        ).order_by('nombre_comercial')
        self.fields['proveedor_servicio'].empty_label = "--- Seleccione Proveedor ---"
        self.fields['proveedor_servicio'].required = False
        
        # 2. Filtro de Unidades
        self.fields['unidad'].queryset = Unidad.objects.filter(en_servicio=True).order_by('nUnidad')
        self.fields['unidad'].required = False
        
        # 3. Filtro de Choferes Flotilla (Requisitos estrictos)
        self.fields['chofer_flotilla'].queryset = User.objects.filter(
            Q(perfil_directorio__vigencia_licencia__gte=hoy) | Q(perfil_directorio__vigencia_licencia__isnull=True),
            is_active=True,
            perfil_directorio__licencia__isnull=False
        ).exclude(perfil_directorio__licencia="").select_related('perfil_directorio').order_by('perfil_directorio__nombre')
        
        self.fields['chofer_flotilla'].label_from_instance = lambda obj: f"✅ {obj.perfil_directorio.nombre}"

        # 4. Filtro de Choferes General (Para vehículo personal, más flexible)
        self.fields['chofer'].queryset = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
        self.fields['chofer'].label_from_instance = lambda obj: (
            obj.perfil_directorio.nombre if hasattr(obj, 'perfil_directorio') and obj.perfil_directorio 
            else (obj.get_full_name() or obj.username)
        )
        self.fields['chofer'].required = False
        
        # 5. Filtro de Chalanes
        self.fields['chalan'].queryset = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
        self.fields['chalan'].label_from_instance = lambda obj: (
            obj.perfil_directorio.nombre if hasattr(obj, 'perfil_directorio') and obj.perfil_directorio 
            else (obj.get_full_name() or obj.username)
        )
        self.fields['chalan'].required = False

        # Inicializar estado del switch
        if self.instance and self.instance.pk:
            if self.instance.proveedor_servicio:
                self.fields['tipo_ruta_switch'].initial = 'EXTERNA'
            elif self.instance.vehiculo_personal_info:
                self.fields['tipo_ruta_switch'].initial = 'PERSONAL'
            else:
                self.fields['tipo_ruta_switch'].initial = 'INTERNA'
                self.fields['chofer_flotilla'].initial = self.instance.chofer

    def clean(self):
        cleaned_data = super().clean()
        # v3.5: Asegurar que tipo_ruta_switch tenga siempre un valor (default INTERNA si falla el radio)
        tipo_ruta_switch = cleaned_data.get('tipo_ruta_switch') or self.data.get('tipo_ruta_switch') or 'INTERNA'
        
        chofer_flexible = cleaned_data.get('chofer')
        chofer_estricto = cleaned_data.get('chofer_flotilla')
        unidad = cleaned_data.get('unidad')
        vehiculo_info = cleaned_data.get('vehiculo_personal_info')
        proveedor_servicio = cleaned_data.get('proveedor_servicio')

        if tipo_ruta_switch == 'EXTERNA':
            if not proveedor_servicio:
                self.add_error('proveedor_servicio', "Debes seleccionar un proveedor del catálogo para flete externo.")
            cleaned_data['chofer'] = None
            cleaned_data['unidad'] = None
            cleaned_data['chalan'] = None
            cleaned_data['vehiculo_personal_info'] = None
            cleaned_data['proveedor_externo'] = None
            
        elif tipo_ruta_switch == 'PERSONAL':
            if not chofer_flexible:
                self.add_error('chofer', "Debes seleccionar un responsable para el vehículo personal.")
            if not vehiculo_info:
                self.add_error('vehiculo_personal_info', "Especifica la información del vehículo (Moto/Auto).")
            cleaned_data['chofer'] = chofer_flexible
            cleaned_data['unidad'] = None
            cleaned_data['proveedor_servicio'] = None
            cleaned_data['proveedor_externo'] = None
            
        else: # INTERNA (Flotilla)
            if not chofer_estricto:
                self.add_error('chofer_flotilla', "Selecciona un chofer apto para flotilla.")
            if not unidad:
                self.add_error('unidad', "Asigna una unidad de flotilla.")
            cleaned_data['chofer'] = chofer_estricto
            cleaned_data['vehiculo_personal_info'] = None
            cleaned_data['proveedor_servicio'] = None
            cleaned_data['proveedor_externo'] = None

        return cleaned_data

class MensajeInternoForm(forms.ModelForm):
    class Meta:
        model = MensajeInterno
        fields = ['destinatario', 'contenido']
        widgets = {
            'destinatario': forms.Select(attrs={'class': 'form-select'}),
            'contenido': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Escribe un mensaje...'}),
        }

class OperadorForm(forms.ModelForm):
    class Meta:
        model = Operador
        fields = ['nombre', 'puesto', 'telefono', 'email', 'licencia', 'vigencia_licencia', 'usuario_asociado', 'usa_sistema', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'puesto': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'licencia': forms.TextInput(attrs={'class': 'form-control'}),
            'vigencia_licencia': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'usuario_asociado': forms.Select(attrs={'class': 'form-select'}),
            'usa_sistema': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_usuario_asociado(self):
        usuario = self.cleaned_data.get('usuario_asociado')
        if usuario:
            # Revisa si este usuario ya está en OTRO operador
            qs = Operador.objects.filter(usuario_asociado=usuario)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise forms.ValidationError("Este usuario ya está asignado a otro colaborador en el directorio. Seleccione uno distinto.")
        return usuario

class DatabaseRestoreForm(forms.Form):
    backup_file = forms.FileField(
        label="Archivo de Respaldo (.sql)",
        help_text="Seleccione un archivo .sql generado previamente por el sistema.",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.sql'})
    )
    confirmacion = forms.BooleanField(
        label="Confirmo que deseo sobreescribir la base de datos actual",
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = [
            'nombre_comercial', 'razon_social', 'rfc', 'especialidad',
            'contacto_nombre', 'telefono', 'email', 'direccion', 'activo'
        ]
        widgets = {
            'nombre_comercial': forms.TextInput(attrs={'class': 'form-control'}),
            'razon_social': forms.TextInput(attrs={'class': 'form-control'}),
            'rfc': forms.TextInput(attrs={'class': 'form-control'}),
            'especialidad': forms.Select(attrs={'class': 'form-select'}),
            'contacto_nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
