"""
SaiSuite — Proyectos: Signals
Recálculo automático de avance cuando cambia ProjectActivity o Task.
Notificaciones automáticas al responsable cuando se crea o modifica una tarea.
"""
import logging

from django.db.models.signals import m2m_changed, post_delete, post_save, pre_save
from django.dispatch import receiver

from apps.proyectos.models import ProjectActivity, Task, TaskDependency

logger = logging.getLogger(__name__)


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

# Campos rastreados para detectar cambios en pre_save → post_save
_TASK_TRACKED_FIELDS = ('responsable_id', 'estado', 'prioridad', 'fecha_inicio', 'fecha_fin', 'fecha_limite')


@receiver(pre_save, sender=Task)
def tarea_pre_save(sender, instance: Task, **kwargs):
    """
    Captura el estado anterior de los campos rastreados antes de guardar.
    El valor se almacena en atributos temporales del instance (no persisten en BD).
    Solo aplica en actualizaciones (instance.pk ya existe).
    """
    if not instance.pk:
        # Creación: no hay estado anterior
        instance._pre_save_snapshot = None
        return

    try:
        anterior = Task.objects.filter(pk=instance.pk).values(*_TASK_TRACKED_FIELDS).get()
        instance._pre_save_snapshot = anterior
    except Task.DoesNotExist:
        instance._pre_save_snapshot = None


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

    # Notificaciones automáticas — envueltas en try/except para no romper el flujo
    try:
        _notificar_cambios_tarea(instance, created)
    except Exception:
        logger.exception('error_notificaciones_tarea', extra={'tarea': str(instance.pk)})

    # Cascada Task → ProjectActivity → Fase → Proyecto (DEC-021)
    if instance.actividad_proyecto_id:
        from apps.proyectos.services import recalcular_cantidad_ejecutada_ap
        recalcular_cantidad_ejecutada_ap(instance.actividad_proyecto_id)
    if instance.fase_id:
        calcular_avance_fase_desde_tareas(instance.fase_id)
        if instance.proyecto_id:
            calcular_avance_proyecto(instance.proyecto_id)


def _notificar_cambios_tarea(instance: Task, created: bool) -> None:
    """
    Genera notificaciones automáticas al responsable cuando una tarea es
    creada o cuando cambian responsable, estado, prioridad o fechas.

    Importación lazy de NotificacionService para evitar dependencia circular
    en el startup de Django.
    """
    from apps.notifications.services import NotificacionService

    url_accion = f'/proyectos/tareas/{instance.pk}'
    metadata = {
        'tarea_nombre':    instance.nombre,
        'proyecto_nombre': getattr(getattr(instance, 'proyecto', None), 'nombre', ''),
        'tarea_codigo':    instance.codigo or '',
    }

    if created:
        # Nueva tarea: notificar al responsable si existe
        if instance.responsable_id:
            NotificacionService.crear(
                usuario=instance.responsable,
                tipo='asignacion',
                titulo=f'Tarea asignada: {instance.nombre}',
                mensaje=(
                    f'Se te asignó la tarea "{instance.nombre}" '
                    f'en el proyecto "{metadata["proyecto_nombre"]}".'
                ),
                objeto_relacionado=instance,
                url_accion=url_accion,
                metadata=metadata,
            )
            logger.info(
                'notificacion_tarea_creada',
                extra={'tarea': str(instance.pk), 'responsable': str(instance.responsable_id)},
            )
        return

    # ── Actualización: comparar contra snapshot capturado en pre_save ─────────
    snapshot = getattr(instance, '_pre_save_snapshot', None)
    if snapshot is None:
        # No hay snapshot (p.ej. bulk_update sin señal pre_save) — salir sin notificar
        return

    responsable_actual = instance.responsable

    # 1. Cambio de responsable
    anterior_responsable_id = snapshot.get('responsable_id')
    if instance.responsable_id != anterior_responsable_id:
        # Notificar al nuevo responsable
        if instance.responsable_id:
            NotificacionService.crear(
                usuario=responsable_actual,
                tipo='asignacion',
                titulo=f'Tarea asignada: {instance.nombre}',
                mensaje=(
                    f'Se te reasignó la tarea "{instance.nombre}" '
                    f'en el proyecto "{metadata["proyecto_nombre"]}".'
                ),
                objeto_relacionado=instance,
                url_accion=url_accion,
                metadata=metadata,
            )
            logger.info(
                'notificacion_tarea_reasignada_nuevo',
                extra={'tarea': str(instance.pk), 'nuevo_responsable': str(instance.responsable_id)},
            )
        # Notificar al responsable anterior (si existía)
        if anterior_responsable_id:
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                responsable_anterior = User.objects.get(pk=anterior_responsable_id)
                NotificacionService.crear(
                    usuario=responsable_anterior,
                    tipo='asignacion',
                    titulo=f'Ya no eres responsable: {instance.nombre}',
                    mensaje=(
                        f'Fuiste removido como responsable de la tarea '
                        f'"{instance.nombre}" en el proyecto "{metadata["proyecto_nombre"]}".'
                    ),
                    objeto_relacionado=instance,
                    url_accion=url_accion,
                    metadata=metadata,
                )
                logger.info(
                    'notificacion_tarea_reasignada_anterior',
                    extra={'tarea': str(instance.pk), 'anterior_responsable': str(anterior_responsable_id)},
                )
            except Exception:
                logger.exception(
                    'error_notificar_responsable_anterior',
                    extra={'tarea': str(instance.pk), 'anterior_responsable': str(anterior_responsable_id)},
                )
        # Tras el cambio de responsable, las notificaciones de estado/prioridad/fecha
        # ya se refieren al nuevo responsable — seguir evaluando los demás cambios.

    # A partir de aquí solo notificamos si hay responsable actual
    if not responsable_actual:
        return

    # 2. Cambio de estado
    if instance.estado != snapshot.get('estado'):
        estado_display = dict(instance._meta.get_field('estado').choices).get(instance.estado, instance.estado)
        NotificacionService.crear(
            usuario=responsable_actual,
            tipo='cambio_estado',
            titulo=f'Estado actualizado: {instance.nombre}',
            mensaje=f'La tarea "{instance.nombre}" cambió a estado "{estado_display}".',
            objeto_relacionado=instance,
            url_accion=url_accion,
            metadata={**metadata, 'estado_nuevo': instance.estado},
        )
        logger.info(
            'notificacion_cambio_estado_tarea',
            extra={'tarea': str(instance.pk), 'estado': instance.estado},
        )

    # 3. Cambio de prioridad
    if instance.prioridad != snapshot.get('prioridad'):
        prioridad_display = dict(instance._meta.get_field('prioridad').choices).get(instance.prioridad, str(instance.prioridad))
        NotificacionService.crear(
            usuario=responsable_actual,
            tipo='cambio_estado',
            titulo=f'Prioridad actualizada: {instance.nombre}',
            mensaje=f'La prioridad de la tarea "{instance.nombre}" cambió a "{prioridad_display}".',
            objeto_relacionado=instance,
            url_accion=url_accion,
            metadata={**metadata, 'prioridad_nueva': instance.prioridad},
        )
        logger.info(
            'notificacion_cambio_prioridad_tarea',
            extra={'tarea': str(instance.pk), 'prioridad': instance.prioridad},
        )

    # 4. Cambio de fechas (inicio, fin o límite)
    fechas_cambiaron = (
        instance.fecha_inicio  != snapshot.get('fecha_inicio')
        or instance.fecha_fin  != snapshot.get('fecha_fin')
        or instance.fecha_limite != snapshot.get('fecha_limite')
    )
    if fechas_cambiaron:
        NotificacionService.crear(
            usuario=responsable_actual,
            tipo='cambio_estado',
            titulo=f'Fechas actualizadas: {instance.nombre}',
            mensaje=f'Las fechas de la tarea "{instance.nombre}" fueron modificadas.',
            objeto_relacionado=instance,
            url_accion=url_accion,
            metadata={
                **metadata,
                'fecha_inicio':  str(instance.fecha_inicio)  if instance.fecha_inicio  else '',
                'fecha_fin':     str(instance.fecha_fin)     if instance.fecha_fin     else '',
                'fecha_limite':  str(instance.fecha_limite)  if instance.fecha_limite  else '',
            },
        )
        logger.info(
            'notificacion_cambio_fechas_tarea',
            extra={'tarea': str(instance.pk)},
        )


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


