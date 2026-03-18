"""
SaiSuite — Users: Permisos
"""
from rest_framework.permissions import BasePermission


class HasModuleAccess(BasePermission):
    """
    Verifica que el usuario tenga acceso al módulo especificado.

    Uso:
        class MyView(APIView):
            permission_classes = [IsAuthenticated, HasModuleAccess]
            required_module = 'proyectos'

    Si la view no define `required_module`, el permiso pasa (no restringe).
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        required_module = getattr(view, 'required_module', None)
        if not required_module:
            return True  # Sin módulo requerido, no se restringe

        company = getattr(request.user, 'company', None)
        if not company:
            return False

        from apps.companies.models import CompanyModule
        return CompanyModule.objects.filter(
            company=company,
            module=required_module,
            is_active=True,
        ).exists()
