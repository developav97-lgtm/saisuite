# FEATURE-6-BACKEND-ARCHITECTURE.md
# Advanced Scheduling — Arquitectura Backend

**Fecha:** 27 Marzo 2026
**Feature:** #6 — Advanced Scheduling
**Decisión tecnológica:** Django + Python (ver evaluación abajo)

---

## 1. Evaluación Django vs Go

| Criterio | Estado | Notas |
|----------|--------|-------|
| Alta concurrencia >1000 req/s | ❌ | Scheduling es batch, no stream |
| Procesamiento intensivo | ⚠️ | >1000 tareas puede superar 5s |
| Ejecutable standalone | ❌ | Corre en servidor |
| Optimización de costos | ❌ | Sin métricas reales aún |

**Veredicto: Django + Python para MVP.**
Si prueba SK-28 muestra >5s en 1000 tareas → migrar auto-schedule a Celery task async.
Go microservice solo si Celery no es suficiente (requiere métricas reales post-launch).

---

## 2. Modelos nuevos

### 2.1 ProjectBaseline

```python
class ProjectBaseline(BaseModel):
    """
    Snapshot del plan del proyecto en un momento dado.
    Permite comparar plan original vs plan actual.
    """
    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
        related_name='baselines',
    )
    name = models.CharField(max_length=255)  # "Plan Original", "Baseline Q1"
    description = models.TextField(blank=True)
    is_active_baseline = models.BooleanField(
        default=False,
        help_text='Solo un baseline activo por proyecto.',
    )

    # Snapshot de tareas: [{task_id, nombre, fecha_inicio, fecha_fin, horas_estimadas}]
    tasks_snapshot = models.JSONField(default=list)

    # Snapshot de asignaciones: [{assignment_id, task_id, user_id, porcentaje, fechas}]
    resources_snapshot = models.JSONField(default=list)

    # Métricas del momento del snapshot
    project_end_date_snapshot = models.DateField(null=True, blank=True)
    total_tasks_snapshot = models.IntegerField(default=0)
    critical_path_snapshot = models.JSONField(default=list)  # [task_id, ...]

    class Meta:
        verbose_name = 'Baseline de Proyecto'
        verbose_name_plural = 'Baselines de Proyectos'
        ordering = ['-created_at']
        # Solo un baseline activo por proyecto+company
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'project'],
                condition=models.Q(is_active_baseline=True),
                name='uq_one_active_baseline_per_project',
            )
        ]
```

### 2.2 TaskConstraint

```python
class ConstraintType(models.TextChoices):
    ASAP                    = 'asap',                     'As Soon As Possible'
    ALAP                    = 'alap',                     'As Late As Possible'
    MUST_START_ON           = 'must_start_on',            'Must Start On'
    MUST_FINISH_ON          = 'must_finish_on',           'Must Finish On'
    START_NO_EARLIER_THAN   = 'start_no_earlier_than',    'Start No Earlier Than'
    START_NO_LATER_THAN     = 'start_no_later_than',      'Start No Later Than'
    FINISH_NO_EARLIER_THAN  = 'finish_no_earlier_than',   'Finish No Earlier Than'
    FINISH_NO_LATER_THAN    = 'finish_no_later_than',     'Finish No Later Than'


class TaskConstraint(BaseModel):
    """
    Restricción de scheduling aplicada a una tarea.
    Las restricciones se respetan durante auto-schedule.
    """
    task = models.ForeignKey(
        'Task',
        on_delete=models.CASCADE,
        related_name='scheduling_constraints',
    )
    constraint_type = models.CharField(
        max_length=30,
        choices=ConstraintType.choices,
        default=ConstraintType.ASAP,
    )
    constraint_date = models.DateField(
        null=True,
        blank=True,
        help_text='Requerido para tipos con fecha (must_start_on, etc.)',
    )

    class Meta:
        verbose_name = 'Restricción de Tarea'
        verbose_name_plural = 'Restricciones de Tareas'
        # Una tarea puede tener múltiples constraints de tipos distintos
        unique_together = [('company', 'task', 'constraint_type')]

    def clean(self):
        from django.core.exceptions import ValidationError
        date_required = [
            'must_start_on', 'must_finish_on',
            'start_no_earlier_than', 'start_no_later_than',
            'finish_no_earlier_than', 'finish_no_later_than',
        ]
        if self.constraint_type in date_required and not self.constraint_date:
            raise ValidationError({
                'constraint_date': f'constraint_date es obligatorio para {self.constraint_type}.'
            })
```

### 2.3 WhatIfScenario

