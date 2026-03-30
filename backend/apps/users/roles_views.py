"""
SaiSuite — Roles & Permissions Views
Las views SOLO orquestan: reciben request → llaman service → retornan response.
"""
import logging
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.companies.permissions import IsCompanyAdmin
from .models import Permission, Role
from .serializers import (
    PermissionSerializer,
    RoleSerializer,
    RoleCreateUpdateSerializer,
)

logger = logging.getLogger(__name__)


class PermissionListView(APIView):
    """GET /api/v1/auth/permissions/ — lista todos los permisos del sistema."""

    permission_classes = [IsAuthenticated, IsCompanyAdmin]

    def get(self, request):
        permisos = Permission.objects.all()
        return Response(PermissionSerializer(permisos, many=True).data)


class PermissionByModuleView(APIView):
    """GET /api/v1/auth/permissions/by-module/ — permisos agrupados por módulo."""

    permission_classes = [IsAuthenticated, IsCompanyAdmin]

    def get(self, request):
        permisos = Permission.objects.all()
        agrupados: dict = {}
        for permiso in permisos:
            agrupados.setdefault(permiso.modulo, []).append(
                PermissionSerializer(permiso).data
            )
        return Response(agrupados)


class RoleListCreateView(APIView):
    """
    GET  /api/v1/auth/roles/ — lista roles de la empresa.
    POST /api/v1/auth/roles/ — crea un rol personalizado.
    """

    permission_classes = [IsAuthenticated, IsCompanyAdmin]

    def get(self, request):
        company = getattr(request.user, 'effective_company', None)
        if not company:
            return Response([])
        roles = (
            Role.objects
            .filter(empresa=company)
            .prefetch_related('permisos', 'usuarios')
        )
        return Response(RoleSerializer(roles, many=True).data)

    def post(self, request):
        company = getattr(request.user, 'effective_company', None)
        if not company:
            return Response({'error': 'Sin empresa activa'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = RoleCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = serializer.save(empresa=company)

        logger.info('rol_creado', extra={
            'user_id':    str(request.user.id),
            'empresa_id': str(company.id),
            'rol_id':     role.id,
            'rol_nombre': role.nombre,
        })
        return Response(RoleSerializer(role).data, status=status.HTTP_201_CREATED)


class RoleDetailView(APIView):
    """
    GET    /api/v1/auth/roles/<pk>/ — detalle de un rol.
    PATCH  /api/v1/auth/roles/<pk>/ — actualiza nombre/descripción/permisos.
    DELETE /api/v1/auth/roles/<pk>/ — elimina rol (no sistema, sin usuarios).
    """

    permission_classes = [IsAuthenticated, IsCompanyAdmin]

    def _get_role(self, request, pk: int) -> Role:
        company = getattr(request.user, 'effective_company', None)
        try:
            return (
                Role.objects
                .prefetch_related('permisos', 'usuarios')
                .get(id=pk, empresa=company)
            )
        except Role.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound('Rol no encontrado.')

    def get(self, request, pk: int):
        role = self._get_role(request, pk)
        return Response(RoleSerializer(role).data)

    def patch(self, request, pk: int):
        role = self._get_role(request, pk)
        serializer = RoleCreateUpdateSerializer(role, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        role = serializer.save()
        logger.info('rol_actualizado', extra={
            'user_id': str(request.user.id), 'rol_id': role.id,
        })
        return Response(RoleSerializer(role).data)

    def delete(self, request, pk: int):
        role = self._get_role(request, pk)

        if role.es_sistema:
            return Response(
                {'error': 'No se pueden eliminar roles de sistema.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        count = role.usuarios.count()
        if count > 0:
            return Response(
                {
                    'error': 'No se puede eliminar un rol con usuarios asignados.',
                    'usuarios_count': count,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info('rol_eliminado', extra={
            'user_id': str(request.user.id), 'rol_id': role.id, 'rol_nombre': role.nombre,
        })
        role.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
