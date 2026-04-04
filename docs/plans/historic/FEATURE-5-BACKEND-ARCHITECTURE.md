# Feature #5: Reporting & Analytics — Backend Architecture
# SaiSuite | apps/proyectos | Django 5 + DRF + PostgreSQL 16
# Autor: Backend Architect | Fecha: 2026-03-27

---

## Indice

1. Analisis de Modelos Existentes para Metricas
2. Decision: Nuevos Modelos Necesarios
3. Diseno de Services (firmas exactas)
4. Endpoints REST
5. Estrategia de Caching
6. Exportacion PDF/Excel
7. Indices de Base de Datos
8. Estructura de Archivos Backend

---

## 1. Analisis de Modelos Existentes para Metricas

### Mapa de Datos Disponibles

Antes de disenar los services, se mapean los campos reales que existen en la BD
tras el refactor REFT-01 a REFT-21 (rama `refactor/english-rename`, commit c2947be).

| Modelo | Campos Clave para Analytics |
|---|---|
| `Project` | `estado`, `presupuesto_total`, `porcentaje_avance`, `fecha_inicio_planificada`, `fecha_fin_planificada`, `fecha_inicio_real`, `fecha_fin_real`, `tipo`, `company_id` |
| `Phase` | `proyecto_id`, `estado`, `orden`, `porcentaje_avance`, `fecha_inicio_planificada`, `fecha_fin_planificada` |
| `Task` | `proyecto_id`, `fase_id`, `estado`, `horas_estimadas`, `horas_registradas`, `fecha_limite`, `prioridad`, `responsable_id`, `porcentaje_completado`, `company_id` |
| `TimesheetEntry` | `tarea_id`, `usuario_id`, `fecha`, `horas`, `validado`, `company_id` |
| `ResourceAssignment` | `tarea_id`, `usuario_id`, `porcentaje_asignacion`, `fecha_inicio`, `fecha_fin`, `activo`, `company_id` |
| `ResourceCapacity` | `usuario_id`, `horas_por_semana`, `fecha_inicio`, `fecha_fin`, `activo`, `company_id` |

**Nota critica sobre Task:** El campo `fecha_limite` es el deadline real de la tarea (no `fecha_fin`).
`fecha_fin` puede ser nulo. Para On-Time Rate se usa `fecha_limite`.

---

### 1.1 Completion Rate

**Definicion:** % de tareas con estado `completed` sobre el total de tareas activas del proyecto.

```
completion_rate = (tareas_completed / total_tareas) * 100
```

**Modelos:** `Task` unicamente.

**Campos:** `Task.proyecto_id`, `Task.estado`, `Task.company_id`.

**Requiere JOIN/prefetch:** No. Agregacion directa sobre `Task`.

**Calculo en DB o Python:** 100% en DB con `annotate` + `Count` + filtro condicional.

```sql
-- Query equivalente (Django ORM annotate)
SELECT
    COUNT(*) FILTER (WHERE estado = 'completed') AS completed,
    COUNT(*) AS total
FROM proyectos_task
WHERE proyecto_id = %s
  AND company_id = %s;
```

**Complejidad:** Baja. Una sola query con agregacion. Indice existente `idx_task_project_estado`
(`proyecto`, `estado`) en `Task.Meta.indexes` lo cubre completamente.

---

### 1.2 On-Time Rate

**Definicion:** % de tareas completadas cuya fecha de completion fue antes o igual a `fecha_limite`.

**Problema real:** La BD no almacena `fecha_completion` (cuando la tarea cambio a `completed`).
Solo existe `updated_at` en `BaseModel`, que se actualiza en cualquier cambio.

**Decision de diseno:** Para MVP, On-Time Rate = tareas `completed` donde `fecha_limite IS NOT NULL`
y `fecha_limite >= hoy` (las que ya estan completadas y su deadline no ha vencido, o sea que se
completaron a tiempo). Las tareas sin `fecha_limite` se excluyen del calculo.

Esta es una aproximacion valida para MVP. Si se requiere exactitud completa, seria necesario
agregar un campo `fecha_completion: DateField(null=True)` en `Task` (ver Seccion 2).

**Modelos:** `Task`.

**Campos:** `Task.estado`, `Task.fecha_limite`, `Task.proyecto_id`.

**Calculo en DB:** Con `annotate` y `Count` condicional.

```sql
SELECT
    COUNT(*) FILTER (
        WHERE estado = 'completed'
          AND fecha_limite IS NOT NULL
          AND fecha_limite >= updated_at::date
    ) AS on_time,
    COUNT(*) FILTER (
        WHERE fecha_limite IS NOT NULL
          AND estado IN ('completed', 'cancelled')
    ) AS total_con_deadline
FROM proyectos_task
WHERE proyecto_id = %s
  AND company_id = %s;
```

**Complejidad:** Baja-media. Una query. La aproximacion via `updated_at` introduce ruido
(si la tarea se edita despues de completarse, `updated_at` cambia). Recomendado agregar
`fecha_completion` en Fase 2.

---

### 1.3 Budget Variance (Varianza de Presupuesto en Horas)

**Definicion:** Diferencia porcentual entre horas estimadas y horas registradas.

```
budget_variance = ((horas_registradas - horas_estimadas) / horas_estimadas) * 100
```

Positivo = sobre presupuesto. Negativo = bajo presupuesto.

**Modelos:** `Task` (horas_estimadas, horas_registradas ya estan desnormalizadas en Task).

**Campos:** `Task.horas_estimadas`, `Task.horas_registradas`, `Task.proyecto_id`.

**Calculo en DB:** Agregacion con `Sum`. No requiere JOIN.

```sql
SELECT
    SUM(horas_estimadas) AS total_estimadas,
    SUM(horas_registradas) AS total_registradas
FROM proyectos_task
WHERE proyecto_id = %s
  AND company_id = %s
  AND horas_estimadas > 0;
```

**Complejidad:** Baja. Una query, sin JOINs. `horas_registradas` en `Task` ya se actualiza
via signal cuando se crea un `TimesheetEntry` (verificar en `tarea_services.py`).

---

### 1.4 Velocity

**Definicion:** Tareas completadas por semana, promedio de las ultimas N semanas (default 8).

**Modelos:** `Task` + `updated_at` de `BaseModel` (como proxy de fecha_completion).

**Campos:** `Task.estado`, `Task.updated_at`, `Task.proyecto_id`.

**Calculo:** Requiere truncar `updated_at` a semana ISO (`date_trunc('week', updated_at)`).
Calculo en DB con `GROUP BY` semanal.

```sql
SELECT
    date_trunc('week', updated_at) AS semana,
    COUNT(*) AS tareas_completadas
FROM proyectos_task
WHERE proyecto_id = %s
  AND company_id = %s
  AND estado = 'completed'
  AND updated_at >= NOW() - INTERVAL '8 weeks'
GROUP BY semana
ORDER BY semana;
```

**Complejidad:** Media. Necesita `TruncWeek` de Django o SQL nativo. La precision depende
de `updated_at` como proxy de fecha_completion.

**Requiere JOIN:** No.

---

### 1.5 Burn Rate

**Definicion:** Horas registradas por semana, promedio de las ultimas N semanas.

**Modelos:** `TimesheetEntry`. Es mas preciso que usar `Task.horas_registradas`
porque `TimesheetEntry.fecha` es la fecha real del trabajo.

**Campos:** `TimesheetEntry.fecha`, `TimesheetEntry.horas`, `TimesheetEntry.tarea_id`.

**Requiere JOIN:** Si. `TimesheetEntry -> Task` para filtrar por proyecto.

```sql
SELECT
    date_trunc('week', te.fecha) AS semana,
    SUM(te.horas) AS horas_registradas
FROM timesheet_entries te
INNER JOIN proyectos_task t ON t.id = te.tarea_id
WHERE t.proyecto_id = %s
  AND te.company_id = %s
  AND te.fecha >= NOW() - INTERVAL '8 weeks'
GROUP BY semana
ORDER BY semana;
```

**Complejidad:** Media. Un JOIN simple. Indice `(usuario, fecha)` en `TimesheetEntry`
existe, pero se necesita indice en `(tarea_id, fecha)` para esta query (ver Seccion 7).

---

### 1.6 Burn Down

