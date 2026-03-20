"""
SaiSuite — Proyectos: Signals
Recálculo automático de avance cuando cambia ActividadProyecto.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from apps.proyectos.models import ActividadProyecto


@receiver(post_save, sender=ActividadProyecto)
def recalcular_avance_al_guardar(sender, instance: ActividadProyecto, **kwargs):
    """Recalcula avance de fase y proyecto cuando se guarda una ActividadProyecto."""
    from apps.proyectos.services import calcular_avance_fase, calcular_avance_proyecto
    if instance.fase_id:
        calcular_avance_fase(instance.fase_id)
    calcular_avance_proyecto(instance.proyecto_id)


@receiver(post_delete, sender=ActividadProyecto)
def recalcular_avance_al_eliminar(sender, instance: ActividadProyecto, **kwargs):
    """Recalcula avance de fase y proyecto cuando se elimina una ActividadProyecto."""
    from apps.proyectos.services import calcular_avance_fase, calcular_avance_proyecto
    if instance.fase_id:
        calcular_avance_fase(instance.fase_id)
    calcular_avance_proyecto(instance.proyecto_id)
