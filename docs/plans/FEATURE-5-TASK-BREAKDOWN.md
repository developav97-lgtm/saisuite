# Feature #5: Reporting & Analytics — Task Breakdown
**Proyecto:** SaiSuite — ValMen Tech
**Fecha:** 27 Marzo 2026
**Autor:** SeniorProjectManager Agent
**Estado:** Listo para planificación de sprint

---

## Resumen Ejecutivo

Feature #5 añade capacidades de reporting y analytics sobre los datos de Projects, Tasks, Timesheets y Resources ya disponibles. No requiere modelos nuevos para el MVP — los datos existen, solo hay que agregarlos, graficarlos y exportarlos. El riesgo principal es la complejidad del frontend con Chart.js y la exportación PDF/Excel desde Django.

**Estimación total:** 18–22 días calendario (equipo de 1 desarrollador)
**Complejidad global:** XL

---

## 1. Analisis de Dependencias con Features Existentes

### 1.1 Datos disponibles por modelo

#### Project
Campos relevantes para analytics:
- `estado` — distribución de proyectos por estado (draft/planned/in_progress/suspended/closed/cancelled)
- `tipo` — distribución por tipo (civil_works/consulting/manufacturing/etc.)
- `presupuesto_total` — presupuesto planificado
- `porcentaje_administracion`, `porcentaje_imprevistos`, `porcentaje_utilidad` — cálculo de AIU
- `porcentaje_avance` — avance físico calculado automáticamente por signals
- `fecha_inicio_planificada`, `fecha_fin_planificada` — línea base
- `fecha_inicio_real`, `fecha_fin_real` — fechas reales (desviación de cronograma)
- `gerente`, `coordinador` — rendimiento por responsable

#### Phase
- `estado` — distribución planned/active/completed/cancelled
- `porcentaje_avance` — avance por fase
- `presupuesto_mano_obra`, `presupuesto_materiales`, `presupuesto_subcontratos`, `presupuesto_equipos`, `presupuesto_otros` — burn-down por categoría
- `fecha_inicio_planificada`, `fecha_fin_planificada` vs reales — desviación por fase
- `orden` — secuencia temporal de fases

#### Task
- `estado` — distribución todo/in_progress/in_review/blocked/completed/cancelled
- `prioridad` — distribución 1-4
- `horas_estimadas`, `horas_registradas` — eficiencia de estimación (ratio real/estimado)
- `fecha_limite` vs `created_at` + estado — tareas vencidas
- `porcentaje_completado` — throughput
- `responsable` — carga por usuario
- `tags` — distribución por etiqueta
- `fecha_inicio`, `fecha_fin` — duración real de tareas

#### TimesheetEntry
- `fecha`, `horas`, `usuario`, `tarea` — horas registradas por día/semana/mes
- `validado` — ratio de horas validadas vs pendientes
- Joined con Task.fase y Task.proyecto — horas por proyecto/fase

#### WorkSession
- `duracion_segundos`, `inicio`, `fin`, `usuario`, `tarea` — horas cronometradas vs manuales
- `estado` — sesiones activas en tiempo real

#### ResourceAssignment
- `porcentaje_asignacion`, `fecha_inicio`, `fecha_fin`, `usuario` — carga asignada
- Joined con Task y Project — utilización de recursos por proyecto

#### ResourceCapacity
- `horas_semana`, `fecha_inicio`, `fecha_fin` — capacidad disponible por usuario

#### ResourceAvailability
- `tipo_ausencia`, `fecha_inicio`, `fecha_fin` — ausencias que reducen disponibilidad real

### 1.2 Endpoints existentes reutilizables