**Definicion:** Horas estimadas restantes vs tiempo. Muestra la tendencia de completitud.

```
horas_restantes(t) = total_horas_estimadas - horas_registradas_acumuladas_hasta(t)
```

**Modelos:** `Task` (horas_estimadas por proyecto) + `TimesheetEntry` (horas por fecha).

**Campos:** `Task.horas_estimadas`, `TimesheetEntry.fecha`, `TimesheetEntry.horas`.

**Requiere JOIN:** Si. `TimesheetEntry -> Task -> Project`.

**Calculo:** Acumulativo. Se calcula la suma corrida de horas registradas por semana
y se resta del total de horas estimadas.

```sql
-- Paso 1: Total horas estimadas del proyecto
SELECT SUM(horas_estimadas) AS total_estimadas
FROM proyectos_task
WHERE proyecto_id = %s AND company_id = %s;

-- Paso 2: Horas registradas acumuladas por semana
SELECT
    date_trunc('week', te.fecha) AS semana,
    SUM(te.horas) OVER (
        ORDER BY date_trunc('week', te.fecha)
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS horas_acumuladas
FROM timesheet_entries te
INNER JOIN proyectos_task t ON t.id = te.tarea_id
WHERE t.proyecto_id = %s AND te.company_id = %s
GROUP BY semana
ORDER BY semana;
```

**Complejidad:** Alta. Requiere window functions (Django ORM no las soporta nativamente;
usar `RawSQL` o `Window` de Django 3.2+). En Python se puede calcular la suma corrida
con O(n) sobre el resultado de la query agregada.

**Recomendacion MVP:** Calcular en Python. Hacer la query de horas por semana (simple),
luego acumular con `itertools.accumulate` en el service.

---

### 1.7 Resource Utilization

**Definicion:** % de uso de la capacidad por usuario en un proyecto durante un periodo.

```
utilizacion = (horas_registradas / horas_capacidad) * 100
```

**Modelos:** `TimesheetEntry` + `ResourceCapacity` + `ResourceAssignment`.

**Campos:**
- `TimesheetEntry.horas`, `TimesheetEntry.usuario_id`, `TimesheetEntry.fecha`
- `ResourceCapacity.horas_por_semana`, `ResourceCapacity.usuario_id`
- `ResourceAssignment.usuario_id`, `ResourceAssignment.tarea_id`

**Requiere JOIN:** Si. Multiplos. La logica ya existe en `resource_services.calculate_user_workload()`.
El service de analytics la reutilizara directamente.

**Complejidad:** Alta. Pero `calculate_user_workload()` ya esta implementado y probado.
El analytics service simplemente lo llama para cada usuario del proyecto.

---

### 1.8 Task Distribution

**Definicion:** Conteo de tareas por estado en el proyecto.

**Modelos:** `Task` unicamente.

**Campos:** `Task.estado`, `Task.proyecto_id`.

**Calculo en DB:** Un `GROUP BY estado` con `Count`.

```sql
SELECT estado, COUNT(*) AS cantidad
FROM proyectos_task
WHERE proyecto_id = %s AND company_id = %s
GROUP BY estado;
```

**Complejidad:** Muy baja. Una query, sin JOINs. Indice existente `(proyecto, estado)` la cubre.

---

## 2. Decision: Nuevos Modelos Necesarios

### 2.1 DashboardConfig — Configuraciones Personalizadas

**Evaluacion:**
- Permite que cada usuario guarde que metricas ver, orden de widgets, filtros preferidos.
- Requiere un modelo nuevo, migracion, serializer, views CRUD.
- Complejidad de desarrollo: media (2-3 dias adicionales).
- Valor en MVP: bajo. El dashboard inicial puede tener una configuracion fija.

**Decision: NO para MVP.**

Razon: Un solo desarrollador. La configuracion fija reduce la superficie de codigo a mantener
y el tiempo de entrega. Se puede agregar en Feature #6 si hay demanda real.

### 2.2 MetricSnapshot — Cache de Metricas Pre-calculadas

**Evaluacion:**
- Guarda resultados de metricas con timestamp para evitar recalcular en cada request.
- Alternativa al cache en memoria/Redis.
- Requiere: modelo, migracion, tarea Celery de actualizacion periodica.
- Complejidad: alta (modelo + tarea periodica + logica de invalidacion).
- Ventaja sobre cache: persiste entre reinicios del servidor.

**Decision: NO para MVP.**

Razon: Para el volumen esperado en MVP (empresas con <50 proyectos, <500 tareas cada una),
las queries de analytics son suficientemente rapidas con indices correctos y cache en memoria
con TTL corto. Un `MetricSnapshot` agrega complejidad de sincronizacion innecesaria.

Si en produccion las queries superan 2 segundos para proyectos grandes, se implementara
entonces (con datos reales para justificarlo).

### 2.3 Task.fecha_completion — Campo de Precision para On-Time Rate

**Evaluacion:**
- Agrega `fecha_completion: DateField(null=True)` a `Task`.
- Se setea automaticamente via signal cuando `estado` cambia a `completed`.
- Resuelve la imprecision de usar `updated_at` como proxy.
- Complejidad: baja (1 campo, 1 migration, 1 signal).

**Decision: SI, pero como mejora incremental en la primera iteracion de Fase 5.**

Razon: El costo es minimo y la precision del On-Time Rate mejora significativamente.
Se agrega junto con las migrations de analytics_services. Los registros historicos
tendran `fecha_completion=NULL`; el service los excluye del calculo.

**Migration necesaria:**
```python
# En la primera iteracion de Fase 5
migrations.AddField(
    model_name='task',
    name='fecha_completion',
    field=models.DateField(null=True, blank=True),
)
```

**Signal adicional en `models.py`:**
```python
# En apps/proyectos/signals.py (o al final de models.py)
@receiver(pre_save, sender=Task)
def set_fecha_completion(sender, instance, **kwargs):
    if instance.pk:
        try:
            anterior = Task.objects.get(pk=instance.pk)
            if anterior.estado != 'completed' and instance.estado == 'completed':
                instance.fecha_completion = date.today()
            elif anterior.estado == 'completed' and instance.estado != 'completed':
                instance.fecha_completion = None
        except Task.DoesNotExist:
            pass
```

---

## 3. Diseno de Services

Todos los services van en el nuevo archivo `analytics_services.py`.
Siguen el patron del proyecto: logica de negocio completa, sin logica en views.

### Convenciones del modulo

```python
# analytics_services.py — encabezado obligatorio
"""
SaiSuite — Proyectos: AnalyticsService
TODA la logica de analytics va aqui.
Las views solo orquestan: reciben request -> llaman service -> retornan response.
"""
import logging
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID
from itertools import accumulate

from django.core.cache import cache
from django.db.models import Count, Sum, Q, F, Case, When, Value, IntegerField
from django.db.models.functions import TruncWeek, TruncDate, Coalesce

from apps.proyectos.models import Project, Phase, Task, TimesheetEntry, ResourceAssignment, ResourceCapacity
from apps.proyectos.resource_services import calculate_user_workload

logger = logging.getLogger(__name__)
```

---

### 3.1 get_project_kpis

