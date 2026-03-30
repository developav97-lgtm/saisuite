"""
SaiSuite — Terceros: Permisos custom
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class HasTerceroPermission(BasePermission):
    """
    Verifica permisos granulares para el módulo de Terceros.

    - GET/HEAD/OPTIONS: requiere terceros.view
    - POST: requiere terceros.create
    - PATCH/PUT: requiere terceros.edit
    - DELETE: requiere terceros.delete

    Superusers y staff siempre tienen acceso.
    """

    _PERM_MAP = {
        'view':   'terceros.view',
        'create': 'terceros.create',
        'edit':   'terceros.edit',
        'delete': 'terceros.delete',
    }

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff:
            return True

        if request.method in SAFE_METHODS:
            accion = 'view'
        elif request.method == 'DELETE':
            accion = 'delete'
        elif request.method == 'POST':
            accion = 'create'
        else:
            accion = 'edit'

        return user.tiene_permiso(self._PERM_MAP[accion])
