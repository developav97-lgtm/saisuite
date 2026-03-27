"""
SaiSuite — Proyectos: Signals
Recálculo automático de avance cuando cambia ProjectActivity o Task.
"""
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from apps.proyectos.models import ProjectActivity, Task


# ──────────────────────────────────────────────
# ProjectActivity
# ──────────────────────────────────────────────

@receiver(post_save, sender=ProjectActivity)
def recalcular_avance_al_guardar(sender, instance: ProjectActivity, **kwargs):
    """Recalcula avance de fase y proyecto cuando se guarda una ProjectActivity."""
    from apps.proyectos.services import calcular_avance_fase, calcular_avance_proyecto
    if instance.fase_id:
        calcular_avance_fase(instance.fase_id)
    calcular_avance_proyecto(instance.proyecto_id)


@receiver(post_delete, sender=ProjectActivity)
def recalcular_avance_al_eliminar(sender, instance: ProjectActivity, **kwargs):
    """Recalcula avance de fase y proyecto cuando se elimina una ProjectActivity."""
    from apps.proyectos.services import calcular_avance_fase, calcular_avance_proyecto
    if instance.fase_id:
        calcular_avance_fase(instance.fase_id)
    calcular_avance_proyecto(instance.proyecto_id)


# ──────────────────────────────────────────────
# Task
# ──────────────────────────────────────────────

@receiver(post_save, sender=Task)
def tarea_post_save(sender, instance: Task, created: bool, **kwargs):
    """
    Signal ejecutado después de guardar una Task.

    - Creación: auto-agrega responsable como follower.
    - Completada + recurrente: genera nueva instancia.
    - Tiene padre: recalcula avance del padre.
    - Siempre: recalcula avance de la Fase y del Proyecto (DEC-021).
    """
    from apps.proyectos.tarea_services import TaskService
    from apps.proyectos.services import calcular_avance_fase_desde_tareas, calcular_avance_proyecto

    if created:
        # Auto-agregar responsable como follower
        if instance.responsable_id:
            instance.followers.add(instance.responsable_id)
    else:
        # Generar nueva tarea si es recurrente y se acaba de completar
        if instance.estado == 'completed' and instance.es_recurrente:
            TaskService.generar_tarea_recurrente(instance)

        # Recalcular avance de la tarea padre (si existe)
        if instance.tarea_padre_id:
            try:
                tarea_padre = Task.objects.get(id=instance.tarea_padre_id)
                TaskService.recalcular_avance_tarea_padre(tarea_padre)
            except Task.DoesNotExist:
                pass

    # Cascada Task → ProjectActivity → Fase → Proyecto (DEC-021)
    if instance.actividad_proyecto_id:
        from apps.proyectos.services import recalcular_cantidad_ejecutada_ap
        recalcular_cantidad_ejecutada_ap(instance.actividad_proyecto_id)
    if instance.fase_id:
        calcular_avance_fase_desde_tareas(instance.fase_id)
        if instance.proyecto_id:
            calcular_avance_proyecto(instance.proyecto_id)


@receiver(post_delete, sender=Task)
def tarea_post_delete(sender, instance: Task, **kwargs):
    """Recalcula avance de la Fase y Proyecto cuando se elimina una Task."""
    from apps.proyectos.services import calcular_avance_fase_desde_tareas, calcular_avance_proyecto, recalcular_cantidad_ejecutada_ap
    if instance.actividad_proyecto_id:
        recalcular_cantidad_ejecutada_ap(instance.actividad_proyecto_id)
    if instance.fase_id:
        calcular_avance_fase_desde_tareas(instance.fase_id)
        if instance.proyecto_id:
            calcular_avance_proyecto(instance.proyecto_id)


@receiver(m2m_changed, sender=Task.followers.through)
def tarea_followers_changed(sender, instance: Task, action: str, **kwargs):
    """
    Signal cuando cambian los followers de una task.
    Reservado para enviar notificaciones vía webhook a n8n.
    """
    if action in ['post_add', 'post_remove']:
        # TODO: Enviar webhook a n8n para notificar cambio de followers
        pass