```python
def get_project_kpis(project_id: UUID, company_id: UUID) -> dict:
    """
    Retorna los KPIs principales de un proyecto en una sola llamada.

    Inputs:
        project_id: UUID del proyecto
        company_id: UUID de la empresa (multi-tenant)

    Outputs: {
        'completion_rate': float,      # 0-100, % tareas completadas
        'on_time_rate': float,         # 0-100, % completadas a tiempo (requiere fecha_completion)
        'budget_variance': float,      # %; positivo = sobre presupuesto, negativo = bajo
        'total_tasks': int,
        'completed_tasks': int,
        'blocked_tasks': int,
        'overdue_tasks': int,          # tareas con fecha_limite vencida y no completadas
        'total_horas_estimadas': str,  # Decimal como string para serializer
        'total_horas_registradas': str,
        'porcentaje_avance': str,      # del Project.porcentaje_avance
    }

    Queries involucradas:
        Q1: Task aggregate — Count por estado + Sum horas (1 query)
        Q2: Project.porcentaje_avance (select_related o .values)

    Total: 2 queries.

    Caching: TTL 5 minutos. Cache key: f'kpis:{company_id}:{project_id}'
    Invalidacion: cuando se crea/modifica Task o TimesheetEntry del proyecto.
    """
    cache_key = f'analytics:kpis:{company_id}:{project_id}'
    cached = cache.get(cache_key)
    if cached:
        logger.info(
            'kpis_cache_hit',
            extra={'project_id': str(project_id), 'company_id': str(company_id)},
        )
        return cached

    today = date.today()

    # Q1: Agregacion de tareas
    agg = Task.objects.filter(
        proyecto_id=project_id,
        company_id=company_id,
    ).aggregate(
        total=Count('id'),
        completed=Count('id', filter=Q(estado='completed')),
        blocked=Count('id', filter=Q(estado='blocked')),
        on_time=Count(
            'id',
            filter=Q(
                estado='completed',
                fecha_completion__isnull=False,
                fecha_limite__isnull=False,
                fecha_completion__lte=F('fecha_limite'),
            ),
        ),
        with_deadline_completed=Count(
            'id',
            filter=Q(
                estado='completed',
                fecha_completion__isnull=False,
                fecha_limite__isnull=False,
            ),
        ),
        overdue=Count(
            'id',
            filter=Q(
                fecha_limite__lt=today,
                estado__in=['todo', 'in_progress', 'in_review', 'blocked'],
            ),
        ),
        sum_estimadas=Coalesce(Sum('horas_estimadas'), Decimal('0.00')),
        sum_registradas=Coalesce(Sum('horas_registradas'), Decimal('0.00')),
    )

    # Q2: Datos del proyecto
    proyecto = Project.objects.filter(
        id=project_id, company_id=company_id
    ).values('porcentaje_avance').first()

    total = agg['total'] or 0
    completed = agg['completed'] or 0
    completion_rate = round((completed / total * 100), 2) if total > 0 else 0.0

    on_time = agg['on_time'] or 0
    with_deadline = agg['with_deadline_completed'] or 0
    on_time_rate = round((on_time / with_deadline * 100), 2) if with_deadline > 0 else None

    estimadas = agg['sum_estimadas']
    registradas = agg['sum_registradas']
    if estimadas and estimadas > 0:
        budget_variance = round(float((registradas - estimadas) / estimadas * 100), 2)
    else:
        budget_variance = None

    result = {
        'completion_rate': completion_rate,
        'on_time_rate': on_time_rate,
        'budget_variance': budget_variance,
        'total_tasks': total,
        'completed_tasks': completed,
        'blocked_tasks': agg['blocked'] or 0,
        'overdue_tasks': agg['overdue'] or 0,
        'total_horas_estimadas': str(estimadas),
        'total_horas_registradas': str(registradas),
        'porcentaje_avance': str(proyecto['porcentaje_avance']) if proyecto else '0',
    }

    cache.set(cache_key, result, timeout=300)  # 5 minutos

    logger.info(
        'kpis_calculados',
        extra={
            'project_id': str(project_id),
            'company_id': str(company_id),
            'total_tasks': total,
            'completion_rate': completion_rate,
        },
    )
    return result
```

---

### 3.2 get_burn_down_data

```python
def get_burn_down_data(
    project_id: UUID,
    company_id: UUID,
    granularity: str = 'week',  # 'week' o 'day'
) -> list[dict]:
    """
    Datos para el grafico de Burn Down del proyecto.

    Retorna la evolucion de horas restantes a lo largo del tiempo.
    La linea ideal se calcula linealmente desde el inicio hasta el fin planificado.

    Inputs:
        project_id: UUID del proyecto
        company_id: UUID de la empresa
        granularity: 'week' (default para proyectos largos) | 'day' (proyectos cortos)

    Outputs: list de {
        'periodo': str,                 # ISO date del inicio del periodo
        'horas_restantes': str,         # Decimal
        'horas_registradas_periodo': str,
        'horas_acumuladas': str,
        'ideal': str,                   # horas que deberian quedar segun plan
    }

    Queries involucradas:
        Q1: Project (fechas, horas estimadas totales)
        Q2: Task.sum(horas_estimadas) del proyecto
        Q3: TimesheetEntry GROUP BY semana/dia con JOIN a Task

    Total: 3 queries + calculo Python O(n) para suma corrida e ideal.

    Caching: TTL 10 minutos. Cache key: f'burndown:{company_id}:{project_id}:{granularity}'
    Invalidacion: cuando se registra un TimesheetEntry en el proyecto.
    """
    cache_key = f'analytics:burndown:{company_id}:{project_id}:{granularity}'
    cached = cache.get(cache_key)
    if cached:
        return cached

    # Q1: Proyecto
    proyecto = Project.objects.filter(
        id=project_id, company_id=company_id
    ).values(
        'fecha_inicio_planificada', 'fecha_fin_planificada',
        'fecha_inicio_real',
    ).first()

    if not proyecto:
        return []

    # Q2: Total horas estimadas
    total_estimadas = Task.objects.filter(
        proyecto_id=project_id, company_id=company_id,
    ).aggregate(
        total=Coalesce(Sum('horas_estimadas'), Decimal('0.00'))
    )['total']

    if total_estimadas == 0:
        return []

    # Q3: Horas registradas por periodo
    trunc_fn = TruncWeek if granularity == 'week' else TruncDate
    entries = (
        TimesheetEntry.objects.filter(
            company_id=company_id,
            tarea__proyecto_id=project_id,
        )
        .annotate(periodo=trunc_fn('fecha'))
        .values('periodo')
        .annotate(horas_periodo=Sum('horas'))
        .order_by('periodo')
    )

    # Calculo en Python: suma corrida y linea ideal
    fecha_inicio = proyecto['fecha_inicio_real'] or proyecto['fecha_inicio_planificada']
    fecha_fin = proyecto['fecha_fin_planificada']
    dias_totales = (fecha_fin - fecha_inicio).days or 1

    result = []
    acumulado = Decimal('0.00')

    for entry in entries:
        acumulado += entry['horas_periodo']
        restantes = max(total_estimadas - acumulado, Decimal('0.00'))
        dias_transcurridos = (entry['periodo'].date() - fecha_inicio).days
        ideal = max(
            total_estimadas - (total_estimadas * Decimal(dias_transcurridos) / Decimal(dias_totales)),
            Decimal('0.00'),
        )
        result.append({
            'periodo':                    entry['periodo'].date().isoformat(),
            'horas_restantes':            str(restantes.quantize(Decimal('0.01'))),
            'horas_registradas_periodo':  str(entry['horas_periodo'].quantize(Decimal('0.01'))),
            'horas_acumuladas':           str(acumulado.quantize(Decimal('0.01'))),
            'ideal':                      str(ideal.quantize(Decimal('0.01'))),
        })

    cache.set(cache_key, result, timeout=600)  # 10 minutos

    logger.info(
        'burndown_calculado',
        extra={
            'project_id':    str(project_id),
            'company_id':    str(company_id),
            'granularity':   granularity,
            'periodos':      len(result),
            'total_estimadas': str(total_estimadas),
        },
    )
    return result
```

---

### 3.3 get_velocity_data

```python
def get_velocity_data(
    project_id: UUID,
    company_id: UUID,
    periods: int = 8,
) -> list[dict]:
    """
    Velocidad del equipo: tareas completadas por semana.

    Inputs:
        project_id: UUID del proyecto
        company_id: UUID de la empresa
        periods: numero de semanas a mostrar (default 8)

    Outputs: list de {
        'semana': str,           # ISO date del lunes de la semana
        'tareas_completadas': int,
        'promedio_acumulado': float,  # promedio movil hasta esa semana
    }

    Queries involucradas:
        Q1: Task GROUP BY TruncWeek(fecha_completion) — 1 query con filtro de fechas

    Total: 1 query + calculo Python para promedio movil.

    Caching: TTL 10 minutos.
    """
    cache_key = f'analytics:velocity:{company_id}:{project_id}:{periods}'
    cached = cache.get(cache_key)
    if cached:
        return cached

    cutoff = date.today() - timedelta(weeks=periods)

    qs = (
        Task.objects.filter(
            proyecto_id=project_id,
            company_id=company_id,
            estado='completed',
            fecha_completion__isnull=False,
            fecha_completion__gte=cutoff,
        )
        .annotate(semana=TruncWeek('fecha_completion'))
        .values('semana')
        .annotate(completadas=Count('id'))
        .order_by('semana')
    )

    result = []
    totales = []
    for entry in qs:
        totales.append(entry['completadas'])
        promedio = round(sum(totales) / len(totales), 2)
        result.append({
            'semana':               entry['semana'].date().isoformat(),
            'tareas_completadas':   entry['completadas'],
            'promedio_acumulado':   promedio,
        })

    cache.set(cache_key, result, timeout=600)

    logger.info(
        'velocity_calculado',
        extra={
            'project_id': str(project_id),
            'company_id': str(company_id),
            'periods':    periods,
            'semanas_con_datos': len(result),
        },
    )
    return result
```

