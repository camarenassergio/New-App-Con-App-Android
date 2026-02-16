import time
from django.core.cache import cache
from django.http import HttpResponseForbidden

class SimpleRateLimitMiddleware:
    """
    Simple IP-based Rate Limiting Middleware
    Limits requests to prevent basic DoS attacks.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limit = 100  # Requests
        self.period = 60       # Seconds

    def __call__(self, request):
        ip = self.get_client_ip(request)
        if not ip:
            return self.get_response(request)

        cache_key = f'ratelimit_{ip}'
        request_history = cache.get(cache_key, [])
        
        now = time.time()
        
        # Remove old requests outside the window
        request_history = [t for t in request_history if now - t < self.period]
        
        if len(request_history) >= self.rate_limit:
            return HttpResponseForbidden("403 Forbidden: Demasiadas solicitudes. Intenta de nuevo más tarde.")
        
        request_history.append(now)
        cache.set(cache_key, request_history, self.period)

        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
