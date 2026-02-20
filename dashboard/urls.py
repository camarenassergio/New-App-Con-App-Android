from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardHomeView.as_view(), name='home'),
    path('unidades/', views.UnidadListView.as_view(), name='unidades_list'),
    path('unidades/nueva/', views.UnidadCreateView.as_view(), name='unidad_create'),
    path('unidades/<int:pk>/', views.UnidadDetailView.as_view(), name='unidad_detail'),
    path('unidades/<int:pk>/editar/', views.UnidadUpdateView.as_view(), name='unidad_update'),
    path('operadores/', views.OperadorListView.as_view(), name='operadores_list'),
    path('viajes/', views.ViajeListView.as_view(), name='viajes_list'),
    path('combustible/', views.CombustibleGeneralView.as_view(), name='combustible_general'),
    path('combustible/nuevo/', views.CombustibleCreateView.as_view(), name='combustible_create'),
    path('combustible/unidad/<int:pk>/', views.CombustibleUnidadDetailView.as_view(), name='combustible_unidad_detail'),
    path('combustible/editar/<int:pk>/', views.CombustibleUpdateView.as_view(), name='combustible_edit'),
    path('combustible/eliminar/<int:pk>/', views.CombustibleDeleteView.as_view(), name='combustible_delete'),
    
    # --- GESTIÓN DE GASTOS ---
    path('gastos/', views.GastoUnidadListView.as_view(), name='gastos_list'),
    path('gastos/nuevo/', views.GastoUnidadCreateView.as_view(), name='gastos_create'),
    
    path('usuarios/', views.UsuarioListView.as_view(), name='usuarios_list'),
    path('usuarios/nuevo/', views.UsuarioCreateView.as_view(), name='usuario_create'),
]
