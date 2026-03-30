"""
SaiSuite — Chat: Models
Conversaciones 1-a-1 y mensajes entre usuarios de la misma empresa.
Regla: lógica de negocio va en services.py, no aquí.
"""
import logging
from django.conf import settings
from django.db import models

from apps.core.models import BaseModel

logger = logging.getLogger(__name__)


class Conversacion(BaseModel):
    """
    Conversación 1-a-1 entre dos usuarios de la misma empresa.
    Se crea únicamente desde ChatService — nunca desde views directamente.
    """

    participante_1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversaciones_iniciadas',
    )
    participante_2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversaciones_recibidas',
    )
    ultimo_mensaje = models.ForeignKey(
        'Mensaje',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )
    ultimo_mensaje_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Conversación'
        verbose_name_plural = 'Conversaciones'
        unique_together = [('company', 'participante_1', 'participante_2')]
        indexes = [
            models.Index(fields=['company', '-ultimo_mensaje_at']),
        ]
        ordering = ['-ultimo_mensaje_at']

    def __str__(self):
        return f'{self.participante_1.email} \u2194 {self.participante_2.email}'


class Mensaje(BaseModel):
    """
    Mensaje individual dentro de una conversación.
    Soporta texto, HTML procesado, imágenes (Cloudflare R2) y respuestas.
    """

    conversacion = models.ForeignKey(
        Conversacion,
        on_delete=models.CASCADE,
        related_name='mensajes',
    )
    remitente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mensajes_enviados',
    )
    contenido = models.TextField(blank=True)
    contenido_html = models.TextField(blank=True)
    imagen_url = models.CharField(max_length=500, blank=True, default='')
    responde_a = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='respuestas',
    )
    leido_por_destinatario = models.BooleanField(default=False)
    leido_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Mensaje'
        verbose_name_plural = 'Mensajes'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversacion', 'created_at']),
        ]

    def __str__(self):
        return f'Mensaje de {self.remitente.email} en {self.conversacion_id}'
