"""
SaiSuite — CRM Permissions
Permisos sobre roles existentes: company_admin, seller, viewer.
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class CanAccessCrm(BasePermission):
    """Verifica que la empresa del usuario tiene el módulo 'crm' activo."""
    message = 'Su empresa no tiene acceso al módulo CRM.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_staff or user.is_superuser:
            return True
        if not user.company:
            return False
        return user.company.modules.filter(module='crm', is_active=True).exists()


class CrmBasePermission(CanAccessCrm):
    """
    Permisos base CRM:
    - company_admin / valmen_admin: CRUD completo
    - seller: CRUD en registros propios, lectura del resto
    - viewer: solo lectura
    """
    ROLES_SOLO_LECTURA  = {'viewer', 'valmen_support'}
    ROLES_ADMIN         = {'company_admin', 'valmen_admin'}

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        user = request.user
        if user.is_staff or user.is_superuser:
            return True
        if request.method in SAFE_METHODS:
            return True
        return user.role not in self.ROLES_SOLO_LECTURA

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if user.is_staff or user.is_superuser or user.role in self.ROLES_ADMIN:
            return True
        # Seller puede editar/eliminar solo lo que le está asignado
        asignado = getattr(obj, 'asignado_a_id', None) or getattr(obj, 'asignado_a', None)
        if hasattr(asignado, 'id'):
            asignado = asignado.id
        return str(asignado) == str(user.id)


class CrmAdminPermission(CanAccessCrm):
    """Solo company_admin o valmen_admin pueden acceder (configuración, scoring rules, etc.)."""
    ROLES_ADMIN = {'company_admin', 'valmen_admin'}

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        user = request.user
        if user.is_staff or user.is_superuser:
            return True
        return user.role in self.ROLES_ADMIN


class CrmImportPermission(CanAccessCrm):
    """Para importar leads masivamente: company_admin o seller."""
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        user = request.user
        if user.is_staff or user.is_superuser:
            return True
        return user.role in {'company_admin', 'valmen_admin', 'seller'}
