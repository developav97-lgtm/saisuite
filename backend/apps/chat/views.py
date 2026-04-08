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
    MensajeEditSerializer,
    MensajeSerializer,
)
from rest_framework.views import APIView

from .services import ChatService, PresenceService, BotResponseService

logger = logging.getLogger(__name__)


class BotConversacionView(APIView):
    """
    POST /api/v1/chat/conversaciones/bot/
    Crea o obtiene una conversacion con el bot IA.
    Body: { "context": "dashboard" }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        context = request.data.get('context', 'dashboard').strip()
        if not context:
            context = 'dashboard'

        company = getattr(request.user, 'effective_company', None)
        if not company:
            return Response({'error': 'Sin empresa asignada.'}, status=status.HTTP_400_BAD_REQUEST)

        conv = ChatService.obtener_o_crear_conversacion_bot(request.user, company, bot_context=context)
        serializer = ConversacionListSerializer(conv, context={'request': request})
        return Response(serializer.data)


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
            thumbnail_url=serializer.validated_data.get('thumbnail_url', ''),
            responde_a_id=serializer.validated_data.get('responde_a_id'),
            archivo_url=serializer.validated_data.get('archivo_url', ''),
            archivo_nombre=serializer.validated_data.get('archivo_nombre', ''),
            archivo_tamaño=serializer.validated_data.get('archivo_tamaño'),
        )
    except PermissionError as e:
        return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)

    # Push WS broadcast desde contexto sync HTTP — sin deadlock posible
    ChatService.broadcast_nuevo_mensaje(mensaje, conversacion_id)

    # Si es conversacion bot, lanzar respuesta en background
    if mensaje.conversacion.bot_context:
        import threading
        from apps.chat.services import BotResponseService
        threading.Thread(
            target=BotResponseService.process_bot_message,
            args=(mensaje.conversacion, mensaje.contenido, request.user),
            daemon=True,
        ).start()

    output = MensajeSerializer(mensaje)
    return Response(output.data, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def limpiar_chat_bot_view(request):
    """DELETE: Elimina todos los mensajes de la conversación bot del usuario."""
    company = getattr(request.user, 'effective_company', None)
    if not company:
        return Response({'error': 'Sin empresa asignada.'}, status=status.HTTP_400_BAD_REQUEST)
    deleted = ChatService.limpiar_mensajes_bot(request.user, company)
    return Response({'deleted': deleted}, status=status.HTTP_200_OK)


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
    """
    GET: Autocomplete para entidades enlazables en chat.

    Busca por código O nombre en todos los catálogos registrados en ENTITY_REGISTRY.
    No filtra por prefijo — cada empresa define sus propios consecutivos.
    Parámetro opcional ?tipo=proyecto|tarea|... para limitar la búsqueda.
    """
    import importlib
    from .services import ENTITY_REGISTRY

    query = request.query_params.get('query', '').strip()
    tipo_filtro = request.query_params.get('tipo', '').strip()
    company = request.user.effective_company

    if not query:
        return Response([])

    results = []

    for module_path, class_name, entity_type, _base_url, nombre_field in ENTITY_REGISTRY:
        if tipo_filtro and entity_type != tipo_filtro:
            continue
        try:
            mod = importlib.import_module(module_path)
            model_class = getattr(mod, class_name)
            entities = model_class.all_objects.filter(
                company=company,
            ).filter(
                Q(codigo__icontains=query) | Q(**{f'{nombre_field}__icontains': query})
            )[:10]

            for entity in entities:
                results.append({
                    'id': entity.id,
                    'codigo': entity.codigo,
                    'nombre': getattr(entity, nombre_field, '') or '',
                    'tipo': entity_type,
                })
        except Exception:
            logger.exception('autocomplete_entity_failed',
                             extra={'module': module_path, 'class': class_name})

    serializer = AutocompleteEntidadSerializer(results, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def autocomplete_usuarios_view(request):
    """GET: Autocomplete para @menciones."""
    query = request.query_params.get('query', '').strip()
    company = request.user.effective_company

    if not query:
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


# ── Archivos ─────────────────────────────────────────────────────


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_archivo_view(request):
    """POST /api/v1/chat/upload-archivo/ — Sube archivo a R2."""
    file_obj = request.FILES.get('archivo')
    if not file_obj:
        return Response({'error': 'No se envió ningún archivo.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        result = ChatService.upload_archivo_r2(file_obj, str(request.user.company_id))
        return Response(result, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        logger.exception('error_subiendo_archivo_r2', extra={'user': str(request.user.id)})
        return Response({'error': 'Error al subir el archivo.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_imagen_view(request):
    """POST /api/v1/chat/upload-imagen/ — Sube imagen a R2, genera thumbnail WEBP."""
    file_obj = request.FILES.get('imagen')
    if not file_obj:
        return Response({'error': 'No se envió ninguna imagen.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        result = ChatService.upload_imagen_r2(file_obj, str(request.user.company_id))
        return Response(result, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        logger.exception('error_subiendo_imagen_r2', extra={'user': str(request.user.id)})
        return Response({'error': 'Error al subir la imagen.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def editar_mensaje_view(request, mensaje_id):
    """PATCH /api/v1/chat/mensajes/{id}/editar/ — Edita contenido de un mensaje propio."""
    serializer = MensajeEditSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        mensaje = ChatService.editar_mensaje(
            mensaje_id=str(mensaje_id),
            nuevo_contenido=serializer.validated_data['contenido'],
            usuario=request.user,
        )
    except LookupError as e:
        return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
    except PermissionError as e:
        return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
    except Exception:
        logger.exception('error_editando_mensaje', extra={'user': str(request.user.id)})
        return Response({'error': 'Error al editar el mensaje.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(MensajeSerializer(mensaje).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def presencia_view(request):
    """
    GET /api/v1/chat/presencia/ — Estado online/offline de los peers del usuario.
    Retorna {user_id: 'online'|'offline'} para todos los interlocutores.
    """
    from django.db.models import Q as _Q
    from apps.chat.models import Conversacion

    convs = Conversacion.all_objects.filter(
        _Q(participante_1=request.user) | _Q(participante_2=request.user),
        company=request.user.effective_company,
    ).values_list('participante_1_id', 'participante_2_id')

    peer_ids = set()
    user_id = str(request.user.id)
    for p1, p2 in convs:
        peer = str(p2) if str(p1) == user_id else str(p1)
        peer_ids.add(peer)

    statuses = PresenceService.get_statuses(list(peer_ids))
    return Response(statuses)


# ── Búsqueda ─────────────────────────────────────────────────────


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def buscar_mensajes_view(request, conversacion_id):
    """GET /api/v1/chat/conversaciones/{id}/buscar/?q=texto"""
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return Response({'results': [], 'query': query})

    mensajes = ChatService.buscar_mensajes(
        str(conversacion_id), query, str(request.user.id)
    )
    serializer = MensajeSerializer(mensajes, many=True, context={'request': request})
    return Response({'results': serializer.data, 'query': query})