| Endpoint | Uso en Analytics |
|---|---|
| `GET /api/v1/projects/` | Lista proyectos con estado/avance para overview |
| `GET /api/v1/projects/{id}/` | KPIs de proyecto individual |
| `GET /api/v1/projects/{id}/phases/` | Avance por fase |
| `GET /api/v1/projects/{id}/financial-status/` | Estado financiero (si implementado) |
| `GET /api/v1/projects/tasks/` | Distribución de tareas con filtros |
| `GET /api/v1/projects/timesheets/` | Horas registradas por período |
| `GET /api/v1/projects/resources/workload/` | Workload actual (Feature #4) |
| `GET /api/v1/projects/resources/calendar/` | Calendario de usuario (Feature #4) |
| `GET /api/v1/projects/{id}/team-availability/` | Disponibilidad del equipo |

**Nota crítica:** La mayoría de los endpoints existentes retornan datos crudos sin agregar. Feature #5 requiere endpoints de agregación nuevos en `analytics_services.py`.

### 1.3 Gaps identificados

1. No existe endpoint que agregue horas por semana/mes (necesario para BurnDown)
2. No existe endpoint de comparativa multi-proyecto (necesario para OverviewDashboard)
3. No existe endpoint de velocity de tareas completadas por sprint/semana
4. No existe exportación de ningún tipo
5. No existe `DashboardConfig` para guardar preferencias de usuario
6. El `financial-status` endpoint no está confirmado como implementado (verificar en views.py)

---

## 2. Epicas y Tareas Ejecutables

---

### EPIC 1: Backend Analytics Services

**Estimacion:** 5–6 dias
**Complejidad:** L
**Prerequisito:** Ninguno (datos ya existen en BD)

#### BK-AN-01: `analytics_services.py` — Metricas de proyecto individual

**Descripcion:** Crear `backend/apps/proyectos/analytics_services.py` con las siguientes funciones de agregacion puras. TODA la logica va aqui, nunca en views.

**Funciones a implementar:**

```python
def get_project_kpis(project_id: str, company_id: str) -> dict:
    """
    Retorna KPIs del proyecto:
    - total_tasks: int
    - tasks_by_status: dict[str, int]  # {todo: N, in_progress: N, ...}
    - completion_rate: float           # % tareas completadas
    - overdue_tasks: int               # tareas con fecha_limite < hoy y no completadas
    - total_hours_estimated: Decimal
    - total_hours_registered: Decimal
    - efficiency_ratio: float          # horas_registradas / horas_estimadas
    - phases_completed: int
    - phases_total: int
    - physical_progress: Decimal       # project.porcentaje_avance
    """

def get_hours_by_period(
    project_id: str,
    company_id: str,
    start_date: date,
    end_date: date,
    group_by: str = 'week',  # 'day' | 'week' | 'month'
) -> list[dict]:
    """
    Agrupa TimesheetEntry.horas por periodo.
    Retorna: [{"period": "2026-W12", "hours": 24.5, "users": 3}, ...]
    Usa TruncWeek / TruncMonth de django.db.models.functions.
    """

def get_task_velocity(
    project_id: str,
    company_id: str,
    weeks: int = 8,
) -> list[dict]:
    """
    Tareas completadas por semana (ultimas N semanas).
    Retorna: [{"week": "2026-W12", "completed": 5, "created": 8}, ...]
    Filtra por Task.estado = 'completed' y Task.updated_at para fecha de completado.
    """

def get_burndown_data(
    project_id: str,
    company_id: str,
) -> dict:
    """
    BurnDown basado en horas: ideal vs real vs restante.
    Retorna:
    {
      "ideal": [{"date": "...", "hours": N}, ...],  # linea recta desde total a 0
      "actual": [{"date": "...", "hours": N}, ...], # horas acumuladas de TimesheetEntry
      "remaining": [{"date": "...", "hours": N}, ...] # horas estimadas - registradas por fecha
    }
    """

def get_task_distribution(project_id: str, company_id: str) -> dict:
    """
    Distribucion de tareas por estado, prioridad y responsable.
    Retorna:
    {
      "by_status": {"todo": N, "in_progress": N, ...},
      "by_priority": {"low": N, "normal": N, "high": N, "urgent": N},
      "by_assignee": [{"user_id": "...", "name": "...", "task_count": N, "hours": N}, ...]
    }
    """
```

**Archivos a crear/editar:**
- `backend/apps/proyectos/analytics_services.py` (NUEVO)

**Acceptance Criteria:**
- Todas las funciones usan `select_related` o anotaciones Django ORM — ningun N+1 query
- Todas las funciones filtran por `company_id` (multi-tenant obligatorio)
- `get_hours_by_period` soporta los 3 modos: day, week, month
- `get_burndown_data` retorna datos desde `project.fecha_inicio_planificada` hasta hoy o `fecha_fin_planificada`
- Cada funcion esta documentada con types y docstring

**Referencia:** CLAUDE.md seccion 3 — "Lógica de negocio SOLO en services.py"

---

#### BK-AN-02: `analytics_services.py` — Metricas multi-proyecto (Overview)

**Descripcion:** Añadir funciones de comparativa multi-proyecto al mismo archivo.

**Funciones a implementar:**

```python
def get_portfolio_summary(company_id: str) -> dict:
    """
    Resumen del portafolio completo:
    - projects_by_status: dict[str, int]
    - projects_by_type: dict[str, int]
    - total_budget: Decimal
    - avg_physical_progress: float
    - projects_at_risk: int  # avance < esperado segun fechas
    - overdue_projects: int  # fecha_fin_planificada < hoy y no cerrados
    """

def get_resource_utilization_summary(
    company_id: str,
    start_date: date,
    end_date: date,
) -> list[dict]:
    """
    Utilizacion por usuario en el periodo.
    Retorna: [
      {
        "user_id": "...",
        "user_name": "...",
        "capacity_hours": N,        # ResourceCapacity.horas_semana * semanas
        "assigned_hours": N,        # suma de asignaciones (porcentaje * duracion)
        "registered_hours": N,      # TimesheetEntry.horas reales
        "utilization_rate": float,  # registered / capacity
      }, ...
    ]
    """

def get_projects_comparison(
    company_id: str,
    project_ids: list[str],
) -> list[dict]:
    """
    Comparativa de N proyectos seleccionados.
    Retorna lista de project KPIs para renderizar en grafico comparativo.
    """
```

**Archivos a editar:**
- `backend/apps/proyectos/analytics_services.py` (continuar desde BK-AN-01)

**Acceptance Criteria:**
- `get_portfolio_summary` corre en < 500ms para hasta 100 proyectos
- `get_resource_utilization_summary` combina datos de `ResourceCapacity`, `ResourceAssignment` y `TimesheetEntry`
- Todos los calculos de fechas usan `date` de Python (no `datetime`) para consistencia

---

#### BK-AN-03: Analytics Views y URLs

**Descripcion:** Crear views que orquesten los analytics services. Las views NO calculan nada — llaman al service y retornan la respuesta.

**Endpoints a crear:**

```
GET /api/v1/projects/{id}/analytics/kpis/
    Params: ninguno
    Response: ProjectKPIsSerializer

GET /api/v1/projects/{id}/analytics/hours/
    Params: start_date, end_date, group_by (day|week|month)
    Response: HoursByPeriodSerializer (lista)

GET /api/v1/projects/{id}/analytics/velocity/
    Params: weeks (default=8, max=52)
    Response: TaskVelocitySerializer (lista)

GET /api/v1/projects/{id}/analytics/burndown/
    Params: ninguno
    Response: BurndownSerializer

GET /api/v1/projects/{id}/analytics/task-distribution/
    Params: ninguno
    Response: TaskDistributionSerializer

GET /api/v1/projects/analytics/portfolio/
    Params: ninguno
    Response: PortfolioSummarySerializer

GET /api/v1/projects/analytics/resource-utilization/
    Params: start_date, end_date
    Response: ResourceUtilizationSerializer (lista)

GET /api/v1/projects/analytics/comparison/
    Params: project_ids (comma-separated UUIDs, max 5)
    Response: ProjectComparisonSerializer (lista)
```

**Archivos a crear/editar:**
- `backend/apps/proyectos/views.py` — añadir `ProjectAnalyticsView`, `PortfolioAnalyticsView`
- `backend/apps/proyectos/serializers.py` — añadir serializers de analytics (solo lectura, sin lógica)
- `backend/apps/proyectos/urls.py` — registrar nuevas URLs

**Acceptance Criteria:**
- Todos los endpoints requieren autenticacion JWT
- Filtran por `company` del usuario autenticado (ningun endpoint expone datos de otra empresa)
- Retornan 400 con mensaje claro si los parametros son invalidos
- `project_ids` en comparison acepta maximo 5 IDs (validado en serializer)
- Documentado en `docs/API-DOCS-UPDATED.md` (actualizar)

---

#### BK-AN-04: Tests de Analytics Backend

**Descripcion:** Tests para `analytics_services.py` y las views de analytics.

**Archivos a crear:**
- `backend/apps/proyectos/tests/test_analytics_services.py`
- `backend/apps/proyectos/tests/test_analytics_views.py`

**Casos de prueba minimos (services):**

```python
# test_analytics_services.py
class TestGetProjectKPIs:
    def test_kpis_empty_project_returns_zeros()
    def test_kpis_with_tasks_calculates_completion_rate()
    def test_kpis_overdue_count_excludes_completed_tasks()
    def test_kpis_filters_by_company_id()       # CRITICO: multi-tenant

class TestGetHoursByPeriod:
    def test_group_by_week_returns_correct_period_labels()
    def test_group_by_month_aggregates_correctly()
    def test_empty_period_returns_empty_list()
    def test_filters_by_project_and_company()

class TestGetTaskVelocity:
    def test_velocity_last_8_weeks()
    def test_velocity_with_no_completed_tasks_returns_zeros()

class TestGetBurndownData:
    def test_ideal_line_is_linear()
    def test_actual_matches_timesheet_entries()
    def test_project_with_no_timesheets_has_zero_actuals()

class TestGetPortfolioSummary:
    def test_counts_projects_by_status()
    def test_isolates_company_data()    # CRITICO: multi-tenant
```

**Cobertura minima:** 80% en `analytics_services.py` (regla CLAUDE.md)

---

#### BK-AN-05: Exportacion Backend (PDF y Excel)

**Descripcion:** Implementar servicios de exportacion. PDF via WeasyPrint (Django), Excel via openpyxl.

**Dependencias a instalar:**
```
pip install openpyxl WeasyPrint
```

**Funciones a implementar en `export_services.py` (archivo nuevo):**

```python
def export_project_report_excel(project_id: str, company_id: str) -> bytes:
    """
    Genera archivo .xlsx con:
    - Hoja 1: KPIs del proyecto
    - Hoja 2: Tareas (estado, responsable, horas estimadas/reales)
    - Hoja 3: Timesheets por semana
    - Hoja 4: Fases y avance
    """

def export_project_report_pdf(project_id: str, company_id: str) -> bytes:
    """
    Genera reporte PDF con logo, KPIs, graficos de texto (no Chart.js — WeasyPrint es server-side).
    Template: backend/templates/reports/project_report.html
    """

def export_portfolio_excel(company_id: str) -> bytes:
    """
    Exporta comparativa de todos los proyectos activos en una sola hoja.
    """
```

**Endpoints a crear:**
```
GET /api/v1/projects/{id}/analytics/export/excel/
    Response: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet

GET /api/v1/projects/{id}/analytics/export/pdf/
    Response: application/pdf

GET /api/v1/projects/analytics/export/portfolio/excel/
    Response: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
```

**Archivos a crear:**
- `backend/apps/proyectos/export_services.py`
- `backend/templates/reports/project_report.html`
- `backend/templates/reports/base_report.html`

**Acceptance Criteria:**
- Excel descargable con nombre `proyecto-{codigo}-reporte-{fecha}.xlsx`
- PDF con header ValMen Tech y datos del proyecto
- Ambos formatos incluyen datos filtrados por `company_id`
- Archivos generados en memoria (no persistidos en disco)

**Nota de riesgo:** WeasyPrint tiene dependencias del sistema (libcairo, libpango). Verificar compatibilidad con el entorno de desarrollo antes de comprometer esta opcion. Si hay problemas, la alternativa es generar PDF desde el frontend con jsPDF (documentar en DECISIONS.md).

---

### EPIC 2: Angular — Chart.js Setup y Servicios

**Estimacion:** 3–4 dias
**Complejidad:** M
**Prerequisito:** Epic 1 (al menos BK-AN-01 y BK-AN-03 completados para tener endpoints reales)

#### FE-AN-01: Instalacion y configuracion de Chart.js

**Descripcion:** Instalar Chart.js directamente (sin wrapper) en el proyecto Angular. La decision de usar Chart.js nativo (no ng2-charts) se justifica por: control total sobre opciones, sin dependencia de wrapper que puede quedar desactualizado, y compatibilidad garantizada con signals de Angular 18.

**Referencia DECISIONS.md:** Documentar como DEC-026 antes de ejecutar.

**Comandos:**
```bash
npm install chart.js
```

**Archivos a crear:**
- `frontend/src/app/features/proyectos/services/chart-config.service.ts`
  - Configuracion global de Chart.js (defaults de colores corporativos ValMen Tech)
  - Paleta: azul corporativo (`#1976d2`), variantes para multi-serie
  - Localizacion: formato de fechas en es-CO
  - Registrar los tipos de graficos necesarios: `LineController`, `BarController`, `DoughnutController`, `CategoryScale`, `LinearScale`, `TimeScale`, `Legend`, `Tooltip`

```typescript
// chart-config.service.ts (estructura esperada)
@Injectable({ providedIn: 'root' })
export class ChartConfigService {
  readonly corporatePalette: string[]  // azules y grises corporativos

  getLineChartDefaults(): ChartConfiguration<'line'>
  getBarChartDefaults(): ChartConfiguration<'bar'>
  getDoughnutChartDefaults(): ChartConfiguration<'doughnut'>
  buildTimeSeriesDataset(label: string, data: {x: string, y: number}[], color?: string): ChartDataset<'line'>
}
```

**Acceptance Criteria:**
- `chart.js` importado y registrado una vez en `chart-config.service.ts`
- No hay importaciones directas de Chart.js fuera de este servicio y de los componentes de graficos
- La paleta de colores usa `var(--sc-primary)` o el valor hexadecimal equivalente documentado en UI-UX-STANDARDS.md

---

#### FE-AN-02: Interfaces TypeScript para datos de analytics

**Descripcion:** Crear modelos TypeScript que espején exactamente los serializers de BK-AN-03. Ningun `any`.

**Archivo a crear:**
- `frontend/src/app/features/proyectos/models/analytics.model.ts`

**Interfaces requeridas:**
```typescript
export interface ProjectKPIs {
  total_tasks: number;
  tasks_by_status: Record<TaskStatus, number>;
  completion_rate: number;
  overdue_tasks: number;
  total_hours_estimated: string;   // Decimal llega como string desde DRF
  total_hours_registered: string;
  efficiency_ratio: number;
  phases_completed: number;
  phases_total: number;
  physical_progress: string;
}

export interface HoursByPeriod {
  period: string;     // "2026-W12" | "2026-03" | "2026-03-27"
  hours: number;
  users: number;
}

export interface TaskVelocityPoint {
  week: string;
  completed: number;
  created: number;
}

export interface BurndownData {
  ideal: Array<{ date: string; hours: number }>;
  actual: Array<{ date: string; hours: number }>;
  remaining: Array<{ date: string; hours: number }>;
}

export interface TaskDistribution {
  by_status: Record<TaskStatus, number>;
  by_priority: Record<'low' | 'normal' | 'high' | 'urgent', number>;
  by_assignee: Array<{
    user_id: string;
    name: string;
    task_count: number;
    hours: number;
  }>;
}

export interface PortfolioSummary {
  projects_by_status: Record<ProjectStatus, number>;
  projects_by_type: Record<string, number>;
  total_budget: string;
  avg_physical_progress: number;
  projects_at_risk: number;
  overdue_projects: number;
}

export interface ResourceUtilizationItem {
  user_id: string;
  user_name: string;
  capacity_hours: number;
  assigned_hours: number;
  registered_hours: number;
  utilization_rate: number;
}

export type GroupBy = 'day' | 'week' | 'month';
```

**Acceptance Criteria:**
- Ningun `any` — strict TypeScript
- Todos los campos de tipo Decimal de Django llegan como `string` (DRF default) — tipado correcto
- `TaskStatus` y `ProjectStatus` importados desde los modelos ya existentes (`tarea.model.ts`, `proyecto.model.ts`)

---

#### FE-AN-03: AnalyticsService

**Descripcion:** Servicio Angular que consume todos los endpoints de analytics. Un solo servicio para toda la feature.

**Archivo a crear:**
- `frontend/src/app/features/proyectos/services/analytics.service.ts`

**Metodos requeridos:**
```typescript
@Injectable({ providedIn: 'root' })
export class AnalyticsService {
  getProjectKPIs(projectId: string): Observable<ProjectKPIs>
  getHoursByPeriod(projectId: string, params: HoursPeriodParams): Observable<HoursByPeriod[]>
  getTaskVelocity(projectId: string, weeks?: number): Observable<TaskVelocityPoint[]>
  getBurndownData(projectId: string): Observable<BurndownData>
  getTaskDistribution(projectId: string): Observable<TaskDistribution>
  getPortfolioSummary(): Observable<PortfolioSummary>
  getResourceUtilization(params: UtilizationParams): Observable<ResourceUtilizationItem[]>
  exportProjectExcel(projectId: string): Observable<Blob>
  exportProjectPdf(projectId: string): Observable<Blob>
  exportPortfolioExcel(): Observable<Blob>
}
```

**Acceptance Criteria:**
- Usa `inject(HttpClient)` — no constructor injection
- Las exportaciones retornan `Observable<Blob>` con `responseType: 'blob'`
- Ningun `any` — tipado completo con las interfaces de FE-AN-02
- JWT se añade automaticamente via interceptor (no añadir headers manualmente)

---

### EPIC 3: Dashboard Components

**Estimacion:** 5–6 dias
**Complejidad:** L
**Prerequisito:** Epic 2 completado (FE-AN-01, FE-AN-02, FE-AN-03)

#### FE-AN-04: Componentes de graficos base (reutilizables)

**Descripcion:** 4 componentes presentacionales de graficos. Cada uno recibe datos via `input()` y renderiza el grafico. Sin logica de negocio, sin llamadas HTTP.

**Directorio:** `frontend/src/app/features/proyectos/components/charts/`

**Componentes a crear:**

**a) BurndownChartComponent**
```
Selector: app-burndown-chart
Input: data = input.required<BurndownData>()
Chart type: line (3 series: ideal, actual, remaining)
```

**b) VelocityChartComponent**
```
Selector: app-velocity-chart
Input: data = input.required<TaskVelocityPoint[]>()
Chart type: bar (2 series: completed, created)
```

