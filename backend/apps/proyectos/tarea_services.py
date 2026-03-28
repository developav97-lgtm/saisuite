"""
SaiSuite — Proyectos: TaskService + TimesheetService + TimesheetEntryService + DependencyService
TODA la lógica de negocio de Tareas va aquí. Las views solo orquestan.
"""
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import List, Optional

from django.db.models import Sum

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.proyectos.models import (
    Project, Phase, Task, TaskTag, WorkSession, TimesheetEntry,
    TaskDependency, SaiopenActivity, ProjectActivity, Activity,
    ProjectStatus, PhaseStatus, MeasurementMode, DependencyType,
)

logger = logging.getLogger(__name__)


class TaskService:
    """Service para operaciones de negocio de Tareas."""

    @staticmethod
    @transaction.atomic
    def crear_tarea_con_validaciones(
        proyecto: Project,
        nombre: str,
        **kwargs,
    ) -> Task:
        """
        Crear tarea con validaciones de negocio completas.

        Raises:
            ValidationError: Si el proyecto no está activo o la jerarquía es inválida.
        """
        estados_activos = ['planned', 'in_progress']
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

        # Auto-asignar fase: si no se provee, buscar la fase activa o la primera del proyecto (DEC-021)
        if 'fase' not in kwargs:
            fase = (
                Phase.all_objects.filter(proyecto=proyecto, estado=PhaseStatus.ACTIVE, activo=True).first()
                or Phase.all_objects.filter(proyecto=proyecto, activo=True).order_by('orden').first()
            )
            if fase:
                kwargs['fase'] = fase

        tarea = Task.objects.create(
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
    def validar_puede_completar(tarea: Task) -> tuple[bool, Optional[str]]:
        """
        Valida si una tarea puede ser completada.

        Returns:
            (puede_completar, mensaje_error)
        """
        if tarea.tiene_subtareas:
            subtareas_pendientes = tarea.subtasks.exclude(
                estado__in=['completed', 'cancelled']
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
        tarea: Task,
        nuevo_estado: str,
        user=None,
    ) -> Task:
        """
        Cambia el estado de la tarea con validaciones de negocio.

        Raises:
            ValidationError: Si el estado es inválido o no se puede completar.
        """
        estados_validos = [choice[0] for choice in Task._meta.get_field('estado').choices]
        if nuevo_estado not in estados_validos:
            raise ValidationError({
                'estado': f'Estado inválido. Opciones: {estados_validos}'
            })

        if nuevo_estado == 'completed':
            puede_completar, mensaje = TaskService.validar_puede_completar(tarea)
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
    def recalcular_avance_tarea_padre(tarea_padre: Task) -> None:
        """
        Recalcula el porcentaje_completado de una tarea a partir del promedio
        de sus subtareas. Usa QuerySet.update() para evitar disparar signals
        y prevenir recursión infinita.
        """
        subtareas = tarea_padre.subtasks.all()

        if not subtareas.exists():
            return

        total = subtareas.count()
        suma = sum(s.porcentaje_completado for s in subtareas)
        nuevo_porcentaje = int(suma / total)

        if tarea_padre.porcentaje_completado != nuevo_porcentaje:
            Task.objects.filter(id=tarea_padre.id).update(
                porcentaje_completado=nuevo_porcentaje
            )
            logger.info('Avance de tarea padre recalculado', extra={
                'tarea_padre_id': str(tarea_padre.id),
                'nuevo_porcentaje': nuevo_porcentaje,
            })

            # Propagación recursiva hacia arriba
            if tarea_padre.tarea_padre_id:
                tarea_abuelo = Task.objects.get(id=tarea_padre.tarea_padre_id)
                TaskService.recalcular_avance_tarea_padre(tarea_abuelo)

    @staticmethod
    @transaction.atomic
    def eliminar_tarea_con_subtareas(
        tarea: Task,
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

        subtareas_count = tarea.subtasks.count()
        tarea_id = tarea.id
        tarea_nombre = tarea.nombre

        if accion_subtareas == 'promover' and subtareas_count > 0:
            tarea.subtasks.update(tarea_padre=tarea.tarea_padre)

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
    def obtener_tareas_vencidas(proyecto: Optional[Project] = None) -> List[Task]:
        """
        Retorna tareas cuya fecha_limite ya pasó y no están completadas ni canceladas.
        """
        qs = Task.objects.filter(
            fecha_limite__lt=timezone.now().date()
        ).exclude(
            estado__in=['completed', 'cancelled']
        ).select_related('proyecto', 'responsable')

        if proyecto:
            qs = qs.filter(proyecto=proyecto)

        return list(qs)

    @staticmethod
    def obtener_tareas_proximas_vencer(
        dias: int = 1,
        proyecto: Optional[Project] = None,
    ) -> List[Task]:
        """
        Retorna tareas que vencen dentro de los próximos N días (inclusive hoy).
        """
        hoy = timezone.now().date()
        fecha_limite = hoy + timedelta(days=dias)

        qs = Task.objects.filter(
            fecha_limite__gte=hoy,
            fecha_limite__lte=fecha_limite,
        ).exclude(
            estado__in=['completed', 'cancelled']
        ).select_related('proyecto', 'responsable')

        if proyecto:
            qs = qs.filter(proyecto=proyecto)

        return list(qs)

    @staticmethod
    @transaction.atomic
    def generar_tarea_recurrente(tarea_original: Task) -> Optional[Task]:  # noqa: E501
        """
        Genera una nueva instancia de una tarea recurrente cuando la original
        es completada.

        Returns:
            Nueva Task creada, o None si no aplica.
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

        nueva_tarea = Task.objects.create(
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

        Task.objects.filter(id=tarea_original.id).update(
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
    def agregar_horas(tarea: Task, horas: Decimal) -> Task:
        """
        Agrega horas manualmente a las horas_registradas de la tarea.
        Sincroniza porcentaje_completado con el progreso calculado por horas.
        Raises:
            ValidationError: si las horas son <= 0.
        """
        if horas <= 0:
            raise ValidationError({'horas': 'Las horas deben ser mayores a 0.'})

        tarea.horas_registradas = tarea.horas_registradas + horas

        # Sincronizar porcentaje_completado con progreso calculado por horas
        update_fields = ['horas_registradas']
        if tarea.horas_estimadas and tarea.horas_estimadas > 0:
            nuevo_porcentaje = min(
                int(float(tarea.horas_registradas) / float(tarea.horas_estimadas) * 100),
                100,
            )
            tarea.porcentaje_completado = nuevo_porcentaje
            update_fields.append('porcentaje_completado')

        tarea.save(update_fields=update_fields)

        logger.info('Horas agregadas manualmente', extra={
            'tarea_id': str(tarea.id),
            'horas': str(horas),
            'porcentaje_completado': tarea.porcentaje_completado,
        })
        return tarea

    @staticmethod
    @transaction.atomic
    def agregar_cantidad(tarea: Task, cantidad: Decimal) -> Task:
        """
        Agrega cantidad ejecutada manualmente a cantidad_registrada.
        Sincroniza porcentaje_completado con el progreso calculado.
        Raises:
            ValidationError: si la cantidad es <= 0.
        """
        if cantidad <= 0:
            raise ValidationError({'cantidad': 'La cantidad debe ser mayor a 0.'})

        tarea.cantidad_registrada = tarea.cantidad_registrada + cantidad

        update_fields = ['cantidad_registrada']
        if tarea.cantidad_objetivo and tarea.cantidad_objetivo > 0:
            nuevo_porcentaje = min(
                int(float(tarea.cantidad_registrada) / float(tarea.cantidad_objetivo) * 100),
                100,
            )
            tarea.porcentaje_completado = nuevo_porcentaje
            update_fields.append('porcentaje_completado')

        tarea.save(update_fields=update_fields)

        logger.info('Cantidad agregada manualmente', extra={
            'tarea_id': str(tarea.id),
            'cantidad': str(cantidad),
            'porcentaje_completado': tarea.porcentaje_completado,
        })
        return tarea

    @staticmethod
    @transaction.atomic
    def iniciar_sesion(tarea: Task, usuario) -> WorkSession:
        """
        Inicia un cronómetro para la tarea.
        Solo puede haber una sesión activa por usuario a la vez.
        Raises:
            ValidationError: si ya existe una sesión activa o pausada.
        """
        sesion_activa = WorkSession.objects.filter(
            usuario=usuario,
            estado__in=['active', 'paused'],
        ).first()

        if sesion_activa:
            raise ValidationError(
                'Ya tienes una sesión activa. Detén o reanuda la sesión actual antes de iniciar una nueva.'
            )

        sesion = WorkSession.objects.create(
            company=tarea.company,
            tarea=tarea,
            usuario=usuario,
            inicio=timezone.now(),
            estado='active',
        )

        logger.info('Sesión de trabajo iniciada', extra={
            'sesion_id': str(sesion.id),
            'tarea_id': str(tarea.id),
            'usuario_id': str(usuario.id),
        })
        return sesion

    @staticmethod
    @transaction.atomic
    def pausar_sesion(sesion_id: str, usuario) -> WorkSession:
        """
        Pausa una sesión activa.
        Raises:
            ValidationError: si la sesión no existe o no está activa.
        """
        try:
            sesion = WorkSession.objects.get(
                id=sesion_id, usuario=usuario, estado='active',
            )
        except WorkSession.DoesNotExist:
            raise ValidationError('Sesión no encontrada o no está activa.')

        pausas = sesion.pausas or []
        pausas.append({'inicio': timezone.now().isoformat(), 'fin': None})
        sesion.pausas = pausas
        sesion.estado = 'paused'
        sesion.save(update_fields=['pausas', 'estado'])

        logger.info('Sesión pausada', extra={'sesion_id': str(sesion.id)})
        return sesion

    @staticmethod
    @transaction.atomic
    def reanudar_sesion(sesion_id: str, usuario) -> WorkSession:
        """
        Reanuda una sesión pausada cerrando el registro de pausa activo.
        Raises:
            ValidationError: si la sesión no existe o no está pausada.
        """
        try:
            sesion = WorkSession.objects.get(
                id=sesion_id, usuario=usuario, estado='paused',
            )
        except WorkSession.DoesNotExist:
            raise ValidationError('Sesión no encontrada o no está pausada.')

        pausas = sesion.pausas or []
        if pausas and pausas[-1]['fin'] is None:
            pausas[-1]['fin'] = timezone.now().isoformat()
        sesion.pausas = pausas
        sesion.estado = 'active'
        sesion.save(update_fields=['pausas', 'estado'])

        logger.info('Sesión reanudada', extra={'sesion_id': str(sesion.id)})
        return sesion

    @staticmethod
    @transaction.atomic
    def detener_sesion(sesion_id: str, usuario, notas: str = '') -> WorkSession:
        """
        Detiene la sesión (activa o pausada), calcula la duración neta
        y suma las horas a tarea.horas_registradas.
        Raises:
            ValidationError: si la sesión no existe.
        """
        try:
            sesion = WorkSession.objects.select_related('tarea').get(
                id=sesion_id,
                usuario=usuario,
                estado__in=['active', 'paused'],
            )
        except WorkSession.DoesNotExist:
            raise ValidationError('Sesión no encontrada.')

        ahora = timezone.now()

        # Cerrar pausa activa si la sesión estaba pausada
        if sesion.estado == 'paused':
            pausas = sesion.pausas or []
            if pausas and pausas[-1]['fin'] is None:
                pausas[-1]['fin'] = ahora.isoformat()
            sesion.pausas = pausas

        sesion.fin = ahora
        sesion.estado = 'finished'
        sesion.notas = notas
        sesion.duracion_segundos = TimesheetService._calcular_duracion_segundos(sesion)
        sesion.save(update_fields=['fin', 'estado', 'notas', 'duracion_segundos', 'pausas'])

        # Sumar horas a la tarea y sincronizar porcentaje_completado
        horas = Decimal(sesion.duracion_segundos) / Decimal(3600)
        tarea = sesion.tarea
        tarea.horas_registradas = tarea.horas_registradas + horas

        update_fields = ['horas_registradas']
        if tarea.horas_estimadas and tarea.horas_estimadas > 0:
            nuevo_porcentaje = min(
                int(float(tarea.horas_registradas) / float(tarea.horas_estimadas) * 100),
                100,
            )
            tarea.porcentaje_completado = nuevo_porcentaje
            update_fields.append('porcentaje_completado')

        tarea.save(update_fields=update_fields)

        logger.info('Sesión detenida', extra={
            'sesion_id': str(sesion.id),
            'duracion_segundos': sesion.duracion_segundos,
            'tarea_id': str(tarea.id),
            'porcentaje_completado': tarea.porcentaje_completado,
        })
        return sesion

    @staticmethod
    def sesion_activa_usuario(usuario) -> Optional[WorkSession]:
        """
        Retorna la sesión activa o pausada del usuario, o None si no hay ninguna.
        Útil para restaurar el estado del cronómetro al recargar la página.
        """
        return WorkSession.objects.filter(
            usuario=usuario,
            estado__in=['active', 'paused'],
        ).select_related('tarea').first()

    @staticmethod
    def _calcular_duracion_segundos(sesion: WorkSession) -> int:
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


class DependencyService:
    """
    Service para operaciones de dependencias entre tareas.
    Incluye detección de ciclos (DFS), CPM y reprogramación en cascada.
    """

    @staticmethod
    @transaction.atomic
    def crear_dependencia(
        predecesora_id: str,
        sucesora_id: str,
        company,
        tipo: str = 'FS',
        retraso_dias: int = 0,
    ) -> TaskDependency:
        """
        Crea una dependencia entre dos tareas validando que no forme un ciclo.

        Raises:
            ValidationError: si las tareas no existen, son iguales o forman ciclo.
        """
        if str(predecesora_id) == str(sucesora_id):
            raise ValidationError(
                'Una tarea no puede ser predecesora de sí misma.'
            )

        try:
            predecesora = Task.objects.get(id=predecesora_id, company=company)
            sucesora    = Task.objects.get(id=sucesora_id, company=company)
        except Task.DoesNotExist:
            raise ValidationError('Una o ambas tareas no existen.')

        if predecesora.proyecto_id != sucesora.proyecto_id:
            raise ValidationError(
                'Ambas tareas deben pertenecer al mismo proyecto.'
            )

        if DependencyService._detectar_ciclo(predecesora_id, sucesora_id, company):
            raise ValidationError(
                'La dependencia crearía un ciclo entre las tareas.'
            )

        dependencia, created = TaskDependency.objects.get_or_create(
            company=company,
            tarea_predecesora=predecesora,
            tarea_sucesora=sucesora,
            defaults={
                'tipo_dependencia': tipo,
                'retraso_dias': retraso_dias,
            },
        )

        if not created:
            raise ValidationError(
                'Ya existe una dependencia entre estas dos tareas.'
            )

        logger.info('dependencia_creada', extra={
            'predecesora_id': str(predecesora_id),
            'sucesora_id': str(sucesora_id),
            'tipo': tipo,
        })
        return dependencia

    @staticmethod
    def _detectar_ciclo(pred_id: str, suc_id: str, company) -> bool:
        """
        DFS desde suc_id para ver si se puede alcanzar pred_id.
        Si se puede alcanzar, agregar la arista pred→suc crearía un ciclo.
        Retorna True si habría ciclo, False si es seguro.
        """
        # Construir mapa de adyacencia para las tareas de la misma empresa
        sucesoras_map: dict[str, list[str]] = defaultdict(list)
        for dep in TaskDependency.objects.filter(company=company).values(
            'tarea_predecesora_id', 'tarea_sucesora_id'
        ):
            sucesoras_map[str(dep['tarea_predecesora_id'])].append(
                str(dep['tarea_sucesora_id'])
            )

        # BFS/DFS desde suc_id
        visitados: set[str] = set()
        cola = deque([str(suc_id)])
        pred_str = str(pred_id)

        while cola:
            actual = cola.popleft()
            if actual == pred_str:
                return True  # ciclo detectado
            if actual in visitados:
                continue
            visitados.add(actual)
            cola.extend(sucesoras_map.get(actual, []))

        return False

    @staticmethod
    def calcular_camino_critico(proyecto_id: str, company) -> List[str]:
        """
        Calcula el camino crítico del proyecto usando el algoritmo CPM.
        Retorna lista de IDs de tareas (str) que pertenecen al camino crítico.

        Solo considera tareas con fecha_inicio y fecha_fin definidas.
        Para tareas sin duración, se usa 1 día por defecto.
        """
        from datetime import date

        tareas_qs = Task.objects.filter(
            proyecto_id=proyecto_id,
            company=company,
        ).values('id', 'fecha_inicio', 'fecha_fin', 'nombre')

        if not tareas_qs:
            return []

        tareas_dict = {str(t['id']): t for t in tareas_qs}

        # Duraciones en días
        def duracion(tarea_id: str) -> int:
            t = tareas_dict.get(tarea_id)
            if not t:
                return 1
            fi = t['fecha_inicio']
            ff = t['fecha_fin']
            if fi and ff:
                delta = (ff - fi).days
                return max(1, delta)
            return 1

        deps_qs = TaskDependency.objects.filter(
            company=company,
            tarea_predecesora__proyecto_id=proyecto_id,
        ).values('tarea_predecesora_id', 'tarea_sucesora_id', 'retraso_dias')

        # Construir grafo
        sucesoras_map: dict[str, list[tuple[str, int]]] = defaultdict(list)
        predecesoras_map: dict[str, list[tuple[str, int]]] = defaultdict(list)

        for dep in deps_qs:
            pred = str(dep['tarea_predecesora_id'])
            suc  = str(dep['tarea_sucesora_id'])
            lag  = dep['retraso_dias']
            sucesoras_map[pred].append((suc, lag))
            predecesoras_map[suc].append((pred, lag))

        todos_ids = list(tareas_dict.keys())

        # Early Start (ES) y Early Finish (EF) — forward pass
        es: dict[str, int] = {tid: 0 for tid in todos_ids}
        ef: dict[str, int] = {}

        # Orden topológico con Kahn
        in_degree: dict[str, int] = {tid: 0 for tid in todos_ids}
        for pred, sucesoras in sucesoras_map.items():
            for suc, _ in sucesoras:
                if suc in in_degree:
                    in_degree[suc] += 1

        orden: list[str] = []
        queue = deque([tid for tid in todos_ids if in_degree[tid] == 0])
        while queue:
            nodo = queue.popleft()
            orden.append(nodo)
            for suc, lag in sucesoras_map.get(nodo, []):
                if suc not in in_degree:
                    continue
                in_degree[suc] -= 1
                # ES de sucesora = max(ES actual, EF de predecesora + lag)
                ef_pred = es[nodo] + duracion(nodo)
                es[suc] = max(es[suc], ef_pred + lag)
                if in_degree[suc] == 0:
                    queue.append(suc)

        for tid in todos_ids:
            ef[tid] = es[tid] + duracion(tid)

        # Late Start (LS) y Late Finish (LF) — backward pass
        duracion_proyecto = max(ef.values()) if ef else 0
        lf: dict[str, int] = {tid: duracion_proyecto for tid in todos_ids}
        ls: dict[str, int] = {}

        for nodo in reversed(orden):
            for suc, lag in sucesoras_map.get(nodo, []):
                if suc not in lf:
                    continue
                lf[nodo] = min(lf[nodo], lf[suc] - duracion(suc) - lag)

        for tid in todos_ids:
            ls[tid] = lf[tid] - duracion(tid)

        # Holgura total = LS - ES  (0 → camino crítico)
        criticas = [
            tid for tid in todos_ids
            if (ls[tid] - es[tid]) == 0
        ]

        logger.info('camino_critico_calculado', extra={
            'proyecto_id': str(proyecto_id),
            'tareas_criticas': len(criticas),
        })
        return criticas

    @staticmethod
    @transaction.atomic
    def reprogramar_en_cascada(tarea_id: str, company, _visitados: Optional[set] = None) -> None:
        """
        Reprograma automáticamente las tareas sucesoras de tipo FS
        cuando cambia la fecha_fin de una predecesora.
        Solo ajusta si la nueva fecha es POSTERIOR a la actual.
        Recursivo: propaga cambios hacia abajo en la cadena.
        """
        if _visitados is None:
            _visitados = set()

        if str(tarea_id) in _visitados:
            return  # prevenir loops
        _visitados.add(str(tarea_id))

        try:
            predecesora = Task.objects.get(id=tarea_id, company=company)
        except Task.DoesNotExist:
            return

        if not predecesora.fecha_fin:
            return

        deps_fs = TaskDependency.objects.filter(
            tarea_predecesora=predecesora,
            tipo_dependencia='FS',
            company=company,
        ).select_related('tarea_sucesora')

        for dep in deps_fs:
            sucesora = dep.tarea_sucesora
            nueva_fecha_inicio = predecesora.fecha_fin + timedelta(days=dep.retraso_dias)

            if sucesora.fecha_inicio is None or nueva_fecha_inicio > sucesora.fecha_inicio:
                # Calcular desplazamiento para mantener duración
                if sucesora.fecha_inicio and sucesora.fecha_fin:
                    duracion_dias = (sucesora.fecha_fin - sucesora.fecha_inicio).days
                else:
                    duracion_dias = None

                sucesora.fecha_inicio = nueva_fecha_inicio
                if duracion_dias is not None:
                    sucesora.fecha_fin = nueva_fecha_inicio + timedelta(days=duracion_dias)

                sucesora.save(update_fields=['fecha_inicio', 'fecha_fin'])
                logger.info('tarea_reprogramada_cascada', extra={
                    'sucesora_id': str(sucesora.id),
                    'nueva_fecha_inicio': str(nueva_fecha_inicio),
                })

                # Recursión hacia las sucesoras de la sucesora
                DependencyService.reprogramar_en_cascada(
                    str(sucesora.id), company, _visitados
                )


# ──────────────────────────────────────────────────────────────────────────────
# TimesheetEntryService
# ──────────────────────────────────────────────────────────────────────────────

class TimesheetEntryService:
    """
    Lógica de negocio para registros diarios de horas (TimesheetEntry).
    Gestiona registro manual, edición, eliminación y validación por manager.
    """

    # ── Registro manual ───────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def registrar_horas(
        tarea_id: str,
        usuario,
        fecha: date,
        horas: Decimal,
        descripcion: str = '',
        company=None,
    ):
        """
        Crea o actualiza un registro de horas/días para usuario/tarea/fecha.
        Si ya existe un entry para ese día/tarea/usuario, lo actualiza
        siempre que no esté validado.
        Siempre recalcula tarea.horas_registradas con la suma de todos los entries.

        Raises:
            ValidationError: si horas fuera de rango o entry ya validado.
        """
        if horas <= 0 or horas > 365:
            raise ValidationError({'horas': 'El valor debe estar entre 0.01 y 365.'})

        tarea = Task.objects.select_related('company').get(
            id=tarea_id, company=company,
        )

        entry, created = TimesheetEntry.objects.get_or_create(
            tarea=tarea,
            usuario=usuario,
            fecha=fecha,
            defaults={
                'company': company,
                'horas': horas,
                'descripcion': descripcion,
            },
        )

        if not created:
            if entry.validado:
                raise ValidationError(
                    'Este registro ya fue validado y no se puede modificar.'
                )
            entry.horas       = horas
            entry.descripcion = descripcion
            entry.save(update_fields=['horas', 'descripcion'])

        # Recalcular horas_registradas con todos los entries (validados y no validados)
        TimesheetEntryService._recalcular_horas(tarea)

        logger.info('timesheet_entry_registrado', extra={
            'entry_id': str(entry.id),
            'tarea_id': tarea_id,
            'usuario_id': str(usuario.id),
            'fecha': str(fecha),
            'horas': str(horas),
            'es_nuevo': created,
        })
        return entry

    @staticmethod
    @transaction.atomic
    def eliminar_entry(entry_id: str, usuario):
        """
        Elimina un entry no validado. Solo el propietario o admin puede eliminar.

        Raises:
            ValidationError: si el entry está validado.
        """
        try:
            entry = TimesheetEntry.objects.get(id=entry_id, usuario=usuario)
        except TimesheetEntry.DoesNotExist:
            raise ValidationError('Registro no encontrado.')

        if entry.validado:
            raise ValidationError('No se puede eliminar un registro ya validado.')

        tarea = entry.tarea
        entry.delete()

        # Recalcular horas_registradas tras eliminar
        TimesheetEntryService._recalcular_horas(tarea)

        logger.info('timesheet_entry_eliminado', extra={'entry_id': entry_id})

    # ── Validación por manager ─────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def validar_timesheet(entry_id: str, validador):
        """
        Manager/coordinador aprueba un registro de horas.
        Solo puede validar el gerente o coordinador del proyecto,
        o un company_admin.
        Al validar, recalcula tarea.horas_registradas con la suma de entries validados.

        Raises:
            ValidationError: si el validador no tiene permisos o el entry no existe.
        """
        from django.utils import timezone

        try:
            entry = TimesheetEntry.objects.select_related(
                'tarea__proyecto',
            ).get(id=entry_id)
        except TimesheetEntry.DoesNotExist:
            raise ValidationError('Registro no encontrado.')

        if entry.validado:
            raise ValidationError('Este registro ya fue validado.')

        # Verificar permiso: company_admin, gerente o coordinador del proyecto
        proyecto = entry.tarea.proyecto
        es_admin = getattr(validador, 'role', '') == 'company_admin' or getattr(validador, 'is_staff', False)
        es_gerente     = str(proyecto.gerente_id)     == str(validador.id)
        es_coordinador = proyecto.coordinador_id and str(proyecto.coordinador_id) == str(validador.id)

        if not (es_admin or es_gerente or es_coordinador):
            raise ValidationError(
                'Solo el gerente, coordinador del proyecto o administrador pueden validar registros de horas.'
            )

        entry.validado         = True
        entry.validado_por     = validador
        entry.fecha_validacion = timezone.now()
        entry.save(update_fields=['validado', 'validado_por', 'fecha_validacion'])

        TimesheetEntryService.recalcular_horas_tarea(str(entry.tarea_id))

        logger.info('timesheet_entry_validado', extra={
            'entry_id': str(entry.id),
            'validador_id': str(validador.id),
        })
        return entry

    # ── Cálculo de horas acumuladas ────────────────────────────────────────────

    @staticmethod
    def _recalcular_horas(tarea) -> None:
        """Suma todos los entries (validados y no validados) y actualiza la tarea."""
        total = TimesheetEntry.objects.filter(
            tarea=tarea,
        ).aggregate(total=Sum('horas'))['total'] or Decimal('0')

        tarea.horas_registradas = total
        update_fields = ['horas_registradas']
        if tarea.horas_estimadas and tarea.horas_estimadas > 0:
            nuevo_pct = min(
                int(float(total) / float(tarea.horas_estimadas) * 100),
                100,
            )
            tarea.porcentaje_completado = nuevo_pct
            update_fields.append('porcentaje_completado')
        tarea.save(update_fields=update_fields)

    @staticmethod
    @transaction.atomic
    def recalcular_horas_tarea(tarea_id: str) -> Decimal:
        """
        Recalcula tarea.horas_registradas como suma de todos los entries validados.
        """
        total = TimesheetEntry.objects.filter(
            tarea_id=tarea_id,
            validado=True,
        ).aggregate(total=Sum('horas'))['total'] or Decimal('0')

        tarea = Task.objects.get(id=tarea_id)
        tarea.horas_registradas = Decimal(str(total))

        update_fields = ['horas_registradas']
        if tarea.horas_estimadas and tarea.horas_estimadas > 0:
            nuevo_porcentaje = min(
                int(float(tarea.horas_registradas) / float(tarea.horas_estimadas) * 100),
                100,
            )
            tarea.porcentaje_completado = nuevo_porcentaje
            update_fields.append('porcentaje_completado')

        tarea.save(update_fields=update_fields)

        logger.info('horas_tarea_recalculadas', extra={
            'tarea_id': tarea_id,
            'total': str(total),
        })
        return Decimal(str(total))

    # ── Consulta semanal ──────────────────────────────────────────────────────

    @staticmethod
    def mis_horas(usuario, fecha_inicio: date, fecha_fin: date, company=None):
        """
        Retorna los TimesheetEntry del usuario en el rango [fecha_inicio, fecha_fin],
        opcionalmente filtrado por company.
        """
        qs = TimesheetEntry.objects.filter(
            usuario=usuario,
            fecha__gte=fecha_inicio,
            fecha__lte=fecha_fin,
        ).select_related('tarea', 'validado_por').order_by('-fecha', '-created_at')

        if company:
            qs = qs.filter(company=company)

        return qs

