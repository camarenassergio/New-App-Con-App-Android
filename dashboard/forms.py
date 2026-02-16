from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django import forms
from .models import Unidad, RegistroCombustible, Personal

User = get_user_model()

class PersonalCreationForm(UserCreationForm):
    # Campos adicionales de Personal
    nombre_completo = forms.CharField(max_length=150, label="Nombre Completo")
    puesto = forms.ChoiceField(choices=Personal.PUESTO_CHOICES, label="Puesto / Rol")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('nombre_completo', 'puesto',)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.save()
        
        # Crear perfil Personal
        Personal.objects.create(
            usuario=user,
            nombre_completo=self.cleaned_data['nombre_completo'],
            puesto=self.cleaned_data['puesto']
        )
        return user

class UnidadForm(forms.ModelForm):
    class Meta:
        model = Unidad
        fields = ['nombre_corto', 'placas', 'descripcion_vehiculo', 'no_serie', 'no_motor', 
                  'tarjeta_circulacion', 'vencimiento_placa', 'tipo_permiso_stc',
                  'nombre_aseguradora', 'tipo_cobertura_seguro', 'poliza_seguro', 'vencimiento_poliza',
                  'marca', 'submarca', 'modelo_anio', 'tipo', 'capacidad_kg', 'capacidad_tanque']
        widgets = {
            'fecha_adquisicion': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'vencimiento_placa': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'vencimiento_poliza': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'ultimo_pago_tenencia': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'vencimiento_verificacion': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

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
