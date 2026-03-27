"""
SaiSuite — Proyectos: Permisos custom
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class CanAccessProyectos(BasePermission):
    """
    Verifica que la empresa del usuario tiene el módulo 'proyectos' activo.
    """
    message = 'Su empresa no tiene acceso al módulo de Proyectos.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if not user.company:
            # valmen_admin / valmen_support no tienen company — tienen acceso total
            return user.is_staff
        return user.company.modules.filter(module='proyectos', is_active=True).exists()


class CanEditProyecto(BasePermission):
    """
    Solo company_admin o el gerente del proyecto pueden editar.
    Viewers y valmen_support tienen acceso de solo lectura.
    """
    message = 'No tiene permisos para modificar este proyecto.'

    ROLES_SOLO_LECTURA = {'viewer', 'valmen_support'}

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.role not in self.ROLES_SOLO_LECTURA

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if user.role == 'company_admin' or user.is_staff:
            return True
        # El gerente puede editar su propio proyecto
        return obj.gerente_id == user.id


class TaskPermission(CanAccessProyectos):
    """
    Permisos para Task:
    - Ver: Cualquier usuario con acceso al módulo proyectos
    - Crear/Editar: company_admin, seller, o usuarios con rol de edición
    - Eliminar: Solo company_admin o valmen_admin
    Hereda la validación de módulo activo de CanAccessProyectos.
    """

    ROLES_SOLO_LECTURA = {'viewer', 'valmen_support'}
    ROLES_PUEDE_ELIMINAR = {'company_admin', 'valmen_admin'}

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if request.method == 'DELETE':
            return user.role in self.ROLES_PUEDE_ELIMINAR or user.is_staff
        return user.role not in self.ROLES_SOLO_LECTURA

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        # Admins tienen acceso total
        if user.role in self.ROLES_PUEDE_ELIMINAR or user.is_staff:
            return True
        # Responsable puede editar su tarea (pero no eliminar)
        if request.method in ('PUT', 'PATCH'):
            return obj.responsable_id == user.id
        return False

