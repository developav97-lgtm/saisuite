"""
SaiSuite — AI: Models
Knowledge Base (RAG), fuentes indexadas y feedback de IA.
Regla: lógica de negocio va en services.py, no aquí.
"""
import logging

from django.conf import settings
from django.db import models
from pgvector.django import HnswIndex, VectorField

from apps.core.models import BaseModel

logger = logging.getLogger(__name__)


class KnowledgeSource(BaseModel):
    """
    Registro de cada archivo fuente indexado en la knowledge base.
    Permite rastrear qué archivos se han procesado, detectar cambios
    via SHA-256 hash, y gestionar upserts sin duplicar chunks.
    """

    class SourceChannel(models.TextChoices):
        DRIVE = 'drive', 'Google Drive'
        UPLOAD = 'upload', 'Panel Admin'
        CLI = 'cli', 'Management Command'

    class Category(models.TextChoices):
        MANUAL = 'manual', 'Manual'
        NORMA = 'norma', 'Norma'
        FAQ = 'faq', 'FAQ'
        GUIA = 'guia', 'Guía'
        CUSTOM = 'custom', 'Custom'

    file_name = models.CharField(max_length=255)
    source_channel = models.CharField(
        max_length=20,
        choices=SourceChannel.choices,
    )
    original_format = models.CharField(
        max_length=10,
        help_text='Extensión del archivo original: md, pdf, docx, txt',
    )
    module = models.CharField(
        max_length=50,
        help_text='Módulo al que pertenece: proyectos, dashboard, terceros, contabilidad, general',
    )
    category = models.CharField(
        max_length=30,
        choices=Category.choices,
        default=Category.CUSTOM,
    )
    file_hash = models.CharField(
        max_length=64,
        help_text='SHA-256 del contenido para detectar cambios y evitar re-procesar',
    )
    chunk_count = models.PositiveIntegerField(default=0)
    total_tokens = models.PositiveIntegerField(default=0)
    last_indexed_at = models.DateTimeField()
    drive_file_id = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Google Drive file ID (solo canal drive)',
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = 'Knowledge Source'
        verbose_name_plural = 'Knowledge Sources'
        unique_together = [('company', 'file_name', 'source_channel')]
        ordering = ['-last_indexed_at']

    def __str__(self):
        return f'{self.file_name} ({self.source_channel}) — {self.chunk_count} chunks'


class KnowledgeChunk(BaseModel):
    """
    Fragmento de conocimiento indexado con embedding vectorial.
    Cada chunk es una sección de un documento (~500 tokens) con su
    embedding para búsqueda semántica via pgvector.
    """

    class SourceType(models.TextChoices):
        MANUAL = 'manual', 'Manual de usuario'
        NORMA = 'norma', 'Norma colombiana'
        FAQ_APRENDIDA = 'faq_aprendida', 'FAQ aprendida'
        HELP_TEXT = 'help_text', 'Help text'
        CUSTOM = 'custom', 'Custom'

    source = models.ForeignKey(
        KnowledgeSource,
        on_delete=models.CASCADE,
        related_name='chunks',
        null=True,
        blank=True,
        help_text='Fuente del chunk. Null para FAQ aprendidas sin archivo.',
    )
    source_type = models.CharField(
        max_length=30,
        choices=SourceType.choices,
    )
    source_file = models.CharField(
        max_length=255,
        help_text='Ruta o nombre del archivo fuente. Ej: docs/manuales/MANUAL-PROYECTOS.md',
    )
    module = models.CharField(
        max_length=50,
        help_text='Módulo: proyectos, dashboard, terceros, contabilidad, general',
    )
    title = models.CharField(max_length=255)
    content = models.TextField()
    token_count = models.PositiveIntegerField(default=0)
    embedding = VectorField(
        dimensions=1536,
        help_text='Embedding vectorial (text-embedding-3-small, 1536 dims)',
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Metadata adicional: section, subsection, page, etc.',
    )

    class Meta:
        verbose_name = 'Knowledge Chunk'
        verbose_name_plural = 'Knowledge Chunks'
        ordering = ['-created_at']
        indexes = [
            HnswIndex(
                name='kb_embedding_idx',
                fields=['embedding'],
                m=16,
                ef_construction=64,
                opclasses=['vector_cosine_ops'],
            ),
        ]

    def __str__(self):
        return f'{self.title} ({self.module}) — {self.token_count} tokens'


class AIFeedback(BaseModel):
    """
    Feedback del usuario sobre respuestas de IA (thumbs up/down).
    Se usa para aprendizaje: respuestas con feedback positivo se cachean
    y eventualmente se convierten en FAQ aprendidas.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_feedbacks',
    )
    mensaje = models.ForeignKey(
        'chat.Mensaje',
        on_delete=models.CASCADE,
        related_name='ai_feedbacks',
    )
    rating = models.SmallIntegerField(
        help_text='1 = thumbs up, -1 = thumbs down',
    )
    module_context = models.CharField(
        max_length=50,
        help_text='Módulo donde se dio el feedback',
    )
    question = models.TextField(help_text='Pregunta original del usuario')
    answer = models.TextField(help_text='Respuesta del bot que se evaluó')

    class Meta:
        verbose_name = 'AI Feedback'
        verbose_name_plural = 'AI Feedbacks'
        unique_together = [('user', 'mensaje')]
        ordering = ['-created_at']

    def __str__(self):
        icon = '+' if self.rating > 0 else '-'
        return f'[{icon}] {self.user.email} — {self.module_context}'
