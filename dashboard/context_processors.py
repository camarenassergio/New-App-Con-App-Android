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