---

### 3.4 get_task_distribution

```python
def get_task_distribution(project_id: UUID, company_id: UUID) -> dict:
    """
    Distribucion de tareas por estado y por prioridad.

    Inputs:
        project_id: UUID del proyecto
        company_id: UUID de la empresa

    Outputs: {
        'por_estado': {
            'todo': int,
            'in_progress': int,
            'in_review': int,
            'blocked': int,
            'completed': int,
            'cancelled': int,
        },
        'por_prioridad': {
            '1': int,  # Baja
            '2': int,  # Normal
            '3': int,  # Alta
            '4': int,  # Urgente
        },
        'por_fase': list de {
            'fase_id': str,
            'fase_nombre': str,
            'total': int,
            'completadas': int,
        },
    }

    Queries involucradas:
        Q1: Task GROUP BY estado (1 query)
        Q2: Task GROUP BY prioridad (1 query)
        Q3: Task JOIN Phase GROUP BY fase (1 query con select_related)

    Total: 3 queries ligeras.

    Caching: TTL 5 minutos.
    """
    cache_key = f'analytics:distribution:{company_id}:{project_id}'
    cached = cache.get(cache_key)
    if cached:
        return cached

    estados_qs = (
        Task.objects.filter(proyecto_id=project_id, company_id=company_id)
        .values('estado')
        .annotate(cantidad=Count('id'))
    )
    por_estado = {
        e: 0 for e in ['todo', 'in_progress', 'in_review', 'blocked', 'completed', 'cancelled']
    }
    for row in estados_qs:
        por_estado[row['estado']] = row['cantidad']

    prioridad_qs = (
        Task.objects.filter(proyecto_id=project_id, company_id=company_id)
        .values('prioridad')
        .annotate(cantidad=Count('id'))
    )
    por_prioridad = {str(i): 0 for i in [1, 2, 3, 4]}
    for row in prioridad_qs:
        por_prioridad[str(row['prioridad'])] = row['cantidad']

    fase_qs = (
        Task.objects.filter(proyecto_id=project_id, company_id=company_id)
        .values('fase_id', 'fase__nombre')
        .annotate(
            total=Count('id'),
            completadas=Count('id', filter=Q(estado='completed')),
        )
        .order_by('fase__orden')
    )
    por_fase = [
        {
            'fase_id':    str(row['fase_id']),
            'fase_nombre': row['fase__nombre'],
            'total':      row['total'],
            'completadas': row['completadas'],
        }
        for row in fase_qs
    ]

    result = {
        'por_estado': por_estado,
        'por_prioridad': por_prioridad,
        'por_fase': por_fase,
    }

    cache.set(cache_key, result, timeout=300)

    logger.info(
        'distribution_calculada',
        extra={'project_id': str(project_id), 'company_id': str(company_id)},
    )
    return result
```

---

### 3.5 get_resource_utilization

```python
def get_resource_utilization(
    project_id: UUID,
    company_id: UUID,
    start_date: date,
    end_date: date,
) -> list[dict]:
    """
    Utilizacion de recursos (usuarios) en el proyecto durante un periodo.

    Reutiliza calculate_user_workload() de resource_services para cada usuario
    del proyecto. Estrategia sin N+1: 1 query para usuarios, luego N queries
    para workload (donde N = usuarios del equipo, tipicamente < 20).

    Inputs:
        project_id: UUID del proyecto
        company_id: UUID de la empresa
        start_date: inicio del periodo
        end_date: fin del periodo

    Outputs: list de {
        'usuario_id': str,
        'usuario_nombre': str,
        'horas_capacidad': str,
        'horas_asignadas': str,
        'horas_registradas': str,
        'porcentaje_utilizacion': str,
        'conflictos': int,             # cantidad de dias con sobreasignacion
    }

    Queries:
        Q1: ResourceAssignment DISTINCT usuario_id para el proyecto (1 query)
        Q2-QN: calculate_user_workload por usuario (3 queries cada uno)
               Para 10 usuarios: 1 + 30 = 31 queries totales.
               Aceptable para MVP (<20 usuarios por proyecto).

    Caching: TTL 15 minutos (dato mas estable que KPIs).
    """
    cache_key = f'analytics:utilization:{company_id}:{project_id}:{start_date}:{end_date}'
    cached = cache.get(cache_key)
    if cached:
        return cached

    from django.contrib.auth import get_user_model
    User = get_user_model()

    # Q1: usuarios con asignaciones activas en el proyecto
    usuario_ids = list(
        ResourceAssignment.objects.filter(
            company_id=company_id,
            tarea__proyecto_id=project_id,
            activo=True,
            fecha_inicio__lte=end_date,
            fecha_fin__gte=start_date,
        ).values_list('usuario_id', flat=True).distinct()
    )

    if not usuario_ids:
        return []

    usuarios = User.objects.filter(
        id__in=usuario_ids, company_id=company_id
    ).values('id', 'first_name', 'last_name', 'email')

    result = []
    for usuario in usuarios:
        workload = calculate_user_workload(
            usuario_id=str(usuario['id']),
            company_id=str(company_id),
            start_date=start_date,
            end_date=end_date,
        )
        nombre = f"{usuario['first_name']} {usuario['last_name']}".strip() or usuario['email']
        result.append({
            'usuario_id':             str(usuario['id']),
            'usuario_nombre':         nombre,
            'horas_capacidad':        str(workload.horas_capacidad),
            'horas_asignadas':        str(workload.horas_asignadas),
            'horas_registradas':      str(workload.horas_registradas),
            'porcentaje_utilizacion': str(workload.porcentaje_utilizacion),
            'conflictos':             len(workload.conflictos),
        })

    cache.set(cache_key, result, timeout=900)  # 15 minutos

    logger.info(
        'utilizacion_calculada',
        extra={
            'project_id':  str(project_id),
            'company_id':  str(company_id),
            'usuarios':    len(result),
            'start_date':  str(start_date),
            'end_date':    str(end_date),
        },
    )
    return result
```

---

### 3.6 compare_projects

```python
def compare_projects(
    project_ids: list[UUID],
    company_id: UUID,
) -> list[dict]:
    """
    Comparacion de metricas entre multiples proyectos.

    Llama a get_project_kpis() para cada proyecto. Aprovecha el cache
    de get_project_kpis (cada proyecto se cachea individualmente).

    Inputs:
        project_ids: lista de UUIDs (maximo 10 para MVP)
        company_id: UUID de la empresa

    Outputs: list de {
        'project_id': str,
        'nombre': str,
        'codigo': str,
        'estado': str,
        'tipo': str,
        'kpis': dict,   # identico al output de get_project_kpis()
    }

    Queries:
        Q1: Project.filter(id__in=project_ids) — 1 query para metadatos
        Q2-QN: get_project_kpis() por proyecto (2 queries c/u, mayormente desde cache)
        Total con cache frio: 1 + 2*N queries. Con cache caliente: 1 query.

    Validacion: maximo 10 proyectos por llamada para evitar sobrecarga.
    """
    if len(project_ids) > 10:
        raise ValueError('compare_projects: maximo 10 proyectos por llamada.')

    proyectos = Project.objects.filter(
        id__in=project_ids, company_id=company_id
    ).values('id', 'nombre', 'codigo', 'estado', 'tipo')

    proyectos_map = {str(p['id']): p for p in proyectos}

    result = []
    for pid in project_ids:
        pid_str = str(pid)
        if pid_str not in proyectos_map:
            continue
        meta = proyectos_map[pid_str]
        kpis = get_project_kpis(project_id=pid, company_id=company_id)
        result.append({
            'project_id': pid_str,
            'nombre':     meta['nombre'],
            'codigo':     meta['codigo'],
            'estado':     meta['estado'],
            'tipo':       meta['tipo'],
            'kpis':       kpis,
        })

    logger.info(
        'proyectos_comparados',
        extra={'company_id': str(company_id), 'cantidad': len(result)},
    )
    return result
```

