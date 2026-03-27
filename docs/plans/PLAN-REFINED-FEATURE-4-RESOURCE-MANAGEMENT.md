# PLAN REFINADO — Feature #4: Resource Management
**Proyecto:** SaiSuite — ValMen Tech
**Fecha:** 26 Marzo 2026
**Agentes consultados:** Backend Architect · UI Designer · Senior PM · Project Shepherd · Database Optimizer
**Estado:** Listo para desarrollo

---

## ⚠️ CAMBIOS RESPECTO AL PLAN INICIAL

| Aspecto | Plan inicial | Plan refinado | Agente |
|---|---|---|---|
| Estimación total | 6-8 días | **15 días** (120.5h reales) | Senior PM |
| Estimación mínima (optimista) | — | 10-11 días | Project Shepherd |
| Calendario frontend | FullCalendar (mencionado) | `mat-expansion-panel` por semana — 100% Angular Material | UI Designer |
| Charts | `p-chart` (PrimeNG — PROHIBIDO) | `ngx-charts` (`@swimlane/ngx-charts`) | UI Designer |
| Algoritmo conflictos | Loop Python día a día | 1 query SQL + Python loop en memoria | DB Optimizer |
| `detect_overallocation` | Simple suma | `generate_series` PostgreSQL (escala a 365d) | Backend Architect |
| ResourceAssignment FK user | CASCADE | **PROTECT** — preservar histórico | Backend Architect |
| ResourceAvailability | Solo `aprobado: bool` | + `aprobado_por FK` + `fecha_aprobacion` | Backend Architect |
| Solapamiento en BD | No contemplado | `ExclusionConstraint` + extensión `btree_gist` | DB Optimizer |

> **Nota crítica:** El plan original mencionaba PrimeNG (`p-selectButton`, `p-chart`, `p-calendar`). PrimeNG está **explícitamente prohibido** en CLAUDE.md (DEC-011). Todos los componentes usan Angular Material.

---

## DECISIÓN PENDIENTE — Antes del Día 1

**DEC-023 (requiere respuesta antes de codificar BK-13):**

¿Cuál es la definición de "sobreasignación"?

| Opción | Descripción | Impacto |
|---|---|---|
| **A — Diaria** | Sobreasignado si suma de % en **cualquier día** supera 100% | Más estricta, más conflictos reportados |
| **B — Semanal** | Sobreasignado si promedio semanal supera 100% | Más flexible, común en herramientas PM |

Esta decisión impacta directamente `BK-13` y los ~20 tests de `BK-27`. Documentar en `DECISIONS.md`.

---

## 1. MODELOS DJANGO — CÓDIGO VALIDADO

### AvailabilityType

```python
class AvailabilityType(models.TextChoices):
    VACATION   = 'vacation',   'Vacaciones'
    SICK_LEAVE = 'sick_leave', 'Incapacidad'
    HOLIDAY    = 'holiday',    'Festivo'
    TRAINING   = 'training',   'Capacitación'
    OTHER      = 'other',      'Otro'
```

### ResourceAssignment

```python
class ResourceAssignment(BaseModel):
    """
    Asignación formal de un usuario a una tarea con porcentaje de dedicación.
    unique_together (company, task, user): un usuario solo tiene una asignación
    activa por tarea. Extensible con campo 'rol' en Feature #5 si se requiere.
    FK user → PROTECT: nunca eliminar usuario con asignaciones (preservar histórico).
    """
    task = models.ForeignKey('Task', on_delete=models.CASCADE,
                              related_name='resource_assignments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                              related_name='resource_assignments')
    porcentaje_asignacion = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('100.00'))],
        help_text='Fracción de la capacidad semanal del usuario (0.01–100).',
    )
    fecha_inicio = models.DateField()
    fecha_fin    = models.DateField()
    notas        = models.TextField(blank=True)
    activo       = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name        = 'Asignación de recurso'
        verbose_name_plural = 'Asignaciones de recursos'
        ordering            = ['fecha_inicio', 'user']
        unique_together     = [('company', 'task', 'user')]
        indexes = [
            models.Index(fields=['company', 'user', 'fecha_inicio', 'fecha_fin'],
                         name='idx_rassign_company_user_dates'),
            models.Index(fields=['task', 'fecha_inicio', 'fecha_fin'],
                         name='idx_rassign_task_dates'),
            models.Index(fields=['user', 'activo'],
                         name='idx_rassign_user_activo'),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(fecha_fin__gte=models.F('fecha_inicio')),
                name='ck_rassign_fecha_fin_gte_inicio',
            ),
        ]
```

