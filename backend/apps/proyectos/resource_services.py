"""
SaiSuite — Proyectos: ResourceService
TODA la lógica de negocio de Resource Management va aquí.
Las views solo orquestan: reciben request → llaman service → retornan response.

Servicios implementados:
    - assign_resource_to_task()        BK-11
    - remove_resource_from_task()      BK-12
    - detect_overallocation_conflicts()  BK-13  (Día 3)
    - calculate_user_workload()          BK-14  (Día 5)
    - get_team_availability_timeline()   BK-15  (Día 5)
    - set_user_capacity()                BK-16  (Día 4)
    - register_availability()            BK-17  (Día 4)
    - approve_availability()             BK-18  (Día 4)
"""
import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.proyectos.models import (
    ResourceAssignment,
    ResourceAvailability,
    ResourceCapacity,
    Task,
    TimesheetEntry,
    AvailabilityType,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# BK-11: assign_resource_to_task
# ---------------------------------------------------------------------------

@transaction.atomic
def assign_resource_to_task(
    tarea: Task,
    usuario_id: str,
    porcentaje_asignacion: Decimal,
    fecha_inicio: date,
    fecha_fin: date,
    notas: str = '',
) -> ResourceAssignment:
    """
    Asigna un usuario a una tarea con porcentaje de dedicación y rango de fechas.

    Validaciones:
    - La tarea debe pertenecer a un proyecto activo (planned o in_progress)
    - fecha_fin >= fecha_inicio
    - porcentaje_asignacion entre 0.01 y 100
    - El usuario no puede tener ya una asignación activa en la misma tarea
      (unique_together a nivel de BD; aquí damos un mensaje claro)

    No bloquea por sobreasignación (>100%): solo advierte en la respuesta.
    La detección de conflictos se consulta aparte vía detect_overallocation_conflicts().

    Args:
        tarea: instancia de Task ya cargada
        usuario_id: UUID del usuario a asignar
        porcentaje_asignacion: fracción de dedicación (0.01–100)
        fecha_inicio: inicio de la asignación
        fecha_fin: fin de la asignación
        notas: texto libre opcional

    Returns:
        ResourceAssignment creado

    Raises:
        ValidationError: si alguna validación de negocio falla
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # 1. Validar estado de la tarea
    estados_permitidos = ['todo', 'in_progress', 'in_review', 'blocked']
    if tarea.estado not in estados_permitidos:
        raise ValidationError({
            'tarea': (
                f'No se puede asignar recursos a una tarea con estado "{tarea.estado}". '
                f'La tarea debe estar en: {estados_permitidos}.'
            )
        })

    # 2. Validar que el proyecto está activo
    estados_proyecto_activos = ['planned', 'in_progress']
    if tarea.proyecto.estado not in estados_proyecto_activos:
        raise ValidationError({
            'tarea': (
                f'El proyecto "{tarea.proyecto.codigo}" tiene estado '
                f'"{tarea.proyecto.estado}" y no admite nuevas asignaciones.'
            )
        })

    # 3. Validar fechas
    if fecha_fin < fecha_inicio:
        raise ValidationError({
            'fecha_fin': 'La fecha de fin debe ser igual o posterior a la fecha de inicio.'
        })

    # 4. Validar porcentaje
    if not (Decimal('0.01') <= porcentaje_asignacion <= Decimal('100')):
        raise ValidationError({
            'porcentaje_asignacion': 'El porcentaje debe estar entre 0.01 y 100.'
        })

    # 5. Obtener usuario — validar que pertenece a la misma empresa
    try:
        usuario = User.objects.get(id=usuario_id, company=tarea.company)
    except User.DoesNotExist:
        raise ValidationError({
            'usuario_id': 'El usuario no existe o no pertenece a la misma empresa.'
        })

    # 6. Verificar si ya existe asignación activa para este usuario en esta tarea
    existe = ResourceAssignment.objects.filter(
        company=tarea.company,
        tarea=tarea,
        usuario=usuario,
        activo=True,
    ).exists()
    if existe:
        raise ValidationError({
            'usuario_id': (
                f'{usuario.full_name or usuario.email} ya tiene una asignación '
                f'activa en esta tarea. Elimina la existente antes de reasignar.'
            )
        })

    # 7. Crear la asignación
    asignacion = ResourceAssignment.objects.create(
        company=tarea.company,
        tarea=tarea,
        usuario=usuario,
        porcentaje_asignacion=porcentaje_asignacion,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        notas=notas,
        activo=True,
    )

    logger.info(
        'recurso_asignado',
        extra={
            'asignacion_id': str(asignacion.id),
            'tarea_id':      str(tarea.id),
            'tarea_codigo':  tarea.codigo,
            'usuario_id':    str(usuario.id),
            'porcentaje':    str(porcentaje_asignacion),
            'fecha_inicio':  str(fecha_inicio),
            'fecha_fin':     str(fecha_fin),
            'company_id':    str(tarea.company_id),
        },
    )

    return asignacion


# ---------------------------------------------------------------------------
# BK-12: remove_resource_from_task
# ---------------------------------------------------------------------------

@transaction.atomic
def remove_resource_from_task(
    asignacion_id: str,
    company_id: str,
) -> None:
    """
    Desactiva (soft delete) una asignación de recurso.

    No elimina físicamente el registro — preserva el histórico de asignaciones.
    Para eliminar permanentemente usar el Django Admin.

    Args:
        asignacion_id: UUID de la ResourceAssignment
        company_id: UUID de la empresa (validación multi-tenant)

    Raises:
        ValidationError: si la asignación no existe o ya está inactiva
    """
    try:
        asignacion = ResourceAssignment.objects.get(
            id=asignacion_id,
            company_id=company_id,
        )
    except ResourceAssignment.DoesNotExist:
        raise ValidationError({
            'asignacion_id': 'La asignación no existe o no pertenece a esta empresa.'
        })

    if not asignacion.activo:
        raise ValidationError({
            'asignacion_id': 'La asignación ya está inactiva.'
        })

    asignacion.activo = False
    asignacion.save(update_fields=['activo', 'updated_at'])

    logger.info(
        'recurso_desasignado',
        extra={
            'asignacion_id': str(asignacion.id),
            'tarea_id':      str(asignacion.tarea_id),
            'usuario_id':    str(asignacion.usuario_id),
            'company_id':    company_id,
        },
    )


# ---------------------------------------------------------------------------
# BK-13: detect_overallocation_conflicts  (Día 3)
# ---------------------------------------------------------------------------

@dataclass
class OverallocationConflict:
    fecha: date
    porcentaje_total: Decimal
    asignaciones: list[dict] = field(default_factory=list)


def detect_overallocation_conflicts(
    usuario_id: str,
    company_id: str,
    start_date: date,
    end_date: date,
    threshold: Decimal = Decimal('100.00'),
    exclude_asignacion_id: Optional[str] = None,
) -> list[OverallocationConflict]:
    """
    Detecta días donde la suma de porcentaje_asignacion supera el threshold.

    Definición de sobreasignación (DEC-025): sobreasignado si la suma de
    porcentajes en CUALQUIER DÍA del período supera el threshold (default: 100%).

    Estrategia: 1 SQL query trae todos los assignments que solapan el período.
    La suma por día se calcula en Python sobre el resultado en memoria
    (O(assignments × días) — negligible para <500 assignments por usuario).

    Args:
        usuario_id: UUID del usuario
        company_id: UUID de la empresa (multi-tenant)
        start_date: inicio del período a verificar
        end_date: fin del período a verificar
        threshold: porcentaje máximo permitido (default 100%)
        exclude_asignacion_id: UUID de asignación a excluir (útil al actualizar)

    Returns:
        Lista de OverallocationConflict ordenada por fecha, vacía si no hay conflictos
    """
    qs = ResourceAssignment.objects.filter(
        company_id=company_id,
        usuario_id=usuario_id,
        activo=True,
        fecha_inicio__lte=end_date,
        fecha_fin__gte=start_date,
    ).values(
        'id', 'tarea_id', 'tarea__codigo', 'tarea__nombre',
        'porcentaje_asignacion', 'fecha_inicio', 'fecha_fin',
    )

    if exclude_asignacion_id:
        qs = qs.exclude(id=exclude_asignacion_id)

    assignments = list(qs)
    if not assignments:
        return []

    # Construir mapa fecha → assignments activos ese día
    date_map: dict[date, list[dict]] = {}
    current = start_date
    while current <= end_date:
        date_map[current] = []
        current += timedelta(days=1)

    for a in assignments:
        eff_start = max(a['fecha_inicio'], start_date)
        eff_end   = min(a['fecha_fin'],   end_date)
        current   = eff_start
        while current <= eff_end:
            date_map[current].append(a)
            current += timedelta(days=1)

    conflicts: list[OverallocationConflict] = []
    for fecha, day_assignments in date_map.items():
        if not day_assignments:
            continue
        total = sum(a['porcentaje_asignacion'] for a in day_assignments)
        if total > threshold:
            conflicts.append(
                OverallocationConflict(
                    fecha=fecha,
                    porcentaje_total=total,
                    asignaciones=[
                        {
                            'id':         str(a['id']),
                            'tarea_id':   str(a['tarea_id']),
                            'codigo':     a['tarea__codigo'],
                            'nombre':     a['tarea__nombre'],
                            'porcentaje': str(a['porcentaje_asignacion']),
                        }
                        for a in day_assignments
                    ],
                )
            )

    logger.info(
        'overallocation_check',
        extra={
            'usuario_id':     usuario_id,
            'company_id':     company_id,
            'period_days':    (end_date - start_date).days + 1,
            'assignments':    len(assignments),
            'conflicts':      len(conflicts),
        },
    )

    return sorted(conflicts, key=lambda c: c.fecha)


# ---------------------------------------------------------------------------
# BK-14: calculate_user_workload  (Día 5)
# ---------------------------------------------------------------------------

@dataclass
class UserWorkload:
    usuario_id:            str
    periodo_inicio:        date
    periodo_fin:           date
    horas_capacidad:       Decimal
    horas_asignadas:       Decimal
    horas_registradas:     Decimal
    porcentaje_utilizacion: Decimal
    conflictos:            list[dict] = field(default_factory=list)


def _count_business_days(start: date, end: date) -> int:
    """Cuenta días laborales (L–V) entre dos fechas, ambos extremos incluidos."""
    if start > end:
        return 0
    count = 0
    current = start
    while current <= end:
        if current.weekday() < 5:   # 0=lunes … 4=viernes
            count += 1
        current += timedelta(days=1)
    return count


def calculate_user_workload(
    usuario_id: str,
    company_id: str,
    start_date: date,
    end_date: date,
) -> UserWorkload:
    """
    Calcula la carga de trabajo de un usuario en un período.

    Retorna:
    - horas_capacidad:    horas disponibles según ResourceCapacity
    - horas_asignadas:    calculadas desde ResourceAssignment
                          (porcentaje × horas_dia × días_laborales_solapados)
    - horas_registradas:  suma de TimesheetEntry.horas en el período
    - porcentaje_utilizacion: horas_registradas / horas_capacidad × 100
    - conflictos:         días con sobreasignación >100%
    """
    # --- Query 1: Capacidad del período ---
    capacidades = list(
        ResourceCapacity.objects.filter(
            company_id=company_id,
            usuario_id=usuario_id,
            activo=True,
            fecha_inicio__lte=end_date,
        ).filter(
            Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=start_date)
        ).values('horas_por_semana', 'fecha_inicio', 'fecha_fin')
    )

    horas_capacidad = Decimal('0.00')
    for cap in capacidades:
        cap_start = max(cap['fecha_inicio'], start_date)
        cap_end   = min(cap['fecha_fin'] or end_date, end_date)
        dias_lab  = _count_business_days(cap_start, cap_end)
        # horas = horas/semana × días_laborales / 5 días/semana
        horas_capacidad += cap['horas_por_semana'] * Decimal(dias_lab) / Decimal('5')

    # --- Query 2: Horas asignadas ---
    asignaciones = list(
        ResourceAssignment.objects.filter(
            company_id=company_id,
            usuario_id=usuario_id,
            activo=True,
            fecha_inicio__lte=end_date,
            fecha_fin__gte=start_date,
        ).values('porcentaje_asignacion', 'fecha_inicio', 'fecha_fin')
    )

    total_dias_lab = _count_business_days(start_date, end_date) or 1
    horas_dia = horas_capacidad / Decimal(total_dias_lab) if horas_capacidad else Decimal('0')

    horas_asignadas = Decimal('0.00')
    for a in asignaciones:
        eff_start = max(a['fecha_inicio'], start_date)
        eff_end   = min(a['fecha_fin'],   end_date)
        dias_lab  = _count_business_days(eff_start, eff_end)
        horas_asignadas += (
            a['porcentaje_asignacion'] / Decimal('100') * horas_dia * Decimal(dias_lab)
        )

    # --- Query 3: Horas registradas (agregación directa en BD) ---
    result = TimesheetEntry.objects.filter(
        company_id=company_id,
        usuario_id=usuario_id,
        fecha__gte=start_date,
        fecha__lte=end_date,
    ).aggregate(
        total=Coalesce(Sum('horas'), Decimal('0.00'))
    )
    horas_registradas = result['total']

    porcentaje_utilizacion = (
        (horas_registradas / horas_capacidad * Decimal('100')).quantize(Decimal('0.01'))
        if horas_capacidad > 0
        else Decimal('0.00')
    )

    # Detectar conflictos en el período
    conflictos_raw = detect_overallocation_conflicts(
        usuario_id=usuario_id,
        company_id=company_id,
        start_date=start_date,
        end_date=end_date,
    )
    conflictos = [
        {
            'fecha':            str(c.fecha),
            'porcentaje_total': str(c.porcentaje_total),
        }
        for c in conflictos_raw
    ]

    return UserWorkload(
        usuario_id=usuario_id,
        periodo_inicio=start_date,
        periodo_fin=end_date,
        horas_capacidad=horas_capacidad.quantize(Decimal('0.01')),
        horas_asignadas=horas_asignadas.quantize(Decimal('0.01')),
        horas_registradas=horas_registradas.quantize(Decimal('0.01')),
        porcentaje_utilizacion=porcentaje_utilizacion,
        conflictos=conflictos,
    )


# ---------------------------------------------------------------------------
# BK-15: get_team_availability_timeline  (Día 5)
# ---------------------------------------------------------------------------

@dataclass
class UserTimelineData:
    usuario_id:    str
    usuario_nombre: str
    usuario_email: str
    asignaciones:  list[dict] = field(default_factory=list)
    ausencias:     list[dict] = field(default_factory=list)


def get_team_availability_timeline(
    proyecto_id: str,
    company_id: str,
    start_date: date,
    end_date: date,
) -> list[UserTimelineData]:
    """
    Retorna el timeline de disponibilidad del equipo de un proyecto.

    Estrategia sin N+1:
    1. Una query para user_ids únicos con assignments en el proyecto
    2. Una query prefetch para assignments del período (filtrado)
    3. Una query prefetch para ausencias aprobadas del período (filtrado)
    Total: 3 queries independientemente del tamaño del equipo.

    Args:
        proyecto_id: UUID del proyecto
        company_id: UUID de la empresa (multi-tenant)
        start_date: inicio del período
        end_date: fin del período

    Returns:
        Lista de UserTimelineData, una por miembro del equipo
    """
    from django.contrib.auth import get_user_model
    from django.db.models import Prefetch
    User = get_user_model()

    # Query 1: usuarios únicos con assignments activos en el proyecto
    usuario_ids = list(
        ResourceAssignment.objects.filter(
            company_id=company_id,
            tarea__proyecto_id=proyecto_id,
            activo=True,
            fecha_inicio__lte=end_date,
            fecha_fin__gte=start_date,
        ).values_list('usuario_id', flat=True).distinct()
    )

    if not usuario_ids:
        return []

    # Prefetch assignments del proyecto en el período (Query 2)
    assignments_prefetch = Prefetch(
        'resource_assignments',
        queryset=ResourceAssignment.objects.filter(
            company_id=company_id,
            tarea__proyecto_id=proyecto_id,
            activo=True,
            fecha_inicio__lte=end_date,
            fecha_fin__gte=start_date,
        ).select_related('tarea').order_by('fecha_inicio'),
        to_attr='project_assignments',
    )

    # Prefetch ausencias aprobadas del período (Query 3)
    availabilities_prefetch = Prefetch(
        'resource_availabilities',
        queryset=ResourceAvailability.objects.filter(
            company_id=company_id,
            aprobado=True,
            activo=True,
            fecha_inicio__lte=end_date,
            fecha_fin__gte=start_date,
        ).order_by('fecha_inicio'),
        to_attr='period_availabilities',
    )

    usuarios = (
        User.objects.filter(
            id__in=usuario_ids,
            company_id=company_id,
        )
        .prefetch_related(assignments_prefetch, availabilities_prefetch)
        .order_by('last_name', 'first_name')
    )

    result: list[UserTimelineData] = []
    for usuario in usuarios:
        result.append(
            UserTimelineData(
                usuario_id=str(usuario.id),
                usuario_nombre=usuario.full_name or usuario.email,
                usuario_email=usuario.email,
                asignaciones=[
                    {
                        'id':                   str(a.id),
                        'tarea_id':             str(a.tarea_id),
                        'tarea_codigo':         a.tarea.codigo,
                        'tarea_nombre':         a.tarea.nombre,
                        'porcentaje_asignacion': str(a.porcentaje_asignacion),
                        'fecha_inicio':         str(a.fecha_inicio),
                        'fecha_fin':            str(a.fecha_fin),
                    }
                    for a in usuario.project_assignments
                ],
                ausencias=[
                    {
                        'id':          str(av.id),
                        'tipo':        av.tipo,
                        'tipo_display': av.get_tipo_display(),
                        'fecha_inicio': str(av.fecha_inicio),
                        'fecha_fin':    str(av.fecha_fin),
                        'descripcion':  av.descripcion,
                    }
                    for av in usuario.period_availabilities
                ],
            )
        )

    return result


# ---------------------------------------------------------------------------
# BK-16: set_user_capacity  (Día 4)
# ---------------------------------------------------------------------------

@transaction.atomic
def set_user_capacity(
    usuario_id: str,
    company_id: str,
    horas_por_semana: Decimal,
    fecha_inicio: date,
    fecha_fin: Optional[date] = None,
    capacity_id: Optional[str] = None,
) -> ResourceCapacity:
    """
    Crea o actualiza la capacidad laboral de un usuario para un período.

    Valida que no haya solapamiento con otras capacidades del mismo usuario
    (excepto la que se está editando, si capacity_id está presente).

    Args:
        usuario_id: UUID del usuario
        company_id: UUID de la empresa
        horas_por_semana: horas laborales por semana (0.01–168)
        fecha_inicio: inicio del período de capacidad
        fecha_fin: fin del período (None = indefinido)
        capacity_id: si se provee, actualiza el registro existente

    Returns:
        ResourceCapacity creada o actualizada

    Raises:
        ValidationError: si hay solapamiento con otra capacidad o datos inválidos
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # Validar que el usuario existe en la empresa
    try:
        usuario = User.objects.get(id=usuario_id, company_id=company_id)
    except User.DoesNotExist:
        raise ValidationError({
            'usuario_id': 'El usuario no existe o no pertenece a esta empresa.'
        })

    # Validar fechas
    if fecha_fin and fecha_fin <= fecha_inicio:
        raise ValidationError({
            'fecha_fin': 'La fecha de fin debe ser posterior a la fecha de inicio.'
        })

    # Verificar solapamiento con otras capacidades del mismo usuario
    overlap_qs = ResourceCapacity.objects.filter(
        company_id=company_id,
        usuario=usuario,
        activo=True,
        fecha_inicio__lte=fecha_fin or date(9999, 12, 31),
    ).filter(
        Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fecha_inicio)
    )
    if capacity_id:
        overlap_qs = overlap_qs.exclude(id=capacity_id)

    if overlap_qs.exists():
        raise ValidationError({
            'fecha_inicio': (
                'Ya existe un período de capacidad que se solapa con las fechas indicadas. '
                'Ajusta las fechas o desactiva el período existente primero.'
            )
        })

    if capacity_id:
        # Actualizar registro existente
        capacidad = ResourceCapacity.objects.get(
            id=capacity_id, company_id=company_id, usuario=usuario
        )
        capacidad.horas_por_semana = horas_por_semana
        capacidad.fecha_inicio     = fecha_inicio
        capacidad.fecha_fin        = fecha_fin
        capacidad.save(update_fields=[
            'horas_por_semana', 'fecha_inicio', 'fecha_fin', 'updated_at'
        ])
    else:
        capacidad = ResourceCapacity.objects.create(
            company_id=company_id,
            usuario=usuario,
            horas_por_semana=horas_por_semana,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            activo=True,
        )

    logger.info(
        'capacidad_usuario_actualizada',
        extra={
            'capacity_id':      str(capacidad.id),
            'usuario_id':       usuario_id,
            'horas_por_semana': str(horas_por_semana),
            'fecha_inicio':     str(fecha_inicio),
            'fecha_fin':        str(fecha_fin) if fecha_fin else 'indefinido',
            'company_id':       company_id,
        },
    )

    return capacidad


