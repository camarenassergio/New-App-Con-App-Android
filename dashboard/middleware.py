class RoleSwitchMiddleware:
    """
    Middleware that overrides the user's active role (puesto) for the duration of the request
    if a 'modo_vista' has been set in the session.
    This allows the "Workspace Switcher" to magically change the UI without altering the DB.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and hasattr(request.user, 'personal'):
            # Store the original puesto to prevent it from being overridden everywhere
            if 'puesto_base' not in request.session:
                request.session['puesto_base'] = request.user.personal.puesto
                
            modo_vista = request.session.get('modo_vista')
            if modo_vista:
                # Override the user's puesto attribute dynamically for this request
                request.user.personal.puesto = modo_vista
                
        response = self.get_response(request)
        return response
