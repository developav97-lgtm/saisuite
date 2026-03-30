"""
SaiSuite — LicensePermission (DRF Permission Class)
Verifica que la empresa del usuario tenga una licencia activa y vigente.
También valida que la sesión JWT sea activa (session_id en el payload).

Bloquea con HTTP 402 si:
  - La empresa no tiene licencia configurada
  - La licencia está vencida, expirada o suspendida

Bloquea con HTTP 401 si:
  - El session_id del JWT no corresponde a la sesión activa del usuario

Siempre permite:
  - Usuarios no autenticados (JWT los maneja por separado)
  - Superadmins (is_superadmin=True o is_staff=True)
  - Usuarios sin empresa asignada
  - Rutas de auth y licencias
"""
import logging
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import APIException, AuthenticationFailed

logger = logging.getLogger(__name__)

# Prefijos de path exentos
_EXEMPT_PREFIXES = (
    '/api/v1/auth/',
    '/api/v1/companies/licenses/',
    '/api/v1/admin/',
)


class LicenseRequired(APIException):
    status_code = 402
    default_code = 'license_required'
    default_detail = 'Tu empresa no tiene una licencia activa. Contacta a ValMen Tech para activarla.'


class LicensePermission(BasePermission):
    """
    Permission global que valida:
    1. Licencia activa de la empresa.
    2. Sesión activa (session_id en JWT vs UserSession en BD).
    """

    def has_permission(self, request, view) -> bool:
        # Usuarios no autenticados — dejar que IsAuthenticated los rechace
        if not request.user or not request.user.is_authenticated:
            return True

        # Superadmins siempre pasan
        if getattr(request.user, 'is_superadmin', False) or getattr(request.user, 'is_staff', False):
            return True

        # Rutas exentas
        for prefix in _EXEMPT_PREFIXES:
            if request.path.startswith(prefix):
                return True

        # Validar session_id si está en el JWT
        auth = getattr(request, 'auth', None)
        if auth is not None:
            session_id = auth.get('session_id') if hasattr(auth, 'get') else None
            if session_id:
                from apps.companies.services import SessionService
                session = SessionService.validate_session(session_id)
                if session is None:
                    logger.info('session_invalid_or_expired', extra={
                        'user_id': str(request.user.id),
                        'session_id': session_id,
                    })
                    raise AuthenticationFailed(
                        'Tu sesión ha expirado o fue cerrada desde otro dispositivo. Inicia sesión nuevamente.'
                    )
                # Actualizar actividad de la sesión
                session.touch()

        # Usuarios sin empresa asignada — no bloquear
        company = getattr(request.user, 'company', None)
        if company is None:
            return True

        # Verificar licencia
        try:
            from apps.companies.models import CompanyLicense
            lic = CompanyLicense.objects.get(company=company)
        except CompanyLicense.DoesNotExist:
            logger.warning('license_missing', extra={'company_id': str(company.id), 'path': request.path})
            raise LicenseRequired()

        if lic.status in ('expired', 'suspended') or lic.is_expired:
            logger.info('license_blocked', extra={'company_id': str(company.id), 'status': lic.status})
            raise LicenseRequired('Tu licencia ha vencido o está suspendida. Contacta a ValMen Tech para renovarla.')

        return True
