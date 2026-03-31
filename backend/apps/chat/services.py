"""
SaiSuite — Chat: Services
Toda la logica de negocio del modulo de chat.
Regla: NUNCA logica de negocio en views o modelos.
"""
import re
import logging

import bleach
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models import Q
from django.utils import timezone

from .models import Conversacion, Mensaje

logger = logging.getLogger(__name__)

ALLOWED_TAGS = ['a', 'span']
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'data-type', 'data-id', 'class'],
    'span': ['class', 'data-user-id'],  # data-user-id para menciones; class para chips
}

# Patrón genérico: [CUALQUIER-CODIGO-123] — el prefijo lo define la empresa,
# no lo valida el sistema. Se busca en todos los catálogos registrados.
ENTITY_PATTERN = re.compile(r'\[([A-Z0-9]{2,8}-\d{3,})\]')

# Registro de entidades enlazables desde el chat.
# Cada entrada: (app_module, ModelClass, tipo_legible, url_base_angular, nombre_field)
#   - nombre_field: campo del modelo que representa el nombre legible.
#                   Por defecto 'nombre'; Tercero usa 'nombre_completo'.
# Para agregar un catálogo nuevo basta con agregar una línea aquí.
ENTITY_REGISTRY = [
    # Cada entrada: (app_module, ModelClass, tipo, url_template, nombre_field)
    # url_template: usa {id} como placeholder → se reemplaza con entity.id
    ('apps.proyectos.models', 'Project', 'proyecto', '/proyectos/{id}',          'nombre'),
    ('apps.proyectos.models', 'Task',    'tarea',    '/proyectos/tareas/{id}',   'nombre'),
    ('apps.terceros.models',  'Tercero', 'tercero',  '/terceros/{id}/editar',    'nombre_completo'),
    # Futuro:
    # ('apps.sync_agent.models', 'SaiInvoice', 'factura', '/ventas/facturas/{id}', 'numero'),
]
MENTION_PATTERN = re.compile(r'@([\w.\s]+?)(?=\s@|\s*$|[,;:.!?])')