**c) TaskDistributionChartComponent**
```
Selector: app-task-distribution-chart
Input: distribution = input.required<TaskDistribution>()
        mode = input<'status' | 'priority'>('status')
Chart type: doughnut
```

**d) ResourceUtilizationChartComponent**
```
Selector: app-resource-utilization-chart
Input: data = input.required<ResourceUtilizationItem[]>()
Chart type: bar horizontal (capacity vs registered)
```

**Patron de implementacion para TODOS los componentes de grafico:**
```typescript
@Component({
  selector: 'app-[nombre]-chart',
  template: `<canvas #chartCanvas></canvas>`,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class [Nombre]ChartComponent implements AfterViewInit, OnDestroy {
  private readonly chartConfig = inject(ChartConfigService);

  @ViewChild('chartCanvas') canvasRef!: ElementRef<HTMLCanvasElement>;
  private chart?: Chart;

  // Usar effect() de Angular para reaccionar a cambios en inputs

  ngOnDestroy(): void { this.chart?.destroy(); }
}
```

**Acceptance Criteria:**
- `ChangeDetectionStrategy.OnPush` en todos
- `chart.destroy()` en `ngOnDestroy` — sin memory leaks
- Graficos responsive (`maintainAspectRatio: false` + contenedor con altura fija en CSS)
- Colores de la paleta corporativa de `ChartConfigService`
- Ninguna llamada HTTP dentro del componente

---

#### FE-AN-05: KPI Cards Component

**Descripcion:** Componente de tarjetas de KPIs para el dashboard de proyecto individual.

**Archivo:** `frontend/src/app/features/proyectos/components/kpi-cards/kpi-cards.component.ts`

**Input:** `kpis = input.required<ProjectKPIs>()`

**Cards a mostrar (una `mat-card` por KPI):**
1. Avance fisico: `physical_progress`% — `mat-progress-bar`
2. Tareas completadas: `completion_rate`% — numero grande + denominador
3. Horas registradas vs estimadas: `total_hours_registered` / `total_hours_estimated`
4. Eficiencia: `efficiency_ratio` — badge color segun rango (verde >80%, amarillo 60-80%, rojo <60%)
5. Tareas vencidas: `overdue_tasks` — badge rojo si > 0
6. Fases completadas: `phases_completed` / `phases_total`

**Acceptance Criteria:**
- Usa `mat-card` de Angular Material
- Variables CSS `var(--sc-*)` para colores — ningun color hardcodeado
- Responsive: 3 columnas en desktop, 2 en tablet, 1 en mobile (CSS Grid)
- Avance fisico usa `mat-progress-bar` con `mode="determinate"`

---

#### FE-AN-06: ProjectDashboardComponent (Dashboard de proyecto individual)

**Descripcion:** Componente contenedor inteligente que orquesta KPIs + 4 graficos para un proyecto especifico. Este componente es el que se mostrara como tab "Analytics" en `proyecto-detail`.

**Archivo:** `frontend/src/app/features/proyectos/components/project-dashboard/project-dashboard.component.ts`

**Input:** `projectId = input.required<string>()`

**Layout:**
```
┌─────────────────────────────────────────────┐
│ KPI Cards (6 tarjetas en grid)              │
├─────────────────┬───────────────────────────┤
│ BurnDown Chart  │ Task Distribution (donut) │
├─────────────────┴───────────────────────────┤
│ Velocity Chart (ancho completo)             │
├─────────────────────────────────────────────┤
│ Filtro periodo: [semana|mes] [desde][hasta] │
│ Hours by Period Chart (barra)               │
└─────────────────────────────────────────────┘
```

**Estado del componente (signals):**
```typescript
readonly kpis = signal<ProjectKPIs | null>(null);
readonly burndown = signal<BurndownData | null>(null);
readonly velocity = signal<TaskVelocityPoint[]>([]);
readonly distribution = signal<TaskDistribution | null>(null);
readonly hoursByPeriod = signal<HoursByPeriod[]>([]);
readonly loading = signal(true);
readonly selectedPeriod = signal<GroupBy>('week');
```

**Acceptance Criteria:**
- `mat-progress-bar` encima del contenido durante carga (NUNCA spinner centrado)
- Carga paralela con `forkJoin` para KPIs + BurnDown + Velocity + Distribution
- `hours-by-period` se recarga cuando cambia `selectedPeriod` con `effect()`
- Todos los datos filtrados por `projectId` input
- Error handling: `MatSnackBar` con `panelClass: ['snack-error']`

---

#### FE-AN-07: OverviewDashboardComponent (Dashboard multi-proyecto)

**Descripcion:** Dashboard del portafolio completo. Vista independiente accesible desde el modulo de proyectos.

**Archivo:** `frontend/src/app/features/proyectos/components/overview-dashboard/overview-dashboard.component.ts`

**Ruta:** `/proyectos/analytics` (añadir a `proyectos.routes.ts`)

**Layout:**
```
┌─────────────────────────────────────────────┐
│ Portfolio Summary Cards                     │
│ (proyectos totales, en riesgo, vencidos)    │
├─────────────────┬───────────────────────────┤
│ Projects by     │ Projects by Type          │
│ Status (donut)  │ (donut)                   │
├─────────────────┴───────────────────────────┤
│ Resource Utilization Chart (barra por user) │
├─────────────────────────────────────────────┤
│ Projects Comparison Table (mat-table)       │
│ Selector multi-proyecto (max 5)             │
└─────────────────────────────────────────────┘
```

**Acceptance Criteria:**
- Lazy loaded desde `proyectos.routes.ts`
- `ChangeDetectionStrategy.OnPush`
- La tabla comparativa usa `mat-table` con los proyectos seleccionados
- Selector de proyectos usa `mat-select` con `multiple` (max 5, validado)
- `sc-empty-state` si no hay proyectos en el portafolio

---

### EPIC 4: Report Builder

**Estimacion:** 4–5 dias
**Complejidad:** L
**Prerequisito:** Epic 3 completado, Epic 1 BK-AN-05 completado

#### FE-AN-08: ReportBuilderComponent

**Descripcion:** Componente para configurar y previsualizar un reporte antes de exportar.

**Archivo:** `frontend/src/app/features/proyectos/components/report-builder/report-builder.component.ts`

**Ruta:** `/proyectos/:id/analytics/report` (nuevo)

**Secciones del formulario:**
```
1. Periodo del reporte: [fecha desde] [fecha hasta]
2. Secciones a incluir:
   [ ] KPIs generales
   [ ] Horas por periodo
   [ ] Distribucion de tareas
   [ ] Burndown
   [ ] Equipo (resource utilization)
