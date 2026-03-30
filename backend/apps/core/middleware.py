"""
SaiSuite — CompanyMiddleware
Inyecta la empresa del usuario autenticado en thread local.
CompanyManager lo usa para filtrar queries automáticamente.
"""
import logging
import threading

logger = logging.getLogger(__name__)
_thread_locals = threading.local()


def get_current_company():
    """Retorna la Company del request actual, o None."""
    return getattr(_thread_locals, 'company', None)


class CompanyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.company = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            effective = getattr(request.user, 'effective_company', None)
            if effective:
                _thread_locals.company = effective
        response = self.get_response(request)
        _thread_locals.company = None
        return response