---

### 3.7 get_project_timeline

```python
def get_project_timeline(
    project_id: UUID,
    company_id: UUID,
) -> list[dict]:
    """
    Datos del timeline tipo Gantt para el proyecto.

    Retorna fases y tareas con fechas planificadas vs reales para
    renderizar el grafico de Gantt en el frontend.

    Inputs:
        project_id: UUID del proyecto
        company_id: UUID de la empresa

    Outputs: list de {
        'id': str,
        'tipo': 'phase' | 'task',
        'nombre': str,
        'fase_id': str | None,
        'fecha_inicio_planificada': str,
        'fecha_fin_planificada': str,
        'fecha_inicio_real': str | None,
        'fecha_fin_real': str | None,
        'estado': str,
        'progreso': float,
        'orden': int | None,  # para fases
    }

    Queries:
        Q1: Phase.filter(proyecto=project_id) — todas las fases
        Q2: Task.filter(proyecto=project_id).select_related('fase')

    Total: 2 queries limpias.

    Caching: TTL 10 minutos.
    """
    cache_key = f'analytics:timeline:{company_id}:{project_id}'
    cached = cache.get(cache_key)
    if cached:
        return cached

    fases = Phase.objects.filter(
        proyecto_id=project_id, company_id=company_id
    ).values(
        'id', 'nombre', 'orden', 'estado', 'porcentaje_avance',
        'fecha_inicio_planificada', 'fecha_fin_planificada',
        'fecha_inicio_real', 'fecha_fin_real',
    ).order_by('orden')

    tareas = Task.objects.filter(
        proyecto_id=project_id, company_id=company_id,
    ).exclude(
        fecha_inicio=None, fecha_fin=None,
    ).values(
        'id', 'nombre', 'fase_id', 'estado', 'porcentaje_completado',
        'fecha_inicio', 'fecha_fin', 'fecha_limite', 'orden_display',
    ).order_by('fase_id', 'fecha_inicio')

    result = []

    for fase in fases:
        result.append({
            'id':                        str(fase['id']),
            'tipo':                      'phase',
            'nombre':                    fase['nombre'],
            'fase_id':                   None,
            'fecha_inicio_planificada':  fase['fecha_inicio_planificada'].isoformat(),
            'fecha_fin_planificada':     fase['fecha_fin_planificada'].isoformat(),
            'fecha_inicio_real':         fase['fecha_inicio_real'].isoformat() if fase['fecha_inicio_real'] else None,
            'fecha_fin_real':            fase['fecha_fin_real'].isoformat() if fase['fecha_fin_real'] else None,
            'estado':                    fase['estado'],
            'progreso':                  float(fase['porcentaje_avance']),
            'orden':                     fase['orden'],
        })

    for tarea in tareas:
        fecha_inicio = tarea['fecha_inicio'] or tarea['fecha_limite']
        fecha_fin = tarea['fecha_fin'] or tarea['fecha_limite']
        if not fecha_inicio:
            continue
        result.append({
            'id':                        str(tarea['id']),
            'tipo':                      'task',
            'nombre':                    tarea['nombre'],
            'fase_id':                   str(tarea['fase_id']),
            'fecha_inicio_planificada':  fecha_inicio.isoformat(),
            'fecha_fin_planificada':     (fecha_fin or fecha_inicio).isoformat(),
            'fecha_inicio_real':         None,
            'fecha_fin_real':            None,
            'estado':                    tarea['estado'],
            'progreso':                  float(tarea['porcentaje_completado']),
            'orden':                     None,
        })

    cache.set(cache_key, result, timeout=600)

    logger.info(
        'timeline_calculado',
        extra={
            'project_id': str(project_id),
            'company_id': str(company_id),
            'items':      len(result),
        },
    )
    return result
```

---

### 3.8 invalidate_project_analytics_cache (service auxiliar)

```python
def invalidate_project_analytics_cache(project_id: UUID, company_id: UUID) -> None:
    """
    Invalida todas las claves de cache de analytics para un proyecto.

    Llamar desde signals o desde otros services cuando cambia data
    relevante (nuevo TimesheetEntry, cambio de estado de Task, etc.).

    Patrones de cache invalidados:
        analytics:kpis:{company_id}:{project_id}
        analytics:burndown:{company_id}:{project_id}:*
        analytics:velocity:{company_id}:{project_id}:*
        analytics:distribution:{company_id}:{project_id}
        analytics:timeline:{company_id}:{project_id}
        analytics:utilization:{company_id}:{project_id}:*

    Nota: Django's cache backend local no soporta wildcards. Se invalidan
    los patrones fijos. Para granularity/periodo variables, se invalidan
    las variantes mas comunes ('week' y 'day').
    """
    prefixes = [
        f'analytics:kpis:{company_id}:{project_id}',
        f'analytics:burndown:{company_id}:{project_id}:week',
        f'analytics:burndown:{company_id}:{project_id}:day',
        f'analytics:velocity:{company_id}:{project_id}:8',
        f'analytics:velocity:{company_id}:{project_id}:12',
        f'analytics:distribution:{company_id}:{project_id}',
        f'analytics:timeline:{company_id}:{project_id}',
    ]
    cache.delete_many(prefixes)

    logger.info(
        'analytics_cache_invalidado',
        extra={'project_id': str(project_id), 'company_id': str(company_id), 'claves': len(prefixes)},
    )
```

---

## 4. Endpoints REST

Todos los endpoints se registran bajo `/api/v1/projects/` (prefijo existente).
Respetan el patron de permissions del modulo (`CanAccessProyectos`).

### Tabla de Endpoints

| # | URL | Metodo | Descripcion | Sincrono |
|---|---|---|---|---|
| 1 | `/api/v1/projects/{id}/kpis/` | GET | KPIs principales del proyecto | Si |
| 2 | `/api/v1/projects/{id}/burn-down/` | GET | Datos de burn down | Si |
| 3 | `/api/v1/projects/{id}/velocity/` | GET | Velocidad del equipo | Si |
| 4 | `/api/v1/projects/{id}/task-distribution/` | GET | Distribucion de tareas | Si |
| 5 | `/api/v1/projects/{id}/resource-utilization/` | GET | Utilizacion de recursos | Si |
| 6 | `/api/v1/projects/{id}/timeline/` | GET | Datos del timeline/Gantt | Si |
| 7 | `/api/v1/projects/compare/` | GET | Comparacion multi-proyecto | Si |
| 8 | `/api/v1/projects/reports/export-excel/` | POST | Exportar reporte a Excel | Si |
| 9 | `/api/v1/projects/{id}/phase-summary/` | GET | Resumen de fases con avance | Si |
| 10 | `/api/v1/projects/{id}/overdue-tasks/` | GET | Tareas vencidas del proyecto | Si |

---

### Especificaciones Detalladas

#### EP-1: GET `/api/v1/projects/{id}/kpis/`

**Parametros de query:** Ninguno.

**Response schema:**
```json
{
    "data": {
        "completion_rate": 67.5,
        "on_time_rate": 80.0,
        "budget_variance": 12.5,
        "total_tasks": 40,
        "completed_tasks": 27,
        "blocked_tasks": 2,
        "overdue_tasks": 3,
        "total_horas_estimadas": "320.00",
        "total_horas_registradas": "360.00",
        "porcentaje_avance": "65.00"
    },
    "meta": {
        "project_id": "uuid",
        "cached": true,
        "timestamp": "2026-03-27T10:00:00Z"
    }
}
```

**Permisos:** `CanAccessProyectos`. Cualquier rol con acceso al modulo.

**Sincrono:** Si. TTL cache 5 min. Respuesta esperada < 100ms con cache, < 500ms sin cache.

---

#### EP-2: GET `/api/v1/projects/{id}/burn-down/`

**Parametros de query:**
- `granularity`: `week` (default) | `day`

**Response schema:**
```json
{
    "data": [
        {
            "periodo": "2026-01-06",
            "horas_restantes": "280.00",
            "horas_registradas_periodo": "40.00",
            "horas_acumuladas": "40.00",
            "ideal": "278.00"
        }
    ],
    "meta": {
        "project_id": "uuid",
        "total_horas_estimadas": "320.00",
        "granularity": "week"
    }
}
```