3. Formato: [Excel] [PDF]
4. [Previsualizar] [Exportar]
```

**Acceptance Criteria:**
- Formulario usa `ReactiveFormsModule` con `FormBuilder`
- Campos de fecha con `mat-datepicker`
- Checkboxes con `mat-checkbox`
- Radio buttons con `mat-radio-group` para formato
- Boton "Previsualizar" muestra un resumen de datos (sin Chart.js — solo texto/tablas) en `mat-expansion-panel`
- Boton "Exportar" llama al endpoint correcto y descarga el archivo via `URL.createObjectURL()`
- Loading state en el boton de exportar (`mat-spinner` inline, no centrado)

---

#### FE-AN-09: Descarga de archivos desde Angular

**Descripcion:** Utilitario para manejar descarga de Blob (Excel/PDF) desde el servicio.

**Archivo a crear:**
- `frontend/src/app/shared/utils/file-download.util.ts`

```typescript
export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
```

**Acceptance Criteria:**
- `URL.revokeObjectURL` siempre llamado para evitar memory leaks
- Funcion pura, sin dependencias de Angular
- Tipado correcto (no `any`)

---

### EPIC 5: Integraciones en Componentes Existentes

**Estimacion:** 2–3 dias
**Complejidad:** M
**Prerequisito:** Epic 3 (FE-AN-06 completado), Epic 2

#### IT-AN-01: Tab "Analytics" en ProyectoDetailComponent

**Descripcion:** Añadir tab de analytics al detalle de proyecto existente.

**Archivo a editar:**
- `frontend/src/app/features/proyectos/components/proyecto-detail/proyecto-detail.component.ts`
- `frontend/src/app/features/proyectos/components/proyecto-detail/proyecto-detail.component.html`

**Cambios:**
1. Importar `ProjectDashboardComponent` en el array `imports`
2. Añadir tab `<mat-tab label="Analytics">` con `<app-project-dashboard [projectId]="proyecto()!.id" />`
3. El tab solo se muestra si `proyecto()` no es null

**Acceptance Criteria:**
- Tab aparece entre "Gantt" y el ultimo tab existente
- `ProjectDashboardComponent` recibe el `id` del proyecto actual
- No rompe ninguno de los tabs existentes (Fases, Terceros, Documentos, Hitos, Actividades, Gantt, Team)
- La carga del tab es lazy: `ProjectDashboardComponent` no inicia requests hasta que el tab esta activo (usar `@defer` de Angular 18 o condicional en `ngAfterViewInit`)

---

#### IT-AN-02: Metricas de tarea en TareaDetailComponent

**Descripcion:** Añadir seccion de metricas simples en el detalle de tarea individual.

**Archivo a editar:**
- `frontend/src/app/features/proyectos/components/tarea-detail/tarea-detail.component.ts`
- `frontend/src/app/features/proyectos/components/tarea-detail/tarea-detail.component.html`

**Metricas a mostrar (sin Chart.js — solo datos de texto/progress bar):**
- Horas estimadas vs registradas (`mat-progress-bar`)
- Numero de timesheets registrados
- Fecha de completado (si `estado === 'completed'`)
- Eficiencia: `horas_registradas / horas_estimadas` como badge

**Datos disponibles:** Los campos `horas_estimadas` y `horas_registradas` ya estan en el modelo `Task`. No se necesita llamada adicional — usar los datos ya cargados en `tarea-detail`.

**Acceptance Criteria:**
- No añade nuevas llamadas HTTP — usa datos ya disponibles en el componente
- Seccion de metricas aparece como `mat-expansion-panel` con `expanded="false"` por defecto
- Solo se muestra si `tarea.horas_estimadas > 0`

---

#### IT-AN-03: Link a Overview Dashboard en navegacion del modulo

**Descripcion:** Añadir acceso al Overview Dashboard desde la navegacion de proyectos.

**Archivos a editar:**
- `frontend/src/app/features/proyectos/proyectos.routes.ts` — añadir ruta `/proyectos/analytics`
- Sidebar o menu contextual del modulo — añadir item "Analytics"

**Acceptance Criteria:**
- Ruta `/proyectos/analytics` carga `OverviewDashboardComponent` con lazy loading
- La ruta debe ir ANTES de `:id` en el array de rutas para evitar captura incorrecta
- Item de menu con icono `insights` de Material Icons

---

## 3. Estimaciones por Epic

| Epic | Descripcion | Dias | Complejidad | Bloqueadores |
|---|---|---|---|---|
| Epic 1: Backend Analytics | Services + Views + URLs + Tests + Export | 5–6 | L | Ninguno — datos ya existen |
| Epic 2: Chart.js Setup | Instalacion + ChartConfigService + Interfaces + AnalyticsService | 3–4 | M | Epic 1 (endpoints reales para probar) |
| Epic 3: Dashboard Components | KPI Cards + ProjectDashboard + OverviewDashboard | 5–6 | L | Epic 2 completado |
| Epic 4: Report Builder | Formulario + Descarga Excel/PDF | 4–5 | L | Epic 1 BK-AN-05 + Epic 2 FE-AN-03 |
| Epic 5: Integraciones | Tabs en detail + navegacion | 2–3 | M | Epic 3 FE-AN-06 completado |
| **Total** | | **19–24 dias** | **XL** | |

**Nota sobre estimacion:** Los dias incluyen: implementacion, testing manual, correcciones, y testing automatizado backend. No incluye deploy ni QA de aceptacion del cliente.

---

## 4. Criterios de Aceptacion por Epic

### Epic 1 — Done cuando:
- `python manage.py test apps.proyectos.tests.test_analytics_services` pasa con >= 80% cobertura en `analytics_services.py`
- Los 8 endpoints de analytics retornan 200 con datos reales (probado con Postman/curl)
- Los endpoints retornan 403 si se intenta acceder a datos de otra empresa (multi-tenant verificado)
- Excel descargable desde endpoint con datos reales
- PDF descargable (o decision documentada de usar jsPDF si WeasyPrint da problemas)

### Epic 2 — Done cuando:
- `npm run build` sin errores TypeScript en modo strict
- `ChartConfigService` correctamente configura Chart.js una sola vez
- `AnalyticsService` tiene tipado completo — sin `any` en toda la feature
- `analytics.model.ts` refleja exactamente la respuesta de los endpoints

### Epic 3 — Done cuando:
- `ProjectDashboardComponent` muestra los 4 graficos con datos reales del backend
- `OverviewDashboardComponent` muestra resumen del portafolio
- Loading state visible mientras carga (mat-progress-bar)
- Empty state correcto si no hay datos
- No hay errores en consola del navegador
- Responsive en mobile (probado con DevTools a 375px)

### Epic 4 — Done cuando:
- Formulario de report builder selecciona periodo y secciones
- Boton "Exportar Excel" descarga archivo valido que abre en Excel/LibreOffice
- Boton "Exportar PDF" descarga archivo valido (o alternativa documentada)

### Epic 5 — Done cuando:
- Tab "Analytics" aparece en proyecto-detail y carga el dashboard correctamente
- Seccion de metricas aparece en tarea-detail cuando hay horas estimadas
- Ruta `/proyectos/analytics` carga sin errores

---

## 5. Orden de Ejecucion

### Fase 1 (Dias 1–6): Backend Analytics
```
BK-AN-01 → BK-AN-02 → BK-AN-03 → BK-AN-04 → BK-AN-05
```
**Justificacion:** El backend debe estar listo para que el frontend pueda probar con datos reales. Los tests (BK-AN-04) deben hacerse despues de implementar los services pero antes de hacer PR. La exportacion (BK-AN-05) puede hacerse en paralelo con BK-AN-03 si hay capacidad.

### Fase 2 (Dias 7–10): Angular Setup
```
FE-AN-02 (interfaces) → FE-AN-01 (Chart.js) → FE-AN-03 (service)
```
**Justificacion:** Las interfaces TypeScript primero — el resto depende de ellas. Chart.js antes del service para que la configuracion este lista.

**Se puede paralelizar:** FE-AN-02 con BK-AN-05 (si hay otro desarrollador o el backend se termino antes).

### Fase 3 (Dias 11–16): Dashboard Components
```
FE-AN-05 (KPI Cards) → FE-AN-04 (Charts base) → FE-AN-06 (ProjectDashboard) → FE-AN-07 (OverviewDashboard)
```
**Justificacion:** Los componentes de graficos base son reutilizables y deben estar listos antes de los dashboards contenedores.

### Fase 4 (Dias 17–20): Report Builder
```
FE-AN-09 (util descarga) → FE-AN-08 (ReportBuilder)
```
**Justificacion:** El utilitario de descarga es independiente y rapido (< 1 hora). El ReportBuilder es el componente mas complejo del frontend.

### Fase 5 (Dias 21–22): Integraciones
```
IT-AN-02 (tarea-detail) → IT-AN-01 (proyecto-detail tab) → IT-AN-03 (navegacion)
```
**Justificacion:** Las integraciones son los cambios de menor riesgo. La de tarea-detail es la mas simple (no requiere nuevas llamadas HTTP). La del tab en proyecto-detail es la mas critica (puede romper tabs existentes).

---

## 6. Riesgos

### Riesgo 1: WeasyPrint — Dependencias del sistema operativo
**Probabilidad:** Alta
**Impacto:** M — bloquea exportacion PDF
**Descripcion:** WeasyPrint requiere `libcairo`, `libpango`, `libgdk-pixbuf` instalados en el sistema. En entornos Docker o MacOS, la instalacion puede fallar o producir PDFs con estilos rotos.
**Mitigacion:**
- Verificar compatibilidad en el entorno de desarrollo en el dia 1 de BK-AN-05
- Si falla: decisión documentada en DECISIONS.md (DEC-027) de usar `jsPDF` + `html2canvas` en el frontend Angular como alternativa
- La alternativa jsPDF no requiere cambios en el backend

### Riesgo 2: Performance de queries de analytics en proyectos grandes
**Probabilidad:** Media
**Impacto:** M — queries lentas en produccion
**Descripcion:** `get_hours_by_period` y `get_burndown_data` pueden ser costosos si el proyecto tiene miles de `TimesheetEntry`. Sin indices adecuados, pueden superar 1 segundo.
**Mitigacion:**
- Verificar que `TimesheetEntry` tiene indice en `(tarea_id, fecha)` — ya existe segun el modelo (`Index(fields=['usuario', 'fecha'])`)
- Añadir indice compuesto `(tarea__proyecto_id, fecha)` si se identifica N+1 durante testing
- Para MVP: limite de 90 dias en `get_hours_by_period` por defecto; parametrizable

### Riesgo 3: Chart.js y ChangeDetectionStrategy.OnPush
**Probabilidad:** Media
**Impacto:** M — graficos no se actualizan al cambiar inputs
**Descripcion:** Chart.js manipula el DOM directamente. Con `OnPush`, los cambios en `input()` no disparan automaticamente la actualizacion del grafico.
**Mitigacion:**
- Usar `effect()` de Angular 18 para reaccionar a cambios en inputs y llamar `chart.update()`
- Documentar el patron en el primer componente de grafico para que los siguientes lo sigan
- Probar exhaustivamente el cambio de `projectId` mientras el dashboard esta visible

### Riesgo 4: Feature #4 (Resource Management) frontend pendiente
**Probabilidad:** Alta (ya confirmado como pendiente en CONTEXT.md)
**Impacto:** L — `ResourceUtilizationChartComponent` requiere datos de `ResourceAssignment` y `ResourceCapacity`
**Descripcion:** Si el frontend de Feature #4 no esta completo, los datos de utilizacion de recursos pueden estar incompletos o sin registros reales para probar.
**Mitigacion:**
- Los endpoints backend de Resource Management YA existen (BK-11 a BK-18 completados)
- `analytics_services.py` puede calcular utilizacion directamente desde los modelos — no depende del frontend de Feature #4
- En el dashboard, si no hay datos de capacidad, mostrar `sc-empty-state` en `ResourceUtilizationChart` en lugar de grafico vacio

### Riesgo 5: Scope creep — "Solo añadir esta metrica mas"
**Probabilidad:** Alta (tipico en features de analytics)
**Impacto:** M — extiende el timeline sin valor proporcional
**Descripcion:** Analytics es la feature donde mas facilmente se añaden metricas adicionales sin planificacion. Cada metrica nueva implica: funcion en service, serializer, endpoint, interface TypeScript, logica en componente.
**Mitigacion:**
- El MVP de Feature #5 se limita estrictamente a las metricas definidas en este documento
- Cualquier metrica adicional se registra en un backlog separado y se planifica como Feature #5.1
- Regla de oro: si no esta en este documento, no va en el sprint de Feature #5

---

## Resumen de Archivos a Crear

### Backend (Django)
| Archivo | Tarea | Tipo |
|---|---|---|
| `apps/proyectos/analytics_services.py` | BK-AN-01, BK-AN-02 | NUEVO |
| `apps/proyectos/export_services.py` | BK-AN-05 | NUEVO |
| `templates/reports/base_report.html` | BK-AN-05 | NUEVO |
| `templates/reports/project_report.html` | BK-AN-05 | NUEVO |
| `apps/proyectos/tests/test_analytics_services.py` | BK-AN-04 | NUEVO |
| `apps/proyectos/tests/test_analytics_views.py` | BK-AN-04 | NUEVO |
| `apps/proyectos/views.py` | BK-AN-03 | EDITAR |
| `apps/proyectos/serializers.py` | BK-AN-03 | EDITAR |
| `apps/proyectos/urls.py` | BK-AN-03 | EDITAR |

### Frontend (Angular)
| Archivo | Tarea | Tipo |
|---|---|---|
| `models/analytics.model.ts` | FE-AN-02 | NUEVO |
| `services/chart-config.service.ts` | FE-AN-01 | NUEVO |
| `services/analytics.service.ts` | FE-AN-03 | NUEVO |
| `components/charts/burndown-chart/` | FE-AN-04 | NUEVO |
| `components/charts/velocity-chart/` | FE-AN-04 | NUEVO |
| `components/charts/task-distribution-chart/` | FE-AN-04 | NUEVO |
| `components/charts/resource-utilization-chart/` | FE-AN-04 | NUEVO |
| `components/kpi-cards/` | FE-AN-05 | NUEVO |
| `components/project-dashboard/` | FE-AN-06 | NUEVO |
| `components/overview-dashboard/` | FE-AN-07 | NUEVO |
| `components/report-builder/` | FE-AN-08 | NUEVO |
| `shared/utils/file-download.util.ts` | FE-AN-09 | NUEVO |
| `components/proyecto-detail/proyecto-detail.component.*` | IT-AN-01 | EDITAR |
| `components/tarea-detail/tarea-detail.component.*` | IT-AN-02 | EDITAR |
| `proyectos.routes.ts` | IT-AN-03 | EDITAR |

### Documentacion
| Archivo | Razon |
|---|---|
| `DECISIONS.md` | DEC-026 (Chart.js nativo) — antes de FE-AN-01 |
| `DECISIONS.md` | DEC-027 (PDF: WeasyPrint vs jsPDF) — al ejecutar BK-AN-05 |
| `docs/API-DOCS-UPDATED.md` | 8 endpoints nuevos de analytics + 3 de exportacion |
| `CONTEXT.md` | Actualizar al terminar Feature #5 |

---

## Notas Tecnicas Finales

1. **No crear modelo `DashboardConfig`** para el MVP. Las preferencias de usuario (periodo seleccionado, etc.) se guardan en `localStorage` via Angular signals. Si en el futuro se necesita persistencia server-side, se añade en Feature #5.1.

2. **No crear modelo `MetricSnapshot`** para el MVP. Todas las metricas se calculan en tiempo real. Si las queries resultan lentas en produccion con datos reales, se evalua caching en Feature #5.1 (materializacion de snapshots diarios via Celery).

3. **Libreria de graficos definitiva: Chart.js nativo** (`npm install chart.js`). No usar `ng2-charts` (wrapper desactualizado para Angular 18 signals). No usar `@swimlane/ngx-charts` (no necesario para este scope). Documentar como DEC-026.

4. **Multi-tenant obligatorio en TODOS los endpoints de analytics.** El `company_id` se extrae del usuario autenticado en la view — nunca se acepta como parametro del cliente.

5. **Dependencia con Feature #4 frontend:** Los datos de `ResourceUtilization` son calculables desde el backend independientemente del frontend de Feature #4. No hay bloqueo real para Feature #5.
