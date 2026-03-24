"""
SaiSuite — Notifications: Models
Sistema de notificaciones y comentarios 100% genérico via GenericForeignKey.
"""
import uuid
import logging
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone

from apps.core.models import BaseModel

logger = logging.getLogger(__name__)

User = get_user_model()


class Notificacion(BaseModel):
    """
    Notificación genérica del sistema.
    Usa GenericForeignKey para vincular a cualquier modelo Django.
    Se crea únicamente desde NotificacionService — nunca desde views directamente.
    """

    TIPOS = [
        ('comentario',           'Nuevo Comentario'),
        ('mencion',              'Mención'),
        ('aprobacion',           'Aprobación Requerida'),
        ('aprobacion_resultado', 'Resultado de Aprobación'),
        ('asignacion',           'Nueva Asignación'),
        ('cambio_estado',        'Cambio de Estado'),
        ('vencimiento',          'Vencimiento Próximo'),
        ('sistema',              'Mensaje del Sistema'),
        ('chat',                 'Mensaje Directo'),
        ('recordatorio',         'Recordatorio'),
    ]

    # Destinatario
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notificaciones',
    )

    tipo = models.CharField(max_length=30, choices=TIPOS, db_index=True)

    titulo  = models.CharField(max_length=255)
    mensaje = models.TextField()

    # Objeto relacionado (GenericForeignKey) — cualquier modelo Django
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id    = models.UUIDField()
    objeto_relacionado = GenericForeignKey('content_type', 'object_id')

    # Navegación
    url_accion = models.CharField(max_length=500, blank=True)
    ancla      = models.CharField(
        max_length=100, blank=True,
        help_text='Ancla HTML para scroll directo. Ej: #comentario-<uuid>',
    )

    # Estado
    leida    = models.BooleanField(default=False, db_index=True)
    leida_en = models.DateTimeField(null=True, blank=True)

    # Snooze (C.3): oculta temporalmente hasta esta fecha
    snoozed_until = models.DateTimeField(
        null=True, blank=True,
        help_text='Si es futuro, la notificación no aparece en la lista hasta esta fecha.',
    )

    # Remind Me (C.4): recordatorio programado para aparecer en el futuro
    recordatorio_en = models.DateTimeField(
        null=True, blank=True,
        help_text='Fecha en que el recordatorio debe re-aparecer. NULL = aparece inmediatamente.',
    )

    # Datos extra libres
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table            = 'notificaciones'
        verbose_name        = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering            = ['-created_at']
        indexes = [
            models.Index(fields=['usuario', 'leida', '-created_at'],
                         name='notif_usr_leida_created_idx'),
            models.Index(fields=['content_type', 'object_id'],
                         name='notif_ct_oid_idx'),
        ]

    def __str__(self):
        return f'{self.get_tipo_display()} → {self.usuario_id} | {self.titulo}'


class Comentario(BaseModel):
    """
    Comentario genérico con threading (hasta 2 niveles recomendado).
    Soporta menciones @username y notificaciones automáticas.
    """

    # Autor
    autor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comentarios',
    )

    # Objeto comentado (GenericForeignKey)
    content_type       = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id          = models.UUIDField()
    objeto_relacionado = GenericForeignKey('content_type', 'object_id')

    # Threading
    padre = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='respuestas',
    )

    texto = models.TextField()

    # Edición
    editado    = models.BooleanField(default=False)
    editado_en = models.DateTimeField(null=True, blank=True)

    # Menciones (@usuario)
    menciones = models.ManyToManyField(
        User,
        related_name='comentarios_mencionado',
        blank=True,
    )

    class Meta:
        db_table            = 'comentarios'
        verbose_name        = 'Comentario'
        verbose_name_plural = 'Comentarios'
        ordering            = ['created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id', 'created_at'],
                         name='coment_ct_oid_created_idx'),
            models.Index(fields=['padre'], name='coment_padre_idx'),
        ]

    def __str__(self):
        return f'{self.autor_id} — {self.texto[:60]}'

    @property
    def es_raiz(self) -> bool:
        return self.padre_id is None


class PreferenciaNotificacion(BaseModel):
    """
    Preferencias de usuario para tipos de notificación.
    Un registro por (usuario, tipo). Se crea on-demand en NotificacionService.
    """

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='preferencias_notificacion',
    )
    tipo = models.CharField(max_length=30, choices=Notificacion.TIPOS)

    habilitado_app   = models.BooleanField(default=True)
    habilitado_email = models.BooleanField(default=True)   # reservado
    habilitado_push  = models.BooleanField(default=False)  # reservado

    # C.2: configuración avanzada
    FRECUENCIAS = [
        ('inmediata',  'Inmediata'),
        ('cada_hora',  'Resumen cada hora'),
        ('diaria',     'Resumen diario (9 AM)'),
    ]
    frecuencia = models.CharField(
        max_length=20, choices=FRECUENCIAS, default='inmediata',
    )
    agrupar           = models.BooleanField(default=True, verbose_name='Agrupar similares')
    sonido_habilitado = models.BooleanField(default=True, verbose_name='Sonido habilitado')

    class Meta:
        db_table            = 'preferencias_notificacion'
        verbose_name        = 'Preferencia de Notificación'
        verbose_name_plural = 'Preferencias de Notificación'
        unique_together     = [('company', 'usuario', 'tipo')]

    def __str__(self):
        return f'{self.usuario_id} — {self.get_tipo_display()}'