```python
class WhatIfScenario(BaseModel):
    """
    Escenario de simulación hipotética.
    Los cambios se aplican a un clon en memoria — nunca modifican datos reales.
    """
    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
        related_name='what_if_scenarios',
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_scenarios',
    )

    # Cambios propuestos (JSON estructurado)
    # tasks: {str(task_id): {field: new_value, ...}}
    # resources: {str(assignment_id): {field: new_value, ...}}
    # dependencies: {str(dep_id): {retraso_dias: N}}
    task_changes = models.JSONField(default=dict)
    resource_changes = models.JSONField(default=dict)
    dependency_changes = models.JSONField(default=dict)

    # Resultados calculados (null hasta correr simulación)
    simulated_end_date = models.DateField(null=True, blank=True)
    simulated_critical_path = models.JSONField(null=True, blank=True)  # [task_id, ...]
    days_delta = models.IntegerField(
        null=True, blank=True,
        help_text='Días de diferencia vs plan actual (+= retraso, -= adelanto)',
    )
    tasks_affected_count = models.IntegerField(null=True, blank=True)
    simulation_ran_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Escenario What-If'
        verbose_name_plural = 'Escenarios What-If'
        ordering = ['-created_at']
```

---

## 3. Archivo: scheduling_services.py

Patrón: igual que `analytics_services.py` y `resource_services.py` — dentro de `apps/proyectos/`.

### 3.1 SchedulingService — CPM Core

```python
class SchedulingService:

    @staticmethod
    def topological_sort(tasks: list[Task], dependencies: list[TaskDependency]) -> list[Task]:
        """
        Kahn's algorithm para ordenar tareas respetando dependencias.
        Detecta ciclos y lanza ValidationError con lista de tareas en conflicto.

        Complejidad: O(V + E) donde V=tareas, E=dependencias.
        """

    @staticmethod
    def forward_pass(tasks_sorted: list[Task], dependencies: list[TaskDependency], project_start: date) -> dict:
        """
        Calcula early_start y early_finish por tarea.
        Respeta tipos FS, SS, FF y retraso_dias.

        Retorna: {task_id: {'early_start': date, 'early_finish': date}}

        Lógica por tipo de dependencia:
        - FS: sucesora.early_start = predecesora.early_finish + lag
        - SS: sucesora.early_start = predecesora.early_start + lag
        - FF: sucesora.early_finish = predecesora.early_finish + lag
              → early_start = early_finish - duration
        """

    @staticmethod
    def backward_pass(tasks_sorted: list[Task], dependencies: list[TaskDependency], project_end: date) -> dict:
        """
        Calcula late_start y late_finish por tarea (en reversa).

        Retorna: {task_id: {'late_start': date, 'late_finish': date}}
        """

    @staticmethod
    def calculate_float(task_id, forward_data: dict, backward_data: dict) -> dict:
        """
        total_float = late_start - early_start
        free_float = min(successor.early_start) - early_finish - lag
        is_critical = (total_float == 0)
        """

    @staticmethod
    def get_critical_path(tasks: list[Task], forward_data: dict, backward_data: dict) -> list:
        """
        Retorna lista de task_ids donde total_float == 0.
        """

    @staticmethod
    @transaction.atomic
    def auto_schedule_project(
        project_id: str,
        company_id: str,
        scheduling_mode: str = 'asap',
        respect_constraints: bool = True,
        dry_run: bool = False,
    ) -> dict:
        """
        Reprograma todas las tareas del proyecto.

        Algoritmo:
        1. Cargar tareas con fecha_inicio y fecha_fin (excluir nulls)
        2. topological_sort()
        3. forward_pass() → early_start/finish por tarea
        4. backward_pass() → late_start/finish por tarea
        5. Si scheduling_mode == 'asap': aplicar early dates
           Si scheduling_mode == 'alap': aplicar late dates
        6. Si respect_constraints: apply_constraints()
        7. Si dry_run: retornar preview sin guardar
           Si no dry_run: Task.objects.bulk_update(tasks, ['fecha_inicio', 'fecha_fin'])

        Retorna:
        {
            'tasks_rescheduled': int,
            'tasks_excluded': [task_id, ...],  # sin fechas
            'new_project_end_date': date,
            'critical_path': [task_id, ...],
            'warnings': [str, ...],
            'dry_run': bool,
        }
        """

    @staticmethod
    def apply_constraints(tasks: list[Task], constraints: dict, dates: dict) -> dict:
        """
        Ajusta fechas calculadas según restricciones activas.
        constraints: {task_id: [TaskConstraint, ...]}
        dates: {task_id: {'fecha_inicio': date, 'fecha_fin': date}}

        Prioridad de resolución:
        1. must_start_on / must_finish_on (más restrictivas)
        2. start_no_earlier_than / finish_no_later_than
        3. asap / alap (defaults)
        """
```