**Permisos:** `CanAccessProyectos`.

---

#### EP-3: GET `/api/v1/projects/{id}/velocity/`

**Parametros de query:**
- `periods`: entero 4-12 (default 8)

**Response schema:**
```json
{
    "data": [
        {
            "semana": "2026-01-06",
            "tareas_completadas": 5,
            "promedio_acumulado": 5.0
        }
    ],
    "meta": {
        "project_id": "uuid",
        "periods": 8
    }
}
```

**Permisos:** `CanAccessProyectos`.

---

#### EP-4: GET `/api/v1/projects/{id}/task-distribution/`

**Parametros de query:** Ninguno.

**Response schema:**
```json
{
    "data": {
        "por_estado": {
            "todo": 5,
            "in_progress": 8,
            "in_review": 2,
            "blocked": 1,
            "completed": 24,
            "cancelled": 0
        },
        "por_prioridad": {
            "1": 4,
            "2": 20,
            "3": 12,
            "4": 4
        },
        "por_fase": [
            {
                "fase_id": "uuid",
                "fase_nombre": "Cimentacion",
                "total": 10,
                "completadas": 8
            }
        ]
    }
}
```

**Permisos:** `CanAccessProyectos`.

---

#### EP-5: GET `/api/v1/projects/{id}/resource-utilization/`

**Parametros de query:**
- `start_date`: ISO date (requerido)
- `end_date`: ISO date (requerido)

**Validacion:** `end_date - start_date <= 90 dias` para MVP (limitar carga de queries).

**Response schema:**
```json
{
    "data": [
        {
            "usuario_id": "uuid",
            "usuario_nombre": "Juan Perez",
            "horas_capacidad": "160.00",
            "horas_asignadas": "140.00",
            "horas_registradas": "120.00",
            "porcentaje_utilizacion": "75.00",
            "conflictos": 0
        }
    ],
    "meta": {
        "start_date": "2026-01-01",
        "end_date": "2026-03-31"
    }
}
```

**Permisos:** `CanAccessProyectos`. Solo `company_admin` ve todos los usuarios.

---

#### EP-6: GET `/api/v1/projects/{id}/timeline/`

**Parametros de query:** Ninguno.

**Response schema:**
```json
{
    "data": [
        {
            "id": "uuid",
            "tipo": "phase",
            "nombre": "Fase 1: Cimentacion",
            "fase_id": null,
            "fecha_inicio_planificada": "2026-01-01",
            "fecha_fin_planificada": "2026-03-31",
            "fecha_inicio_real": "2026-01-03",
            "fecha_fin_real": null,
            "estado": "active",
            "progreso": 65.0,
            "orden": 1
        }
    ]
}
```

**Permisos:** `CanAccessProyectos`.

---

#### EP-7: GET `/api/v1/projects/compare/`

**Parametros de query:**
- `ids`: lista de UUIDs separados por coma. Ejemplo: `?ids=uuid1,uuid2,uuid3`
- Maximo 10 IDs.

**Response schema:**
```json
{
    "data": [
        {
            "project_id": "uuid",
            "nombre": "Proyecto Alpha",
            "codigo": "PROJ-001",
            "estado": "in_progress",
            "tipo": "civil_works",
            "kpis": { ... }
        }
    ]
}
```

**Permisos:** `CanAccessProyectos`. Solo proyectos de la misma empresa.

---

#### EP-8: POST `/api/v1/projects/reports/export-excel/`

**Body:**
```json
{
    "project_id": "uuid",
    "report_type": "kpis" | "tasks" | "timesheets" | "resources",
    "start_date": "2026-01-01",
    "end_date": "2026-03-31"
}
```

**Response:** Stream binario `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
con header `Content-Disposition: attachment; filename="reporte-{codigo}-{date}.xlsx"`.

**Permisos:** `CanAccessProyectos`. Rol `viewer` puede exportar pero no modificar.

**Sincrono:** Si para MVP. Si el reporte supera 10,000 filas, se debe evaluar Celery.

---

#### EP-9: GET `/api/v1/projects/{id}/phase-summary/`

**Descripcion:** Resumen compacto de fases con avance y conteo de tareas.
Util para la barra de progreso del header del proyecto.

**Response schema:**
```json
{
    "data": [
        {
            "fase_id": "uuid",
            "nombre": "Cimentacion",
            "orden": 1,
            "estado": "active",
            "porcentaje_avance": "65.00",
            "total_tareas": 10,
            "tareas_completadas": 6,
            "tareas_bloqueadas": 1
        }
    ]
}
```

**Queries:** 1 query (Task GROUP BY fase con Count condicional).

---

#### EP-10: GET `/api/v1/projects/{id}/overdue-tasks/`

**Descripcion:** Lista de tareas vencidas del proyecto con informacion de responsable.
Util para el panel de alertas del dashboard.

**Parametros de query:**
- `limit`: entero (default 10, max 50)

**Response schema:**
```json
{
    "data": [
        {
            "task_id": "uuid",
            "codigo": "TASK-00042",
            "nombre": "Instalacion electrica",
            "fecha_limite": "2026-03-15",
            "dias_vencida": 12,
            "estado": "in_progress",
            "responsable_nombre": "Ana Garcia",
            "fase_nombre": "Fase 2: Estructuras"
        }
    ],
    "count": 3
}
```

**Queries:** 1 query con select_related('responsable', 'fase').

---

## 5. Estrategia de Caching

### Decision: Cache en Memoria de Django (locmem / django-cache)

**Para MVP: NO Redis.**

Razon: El proyecto actualmente no tiene Redis en docker-compose.yml ni en la configuracion
de AWS (ECS Fargate). Agregar Redis supone:
- Nuevo servicio en docker-compose.yml
- Nueva instancia en AWS (ElastiCache ~$15-30/mes adicional)
- Nueva dependencia operacional para un solo desarrollador

Para el volumen esperado en MVP (<50 proyectos por empresa, <20 usuarios activos),
el cache en memoria (`LocMemCache` en desarrollo, `FileBasedCache` en produccion)
es suficiente.

**Cuando escalar a Redis:**
- Cuando el servidor tenga multiples instancias detras de un load balancer (cache en memoria
  no es compartido entre instancias).
- Cuando las queries de analytics superen 1 segundo consistentemente.

**Configuracion recomendada en settings (backend/config/production.py):**

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/tmp/saisuite_cache',
        'TIMEOUT': 300,
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}
```

---

### TTL por Tipo de Metrica

| Metrica | TTL | Razon |
|---|---|---|
| KPIs (`get_project_kpis`) | 5 min (300s) | Cambia con cada timesheet registrado |
| Burn Down | 10 min (600s) | Cambia solo con timesheets; menos frecuente |
| Velocity | 10 min (600s) | Cambia cuando se completan tareas; poco frecuente |
| Task Distribution | 5 min (300s) | Cambia con cambios de estado de tareas |
| Resource Utilization | 15 min (900s) | Dato mas estable; cambios en capacidad son raros |
| Timeline/Gantt | 10 min (600s) | Cambia con cambios de fechas o progreso |
| Compare Projects | Heredado de KPIs | Cada proyecto tiene su propio cache |

---

### Invalidacion del Cache

**Cuando invalidar:** Usar signals de Django para invalidar automaticamente.

**Eventos que invalidan el cache de un proyecto:**

| Evento | Modelos Afectados | Accion |
|---|---|---|
| Nuevo `TimesheetEntry` | KPIs, BurnDown, Velocity, Utilization | `invalidate_project_analytics_cache(project_id)` |
| Cambio de estado en `Task` | KPIs, Distribution, Velocity | `invalidate_project_analytics_cache(project_id)` |
| Cambio de fechas en `Task` | Timeline | `invalidate_project_analytics_cache(project_id)` |
| Cambio de estado en `Phase` | Timeline, PhaseSummary | `invalidate_project_analytics_cache(project_id)` |
| Cambio de `ResourceAssignment` | Utilization | `invalidate_project_analytics_cache(project_id)` |

**Implementacion en `signals.py` (archivo nuevo o al final de `models.py`):**