### ResourceCapacity

```python
class ResourceCapacity(BaseModel):
    """
    Capacidad laboral semanal de un usuario para un período.
    fecha_fin=None = capacidad indefinida.
    Solapamientos de períodos validados en ResourceCapacityService (no unique_together).
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='resource_capacities')
    horas_por_semana = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('168.00'))],
    )
    fecha_inicio = models.DateField()
    fecha_fin    = models.DateField(null=True, blank=True,
                                    help_text='Dejar vacío para capacidad indefinida.')
    activo       = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name        = 'Capacidad de recurso'
        verbose_name_plural = 'Capacidades de recursos'
        ordering            = ['user', 'fecha_inicio']
        indexes = [
            models.Index(fields=['company', 'user', 'activo', 'fecha_inicio'],
                         name='idx_rcap_company_user_active_start'),
            models.Index(fields=['company', 'user'],
                         name='idx_rcap_open_ended',
                         condition=Q(fecha_fin__isnull=True)),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(fecha_fin__isnull=True) | Q(fecha_fin__gt=models.F('fecha_inicio')),
                name='ck_rcap_fecha_fin_gt_inicio',
            ),
            models.CheckConstraint(check=Q(horas_por_semana__gt=0),
                                   name='ck_rcap_horas_positivas'),
        ]
```

### ResourceAvailability

```python
class ResourceAvailability(BaseModel):
    """
    Ausencia o indisponibilidad de un usuario.
    Solo ausencias con aprobado=True se descuentan de la capacidad efectiva.
    Solapamientos del mismo tipo validados en servicio (ExclusionConstraint en BD).
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='resource_availabilities')
    tipo         = models.CharField(max_length=20, choices=AvailabilityType.choices)
    fecha_inicio = models.DateField()
    fecha_fin    = models.DateField()
    descripcion  = models.TextField(blank=True)
    aprobado         = models.BooleanField(default=False, db_index=True)
    aprobado_por     = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='approved_absences',
    )
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name        = 'Disponibilidad de recurso'
        verbose_name_plural = 'Disponibilidades de recursos'
        ordering            = ['fecha_inicio', 'user']
        indexes = [
            models.Index(fields=['company', 'user', 'aprobado', 'fecha_inicio', 'fecha_fin'],
                         name='idx_ravail_company_user_aprobado_dates'),
            models.Index(fields=['company', 'aprobado'],
                         name='idx_ravail_company_aprobado'),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(fecha_fin__gte=models.F('fecha_inicio')),
                name='ck_ravail_fecha_fin_gte_inicio',
            ),
        ]
```

### Migración 0014 — Puntos críticos

```python
# migrations/0014_resource_management.py
from django.contrib.postgres.operations import BtreeGistExtension

class Migration(migrations.Migration):
    atomic = False  # Requerido para ExclusionConstraint con btree_gist

    operations = [
        BtreeGistExtension(),  # Idempotente — no falla si ya existe
        migrations.CreateModel('ResourceAssignment', ...),
        migrations.CreateModel('ResourceCapacity', ...),
        migrations.CreateModel('ResourceAvailability', ...),
        # RunPython para crear ResourceCapacity default (40h/semana)
        # para todos los usuarios existentes de cada empresa
        migrations.RunPython(
            code=crear_capacidad_default,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
```

> **⚠️ En AWS RDS/Aurora:** `BtreeGistExtension` requiere superuser. Ejecutar manualmente antes del deploy si el user de BD no tiene permisos:
> `CREATE EXTENSION IF NOT EXISTS btree_gist;`

---

## 2. ALGORITMOS DE SERVICIO

### detect_overallocation_conflicts

