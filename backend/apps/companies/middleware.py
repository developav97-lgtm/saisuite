"""
SaiSuite — LicensePermission (DRF Permission Class)
Verifica que la empresa del usuario tenga una licencia activa y vigente.
Bloquea requests con HTTP 402 si:
  - La empresa no tiene licencia configurada
  - La licencia está vencida, expirada o suspendida

Siempre permite:
  - Usuarios no autenticados (JWT los maneja por separado)
  - Superadmins (is_superadmin=True o is_staff=True)
  - Usuarios sin empresa asignada
  - Rutas de licencia (para poder crear/ver la propia)
"""
import logging
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import APIException

logger = logging.getLogger(__name__)

# Prefijos de path exentos (la permission no aplica)
_EXEMPT_PREFIXES = (
    '/api/v1/auth/',
    '/api/v1/companies/licenses/',
)


class LicenseRequired(APIException):
    status_code = 402
    default_code = 'license_required'
    default_detail = 'Tu empresa no tiene una licencia activa. Contacta a ValMen Tech para activarla.'


class LicensePermission(BasePermission):
    """
    Permission global que valida la licencia de la empresa.
    Se agrega a DEFAULT_PERMISSION_CLASSES en settings.
    """

    def has_permission(self, request, view) -> bool:
        # Usuarios no autenticados — dejar que IsAuthenticated los rechace
        if not request.user or not request.user.is_authenticated:
            return True

        # Superadmins siempre pasan
        if getattr(request.user, 'is_superadmin', False) or getattr(request.user, 'is_staff', False):
            return True

        # Rutas exentas (auth, licenses)
        for prefix in _EXEMPT_PREFIXES:
            if request.path.startswith(prefix):
                return True

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
