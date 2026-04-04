from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardHomeView.as_view(), name='home'),
    path('unidades/', views.UnidadListView.as_view(), name='unidades_list'),
    path('unidades/nueva/', views.UnidadCreateView.as_view(), name='unidad_create'),
    path('unidades/<int:pk>/', views.UnidadDetailView.as_view(), name='unidad_detail'),
    path('unidades/<int:pk>/editar/', views.UnidadUpdateView.as_view(), name='unidad_update'),
    path('unidades/<int:pk>/toggle/', views.UnidadToggleEstadoView.as_view(), name='unidad_toggle'),
    path('operadores/', views.OperadorListView.as_view(), name='operadores_list'),
    path('operadores/nuevo/', views.OperadorCreateView.as_view(), name='operador_create'),
    path('operadores/<int:pk>/editar/', views.OperadorUpdateView.as_view(), name='operador_update'),
    path('viajes/', views.ViajeListView.as_view(), name='viajes_list'),
    path('viajes/nuevo/', views.ViajeCreateView.as_view(), name='viaje_create'),
    path('viajes/<int:pk>/editar/', views.ViajeUpdateView.as_view(), name='viaje_update'),
    path('combustible/', views.CombustibleGeneralView.as_view(), name='combustible_general'),
    path('combustible/nuevo/', views.CombustibleCreateView.as_view(), name='combustible_create'),
    path('combustible/unidad/<int:pk>/', views.CombustibleUnidadDetailView.as_view(), name='combustible_unidad_detail'),
    path('combustible/editar/<int:pk>/', views.CombustibleUpdateView.as_view(), name='combustible_edit'),
    path('combustible/eliminar/<int:pk>/', views.CombustibleDeleteView.as_view(), name='combustible_delete'),
    
    # --- GESTIÓN DE GASTOS ---
    path('gastos/', views.GastoUnidadListView.as_view(), name='gastos_list'),
    path('gastos/nuevo/', views.GastoUnidadCreateView.as_view(), name='gastos_create'),
    
    # --- ÓRDENES DE SERVICIO ---
    path('ordenes-servicio/', views.OrdenServicioListView.as_view(), name='orden_servicio_list'),
    path('ordenes-servicio/nueva/', views.OrdenServicioCreateView.as_view(), name='orden_servicio_create'),
    path('ordenes-servicio/<int:pk>/', views.OrdenServicioDetailView.as_view(), name='orden_servicio_detail'),
    
    # --- CHECKLIST DIARIO ---
    path('checklist/', views.ChecklistUnidadListView.as_view(), name='checklist_unidad_list'),
    path('checklist/nuevo/', views.ChecklistUnidadCreateView.as_view(), name='checklist_unidad_create'),
    
    # --- INVENTARIO LLANTAS ---
    path('llantas/', views.InventarioLlantaListView.as_view(), name='inventario_llanta_list'),
    path('llantas/nueva/', views.InventarioLlantaCreateView.as_view(), name='inventario_llanta_create'),
    path('llantas/<int:pk>/editar/', views.InventarioLlantaUpdateView.as_view(), name='inventario_llanta_update'),

    # --- EVALUACION DE ENTREGA SDC ---
    path('viaje/<int:viaje_id>/evaluacion/nueva/', views.EvaluacionEntregaCreateView.as_view(), name='evaluacion_entrega_create'),
    path('evaluacion/<int:pk>/editar/', views.EvaluacionEntregaUpdateView.as_view(), name='evaluacion_entrega_update'),

    # --- ZONAS DE ENTREGA CRUD ---
    path('zonas/', views.ZonaEntregaListView.as_view(), name='zona_entrega_list'),
    path('zonas/nueva/', views.ZonaEntregaCreateView.as_view(), name='zona_entrega_create'),
    path('zonas/<int:pk>/editar/', views.ZonaEntregaUpdateView.as_view(), name='zona_entrega_update'),
    path('zonas/<int:pk>/eliminar/', views.ZonaEntregaDeleteView.as_view(), name='zona_entrega_delete'),
    path('zonas/importar/', views.ZonaEntregaImportView.as_view(), name='zona_entrega_import'),
    path('zonas/mapa/', views.ZonaEntregaMapView.as_view(), name='zona_entrega_map'),
    path('api/zonas-geojson/', views.ZonasGeoJSONView.as_view(), name='zonas_geojson_api'),
    path('api/colonias-por-cp/', views.colonias_por_cp_api, name='colonias_por_cp_api'),
    path('api/calcular-centroide/', views.calcular_centroide_zona_api, name='calcular_centroide_api'),
    path('api/geojson-por-cp/', views.geojson_por_cp_api, name='geojson_por_cp_api'),
    path('api/agregar-cp-a-zona/', views.agregar_cp_a_zona_api, name='agregar_cp_a_zona_api'),
    path('api/calcular-flete/', views.CalcularFleteSugeridoView.as_view(), name='calcular_flete_api'),
    path('api/buscar-colonia/', views.buscar_colonia_api, name='buscar_colonia_api'),
    path('api/solicitar-autorizacion-zona/', views.solicitar_autorizacion_zona_api, name='solicitar_autorizacion_zona_api'),
    path('api/verificar-zona-cp/', views.verificar_zona_por_cp_api, name='verificar_zona_por_cp_api'),

    path('usuarios/', views.UsuarioListView.as_view(), name='usuarios_list'),
    path('usuarios/nuevo/', views.UsuarioCreateView.as_view(), name='usuario_create'),
    path('usuarios/<int:pk>/editar/', views.UsuarioUpdateView.as_view(), name='usuario_update'),
    path('usuarios/<int:pk>/toggle-estado/', views.UsuarioToggleActiveView.as_view(), name='usuario_toggle_estado'),
    
    # --- CONFIGURACION GENERAL ---
    path('configuraciones/', views.ConfiguracionGeneralUpdateView.as_view(), name='configuracion_general'),
    path('configuraciones/backup/', views.DatabaseBackupView.as_view(), name='database_backup'),
    path('configuraciones/restore/', views.DatabaseRestoreView.as_view(), name='database_restore'),
    
    # --- PERFIL DE USUARIO ---
    path('mi-perfil/', views.UsuarioPerfilView.as_view(), name='usuario_perfil'),
    path('cambiar-password/', views.UsuarioPasswordChangeView.as_view(), name='usuario_cambiar_password'),
    path('cambiar-modo/', views.CambiarModoVista.as_view(), name='cambiar_modo'),

    # --- LOGISTICA (PASO 2 - FASE 2) ---
    path('logistica/dashboard/', views.LogisticaDashboardView.as_view(), name='logistica_dashboard'),
    path('logistica/armar-viaje/', views.LogisticaArmarViajeView.as_view(), name='logistica_armar_viaje'),
    path('logistica/pedido/<int:pk>/dividir/', views.PedidoDividirView.as_view(), name='pedido_dividir'),

    # --- MOSTRADOR (PASO 1 - FASE 2) ---
    path('mostrador/dashboard/', views.MostradorDashboardView.as_view(), name='mostrador_dashboard'),
    path('mostrador/', views.MostradorHomeView.as_view(), name='mostrador_home'),
    path('mostrador/cotizar-modal/', views.CotizadorFleteModalView.as_view(), name='cotizador_modal'),
    path('mostrador/cotizar-accion/', views.CalcularFleteAccionView.as_view(), name='cotizar_accion'),
    path('mostrador/cliente-busqueda/', views.ClienteSAEBusquedaView.as_view(), name='cliente_sae_busqueda'),
    path('mostrador/cliente-buscador-modal/', views.ClienteBuscadorModalView.as_view(), name='cliente_buscador_modal'),
    path('mostrador/cliente-buscador-accion/', views.ClienteBuscadorAccionView.as_view(), name='cliente_buscador_accion'),
    path('mostrador/obras-select/', views.ObraSelectFragmentView.as_view(), name='obras_select_fragment'),
    path('mostrador/obra-nueva-modal/', views.ObraCreateModalView.as_view(), name='obra_create_modal'),
    path('pedido/nuevo/', views.PedidoCreateView.as_view(), name='pedido_create'),
    path('pedido/<int:pk>/', views.PedidoDetailView.as_view(), name='pedido_detail'),
    path('pedido/<int:pk>/editar/', views.PedidoUpdateView.as_view(), name='pedido_update'),
    path('pedido/<int:pk>/desbloquear/', views.PedidoUnlockView.as_view(), name='pedido_unlock'),
    path('pedido/<int:pk>/cancelar/', views.PedidoCancelView.as_view(), name='pedido_cancel'),
    path('pedido/<int:pk>/cambiar-estado/', views.PedidoCambiarEstadoView.as_view(), name='pedido_cambiar_estado'),

    # --- GESTIÓN DE ALMACÉN (PASO 2 - FLUJO OPERATIVO) ---
    path('almacen/dashboard/', views.AlmacenDashboardView.as_view(), name='almacen_dashboard'),
    path('almacen/preparacion/', views.AlmacenPreparacionListView.as_view(), name='almacen_preparacion'),
    path('almacen/carga/', views.AlmacenCargaListView.as_view(), name='almacen_carga'),

    # --- GESTIÓN DE CLIENTES Y OBRAS (ADMIN/MOSTRADOR) ---
    path('clientes/', views.ClienteListView.as_view(), name='cliente_list'),
    path('clientes/nuevo/', views.ClienteCreateView.as_view(), name='cliente_create'),
    path('clientes/<int:pk>/editar/', views.ClienteUpdateView.as_view(), name='cliente_update'),
    path('clientes/<int:cliente_pk>/obras/', views.ObraListView.as_view(), name='obra_list'),
    path('clientes/<int:cliente_pk>/obras/nueva/', views.ObraCreateView.as_view(), name='obra_create'),
    path('obras/<int:pk>/editar/', views.ObraUpdateView.as_view(), name='obra_update'),

    # --- NOTIFICACIONES ---
    path('notificaciones/', views.NotificacionListView.as_view(), name='notificaciones_list'),
    path('notificaciones/dropdown/', views.NotificacionesDropdownView.as_view(), name='notificaciones_dropdown'),
    path('notificaciones/<int:pk>/marcar-leida/', views.NotificacionMarcarLeidaView.as_view(), name='notificacion_marcar_leida'),
    path('notificaciones/marcar-todas-leidas/', views.marcar_todas_leidas, name='notificaciones_marcar_todas_leidas'),
    path('notificaciones/count/', views.notificaciones_count_ajax, name='notificaciones_count'),
    path('api/enviar-mensaje/', views.DirectMessageView.as_view(), name='enviar_mensaje_api'),
    path('mostrador/cliente/<int:pk>/update-telefono/', views.ClienteUpdateTelefonoModalView.as_view(), name='cliente_update_telefono_modal'),
]