**Estrategia aprobada:** 1 SQL query con overlap filter + Python loop en memoria.

```python
def detect_overallocation_conflicts(user_id, company_id, start_date, end_date,
                                     threshold=Decimal('100.00')):
    """
    1 query trae todos los assignments que solapan el período.
    Python itera en memoria por día (O(assignments × días) — negligible para ~100 assignments).
    Para escalar a >500 assignments: migrar a generate_series PostgreSQL (documentado aparte).
    """
    assignments = ResourceAssignment.objects.filter(
        company_id=company_id, user_id=user_id, activo=True,
        fecha_inicio__lte=end_date, fecha_fin__gte=start_date,
    ).values('id', 'task_id', 'task__nombre', 'porcentaje_asignacion',
             'fecha_inicio', 'fecha_fin')

    # Construir mapa fecha → assignments activos
    date_map: dict[date, list] = {}
    current = start_date
    while current <= end_date:
        date_map[current] = []
        current += timedelta(days=1)

    for a in assignments:
        eff_start = max(a['fecha_inicio'], start_date)
        eff_end   = min(a['fecha_fin'], end_date)
        current   = eff_start
        while current <= eff_end:
            date_map[current].append(a)
            current += timedelta(days=1)

    return [
        {'fecha': d, 'porcentaje_total': sum(a['porcentaje_asignacion'] for a in day_a),
         'assignments': day_a}
        for d, day_a in date_map.items()
        if day_a and sum(a['porcentaje_asignacion'] for a in day_a) > threshold
    ]
```

### calculate_user_workload — 3 queries independientes

```python
# Query 1: ResourceCapacity → horas disponibles (cálculo en Python para sub-períodos)
# Query 2: ResourceAssignment → horas asignadas (porcentaje × días laborales)
# Query 3: WorkSession aggregate → Sum('horas_totales') con Coalesce
# Resultado: UserWorkload(horas_capacidad, horas_asignadas, horas_registradas, %)
```

### get_team_availability_timeline — 3 queries totales (sin N+1)

```python
# Query 1: user_ids únicos con assignments en el proyecto + período
# Query 2+3: User.objects.filter(id__in=user_ids).prefetch_related(
#     Prefetch('resourceassignment_set', queryset=...filtrado..., to_attr='project_assignments'),
#     Prefetch('resourceavailability_set', queryset=...filtrado..., to_attr='period_availabilities'),
# )
```

---

## 3. WIREFRAMES Y ESPECIFICACIÓN UI

### Componente 1: ResourceAssignmentFormComponent (Modal)

**Componentes AM:** `MatDialog`, `MatAutocomplete` (usuario), `MatInput` (% numérico), `MatDatepicker` (fechas), `MatProgressBar` (carga existente), `MatSnackBar`

```
┌──────────────────────────────────────────────────────┐
│  Asignar recurso                                [X]  │
├──────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────┐     │
│  │ Usuario *                                ▼  │     │
│  └─────────────────────────────────────────────┘     │
│  ┌──────────────────┐  ┌────────────────────────┐    │
│  │ Dedicación (%) * │  │ Carga actual del usuario│    │
│  │   [ 50     ]%    │  │ ██████░░░░  60%         │    │
│  └──────────────────┘  └────────────────────────┘    │
│  ┌──────────────────────────────────────────────┐    │
│  │  ⚠  Suma total: 110% — sobreasignado         │    │
│  └──────────────────────────────────────────────┘    │
│  ┌──────────────────┐  ┌────────────────────┐        │
│  │ Fecha inicio *   │  │ Fecha fin *         │        │
│  │ [📅 01/04/2026] │  │ [📅 30/04/2026]    │        │
│  └──────────────────┘  └────────────────────┘        │
│  ┌─────────────────────────────────────────────┐     │
│  │ Notas (opcional)                             │     │
│  └─────────────────────────────────────────────┘     │
│                      [Cancelar]  [Asignar recurso]   │
└──────────────────────────────────────────────────────┘
```

- Sobreasignación: advertencia visual (no bloqueo) con `raf-overassignment-warning` (naranja)
- Verificación en tiempo real: `combineLatest` + `debounceTime(400ms)` → `ResourceService.getWorkload()`
- `[min]="form.value.fecha_inicio"` en el segundo datepicker para evitar fechas inválidas

