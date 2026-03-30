"""
SaiSuite — Notifications: Views
Las views SOLO orquestan: reciben request → llaman service → retornan response.
"""
import logging
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import Notificacion, Comentario, PreferenciaNotificacion
from .serializers import (
    NotificacionSerializer,
    ComentarioSerializer,
    ComentarioCreateSerializer,
    ComentarioEditSerializer,
    PreferenciaNotificacionSerializer,
    NoLeidasCountSerializer,
)
from .services import NotificacionService, ComentarioService
from .filters import NotificacionFilter, ComentarioFilter
from .permissions import IsNotificacionOwner, ComentarioPermission

logger = logging.getLogger(__name__)


class NotificacionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Notificaciones del usuario autenticado.
    El usuario solo ve las suyas — filtrado automático por usuario en get_queryset.
    """
    serializer_class   = NotificacionSerializer
    permission_classes = [IsAuthenticated, IsNotificacionOwner]
    filter_backends    = [DjangoFilterBackend, OrderingFilter]
    filterset_class    = NotificacionFilter
    ordering_fields    = ['created_at']
    ordering           = ['-created_at']

    def get_queryset(self):
        return (
            Notificacion.objects
            .filter(usuario=self.request.user)
            .select_related('content_type')
            .order_by('-created_at')
        )

    @action(detail=True, methods=['post'], url_path='leer')
    def leer(self, request, pk=None):
        """Marca una notificación como leída."""
        try:
            notif = NotificacionService.marcar_leida(pk, request.user)
        except Notificacion.DoesNotExist:
            return Response({'detail': 'No encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(NotificacionSerializer(notif).data)

    @action(detail=True, methods=['post'], url_path='marcar-no-leida')
    def marcar_no_leida(self, request, pk=None):
        """Marca una notificación como no leída."""
        try:
            notif = NotificacionService.marcar_no_leida(pk, request.user)
        except Notificacion.DoesNotExist:
            return Response({'detail': 'No encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(NotificacionSerializer(notif).data)

    @action(detail=False, methods=['post'], url_path='leer-todas')
    def leer_todas(self, request):
        """Marca todas las notificaciones del usuario como leídas."""
        count = NotificacionService.marcar_todas_leidas(request.user)
        return Response({'count': count})

    @action(detail=False, methods=['get'], url_path='no-leidas')
    def no_leidas(self, request):
        """Devuelve el conteo de notificaciones sin leer."""
        count = NotificacionService.contar_sin_leer(request.user)
        return Response(NoLeidasCountSerializer({'count': count}).data)

    @action(detail=False, methods=['get'], url_path='agrupadas')
    def agrupadas(self, request):
        """Lista notificaciones agrupadas por tipo y objeto."""
        items = NotificacionService.agrupar_notificaciones(request.user)
        return Response(items)

    @action(detail=False, methods=['post'], url_path='marcar-grupo-leidas')
    def marcar_grupo_leidas(self, request):
        """Marca como leídas todas las notificaciones de un grupo."""
        ids = request.data.get('notificaciones_ids', [])
        if not ids:
            return Response({'detail': 'notificaciones_ids requerido.'}, status=status.HTTP_400_BAD_REQUEST)
        count = NotificacionService.marcar_grupo_leidas(ids, request.user)
        return Response({'count': count})

    @action(detail=True, methods=['post'], url_path='snooze')
    def snooze(self, request, pk=None):
        """Pospone una notificación. Body: { minutos: int }"""
        minutos = request.data.get('minutos')
        if not minutos or not isinstance(minutos, int) or minutos <= 0:
            return Response({'detail': 'minutos debe ser un entero positivo.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            notif = NotificacionService.snooze(pk, request.user, minutos)
        except Notificacion.DoesNotExist:
            return Response({'detail': 'No encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(NotificacionSerializer(notif).data)

    @action(detail=True, methods=['post'], url_path='remind-me')
    def remind_me(self, request, pk=None):
        """Marca como leída y crea recordatorio futuro. Body: { minutos: int }"""
        minutos = request.data.get('minutos')
        if not minutos or not isinstance(minutos, int) or minutos <= 0:
            return Response({'detail': 'minutos debe ser un entero positivo.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            recordatorio = NotificacionService.remind_me(pk, request.user, minutos)
        except Notificacion.DoesNotExist:
            return Response({'detail': 'No encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(NotificacionSerializer(recordatorio).data, status=status.HTTP_201_CREATED)


class ComentarioViewSet(viewsets.ModelViewSet):
    """
    CRUD de comentarios.
    Filtrar por objeto: ?content_type_model=tarea&object_id=<uuid>&solo_raiz=true
    """
    permission_classes = [IsAuthenticated, ComentarioPermission]
    filter_backends    = [DjangoFilterBackend, OrderingFilter]
    filterset_class    = ComentarioFilter
    ordering_fields    = ['created_at']
    ordering           = ['created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return ComentarioCreateSerializer
        if self.action in ('update', 'partial_update'):
            return ComentarioEditSerializer
        return ComentarioSerializer

    def get_queryset(self):
        return (
            Comentario.objects
            .filter(padre__isnull=True)          # solo raíz por defecto
            .select_related('autor', 'content_type')
            .prefetch_related('respuestas__autor', 'menciones')
            .order_by('created_at')
        )

    def create(self, request, *args, **kwargs):
        serializer = ComentarioCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        ct = ContentType.objects.get(model=data['content_type_model'])
        try:
            objeto = ct.get_object_for_this_type(pk=data['object_id'])
        except Exception:
            return Response(
                {'detail': 'Objeto relacionado no encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            comentario = ComentarioService.crear_comentario(
                autor=request.user,
                objeto_relacionado=objeto,
                texto=data['texto'],
                padre=data.get('padre_obj'),
            )
        except ValidationError as exc:
            return Response({'detail': exc.message}, status=status.HTTP_400_BAD_REQUEST)

        # Si es respuesta, devolver el comentario padre actualizado (con la respuesta incluida)
        if comentario.padre_id:
            padre = Comentario.objects.prefetch_related(
                'respuestas__autor', 'menciones',
            ).select_related('autor').get(id=comentario.padre_id)
            return Response(ComentarioSerializer(padre).data, status=status.HTTP_201_CREATED)

        return Response(
            ComentarioSerializer(
                Comentario.objects.prefetch_related('respuestas__autor', 'menciones')
                .select_related('autor').get(id=comentario.id)
            ).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial    = kwargs.pop('partial', False)
        comentario = self.get_object()

        serializer = ComentarioEditSerializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        comentario = ComentarioService.editar_comentario(
            comentario=comentario,
            texto=serializer.validated_data['texto'],
        )
        return Response(ComentarioSerializer(comentario).data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class PreferenciaNotificacionViewSet(
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Preferencias de notificación del usuario autenticado.
    Se crean on-demand; aquí solo se leen y actualizan.
    """
    serializer_class   = PreferenciaNotificacionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PreferenciaNotificacion.objects.filter(usuario=self.request.user)

    def get_object(self):
        """Lookup por 'tipo' en lugar de pk para simplificar el frontend."""
        tipo = self.kwargs.get('pk')
        obj, _ = PreferenciaNotificacion.objects.get_or_create(
            company=self.request.user.effective_company,
            usuario=self.request.user,
            tipo=tipo,
            defaults={'habilitado_app': True},
        )
        self.check_object_permissions(self.request, obj)
        return obj
