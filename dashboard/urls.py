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

    path('usuarios/', views.UsuarioListView.as_view(), name='usuarios_list'),
    path('usuarios/nuevo/', views.UsuarioCreateView.as_view(), name='usuario_create'),
    
    # --- PERFIL DE USUARIO ---
    path('mi-perfil/', views.UsuarioPerfilView.as_view(), name='usuario_perfil'),
    path('cambiar-password/', views.UsuarioPasswordChangeView.as_view(), name='usuario_cambiar_password'),
]
