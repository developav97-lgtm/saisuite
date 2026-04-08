"""
SaiSuite — AI: Views
Endpoints para Knowledge Base y feedback de IA.
Regla: las views solo orquestan — llaman a services y retornan respuestas.
"""
import logging

from django.conf import settings
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai.models import AIFeedback, KnowledgeSource
from apps.ai.serializers import (
    AIFeedbackCreateSerializer,
    AIFeedbackSerializer,
    KnowledgeIngestResultSerializer,
    KnowledgeIngestSerializer,
    KnowledgeSourceListSerializer,
    KnowledgeUploadSerializer,
)
from apps.ai.services import KnowledgeIngestionService, LearningService

logger = logging.getLogger(__name__)


class IsCompanyAdmin(IsAuthenticated):
    """Solo company_admin y valmen_admin pueden gestionar la KB."""

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        user = request.user
        return user.is_staff or getattr(user, 'role', '') in ('company_admin', 'valmen_admin')


class N8NWebhookAuthentication:
    """Autenticación via header X-N8N-Secret para llamadas desde n8n."""

    @staticmethod
    def is_valid(request) -> bool:
        secret = request.META.get('HTTP_X_N8N_SECRET', '')
        expected = settings.N8N_WEBHOOK_SECRET
        if not expected:
            logger.warning('n8n_webhook_secret_not_configured')
            return False
        return secret == expected


# ── Knowledge Base endpoints ─────────────────────────────────────


