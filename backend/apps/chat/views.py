"""
SaiSuite — Chat: Views
Las views SOLO orquestan: reciben request -> llaman service -> retornan response.
"""
import logging

from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .serializers import (
    AutocompleteEntidadSerializer,
    AutocompleteUsuarioSerializer,
    ConversacionCreateSerializer,
    ConversacionListSerializer,
    MensajeCreateSerializer,
    MensajeSerializer,
)
from .services import ChatService

logger = logging.getLogger(__name__)


class MensajePagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100


# ── Conversaciones ──────────────────────────────────────────────────


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def conversaciones_view(request):
    """GET: Listar conversaciones. POST: Crear/obtener conversacion."""
    if request.method == 'GET':
        conversaciones = ChatService.listar_conversaciones(request.user)
        serializer = ConversacionListSerializer(
            conversaciones, many=True, context={'request': request},
        )
        return Response(serializer.data)

    # POST — crear u obtener conversacion
    serializer = ConversacionCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    from apps.users.models import User
    try:
        destinatario = User.objects.get(
            id=serializer.validated_data['destinatario_id'],
            company=request.user.effective_company,
        )
    except User.DoesNotExist:
        return Response(
            {'error': 'Usuario no encontrado'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if destinatario.id == request.user.id:
        return Response(
            {'error': 'No puedes crear una conversacion contigo mismo'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    conv = ChatService.obtener_o_crear_conversacion(
        request.user, destinatario, request.user.effective_company,
    )
    output = ConversacionListSerializer(conv, context={'request': request})
    return Response(output.data, status=status.HTTP_200_OK)


# ── Mensajes ────────────────────────────────────────────────────────


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mensajes_view(request, conversacion_id):
    """GET: Listar mensajes de una conversacion (paginado)."""
    try:
        queryset = ChatService.listar_mensajes(conversacion_id, request.user)
    except PermissionError as e:
        return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)

    paginator = MensajePagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = MensajeSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enviar_mensaje_view(request, conversacion_id):
    """POST: Enviar un mensaje en una conversacion."""
    serializer = MensajeCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        mensaje = ChatService.enviar_mensaje(
            conversacion_id=conversacion_id,
            remitente=request.user,
            contenido=serializer.validated_data.get('contenido', ''),
            imagen_url=serializer.validated_data.get('imagen_url', ''),
            responde_a_id=serializer.validated_data.get('responde_a_id'),
        )
    except PermissionError as e:
        return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)

    output = MensajeSerializer(mensaje)
    return Response(output.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def marcar_leido_view(request, mensaje_id):
    """POST: Marcar un mensaje como leido."""
    try:
        mensaje = ChatService.marcar_leido(mensaje_id, request.user)
    except PermissionError as e:
        return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)

    return Response({'status': 'ok', 'leido_at': mensaje.leido_at})


# ── Autocomplete ────────────────────────────────────────────────────


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def autocomplete_entidades_view(request):
    """GET: Autocomplete para entidades de proyecto como [PRY-001]."""
    query = request.query_params.get('query', '').strip()
    tipo = request.query_params.get('tipo', '').strip()
    company = request.user.effective_company

    if not query or len(query) < 2:
        return Response([])

    from apps.proyectos.models import Project, Task

    results = []

    type_map = {
        'proyecto': (Project, 'PRY'),
        'tarea': (Task, 'TAR'),
    }

    # Si se especifica tipo, buscar solo ese tipo
    search_types = {tipo: type_map[tipo]} if tipo in type_map else type_map

    for entity_type, (model_class, prefix) in search_types.items():
        entities = model_class.all_objects.filter(
            company=company,
        ).filter(
            Q(codigo__icontains=query) | Q(nombre__icontains=query)
        )[:10]

        for entity in entities:
            results.append({
                'id': entity.id,
                'codigo': entity.codigo,
                'nombre': entity.nombre,
                'tipo': entity_type,
            })

    serializer = AutocompleteEntidadSerializer(results, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def autocomplete_usuarios_view(request):
    """GET: Autocomplete para @menciones."""
    query = request.query_params.get('query', '').strip()
    company = request.user.effective_company

    if not query or len(query) < 2:
        return Response([])

    from apps.users.models import User

    users = User.objects.filter(
        company=company,
        is_active=True,
    ).filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query)
    ).exclude(id=request.user.id)[:10]

    results = [
        {'id': u.id, 'nombre': u.full_name, 'email': u.email}
        for u in users
    ]
    serializer = AutocompleteUsuarioSerializer(results, many=True)
    return Response(serializer.data)
