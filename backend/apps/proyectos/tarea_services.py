"""
SaiSuite — Proyectos: TareaService + TimesheetService
TODA la lógica de negocio de Tareas va aquí. Las views solo orquestan.
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.proyectos.models import Proyecto, Tarea

logger = logging.getLogger(__name__)


class TareaService:
    """Service para operaciones de negocio de Tareas."""

    @staticmethod
    @transaction.atomic
    def crear_tarea_con_validaciones(
        proyecto: Proyecto,
        nombre: str,
        **kwargs,
    ) -> Tarea:
        """
        Crear tarea con validaciones de negocio completas.

        Raises:
            ValidationError: Si el proyecto no está activo o la jerarquía es inválida.
        """
        estados_activos = ['planificado', 'en_ejecucion']
        if proyecto.estado not in estados_activos:
            raise ValidationError({
                'proyecto': (
                    f'No se pueden crear tareas en proyecto con estado "{proyecto.estado}". '
                    f'El proyecto debe estar en {estados_activos}.'
                )
            })

        tarea_padre = kwargs.get('tarea_padre')
        if tarea_padre:
            if tarea_padre.proyecto_id != proyecto.id:
                raise ValidationError({
                    'tarea_padre': 'La tarea padre debe pertenecer al mismo proyecto.'
                })
            if tarea_padre.nivel_jerarquia >= 4:
                raise ValidationError({
                    'tarea_padre': 'Máximo 5 niveles de jerarquía (0-4). La tarea padre ya está en el nivel máximo.'
                })

        tarea = Tarea.objects.create(
            proyecto=proyecto,
            company=proyecto.company,
            nombre=nombre,
            **kwargs,
        )

        logger.info('Tarea creada', extra={
            'tarea_id': str(tarea.id),
            'codigo': tarea.codigo,
            'proyecto_id': str(proyecto.id),
        })
        return tarea

    @staticmethod
    def validar_puede_completar(tarea: Tarea) -> tuple[bool, Optional[str]]:
        """
        Valida si una tarea puede ser completada.

        Returns:
            (puede_completar, mensaje_error)
        """
        if tarea.tiene_subtareas:
            subtareas_pendientes = tarea.subtareas.exclude(
                estado__in=['completada', 'cancelada']
            ).count()

            if subtareas_pendientes > 0:
                return (
                    False,
                    f'No se puede completar: hay {subtareas_pendientes} subtarea(s) pendiente(s).',
                )

        return (True, None)

    @staticmethod
    @transaction.atomic
    def cambiar_estado(
        tarea: Tarea,
        nuevo_estado: str,
        user=None,
    ) -> Tarea:
        """
        Cambia el estado de la tarea con validaciones de negocio.

        Raises:
            ValidationError: Si el estado es inválido o no se puede completar.
        """
        estados_validos = [choice[0] for choice in Tarea._meta.get_field('estado').choices]
        if nuevo_estado not in estados_validos:
            raise ValidationError({
                'estado': f'Estado inválido. Opciones: {estados_validos}'
            })

        if nuevo_estado == 'completada':
            puede_completar, mensaje = TareaService.validar_puede_completar(tarea)
            if not puede_completar:
                raise ValidationError({'estado': mensaje})
            tarea.porcentaje_completado = 100

        tarea.estado = nuevo_estado
        tarea.save()

        logger.info('Estado de tarea cambiado', extra={
            'tarea_id': str(tarea.id),
            'nuevo_estado': nuevo_estado,
        })
        return tarea

    @staticmethod
    def recalcular_avance_tarea_padre(tarea_padre: Tarea) -> None:
        """
        Recalcula el porcentaje_completado de una tarea a partir del promedio
        de sus subtareas. Usa QuerySet.update() para evitar disparar signals
        y prevenir recursión infinita.
        """
        subtareas = tarea_padre.subtareas.all()

        if not subtareas.exists():
            return

        total = subtareas.count()
        suma = sum(s.porcentaje_completado for s in subtareas)
        nuevo_porcentaje = int(suma / total)

        if tarea_padre.porcentaje_completado != nuevo_porcentaje:
            Tarea.objects.filter(id=tarea_padre.id).update(
                porcentaje_completado=nuevo_porcentaje
            )
            logger.info('Avance de tarea padre recalculado', extra={
                'tarea_padre_id': str(tarea_padre.id),
                'nuevo_porcentaje': nuevo_porcentaje,
            })

            # Propagación recursiva hacia arriba
            if tarea_padre.tarea_padre_id:
                tarea_abuelo = Tarea.objects.get(id=tarea_padre.tarea_padre_id)
                TareaService.recalcular_avance_tarea_padre(tarea_abuelo)

    @staticmethod
    @transaction.atomic
    def eliminar_tarea_con_subtareas(
        tarea: Tarea,
        accion_subtareas: str = 'cascada',
    ) -> dict:
        """
        Elimina una tarea con manejo explícito de sus subtareas.

        Args:
            accion_subtareas: 'cascada' (elimina todo) o 'promover' (sube subtareas un nivel).

        Raises:
            ValidationError: Si la acción es inválida.
        """
        if accion_subtareas not in ['cascada', 'promover']:
            raise ValidationError({
                'accion_subtareas': 'Debe ser "cascada" o "promover".'
            })

        subtareas_count = tarea.subtareas.count()
        tarea_id = tarea.id
        tarea_nombre = tarea.nombre

        if accion_subtareas == 'promover' and subtareas_count > 0:
            tarea.subtareas.update(tarea_padre=tarea.tarea_padre)

        tarea.delete()

        logger.info('Tarea eliminada', extra={
            'tarea_id': str(tarea_id),
            'accion_subtareas': accion_subtareas,
            'subtareas_afectadas': subtareas_count,
        })

        return {
            'success': True,
            'tarea_id': tarea_id,
            'tarea_nombre': tarea_nombre,
            'subtareas_eliminadas': subtareas_count if accion_subtareas == 'cascada' else 0,
            'subtareas_promovidas': subtareas_count if accion_subtareas == 'promover' else 0,
        }

    @staticmethod
    def obtener_tareas_vencidas(proyecto: Optional[Proyecto] = None) -> List[Tarea]:
        """
        Retorna tareas cuya fecha_limite ya pasó y no están completadas ni canceladas.
        """
        qs = Tarea.objects.filter(
            fecha_limite__lt=timezone.now().date()
        ).exclude(
            estado__in=['completada', 'cancelada']
        ).select_related('proyecto', 'responsable')

        if proyecto:
            qs = qs.filter(proyecto=proyecto)

        return list(qs)

    @staticmethod
    def obtener_tareas_proximas_vencer(
        dias: int = 1,
        proyecto: Optional[Proyecto] = None,
    ) -> List[Tarea]:
        """
        Retorna tareas que vencen dentro de los próximos N días (inclusive hoy).
        """
        hoy = timezone.now().date()
        fecha_limite = hoy + timedelta(days=dias)

        qs = Tarea.objects.filter(
            fecha_limite__gte=hoy,
            fecha_limite__lte=fecha_limite,
        ).exclude(
            estado__in=['completada', 'cancelada']
        ).select_related('proyecto', 'responsable')

        if proyecto:
            qs = qs.filter(proyecto=proyecto)

        return list(qs)

    @staticmethod
    @transaction.atomic
    def generar_tarea_recurrente(tarea_original: Tarea) -> Optional[Tarea]:  # noqa: E501
        """
        Genera una nueva instancia de una tarea recurrente cuando la original
        es completada.

        Returns:
            Nueva Tarea creada, o None si no aplica.
        """
        if not tarea_original.es_recurrente:
            return None

        if not tarea_original.frecuencia_recurrencia:
            return None

        deltas = {
            'diaria': timedelta(days=1),
            'semanal': timedelta(weeks=1),
            'mensual': timedelta(days=30),
        }
        delta = deltas.get(tarea_original.frecuencia_recurrencia)
        if delta is None:
            return None

        base_fecha = tarea_original.fecha_limite or timezone.now().date()
        nueva_fecha_limite = base_fecha + delta

        nueva_tarea = Tarea.objects.create(
            company=tarea_original.company,
            proyecto=tarea_original.proyecto,
            fase=tarea_original.fase,
            tarea_padre=tarea_original.tarea_padre,
            nombre=tarea_original.nombre,
            descripcion=tarea_original.descripcion,
            responsable=tarea_original.responsable,
            prioridad=tarea_original.prioridad,
            horas_estimadas=tarea_original.horas_estimadas,
            fecha_limite=nueva_fecha_limite,
            es_recurrente=True,
            frecuencia_recurrencia=tarea_original.frecuencia_recurrencia,
        )

        nueva_tarea.tags.set(tarea_original.tags.all())
        nueva_tarea.followers.set(tarea_original.followers.all())

        Tarea.objects.filter(id=tarea_original.id).update(
            proxima_generacion=nueva_fecha_limite
        )

        logger.info('Tarea recurrente generada', extra={
            'original_id': str(tarea_original.id),
            'nueva_id': str(nueva_tarea.id),
            'nueva_fecha_limite': str(nueva_fecha_limite),
        })
        return nueva_tarea


class TimesheetService:
    """
    Service para el sistema de timesheet (registro de horas) en tareas.
    Modo manual y cronómetro con pausas.
    """

    @staticmethod
    @transaction.atomic
    def agregar_horas(tarea: Tarea, horas: Decimal) -> Tarea:
        """
        Agrega horas manualmente a las horas_registradas de la tarea.
        Raises:
            ValidationError: si las horas son <= 0.
        """
        if horas <= 0:
            raise ValidationError({'horas': 'Las horas deben ser mayores a 0.'})

        tarea.horas_registradas = tarea.horas_registradas + horas
        tarea.save(update_fields=['horas_registradas'])

        logger.info('Horas agregadas manualmente', extra={
            'tarea_id': str(tarea.id),
            'horas': str(horas),
        })
        return tarea

    @staticmethod
    @transaction.atomic
    def iniciar_sesion(tarea: Tarea, usuario) -> 'SesionTrabajo':
        """
        Inicia un cronómetro para la tarea.
        Solo puede haber una sesión activa por usuario a la vez.
        Raises:
            ValidationError: si ya existe una sesión activa o pausada.
        """
        from apps.proyectos.models import SesionTrabajo

        sesion_activa = SesionTrabajo.objects.filter(
            usuario=usuario,
            estado__in=['activa', 'pausada'],
        ).first()

        if sesion_activa:
            raise ValidationError(
                'Ya tienes una sesión activa. Detén o reanuda la sesión actual antes de iniciar una nueva.'
            )

        sesion = SesionTrabajo.objects.create(
            company=tarea.company,
            tarea=tarea,
            usuario=usuario,
            inicio=timezone.now(),
            estado='activa',
        )

        logger.info('Sesión de trabajo iniciada', extra={
            'sesion_id': str(sesion.id),
            'tarea_id': str(tarea.id),
            'usuario_id': str(usuario.id),
        })
        return sesion

    @staticmethod
    @transaction.atomic
    def pausar_sesion(sesion_id: str, usuario) -> 'SesionTrabajo':
        """
        Pausa una sesión activa.
        Raises:
            ValidationError: si la sesión no existe o no está activa.
        """
        from apps.proyectos.models import SesionTrabajo

        try:
            sesion = SesionTrabajo.objects.get(
                id=sesion_id, usuario=usuario, estado='activa',
            )
        except SesionTrabajo.DoesNotExist:
            raise ValidationError('Sesión no encontrada o no está activa.')

        pausas = sesion.pausas or []
        pausas.append({'inicio': timezone.now().isoformat(), 'fin': None})
        sesion.pausas = pausas
        sesion.estado = 'pausada'
        sesion.save(update_fields=['pausas', 'estado'])

        logger.info('Sesión pausada', extra={'sesion_id': str(sesion.id)})
        return sesion

    @staticmethod
    @transaction.atomic
    def reanudar_sesion(sesion_id: str, usuario) -> 'SesionTrabajo':
        """
        Reanuda una sesión pausada cerrando el registro de pausa activo.
        Raises:
            ValidationError: si la sesión no existe o no está pausada.
        """
        from apps.proyectos.models import SesionTrabajo

        try:
            sesion = SesionTrabajo.objects.get(
                id=sesion_id, usuario=usuario, estado='pausada',
            )
        except SesionTrabajo.DoesNotExist:
            raise ValidationError('Sesión no encontrada o no está pausada.')

        pausas = sesion.pausas or []
        if pausas and pausas[-1]['fin'] is None:
            pausas[-1]['fin'] = timezone.now().isoformat()
        sesion.pausas = pausas
        sesion.estado = 'activa'
        sesion.save(update_fields=['pausas', 'estado'])

        logger.info('Sesión reanudada', extra={'sesion_id': str(sesion.id)})
        return sesion

    @staticmethod
    @transaction.atomic
    def detener_sesion(sesion_id: str, usuario, notas: str = '') -> 'SesionTrabajo':
        """
        Detiene la sesión (activa o pausada), calcula la duración neta
        y suma las horas a tarea.horas_registradas.
        Raises:
            ValidationError: si la sesión no existe.
        """
        from apps.proyectos.models import SesionTrabajo

        try:
            sesion = SesionTrabajo.objects.select_related('tarea').get(
                id=sesion_id,
                usuario=usuario,
                estado__in=['activa', 'pausada'],
            )
        except SesionTrabajo.DoesNotExist:
            raise ValidationError('Sesión no encontrada.')

        ahora = timezone.now()

        # Cerrar pausa activa si la sesión estaba pausada
        if sesion.estado == 'pausada':
            pausas = sesion.pausas or []
            if pausas and pausas[-1]['fin'] is None:
                pausas[-1]['fin'] = ahora.isoformat()
            sesion.pausas = pausas

        sesion.fin = ahora
        sesion.estado = 'finalizada'
        sesion.notas = notas
        sesion.duracion_segundos = TimesheetService._calcular_duracion_segundos(sesion)
        sesion.save(update_fields=['fin', 'estado', 'notas', 'duracion_segundos', 'pausas'])

        # Sumar horas a la tarea
        horas = Decimal(sesion.duracion_segundos) / Decimal(3600)
        tarea = sesion.tarea
        tarea.horas_registradas = tarea.horas_registradas + horas
        tarea.save(update_fields=['horas_registradas'])

        logger.info('Sesión detenida', extra={
            'sesion_id': str(sesion.id),
            'duracion_segundos': sesion.duracion_segundos,
            'tarea_id': str(tarea.id),
        })
        return sesion

    @staticmethod
    def sesion_activa_usuario(usuario) -> Optional['SesionTrabajo']:
        """
        Retorna la sesión activa o pausada del usuario, o None si no hay ninguna.
        Útil para restaurar el estado del cronómetro al recargar la página.
        """
        from apps.proyectos.models import SesionTrabajo

        return SesionTrabajo.objects.filter(
            usuario=usuario,
            estado__in=['activa', 'pausada'],
        ).select_related('tarea').first()

    @staticmethod
    def _calcular_duracion_segundos(sesion: 'SesionTrabajo') -> int:
        """
        Calcula la duración neta de la sesión en segundos,
        restando el tiempo total de pausas.
        """
        fin = sesion.fin or timezone.now()
        duracion_total = (fin - sesion.inicio).total_seconds()

        duracion_pausas = 0.0
        for pausa in (sesion.pausas or []):
            inicio_pausa = datetime.fromisoformat(
                pausa['inicio'].replace('Z', '+00:00')
            )
            if pausa.get('fin'):
                fin_pausa = datetime.fromisoformat(
                    pausa['fin'].replace('Z', '+00:00')
                )
                duracion_pausas += (fin_pausa - inicio_pausa).total_seconds()

        return max(0, int(duracion_total - duracion_pausas))