---

### Componente 2: ResourceCalendarComponent — Vista por semanas

**Decisión:** `mat-expansion-panel` por semana — 100% Angular Material, sin dependencia externa.

**Justificación vs FullCalendar:** El modelo de datos es por rangos de fechas (no eventos puntuales). La vista semanal con expansión es más fiel a la realidad y totalmente nativa.

```
┌─────────────────────────────────────────────────────────┐
│  Calendario de Ana García            [< Marzo 2026 >]   │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐    │
│  │ Semana 1 (2-8 Mar) — 2 asignaciones          ▼ │    │
│  ├─────────────────────────────────────────────────┤    │
│  │  ● Proyecto Alpha — Diseño UI    60% ████████░░ │    │
│  │    02/03 → 06/03                               │    │
│  │  ● Proyecto Beta — Revisión      30% █████░░░░░ │    │
│  │    03/03 → 08/03                               │    │
│  │  ─────────────────────────────────────────────  │    │
│  │  Carga semana: 90%  ████████████████░░  OK      │    │
│  └─────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Semana 2 (9-15 Mar) — 0 asignaciones         ─ │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

- Color coding: array de colores `var(--sc-*)` asignado por `proyecto_id` (cíclico)
- Ausencias: icono `beach_access` en header de semana + fila especial en el panel
- **Componentes AM:** `MatExpansionModule`, `MatProgressBarModule`, `MatChipModule`, `MatTooltipModule`

---

### Componente 3: TeamCalendarComponent — Timeline de equipo

**Decisión:** `mat-table` con columnas dinámicas + sticky columns CSS. Sin dependencia externa.

```
┌──────────────┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──────────┐
│  Recurso     │02│03│04│05│06│07│08│09│10│11│ Carga    │
│  (sticky)    │Lu│Ma│Mi│Ju│Vi│Sa│Do│Lu│Ma│Mi│ (sticky) │
├──────────────┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──────────┤
│ Ana García   │██│██│██│██│██│  │  │██│██│██│  60%  OK │
├──────────────┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──────────┤
│ Carlos Ruiz  │██│██│██│██│  │  │  │  │  │██│  85%  ⚠  │
│              │85│85│85│85│  │  │  │  │  │85│          │
├──────────────┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──────────┤
│ Pedro Salas  │🏖│🏖│🏖│🏖│🏖│  │  │  │  │  │ Vacac.  │
└──────────────┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──────────┘
```

- Rango visible: 2 semanas por defecto, navegación con botones
- Columna recurso y columna carga: `position: sticky` (primera y última)
- `.tc-cell--over` (rojo tenue) si >100%, `.tc-cell--warn` (naranja) si 80-100%
- `.tc-cell--absence` (gris sutil) + icono `beach_access` para vacaciones
- **Componentes AM:** `MatTableModule`, `MatIconModule`, `MatTooltipModule`, `MatProgressBarModule`

---

### Componente 4: WorkloadChartComponent — Gráfico de barras

**Decisión:** `ngx-charts` (`@swimlane/ngx-charts`) — API Angular nativa, ~90KB gzip.

```bash
npm install @swimlane/ngx-charts
```

```
│  200h ─
│  160h ─  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  (capacidad máx — referencia)
│  120h ─    ███
│       │    ███ ▓▓▓
│   80h ─    ███ ▓▓▓ ░░░
│   40h ─    ███ ▓▓▓ ░░░
│    0h ─────────────────────
│           Sem 1  Sem 2  Sem 3
│
│ ███ Capacidad   ▓▓▓ Asignadas   ░░░ Registradas
```

- Componente: `ngx-charts-bar-vertical-2d`
- Colores: `{ Capacidad: '#e3f2fd', Asignadas: '#1565c0', Registradas: '#2e7d32' }`
- Responsive: `[view]` calculado con `ResizeObserver`
- Dark mode: `colorScheme` signal que cambia con `ThemeService.isDark()`

---

### Componente 5: Tab "Recursos" en TareaDetail

**Integración:** `<ng-template matTabContent>` (lazy) dentro del `mat-tab-group` existente.

```
┌─────────────────────────────────────────────────────┐
│  Recursos  [3]                [+ Asignar recurso]    │
├─────────────────────────────────────────────────────┤
│  A  Ana García     60%  ████████████░░  OK          │
│     01/03 → 30/04                     [✏] [🗑]     │
├─────────────────────────────────────────────────────┤
│  C  Carlos Ruiz   110%  ████████████████  ⚠         │
│     ⚠ Sobreasignado en este período   [✏] [🗑]     │
└─────────────────────────────────────────────────────┘
```

- Estado vacío: `sc-empty-state` con icono `group_add` + botón "Asignar recurso"
- Sobreasignación: borde izquierdo `var(--sc-danger)`, `mat-progress-bar color="warn"`
- Confirmación de eliminación: `MatDialog` + `ConfirmDialogComponent`

---

## 4. TASK BREAKDOWN COMPLETO

### Resumen de estimaciones

| Categoría | Tareas | Horas |
|---|---|---|
| Backend — Modelos + migraciones (BK-1 a BK-5) | 5 | 8 h |
| Backend — Serializers (BK-6 a BK-10) | 5 | 8 h |
| Backend — Services (BK-11 a BK-18) | 8 | **27 h** |
| Backend — Views + URLs (BK-19 a BK-25) | 7 | 15.5 h |
| Backend — Tests (BK-26 a BK-28) | 3 | **16 h** |
| Frontend — Modelos + Servicios (FE-1 a FE-3) | 3 | 5.5 h |
| Frontend — Componentes (FE-4 a FE-10) | 7 | **31.5 h** |
| Integraciones (IT-1 a IT-3) | 3 | 7.5 h |
| Documentación (DOC-1 a DOC-3) | 3 | 1.5 h |
| **TOTAL** | **44** | **120.5 h = 15 días** |

### Tabla de tareas (BK = Backend, FE = Frontend, IT = Integración)

| ID | Nombre | Horas | Depende de | Riesgo |
|---|---|---|---|---|
| BK-1 | Modelo `ResourceAssignment` | 2 | — | Bajo |
| BK-2 | Modelo `ResourceCapacity` | 1.5 | — | Bajo |
| BK-3 | Modelo `ResourceAvailability` + `AvailabilityType` | 2 | — | Bajo |
| BK-4 | Migración `0014_resource_models` + `RunPython` capacidad default | 1 | BK-1,2,3 | Medio |
| BK-5 | Django Admin para 3 modelos | 1.5 | BK-4 | Bajo |
| BK-6 | Serializers `ResourceAssignment` (lista + detalle) | 2 | BK-4 | Bajo |
| BK-7 | Serializers `ResourceCapacity` | 1 | BK-4 | Bajo |
| BK-8 | Serializers `ResourceAvailability` | 1.5 | BK-4 | Bajo |
| BK-9 | `WorkloadSummarySerializer` (datos calculados) | 2 | BK-6,7 | Medio |
| BK-10 | `TeamAvailabilitySerializer` (estructura anidada) | 1.5 | BK-8 | Medio |
| BK-11 | `assign_resource_to_task()` + validación solapamiento | 4 | BK-4 | Medio |
| BK-12 | `remove_resource_from_task()` (soft delete) | 1.5 | BK-11 | Bajo |
| BK-13 | `detect_overallocation_conflicts()` — TDD primero | 5 | BK-11 | **Alto** |
| BK-14 | `calculate_user_workload()` — cruce 3 fuentes de datos | 6 | BK-11,7 | **Alto** |
| BK-15 | `get_team_availability_timeline()` — 3 queries sin N+1 | 4 | BK-13,14 | Medio |
| BK-16 | `set_user_capacity()` + `validate_no_overlap()` | 3 | BK-4 | Medio |
| BK-17 | `register_availability()` + validación solapamiento mismo tipo | 2 | BK-4 | Bajo |
| BK-18 | `approve_availability()` — sets `aprobado_por` + `fecha_aprobacion` | 1.5 | BK-17 | Bajo |
| BK-19 | `ResourceAssignmentViewSet` (anidado en task) | 2.5 | BK-6,11,12 | Bajo |
| BK-20 | `ResourceCapacityViewSet` (anidado en user) | 2 | BK-7,16 | Bajo |
| BK-21 | `ResourceAvailabilityViewSet` + action `approve/` | 2.5 | BK-8,17,18 | Bajo |
| BK-22 | `WorkloadView` GET `/users/{id}/workload-summary/` | 2 | BK-9,14 | Medio |
| BK-23 | `TeamAvailabilityView` GET `/projects/{id}/team-availability/` | 2 | BK-10,15 | Medio |
| BK-24 | `UserCalendarView` GET `/users/{id}/calendar-data/` | 3 | BK-8,11 | Medio |
| BK-25 | Actualizar `urls.py` con todas las rutas nuevas | 1.5 | BK-19..24 | Bajo |
| BK-26 | `test_resource_models.py` — modelos, `clean()`, constraints | 3 | BK-4 | Bajo |
| BK-27 | `test_resource_services.py` — cobertura ≥85% | 8 | BK-18 | **Alto** |
| BK-28 | `test_resource_views.py` — endpoints, permisos, multi-tenant | 5 | BK-25 | Medio |
| FE-1 | Interfaces TS: 3 modelos base | 1.5 | BK-6,7,8 | Bajo |
| FE-2 | Interfaces TS: `WorkloadSummary`, `TeamAvailabilityEntry` | 1 | BK-9,10 | Bajo |
| FE-3 | `ResourceService` — todos los endpoints tipados | 3 | FE-1,2 | Bajo |
| FE-4 | `ResourceAssignmentFormComponent` — modal completo | 4 | FE-3 | Medio |
| FE-5 | `ResourceAvailabilityFormComponent` | 3 | FE-3 | Bajo |
| FE-6 | `UserCapacityFormComponent` | 2.5 | FE-3 | Bajo |
| FE-7 | `WorkloadChartComponent` con ngx-charts | 5 | FE-3 | **Alto** |
| FE-8 | `ResourceCalendarComponent` — expansión por semana | 6 | FE-3 | **Alto** |
| FE-9 | `TeamCalendarComponent` — mat-table columnas dinámicas | 7 | FE-3,8 | **Alto** |
| FE-10 | `ResourceDashboardComponent` — container orquestador | 4 | FE-4..9 | Medio |
| IT-1 | Tab "Recursos" en `TareaDetailComponent` (lazy matTabContent) | 2.5 | FE-4,3 | Bajo |
| IT-2 | Avatares de asignados en `GanttViewComponent` | 3 | FE-1 | **Medio** |
| IT-3 | Tab "Equipo" en `ProyectoDetailComponent` | 2 | FE-9,10 | Bajo |
| DOC-1 | Actualizar `CONTEXT.md` | 0.5 | IT-3 | Bajo |
| DOC-2 | Entrada en `DECISIONS.md` (DEC-023+) | 0.5 | IT-3 | Bajo |
| DOC-3 | Actualizar `ERRORS.md` con errores del desarrollo | 0.5 | IT-3 | Bajo |

---

## 5. MAPA DE DEPENDENCIAS — CAMINO CRÍTICO

```
BK-1 ─┐
BK-2 ─┼→ BK-4 ─→ BK-11 ─→ BK-13 ─→ BK-14 ─→ BK-9 ─→ BK-22 ─→ FE-2 ─→ FE-3 ─→ FE-7 ─→ FE-10 ─→ IT-3
BK-3 ─┘           └──────→ BK-12                │                              └──→ FE-8 ─→ FE-9 ─┘
                            └──────→ BK-15 ──────┘
                   BK-16 ─→ BK-20
                   BK-17 ─→ BK-18 ─→ BK-21
                   BK-25 ─→ BK-26, BK-27, BK-28
                   BK-28 ─→ FE-1 ─→ FE-3 ─→ FE-4 ─→ IT-1
                                              └──→ IT-2 (riesgo: frappe-gantt hooks)
