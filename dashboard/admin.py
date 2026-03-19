from django.contrib import admin
from .models import (
    Unidad, ZonaEntrega, CodigoPostalCat, Viaje, EvaluacionEntrega, 
    Personal, ServicioMantenimiento, RegistroCombustible, 
    ConfiguracionLogistica, GastoUnidad, OrdenServicio, 
    ChecklistUnidad, InventarioLlanta, ConfiguracionGeneral, 
    MedicionNeumatico, Cliente, Obra, Pedido, Despacho, 
    EvidenciaMaterial, ViajeNuevo, MensajeInterno, Operador
)

@admin.register(Unidad)
class UnidadAdmin(admin.ModelAdmin):
    list_display = ('nUnidad', 'placas', 'marca', 'submarca', 'modelo_anio', 'tipo', 'en_servicio')
    search_fields = ('nUnidad', 'placas', 'no_serie')
    list_filter = ('tipo', 'marca', 'en_servicio')

@admin.register(Operador)
class OperadorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'licencia', 'vigencia_licencia', 'activo')
    search_fields = ('nombre', 'licencia')

@admin.register(ZonaEntrega)
class ZonaEntregaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tarifa_flete', 'costo_maniobra')
    search_fields = ('nombre', 'codigos_postales')

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('id_sae', 'razon_social', 'telefono_principal')
    search_fields = ('id_sae', 'razon_social')

class ObraInline(admin.TabularInline):
    model = Obra
    extra = 1

@admin.register(Obra)
class ObraAdmin(admin.ModelAdmin):
    list_display = ('alias', 'cliente', 'zona', 'esta_activa', 'fecha_ultimo_pedido')
    list_filter = ('esta_activa', 'zona')
    search_fields = ('alias', 'cliente__razon_social')

class DespachoInline(admin.TabularInline):
    model = Despacho
    extra = 0

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('folio_sae', 'cliente', 'obra', 'estado', 'es_urgente', 'fecha_registro')
    list_filter = ('estado', 'es_urgente')
    search_fields = ('folio_sae', 'cliente__razon_social', 'obra__alias')
    inlines = [DespachoInline]

@admin.register(Despacho)
class DespachoAdmin(admin.ModelAdmin):
    list_display = ('id', 'pedido', 'tipo_envio', 'estado', 'peso_asignado_kg')
    list_filter = ('tipo_envio', 'estado')

@admin.register(ViajeNuevo)
class ViajeNuevoAdmin(admin.ModelAdmin):
    list_display = ('id', 'chofer', 'unidad', 'fecha_creacion', 'completado')
    list_filter = ('completado',)

@admin.register(MensajeInterno)
class MensajeInternoAdmin(admin.ModelAdmin):
    list_display = ('remitente', 'destinatario', 'leido', 'fecha_envio')
    list_filter = ('leido',)

admin.site.register(CodigoPostalCat)
admin.site.register(Viaje)
admin.site.register(EvaluacionEntrega)
admin.site.register(Personal)
admin.site.register(ServicioMantenimiento)
admin.site.register(RegistroCombustible)
admin.site.register(ConfiguracionLogistica)
admin.site.register(GastoUnidad)
admin.site.register(OrdenServicio)
admin.site.register(ChecklistUnidad)
admin.site.register(InventarioLlanta)
admin.site.register(ConfiguracionGeneral)
admin.site.register(MedicionNeumatico)
admin.site.register(EvidenciaMaterial)
