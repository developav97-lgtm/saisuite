"""
SaiSuite — Companies: Permisos
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsSuperAdmin(BasePermission):
    """Solo superadmins de ValMen Tech pueden acceder."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and (getattr(request.user, 'is_superadmin', False) or request.user.is_staff)
        )


class IsCompanyAdmin(BasePermission):
    """Solo company_admin o superior pueden acceder."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        role = getattr(request.user, 'role', '')
        return (
            role in ('company_admin', 'valmen_admin', 'valmen_support')
            or request.user.is_staff
        )


class IsCompanyAdminOrReadOnly(BasePermission):
    """Company admin para escritura, cualquier usuario autenticado para lectura."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        role = getattr(request.user, 'role', '')
        return role in ('company_admin', 'valmen_admin') or request.user.is_staff