```

**Camino crítico:** `BK-4 → BK-11 → BK-13 → BK-14 → BK-9 → FE-3 → FE-8 → FE-9 → IT-3`

---

## 6. RIESGOS Y MITIGACIONES

| # | Riesgo | Prob. | Impacto | Señal de alerta | Mitigación |
|---|---|---|---|---|---|
| R-1 | BK-13 más complejo de lo esperado (algoritmo conflictos) | Alta | Alto | Fin día 3: no hay 5 escenarios con tests pasando | TDD obligatorio — escribir tests ANTES de implementar. Acordar DEC-023 antes del día 1 |
| R-2 | FE-8/FE-9 calendarios se expanden a 12h+ | Alta | Alto | Fin día 12: `ResourceCalendarComponent` no renderiza datos reales | Implementar versión mínima primero (tabla simple), pulir después |
| R-3 | IT-2 frappe-gantt no expone hooks de render | Media | Medio | 1h de investigación: no hay API de customización | Si no hay hooks → IT-2 es CSS overlay (3h máx). Si tampoco funciona → marcar como "próxima iteración" |
| R-4 | BK-14 workload inconsistente en semanas parciales | Media | Alto | Tests con mes que empieza en miércoles fallan | Definir unidad de cálculo = **semana ISO** (L-D). Documentar en docstring |
| R-5 | BK-27 cobertura 85% difícil para algoritmos de fecha | Alta | Medio | Cobertura <70% al finalizar BK-27 | Escribir tests en paralelo con services (no al final) |

---

## 7. HANDOFFS

### Handoff Backend → Frontend (Fin Día 8)

**Backend entrega:**
- Todos los endpoints funcionando en `localhost:8000`
- Colección Postman exportada: `docs/postman/feature4-resources.json`
- Archivo `frontend/src/app/features/proyectos/models/resource.types.ts` con interfaces TS generadas a partir de los serializers

**Endpoints bloqueantes** (frontend no puede avanzar sin ellos):
- `GET /users/{id}/calendar-data/` — bloquea FE-8
- `GET /projects/{id}/team-availability/` — bloquea FE-9
- `GET /projects/{id}/resource-conflicts/` — bloquea indicadores de sobreasignación

**Endpoints mockeables** (frontend puede usar fixture JSON mientras tanto):
- `POST /tasks/{id}/resource-assignments/` — FE-4 puede mockear con delay 500ms
- `GET /users/{id}/workload-summary/` — FE-7 puede usar datos ficticios

### Handoff Frontend → Testing (Fin Día 14)

**Criterios obligatorios (todos):**
1. Los 8 componentes renderizan sin errores con datos reales
2. Flujo completo "asignar → ver conflicto → resolver" navegable sin crashes
3. Los 375 tests backend existentes siguen pasando
4. No hay `console.error` en el flujo crítico
5. IT-1 (tab Recursos en TareaDetail) funciona end-to-end

### Handoff Final → Main

**Backend:**
- [ ] `python manage.py test` 100% (incluyendo nuevos)
- [ ] Cobertura `resource_services.py` ≥ 85% medida con `coverage.py`
- [ ] Migración `0014` probada en staging
- [ ] 0 queries N+1 verificadas con django-debug-toolbar
- [ ] Multi-tenant: ningún endpoint retorna datos cross-company

**Frontend:**
- [ ] `ng build --configuration=production` sin errores
- [ ] `ng test --watch=false` 100%
- [ ] `ng lint` 0 errores (0 `any`, 0 `*ngIf`)
- [ ] IT-1, IT-2, IT-3 probadas manualmente en staging

**Infraestructura:**
- [ ] Solo tablas nuevas — 0 migración de datos destructiva
- [ ] `ResourceCapacity` default creado para todos los usuarios existentes (migration `RunPython`)
- [ ] `BtreeGistExtension` aplicada antes del deploy

---

## 8. TIMELINE SEMANAL

### Semana 1 (Días 1–5) — Backend core

| Día | Tareas | Resultado |
|---|---|---|
| 1 | BK-1, BK-2, BK-3, BK-4, inicio BK-5 | Modelos en BD, migración aplicada |
| 2 | BK-5, BK-6, BK-7, BK-8, BK-11 | Serializers + primera función de service |
| **3** ⚠️ | BK-12, **BK-13** (TDD), BK-26 | Detección de conflictos con tests — día más crítico |
| 4 | BK-16, BK-17, BK-18, BK-9, BK-10 | Services de capacidad y disponibilidad |
| **5** | **BK-14**, BK-15 | Cálculo de workload — segunda tarea de alto riesgo |

> Si el Día 3 se atrasa → el Día 4 absorbe BK-13. Aceptable si BK-14 no sufre.

### Semana 2 (Días 6–10) — Views, tests, inicio frontend

| Día | Tareas | Resultado |
|---|---|---|
| 6 | BK-19, BK-20, BK-21, BK-25 | **Demo de API completa con Postman** |
| 7 | BK-22, BK-23, BK-24, inicio BK-27 | API completa |
| 8 | BK-27 (completar), inicio BK-28 | Backend testeado. **Gate de handoff** |
| 9 | BK-28, FE-1, FE-2, FE-3 | Backend certificado + ResourceService Angular listo |
| 10 | FE-4, FE-5, FE-6, IT-1 | Formularios + **Demo parcial UI desde TareaDetail** |

### Semana 3 (Días 11–15) — Componentes visuales y cierre

| Día | Tareas | Resultado |
|---|---|---|
| 11 | FE-7, FE-10 | WorkloadChart + Dashboard container |
| **12** | **FE-8** | ResourceCalendar por semanas |
| **13** | **FE-9** | TeamCalendar con mat-table dinámico |
| 14 | IT-2, IT-3, bug fixes visuales | Integraciones + **Demo final completa** |
| 15 | Tests frontend, DOC-1/2/3, review final | Feature lista para PR |

---

## 9. DEFINICIÓN DE DONE (MVP vs Producción)

### Criterios mínimos para demo al cliente (Día 10)
1. Se puede asignar un usuario a una tarea con % y fechas
2. El sistema muestra indicador visual si el recurso está sobreasignado
3. El calendario de un recurso muestra sus asignaciones actuales

### Criterios para merge a producción (Día 15)
- Todos los ítems del Handoff Final (sección 7)
- `DECISIONS.md` con DEC-023 documentada
- `CONTEXT.md` actualizado con estado de Feature #4

---

## 10. ARCHIVOS A CREAR

### Backend (en `backend/apps/proyectos/`)
```
models.py           ← agregar los 3 modelos + AvailabilityType al final
resource_services.py  ← NUEVO — ResourceService con todas las funciones
serializers.py      ← agregar serializers de resources
views.py            ← agregar ViewSets y Views de resources
urls.py             ← registrar nuevas rutas
migrations/
  0014_resource_models.py  ← NUEVO
