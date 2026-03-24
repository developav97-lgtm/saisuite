"""
SaiSuite — Proyectos: Signals
Recálculo automático de avance cuando cambia ActividadProyecto o Tarea.
"""
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from apps.proyectos.models import ActividadProyecto, Tarea


# ──────────────────────────────────────────────
# ActividadProyecto
# ──────────────────────────────────────────────

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


# ──────────────────────────────────────────────
# Tarea
# ──────────────────────────────────────────────

@receiver(post_save, sender=Tarea)
def tarea_post_save(sender, instance: Tarea, created: bool, **kwargs):
    """
    Signal ejecutado después de guardar una Tarea.

    - Creación: auto-agrega responsable como follower.
    - Completada + recurrente: genera nueva instancia.
    - Tiene padre: recalcula avance del padre.
    - Siempre: recalcula avance de la Fase y del Proyecto (DEC-021).
    """
    from apps.proyectos.tarea_services import TareaService
    from apps.proyectos.services import calcular_avance_fase_desde_tareas, calcular_avance_proyecto

    if created:
        # Auto-agregar responsable como follower
        if instance.responsable_id:
            instance.followers.add(instance.responsable_id)
    else:
        # Generar nueva tarea si es recurrente y se acaba de completar
        if instance.estado == 'completada' and instance.es_recurrente:
            TareaService.generar_tarea_recurrente(instance)

        # Recalcular avance de la tarea padre (si existe)
        if instance.tarea_padre_id:
            try:
                tarea_padre = Tarea.objects.get(id=instance.tarea_padre_id)
                TareaService.recalcular_avance_tarea_padre(tarea_padre)
            except Tarea.DoesNotExist:
                pass

    # Cascada Tarea → Fase → Proyecto (DEC-021)
    if instance.fase_id:
        calcular_avance_fase_desde_tareas(instance.fase_id)
        if instance.proyecto_id:
            calcular_avance_proyecto(instance.proyecto_id)


@receiver(post_delete, sender=Tarea)
def tarea_post_delete(sender, instance: Tarea, **kwargs):
    """Recalcula avance de la Fase y Proyecto cuando se elimina una Tarea."""
    from apps.proyectos.services import calcular_avance_fase_desde_tareas, calcular_avance_proyecto
    if instance.fase_id:
        calcular_avance_fase_desde_tareas(instance.fase_id)
        if instance.proyecto_id:
            calcular_avance_proyecto(instance.proyecto_id)


@receiver(m2m_changed, sender=Tarea.followers.through)
def tarea_followers_changed(sender, instance: Tarea, action: str, **kwargs):
    """
    Signal cuando cambian los followers de una tarea.
    Reservado para enviar notificaciones vía webhook a n8n.
    """
    if action in ['post_add', 'post_remove']:
        # TODO: Enviar webhook a n8n para notificar cambio de followers
        pass
