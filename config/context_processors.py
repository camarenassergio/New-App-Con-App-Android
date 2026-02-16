from django.conf import settings

def environment_context(request):
    """
    Exposes the ENVIRONMENT ('DEV' or 'QA') variable to templates.
    """
    return {
        'ENVIRONMENT': getattr(settings, 'ENVIRONMENT', 'UNKNOWN'),
    }