class ChatService:
    """
    Servicio para gestionar conversaciones y mensajes 1-a-1.
    Punto unico de logica de negocio — views solo orquestan.
    """

    # ── Conversaciones ──────────────────────────────────────────────

    @staticmethod
    def obtener_o_crear_conversacion(usuario1, usuario2, company):
        """
        Obtiene una conversacion existente o crea una nueva entre dos usuarios.
        Siempre almacena con el UUID menor primero para evitar duplicados.
        """
        if str(usuario1.id) > str(usuario2.id):
            usuario1, usuario2 = usuario2, usuario1

        conv, created = Conversacion.all_objects.get_or_create(
            company=company,
            participante_1=usuario1,
            participante_2=usuario2,
        )

        action = 'conversacion_creada' if created else 'conversacion_obtenida'
        logger.info(action, extra={
            'conversacion': str(conv.id),
            'usuario1': str(usuario1.id),
            'usuario2': str(usuario2.id),
        })

        if created:
            # Broadcast to both participants so their WS consumers join the new group
            ChatService._broadcast_new_conversation(conv, usuario1, usuario2)

        return conv

    @staticmethod
    def listar_conversaciones(usuario):
        """Lista todas las conversaciones de un usuario, ordenadas por ultimo mensaje."""
        return Conversacion.all_objects.filter(
            Q(participante_1=usuario) | Q(participante_2=usuario),
            company=usuario.effective_company,
        ).select_related(
            'participante_1', 'participante_2', 'ultimo_mensaje',
        ).order_by('-ultimo_mensaje_at')

    # ── Mensajes ────────────────────────────────────────────────────

    @staticmethod
    def enviar_mensaje(conversacion_id, remitente, contenido, imagen_url='', thumbnail_url='',
                       responde_a_id=None, archivo_url='', archivo_nombre='', archivo_tamaño=None):
        """
        Envia un mensaje en una conversacion.
        Valida que el remitente sea participante, procesa contenido HTML,
        actualiza la conversacion, pushea via WebSocket y notifica al destinatario.
        """
        from .serializers import MensajeSerializer

        conv = Conversacion.all_objects.get(id=conversacion_id)

        # Validar que el remitente es participante
        if remitente.id not in (conv.participante_1_id, conv.participante_2_id):
            raise PermissionError('Usuario no es participante de esta conversacion')

        # Procesar contenido para enlaces y menciones
        contenido_html = ChatService.procesar_contenido(contenido, conv.company)

        # Manejar respuesta
        responde_a = None
        if responde_a_id:
            responde_a = Mensaje.all_objects.filter(
                id=responde_a_id,
                conversacion=conv,
            ).first()

        mensaje = Mensaje.all_objects.create(
            company=conv.company,
            conversacion=conv,
            remitente=remitente,
            contenido=contenido,
            contenido_html=contenido_html,
            imagen_url=imagen_url or '',
            thumbnail_url=thumbnail_url or '',
            archivo_url=archivo_url or '',
            archivo_nombre=archivo_nombre or '',
            archivo_tamaño=archivo_tamaño,
            responde_a=responde_a,
        )

        # Actualizar ultimo mensaje de la conversacion
        conv.ultimo_mensaje = mensaje
        conv.ultimo_mensaje_at = mensaje.created_at
        conv.save(update_fields=['ultimo_mensaje', 'ultimo_mensaje_at', 'updated_at'])

        # Notificar al destinatario
        destinatario = (
            conv.participante_2
            if remitente.id == conv.participante_1_id
            else conv.participante_1
        )
        ChatService._notificar_destinatario(mensaje, destinatario, conv)

        # Notificar menciones
        ChatService._notificar_menciones(contenido, remitente, conv)

        logger.info('mensaje_enviado', extra={
            'conversacion': str(conv.id),
            'mensaje': str(mensaje.id),
            'remitente': str(remitente.id),
        })

        return mensaje

    @staticmethod
    def listar_mensajes(conversacion_id, usuario):
        """Lista mensajes de una conversacion. Valida que el usuario sea participante."""
        conv = Conversacion.all_objects.get(id=conversacion_id)

        if usuario.id not in (conv.participante_1_id, conv.participante_2_id):
            raise PermissionError('Usuario no es participante de esta conversacion')

        return conv.mensajes.select_related('remitente', 'responde_a').order_by('-created_at')

    @staticmethod
    def marcar_leido(mensaje_id, usuario):
        """Marca un mensaje como leido por el destinatario."""
        mensaje = Mensaje.all_objects.get(id=mensaje_id)
        conv = mensaje.conversacion

        # Solo el destinatario puede marcar como leido
        destinatario_id = (
            conv.participante_2_id
            if mensaje.remitente_id == conv.participante_1_id
            else conv.participante_1_id
        )
        if usuario.id != destinatario_id:
            raise PermissionError('Solo el destinatario puede marcar como leido')

        if not mensaje.leido_por_destinatario:
            mensaje.leido_por_destinatario = True
            mensaje.leido_at = timezone.now()
            mensaje.save(update_fields=['leido_por_destinatario', 'leido_at', 'updated_at'])

            # Push read receipt via WebSocket
            try:
                channel_layer = get_channel_layer()
                if channel_layer is not None:
                    async_to_sync(channel_layer.group_send)(
                        f'chat_{conv.id}',
                        {
                            'type': 'chat.message_read',
                            'data': {
                                'mensaje_id': str(mensaje.id),
                                'leido_at': mensaje.leido_at.isoformat(),
                                'leido_por': str(usuario.id),
                            },
                        },
                    )
            except Exception:
                logger.exception('ws_read_receipt_failed', extra={
                    'mensaje': str(mensaje.id),
                })

        return mensaje

    # ── Procesamiento de contenido ──────────────────────────────────

    @staticmethod
    def procesar_contenido(contenido, company):
        """Procesa contenido raw en HTML con enlaces a entidades y menciones."""
        html = contenido
        html = ChatService.procesar_enlaces(html, company)
        html = ChatService.procesar_menciones(html, company)
        # Sanitizar HTML
        html = bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)
        return html

    @staticmethod
    def procesar_enlaces(contenido, company):
        """
        Convierte patrones [CODIGO-123] en chips HTML navegables.

        No valida el prefijo — cada empresa define sus propios consecutivos.
        Busca el código en todos los catálogos del ENTITY_REGISTRY y usa
        el primero que lo encuentre para generar el chip con código + nombre.
        """
        import importlib

        # Importar modelos lazy para evitar circularidades
        registry = []
        for module_path, class_name, entity_type, base_url, nombre_field in ENTITY_REGISTRY:
            try:
                mod = importlib.import_module(module_path)
                model_class = getattr(mod, class_name)
                registry.append((model_class, entity_type, base_url, nombre_field))
            except Exception:
                logger.exception('entity_registry_import_failed',
                                 extra={'module': module_path, 'class': class_name})

        def replace_entity(match):
            codigo = match.group(1)  # Código completo, ej. "PCON-0002"

            for model_class, entity_type, base_url, nombre_field in registry:
                try:
                    entity = model_class.all_objects.filter(
                        company=company,
                        codigo=codigo,
                    ).first()
                    if entity:
                        nombre = getattr(entity, nombre_field, '') or ''
                        url = base_url.replace('{id}', str(entity.id))
                        return (
                            f'<a href="{url}" data-type="{entity_type}" '
                            f'data-id="{entity.id}" class="chat-entity-link">'
                            f'<span class="chat-entity-link__code">{codigo}</span>'
                            f'<span class="chat-entity-link__name">{nombre}</span>'
                            f'</a>'
                        )
                except Exception:
                    logger.exception('entity_link_failed',
                                     extra={'codigo': codigo})

            return match.group(0)  # Código no encontrado — dejar como texto

        return ENTITY_PATTERN.sub(replace_entity, contenido)

    @staticmethod
    def procesar_menciones(contenido, company):
        """Convierte patrones @Username en spans HTML."""
        from apps.users.models import User

        def replace_mention(match):
            name = match.group(1).strip()
            try:
                user = User.objects.filter(
                    company=company,
                ).filter(
                    Q(first_name__icontains=name) |
                    Q(last_name__icontains=name) |
                    Q(email__icontains=name)
                ).first()
                if user:
                    return (
                        f'<span class="chat-mention" data-user-id="{user.id}">'
                        f'@{user.full_name}</span>'
                    )
            except Exception:
                logger.exception('mention_processing_failed', extra={'name': name})

            return match.group(0)

        return MENTION_PATTERN.sub(replace_mention, contenido)

    # ── Archivos ────────────────────────────────────────────────────

    @staticmethod
    def upload_archivo_r2(file_obj, company_id: str) -> dict:
        """Sube un archivo a Cloudflare R2 y retorna URL + metadatos."""
        import boto3
        from django.conf import settings
        import os
        import uuid
        import mimetypes

        ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.xlsx', '.doc', '.xls', '.pptx', '.txt'}
        MAX_SIZE = 10 * 1024 * 1024  # 10 MB

        nombre_original = file_obj.name
        extension = os.path.splitext(nombre_original)[1].lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise ValueError(f'Formato no permitido: {extension}')

        tamaño = file_obj.size
        if tamaño > MAX_SIZE:
            raise ValueError('El archivo supera el límite de 10 MB')

        # Nombre único en R2: files/{company_id}/{uuid}{ext}
        file_key = f'files/{company_id}/{uuid.uuid4().hex}{extension}'

        s3 = boto3.client(
            's3',
            endpoint_url=settings.CLOUDFLARE_R2_ENDPOINT,
            aws_access_key_id=settings.CLOUDFLARE_R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.CLOUDFLARE_R2_SECRET_ACCESS_KEY,
            region_name='auto',
        )

        content_type = mimetypes.guess_type(nombre_original)[0] or 'application/octet-stream'
        s3.upload_fileobj(
            file_obj,
            settings.CLOUDFLARE_R2_BUCKET_NAME,
            file_key,
            ExtraArgs={'ContentType': content_type},
        )

        # Usar URL pública configurada (CDN/dominio custom) o presigned URL como fallback
        public_base = getattr(settings, 'CLOUDFLARE_R2_PUBLIC_URL', '').rstrip('/')
        if public_base:
            url = f'{public_base}/{file_key}'
        else:
            # R2 presigned URLs: max 604800 s (7 días). Configurar CLOUDFLARE_R2_PUBLIC_URL para URLs permanentes.
            url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': settings.CLOUDFLARE_R2_BUCKET_NAME, 'Key': file_key},
                ExpiresIn=604800,
            )

        logger.info('archivo_subido_r2', extra={
            'company_id': company_id,
            'file_key': file_key,
            'tamaño': tamaño,
        })

        return {
            'archivo_url': url,
            'archivo_nombre': nombre_original,
            'archivo_tamaño': tamaño,
        }

    @staticmethod
    def upload_imagen_r2(file_obj, company_id: str) -> dict:
        """
        Sube imagen a Cloudflare R2.
        Genera thumbnail WEBP 320x320 (mantiene aspect ratio).
        Retorna: {imagen_url, thumbnail_url, width, height}.
        """
        import io
        import mimetypes
        import os
        import uuid

        import boto3
        from django.conf import settings
        from PIL import Image

        ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
        MAX_SIZE = 5 * 1024 * 1024  # 5 MB

        nombre_original = file_obj.name
        extension = os.path.splitext(nombre_original)[1].lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise ValueError(f'Formato no permitido: {extension}. Use JPG, PNG o WEBP.')

        tamano = file_obj.size
        if tamano > MAX_SIZE:
            raise ValueError('La imagen supera el límite de 5 MB')

        # Abrir con Pillow para validar y obtener dimensiones
        try:
            file_obj.seek(0)
            img = Image.open(file_obj)
            img.verify()
        except Exception:
            raise ValueError('El archivo no es una imagen válida.')

        file_obj.seek(0)
        img = Image.open(file_obj)
        width, height = img.size

        # Thumbnail 320x320 máximo, aspect ratio preservado, formato WEBP
        thumb = img.copy()
        if thumb.mode in ('RGBA', 'LA', 'P'):
            thumb = thumb.convert('RGBA')
        else:
            thumb = thumb.convert('RGB')
        thumb.thumbnail((320, 320), Image.LANCZOS)
        thumb_io = io.BytesIO()
        thumb.save(thumb_io, format='WEBP', quality=80, method=4)
        thumb_io.seek(0)

        uid = uuid.uuid4().hex
        original_key = f'images/original/{company_id}/{uid}{extension}'
        thumbnail_key = f'images/thumbnails/{company_id}/{uid}.webp'

        s3 = boto3.client(
            's3',
            endpoint_url=settings.CLOUDFLARE_R2_ENDPOINT,
            aws_access_key_id=settings.CLOUDFLARE_R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.CLOUDFLARE_R2_SECRET_ACCESS_KEY,
            region_name='auto',
        )

        content_type = mimetypes.guess_type(nombre_original)[0] or 'image/jpeg'
        file_obj.seek(0)
        s3.upload_fileobj(
            file_obj, settings.CLOUDFLARE_R2_BUCKET_NAME, original_key,
            ExtraArgs={'ContentType': content_type},
        )
        s3.upload_fileobj(
            thumb_io, settings.CLOUDFLARE_R2_BUCKET_NAME, thumbnail_key,
            ExtraArgs={'ContentType': 'image/webp'},
        )

        # Usar URL pública configurada (CDN/dominio custom) o presigned URL como fallback
        public_base = getattr(settings, 'CLOUDFLARE_R2_PUBLIC_URL', '').rstrip('/')
        if public_base:
            imagen_url = f'{public_base}/{original_key}'
            thumbnail_url = f'{public_base}/{thumbnail_key}'
        else:
            # R2 presigned URLs: max 604800 s (7 días). Configurar CLOUDFLARE_R2_PUBLIC_URL para URLs permanentes.
            imagen_url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': settings.CLOUDFLARE_R2_BUCKET_NAME, 'Key': original_key},
                ExpiresIn=604800,
            )
            thumbnail_url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': settings.CLOUDFLARE_R2_BUCKET_NAME, 'Key': thumbnail_key},
                ExpiresIn=604800,
            )

        logger.info('imagen_subida_r2', extra={
            'company_id': company_id,
            'original_key': original_key,
            'tamano': tamano,
            'width': width,
            'height': height,
        })

        return {
            'imagen_url': imagen_url,
            'thumbnail_url': thumbnail_url,
            'width': width,
            'height': height,
        }

    # ── Búsqueda ────────────────────────────────────────────────────

    @staticmethod
    def buscar_mensajes(conversacion_id: str, query: str, user_id: str) -> list:
        """Busca mensajes en una conversación por contenido (case-insensitive)."""
        conv = Conversacion.all_objects.filter(id=conversacion_id).filter(
            Q(participante_1_id=user_id) | Q(participante_2_id=user_id)
        ).first()

        if not conv:
            return []

        resultados = list(
            Mensaje.all_objects.filter(
                conversacion=conv,
                contenido__icontains=query,
            ).select_related('remitente', 'responde_a').order_by('created_at')
        )

        logger.info('mensajes_buscados', extra={
            'conversacion_id': conversacion_id,
            'query': query,
            'resultados': len(resultados),
        })

        return resultados

    # ── Notificaciones internas ─────────────────────────────────────

    @staticmethod
    def _notificar_destinatario(mensaje, destinatario, conversacion):
        """Envia notificacion al destinatario del mensaje."""
        try:
            from apps.notifications.services import NotificacionService
            NotificacionService.crear(
                usuario=destinatario,
                tipo='chat',
                titulo=f'Mensaje de {mensaje.remitente.full_name}',
                mensaje=mensaje.contenido[:100],
                objeto_relacionado=conversacion,
                url_accion='',
                ancla='',
                metadata={
                    'conversacion_id': str(conversacion.id),
                    'mensaje_id': str(mensaje.id),
                },
            )
        except Exception:
            logger.exception('chat_notification_failed', extra={
                'mensaje': str(mensaje.id),
            })

    @staticmethod
    def _notificar_menciones(contenido, remitente, conversacion):
        """Envia notificaciones a usuarios mencionados."""
        from apps.users.models import User
        from apps.notifications.services import NotificacionService

        for match in MENTION_PATTERN.finditer(contenido):
            name = match.group(1).strip()
            try:
                user = User.objects.filter(
                    company=conversacion.company,
                ).filter(
                    Q(first_name__icontains=name) |
                    Q(last_name__icontains=name) |
                    Q(email__icontains=name)
                ).first()

                if user and user.id != remitente.id:
                    NotificacionService.crear(
                        usuario=user,
                        tipo='mencion',
                        titulo=f'{remitente.full_name} te menciono en un chat',
                        mensaje=contenido[:100],
                        objeto_relacionado=conversacion,
                        url_accion='',
                        ancla='',
                        metadata={
                            'conversacion_id': str(conversacion.id),
                        },
                    )
            except Exception:
                logger.exception('mention_notification_failed', extra={
                    'name': name,
                })

    # ── Edición de mensajes ──────────────────────────────────────────

    @staticmethod
    def editar_mensaje(mensaje_id: str, nuevo_contenido: str, usuario) -> 'Mensaje':
        """
        Edita un mensaje enviado.
        Reglas: solo el remitente puede editar, máximo 15 minutos desde created_at.
        Guarda contenido_original en la primera edición.
        Reprocesa enlaces y menciones en el nuevo contenido.
        """
        import datetime
        from django.utils import timezone as tz

        mensaje = Mensaje.all_objects.select_related('conversacion', 'remitente').filter(
            id=mensaje_id,
        ).first()

        if not mensaje:
            raise LookupError('Mensaje no encontrado')

        if mensaje.remitente_id != usuario.id:
            raise PermissionError('Solo el remitente puede editar este mensaje')

        edad = tz.now() - mensaje.created_at
        if edad > datetime.timedelta(minutes=15):
            raise PermissionError('No se puede editar un mensaje de más de 15 minutos')

        if not mensaje.editado:
            mensaje.contenido_original = mensaje.contenido

        mensaje.contenido = nuevo_contenido.strip()
        mensaje.contenido_html = ChatService.procesar_contenido(
            mensaje.contenido, mensaje.conversacion.company,
        )
        mensaje.editado = True
        mensaje.editado_at = tz.now()
        mensaje.save(update_fields=[
            'contenido', 'contenido_html', 'editado', 'editado_at', 'contenido_original', 'updated_at',
        ])

        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'chat_{mensaje.conversacion_id}',
                {
                    'type': 'chat.message_edited',
                    'data': {
                        'mensaje_id': str(mensaje.id),
                        'contenido': mensaje.contenido,
                        'contenido_html': mensaje.contenido_html,
                        'editado_at': mensaje.editado_at.isoformat(),
                    },
                },
            )
        except Exception:
            logger.exception('chat_ws_edit_broadcast_failed', extra={'mensaje_id': str(mensaje.id)})

        logger.info('mensaje_editado', extra={
            'mensaje_id': str(mensaje.id),
            'user_id': str(usuario.id),
        })
        return mensaje

    # ── Broadcasts WebSocket (sólo desde contexto sync — NO desde database_sync_to_async) ─

    @staticmethod
    def _serialize_para_ws(serializer_data) -> dict:
        """
        Convierte datos del serializer DRF a un dict msgpack-compatible.
        DRF puede retornar uuid.UUID, Decimal, datetime nativos de Python
        que msgpack (usado por channels_redis) no sabe serializar.
        Pasar por json.dumps/loads con DjangoJSONEncoder resuelve todos los tipos.
        """
        import json
        from django.core.serializers.json import DjangoJSONEncoder
        return json.loads(json.dumps(dict(serializer_data), cls=DjangoJSONEncoder))

    @staticmethod
    def broadcast_nuevo_mensaje(mensaje, conv_id: str) -> None:
        """
        Envía el evento new_message al grupo de la conversación.
        Llamar SOLO desde sync views (HTTP), no desde database_sync_to_async.
        El consumer WS usa su propio channel_layer.group_send() asíncrono.
        """
        from .serializers import MensajeSerializer
        try:
            channel_layer = get_channel_layer()
            if channel_layer is None:
                return
            message_data = ChatService._serialize_para_ws(MensajeSerializer(mensaje).data)
            async_to_sync(channel_layer.group_send)(
                f'chat_{conv_id}',
                {'type': 'chat.new_message', 'data': message_data},
            )
            logger.info('ws_chat_message_pushed', extra={
                'conversacion': str(conv_id),
                'mensaje': str(mensaje.id),
            })
        except Exception:
            logger.exception('ws_chat_push_failed', extra={'mensaje': str(mensaje.id)})

    @staticmethod
    def _broadcast_new_conversation(conv, usuario1, usuario2) -> None:
        """
        Notifica a ambos participantes via WS para que sus consumers se unan
        al nuevo grupo chat_{conv_id} y puedan recibir mensajes en tiempo real.
        """
        try:
            channel_layer = get_channel_layer()
            if channel_layer is None:
                return
            payload = {
                'type': 'chat.new_conversation',
                'conversacion_id': str(conv.id),
                'data': {'conversacion_id': str(conv.id)},
            }
            for participant in [usuario1, usuario2]:
                async_to_sync(channel_layer.group_send)(
                    f'chat_user_{participant.id}',
                    payload,
                )
        except Exception:
            logger.exception(
                'ws_new_conversation_broadcast_failed',
                extra={'conv': str(conv.id)},
            )