class KnowledgeIngestView(APIView):
    """
    POST /api/v1/ai/knowledge/ingest/
    Llamado por n8n cuando se detecta un archivo nuevo/modificado en Google Drive.
    Auth: X-N8N-Secret header.
    """

    permission_classes = []
    authentication_classes = []
    parser_classes = [MultiPartParser]

    def post(self, request):
        if not N8NWebhookAuthentication.is_valid(request):
            return Response(
                {'error': 'Invalid or missing X-N8N-Secret header.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = KnowledgeIngestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data['file']
        file_content = uploaded_file.read()
        file_name = serializer.validated_data.get('file_name', uploaded_file.name)

        # Para webhooks n8n, necesitamos el company_id
        # Se puede pasar como header o en el body
        company_id = request.META.get('HTTP_X_COMPANY_ID', '')
        if not company_id:
            company_id = request.data.get('company_id', '')

        if not company_id:
            # Fallback: usar la primera empresa (solo en dev)
            from apps.companies.models import Company
            company = Company.objects.first()
            if not company:
                return Response(
                    {'error': 'No se encontró empresa.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            company_id = company.id

        result = KnowledgeIngestionService.ingest(
            file_content=file_content,
            file_name=file_name,
            company_id=company_id,
            module=serializer.validated_data.get('module', ''),
            category=serializer.validated_data.get('category', ''),
            source_channel='drive',
            drive_file_id=serializer.validated_data.get('drive_file_id', ''),
        )

        return Response(
            KnowledgeIngestResultSerializer(result).data,
            status=status.HTTP_200_OK,
        )


class KnowledgeUploadView(APIView):
    """
    POST /api/v1/ai/knowledge/upload/
    Subir un archivo desde el panel de administración.
    Auth: JWT (company_admin o valmen_admin).
    """

    permission_classes = [IsCompanyAdmin]
    parser_classes = [MultiPartParser]

    def post(self, request):
        serializer = KnowledgeUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data['file']
        file_content = uploaded_file.read()

        result = KnowledgeIngestionService.ingest(
            file_content=file_content,
            file_name=uploaded_file.name,
            company_id=request.user.company_id,
            module=serializer.validated_data.get('module', ''),
            category=serializer.validated_data.get('category', ''),
            source_channel='upload',
        )

        return Response(
            KnowledgeIngestResultSerializer(result).data,
            status=status.HTTP_200_OK,
        )


class KnowledgeSourceListView(APIView):
    """
    GET /api/v1/ai/knowledge/sources/
    Lista todas las fuentes indexadas de la empresa.
    Auth: JWT (company_admin o valmen_admin).
    """

    permission_classes = [IsCompanyAdmin]

    def get(self, request):
        sources = KnowledgeSource.objects.all().order_by('-last_indexed_at')
        serializer = KnowledgeSourceListSerializer(sources, many=True)
        return Response(serializer.data)


class KnowledgeSourceDeleteView(APIView):
    """
    DELETE /api/v1/ai/knowledge/sources/<id>/
    Elimina una fuente y todos sus chunks.
    Auth: JWT (company_admin o valmen_admin).
    """

    permission_classes = [IsCompanyAdmin]

    def delete(self, request, source_id):
        try:
            result = KnowledgeIngestionService.delete_source(
                source_id=source_id,
                company_id=request.user.company_id,
            )
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )


class KnowledgeReindexView(APIView):
    """
    POST /api/v1/ai/knowledge/reindex/
    Re-indexa toda la knowledge base desde los archivos locales.
    Auth: JWT (valmen_admin solo).
    """

    permission_classes = [IsCompanyAdmin]

    def post(self, request):
        from django.core.management import call_command
        from io import StringIO

        output = StringIO()
        call_command(
            'index_knowledge_base',
            reindex=True,
            company_id=str(request.user.company_id),
            stdout=output,
        )

        return Response({
            'status': 'reindex_complete',
            'output': output.getvalue(),
        })


# ── Feedback de IA ───────────────────────────────────────────────


class AIFeedbackView(APIView):
    """
    POST /api/v1/ai/feedback/
    Registra thumbs up / thumbs down sobre un mensaje del bot.

    Body: { mensaje_id: UUID, rating: 1|-1 }

    El endpoint extrae automáticamente:
    - question: el mensaje del usuario previo al mensaje del bot
    - answer: el contenido del mensaje del bot
    - module_context: bot_context de la conversación
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AIFeedbackCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        mensaje_id = serializer.validated_data['mensaje_id']
        rating = serializer.validated_data['rating']

        # Obtener el mensaje del bot (el que se está evaluando)
        from apps.chat.models import Mensaje
        from apps.users.models import User

        bot_user = User.objects.filter(is_bot=True).first()

        try:
            bot_message = Mensaje.objects.select_related(
                'conversacion', 'remitente',
            ).get(
                id=mensaje_id,
                conversacion__company=request.user.company,
            )
        except Mensaje.DoesNotExist:
            return Response(
                {'error': 'Mensaje no encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Verificar que es un mensaje del bot
        if not bot_user or bot_message.remitente_id != bot_user.id:
            return Response(
                {'error': 'Solo se puede dar feedback sobre mensajes del asistente.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Obtener la pregunta del usuario (mensaje anterior al mensaje del bot)
        prev_message = (
            Mensaje.objects.filter(
                conversacion=bot_message.conversacion,
                created_at__lt=bot_message.created_at,
            )
            .exclude(remitente=bot_user)
            .order_by('-created_at')
            .first()
        )
        question = prev_message.contenido if prev_message else ''
        answer = bot_message.contenido
        module_context = bot_message.conversacion.bot_context or 'general'

        # Crear o actualizar feedback (unique_together: user + mensaje)
        feedback, created = AIFeedback.all_objects.update_or_create(
            user=request.user,
            mensaje=bot_message,
            defaults={
                'company': request.user.company,
                'rating': rating,
                'module_context': module_context,
                'question': question,
                'answer': answer,
            },
        )

        logger.info(
            'ai_feedback_saved',
            extra={
                'feedback_id': str(feedback.id),
                'rating': rating,
                'module': module_context,
                'created': created,
            },
        )

        # Feedback positivo → aprender: convierte Q&A en FAQ chunk
        if rating == 1:
            try:
                learned = LearningService.process_positive_feedback(feedback)
                logger.info(
                    'ai_feedback_learning',
                    extra={'feedback_id': str(feedback.id), 'learned': learned},
                )
            except Exception:
                # No bloquear la respuesta si el aprendizaje falla
                logger.exception(
                    'ai_feedback_learning_failed',
                    extra={'feedback_id': str(feedback.id)},
                )

        return Response(
            AIFeedbackSerializer(feedback).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