# ──────────────────────────────────────────────
# TaskDependency
# ──────────────────────────────────────────────

@receiver(post_save, sender=TaskDependency)
def dependencia_post_save(sender, instance: TaskDependency, created: bool, **kwargs):
    """
    Notifica a los responsables de ambas tareas cuando se crea una dependencia.
    Solo en creación — la edición de tipo/lag no dispara notificación.
    """
    if not created:
        return

    try:
        _notificar_nueva_dependencia(instance)
    except Exception:
        logger.exception('error_notificacion_dependencia', extra={'dependencia': str(instance.pk)})


def _notificar_nueva_dependencia(dep: TaskDependency) -> None:
    """Genera notificaciones para ambos responsables de una nueva dependencia."""
    from apps.notifications.services import NotificacionService

    pred = dep.tarea_predecesora
    suc = dep.tarea_sucesora
    tipo_display = dep.get_tipo_dependencia_display()
    proyecto = pred.proyecto

    metadata = {
        'proyecto_nombre': getattr(proyecto, 'nombre', ''),
        'tarea_predecesora': pred.nombre,
        'tarea_sucesora': suc.nombre,
        'tipo_dependencia': dep.tipo_dependencia,
    }

    notificados: set = set()

    # Notificar al responsable de la tarea predecesora
    if pred.responsable_id:
        NotificacionService.crear(
            usuario=pred.responsable,
            tipo='asignacion',
            titulo=f'Nueva dependencia: {suc.nombre}',
            mensaje=(
                f'La tarea "{suc.nombre}" ahora depende ({tipo_display}) '
                f'de tu tarea "{pred.nombre}".'
            ),
            objeto_relacionado=pred,
            url_accion=f'/proyectos/tareas/{pred.pk}',
            metadata=metadata,
        )
        notificados.add(pred.responsable_id)
        logger.info(
            'notificacion_dependencia_predecesora',
            extra={'dependencia': str(dep.pk), 'responsable': str(pred.responsable_id)},
        )

    # Notificar al responsable de la tarea sucesora (si es distinto)
    if suc.responsable_id and suc.responsable_id not in notificados:
        NotificacionService.crear(
            usuario=suc.responsable,
            tipo='asignacion',
            titulo=f'Nueva dependencia: {pred.nombre}',
            mensaje=(
                f'Tu tarea "{suc.nombre}" ahora depende ({tipo_display}) '
                f'de "{pred.nombre}".'
            ),
            objeto_relacionado=suc,
            url_accion=f'/proyectos/tareas/{suc.pk}',
            metadata=metadata,
        )
        logger.info(
            'notificacion_dependencia_sucesora',
            extra={'dependencia': str(dep.pk), 'responsable': str(suc.responsable_id)},
        )
