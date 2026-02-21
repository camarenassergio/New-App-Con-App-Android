from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django import forms
from .models import Unidad, RegistroCombustible, Personal

User = get_user_model()

class PersonalCreationForm(UserCreationForm):
    # Campos adicionales de Personal
    nombre = forms.CharField(max_length=100, label="Nombre(s)")
    apellido_paterno = forms.CharField(max_length=100, label="Apellido Paterno")
    apellido_materno = forms.CharField(max_length=100, label="Apellido Materno", required=False)
    puesto = forms.ChoiceField(choices=Personal.PUESTO_CHOICES, label="Puesto / Rol")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('nombre', 'apellido_paterno', 'apellido_materno', 'puesto',)

    def save(self, commit=True):
        user = super().save(commit=False)
        # Populate User fields for better compatibility
        user.first_name = self.cleaned_data['nombre']
        user.last_name = f"{self.cleaned_data['apellido_paterno']} {self.cleaned_data.get('apellido_materno', '')}".strip()
        
        if commit:
            user.save()
            # Crear perfil Personal
            Personal.objects.create(
                usuario=user,
                nombre=self.cleaned_data['nombre'],
                apellido_paterno=self.cleaned_data['apellido_paterno'],
                apellido_materno=self.cleaned_data.get('apellido_materno', ''),
                puesto=self.cleaned_data['puesto']
            )
        return user

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
        ]
        widgets = {
            'fecha_adquisicion': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'vencimiento_placa': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'vencimiento_poliza': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'ultimo_pago_tenencia': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'vencimiento_verificacion': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }

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
            'chofer', 'motivo_multa', 
            'tipo_permiso', 'vigencia_permiso', 
            'kilometraje'
        ]
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'vigencia_permiso': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
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
            'tipo_permiso': forms.TextInput(attrs={'class': 'form-control'}),
            'evidencia': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

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