class PresenceService:
    """
    Presencia en tiempo real usando Redis TTL.
    online  = key existe en Redis (TTL 35s, heartbeat frontend cada 25s)
    offline = key no existe
    """
    TTL = 35

    @staticmethod
    def _get_redis():
        import redis as redis_client
        from django.conf import settings
        return redis_client.from_url(settings.REDIS_URL, decode_responses=True)

    @staticmethod
    def set_online(user_id: str) -> None:
        try:
            r = PresenceService._get_redis()
            r.setex(f'presence:{user_id}', PresenceService.TTL, 'online')
        except Exception:
            logger.warning('presence_redis_error_set_online', extra={'user_id': user_id})

    @staticmethod
    def set_offline(user_id: str) -> None:
        try:
            r = PresenceService._get_redis()
            r.delete(f'presence:{user_id}')
        except Exception:
            logger.warning('presence_redis_error_set_offline', extra={'user_id': user_id})

    @staticmethod
    def get_status(user_id: str) -> str:
        try:
            r = PresenceService._get_redis()
            value = r.get(f'presence:{user_id}')
            return value if value else 'offline'
        except Exception:
            logger.warning('presence_redis_error_get', extra={'user_id': user_id})
            return 'offline'

    @staticmethod
    def get_statuses(user_ids: list) -> dict:
        if not user_ids:
            return {}
        try:
            r = PresenceService._get_redis()
            pipe = r.pipeline()
            for uid in user_ids:
                pipe.get(f'presence:{uid}')
            values = pipe.execute()
            return {uid: (v or 'offline') for uid, v in zip(user_ids, values)}
        except Exception:
            logger.warning('presence_redis_error_get_statuses')
            return {uid: 'offline' for uid in user_ids}