# ---------------------------------------------------------------------------
# BK-17: register_availability  (Día 4)
# ---------------------------------------------------------------------------

@transaction.atomic
def register_availability(
    usuario_id: str,
    company_id: str,
    tipo: str,
    fecha_inicio: date,
    fecha_fin: date,
    descripcion: str = '',
) -> ResourceAvailability:
    """
    Registra una ausencia de un usuario.

    Valida que no haya solapamiento con otra ausencia del MISMO tipo.
    Ausencias de distintos tipos en las mismas fechas sí son válidas
    (ej: festivo + capacitación el mismo día).

    La ausencia se crea con aprobado=False; aprobación es un paso separado
    vía approve_availability().

    Args:
        usuario_id: UUID del usuario
        company_id: UUID de la empresa
        tipo: valor de AvailabilityType (vacation, sick_leave, holiday, etc.)
        fecha_inicio: inicio de la ausencia
        fecha_fin: fin de la ausencia
        descripcion: texto libre opcional

    Returns:
        ResourceAvailability creada

    Raises:
        ValidationError: si hay solapamiento del mismo tipo o datos inválidos
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # Validar tipo
    tipos_validos = [c[0] for c in AvailabilityType.choices]
    if tipo not in tipos_validos:
        raise ValidationError({
            'tipo': f'Tipo inválido. Valores permitidos: {tipos_validos}'
        })

    # Validar usuario
    try:
        usuario = User.objects.get(id=usuario_id, company_id=company_id)
    except User.DoesNotExist:
        raise ValidationError({
            'usuario_id': 'El usuario no existe o no pertenece a esta empresa.'
        })

    # Validar fechas
    if fecha_fin < fecha_inicio:
        raise ValidationError({
            'fecha_fin': 'La fecha de fin debe ser igual o posterior a la fecha de inicio.'
        })

    # Verificar solapamiento del mismo tipo para el mismo usuario
    solapamiento = ResourceAvailability.objects.filter(
        company_id=company_id,
        usuario=usuario,
        tipo=tipo,
        activo=True,
        fecha_inicio__lte=fecha_fin,
        fecha_fin__gte=fecha_inicio,
    ).exists()

    if solapamiento:
        raise ValidationError({
            'fecha_inicio': (
                f'Ya existe una ausencia de tipo "{tipo}" que se solapa con las '
                f'fechas indicadas ({fecha_inicio} – {fecha_fin}).'
            )
        })

    ausencia = ResourceAvailability.objects.create(
        company_id=company_id,
        usuario=usuario,
        tipo=tipo,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        descripcion=descripcion,
        aprobado=False,
        activo=True,
    )

    logger.info(
        'ausencia_registrada',
        extra={
            'ausencia_id':  str(ausencia.id),
            'usuario_id':   usuario_id,
            'tipo':         tipo,
            'fecha_inicio': str(fecha_inicio),
            'fecha_fin':    str(fecha_fin),
            'company_id':   company_id,
        },
    )

    return ausencia


# ---------------------------------------------------------------------------
# BK-18: approve_availability  (Día 4)
# ---------------------------------------------------------------------------

@transaction.atomic
def approve_availability(
    ausencia_id: str,
    company_id: str,
    aprobador_id: str,
    aprobar: bool = True,
) -> ResourceAvailability:
    """
    Aprueba o rechaza una ausencia de usuario.

    Solo ausencias con aprobado=True se descuentan de la capacidad efectiva
    en calculate_user_workload().

    Args:
        ausencia_id: UUID de la ResourceAvailability
        company_id: UUID de la empresa
        aprobador_id: UUID del usuario que aprueba/rechaza
        aprobar: True para aprobar, False para rechazar (aprobado=False)

    Returns:
        ResourceAvailability actualizada

    Raises:
        ValidationError: si la ausencia no existe o ya fue procesada
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    try:
        ausencia = ResourceAvailability.objects.get(
            id=ausencia_id, company_id=company_id, activo=True
        )
    except ResourceAvailability.DoesNotExist:
        raise ValidationError({
            'ausencia_id': 'La ausencia no existe o no pertenece a esta empresa.'
        })

    try:
        aprobador = User.objects.get(id=aprobador_id, company_id=company_id)
    except User.DoesNotExist:
        raise ValidationError({
            'aprobador_id': 'El aprobador no existe o no pertenece a esta empresa.'
        })

    ausencia.aprobado         = aprobar
    ausencia.aprobado_por     = aprobador if aprobar else None
    ausencia.fecha_aprobacion = timezone.now() if aprobar else None
    ausencia.save(update_fields=[
        'aprobado', 'aprobado_por', 'fecha_aprobacion', 'updated_at'
    ])

    accion = 'aprobada' if aprobar else 'rechazada'
    logger.info(
        f'ausencia_{accion}',
        extra={
            'ausencia_id':  str(ausencia.id),
            'usuario_id':   str(ausencia.usuario_id),
            'aprobador_id': aprobador_id,
            'company_id':   company_id,
        },
    )

    return ausencia