tests/
  test_resource_models.py   ← NUEVO
  test_resource_services.py ← NUEVO
  test_resource_views.py    ← NUEVO
```

### Frontend (en `frontend/src/app/features/proyectos/`)
```
models/
  resource.types.ts           ← NUEVO (interfaces TS)
services/
  resource.service.ts         ← NUEVO
components/
  resource-assignment-form/   ← NUEVO (modal)
  resource-calendar/          ← NUEVO (expansión por semana)
  team-calendar/              ← NUEVO (mat-table dinámico)
  workload-chart/             ← NUEVO (ngx-charts)
  resource-availability-form/ ← NUEVO
  user-capacity-form/         ← NUEVO
  resource-dashboard/         ← NUEVO (container)
```

### Modificaciones a archivos existentes
```
tarea-detail.component.ts/html    ← IT-1: nueva tab Recursos
gantt-view.component.ts/html      ← IT-2: avatares (si frappe-gantt permite)
proyecto-detail.component.ts/html ← IT-3: nueva tab Equipo
docs/DECISIONS.md                 ← DEC-023 (definición sobreasignación)
docs/CONTEXT.md                   ← estado Feature #4
package.json                      ← @swimlane/ngx-charts
```

---

*Plan refinado por: Backend Architect + UI Designer + Senior PM + Project Shepherd + Database Optimizer*
*Fecha: 26 Marzo 2026 — SaiSuite v2.0+*
