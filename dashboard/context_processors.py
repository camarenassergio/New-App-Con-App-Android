from dashboard.models import ConfiguracionLogistica, Notificacion

def contingencia_processor(request):
    """
    Context processor para inyectar el estado del Plan de Contingencia Ambiental
    en todos los templates globales.
    """
    try:
        config = ConfiguracionLogistica.objects.first()
        if config:
            return {
                'estado_contingencia': config.estado_contingencia,
                'mensaje_contingencia': config.mensaje_alerta,
            }
    except Exception:
        # Falla silenciosa si la BD no está inicializada o falla
        pass
        
    return {
        'estado_contingencia': 'NORMAL',
        'mensaje_contingencia': '',
    }

def notificaciones_processor(request):
    """
    Context processor para inyectar el contador de notificaciones no leídas.
    """
    if request.user.is_authenticated:
        try:
            count = Notificacion.objects.filter(usuario=request.user, leido=False).count()
            return {'notificaciones_unread_count': count}
        except Exception:
            pass
    return {'notificaciones_unread_count': 0}

def modos_vista_processor(request):
    """
    Provee los modos de vista permitidos para el Workspace Switcher.
    """
    if request.user.is_authenticated and hasattr(request.user, 'personal'):
        # Usar la base de datos real para evadir manipulaciones del middleware
        real_personal = request.user.personal.__class__.objects.get(pk=request.user.personal.pk)
        puesto_base = request.session.get('puesto_base', real_personal.puesto)
        
        opciones = [puesto_base]
        
        if request.user.is_superuser:
            opciones = ['ADMIN', 'MOSTRADOR', 'LOGISTICA', 'RUTAS', 'ALMACEN', 'CHOFER', 'CAJA']
        elif real_personal.roles_secundarios:
            opciones.extend([r.strip() for r in real_personal.roles_secundarios.split(',') if r.strip()])
        
        # Eliminar duplicados manteniendo orden
        vistos = set()
        opciones_finales = [x for x in opciones if not (x in vistos or vistos.add(x))]
        
        if len(opciones_finales) > 1:
            return {'modos_vista_permitidos': opciones_finales, 'modo_vista_actual': request.user.personal.puesto}
            
    return {}
