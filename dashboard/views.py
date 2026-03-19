from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DetailView, DeleteView, View, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

User = get_user_model()
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.db.models import Sum, F, Q
from django.db.models.functions import TruncMonth
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.contrib import messages
import datetime
import calendar
import json
import os
from decimal import Decimal

from .models import (
    Unidad, Operador, Viaje, ConfiguracionLogistica, GastoUnidad,
    RegistroCombustible, Personal, OrdenServicio, ChecklistUnidad,
    InventarioLlanta, ConfiguracionGeneral, MedicionNeumatico,
    ZonaEntrega, Cliente, Obra, Pedido, Despacho, EvidenciaMaterial,
    ViajeNuevo, MensajeInterno
)
from .forms import (
    UnidadForm, RegistroCombustibleForm, PersonalCreationForm,
    GastoUnidadForm, CombustibleDeleteForm, UsuarioPerfilForm,
    OrdenServicioForm, ChecklistUnidadForm, ViajeForm,
    InventarioLlantaForm, EvaluacionEntregaForm, ZonaEntregaForm,
    ConfiguracionGeneralForm, ClienteForm, ObraForm, PedidoForm,
    DespachoForm, DespachoEntregaForm, ViajeNuevoForm, MensajeInternoForm
)

class AjaxSuccessMixin:
    """
    Mixin universal de éxito:
    - HTMX: redirige al cliente con HX-Redirect + dispara el toast vía HX-Trigger
    - Normal: agrega messages.success y redirige como siempre
    En ambos casos el usuario SOLO ve el toast en la esquina superior derecha.
    """
    ajax_success_message = "¡Registro guardado con éxito!"

    def form_valid(self, form):
        response = super().form_valid(form)

        # Aseguramos que el mensaje quede en el sistema de mensajes de Django
        # (Aplica tanto para HTMX como normal — el toast se renderiza en base.html)
        messages.success(self.request, self.ajax_success_message)

        if "HX-Request" in self.request.headers:
            # Para HTMX: redirigimos limpiamente con HX-Redirect.
            # NO renderizamos HTML intermedio → NO hay página de "éxito".
            # El toast se dispara porque el cliente sigue la redirección y
            # base.html renderiza los messages de Django al cargar la nueva página.
            from django.http import HttpResponse
            redirect_url = self.get_success_url()
            r = HttpResponse(status=204)       # 204 = No Content (no body needed)
            r["HX-Redirect"] = redirect_url   # HTMX navega allí inmediatamente
            return r

        return response


class NonChoferRequiredMixin(UserPassesTestMixin):

    def test_func(self):
        user = self.request.user
        if user.is_superuser: return True
        if not hasattr(user, 'personal'): return True # Fallback if no profile
        return user.personal.puesto != 'CHOFER'

