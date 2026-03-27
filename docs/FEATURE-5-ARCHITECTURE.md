# Feature #5 — Reporting & Analytics: Architecture

**Date:** 2026-03-27
**Author:** Technical Writer
**Scope:** Backend Django + Frontend Angular

---

## Table of Contents

1. [Design Decisions](#design-decisions)
2. [Data Flow](#data-flow)
3. [Metric Calculation Details](#metric-calculation-details)
4. [New Files](#new-files)
5. [Database Performance](#database-performance)
6. [Suggested Future Improvements](#suggested-future-improvements)

---

## Design Decisions

### No New Models

Feature #5 adds zero new database tables. All analytics metrics are computed on-the-fly from four existing models: `Project`, `Phase`, `Task`, and `TimesheetEntry`, plus `ResourceAssignment` and `ResourceCapacity` (introduced in Feature #4).

This decision was made after auditing the fields available on each model. Every required metric — completion rate, on-time rate, velocity, burn rate, burn down, and resource utilization — can be derived from existing data without introducing a `DashboardConfig`, `MetricSnapshot`, or `ProjectDashboard` model.

The trade-off is that all metrics re-execute database queries on each request. This is acceptable for projects with up to ~200 tasks (typical latency under 200ms). For larger projects, caching is the recommended next step (see [Suggested Future Improvements](#suggested-future-improvements)).

### Caching: Django File-Based (No Redis)

Feature #5 uses no server-side caching. All analytics endpoints are read-only and compute from live data. The infrastructure does not include a Redis instance in the current environment, and the expected project sizes at MVP launch do not justify adding one.

When caching becomes necessary (projects exceeding 500 tasks, or repeated dashboard loads creating measurable load), the recommended approach is Django's built-in file-based cache configured in `settings.py`. This adds zero infrastructure dependencies and is trivially reversible. Redis can be evaluated if the cache hit rate does not satisfy latency requirements.

### PDF Export: jsPDF in the Frontend (Not WeasyPrint)

PDF export is handled client-side with jsPDF. This keeps the backend stateless and avoids the significant system dependency footprint of WeasyPrint (which requires Cairo, Pango, and platform-specific font configuration on the server). The frontend already has Chart.js rendering the dashboard visually; jsPDF can capture the canvas elements directly, making the PDF output visually faithful without server-round-trips.

### Excel Export: openpyxl in the Backend

Excel export uses `openpyxl` on the Django backend and streams the file as an HTTP response with `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`. This is the correct approach for multi-project reports: the server aggregates data from multiple projects in a single request-response cycle, which would be complex and slow to do purely client-side. The frontend receives the file as a `Blob` and triggers a browser download via a temporary object URL.

---

## Data Flow

The following diagram shows how a request for the KPIs endpoint travels through the stack:

```
Angular Component (project-analytics-dashboard)
  |
  | HTTP GET /api/v1/projects/{id}/analytics/kpis/
  | Authorization: Bearer <JWT>
  v
Django Request Pipeline
  |
  | JWTAuthentication (simplejwt)
  | CanAccessProyectos permission check
  v
ProjectKPIsView.get()
  |
  | _get_project_for_company(project_pk, request.user.company)
  |   -> get_object_or_404(Project, id=pk, company=company, activo=True)
  |   -> 404 if project belongs to different company
  v
get_project_kpis(project_id, company_id)     [analytics_services.py]
  |
  | Task.objects.filter(proyecto_id=..., company_id=...).aggregate(...)
  | Task.objects.filter(..., fecha_limite__lt=today, estado__in=[...]).count()
  | Task queryset for on-time computation (Python loop)
  | Task.objects.filter(..., estado='completed').annotate(TruncWeek).values().annotate(Count)
  | TimesheetEntry.objects.filter(...).annotate(TruncWeek).values().annotate(Sum)
  v
ProjectKPIsSerializer(data)
  |
  v
Response({'total_tasks': 47, 'completion_rate': 85.11, ...}, status=200)
  |
  v
Angular AnalyticsService.getKPIs()
  |
  | Unwraps Observable<ProjectKPIs>
  v
ProjectAnalyticsDashboardComponent
  | kpis.set(data)
  | computed signals re-evaluate (completionClass, budgetVarianceFmt, etc.)
  v
Template renders KPI cards with color classes
```

For multi-chart load (`loadData()` in the dashboard component), five calls are parallelized with `forkJoin`:

```
forkJoin({
  kpis:         GET /analytics/kpis/
  distribution: GET /analytics/task-distribution/
  velocity:     GET /analytics/velocity/?periods=8
  burnDown:     GET /analytics/burn-down/
  resources:    GET /analytics/resource-utilization/
})
```

All five execute concurrently. Chart rendering begins only after all five resolve, triggered by `setTimeout(() => this.buildCharts(), 0)` to yield the event loop and allow Angular's change detection to update the template with the chart canvas elements before Chart.js attaches to them.

---

## Metric Calculation Details

### Completion Rate

**Service function:** `get_project_kpis()` in `analytics_services.py`

**Strategy:** Single `aggregate()` call combining `Count('id')` (total) and `Count('id', filter=Q(estado='completed'))` (completed).

```python
totals = Task.objects.filter(
    proyecto_id=project_id,
    company_id=company_id,
).aggregate(
    total=Count('id'),
    completed=Count('id', filter=Q(estado='completed')),
    horas_estimadas_total=Sum('horas_estimadas'),
    horas_registradas_total=Sum('horas_registradas'),
)
completion_rate = round(completed / total * 100, 2) if total > 0 else 0.0
```

**Index used:** `idx_task_project_estado` on `(proyecto_id, estado)` — defined in `Task.Meta.indexes`. This index makes the filter + count O(log n) rather than a full table scan.

**Database queries:** 1

---

### On-Time Rate

**Service function:** `get_project_kpis()` in `analytics_services.py`

**Known limitation:** The `Task` model has no `fecha_completion` field. When a task transitions to `completed`, only `updated_at` (from `BaseModel`) changes. Any subsequent edit to that task (adding a comment, changing a tag, updating `porcentaje_completado`) will update `updated_at` again, making it an imprecise proxy for when the task was actually completed.

**Strategy:** Fetch `updated_at` and `fecha_limite` for all completed tasks with a deadline, then compare in Python to avoid non-portable SQL date-casting.

```python
completed_with_deadline_qs = tasks_qs.filter(
    estado='completed',
    fecha_limite__isnull=False,
).values('updated_at', 'fecha_limite')

for task in completed_with_deadline_qs:
    completion_date = task['updated_at'].date()
    if completion_date <= task['fecha_limite']:
        completed_on_time += 1

on_time_rate = round(completed_on_time / count * 100, 2) if count > 0 else 0.0
```

**Database queries:** 1 (additional queryset evaluation after the aggregate call)

---

### Velocity

**Service function:** `get_velocity_data()` in `analytics_services.py`

**Strategy:** Use Django's `TruncWeek('updated_at')` to group completed tasks by the Monday of the week they were last updated. Build a `{week_start: count}` map in Python, then iterate over exactly `periods` weeks (aligning to the current Monday), filling in `0` for weeks with no data.

```python
velocity_qs = Task.objects.filter(
    proyecto_id=project_id,
    company_id=company_id,
    estado='completed',
    updated_at__date__gte=start_date,
).annotate(
    week=TruncWeek('updated_at')
).values('week').annotate(
    tasks_completed=Count('id')
).order_by('week')
```

The fill-zero step in Python ensures the response always contains exactly `periods` elements, which Chart.js requires for consistent bar chart rendering. Without it, sparse data would cause misaligned labels.

**Database queries:** 1

---

### Burn Rate

**Service function:** `get_burn_rate_data()` in `analytics_services.py`

**Strategy:** Identical windowing to Velocity but queries `TimesheetEntry.horas` grouped by `TruncWeek('fecha')`. The `fecha` field on `TimesheetEntry` is the date the work was recorded (a `DateField`), not a `DateTimeField`, which makes `TruncWeek` directly applicable without `.date()` conversion.

```python
timesheet_qs = TimesheetEntry.objects.filter(
    tarea__proyecto_id=project_id,
    company_id=company_id,
    fecha__gte=start_date,
).annotate(
    week=TruncWeek('fecha')
).values('week').annotate(
    hours=Sum('horas')
).order_by('week')
```

**Database queries:** 1

---

### Burn Down

**Service function:** `get_burn_down_data()` in `analytics_services.py`

**Strategy:** Three steps executed in two database queries plus one Python accumulation pass:

1. Get `total_estimated = Sum(Task.horas_estimadas)` — 1 query.
2. Get project dates from `Project` object — 1 query (shares with the project fetch in the view layer; `get_burn_down_data` fetches the project itself).
3. Get weekly hours from `TimesheetEntry` grouped by week within the project date range — 1 query.
4. Compute cumulative hours in Python: `list(itertools.accumulate(weekly_hours))`.
5. Compute remaining hours: `max(total_estimated - cumulative[i], 0)` for each week.
6. Compute ideal line: linear from `total_estimated` to `0` over `num_weeks` steps.

The `itertools.accumulate` approach is preferable to a SQL window function because it avoids a database-engine-specific dependency (PostgreSQL supports `SUM() OVER()`, but the project also runs with SQLite in development).

**Database queries:** 3 (project fetch + task aggregate + timesheet group-by)

---

### Resource Utilization

**Service function:** `get_resource_utilization()` in `analytics_services.py`

**Strategy:** Reuses `calculate_user_workload()` from `resource_services.py` (Feature #4). Only users with at least one active `ResourceAssignment` linked to a task in the project are included. The user list is fetched with `distinct()` to avoid duplicate computation.

```python
usuario_ids = list(
    ResourceAssignment.objects.filter(
        company_id=company_id,
        tarea__proyecto_id=project_id,
        activo=True,
    ).values_list('usuario_id', flat=True).distinct()
)
```

Each user then gets one `calculate_user_workload()` call, which executes its own set of queries. This results in N+1 behavior (one query to get user IDs, then one workload computation per user). For teams of typical size (2–15 people), this is acceptable. For very large teams, a batched computation would reduce query count.

If `calculate_user_workload()` raises an exception for a user, the user is still included with partial data sourced directly from `TimesheetEntry`. This graceful degradation ensures one bad data point does not blank out the entire resource chart.

**Database queries:** 2 + (N workload queries) where N is the number of active team members

---

### Project Timeline

**Service function:** `get_project_timeline()` in `analytics_services.py`

**Strategy:** Uses `Prefetch` to load all active phases with their tasks in exactly 2 queries regardless of the number of phases. Phase statistics are computed in Python over the prefetched `phase.phase_tasks` list.

```python
tasks_prefetch = Prefetch(
    'tasks',
    queryset=Task.objects.filter(
        company_id=company_id,
    ).order_by('fecha_inicio', 'prioridad', 'nombre'),
    to_attr='phase_tasks',
)

phases = (
    Phase.objects.filter(
        proyecto_id=project_id,
        company_id=company_id,
        activo=True,
    )
    .prefetch_related(tasks_prefetch)
    .order_by('orden')
)
```

Note that `Prefetch` does not accept `.values()` — the queryset must return model instances, and field access uses attribute notation (`t.nombre`, `t.estado`) rather than dict access. This is an important constraint if you modify this function.

**Database queries:** 2 (project + phases-with-tasks prefetch)

---

## New Files

| File | Layer | Purpose |
|------|-------|---------|
| `backend/apps/proyectos/analytics_services.py` | Backend | 8 service functions: `get_project_kpis`, `get_task_distribution`, `get_velocity_data`, `get_burn_rate_data`, `get_burn_down_data`, `get_resource_utilization`, `compare_projects`, `get_project_timeline` |
| `backend/apps/proyectos/analytics_views.py` | Backend | 9 `APIView` subclasses (all read-only except `ExportExcelView` which generates a file). One helper function `_get_project_for_company()` for consistent project ownership enforcement. |
| `backend/apps/proyectos/analytics_serializers.py` | Backend | 13 serializer classes, all read-only. Organized by endpoint: `ProjectKPIsSerializer`, `TaskDistributionSerializer`, `VelocityResponseSerializer`, `BurnRateResponseSerializer`, `BurnDownResponseSerializer`, `ResourceUtilizationSerializer`, `ProjectComparisonSerializer`, `ProjectTimelineSerializer` + nested `TimelinePhaseSerializer` and `TimelineTaskSerializer`. Two request-validation serializers: `CompareProjectsRequestSerializer` and `ExportExcelRequestSerializer`. |
| `frontend/src/app/features/proyectos/models/analytics.model.ts` | Frontend | 13 TypeScript interfaces mirroring the backend serializer output exactly: `ProjectKPIs`, `TaskDistribution`, `VelocityDataPoint`, `VelocityResponse`, `BurnRateDataPoint`, `BurnRateResponse`, `BurnDownPoint`, `BurnDownData`, `ResourceUtilization`, `ProjectComparison`, `TimelineTask`, `TimelinePhase`, `ProjectTimeline`. Plus two request interfaces: `CompareProjectsRequest`, `ExportExcelRequest`. |
| `frontend/src/app/features/proyectos/services/analytics.service.ts` | Frontend | `AnalyticsService` (`providedIn: 'root'`) with 9 methods: `getKPIs`, `getTaskDistribution`, `getVelocity`, `getBurnRate`, `getBurnDown`, `getResourceUtilization`, `getTimeline`, `compareProjects`, `exportExcel`. The `exportExcel` method uses `{ responseType: 'blob' }` to handle the binary Excel response. |
| `frontend/src/app/features/proyectos/components/analytics/project-analytics-dashboard/project-analytics-dashboard.component.ts` | Frontend | Standalone component (`ChangeDetectionStrategy.OnPush`). Uses `signal()` for state, `computed()` for KPI CSS class derivation, `forkJoin` to parallelize 5 API calls, and Chart.js for 4 charts: burn down (line), velocity (bar + line overlay), task distribution (doughnut), resource utilization (horizontal bar). Implements `OnInit` and `OnDestroy` for proper subscription cleanup and chart destruction. |

**Modified files:**

| File | Change |
|------|--------|
| `backend/apps/proyectos/urls.py` | Added 9 new URL patterns for analytics endpoints under `# Analytics — Feature #5` section |

---

## Database Performance

### Queries Per Endpoint

| Endpoint | Queries | Notes |
|----------|---------|-------|
| GET kpis/ | 3 | 1 project lookup + 1 aggregate + 1 for on-time task list |
| GET task-distribution/ | 2 | 1 project lookup + 1 group-by query |
| GET velocity/ | 2 | 1 project lookup + 1 TruncWeek query |
| GET burn-rate/ | 2 | 1 project lookup + 1 TruncWeek query |
| GET burn-down/ | 4 | 1 project lookup + 1 task aggregate + 1 project date fetch + 1 timesheet query |
| GET resource-utilization/ | 2 + N | 1 project lookup + 1 assignment query + N workload queries (N = team members) |
| GET timeline/ | 3 | 1 project lookup + 1 project fetch + 1 prefetch phases+tasks |
| POST compare/ | 1 + (3 × M) | 1 project list query + 3 queries per project M |
| POST export-excel/ | 1 + (6 × M) | 1 project list + kpis + distribution per project M |

### N+1 Cases Avoided

**Timeline:** The naive implementation would fetch phases, then query tasks for each phase individually — N+1. The `Prefetch` approach with `to_attr='phase_tasks'` eliminates this completely.

**Task distribution:** A single `values('estado').annotate(count=Count('id'))` call replaces six separate filtered counts.

**Velocity and Burn Rate:** A single `TruncWeek` + `annotate` + `values` query replaces per-week filtered counts.

### Known N+1 Cases (Accepted for MVP)

**Resource utilization:** One `calculate_user_workload()` call per team member. This was a deliberate reuse decision (Feature #4's service is authoritative for workload) rather than a query optimization oversight. For a team of 15 people, this results in approximately 15–30 additional queries. Acceptable at current scale.

**Compare projects:** Calls `get_project_kpis()` per project. For the maximum of 20 projects, this produces up to 60 queries. Acceptable for an on-demand report, but not suitable for high-frequency polling.

---

## Suggested Future Improvements

### High Priority

**Add `Task.fecha_completion` field**

The most impactful accuracy improvement available. Adding a `DateField(null=True, blank=True)` to `Task` and setting it via a `post_save` signal when `estado` transitions to `'completed'` would make On-Time Rate accurate regardless of subsequent edits to the task. This requires one migration and one signal handler.

**Server-side caching for large projects**

Projects with more than 500 tasks and 20+ team members will produce analytics response times above 500ms. Implement Django's file-based cache with a 5-minute TTL for KPI, velocity, and burn rate endpoints. Invalidate cache on `Task.save()` via a post-save signal. A `cache_key` of `f"analytics:{company_id}:{project_id}:{metric_name}"` is sufficient.

### Medium Priority

**Granularity='month' in burn-down**

The `get_burn_down_data()` function accepts `granularity` as a parameter and validates that only `'week'` is passed. Adding a `TruncMonth` path follows the same structure as the weekly path. The main consideration is aligning month boundaries with the project start date.

**Batch KPI computation in compare_projects()**

Replace the loop over `get_project_kpis()` with a single annotated queryset across all requested projects. This reduces compare/ from 3N queries to 3 queries for any number of projects.

### Low Priority

**DashboardConfig model for personalized dashboards**

Allow users to configure which charts appear, the default `periods` value for velocity/burn rate, and whether to show resource utilization. A simple `JSONField` on a `DashboardConfig` model (one per user per project) would suffice.

**Redis cache backend**

If file-based cache proves insufficient (concurrent requests on the same project invalidating each other's cache files), migrate to Redis. The cache key structure remains the same; only the `CACHES` setting in `settings.py` changes.

**Velocity by phase**

`get_velocity_data()` currently aggregates across all phases. Accepting an optional `phase_id` parameter would enable per-phase velocity tracking, useful for construction projects with distinct sequential phases.

**Export-excel: wire `metrics` and `date_range` parameters**

The `ExportExcelRequestSerializer` accepts these fields but `_generate_excel_response()` ignores them. Wiring `date_range` to pass `start_date`/`end_date` to `get_resource_utilization()` and `get_burn_rate_data()` would make the export more useful for specific reporting periods.