```python
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.proyectos.analytics_services import invalidate_project_analytics_cache

@receiver(post_save, sender=TimesheetEntry)
def invalidar_cache_timesheet(sender, instance, **kwargs):
    project_id = instance.tarea.proyecto_id
    invalidate_project_analytics_cache(
        project_id=project_id,
        company_id=instance.company_id,
    )

@receiver(post_save, sender=Task)
def invalidar_cache_task(sender, instance, created, **kwargs):
    invalidate_project_analytics_cache(
        project_id=instance.proyecto_id,
        company_id=instance.company_id,
    )
```

**Nota:** Los signals deben registrarse en `apps/proyectos/apps.py` bajo `ready()`.

---

## 6. Exportacion PDF/Excel

### PDF: Recomendacion para MVP

**Decision: Dejar la generacion de PDF en el frontend (jsPDF o el browser Print API).**

Razon:
1. WeasyPrint requiere instalacion de dependencias del sistema (libpango, libcairo) que
   complican el Dockerfile y el despliegue en ECS Fargate.
2. jsPDF puede capturar directamente los graficos del navegador (Chart.js/D3) como imagenes.
3. Para un solo desarrollador, implementar WeasyPrint + templates HTML es 3-4 dias adicionales
   versus jsPDF que son 4-8 horas.
4. Los reportes de analytics son principalmente graficos + tablas; el frontend ya tiene el dato
   listo para renderizar.

**Si en el futuro se necesita PDF desde el backend (ej: reportes programados enviados por email),**
agregar WeasyPrint en ese momento con justificacion especifica.

---

### Excel: openpyxl en Django

**Decision: openpyxl en el backend.**

Razon: Los datos de timesheets, tareas y recursos son tabulares. El usuario final espera
poder abrir el Excel y aplicar sus propios filtros. Generar en backend garantiza que el
Excel tenga toda la data sin limitaciones del navegador.

**Dependencia:**
```
openpyxl==3.1.2  # agregar a requirements.txt
```

**Service de exportacion (`export_services.py` dentro del mismo modulo o en `analytics_services.py`):**

```python
def export_project_to_excel(
    project_id: UUID,
    company_id: UUID,
    report_type: str,
    start_date: date,
    end_date: date,
) -> bytes:
    """
    Genera un archivo Excel con los datos del proyecto.

    report_type opciones:
        'kpis'       — hoja unica con KPIs del proyecto
        'tasks'      — listado de tareas con estado, responsable, horas
        'timesheets' — registros de horas del periodo por usuario y tarea
        'resources'  — utilizacion de recursos del periodo

    Retorna bytes del archivo .xlsx para streaming en la view.
    """
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from io import BytesIO

    wb = openpyxl.Workbook()
    ws = wb.active

    proyecto = Project.objects.filter(
        id=project_id, company_id=company_id
    ).values('nombre', 'codigo').first()

    ws.title = f"{proyecto['codigo']}-{report_type}"

    # Estilos ValMen Tech: azul corporativo
    header_fill = PatternFill('solid', fgColor='1565C0')
    header_font = Font(bold=True, color='FFFFFF')

    if report_type == 'tasks':
        headers = ['Codigo', 'Nombre', 'Estado', 'Prioridad', 'Responsable',
                   'Fase', 'Horas Est.', 'Horas Reg.', 'Fecha Limite', 'Completado %']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.fill = header_fill
            cell.font = header_font

        tasks = Task.objects.filter(
            proyecto_id=project_id, company_id=company_id
        ).select_related('responsable', 'fase').order_by('fase__orden', 'codigo')

        for row_num, task in enumerate(tasks, 2):
            ws.cell(row=row_num, column=1, value=task.codigo)
            ws.cell(row=row_num, column=2, value=task.nombre)
            ws.cell(row=row_num, column=3, value=task.estado)
            ws.cell(row=row_num, column=4, value=task.get_prioridad_display())
            ws.cell(row=row_num, column=5, value=task.responsable.get_full_name() if task.responsable else '')
            ws.cell(row=row_num, column=6, value=task.fase.nombre)
            ws.cell(row=row_num, column=7, value=float(task.horas_estimadas))
            ws.cell(row=row_num, column=8, value=float(task.horas_registradas))
            ws.cell(row=row_num, column=9, value=str(task.fecha_limite) if task.fecha_limite else '')
            ws.cell(row=row_num, column=10, value=task.porcentaje_completado)

    elif report_type == 'timesheets':
        headers = ['Fecha', 'Usuario', 'Tarea (codigo)', 'Tarea (nombre)',
                   'Fase', 'Horas', 'Validado', 'Descripcion']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.fill = header_fill
            cell.font = header_font

        entries = (
            TimesheetEntry.objects.filter(
                company_id=company_id,
                tarea__proyecto_id=project_id,
                fecha__gte=start_date,
                fecha__lte=end_date,
            )
            .select_related('usuario', 'tarea', 'tarea__fase')
            .order_by('fecha', 'usuario__last_name')
        )

        for row_num, entry in enumerate(entries, 2):
            ws.cell(row=row_num, column=1, value=str(entry.fecha))
            ws.cell(row=row_num, column=2, value=entry.usuario.get_full_name() or entry.usuario.email)
            ws.cell(row=row_num, column=3, value=entry.tarea.codigo)
            ws.cell(row=row_num, column=4, value=entry.tarea.nombre)
            ws.cell(row=row_num, column=5, value=entry.tarea.fase.nombre)
            ws.cell(row=row_num, column=6, value=float(entry.horas))
            ws.cell(row=row_num, column=7, value='Si' if entry.validado else 'No')
            ws.cell(row=row_num, column=8, value=entry.descripcion)

    # Autoajuste de columnas
    for column in ws.columns:
        max_length = max((len(str(cell.value or '')) for cell in column), default=10)
        ws.column_dimensions[column[0].column_letter].width = min(max_length + 4, 50)

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    logger.info(
        'excel_exportado',
        extra={
            'project_id':  str(project_id),
            'company_id':  str(company_id),
            'report_type': report_type,
        },
    )
    return buffer.read()
```

**View correspondiente:**

```python
class ProjectExportExcelView(APIView):
    permission_classes = [CanAccessProyectos]

    def post(self, request):
        from apps.proyectos.analytics_services import export_project_to_excel
        from django.http import HttpResponse

        project_id = request.data.get('project_id')
        report_type = request.data.get('report_type', 'tasks')
        start_date_str = request.data.get('start_date')
        end_date_str = request.data.get('end_date')

        # Validacion minima — serializer completo en Fase 5
        if not all([project_id, start_date_str, end_date_str]):
            return Response({'error': 'project_id, start_date y end_date son requeridos.'}, status=400)

        excel_bytes = export_project_to_excel(
            project_id=project_id,
            company_id=str(request.user.company_id),
            report_type=report_type,
            start_date=date.fromisoformat(start_date_str),
            end_date=date.fromisoformat(end_date_str),
        )

        response = HttpResponse(
            excel_bytes,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="reporte-{report_type}.xlsx"'
        return response
```

---

## 7. Indices de Base de Datos

### Indices Existentes Relevantes (ya en `Task.Meta.indexes`)

```python
# En Task — ya existen:
models.Index(fields=['fase', 'estado']),
models.Index(fields=['proyecto', 'estado']),
models.Index(fields=['responsable']),
models.Index(fields=['fecha_limite']),
```

El indice `(proyecto, estado)` cubre Completion Rate, Task Distribution y Velocity.
El indice `(fecha_limite)` cubre overdue_tasks.

### Indices Existentes en TimesheetEntry

```python
# En TimesheetEntry — ya existen:
models.Index(fields=['usuario', 'fecha']),
models.Index(fields=['tarea', 'validado']),
```

### Indices Faltantes — Necesarios para Analytics

Se deben agregar en la migracion inicial de Fase 5:

