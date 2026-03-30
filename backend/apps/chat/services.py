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
    'span': ['class', 'data-user-id'],
}

# Regex patterns
ENTITY_PATTERN = re.compile(r'\[([A-Z]{3})-(\d{3,})\]')
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
    def enviar_mensaje(conversacion_id, remitente, contenido, imagen_url='', responde_a_id=None):
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
            responde_a=responde_a,
        )

        # Actualizar ultimo mensaje de la conversacion
        conv.ultimo_mensaje = mensaje
        conv.ultimo_mensaje_at = mensaje.created_at
        conv.save(update_fields=['ultimo_mensaje', 'ultimo_mensaje_at', 'updated_at'])

        # Push via WebSocket
        try:
            channel_layer = get_channel_layer()
            if channel_layer is not None:
                message_data = MensajeSerializer(mensaje).data
                group_name = f'chat_{conv.id}'
                async_to_sync(channel_layer.group_send)(group_name, {
                    'type': 'chat.new_message',
                    'data': message_data,
                })
                logger.info('ws_chat_message_pushed', extra={
                    'conversacion': str(conv.id),
                    'mensaje': str(mensaje.id),
                })
        except Exception:
            logger.exception('ws_chat_push_failed', extra={
                'mensaje': str(mensaje.id),
            })

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

        return conv.mensajes.select_related('remitente', 'responde_a').all()

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
        """Convierte patrones [PRY-001] en links HTML a entidades del proyecto."""
        from apps.proyectos.models import Project, Task

        TYPE_MAP = {
            'PRY': (Project, 'proyecto', '/proyectos'),
            'TAR': (Task, 'tarea', '/proyectos'),
        }

        def replace_entity(match):
            prefix = match.group(1)
            number = match.group(2)
            codigo = f'{prefix}-{number}'

            if prefix not in TYPE_MAP:
                return match.group(0)

            model_class, entity_type, base_url = TYPE_MAP[prefix]
            try:
                entity = model_class.all_objects.filter(
                    company=company,
                    codigo=codigo,
                ).first()
                if entity:
                    url = f'{base_url}/{entity.id}'
                    return (
                        f'<a href="{url}" data-type="{entity_type}" '
                        f'data-id="{entity.id}" class="chat-entity-link">'
                        f'[{codigo}]</a>'
                    )
            except Exception:
                logger.exception('entity_link_failed', extra={'codigo': codigo})

            return match.group(0)  # Retornar original si no se encuentra

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
                url_accion='/chat',
                ancla=f'#{conversacion.id}',
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
                        url_accion='/chat',
                        ancla=f'#{conversacion.id}',
                        metadata={
                            'conversacion_id': str(conversacion.id),
                        },
                    )
            except Exception:
                logger.exception('mention_notification_failed', extra={
                    'name': name,
                })
