"""
SaiSuite — Notifications: Permisos
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsNotificacionOwner(BasePermission):
    """Solo el destinatario puede ver y gestionar sus propias notificaciones."""
    message = 'Solo puede acceder a sus propias notificaciones.'

    def has_object_permission(self, request, view, obj):
        return obj.usuario_id == request.user.id


class ComentarioPermission(BasePermission):
    """
    - Leer: cualquier usuario autenticado con acceso a la empresa.
    - Crear: cualquier usuario autenticado.
    - Editar: solo el autor.
    - Eliminar: autor o company_admin / valmen_admin.
    """
    ROLES_ADMIN = {'company_admin', 'valmen_admin'}

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if user.is_staff or getattr(user, 'role', '') in self.ROLES_ADMIN:
            return True
        if request.method == 'DELETE':
            return obj.autor_id == user.id
        # PUT / PATCH: solo el autor
        return obj.autor_id == user.id