class DashboardHomeView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser and hasattr(request.user, 'personal'):
            puesto = request.user.personal.puesto
            if puesto == 'CHOFER':
                return redirect('dashboard:viajes_list')
            elif puesto == 'MOSTRADOR':
                return redirect('dashboard:mostrador_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Totales Base
        context['total_unidades'] = Unidad.objects.count()
        
        # Desglose de Estado Actual
        # Unidades en Taller (Viaje activo de tipo TALLER)
        context['unidades_taller'] = Viaje.objects.filter(estado_actual='TRANSITO', tipo_viaje='TALLER').count()
        
        # Unidades en Ruta (Viaje activo que NO es TALLER)
        context['unidades_ruta'] = Viaje.objects.filter(estado_actual='TRANSITO').exclude(tipo_viaje='TALLER').count()
        
        # Unidades Disponibles (Total Activas - (Ruta + Taller))
        # Asumiendo que 'en_servicio' de la Unidad es el flag de "Dada de Alta en la empresa"
        total_activas = Unidad.objects.filter(en_servicio=True).count()
        context['unidades_disponibles'] = total_activas - (context['unidades_taller'] + context['unidades_ruta'])

        # Mantener compatibilidad si se usaba antes
        context['viajes_activos'] = Viaje.objects.filter(estado_actual='TRANSITO').count()
        
        # Alerts (Example logic)
        context['alertas'] = []
        contingencia = ConfiguracionLogistica.objects.first()
        if contingencia and contingencia.estado_contingencia != 'NORMAL':
            context['alertas'].append({
                'nivel': 'danger', 
                'mensaje': f"CONTINGENCIA ACTIVA: {contingencia.get_estado_contingencia_display()}"
            })

        from .models import InventarioLlanta, ConfiguracionGeneral
        config = ConfiguracionGeneral.get_solo()
        
        llantas_activas = InventarioLlanta.objects.filter(activa=True).select_related('unidad')
        for llanta in llantas_activas:
            # Alerta de desgaste acelerado por tasa
            if llanta.observaciones and "Desgaste Acelerado" in llanta.observaciones:
                context['alertas'].append({
                    'nivel': 'danger',
                    'mensaje': f"🚨 DESGASTE ACELERADO: {llanta.unidad.nUnidad} - {llanta.get_posicion_display()}. {llanta.observaciones}"
                })
            elif llanta.observaciones and "Disparidad Detectada" in llanta.observaciones:
                context['alertas'].append({
                    'nivel': 'warning',
                    'mensaje': f"⚠️ ALERTA ALINEACIÓN/PRESIÓN: {llanta.unidad.nUnidad} - Eje {llanta.get_posicion_display()}. {llanta.observaciones}"
                })
            elif llanta.observaciones and "Desgaste Alta" in llanta.observaciones:
                context['alertas'].append({
                    'nivel': 'warning',
                    'mensaje': f"⚠️ DESGASTE ALTO: {llanta.unidad.nUnidad} - {llanta.get_posicion_display()}. {llanta.observaciones}"
                })

            # Riesgo por profundidad de piso
            if llanta.profundidad_piso_mm <= config.limite_seguridad_llanta_mm:
                context['alertas'].append({
                    'nivel': 'danger',
                    'mensaje': f"⚠️ ALERTA DE LLANTA: La unidad {llanta.unidad.nUnidad} alcanzó el límite de seguridad ({llanta.profundidad_piso_mm} mm) en la llanta {llanta.get_posicion_display()}. Requiere cambio urgente."
                })
            elif llanta.profundidad_piso_mm <= (config.limite_seguridad_llanta_mm + 2):
                context['alertas'].append({
                    'nivel': 'warning',
                    'mensaje': f"🔔 PREVENCIÓN DE LLANTA: La unidad {llanta.unidad.nUnidad} está cerca del límite de seguridad ({llanta.profundidad_piso_mm} mm) en la llanta {llanta.get_posicion_display()}. Considere prever el cambio."
                })
            else:
                # Riesgo por kilometraje
                km_recorridos = llanta.unidad.kilometraje_actual - llanta.km_instalacion
                if km_recorridos >= 0:
                    km_restantes = config.vida_util_estimada_llanta_km - km_recorridos
                    if km_restantes < 5000:  # Umbral de aviso preventivo de 5,000 km
                        context['alertas'].append({
                            'nivel': 'warning',
                            'mensaje': f"🔔 PREVENCIÓN DE LLANTA: La unidad {llanta.unidad.nUnidad} está a {km_restantes} km de superar la vida útil estimada en su llanta {llanta.get_posicion_display()}."
                        })

        # --- DATOS PARA GRÁFICAS ---
        import json
        from django.db.models import Sum, Count, Max, Min
        today = timezone.now().date()
        
        # 1. Gasto Mensual Desglosado (Últimos 6 meses)
        import dateutil.relativedelta
        from collections import defaultdict
        
        meses_keys = []
        for i in range(5, -1, -1):
            m_date = today - dateutil.relativedelta.relativedelta(months=i)
            m_date = m_date.replace(day=1)
            meses_keys.append(m_date)
            
        six_months_ago = meses_keys[0]
        
        combustible_qs = RegistroCombustible.objects.filter(fecha__gte=six_months_ago)\
            .annotate(month=TruncMonth('fecha'))\
            .values('month')\
            .annotate(total_gasto=Sum('total'))\
            .order_by('month')
            
        otros_gastos_qs = GastoUnidad.objects.filter(fecha__gte=six_months_ago)\
            .annotate(month=TruncMonth('fecha'))\
            .values('month', 'tipo')\
            .annotate(total_gasto=Sum('costo'))\
            .order_by('month')
            
        data_matrix = defaultdict(lambda: defaultdict(float))
        
        def to_month_key(date_obj):
            if isinstance(date_obj, datetime.datetime):
                return date_obj.date().replace(day=1)
            return date_obj.replace(day=1)

        for item in combustible_qs:
            m = to_month_key(item['month'])
            data_matrix[m]['Combustible'] += float(item['total_gasto'] or 0)
            
        for item in otros_gastos_qs:
            m = to_month_key(item['month'])
            tipo = item['tipo']
            data_matrix[m][tipo] += float(item['total_gasto'] or 0)
            
        from .utils import MESES_ES
        labels_gasto = []
        for m in meses_keys:
            nombre_mes = MESES_ES.get(m.month, '')[:3]
            labels_gasto.append(f"{nombre_mes} {m.year}")
            
        tipos_gastos_registrados = set(['Combustible']) # Siempre asegurar que exista aunque en 0
        for val_dict in data_matrix.values():
            tipos_gastos_registrados.update(val_dict.keys())
            
        color_palette = {
            'Combustible': '#e65100', 'Verificación': '#28a745', 'Mantenimiento': '#17a2b8',
            'Seguro': '#6f42c1', 'Multa': '#dc3545', 'Peaje': '#ffc107',
            'Tenencia': '#fd7e14', 'Permiso': '#20c997', 'Placas': '#6c757d', 'Otro': '#343a40'
        }
        
        datasets = []
        for tipo in tipos_gastos_registrados:
            data_arr = [data_matrix[m].get(tipo, 0.0) for m in meses_keys]
            if sum(data_arr) > 0:
                color = color_palette.get(tipo, '#007bff')
                datasets.append({
                    'label': tipo,
                    'data': data_arr,
                    'backgroundColor': color,
                    'borderRadius': 4
                })
                
        context['chart_gasto_labels'] = json.dumps(labels_gasto)
        context['chart_gasto_datasets'] = json.dumps(datasets)
        
        # 2. Top Consumo Litros (Mes Actual)
        consumo_mes_qs = RegistroCombustible.objects.filter(fecha__year=today.year, fecha__month=today.month)\
            .values('unidad__nUnidad', 'unidad__nombre_corto')\
            .annotate(total_litros=Sum('litros'))\
            .order_by('-total_litros')[:5]
            
        labels_consumo = []
        data_consumo = []
        for item in consumo_mes_qs:
            # Preferir nombre corto si existe, sino nUnidad
            name = item['unidad__nombre_corto'] if item['unidad__nombre_corto'] else item['unidad__nUnidad']
            labels_consumo.append(name)
            data_consumo.append(float(item['total_litros']))
            
        context['chart_consumo_labels'] = json.dumps(labels_consumo)
        context['chart_consumo_data'] = json.dumps(data_consumo)

        # 3. Rendimiento Promedio (Estimado - Año en curso)
        # Aproximación: (Max Km - Min Km) / Sum(Litros) en el año actual
        # Esto es más rápido que iterar registro por registro
        rendimiento_data = []
        unidades_activas = Unidad.objects.filter(en_servicio=True)
        
        unidades_rendimiento = []
        valores_rendimiento = []
        colores_rendimiento = []
        
        for u in unidades_activas:
            # Filtrar registros de este año
            regs_anio = RegistroCombustible.objects.filter(unidad=u, fecha__year=today.year)
            if regs_anio.exists():
                agregados = regs_anio.aggregate(
                    min_km=Min('kilometraje_actual'),
                    max_km=Max('kilometraje_actual'),
                    total_litros=Sum('litros')
                )
                
                if agregados['max_km'] and agregados['min_km'] and agregados['total_litros'] and agregados['total_litros'] > 0:
                    delta_km = agregados['max_km'] - agregados['min_km']
                    if delta_km > 0:
                        km_l = delta_km / float(agregados['total_litros'])
                        # Filtrar outliers (ej: > 15 km/l en camión es error, < 1 km/l también)
                        if 0.5 < km_l < 25: 
                            unidades_rendimiento.append(u.nombre_corto or u.nUnidad)
                            valores_rendimiento.append(round(km_l, 2))
                            # Color coding básico
                            if km_l > 4.5: colores_rendimiento.append('#28a745') # Verde
                            elif km_l < 2.5: colores_rendimiento.append('#dc3545') # Rojo
                            else: colores_rendimiento.append('#ffc107') # Amarillo
        
        context['chart_rendimiento_labels'] = json.dumps(unidades_rendimiento)
        context['chart_rendimiento_data'] = json.dumps(valores_rendimiento)
        context['chart_rendimiento_colors'] = json.dumps(colores_rendimiento)

        return context

class UnidadListView(LoginRequiredMixin, NonChoferRequiredMixin, ListView):
    model = Unidad
    template_name = "dashboard/unidad_list.html"
    context_object_name = "unidades"

from .forms import UnidadForm

class UnidadCreateView(LoginRequiredMixin, NonChoferRequiredMixin, AjaxSuccessMixin, CreateView):
    model = Unidad
    form_class = UnidadForm
    template_name = "dashboard/unidad_form.html"
    success_url = reverse_lazy('dashboard:unidades_list')
    ajax_success_message = "¡Unidad registrada con éxito!"

class UnidadUpdateView(LoginRequiredMixin, NonChoferRequiredMixin, AjaxSuccessMixin, UpdateView):
    model = Unidad
    form_class = UnidadForm
    template_name = "dashboard/unidad_form.html"
    success_url = reverse_lazy('dashboard:unidades_list')
    ajax_success_message = "¡Unidad actualizada con éxito!"

class UnidadDetailView(LoginRequiredMixin, NonChoferRequiredMixin, DetailView):
    model = Unidad
    template_name = "dashboard/unidad_detail.html"
    context_object_name = "unidad"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import InventarioLlanta
        llantas_activas = InventarioLlanta.objects.filter(unidad=self.object, activa=True)
        llantas_dic = {}
        for ll in llantas_activas:
            estado = "success"
            if ll.profundidad_piso_mm <= 3.0:
                 estado = "danger"
            llantas_dic[ll.posicion] = {
                'id': ll.id,
                'profundidad': float(ll.profundidad_piso_mm),
                'marca': ll.marca,
                'estado': estado,
                'obj': ll
            }
            
        # Comparación por eje y gemelas para colorear en amarillo
        # Parejas de Eje
        parejas_eje = [('DI1', 'DD1'), ('TI1', 'TD1'), ('TI2', 'TD2')]
        # Gemelas
        gemelas = [('TI1', 'TI2'), ('TD1', 'TD2')]
        
        for izq, der in (parejas_eje + gemelas):
            if izq in llantas_dic and der in llantas_dic:
                diff = abs(llantas_dic[izq]['profundidad'] - llantas_dic[der]['profundidad'])
                if diff > 1.5:
                    if llantas_dic[izq]['estado'] != 'danger':
                         llantas_dic[izq]['estado'] = 'warning'
                    if llantas_dic[der]['estado'] != 'danger':
                         llantas_dic[der]['estado'] = 'warning'

        context['esquema_llantas'] = llantas_dic
        return context

from django.views import View

class UnidadToggleEstadoView(LoginRequiredMixin, NonChoferRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        from django.shortcuts import get_object_or_404
        unidad = get_object_or_404(Unidad, pk=pk)
        unidad.en_servicio = not unidad.en_servicio
        unidad.save()

        # HTMX: devuelve solo la fila actualizada (hx-swap="outerHTML" en closest tr)
        if "HX-Request" in request.headers:
            from django.template.loader import render_to_string
            estado_badge = (
                f'<button type="button" '
                f'class="badge bg-success border-0 px-3 py-2 rounded-pill" '
                f'hx-post="/dashboard/unidades/{unidad.pk}/toggle/" '
                f'hx-target="closest tr" hx-swap="outerHTML" '
                f'hx-headers=\'{{"X-CSRFToken": "{request.META.get("CSRF_COOKIE", "")}"}}\' '
                f'hx-confirm="Dar de BAJA TEMPORAL a {unidad.nombre_corto or unidad.nUnidad}. ¿Continuar?" '
                f'title="En servicio. Clic para dar de baja temporal">'
                f'<i class="fas fa-toggle-on me-1"></i> Activa</button>'
                if unidad.en_servicio else
                f'<button type="button" '
                f'class="badge bg-danger border-0 px-3 py-2 rounded-pill" '
                f'hx-post="/dashboard/unidades/{unidad.pk}/toggle/" '
                f'hx-target="closest tr" hx-swap="outerHTML" '
                f'hx-headers=\'{{"X-CSRFToken": "{request.META.get("CSRF_COOKIE", "")}"}}\' '
                f'hx-confirm="REACTIVAR la unidad {unidad.nombre_corto or unidad.nUnidad}. ¿Continuar?" '
                f'title="En taller. Clic para reactivar">'
                f'<i class="fas fa-toggle-off me-1"></i> Inactiva</button>'
            )
            # Devolvemos solo la celda de estado actualizada dentro de la fila
            # El cliente reemplaza el <tr> completo con hx-swap="outerHTML"
            messages.success(request, f"Unidad {unidad.nUnidad} {'reactivada' if unidad.en_servicio else 'dada de baja temporal'}.")
            r = HttpResponse(status=204)
            r["HX-Redirect"] = "/dashboard/unidades/"
            return r

        messages.success(request, f"Unidad {unidad.nUnidad} {'reactivada' if unidad.en_servicio else 'dada de baja temporal'}.")
        return redirect('dashboard:unidades_list')

class OperadorListView(LoginRequiredMixin, NonChoferRequiredMixin, ListView):

    model = Operador
    template_name = "dashboard/operador_list.html"
    context_object_name = "operadores"

class OperadorCreateView(LoginRequiredMixin, NonChoferRequiredMixin, AjaxSuccessMixin, CreateView):
    model = Operador
    fields = ['nombre', 'puesto', 'telefono', 'email', 'licencia', 'vigencia_licencia', 'usuario_asociado', 'usa_sistema', 'activo']
    template_name = "dashboard/operador_form.html"
    success_url = reverse_lazy('dashboard:operadores_list')
    ajax_success_message = "Registro añadido al directorio correctamente."

class OperadorUpdateView(LoginRequiredMixin, NonChoferRequiredMixin, AjaxSuccessMixin, UpdateView):
    model = Operador
    fields = ['nombre', 'puesto', 'telefono', 'email', 'licencia', 'vigencia_licencia', 'usuario_asociado', 'usa_sistema', 'activo']
    template_name = "dashboard/operador_form.html"
    success_url = reverse_lazy('dashboard:operadores_list')
    ajax_success_message = "Registro actualizado correctamente."

class ViajeListView(LoginRequiredMixin, ListView):
    model = Viaje
    template_name = "dashboard/viaje_list.html"
    context_object_name = "viajes"

from .forms import ViajeForm
from django.urls import reverse_lazy
from django.contrib import messages

class ViajeCreateView(LoginRequiredMixin, AjaxSuccessMixin, CreateView):
    model = Viaje
    form_class = ViajeForm
    template_name = "dashboard/viaje_form.html"
    success_url = reverse_lazy('dashboard:viajes_list')
    ajax_success_message = "¡Viaje programado correctamente!"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Viaje programado correctamente.")
        return response

class ViajeUpdateView(LoginRequiredMixin, AjaxSuccessMixin, UpdateView):
    model = Viaje
    form_class = ViajeForm
    template_name = "dashboard/viaje_form.html"
    success_url = reverse_lazy('dashboard:viajes_list')
    ajax_success_message = "¡Viaje actualizado correctamente!"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Viaje actualizado correctamente.")
        return response

from .models import Unidad, Operador, Viaje, ConfiguracionLogistica, RegistroCombustible, Personal
from .forms import UnidadForm, RegistroCombustibleForm, PersonalCreationForm

class UsuarioCreateView(LoginRequiredMixin, NonChoferRequiredMixin, AjaxSuccessMixin, CreateView):
    model = User
    form_class = PersonalCreationForm
    template_name = "dashboard/usuario_form.html"
    success_url = reverse_lazy('dashboard:usuarios_list')
    ajax_success_message = "¡Usuario registrado correctamente!"

class CombustibleCreateView(LoginRequiredMixin, AjaxSuccessMixin, CreateView):
    model = RegistroCombustible
    form_class = RegistroCombustibleForm
    template_name = "dashboard/combustible_form.html"
    success_url = reverse_lazy('dashboard:combustible_general') 
    ajax_success_message = "¡Registro de combustible guardado!"

    def form_valid(self, form):
        unidad = form.cleaned_data['unidad']
        nuevo_kilometraje = form.cleaned_data['kilometraje_actual']

        # Validación: El kilometraje no puede ser menor al actual
        if nuevo_kilometraje < unidad.kilometraje_actual:
            form.add_error('kilometraje_actual', f"El kilometraje no puede ser menor al actual ({unidad.kilometraje_actual} km).")
            return self.form_invalid(form)

        # Asignar usuario y fecha
        form.instance.chofer = self.request.user
        form.instance.fecha = timezone.now().date()
        
        # Guardar el registro de combustible
        response = super().form_valid(form)
        
        # Actualizar el kilometraje de la unidad
        unidad.kilometraje_actual = nuevo_kilometraje
        unidad.save()
        
        return response

class CombustibleUpdateView(LoginRequiredMixin, AjaxSuccessMixin, UpdateView):
    model = RegistroCombustible
    form_class = RegistroCombustibleForm
    template_name = "dashboard/combustible_form.html"
    success_url = reverse_lazy('dashboard:combustible_general')
    ajax_success_message = "¡Registro de combustible actualizado!"

    def get_success_url(self):
        # Redirect back to the unit detail if possible
        if self.object.unidad:
            return reverse_lazy('dashboard:combustible_unidad_detail', kwargs={'pk': self.object.unidad.pk})
        return super().get_success_url()

    def dispatch(self, request, *args, **kwargs):
        # Permission Check
        user = request.user
        if not user.is_authenticated:
            return self.handle_no_permission()

        # 1. Must be Admin (Superuser or puesto='ADMIN')
        is_admin = user.is_superuser or (hasattr(user, 'personal') and user.personal.puesto == 'ADMIN')
        if not is_admin:
             # Opcional: Redirigir o mostrar 403
             from django.core.exceptions import PermissionDenied
             raise PermissionDenied("Solo administradores pueden editar registros.")

        # 2. Date Logic
        # Get object
        obj = self.get_object()
        log_date = obj.fecha
        today = timezone.now().date()
        
        # Calculate date difference
        # allowed: 
        # - Same month/year
        # - Previous month IF today.day < 17
        
        can_edit = False
        
        if log_date.year == today.year and log_date.month == today.month:
            can_edit = True
        else:
            # Check previous month
            first_day_this_month = today.replace(day=1)
            last_day_prev_month = first_day_this_month - datetime.timedelta(days=1)
            
            if log_date.year == last_day_prev_month.year and log_date.month == last_day_prev_month.month:
                if today.day < 17:
                    can_edit = True
        
        if not can_edit:
             from django.core.exceptions import PermissionDenied
             raise PermissionDenied("El periodo de edición para este registro ha expirado.")
             
        return super().dispatch(request, *args, **kwargs)

class UsuarioListView(LoginRequiredMixin, NonChoferRequiredMixin, ListView):
    model = User
    template_name = "dashboard/usuario_list.html"
    context_object_name = "usuarios"

class CombustibleGeneralView(LoginRequiredMixin, NonChoferRequiredMixin, TemplateView):
    template_name = "dashboard/combustible_general.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        from .utils import MESES_ES, get_month_name

        # Estructura para acumular datos por (Mes, Año) -> Lista de datos por Unidad
        # reporte_raw[(year, month)][unidad_id] = { 'litros': 0, 'costo': 0, 'km_recorridos': 0, 'unidad_obj': ... }
        from collections import defaultdict
        reporte_raw = defaultdict(lambda: defaultdict(lambda: {'litros': 0.0, 'costo': 0.0, 'km_recorridos': 0, 'total_global': 0.0}))
        
        # Obtener todas las unidades para asegurar que aparezcan
        unidades = {u.id: u for u in Unidad.objects.all()}
        
        # Obtener registros ordenados para cálculo secuencial de Km
        registros = RegistroCombustible.objects.select_related('unidad').order_by('unidad', 'fecha', 'kilometraje_actual')
        
        # Lógica secuencial para Km
        prev_reg = None
        for reg in registros:
            # Detectar cambio de unidad
            if prev_reg and prev_reg.unidad_id != reg.unidad_id:
                prev_reg = None
            
            km_recorrido = 0
            if prev_reg:
                diff = reg.kilometraje_actual - prev_reg.kilometraje_actual
                if diff > 0:
                    km_recorrido = diff
            
            # Asignar al mes del registro actual
            anio = reg.fecha.year
            mes = reg.fecha.month
            u_id = reg.unidad_id
            
            # Inicializar objeto unidad si no está (por si acaso select_related falla o algo, aunque usamos dict unidades)
            if 'unidad_obj' not in reporte_raw[(anio, mes)][u_id]:
                reporte_raw[(anio, mes)][u_id]['unidad_obj'] = unidades.get(u_id)

            # Acumular
            # Costo Combustible = (Litros * Precio) -> Esto es lo que paga de GASOLINA
            # Total Global = Costo Combustible + Propina -> Esto es lo que sale de la caja chica/tarjeta
            
            costo_combustible_puro = float(reg.litros) * float(reg.precio_litro)
            propina = float(reg.propina)
            total_real = float(reg.total) # Esto debería ser la suma, pero confiamos en DB o recalculamos si se prefiere
            
            # Si el usuario dice que "costo combustible y total tienen mismos valores y no debería",
            # es porque en la versión anterior usé reg.total para ambos.
            # Ahora:
            # costo = costo_combustible_puro
            # total = total_real (que incluye propina)
            
            reporte_raw[(anio, mes)][u_id]['litros'] += float(reg.litros)
            reporte_raw[(anio, mes)][u_id]['costo'] += costo_combustible_puro
            reporte_raw[(anio, mes)][u_id]['km_recorridos'] += km_recorrido
            reporte_raw[(anio, mes)][u_id]['total_global'] += total_real
            
            prev_reg = reg

        
        # --- FILTROS DE FECHA AVANZADOS ---
        # Parametros: mes_inicio, anio_inicio, mes_fin, anio_fin
        
        # 1. Obtener Años Disponibles
        fechas_registros = RegistroCombustible.objects.dates('fecha', 'year', order='DESC')
        anios_disponibles = [d.year for d in fechas_registros]
        
        today = timezone.now().date()
        current_year = today.year
        if not anios_disponibles:
            anios_disponibles = [current_year]
        if current_year not in anios_disponibles:
             anios_disponibles.insert(0, current_year)
             
        # 2. Obtener Valores del Request (o Defaults)
        try:
            r_mes_inicio = int(self.request.GET.get('mes_inicio', 1))
            r_anio_inicio = int(self.request.GET.get('anio_inicio', current_year))
            r_mes_fin = int(self.request.GET.get('mes_fin', 12))
            r_anio_fin = int(self.request.GET.get('anio_fin', current_year))
        except ValueError:
            # Fallback en caso de basura en URL
            r_mes_inicio = 1
            r_anio_inicio = current_year
            r_mes_fin = 12
            r_anio_fin = current_year
            
        # 3. Construir Fechas de Rango
        import calendar
        try:
            start_date = datetime.date(r_anio_inicio, r_mes_inicio, 1)
            
            last_day_fin = calendar.monthrange(r_anio_fin, r_mes_fin)[1]
            end_date = datetime.date(r_anio_fin, r_mes_fin, last_day_fin)
        except ValueError:
             # Caso raro (ej: mes 13), fallback a todo el año actual
            start_date = datetime.date(current_year, 1, 1)
            end_date = datetime.date(current_year, 12, 31)

        # 4. Pasar Contexto para los Selects
        context['anios_disponibles'] = anios_disponibles
        context['meses_range'] = range(1, 13) # Para iterar 1..12 en template
        context['filtros'] = {
            'mes_inicio': r_mes_inicio,
            'anio_inicio': r_anio_inicio,
            'mes_fin': r_mes_fin,
            'anio_fin': r_anio_fin
        }
        
        # 5. Filtrar el Diccionario Raw (Ya poblado)
        # Nota: La lógica ideal sería filtrar 'registros' en la query de DB L212, 
        # PERO necesitamos 'registros' previos para el cálculo secuencial de diferencia de KM.
        # Si filtramos DB, perdemos el registro anterior al rango que nos da el Km inicial.
        # ESTRATEGIA: Calcular todo (como ya se hace) y filtrar AL FINAL el reporte_raw.

        keys_to_remove = []
        for (y, m) in reporte_raw.keys():
            # Crear fecha representativa del mes (día 1) para comparar
            mes_date = datetime.date(y, m, 1)
            
            # Comparar mes_date con start_date (YYYY-MM-01) 
            # Para end_date, comparamos el mes_date (inicio de mes) con end_date 
            # PERO end_date es fin de mes.
            # Lógica: 
            # Si mes_date < start_date (mismo año/mes): Fuera
            # Si mes_date > end_date: Fuera.
            
            # Ajuste: start_date es 1/Nov/2025. Un registro de Nov 2025 (1/Nov) >= start_date -> True.
            # end_date es 28/Feb/2026. Un registro de Feb 2026 (1/Feb) <= end_date -> True.
            
            if mes_date < start_date or mes_date > end_date:
                keys_to_remove.append((y, m))
                
        for k in keys_to_remove:
            del reporte_raw[k]

        # Construir reporte final ordenado cronológicamente descendente
        claves_meses = sorted(reporte_raw.keys(), reverse=True) # [(2025, 8), (2025, 7), ...]
        
        reporte_final = []
        
        for (anio, mes) in claves_meses:
            # Filtrado por Rango de Fechas (ya se hizo al eliminar keys de reporte_raw)
            # fecha_mes_inicio = datetime.date(anio, mes, 1)
            # if start_date and fecha_mes_inicio < start_date:
            #     continue
            # if end_date and fecha_mes_inicio > end_date:
            #     continue
                
            datos_mes = reporte_raw[(anio, mes)]
            filas_mes = []
            
            totals_mes = { 'litros': 0.0, 'combustible': 0.0, 'total_global': 0.0, 'km': 0 }
            
            # Iterar sobre todas las unidades para este mes (o solo las que tuvieron actividad)
            # El usuario quiere ver desglose, asumimos solo las que tuvieron actividad para no llenar de ceros
            # Si se requiere ver todas, iterar sobre `unidades` y hacer get de datos_mes
            
            for u_id, data in datos_mes.items():
                unidad = data['unidad_obj']
                if not unidad: continue # Skip si no hay unidad asociada

                filas_mes.append({
                    'unidad': unidad,
                    'litros': data['litros'],
                    'costo_combustible': data['costo'],
                    'km_recorridos': data['km_recorridos'], # Este es el KM DEL MES, no el actual
                    'total': data['total_global'],
                    'pct_consumo': 0 # Se calcula abajo
                })
                
                totals_mes['litros'] += data['litros']
                totals_mes['combustible'] += data['costo']
                totals_mes['km'] += data['km_recorridos']
                totals_mes['total_global'] += data['total_global']
            
            # Calcular porcentajes
            for fila in filas_mes:
                if totals_mes['combustible'] > 0:
                    fila['pct_consumo'] = (fila['costo_combustible'] / totals_mes['combustible']) * 100
            
            # Ordenar filas por unidad (opcional)
            filas_mes.sort(key=lambda x: x['unidad'].nUnidad)

            nombre_mes = f"{MESES_ES.get(mes, 'DESCONOCIDO')} {anio}"
            
            reporte_final.append({
                'mes_nombre': nombre_mes,
                'filas': filas_mes,
                'totales': totals_mes
            })

        context['reporte_mensual'] = reporte_final
        return context

class CombustibleUnidadDetailView(LoginRequiredMixin, NonChoferRequiredMixin, DetailView):
    model = Unidad
    template_name = "dashboard/combustible_unidad_detail.html"
    context_object_name = "unidad"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        unidad = self.object
        
        # Obtener registros ordenados cronológicamente
        registros = RegistroCombustible.objects.filter(unidad=unidad).order_by('fecha', 'kilometraje_actual')
        
        # Calcular Km entre cargas y Rendimiento
        from .utils import MESES_ES, get_month_name
        
        
        tabla_registros = []
        # Logic for editing permission
        today = timezone.now().date()
        first_day_this_month = today.replace(day=1)
        last_day_prev_month = first_day_this_month - datetime.timedelta(days=1)
        is_admin = self.request.user.is_superuser or (hasattr(self.request.user, 'personal') and self.request.user.personal.puesto == 'ADMIN')

        # Totales Históricos (Tabla)
        totales_historicos = {
            'cargas': 0, 'litros': 0, 'costo': 0, 'propina': 0
        }
        
        # Totales Mes Actual (Tarjetas)
        totales_mes_actual = {
            'cargas': 0, 'litros': 0, 'costo': 0, 'propina': 0
        }
        
        # Iteramos una sola vez para eficiencia
        previous_reg = None
        
        for i, reg in enumerate(registros):
            km_entre_cargas = 0
            rendimiento = 0
            
            if previous_reg:
                # Ojo: aquí suponemos que no hay gaps ni resets. Si odo < prev_odo, asumimos reinicio? 
                # Por ahora lógica original: si negativo -> 0
                diff = reg.kilometraje_actual - previous_reg.kilometraje_actual
                if diff > 0:
                    km_entre_cargas = diff
                 
                # Rendimiento = Km recorridos / Litros cargados en ESTA carga 
                # (Asumiendo que esta carga repuso lo consumido en esos Km)
                if reg.litros > 0:
                    rendimiento = km_entre_cargas / float(reg.litros)
            
            # Check edit permission per row
            puede_editar = False
            es_reciente = False
            
            # Logic for "Recency" (Current Month or Prev Month < 17th)
            if reg.fecha.year == today.year and reg.fecha.month == today.month:
                es_reciente = True
            elif reg.fecha.year == last_day_prev_month.year and reg.fecha.month == last_day_prev_month.month:
                if today.day < 17:
                    es_reciente = True

            if is_admin and es_reciente:
                puede_editar = True

            tabla_registros.append({
                'id': reg.id,
                'numero': i + 1,
                'fecha': reg.fecha,
                'chofer': reg.chofer.get_full_name() or reg.chofer.username,
                'kilometraje': reg.kilometraje_actual,
                'km_entre_cargas': km_entre_cargas,
                'litros': reg.litros,
                'rendimiento': rendimiento,
                'precio_litro': reg.precio_litro,
                'total': reg.total,
                'propina': reg.propina,
                'observaciones': reg.observaciones,
                'evidencia_antes': reg.evidencia_antes,
                'evidencia_despues': reg.evidencia_despues,
                'puede_editar': puede_editar,
                'es_reciente': es_reciente
            })
            
            # Acumular Histórico
            totales_historicos['cargas'] += 1
            totales_historicos['litros'] += float(reg.litros)
            totales_historicos['costo'] += float(reg.total)
            totales_historicos['propina'] += float(reg.propina)
            
            # Acumular Mes Actual
            if reg.fecha.year == today.year and reg.fecha.month == today.month:
                totales_mes_actual['cargas'] += 1
                totales_mes_actual['litros'] += float(reg.litros)
                totales_mes_actual['costo'] += float(reg.total)
                totales_mes_actual['propina'] += float(reg.propina)
            
            previous_reg = reg
            
        # Pasar nombre del mes actual para display
        context['mes_actual_nombre'] = MESES_ES.get(today.month, 'MES ACTUAL') + f" {today.year}"
        
        # Invertir para mostrar lo más reciente primero
        tabla_registros.reverse()
        
        # Paginación
        from django.core.paginator import Paginator
        paginator = Paginator(tabla_registros, 50) # 50 registros por página
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['historial_cargas'] = page_obj
        # Pasamos AMBOS totales al contexto con nombres claros
        context['totales_historicos'] = totales_historicos
        context['totales_mes_actual'] = totales_mes_actual
        
        return context

from .models import GastoUnidad
from .forms import GastoUnidadForm

# --- CONTROL DE GASTOS GENERALE (VERIFICACIÓN, SEGURO, ETC) ---

class GastoUnidadListView(LoginRequiredMixin, NonChoferRequiredMixin, ListView):
    model = GastoUnidad
    template_name = "dashboard/gasto_list.html"
    context_object_name = "gastos"
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset()
        tipo = self.request.GET.get('tipo')
        unidad_id = self.request.GET.get('unidad')
        
        if tipo:
            qs = qs.filter(tipo=tipo)
        if unidad_id:
            qs = qs.filter(unidad_id=unidad_id)
            
        return qs.select_related('unidad', 'chofer').order_by('-fecha')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unidades'] = Unidad.objects.all()
        # Extract unique types for filter
        context['tipos_gasto'] = GastoUnidad.TIPO_GASTO_CHOICES
        return context


class GastoUnidadCreateView(LoginRequiredMixin, NonChoferRequiredMixin, AjaxSuccessMixin, CreateView):
    model = GastoUnidad
    form_class = GastoUnidadForm
    template_name = "dashboard/gasto_form.html"
    success_url = reverse_lazy('dashboard:gastos_list')
    ajax_success_message = "¡Gasto registrado correctamente!"

    def form_valid(self, form):
        # La lógica de negocio fuerte está en el método save() del modelo GastoUnidad.
        # super() llama validación y nuestro Mixin.
        return super().form_valid(form)

from .forms import CombustibleDeleteForm
from django.views.generic import FormView
from django.shortcuts import get_object_or_404
from django.urls import reverse

class CombustibleDeleteView(LoginRequiredMixin, FormView):
    template_name = "dashboard/combustible_delete.html" # No se usa realmente si es modal, pero FormView lo pide
    form_class = CombustibleDeleteForm

    def get_success_url(self):
        # Redirigir al detalle de la unidad
        return reverse_lazy('dashboard:combustible_unidad_detail', kwargs={'pk': self.unidad_id})

    def form_valid(self, form):
        # 1. Obtener objeto y validar existencia
        pk = self.kwargs.get('pk')
        registro = get_object_or_404(RegistroCombustible, pk=pk)
        self.unidad_id = registro.unidad.id
        unidad = registro.unidad
        
        # Validar si la contraseña corresponde a ALGÚN administrador (Superusuario o puesto='ADMIN')
        # Esto permite que un Chofer solicite a un Admin que ingrese su contraseña para borrar.
        
        password = form.cleaned_data['admin_password']
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Obtener todos los candidatos a admin
        superusers = User.objects.filter(is_superuser=True)
        staff_admins = User.objects.filter(personal__puesto='ADMIN')
        
        potential_admins = set(list(superusers) + list(staff_admins))
        
        auth_success = False
        for admin in potential_admins:
            if admin.check_password(password):
                auth_success = True
                break
        
        if not auth_success:
            form.add_error('admin_password', "Contraseña de administrador incorrecta.")
            return self.form_invalid(form)
            
        # 3. Aplicar Corrección de Kilometraje
        nuevo_km = form.cleaned_data['nuevo_kilometraje']
        # Validar lógica básica? El usuario pidió explícitamente MODIFICAR ese valor. Confiamos en el admin.
        unidad.kilometraje_actual = nuevo_km
        unidad.save()
        
        # 4. Eliminar Registro
        registro.delete()
        
        return super().form_valid(form)

# --- VISTAS DE PERFIL DE USUARIO ---
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import UsuarioPerfilForm
from .models import Personal

class UsuarioPerfilView(LoginRequiredMixin, UpdateView):
    model = Personal
    form_class = UsuarioPerfilForm
    template_name = "dashboard/usuario_perfil.html"
    success_url = reverse_lazy('dashboard:home')

    def get_object(self, queryset=None):
        # Obtain the Personal instance for the currently logged-in user
        if hasattr(self.request.user, 'personal'):
            return self.request.user.personal
        else:
            # Create a default Personal object if it doesn't exist
            # This is a fallback for superusers or old users
            personal_obj = Personal.objects.create(
                usuario=self.request.user,
                nombre=self.request.user.first_name or self.request.user.username,
                apellido_paterno=self.request.user.last_name or '',
                puesto='ADMIN' if self.request.user.is_superuser else 'RUTAS'
            )
            return personal_obj

    def form_valid(self, form):
        messages.success(self.request, "Perfil actualizado correctamente.")
        return super().form_valid(form)

class UsuarioPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = "dashboard/usuario_cambiar_password.html"
    success_url = reverse_lazy('dashboard:home')

    def form_valid(self, form):
        messages.success(self.request, "Tu contraseña ha sido cambiada exitosamente.")
        return super().form_valid(form)

    def form_invalid(self, form):
        # Si es un modal, el manejo de errores es tricky. 
        # Idealmente devolveríamos JSON si fuera ajax, pero haremos un redirect con error messages o renderizar una página de error.
        # Por simplicidad en MVP: Renderizar una página de confirmación/error completa si falla.
        # Ojo: El usuario pidió Modal. Si el form es inválido, el modal se cierra y no pasa nada o recarga la página.
        # Para hacerlo robusto sin JS complejo: 
        # Esta vista puede renderizar una template 'borrar_confirmacion.html' si hay error.
        return self.render_to_response(self.get_context_data(form=form, object=get_object_or_404(RegistroCombustible, pk=self.kwargs.get('pk'))))

# --- ÓRDENES DE SERVICIO ---
from .models import OrdenServicio
from .forms import OrdenServicioForm

class OrdenServicioListView(LoginRequiredMixin, ListView):
    model = OrdenServicio
    template_name = "dashboard/orden_servicio_list.html"
    context_object_name = "ordenes"
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset()
        unidad_id = self.request.GET.get('unidad')
        if unidad_id:
            qs = qs.filter(unidad_id=unidad_id)
        return qs.select_related('unidad', 'chofer')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unidades'] = Unidad.objects.all()
        return context

class OrdenServicioCreateView(LoginRequiredMixin, AjaxSuccessMixin, CreateView):
    model = OrdenServicio
    form_class = OrdenServicioForm
    template_name = "dashboard/orden_servicio_form.html"
    success_url = reverse_lazy('dashboard:orden_servicio_list')
    ajax_success_message = "¡Orden de Servicio registrada con éxito!"

    def form_valid(self, form):
        # Asignar usuario logueado como chofer (si aplica, o permitir la selección en la vista)
        # El modelo tiene chofer, lo asignamos aquí por seguridad
        form.instance.chofer = self.request.user
        
        # Validar y guardar
        response = super().form_valid(form)
        messages.success(self.request, "Orden de Servicio registrada correctamente.")
        return response

class OrdenServicioDetailView(LoginRequiredMixin, DetailView):
    model = OrdenServicio
    template_name = "dashboard/orden_servicio_detail.html"
    context_object_name = "orden"

# --- CHECKLIST DIARIO ---
from .models import ChecklistUnidad
from .forms import ChecklistUnidadForm
from django.utils import timezone

class ChecklistUnidadListView(LoginRequiredMixin, ListView):
    model = ChecklistUnidad
    template_name = "dashboard/checklist_unidad_list.html"
    context_object_name = "checklists"
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset()
        unidad_id = self.request.GET.get('unidad')
        fecha_str = self.request.GET.get('fecha')
        
        if unidad_id:
            qs = qs.filter(unidad_id=unidad_id)
        if fecha_str:
            qs = qs.filter(fecha=fecha_str)
            
        return qs.select_related('unidad', 'chofer')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unidades'] = Unidad.objects.all()
        # Verificar si el usuario actual (chofer) ya llenó su checklist hoy
        # Sólo es relevante si es chofer, pero lo mandamos general
        if hasattr(self.request.user, 'personal') and self.request.user.personal.puesto == 'CHOFER':
            hoy = timezone.now().date()
            context['ya_lleno_hoy'] = ChecklistUnidad.objects.filter(chofer=self.request.user, fecha=hoy).exists()
        return context

class ChecklistUnidadCreateView(LoginRequiredMixin, AjaxSuccessMixin, CreateView):
    model = ChecklistUnidad
    form_class = ChecklistUnidadForm
    template_name = "dashboard/checklist_unidad_form.html"
    success_url = reverse_lazy('dashboard:checklist_unidad_list')
    ajax_success_message = "¡Checklist diario guardado correctamente. Buen viaje!"

    def get_context_data(self, **kwargs):
         context = super().get_context_data(**kwargs)
         unidades = Unidad.objects.filter(en_servicio=True)
         context['unidades_activas'] = unidades
         
         from .models import MedicionNeumatico, InventarioLlanta
         import json
         
         datos_mediciones = {}
         for u in unidades:
             ultima_medicion = MedicionNeumatico.objects.filter(unidad=u).order_by('-fecha').first()
             llantas_qs = InventarioLlanta.objects.filter(unidad=u, activa=True)
             llantas_list = [{'id': l.id, 'posicion': l.get_posicion_display()} for l in llantas_qs]
             
             datos_mediciones[u.id] = {
                 'ultima_fecha': ultima_medicion.fecha.isoformat() if ultima_medicion else None,
                 'ultimo_km': ultima_medicion.km_medicion if ultima_medicion else 0,
                 'llantas': llantas_list
             }
             
         context['datos_mediciones_json'] = json.dumps(datos_mediciones)
         return context

    def form_valid(self, form):
        # Asignar chofer, unidad seleccionada y fecha
        form.instance.chofer = self.request.user
        form.instance.fecha = timezone.now().date()
        
        unidad_id = self.request.POST.get('unidad_id')
        if not unidad_id:
            form.add_error(None, "Debes seleccionar una unidad.")
            return self.form_invalid(form)
            
        form.instance.unidad_id = unidad_id
        
        # Validar si ya hizo un checklist HOY para ESA unidad (Opcional, pero buena práctica)
        # SDC pide revisión diaria antes del inicio. Si hace 2 viajes, quizás sólo se requiere 1 al día.
        if ChecklistUnidad.objects.filter(chofer=self.request.user, unidad_id=unidad_id, fecha=form.instance.fecha).exists():
            messages.warning(self.request, "Ya registraste un checklist para esta unidad el día de hoy.")
            # Podemos permitirlo (sobreescribir/duplicar) o bloquearlo. Lo permitimos como registro extra.
            
        response = super().form_valid(form)
        
        # Guardar mediciones de neumáticos si fueron obligadas o provistas e inyectadas al form
        from .models import MedicionNeumatico, InventarioLlanta
        from decimal import Decimal
        
        llantas_activas = InventarioLlanta.objects.filter(unidad_id=unidad_id, activa=True)
        hubo_medicion = False
        km_actual = form.instance.km_actual
        
        # Actualizar kilometraje general de la unidad de paso
        if km_actual > form.instance.unidad.kilometraje_actual:
            form.instance.unidad.kilometraje_actual = km_actual
            form.instance.unidad.save()
            
        from .models import ConfiguracionGeneral
        config = ConfiguracionGeneral.get_solo()
        limite_mm = Decimal(config.limite_seguridad_llanta_mm)
        vida_util_km = Decimal(config.vida_util_estimada_llanta_km)
            
        for llanta in llantas_activas:
            psi_val = self.request.POST.get(f"psi_{llanta.id}")
            mm_val = self.request.POST.get(f"mm_{llanta.id}")
            tipo_desgaste = self.request.POST.get(f"desgaste_{llanta.id}", "Uniforme")
            
            if psi_val and mm_val:
                hubo_medicion = True
                
                observacion_auto = None
                if llanta.profundidad_inicial_mm:
                    prof_actual = Decimal(mm_val)
                    prof_inicial = Decimal(llanta.profundidad_inicial_mm)
                    km_recorridos = Decimal(km_actual - llanta.km_instalacion)
                    
                    if km_recorridos > 0 and prof_inicial > limite_mm:
                        # Tasa esperada de desgaste por km
                        tasa_esperada = (prof_inicial - limite_mm) / vida_util_km
                        # Tasa real de desgaste por km
                        tasa_actual = (prof_inicial - prof_actual) / km_recorridos
                        
                        if tasa_actual > (tasa_esperada * Decimal('1.5')):
                            observacion_auto = "Desgaste Acelerado. Causa: Sobrecarga constante. Acción: Revisar bitácoras de peso vs capacidad de unidad."
                        elif tasa_actual > (tasa_esperada * Decimal('1.25')):
                            if tipo_desgaste == "Irregular":
                                observacion_auto = "Desgaste Alta + Irregular. Causa: Alineación / Balanceo. Acción: Programar servicio de alineación inmediato."
                            else:
                                observacion_auto = "Desgaste Alta + Uniforme. Causa: Presión de aire baja / Estilo de manejo. Acción: Revisar presión en cada carga de combustible."
                                
                medicion = MedicionNeumatico.objects.create(
                    unidad_id=unidad_id,
                    llanta=llanta,
                    km_medicion=km_actual,
                    presion_psi=Decimal(psi_val),
                    profundidad_mm=Decimal(mm_val),
                    observaciones=observacion_auto
                )
                
                llanta.profundidad_piso_mm = Decimal(mm_val)
                if observacion_auto:
                    llanta.observaciones = observacion_auto
                llanta.save()
                
        # 4. Validar disparidad en Medidas (Alineación / Doble Rodado)
        if hubo_medicion:
            posiciones = {l.posicion: l for l in llantas_activas}
            
            check_pares = [
                ('DI1', 'DD1', 'Mala alineación / Convergencia Eje Delantero', 'Programar Alineación Eje Delantero'),
                ('TI1', 'TD1', 'Desgaste disparejo en Eje Trasero', 'Revisar suspensión/alineación Eje Trasero'),
                ('TI2', 'TD2', 'Desgaste disparejo en Eje Trasero', 'Revisar suspensión/alineación Eje Trasero')
            ]
            check_duales = [
                ('TI1', 'TI2', 'Presión dispareja en doble rodado Izquierdo', 'Nivelar aire en Eje Trasero Izquierdo'),
                ('TD1', 'TD2', 'Presión dispareja en doble rodado Derecho', 'Nivelar aire en Eje Trasero Derecho')
            ]
            
            for p1, p2, causa, accion in (check_pares + check_duales):
                if p1 in posiciones and p2 in posiciones:
                    l1 = posiciones[p1]
                    l2 = posiciones[p2]
                    diff = abs(l1.profundidad_piso_mm - l2.profundidad_piso_mm)
                    if diff > Decimal('1.5'):
                        alerta_txt = f"Desgaste Disparejo (>1.5mm entre lados/gemelas). Causa: {causa}. Acción: {accion}."
                        for l_obj in (l1, l2):
                            if alerta_txt not in (l_obj.observaciones or ""):
                                # Prefijo para que salga en dashboard
                                new_obs = f"Disparidad Detectada: {alerta_txt}"
                                l_obj.observaciones = (l_obj.observaciones + " | " + new_obs) if l_obj.observaciones else new_obs
                                l_obj.save()
                                
            messages.info(self.request, "Mediciones de seguridad de neumáticos registradas exitosamente y validadas.")
            
        messages.success(self.request, "Checklist diario guardado correctamente. ¡Buen viaje!")
        return response

# --- INVENTARIO DE LLANTAS ---
from .models import InventarioLlanta
from .forms import InventarioLlantaForm

class InventarioLlantaListView(LoginRequiredMixin, ListView):
    model = InventarioLlanta
    template_name = "dashboard/inventario_llanta_list.html"
    context_object_name = "llantas"
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset()
        unidad_id = self.request.GET.get('unidad')
        if unidad_id:
            qs = qs.filter(unidad_id=unidad_id)
        return qs.select_related('unidad')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unidades'] = Unidad.objects.all()
        from .models import ConfiguracionGeneral
        
        config = ConfiguracionGeneral.get_solo()
        context['config'] = config
        
        # Inyectar cálculo de kilómetros dinámicamente al queryset resultante de la página actual
        for llanta in context['llantas']:
            km_recorridos = llanta.unidad.kilometraje_actual - llanta.km_instalacion
            if km_recorridos < 0:
                km_recorridos = 0
                
            llanta.km_recorridos = km_recorridos
            llanta.km_restantes = config.vida_util_estimada_llanta_km - km_recorridos
            
        return context

class InventarioLlantaCreateView(LoginRequiredMixin, AjaxSuccessMixin, CreateView):
    model = InventarioLlanta
    form_class = InventarioLlantaForm
    template_name = "dashboard/inventario_llanta_form.html"
    success_url = reverse_lazy('dashboard:inventario_llanta_list')
    ajax_success_message = "¡Llanta registrada exitosamente!"

    def get_initial(self):
        initial = super().get_initial()
        unidad_id = self.request.GET.get('unidad')
        posicion = self.request.GET.get('posicion')
        if unidad_id:
            initial['unidad'] = unidad_id
        if posicion:
            initial['posicion'] = posicion
        return initial

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Llanta registrada exitosamente.")
        return response

class InventarioLlantaUpdateView(LoginRequiredMixin, AjaxSuccessMixin, UpdateView):
    model = InventarioLlanta
    form_class = InventarioLlantaForm
    template_name = "dashboard/inventario_llanta_form.html"
    success_url = reverse_lazy('dashboard:inventario_llanta_list')
    ajax_success_message = "¡Registro de llanta actualizado!"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Registro de llanta actualizado.")
        return response

# --- EVALUACION DE ENTREGA (SDC 3.3.2) ---
from .models import EvaluacionEntrega
from .forms import EvaluacionEntregaForm
from django.shortcuts import get_object_or_404

class EvaluacionEntregaCreateView(LoginRequiredMixin, AjaxSuccessMixin, CreateView):
    model = EvaluacionEntrega
    form_class = EvaluacionEntregaForm
    template_name = "dashboard/evaluacion_entrega_form.html"
    ajax_success_message = "¡Evaluación de entrega registrada correctamente!"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check if we have a viaje argument to pre-associate
        viaje_id = self.kwargs.get('viaje_id')
        if viaje_id:
            context['viaje'] = get_object_or_404(Viaje, pk=viaje_id)
        return context

    def form_valid(self, form):
        viaje_id = self.kwargs.get('viaje_id')
        if viaje_id:
            form.instance.viaje_id = viaje_id
        
        response = super().form_valid(form)
        messages.success(self.request, "Evaluación de entrega registrada correctamente.")
        return response

    def get_success_url(self):
        return reverse_lazy('dashboard:viajes_list')


class EvaluacionEntregaUpdateView(LoginRequiredMixin, AjaxSuccessMixin, UpdateView):
    model = EvaluacionEntrega
    form_class = EvaluacionEntregaForm
    template_name = "dashboard/evaluacion_entrega_form.html"
    ajax_success_message = "¡Evaluación de entrega actualizada correctamente!"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['viaje'] = self.object.viaje
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Evaluación de entrega actualizada.")
        return response

    def get_success_url(self):
        return reverse_lazy('dashboard:viajes_list')


# --- GESTION DE ZONAS DE ENTREGA ---
from .models import ZonaEntrega
from .forms import ZonaEntregaForm

class ZonaEntregaListView(LoginRequiredMixin, ListView):
    model = ZonaEntrega
    template_name = "dashboard/zona_entrega_list.html"
    context_object_name = "zonas"
    ordering = ['nombre']

class ZonaEntregaMapView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/zona_entrega_map.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tiene_zonas'] = ZonaEntrega.objects.exists()
        
        # Agrupar por municipio para el catálogo lateral
        zonas = ZonaEntrega.objects.all().order_by('municipio', 'nombre')
        zonas_por_municipio = {}
        for z in zonas:
            muni = z.municipio or "Sin Municipio"
            if muni not in zonas_por_municipio:
                zonas_por_municipio[muni] = []
            zonas_por_municipio[muni].append(z)
            
        context['zonas_agrupadas'] = zonas_por_municipio
        context['zonas_count'] = zonas.count()
        return context

from django.http import JsonResponse
from django.views import View
import json

class ZonasGeoJSONView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        zonas = ZonaEntrega.objects.exclude(geojson_data__isnull=True).exclude(geojson_data__exact='')
        
        feature_collection = {
            "type": "FeatureCollection",
            "features": []
        }
        
        for zona in zonas:
            try:
                # Load the geometry collection saved during model save
                zone_geo = json.loads(zona.geojson_data)
                
                # Each zone might have multiple features, we want to flatten them into the main collection
                # and attach the zone properties to each feature
                if "features" in zone_geo:
                    for feature in zone_geo["features"]:
                        # Decorate the feature with our custom zone data for the frontend
                        feature['properties'] = {
                            "nombre": zona.nombre,
                            "municipio": zona.municipio or "Sin Municipio",
                            "color": zona.color_hex,
                            "id": zona.id,
                            "tiempo": zona.tiempo_traslado_minutos,
                            "distancia": float(zona.distancia_km),
                            "tarifa": float(zona.tarifa_flete),
                            "colonias": str(zona.colonias or 'No hay colonias asignadas.'),
                            "d_cp": feature.get('properties', {}).get('d_cp', ''), # Re-attach CP
                        }
                        feature_collection["features"].append(feature)
            except json.JSONDecodeError:
                continue
                
        return JsonResponse(feature_collection)


class ZonaEntregaCreateView(LoginRequiredMixin, AjaxSuccessMixin, CreateView):
    model = ZonaEntrega
    form_class = ZonaEntregaForm
    template_name = "dashboard/zona_entrega_form.html"
    success_url = reverse_lazy('dashboard:zona_entrega_list')
    ajax_success_message = "¡Zona de Entrega creada exitosamente!"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Zona de Entrega creada exitosamente.")
        return response

class ZonaEntregaUpdateView(LoginRequiredMixin, AjaxSuccessMixin, UpdateView):
    model = ZonaEntrega
    form_class = ZonaEntregaForm
    template_name = "dashboard/zona_entrega_form.html"
    success_url = reverse_lazy('dashboard:zona_entrega_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Zona de Entrega actualizada exitosamente.")
        return response

class ZonaEntregaDeleteView(LoginRequiredMixin, DeleteView):
    model = ZonaEntrega
    template_name = "dashboard/zona_entrega_confirm_delete.html"
    success_url = reverse_lazy('dashboard:zona_entrega_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Zona de Entrega eliminada exitosamente.")
        return super().delete(request, *args, **kwargs)

import csv
import io
from django.views import View

class ZonaEntregaImportView(LoginRequiredMixin, NonChoferRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get('csv_file')
        
        if not csv_file:
            messages.error(request, 'No se seleccionó ningún archivo.')
            return redirect('dashboard:zona_entrega_list')
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Por favor subir un archivo con extensión .csv.')
            return redirect('dashboard:zona_entrega_list')
            
        try:
            data_set = csv_file.read().decode('UTF-8', errors='replace')
            io_string = io.StringIO(data_set)
            reader = csv.DictReader(io_string)
            
            # Limpiamos headers
            original_headers = reader.fieldnames or []
            # normalize map
            h_map = {}
            for h in original_headers:
                h_clean = str(h).strip().upper()
                # Eliminar tildes u otras limpiezas adicionales si fuera necesario
                h_map[h_clean] = h
                
            # Validar columnas requeridas
            required_groups = {
                'Zona': ['ZONA'],
                'Código Postal': ['CÓDIGO POSTAL', 'CODIGO POSTAL', 'CODIGOS POSTALES', 'CP'],
                'Asentamiento / Colonia': ['ASENTAMIENTO', 'ASENTAMIENTOS', 'COLONIA', 'COLONIAS'],
                'Distancia Media': ['DISTANCIA MEDIA', 'DISTANCIA', 'DISTANCIA KM'],
                'Tiempo Medio de Traslado': ['TIEMPO MEDIO DE TRASLADO', 'TIEMPO MEDIO', 'TIEMPO'],
                'Costo Base': ['COSTO BASE', 'TARIFA FLETE', 'TARIFA'],
                'Costo Maniobra adicional': ['COSTO MANIOBRA ADICIONAL', 'COSTO MANIOBRA', 'MANIOBRA']
            }
            
            missing_columns = []
            for label, possibilities in required_groups.items():
                if not any(p in h_map for p in possibilities):
                    missing_columns.append(label)
                    
            if missing_columns:
                nombres_faltantes = ", ".join([f"'{m}'" for m in missing_columns])
                messages.error(
                    request, 
                    f"Inconsistencia de datos: Faltan las siguientes columnas en el Excel/CSV o sus encabezados no son reconocidos: {nombres_faltantes}."
                )
                return redirect('dashboard:zona_entrega_list')
            
            def get_val(row, *possible_keys):
                for k in possible_keys:
                    if k in h_map:
                        return row.get(h_map[k], '').strip()
                return ''
            
            zonas_creadas = 0
            zonas_actualizadas = 0
            
            for row in reader:
                zona_nombre = get_val(row, 'ZONA')
                if not zona_nombre:
                    continue
                    
                cp = get_val(row, 'CÓDIGO POSTAL', 'CODIGO POSTAL', 'CODIGOS POSTALES', 'CP')
                colonia = get_val(row, 'ASENTAMIENTO', 'ASENTAMIENTOS', 'COLONIA', 'COLONIAS')
                distancia_raw = get_val(row, 'DISTANCIA MEDIA', 'DISTANCIA', 'DISTANCIA KM')
                tiempo_raw = get_val(row, 'TIEMPO MEDIO DE TRASLADO', 'TIEMPO MEDIO', 'TIEMPO')
                tarifa_raw = get_val(row, 'COSTO BASE', 'TARIFA FLETE', 'TARIFA')
                maniobra_raw = get_val(row, 'COSTO MANIOBRA ADICIONAL', 'COSTO MANIOBRA', 'MANIOBRA')
                
                def extract_number(val, is_float=True):
                    import re
                    match = re.search(r'[\d\.]+', str(val))
                    if match:
                        try:
                            return float(match.group()) if is_float else int(float(match.group()))
                        except ValueError:
                            pass
                    return 0.0 if float else 0
                    
                distancia = extract_number(distancia_raw)
                tiempo = extract_number(tiempo_raw, is_float=False)
                tarifa = extract_number(tarifa_raw)
                maniobra = extract_number(maniobra_raw)
                
                zona, created = ZonaEntrega.objects.get_or_create(
                    nombre=zona_nombre,
                    defaults={
                        'tiempo_traslado_minutos': tiempo,
                        'distancia_km': distancia,
                        'tarifa_flete': tarifa,
                        'costo_maniobra': maniobra,
                        'codigos_postales': cp,
                        'colonias': colonia
                    }
                )
                
                if created:
                    zonas_creadas += 1
                else:
                    modificado = False
                    
                    if distancia > 0 and zona.distancia_km != distancia:
                        zona.distancia_km = distancia
                        modificado = True
                    if tiempo > 0 and zona.tiempo_traslado_minutos != tiempo:
                        zona.tiempo_traslado_minutos = tiempo
                        modificado = True
                    if tarifa > 0 and zona.tarifa_flete != tarifa:
                        zona.tarifa_flete = tarifa
                        modificado = True
                    if maniobra > 0 and zona.costo_maniobra != maniobra:
                        zona.costo_maniobra = maniobra
                        modificado = True
                        
                    if cp:
                        current_cps = [c.strip() for c in (zona.codigos_postales or '').split(',') if c.strip()]
                        if cp not in current_cps:
                            current_cps.append(cp)
                            zona.codigos_postales = ", ".join(current_cps)
                            modificado = True
                            
                    if colonia:
                        current_colds = [c.strip() for c in (zona.colonias or '').split(',') if c.strip()]
                        if colonia not in current_colds:
                            current_colds.append(colonia)
                            zona.colonias = ", ".join(current_colds)
                            modificado = True
                            
                    if modificado:
                        zona.save()
                        zonas_actualizadas += 1
                        
            messages.success(request, f"Importación finalizada. Zonas nuevas: {zonas_creadas}. Zonas actualizadas: {zonas_actualizadas}.")
            
        except Exception as e:
            messages.error(request, f"Ocurrió un error al procesar el archivo: {str(e)}")
            
        return redirect('dashboard:zona_entrega_list')

from django.http import JsonResponse
from dashboard.models import CodigoPostalCat

def colonias_por_cp_api(request):
    """
    Recibe una cadena de CPs separados por coma (ej. '?cps=50091, 56225') 
    y devuelve la lista concatenada de todas sus colonias encontradas en BD.
    """
    cps_param = request.GET.get('cps', '')
    if not cps_param:
        return JsonResponse({'colonias': []})
        
    # Limpiar y separar los CPs
    cps = [cp.strip() for cp in cps_param.split(',') if cp.strip()]
    
    # Consultar a la base de datos
    colonias_encontradas = CodigoPostalCat.objects.filter(codigo__in=cps).values_list('asentamiento', flat=True)
    
    # Ordenar y asegurar únicos
    colonias_unicas = sorted(list(set(colonias_encontradas)))
    
    # Obtener el municipio predominante (Columna D)
    municipios = CodigoPostalCat.objects.filter(codigo__in=cps).values_list('municipio', flat=True)
    municipio_sugerido = ""
    if municipios:
        from collections import Counter
        municipio_sugerido = Counter(municipios).most_common(1)[0][0]
    
    return JsonResponse({
        'colonias': colonias_unicas,
        'municipio': municipio_sugerido
    })

def buscar_colonia_api(request):
    """
    Busca colonias que coincidan con un texto y devuelve CP, Municipio y sugerencia de Zona.
    Prioriza las colonias que YA TIENEN zona asignada en el sistema.
    """
    query = request.GET.get('q', '').strip()
    if not query or len(query) < 3:
        return JsonResponse({'resultados': []})

    # Buscar en CodigoPostalCat - ampliamos a 30 para tener margen de ordenamiento
    matches = CodigoPostalCat.objects.filter(asentamiento__icontains=query)[:30]

    from dashboard.models import ZonaEntrega

    # Preconstruir índices en memoria para búsqueda O(1) por CP y por colonia
    todas_las_zonas = ZonaEntrega.objects.all()
    zona_por_cp = {}        # {'56200': zona_obj}
    zona_por_colonia = {}   # {'lomas de san esteban': zona_obj}  (minúsculas)

    for zona in todas_las_zonas:
        if zona.codigos_postales:
            for cp in zona.codigos_postales.split(','):
                cp = cp.strip()
                if cp:
                    zona_por_cp[cp] = zona
        if zona.colonias:
            for col in zona.colonias.split(','):
                col_norm = col.strip().lower()
                if col_norm:
                    zona_por_colonia[col_norm] = zona

    resultados_con_zona = []
    resultados_sin_zona = []

    for row in matches:
        zona_match = None
        zona_id = None
        zona_color = '#6c757d'

        # 1. Buscar por CP (más exacto)
        if row.codigo in zona_por_cp:
            z = zona_por_cp[row.codigo]
            zona_match = z.nombre
            zona_id = z.id
            zona_color = z.color_hex or '#6c757d'

        # 2. Si no hay zona por CP, buscar por nombre de colonia (parcial)
        if not zona_match:
            col_norm = row.asentamiento.strip().lower()
            for col_key, z in zona_por_colonia.items():
                if col_norm in col_key or col_key in col_norm:
                    zona_match = z.nombre
                    zona_id = z.id
                    zona_color = z.color_hex or '#6c757d'
                    break

        item = {
            'colonia': row.asentamiento,
            'cp': row.codigo,
            'municipio': row.municipio or row.ciudad or 'N/A',
            'zona_id': zona_id,
            'zona_nombre': zona_match or 'No Asignada',
            'zona_color': zona_color,
            'tiene_zona': bool(zona_match),
        }

        if zona_match:
            resultados_con_zona.append(item)
        else:
            resultados_sin_zona.append(item)

    # Colonias con zona PRIMERO, sin zona al final. Máx 15 resultados totales.
    resultados = (resultados_con_zona + resultados_sin_zona)[:15]

    return JsonResponse({'resultados': resultados})


@login_required
def solicitar_autorizacion_zona_api(request):
    """
    Envía MensajeInterno a todos los usuarios Admin y Logística solicitando
    la creación de una nueva zona para poder registrar la obra.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    import json as _json
    try:
        data = _json.loads(request.body)
    except Exception:
        data = {}

    colonia  = data.get('colonia', 'No especificada')
    municipio = data.get('municipio', 'No especificado')
    cp       = data.get('cp', 'No especificado')

    from dashboard.models import Personal, MensajeInterno

    solicitante = request.user.get_full_name() or request.user.username

    contenido = (
        f"🚨 SOLICITUD DE AUTORIZACIÓN – ZONA NO REGISTRADA\n\n"
        f"El usuario {solicitante} intentó registrar una nueva obra en una colonia "
        f"que NO tiene zona de entrega asignada en el sistema.\n\n"
        f"📍 Datos del destino:\n"
        f"  • Colonia:   {colonia}\n"
        f"  • Municipio: {municipio}\n"
        f"  • CP:        {cp}\n\n"
        f"Si es viable atender este destino, por favor registra la nueva zona "
        f"en Rutas & Zonas incluyendo el CP «{cp}» para desbloquear el formulario. "
        f"Si NO es viable, notifica al usuario que no se realizan envíos a esa dirección.\n\n"
        f"— Sistema automático Casa Lupita Logística"
    )

    # Enviar a todos los ADMIN y RUTAS
    destinatarios = Personal.objects.filter(
        puesto__in=['ADMIN', 'RUTAS']
    ).select_related('usuario')

    enviados = 0
    for personal in destinatarios:
        MensajeInterno.objects.create(
            remitente=request.user,
            destinatario=personal.usuario,
            contenido=contenido,
        )
        enviados += 1

    # Fallback: mensaje global si no hay destinatarios configurados
    if enviados == 0:
        MensajeInterno.objects.create(
            remitente=request.user,
            destinatario=None,
            contenido=contenido,
        )

    return JsonResponse({'ok': True, 'enviados': enviados})


@login_required
def verificar_zona_por_cp_api(request):
    """
    Polling: verifica si un CP o colonia ya tiene zona asignada en el sistema.
    Usado por el frontend para detectar cuando Admin registró la nueva zona.
    """
    cp      = request.GET.get('cp', '').strip()
    colonia = request.GET.get('colonia', '').strip()

    if not cp and not colonia:
        return JsonResponse({'tiene_zona': False})

    from dashboard.models import ZonaEntrega

    todas_zonas = ZonaEntrega.objects.all()
    zona_encontrada = None

    for zona in todas_zonas:
        # 1. Buscar por CP (prioritario)
        if cp and zona.codigos_postales:
            cps = [c.strip() for c in zona.codigos_postales.split(',') if c.strip()]
            if cp in cps:
                zona_encontrada = zona
                break
        # 2. Buscar por nombre de colonia si no encontró por CP
        if not zona_encontrada and colonia and zona.colonias:
            cols = [c.strip().lower() for c in zona.colonias.split(',') if c.strip()]
            if colonia.strip().lower() in cols:
                zona_encontrada = zona
                break

    if zona_encontrada:
        return JsonResponse({
            'tiene_zona': True,
            'zona_id': zona_encontrada.id,
            'zona_nombre': zona_encontrada.nombre,
            'zona_color': zona_encontrada.color_hex or '#3388ff',
            'municipio': zona_encontrada.municipio or '',
        })

    return JsonResponse({'tiene_zona': False})

def calcular_centroide_zona_api(request):
    """
    Calcula el centroide aproximado basado en las geometrías de los CPs.
    """
    import os
    import json
    from django.conf import settings
    
    cps_param = request.GET.get('cps', '')
    if not cps_param:
        return JsonResponse({'error': 'No CPs provided'})
        
    cps_limpios = [cp.strip() for cp in cps_param.split(',') if cp.strip()]
    if not cps_limpios:
        return JsonResponse({'error': 'No valid CPs'})
        
    data_path = os.path.join(settings.BASE_DIR, 'dashboard', 'data', 'zonas_texcoco.json')
    if not os.path.exists(data_path):
        return JsonResponse({'error': 'Data missing'})
        
    total_lat = 0
    total_lon = 0
    count = 0
    
    def process_coords(coords):
        nonlocal total_lat, total_lon, count
        if isinstance(coords[0], (int, float)):
            total_lon += coords[0]
            total_lat += coords[1]
            count += 1
        else:
            for item in coords:
                process_coords(item)
                
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                feature = json.loads(line)
                cp_val = feature.get('properties', {}).get('d_cp', '').strip()
                if cp_val in cps_limpios:
                    geom = feature.get('geometry', {})
                    if geom and 'coordinates' in geom:
                        process_coords(geom['coordinates'])
            except:
                pass
                
    if count > 0:
        return JsonResponse({'lat': total_lat / count, 'lon': total_lon / count})
    else:
        return JsonResponse({'error': 'Geocoding failed for CPs'})

from .models import ConfiguracionGeneral
from .forms import ConfiguracionGeneralForm
from django.contrib import messages

class ConfiguracionGeneralUpdateView(LoginRequiredMixin, NonChoferRequiredMixin, AjaxSuccessMixin, UpdateView):
    model = ConfiguracionGeneral
    form_class = ConfiguracionGeneralForm
    template_name = 'dashboard/configuracion_general.html'
    success_url = reverse_lazy('dashboard:home')
    ajax_success_message = "Configuración general actualizada correctamente."
    
    def get_object(self, queryset=None):
        return ConfiguracionGeneral.get_solo()


from django.http import JsonResponse
from decimal import Decimal

class CalcularFleteSugeridoView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            import json
            data = json.loads(request.body)
            distancia_km = Decimal(str(data.get('distancia_km', 0)))
            tiempo_minutos = Decimal(str(data.get('tiempo_minutos', 0)))
            
            if distancia_km <= 0 or tiempo_minutos <= 0:
                return JsonResponse({'error': 'Distancia y tiempo requeridos'}, status=400)
                
            config = ConfiguracionGeneral.get_solo()
            costo_minuto_chofer = config.costo_minuto_chofer
            costo_minuto_chalan = config.costo_minuto_chalan
            tiempo_descarga = Decimal(config.tiempo_descarga_promedio_min)
            
            # Buscar unidades reales
            unidades_reales = list(Unidad.objects.filter(en_servicio=True).select_related())
            tipos_existentes = {u.tipo: u for u in unidades_reales}
            
            # Garantizar que evaluemos los tipos principales
            tipos_base = ['CAMION', 'CAMIONETA_3_5', 'CAMIONETA_1_5', 'AUTO', 'MOTO']
            unidades_a_evaluar = []
            
            for tb in tipos_base:
                if tb in tipos_existentes:
                    unidades_a_evaluar.append(tipos_existentes[tb])
                else:
                    # Crear unidad Mock/Virtual en memoria para el cálculo
                    virtual_u = Unidad(tipo=tb, nombre_corto=f"Estimado ({tb.title()})", kilometraje_actual=0)
                    # Forzar pk para evitar consultas que arrojen error si el property las necesita
                    virtual_u.pk = -1
                    unidades_a_evaluar.append(virtual_u)
            
            tipos_calculados = {}
            
            for u in unidades_a_evaluar:
                if u.tipo not in tipos_calculados:
                    # Calculamos viaje (Ida y Vuelta)
                    km_totales = distancia_km * 2
                    tiempo_total_viaje = (tiempo_minutos * 2) + tiempo_descarga
                    
                    costo_km = u.costo_operativo_total_por_km
                    costo_operativo = km_totales * costo_km
                    costo_tiempo = tiempo_total_viaje * (costo_minuto_chofer + costo_minuto_chalan)
                    
                    costo_flete = round(costo_operativo + costo_tiempo, 2)
                    
                    tipos_calculados[u.tipo] = {
                        'tipo': u.get_tipo_display() if hasattr(u, 'get_tipo_display') else u.tipo.title(),
                        'costo': float(costo_flete),
                        'ejemplo_unidad': u.nombre_corto or u.nUnidad or 'Virtual Estimado',
                        'desglose': {
                            'km_totales': float(km_totales),
                            'tiempo_total_mins': float(tiempo_total_viaje),
                            'costo_operativo_km': float(costo_km),
                            'subtotal_km': float(costo_operativo),
                            'costo_minuto_personal': float(costo_minuto_chofer + costo_minuto_chalan),
                            'subtotal_tiempo': float(costo_tiempo)
                        }
                    }
                    
            # Ordenar de mayor a menor costo
            resultados = sorted(list(tipos_calculados.values()), key=lambda x: x['costo'], reverse=True)
            
            return JsonResponse({'status': 'ok', 'cotizaciones': resultados})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
# --- VISTAS DE MOSTRADOR (PASO 1 - FASE 2) ---

class MostradorHomeView(LoginRequiredMixin, ListView):
    """Cola de pedidos recientemente registrados"""
    model = Pedido
    template_name = 'dashboard/mostrador_home.html'
    context_object_name = 'pedidos'
    paginate_by = 20

    def get_queryset(self):
        return Pedido.objects.filter(estado='REGISTRADO').order_by('-fecha_registro')

class CotizadorFleteModalView(LoginRequiredMixin, TemplateView):
    """Renderiza el fragmento del modal para cotizar"""
    template_name = 'dashboard/mostrador/modal_cotizador.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['zonas'] = ZonaEntrega.objects.all()
        return context

class CalcularFleteAccionView(LoginRequiredMixin, View):
    """Lógica HTMX para devolver el resultado de la cotización con desglose por unidad"""
    def post(self, request):
        zona_id = request.POST.get('zona')
        es_urgente = request.POST.get('urgente') == 'on'
        
        if not zona_id:
            return HttpResponse('<div class="alert alert-warning">Selecciona una zona</div>')
            
        zona = get_object_or_404(ZonaEntrega, pk=zona_id)
        config = ConfiguracionGeneral.get_solo()
        
        # Parámetros de la zona
        distancia = Decimal(str(zona.distancia_km))
        tiempo = Decimal(str(zona.tiempo_traslado_minutos))
        
        # Tipos a evaluar (Los mismos que el motor avanzado)
        tipos_base = [
            ('MOTO', 'Moto Express'), 
            ('AUTO', 'Auto / Sedán'),
            ('CAMIONETA_1_5', 'Camioneta 1.5 Ton'),
            ('CAMIONETA_3_5', 'Camioneta 3.5 Ton'),
            ('CAMION', 'Camión (Ruta Peso)')
        ]
        
        opciones = []
        for tipo_cod, tipo_nom in tipos_base:
            # Buscamos una unidad real de este tipo para obtener su costo operativo real
            unidad_ejemplo = Unidad.objects.filter(tipo=tipo_cod, en_servicio=True).first()
            if not unidad_ejemplo:
                unidad_ejemplo = Unidad(tipo=tipo_cod) # Mock para el cálculo
                unidad_ejemplo.pk = -1 # Necesario para evitar crash al calcular gastos
            
            # Cálculo base (Simular Ida y Vuelta)
            km_totales = distancia * 2
            tiempo_total = (tiempo * 2) + config.tiempo_descarga_promedio_min
            
            costo_op = km_totales * unidad_ejemplo.costo_operativo_total_por_km
            costo_rh = tiempo_total * (config.costo_minuto_chofer + config.costo_minuto_chalan)
            
            subtotal = costo_op + costo_rh
            if es_urgente:
                subtotal *= Decimal('1.20')
            
            opciones.append({
                'tipo': tipo_nom,
                'codigo': tipo_cod,
                'costo': round(subtotal, 2)
            })
            
        return render(request, 'dashboard/mostrador/resultado_cotizacion.html', {
            'opciones': opciones,
            'zona': zona,
            'es_urgente': es_urgente
        })

from django.db import transaction

class PedidoCreateView(LoginRequiredMixin, CreateView):
    model = Pedido
    form_class = PedidoForm
    template_name = 'dashboard/pedido_form.html'
    success_url = reverse_lazy('dashboard:mostrador_home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['zonas'] = ZonaEntrega.objects.all()
        return context

    def form_valid(self, form):
        try:
            with transaction.atomic():
                # SI NO HAY CLIENTE SELECCIONADO EN EL SISTEMA
                if not form.instance.cliente:
                    id_sae = self.request.POST.get('id_sae_search', '').strip()
                    
                    if id_sae:
                        cliente = Cliente.objects.filter(id_sae=id_sae).first()
                        if not cliente:
                            cliente = Cliente.objects.create(
                                id_sae=id_sae,
                                razon_social=form.instance.cliente_nombre_manual or f"Cliente {id_sae}",
                                telefono_principal=form.instance.cliente_telefono_manual or "",
                            )
                        form.instance.cliente = cliente
                    else:
                        cliente = Cliente.objects.create(
                            id_sae=None, # Cliente Mostrador Puro
                            razon_social=form.instance.cliente_nombre_manual or "CLIENTE MOSTRADOR",
                            telefono_principal=form.instance.cliente_telefono_manual or "",
                        )
                        form.instance.cliente = cliente

                # SI NO HAY OBRA SELECCIONADA (Viene por los campos manuales integrados)
                if not form.instance.obra:
                    alias = self.request.POST.get('obra_alias_manual', '').strip()
                    zona_id = self.request.POST.get('obra_zona_manual')
                    
                    if alias and zona_id:
                        obra = Obra.objects.create(
                            cliente=form.instance.cliente,
                            alias=alias,
                            zona_id=zona_id,
                            cp=self.request.POST.get('obra_cp_manual'),
                            colonia=self.request.POST.get('obra_colonia_manual'),
                            calle_numero=self.request.POST.get('obra_calle_manual'),
                            referencias=self.request.POST.get('obra_referencias_manual'),
                            nombre_receptor=self.request.POST.get('obra_receptor_nombre_manual'),
                            telefono_receptor=self.request.POST.get('obra_receptor_tel_manual'),
                        )
                        form.instance.obra = obra

                # Guardar el pedido final
                messages.success(self.request, f"Pedido {form.instance.folio_sae} registrado correctamente.")
                return super().form_valid(form)
        except Exception as e:
            form.add_error(None, f"Error al procesar el registro triple: {str(e)}")
            return self.form_invalid(form)

class ClienteSAEBusquedaView(LoginRequiredMixin, View):
    """Busca cliente por ID SAE directo (Input Mostrador)"""
    def get(self, request):
        valor = request.GET.get('id_sae_search', '').strip()
        if not valor:
            return HttpResponse('')
            
        cliente = Cliente.objects.filter(id_sae=valor).first()
        
        if cliente:
            return render(request, 'dashboard/mostrador/cliente_info_fragment.html', {'cliente': cliente})
        else:
            return HttpResponse(f'<div class="text-secondary mt-1 small"><i class="fas fa-info-circle"></i> Nuevo ID SAE: <strong>{valor}</strong>. Llene los datos manuales y se guardará al cerrar el pedido.</div>')

class ClienteBuscadorModalView(LoginRequiredMixin, TemplateView):
    """Renderiza el modal de búsqueda avanzada (Lupa)"""
    template_name = 'dashboard/mostrador/modal_buscador_cliente.html'

class ClienteBuscadorAccionView(LoginRequiredMixin, View):
    """Lógica de búsqueda en el modal (Búsqueda Rápida vs Extendida)"""
    def get(self, request):
        query = request.GET.get('q', '').strip()
        extendida = request.GET.get('extendida') == 'true'
        
        if len(query) < 3:
            return HttpResponse('<div class="p-3 text-muted small">Ingrese al menos 3 caracteres...</div>')
            
        q_filter = (models.Q(razon_social__icontains=query) | 
                    models.Q(id_sae__icontains=query) | 
                    models.Q(obras__alias__icontains=query))
        
        clientes = Cliente.objects.filter(q_filter).prefetch_related('obras').distinct()
        
        resultados = []
        for cliente in clientes:
            obras = cliente.obras.all()
            if not extendida:
                limite = timezone.now() - timedelta(days=365)
                obras = obras.filter(models.Q(esta_activa=True) & (models.Q(fecha_ultimo_pedido__gte=limite) | models.Q(fecha_ultimo_pedido__isnull=True)))

            for obra in obras:
                resultados.append({
                    'cliente': cliente,
                    'obra': obra,
                    'activa': obra.es_reciente
                })
        
        return render(request, 'dashboard/mostrador/buscador_resultados_fragment.html', {
            'resultados': resultados,
            'query': query,
            'extendida': extendida
        })

class ObraSelectFragmentView(LoginRequiredMixin, View):
    """Devuelve el <select> de obras filtrado por cliente con soporte para pre-selección"""
    def get(self, request):
        cliente_id = request.GET.get('cliente_id')
        selected_obra_id = request.GET.get('obra_id')
        
        if not cliente_id or cliente_id == "":
            return HttpResponse('<select name="obra" class="form-select" disabled required><option value="">-- Complete datos de cliente --</option></select>')
            
        # Al buscar, si elegimos una obra inactiva desde la lupa, la reactivamos
        if selected_obra_id:
            Obra.objects.filter(pk=selected_obra_id, cliente_id=cliente_id).update(esta_activa=True)

        obras = Obra.objects.filter(cliente_id=cliente_id, esta_activa=True)
        return render(request, 'dashboard/mostrador/obras_select_options.html', {
            'obras': obras,
            'selected_obra_id': selected_obra_id
        })

class ObraCreateModalView(LoginRequiredMixin, CreateView):
    model = Obra
    form_class = ObraForm
    template_name = 'dashboard/mostrador/modal_obra_form.html'

    def form_valid(self, form):
        self.object = form.save()
        # HTMX: Después de guardar, cerramos modal y actualizamos el select de obras
        if "HX-Request" in self.request.headers:
            # Devolvemos un trigger para que el select se recargue o simplemente el nuevo select
            messages.success(self.request, "Nueva obra registrada.")
            response = HttpResponse(status=204)
            response["HX-Trigger"] = "obraGuardada"
            return response
        return super().form_valid(form)

class PedidoDetailView(LoginRequiredMixin, DetailView):
    model = Pedido
    template_name = 'dashboard/mostrador/pedido_detail.html'
    context_object_name = 'pedido'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Determinar si el pedido ya está en ruta o entregado (Inmutable total)
        context['es_editable'] = self.object.estado == 'REGISTRADO'
        return context

class PedidoUnlockView(LoginRequiredMixin, View):
    """Procesa la contraseña de supervisor para permitir editar un pedido registrado"""
    def post(self, request, pk):
        password = request.POST.get('password')
        pedido = get_object_or_404(Pedido, pk=pk)
        
        # Validar contraseña contra cualquier superusuario o admin
        User = get_user_model()
        superusers = User.objects.filter(is_superuser=True)
        staff_admins = User.objects.filter(personal__puesto='ADMIN')
        potential_admins = set(list(superusers) + list(staff_admins))
        
        auth_success = False
        for admin in potential_admins:
            if admin.check_password(password):
                auth_success = True
                break
        
        if auth_success:
            # Si tiene éxito, redirigimos al update view normal
            # Pero como es HTMX, mandamos la cabecera de redirección
            response = HttpResponse(status=204)
            response["HX-Redirect"] = reverse('dashboard:pedido_update', kwargs={'pk': pk})
            messages.success(request, "Autorización concedida. Puede editar el pedido.")
            return response
        else:
            return HttpResponse('<div class="alert alert-danger py-1 small mt-2">Contraseña incorrecta</div>')

class PedidoUpdateView(LoginRequiredMixin, AjaxSuccessMixin, UpdateView):
    model = Pedido
    form_class = PedidoForm
    template_name = 'dashboard/pedido_form.html'
    success_url = reverse_lazy('dashboard:mostrador_home')
    ajax_success_message = "Pedido actualizado correctamente."

class MostradorDashboardView(LoginRequiredMixin, TemplateView):
    """Resumen estadístico exclusivo para el personal de Mostrador"""
    template_name = 'dashboard/mostrador/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoy = timezone.now().date()
        
        # Estadísticas de Pedidos
        context['pedidos_hoy'] = Pedido.objects.filter(fecha_registro__date=hoy).count()
        context['pedidos_urgentes'] = Pedido.objects.filter(es_urgente=True, estado='REGISTRADO').count()
        context['pedidos_cancelados'] = Pedido.objects.filter(estado='CANCELADO').count()
        context['pedidos_en_espera'] = Pedido.objects.filter(estado='REGISTRADO').count()
        
        # Resumen por estado
        context['resumen_estados'] = [
            {'label': 'Registrados', 'count': Pedido.objects.filter(estado='REGISTRADO').count(), 'color': 'info'},
            {'label': 'En Preparación', 'count': Pedido.objects.filter(estado='EN_PREPARACION').count(), 'color': 'warning'},
            {'label': 'En Ruta', 'count': Pedido.objects.filter(estado='EN_RUTA').count(), 'color': 'primary'},
            {'label': 'Entregados', 'count': Pedido.objects.filter(estado='ENTREGADO').count(), 'color': 'success'},
        ]
        
        # Últimos movimientos
        context['pedidos_recientes'] = Pedido.objects.order_by('-fecha_registro')[:10]
        
        return context

class PedidoCancelView(LoginRequiredMixin, View):
    """Permite cancelar un pedido si aún no está en ruta"""
    def post(self, request, pk):
        pedido = get_object_or_404(Pedido, pk=pk)
        if pedido.estado in ['REGISTRADO', 'REPROGRAMADO']:
            pedido.estado = 'CANCELADO'
            pedido.save()
            messages.success(request, f"Pedido {pedido.folio_sae} cancelado correctamente.")
        else:
            messages.error(request, "El pedido no se puede cancelar porque ya está en proceso.")
            
        if "HX-Request" in request.headers:
            response = HttpResponse(status=204)
            response["HX-Redirect"] = reverse('dashboard:pedido_detail', kwargs={'pk': pk})
            return response
        return redirect('dashboard:pedido_detail', pk=pk)

# --- GESTION DE CLIENTES Y OBRAS ---
class ClienteListView(LoginRequiredMixin, NonChoferRequiredMixin, ListView):
    model = Cliente
    template_name = "dashboard/clientes/cliente_list.html"
    context_object_name = "clientes"
    paginate_by = 30

    def get_queryset(self):
        queryset = Cliente.objects.all().order_by('razon_social')
        query = self.request.GET.get('q')
        tipo = self.request.GET.get('tipo')

        if query:
            queryset = queryset.filter(
                Q(razon_social__icontains=query) | Q(id_sae__icontains=query)
            )
        
        if tipo == 'sae':
            queryset = queryset.filter(es_mostrador=False)
        elif tipo == 'mostrador':
            queryset = queryset.filter(es_mostrador=True)

        return queryset

class ClienteCreateView(LoginRequiredMixin, NonChoferRequiredMixin, AjaxSuccessMixin, CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = "dashboard/clientes/cliente_form.html"
    success_url = reverse_lazy('dashboard:cliente_list')
    ajax_success_message = "¡Cliente registrado exitosamente!"

class ClienteUpdateView(LoginRequiredMixin, NonChoferRequiredMixin, AjaxSuccessMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = "dashboard/clientes/cliente_form.html"
    success_url = reverse_lazy('dashboard:cliente_list')
    ajax_success_message = "¡Datos del cliente actualizados!"

class ObraListView(LoginRequiredMixin, NonChoferRequiredMixin, ListView):
    model = Obra
    template_name = "dashboard/clientes/obra_list.html"
    context_object_name = "obras"

    def get_queryset(self):
        self.cliente = get_object_or_404(Cliente, pk=self.kwargs['cliente_pk'])
        return Obra.objects.filter(cliente=self.cliente).order_by('alias')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cliente_obj'] = self.cliente
        return context

class ObraCreateView(LoginRequiredMixin, NonChoferRequiredMixin, AjaxSuccessMixin, CreateView):
    model = Obra
    form_class = ObraForm
    template_name = "dashboard/clientes/obra_form.html"
    ajax_success_message = "¡Obra/Dirección creada con éxito!"

    def get_initial(self):
        initial = super().get_initial()
        initial['cliente'] = get_object_or_404(Cliente, pk=self.kwargs['cliente_pk'])
        return initial

    def get_success_url(self):
        return reverse('dashboard:obra_list', kwargs={'cliente_pk': self.kwargs['cliente_pk']})

class ObraUpdateView(LoginRequiredMixin, NonChoferRequiredMixin, AjaxSuccessMixin, UpdateView):
    model = Obra
    form_class = ObraForm
    template_name = "dashboard/clientes/obra_form.html"
    ajax_success_message = "¡Obra actualizada con éxito!"

    def get_success_url(self):
        return reverse('dashboard:obra_list', kwargs={'cliente_pk': self.object.cliente.pk})