### 3.2 ResourceLevelingService

```python
class ResourceLevelingService:

    @staticmethod
    def calculate_daily_workload(
        project_id: str,
        company_id: str,
        start_date: date,
        end_date: date,
    ) -> dict:
        """
        Calcula carga diaria por usuario en el rango de fechas.
        Retorna: {user_id: {date: porcentaje_total}}
        Usa ResourceAssignment y ResourceCapacity existentes.
        """

    @staticmethod
    def detect_overload_periods(workload: dict, capacities: dict) -> list:
        """
        Identifica días donde workload[user_id][date] > capacities[user_id].
        Retorna: [{user_id, date, overload_pct, conflicting_tasks: [task_id, ...]}]
        """

    @staticmethod
    @transaction.atomic
    def level_resources(
        project_id: str,
        company_id: str,
        dry_run: bool = False,
        max_iterations: int = 500,
    ) -> dict:
        """
        Mueve tareas con float > 0 para eliminar sobreasignación.

        Algoritmo greedy:
        1. Calcular workload diario
        2. Detectar períodos de sobrecarga
        3. Por cada sobrecarga, ordenar tareas asignadas por float (mayor primero)
        4. Retrasar tarea con más float hasta que sobrecarga < 100%
        5. Repetir hasta sin sobreasignaciones o max_iterations

        max_iterations: protección contra loops (retorna con warning si se alcanza)

        Retorna:
        {
            'tasks_moved': int,
            'max_overload_before': float,
            'max_overload_after': float,
            'leveling_effective': bool,
            'warnings': [str, ...],
        }
        """
```

### 3.3 BaselineService

```python
class BaselineService:

    @staticmethod
    @transaction.atomic
    def create_baseline(project_id: str, company_id: str, name: str, set_as_active: bool = True) -> ProjectBaseline:
        """
        Captura snapshot actual del proyecto.
        Si set_as_active=True: desactiva el baseline activo anterior.
        """

    @staticmethod
    def compare_to_baseline(project_id: str, company_id: str, baseline_id: str) -> dict:
        """
        Compara plan actual vs snapshot del baseline.

        Retorna:
        {
            'baseline_name': str,
            'baseline_end_date': date,
            'current_end_date': date,
            'schedule_variance_days': int,  # + = retraso
            'tasks': [{
                'task_id', 'nombre',
                'baseline_start', 'baseline_finish',
                'current_start', 'current_finish',
                'variance_days': int,
                'status': 'ahead' | 'on_schedule' | 'behind',
            }],
            'summary': {
                'ahead': int,
                'on_schedule': int,
                'behind': int,
            }
        }
        """
```

### 3.4 WhatIfService

```python
class WhatIfService:

    @staticmethod
    @transaction.atomic
    def create_scenario(project_id: str, company_id: str, user_id: str, name: str, description: str, changes: dict) -> WhatIfScenario:
        """
        Crea escenario con los cambios propuestos. No ejecuta simulación aún.
        """

    @staticmethod
    def run_simulation(scenario_id: str, company_id: str) -> WhatIfScenario:
        """
        Ejecuta auto-schedule sobre clon en memoria con los cambios aplicados.

        Algoritmo:
        1. Cargar datos reales del proyecto (tareas, dependencias, asignaciones)
        2. Aplicar scenario.task_changes sobre datos en memoria (no BD)
        3. Aplicar scenario.resource_changes sobre datos en memoria
        4. Aplicar scenario.dependency_changes sobre datos en memoria
        5. Ejecutar SchedulingService.auto_schedule_project(dry_run=True) sobre clon
        6. Guardar resultados en WhatIfScenario (simulated_end_date, days_delta, etc.)
        7. Nunca tocar datos reales de la BD

        ⚠️ CRÍTICO: dry_run=True garantiza que NO se modifican Task reales.
        """

    @staticmethod
    def compare_scenarios(scenario_ids: list[str], company_id: str) -> dict:
        """
        Tabla comparativa de múltiples escenarios.

        Retorna:
        {
            'scenarios': [{
                'id', 'name',
                'simulated_end_date',
                'days_delta',
                'tasks_affected_count',
            }],
            'current_plan': {'end_date': date},
        }
        """
```

---

## 4. Views — scheduling_views.py