```python
# Migration: 0016_analytics_indexes.py

class Migration(migrations.Migration):
    dependencies = [
        ('proyectos', '0015_resource_models'),
    ]

    operations = [
        # Indice 1: TimesheetEntry por tarea + fecha
        # Cubre burn_down y burn_rate (JOIN tarea -> proyecto + GROUP BY fecha)
        migrations.AddIndex(
            model_name='timesheetentry',
            index=models.Index(
                fields=['tarea', 'fecha'],
                name='idx_timesheet_tarea_fecha',
            ),
        ),

        # Indice 2: Task.fecha_completion + estado
        # Cubre On-Time Rate y Velocity (cuando se agrega fecha_completion)
        migrations.AddIndex(
            model_name='task',
            index=models.Index(
                fields=['proyecto', 'fecha_completion', 'estado'],
                name='idx_task_proj_completion_estado',
            ),
        ),

        # Indice 3: Task por proyecto + fecha_limite + estado
        # Cubre overdue_tasks con filtro de company implicito por multi-tenant
        migrations.AddIndex(
            model_name='task',
            index=models.Index(
                fields=['proyecto', 'fecha_limite', 'estado'],
                name='idx_task_proj_deadline_estado',
            ),
        ),

        # Indice 4: TimesheetEntry por company + fecha
        # Cubre queries de utilization y burn_rate con filtro company primero
        migrations.AddIndex(
            model_name='timesheetentry',
            index=models.Index(
                fields=['company', 'fecha'],
                name='idx_timesheet_company_fecha',
            ),
        ),

        # Campo fecha_completion en Task
        migrations.AddField(
            model_name='task',
            name='fecha_completion',
            field=models.DateField(null=True, blank=True),
        ),
    ]
```

### Analisis de Cardinalidad

| Indice | Cardinalidad Estimada | Beneficio |
|---|---|---|
| `idx_timesheet_tarea_fecha` | Alta (tarea x dia) | Alto para BurnDown/BurnRate |
| `idx_task_proj_completion_estado` | Media | Alto para Velocity/On-Time |
| `idx_task_proj_deadline_estado` | Media | Alto para OverdueTasks |
| `idx_timesheet_company_fecha` | Alta | Medio para queries company-wide |

**Nota:** PostgreSQL ya tiene estadisticas de los indices existentes. Verificar con
`EXPLAIN ANALYZE` en produccion antes de agregar todos los indices. Los de `Task` son
prioritarios porque la tabla crecera a miles de filas por empresa.

---

## 8. Estructura de Archivos Backend

### Estructura Recomendada: Archivos Separados

```
backend/apps/proyectos/
├── models.py                        # EXISTENTE — agregar fecha_completion a Task
├── services.py                      # EXISTENTE — sin cambios
├── tarea_services.py                # EXISTENTE — sin cambios
├── resource_services.py             # EXISTENTE — sin cambios
├── analytics_services.py            # NUEVO — todos los services de analytics
├── serializers.py                   # EXISTENTE — agregar serializers de analytics
├── analytics_serializers.py         # NUEVO (opcional, si serializers.py crece mucho)
├── views.py                         # EXISTENTE — agregar analytics viewsets
├── analytics_views.py               # NUEVO (recomendado para mantener views.py manejable)
├── urls.py                          # EXISTENTE — registrar nuevas URLs de analytics
├── filters.py                       # EXISTENTE — sin cambios en MVP
├── permissions.py                   # EXISTENTE — reutilizar CanAccessProyectos
├── migrations/
│   ├── 0015_resource_models.py      # EXISTENTE
│   └── 0016_analytics_indexes.py    # NUEVO — indices + fecha_completion
└── tests/
    ├── test_analytics_services.py   # NUEVO — cobertura minima 80%
    ├── test_analytics_views.py      # NUEVO
    ├── test_resource_models.py      # EXISTENTE
    ├── test_resource_services.py    # EXISTENTE
    └── test_resource_views.py       # EXISTENTE
```

### Justificacion de Separacion en Archivos Propios

**Por que `analytics_services.py` separado (NO integrar en `services.py`):**
- `services.py` ya es grande. Agregar 7+ funciones de analytics lo hace dificil de navegar.
- Los analytics services tienen un dominio cohesivo y separado del CRUD.
- Facilita los tests: `test_analytics_services.py` mockea solo lo que necesita.
- Sigue el patron establecido por `resource_services.py` (Feature #4).

**Por que `analytics_views.py` separado (NO integrar en `views.py`):**
- `views.py` tiene ~19 ViewSets y Views. Ya supera las 500 lineas (19100 tokens segun error de lectura).
- Los analytics views son todos APIViews (no ViewSets), codigo diferente.
- Misma razon de cohesion y navegabilidad.

**Por que los serializers pueden ir en `serializers.py` existente:**
- Los serializers de analytics son simples (solo validan query params y formatean responses).
- No justifican un archivo separado en MVP.
- Si crecen, mover a `analytics_serializers.py`.

---

### Registro de URLs

Agregar en `urls.py` existente bajo la seccion de analytics:

```python
# En apps/proyectos/urls.py — seccion NUEVA al final de urlpatterns

from apps.proyectos.analytics_views import (
    ProjectKPIsView,
    ProjectBurnDownView,
    ProjectVelocityView,
    ProjectTaskDistributionView,
    ProjectResourceUtilizationView,
    ProjectTimelineView,
    ProjectPhaseSummaryView,
    ProjectOverdueTasksView,
    ProjectCompareView,
    ProjectExportExcelView,
)

# Agregar al final de urlpatterns:
urlpatterns += [
    # Analytics — Feature #5
    path('<uuid:proyecto_pk>/kpis/', ProjectKPIsView.as_view(), name='project-kpis'),
    path('<uuid:proyecto_pk>/burn-down/', ProjectBurnDownView.as_view(), name='project-burn-down'),
    path('<uuid:proyecto_pk>/velocity/', ProjectVelocityView.as_view(), name='project-velocity'),
    path('<uuid:proyecto_pk>/task-distribution/', ProjectTaskDistributionView.as_view(), name='project-task-distribution'),
    path('<uuid:proyecto_pk>/resource-utilization/', ProjectResourceUtilizationView.as_view(), name='project-resource-utilization'),
    path('<uuid:proyecto_pk>/timeline/', ProjectTimelineView.as_view(), name='project-timeline'),
    path('<uuid:proyecto_pk>/phase-summary/', ProjectPhaseSummaryView.as_view(), name='project-phase-summary'),
    path('<uuid:proyecto_pk>/overdue-tasks/', ProjectOverdueTasksView.as_view(), name='project-overdue-tasks'),
    path('compare/', ProjectCompareView.as_view(), name='projects-compare'),
    path('reports/export-excel/', ProjectExportExcelView.as_view(), name='projects-export-excel'),
]
```

---

### Patron de Analytics View

Todas las analytics views siguen el mismo patron compacto:

```python
# analytics_views.py

class ProjectKPIsView(APIView):
    """GET /api/v1/projects/{proyecto_pk}/kpis/"""
    permission_classes = [CanAccessProyectos]

    def get(self, request, proyecto_pk):
        company_id = str(request.user.company_id)

        # Verificar que el proyecto existe y pertenece a la empresa
        if not Project.objects.filter(id=proyecto_pk, company_id=company_id).exists():
            return Response({'error': 'Proyecto no encontrado.'}, status=404)

        data = get_project_kpis(
            project_id=proyecto_pk,
            company_id=company_id,
        )

        return Response({
            'data': data,
            'meta': {
                'project_id': str(proyecto_pk),
                'timestamp': timezone.now().isoformat(),
            },
        })
```

---

## Resumen de Decisiones de Arquitectura

| Aspecto | Decision | Razon |
|---|---|---|
| Nuevos modelos | Solo `Task.fecha_completion` | Minimo viable; DashboardConfig y MetricSnapshot en Feature #6 |
| Cache | Django locmem/file, SIN Redis | MVP sin overhead operacional |
| TTL KPIs | 5 min | Balance entre frescura y rendimiento |
| PDF | Frontend (jsPDF) | Evitar WeasyPrint en Fargate |
| Excel | openpyxl backend | Datos tabulares completos sin limite de browser |
| Archivos | `analytics_services.py` + `analytics_views.py` separados | Cohesion, navegabilidad, patron de Feature #4 |
| Queries | Max 3 por endpoint con cache | Sub-500ms sin cache, sub-100ms con cache |
| Invalidacion | Django signals post_save | Simple, alineado con patron del proyecto |

---

*Archivo generado el 2026-03-27 como especificacion de Backend Architecture para Feature #5.*
*Proximo paso: crear `docs/plans/FEATURE-5-FRONTEND-ARCHITECTURE.md` para el plan de componentes Angular.*
