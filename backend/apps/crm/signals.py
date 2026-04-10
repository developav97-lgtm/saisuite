"""
SaiSuite — CRM Signals
Auto-genera eventos de timeline en cambios de estado.

Solo se usan signals para eventos que los services no cubren directamente:
- Creación de oportunidad  → evento SISTEMA "Oportunidad creada"
- Creación de actividad    → evento SISTEMA "Actividad programada: X"

Los cambios de etapa (ganar/perder/mover) ya generan eventos en services.py.
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


def _get_current_user():
    """Obtiene el usuario actual del thread local (via middleware)."""
    try:
        from apps.core.middleware import get_current_user
        return get_current_user()
    except (ImportError, AttributeError):
        return None


@receiver(post_save, sender='crm.CrmOportunidad')
def oportunidad_creada_timeline(sender, instance, created, **kwargs):
    """
    Al crear una oportunidad registra un evento SISTEMA en su timeline.
    Se usa post_save con `created=True` para no duplicar eventos en updates.
    """
    if not created:
        return

    try:
        from apps.crm.models import CrmTimelineEvent, TipoTimelineEvent
        CrmTimelineEvent.objects.create(
            company=instance.company,
            oportunidad=instance,
            tipo=TipoTimelineEvent.SISTEMA,
            descripcion=f'Oportunidad creada en etapa "{instance.etapa.nombre}".',
            usuario=_get_current_user(),
            metadata={'etapa_inicial': instance.etapa.nombre},
        )
    except Exception:
        logger.exception('crm_signal_oportunidad_creada_error', extra={
            'oportunidad_id': str(instance.id),
        })


@receiver(post_save, sender='crm.CrmActividad')
def actividad_creada_timeline(sender, instance, created, **kwargs):
    """
    Al programar una actividad nueva, registra un evento en el timeline
    de la oportunidad asociada.
    Solo aplica si la actividad está vinculada a una oportunidad (no a lead).
    """
    if not created:
        return
    # Las actividades de lead no tienen oportunidad — CrmTimelineEvent requiere oportunidad not null
    if not instance.oportunidad_id:
        return

    try:
        from apps.crm.models import CrmTimelineEvent, TipoTimelineEvent
        fecha_str = instance.fecha_programada.strftime('%d/%m/%Y %H:%M') if instance.fecha_programada else '—'
        CrmTimelineEvent.objects.create(
            company=instance.company,
            oportunidad=instance.oportunidad,
            tipo=TipoTimelineEvent.SISTEMA,
            descripcion=(
                f'Actividad programada: {instance.get_tipo_display()} — '
                f'"{instance.titulo}" para el {fecha_str}.'
            ),
            usuario=_get_current_user(),
            metadata={
                'actividad_id': str(instance.id),
                'tipo': instance.tipo,
                'fecha_programada': fecha_str,
            },
        )
    except Exception:
        logger.exception('crm_signal_actividad_creada_error', extra={
            'actividad_id': str(instance.id),
        })