```python
# Auto-Schedule
class AutoScheduleView(APIView):
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def post(self, request, project_pk):
        # Solo gerente o coordinador pueden auto-schedule
        # Parámetros: scheduling_mode, respect_constraints, dry_run
        pass

class ResourceLevelingView(APIView):
    def post(self, request, project_pk):
        pass

class CriticalPathView(APIView):
    def get(self, request, project_pk):
        pass

class TaskFloatView(APIView):
    def get(self, request, task_pk):
        pass

# Constraints
class TaskConstraintViewSet(ModelViewSet):
    # list, create por task_pk
    # destroy por pk
    pass

# Baselines
class ProjectBaselineViewSet(ModelViewSet):
    # list, create por project_pk
    # retrieve con compare por pk
    pass

class BaselineCompareView(APIView):
    def get(self, request, baseline_pk):
        pass

# What-If
class WhatIfScenarioViewSet(ModelViewSet):
    # list, create por project_pk
    # retrieve, destroy por pk
    pass

class RunSimulationView(APIView):
    def post(self, request, scenario_pk):
        pass

class CompareScenariosView(APIView):
    def post(self, request):
        # Body: {scenario_ids: [uuid, ...]}
        pass
```

---

## 5. Endpoints REST — 15 rutas

Todas bajo `/api/v1/projects/` (mismo prefijo existente):

```
# Auto-Scheduling
POST   <uuid:project_pk>/scheduling/auto-schedule/
POST   <uuid:project_pk>/scheduling/level-resources/
GET    <uuid:project_pk>/scheduling/critical-path/
GET    tasks/<uuid:task_pk>/scheduling/float/

# Constraints
GET    tasks/<uuid:task_pk>/constraints/
POST   tasks/<uuid:task_pk>/constraints/
DELETE constraints/<uuid:pk>/

# Baselines
GET    <uuid:project_pk>/baselines/
POST   <uuid:project_pk>/baselines/
GET    baselines/<uuid:pk>/
GET    baselines/<uuid:pk>/compare/
DELETE baselines/<uuid:pk>/

# What-If Scenarios
GET    <uuid:project_pk>/scenarios/
POST   <uuid:project_pk>/scenarios/
GET    scenarios/<uuid:pk>/
POST   scenarios/<uuid:pk>/run-simulation/
DELETE scenarios/<uuid:pk>/
POST   scenarios/compare/
```

**Total:** 16 endpoints (1 más que el feature doc — `DELETE baselines/{pk}`)

---

## 6. Permisos por endpoint

| Endpoint | Permiso mínimo |
|----------|----------------|
| auto-schedule (POST) | `company_admin` o gerente del proyecto |
| level-resources (POST) | `company_admin` o gerente |
| critical-path (GET) | Cualquier miembro de la empresa |
| float (GET) | Cualquier miembro de la empresa |
| constraints CRUD | `company_admin` o gerente/coordinador |
| baselines CRUD | `company_admin` o gerente |
| what-if scenarios | Cualquier miembro (read) / gerente (write) |

---

## 7. Caching

```python
from django.core.cache import cache

# En CriticalPathView.get():
cache_key = f"critical_path:{project_id}:{company_id}"
cached = cache.get(cache_key)
if cached:
    return Response(cached)

result = SchedulingService.get_critical_path(...)
cache.set(cache_key, result, timeout=300)  # 5 minutos

# Invalidar en auto_schedule_project() post-guardado:
cache.delete(f"critical_path:{project_id}:{company_id}")
```

Sin Redis en MVP — Django file-based cache (mismo approach que Feature #5).

---

## 8. Migración 0016

```python
# Índices adicionales en migración 0016:
migrations.AddIndex(
    model_name='task',
    index=models.Index(fields=['proyecto', 'fecha_inicio', 'fecha_fin'], name='idx_task_proj_dates'),
),
migrations.AddIndex(
    model_name='task',
    index=models.Index(fields=['fecha_fin'], name='idx_task_fecha_fin'),
),
migrations.AddIndex(
    model_name='taskdependency',
    index=models.Index(fields=['tarea_predecesora'], name='idx_tdep_predecessor'),
),
```

---

## 9. Nota sobre DependencyType

El modelo actual tiene: `FS`, `SS`, `FF`.
El feature doc menciona `SF` (Start-to-Finish) — **NO agregar en MVP**.
SF es inusual en construcción civil y añade complejidad al CPM sin valor claro para el cliente.
Si se requiere en el futuro → DEC nueva + migración AddField.

---

*Generado: 27 Marzo 2026 — Phase 0 Feature #6*
