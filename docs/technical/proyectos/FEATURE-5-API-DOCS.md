# Feature #5: Analytics API Reference

**Version:** 1.0
**Base URL:** `/api/v1/projects`
**Authentication:** All endpoints require a valid Bearer JWT token in the `Authorization` header.
**Multi-tenancy:** Every endpoint enforces `company_id` isolation at the service layer. A user cannot access analytics for a project belonging to a different company, regardless of whether they know the project UUID.

---

## Table of Contents

1. [GET analytics/kpis/](#1-get-kpis)
2. [GET analytics/task-distribution/](#2-get-task-distribution)
3. [GET analytics/velocity/](#3-get-velocity)
4. [GET analytics/burn-rate/](#4-get-burn-rate)
5. [GET analytics/burn-down/](#5-get-burn-down)
6. [GET analytics/resource-utilization/](#6-get-resource-utilization)
7. [GET analytics/timeline/](#7-get-timeline)
8. [POST analytics/compare/](#8-post-compare)
9. [POST analytics/export-excel/](#9-post-export-excel)
10. [Implementation Notes](#implementation-notes)

---

## 1. GET analytics/kpis/

### `GET /api/v1/projects/{project_id}/analytics/kpis/`

Returns the eight primary KPIs for a single project. All metrics are computed on-the-fly from live data in `Task` and `TimesheetEntry`.

**Authentication:** Bearer JWT (required)

**Permission class:** `CanAccessProyectos` — the requesting user must belong to the same company as the project.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | UUID | The project's primary key |

**Query Parameters:** None

**Response 200:**

```json
{
  "total_tasks": 47,
  "completed_tasks": 40,
  "overdue_tasks": 3,
  "completion_rate": 85.11,
  "on_time_rate": 72.0,
  "budget_variance": -5.2,
  "velocity": 12.3,
  "burn_rate": 38.5
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `total_tasks` | integer | Total task count for the project |
| `completed_tasks` | integer | Tasks with `estado = 'completed'` |
| `overdue_tasks` | integer | Non-completed tasks where `fecha_limite < today` |
| `completion_rate` | float | `(completed_tasks / total_tasks) * 100`, rounded to 2 decimal places |
| `on_time_rate` | float | % of completed tasks that were finished on or before `fecha_limite`. Tasks without a deadline are excluded. Returns `0.0` if no completed tasks have a deadline. |
| `budget_variance` | float | `(horas_registradas - horas_estimadas) / horas_estimadas * 100`. Negative = under budget. Returns `0.0` if `horas_estimadas` is zero. |
| `velocity` | float | Average tasks completed per week over the last 4 weeks (uses `updated_at` as proxy for completion date) |
| `burn_rate` | float | Average hours registered per week over the last 4 weeks, sourced from `TimesheetEntry` |

**Error Responses:**

| Code | Description |
|------|-------------|
| 401 | Missing or invalid JWT |
| 403 | Project belongs to a different company |
| 404 | Project does not exist or `activo = False` |

---

## 2. GET analytics/task-distribution/

### `GET /api/v1/projects/{project_id}/analytics/task-distribution/`

Returns the count and percentage breakdown of tasks by status for a project. Always returns all six statuses; statuses with no tasks return `0`.

**Authentication:** Bearer JWT (required)

**Permission class:** `CanAccessProyectos`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | UUID | The project's primary key |

**Query Parameters:** None

**Response 200:**

```json
{
  "todo": 5,
  "in_progress": 2,
  "in_review": 0,
  "completed": 40,
  "blocked": 0,
  "cancelled": 0,
  "total": 47,
  "percentages": {
    "todo": 10.64,
    "in_progress": 4.26,
    "in_review": 0.0,
    "completed": 85.11,
    "blocked": 0.0,
    "cancelled": 0.0
  }
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `todo` | integer | Tasks with `estado = 'todo'` |
| `in_progress` | integer | Tasks with `estado = 'in_progress'` |
| `in_review` | integer | Tasks with `estado = 'in_review'` |
| `completed` | integer | Tasks with `estado = 'completed'` |
| `blocked` | integer | Tasks with `estado = 'blocked'` |
| `cancelled` | integer | Tasks with `estado = 'cancelled'` |
| `total` | integer | Sum of all status counts |
| `percentages` | object | Each status as a percentage of `total`, rounded to 2 decimal places. All values are `0.0` when `total = 0`. |

**Error Responses:**

| Code | Description |
|------|-------------|
| 401 | Missing or invalid JWT |
| 403 | Project belongs to a different company |
| 404 | Project does not exist or `activo = False` |

---

## 3. GET analytics/velocity/

### `GET /api/v1/projects/{project_id}/analytics/velocity/?periods=8`

Returns weekly team velocity (tasks completed per week) for the last N weeks. The response always contains exactly `periods` data points. Weeks with no completed tasks return `tasks_completed: 0`.

**Authentication:** Bearer JWT (required)

**Permission class:** `CanAccessProyectos`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | UUID | The project's primary key |

**Query Parameters:**

| Parameter | Type | Default | Constraints | Description |
|-----------|------|---------|-------------|-------------|
| `periods` | integer | `8` | 1–52 | Number of weeks to include |

**Response 200:**

```json
{
  "periods": 8,
  "data": [
    {
      "week_label": "Week 1",
      "week_start": "2026-01-26",
      "tasks_completed": 3
    },
    {
      "week_label": "Week 2",
      "week_start": "2026-02-02",
      "tasks_completed": 0
    }
  ]
}
```

**Response Fields (`data` array items):**

| Field | Type | Description |
|-------|------|-------------|
| `week_label` | string | Human-readable label, e.g. `"Week 1"`, `"Week 2"` |
| `week_start` | date (ISO 8601) | Monday of the week (`YYYY-MM-DD`) |
| `tasks_completed` | integer | Tasks whose `updated_at` falls in that week and whose `estado = 'completed'` |

**Error Responses:**

| Code | Description |
|------|-------------|
| 400 | `periods` is not an integer, or outside the 1–52 range |
| 401 | Missing or invalid JWT |
| 403 | Project belongs to a different company |
| 404 | Project does not exist or `activo = False` |

---

## 4. GET analytics/burn-rate/

### `GET /api/v1/projects/{project_id}/analytics/burn-rate/?periods=8`

Returns the weekly burn rate (hours registered per week) for the last N weeks. Data is sourced from `TimesheetEntry.horas`, grouped by `TruncWeek(fecha)`. Weeks with no timesheet entries return `hours_registered: 0.0`.

**Authentication:** Bearer JWT (required)

**Permission class:** `CanAccessProyectos`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | UUID | The project's primary key |

**Query Parameters:**

| Parameter | Type | Default | Constraints | Description |
|-----------|------|---------|-------------|-------------|
| `periods` | integer | `8` | 1–52 | Number of weeks to include |

**Response 200:**

```json
{
  "periods": 8,
  "data": [
    {
      "week_label": "Week 1",
      "week_start": "2026-01-26",
      "hours_registered": 24.5
    },
    {
      "week_label": "Week 2",
      "week_start": "2026-02-02",
      "hours_registered": 0.0
    }
  ]
}
```

**Response Fields (`data` array items):**

| Field | Type | Description |
|-------|------|-------------|
| `week_label` | string | Human-readable label, e.g. `"Week 1"` |
| `week_start` | date (ISO 8601) | Monday of the week |
| `hours_registered` | float | Sum of `TimesheetEntry.horas` for all tasks in the project during that week |

**Error Responses:**

| Code | Description |
|------|-------------|
| 400 | `periods` is not an integer, or outside the 1–52 range |
| 401 | Missing or invalid JWT |
| 403 | Project belongs to a different company |
| 404 | Project does not exist or `activo = False` |

---

## 5. GET analytics/burn-down/

### `GET /api/v1/projects/{project_id}/analytics/burn-down/?granularity=week`

Returns burn down chart data for the full project lifecycle. Each data point provides three values: the ideal remaining hours, the actual remaining hours (cumulative from timesheet), and the cumulative hours registered. The date range spans from the project's `fecha_inicio_planificada` (or `fecha_inicio_real`) to `fecha_fin_planificada` (or `fecha_fin_real`). If neither date is set, the endpoint defaults to the last 8 weeks.

**Authentication:** Bearer JWT (required)

**Permission class:** `CanAccessProyectos`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | UUID | The project's primary key |

**Query Parameters:**

| Parameter | Type | Default | Constraints | Description |
|-----------|------|---------|-------------|-------------|
| `granularity` | string | `"week"` | Only `"week"` is supported | Time granularity. Monthly granularity is planned but not yet implemented. |

**Response 200:**

```json
{
  "total_hours_estimated": 480.0,
  "data_points": [
    {
      "week_label": "Week 1",
      "week_start": "2026-01-05",
      "hours_registered": 32.0,
      "hours_actual_cumulative": 32.0,
      "hours_remaining": 448.0,
      "hours_ideal": 440.0
    },
    {
      "week_label": "Week 2",
      "week_start": "2026-01-12",
      "hours_registered": 28.5,
      "hours_actual_cumulative": 60.5,
      "hours_remaining": 419.5,
      "hours_ideal": 400.0
    }
  ]
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `total_hours_estimated` | float | Sum of `Task.horas_estimadas` for all tasks in the project |
| `data_points` | array | One entry per week in the project's lifecycle |

**`data_points` item fields:**

| Field | Type | Description |
|-------|------|-------------|
| `week_label` | string | `"Week 1"`, `"Week 2"`, etc. |
| `week_start` | date (ISO 8601) | Monday of the week |
| `hours_registered` | float | Hours logged in `TimesheetEntry` for that specific week |
| `hours_actual_cumulative` | float | Running total of `hours_registered` up to and including this week (computed with `itertools.accumulate`) |
| `hours_remaining` | float | `max(total_hours_estimated - hours_actual_cumulative, 0)` |
| `hours_ideal` | float | Linear ideal burn: `total_hours_estimated - (ideal_step * week_index)`, floored at 0 |

**Error Responses:**

| Code | Description |
|------|-------------|
| 400 | `granularity` is not `"week"` |
| 401 | Missing or invalid JWT |
| 403 | Project belongs to a different company |
| 404 | Project does not exist or `activo = False` |

---

## 6. GET analytics/resource-utilization/

### `GET /api/v1/projects/{project_id}/analytics/resource-utilization/`

Returns utilization data for every team member with an active `ResourceAssignment` in the project. Delegates per-user workload computation to `calculate_user_workload()` from `resource_services.py` (Feature #4). Returns an empty array if no active assignments exist.

**Authentication:** Bearer JWT (required)

**Permission class:** `CanAccessProyectos`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | UUID | The project's primary key |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date (YYYY-MM-DD) | No | Start of the period. Defaults to the project's `fecha_inicio_real` or `fecha_inicio_planificada`. |
| `end_date` | date (YYYY-MM-DD) | No | End of the period. Defaults to today. |

**Response 200:**

```json
[
  {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_name": "Ana Torres",
    "user_email": "ana@example.com",
    "assigned_hours": 80.0,
    "registered_hours": 72.0,
    "capacity_hours": 160.0,
    "utilization_percentage": 50.0
  }
]
```

**Response Fields (per array item):**

| Field | Type | Description |
|-------|------|-------------|
| `user_id` | UUID | User primary key |
| `user_name` | string | `first_name + last_name`; falls back to `email` if name fields are empty |
| `user_email` | string | User email address |
| `assigned_hours` | float | Total hours assigned via `ResourceAssignment` |
| `registered_hours` | float | Total hours logged via `TimesheetEntry` |
| `capacity_hours` | float | Hours the user is available per `ResourceCapacity` records |
| `utilization_percentage` | float | `(registered_hours / capacity_hours) * 100`. Returns `0.0` if `calculate_user_workload()` fails for a user; that user still appears in the list with partial data. |

**Error Responses:**

| Code | Description |
|------|-------------|
| 400 | `start_date` or `end_date` is not in `YYYY-MM-DD` format |
| 401 | Missing or invalid JWT |
| 403 | Project belongs to a different company |
| 404 | Project does not exist or `activo = False` |

---

## 7. GET analytics/timeline/

### `GET /api/v1/projects/{project_id}/analytics/timeline/`

Returns the full project timeline including all active phases, each with their planned vs. actual dates, progress percentage, and the list of tasks. Uses a `Prefetch` strategy to avoid N+1 queries: one query for the project, one for all phases with their tasks prefetched.

**Authentication:** Bearer JWT (required)

**Permission class:** `CanAccessProyectos`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | UUID | The project's primary key |

**Query Parameters:** None

**Response 200:**

```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "project_name": "Torre Norte",
  "project_code": "TN-001",
  "start_planned": "2026-01-05",
  "end_planned": "2026-06-30",
  "start_actual": "2026-01-07",
  "end_actual": null,
  "overall_progress": 42.5,
  "phases": [
    {
      "phase_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "phase_name": "Cimentación",
      "phase_order": 1,
      "estado": "completed",
      "start_planned": "2026-01-05",
      "end_planned": "2026-02-28",
      "start_actual": "2026-01-07",
      "end_actual": "2026-02-25",
      "progress": 100.0,
      "total_tasks": 12,
      "completed_tasks": 12,
      "tasks": [
        {
          "task_id": "6ba7b812-9dad-11d1-80b4-00c04fd430c8",
          "task_code": "TSK-001",
          "task_name": "Excavación nivel 1",
          "estado": "completed",
          "prioridad": 1,
          "start_date": "2026-01-07",
          "end_date": "2026-01-20",
          "deadline": "2026-01-22",
          "horas_estimadas": 80.0,
          "horas_registradas": 76.5,
          "porcentaje_completado": 100
        }
      ]
    }
  ]
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `project_id` | UUID | Project primary key |
| `project_name` | string | `Project.nombre` |
| `project_code` | string | `Project.codigo` |
| `start_planned` | date or null | `Project.fecha_inicio_planificada` |
| `end_planned` | date or null | `Project.fecha_fin_planificada` |
| `start_actual` | date or null | `Project.fecha_inicio_real` |
| `end_actual` | date or null | `Project.fecha_fin_real` |
| `overall_progress` | float | `Project.porcentaje_avance` (auto-computed by signals) |
| `phases` | array | Active phases ordered by `Phase.orden` |

**Phase fields:**

| Field | Type | Description |
|-------|------|-------------|
| `phase_id` | UUID | Phase primary key |
| `phase_name` | string | `Phase.nombre` |
| `phase_order` | integer | `Phase.orden` |
| `estado` | string | Phase status (`todo`, `in_progress`, `completed`) |
| `start_planned` | date | `Phase.fecha_inicio_planificada` |
| `end_planned` | date | `Phase.fecha_fin_planificada` |
| `start_actual` | date or null | `Phase.fecha_inicio_real` |
| `end_actual` | date or null | `Phase.fecha_fin_real` |
| `progress` | float | `Phase.porcentaje_avance` |
| `total_tasks` | integer | Count of tasks in this phase |
| `completed_tasks` | integer | Count of tasks with `estado = 'completed'` in this phase |
| `tasks` | array | All tasks in the phase, ordered by `fecha_inicio`, `prioridad`, `nombre` |

**Task fields within phases:**

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | UUID | Task primary key |
| `task_code` | string or null | `Task.codigo` |
| `task_name` | string | `Task.nombre` |
| `estado` | string | Task status |
| `prioridad` | integer | Task priority |
| `start_date` | date or null | `Task.fecha_inicio` |
| `end_date` | date or null | `Task.fecha_fin` |
| `deadline` | date or null | `Task.fecha_limite` |
| `horas_estimadas` | float | Estimated hours |
| `horas_registradas` | float | Registered hours |
| `porcentaje_completado` | integer | Completion percentage (0–100) |

**Error Responses:**

| Code | Description |
|------|-------------|
| 401 | Missing or invalid JWT |
| 403 | Project belongs to a different company |
| 404 | Project does not exist or `activo = False` |

---

## 8. POST analytics/compare/

### `POST /api/v1/projects/analytics/compare/`

Compares multiple projects by their KPI metrics. Accepts a list of project UUIDs. Only projects belonging to the requesting user's company are included in the response — project IDs from other companies are silently filtered out.

**Authentication:** Bearer JWT (required)

**Permission class:** `CanAccessProyectos`

**Path Parameters:** None (cross-project endpoint)

**Request Body:**

```json
{
  "project_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
  ]
}
```

**Request Body Fields:**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `project_ids` | array of UUID | Yes | 1–20 items | Projects to compare |

**Response 200:**

```json
[
  {
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "project_name": "Torre Norte",
    "project_code": "TN-001",
    "completion_rate": 85.11,
    "on_time_rate": 72.0,
    "budget_variance": -5.2,
    "velocity": 12.3,
    "total_tasks": 47,
    "completed_tasks": 40,
    "overdue_tasks": 3
  },
  {
    "project_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    "project_name": "Edificio Sur",
    "project_code": "ES-002",
    "completion_rate": 30.0,
    "on_time_rate": 50.0,
    "budget_variance": 12.5,
    "velocity": 4.0,
    "total_tasks": 30,
    "completed_tasks": 9,
    "overdue_tasks": 5
  }
]
```

**Response Fields (per array item):**

| Field | Type | Description |
|-------|------|-------------|
| `project_id` | UUID | Project primary key |
| `project_name` | string | Project name |
| `project_code` | string | Project code |
| `completion_rate` | float | See KPIs endpoint |
| `on_time_rate` | float | See KPIs endpoint |
| `budget_variance` | float | See KPIs endpoint |
| `velocity` | float | See KPIs endpoint |
| `total_tasks` | integer | Total task count |
| `completed_tasks` | integer | Completed task count |
| `overdue_tasks` | integer | Overdue task count |

**Notes:**

- Projects with `activo = False` are excluded.
- If `get_project_kpis()` raises an exception for a specific project, that project is omitted from the response (logged as a warning). The response may therefore contain fewer items than `project_ids`.
- The response order matches the order in which projects are found in the database query, not the order of `project_ids` in the request.

**Error Responses:**

| Code | Description |
|------|-------------|
| 400 | `project_ids` is missing, empty, contains non-UUID values, or exceeds 20 items |
| 401 | Missing or invalid JWT |

---

## 9. POST analytics/export-excel/

### `POST /api/v1/projects/analytics/export-excel/`

Generates and returns an Excel file (`.xlsx`) containing analytics data for one or more projects. The file is built with `openpyxl` on the server and returned as a binary attachment. It contains three worksheets.

**Authentication:** Bearer JWT (required)

**Permission class:** `CanAccessProyectos`

**Path Parameters:** None (cross-project endpoint)

**Request Body:**

```json
{
  "project_ids": [
    "550e8400-e29b-41d4-a716-446655440000"
  ],
  "metrics": [],
  "date_range": {}
}
```

**Request Body Fields:**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `project_ids` | array of UUID | Yes | 1–20 items | Projects to include |
| `metrics` | array of string | No | — | Reserved for future use; currently ignored |
| `date_range` | object | No | — | Reserved for future use; currently ignored |

**Response 200:**

Binary `.xlsx` file stream.

```
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="analytics_report.xlsx"
```

**Excel Worksheet Structure:**

**Sheet 1: Summary**

| Column | Content |
|--------|---------|
| Project Code | `Project.codigo` |
| Project Name | `Project.nombre` |
| Completion % | `completion_rate` |
| On Time % | `on_time_rate` |
| Budget Variance % | `budget_variance` |
| Velocity (tasks/week) | `velocity` |
| Total Tasks | `total_tasks` |
| Completed Tasks | `completed_tasks` |
| Overdue Tasks | `overdue_tasks` |

**Sheet 2: KPIs**

Detailed KPI table with the same columns as Sheet 1, plus `burn_rate` (hrs/week). Header row is bold.

**Sheet 3: Task Distribution**

| Column | Content |
|--------|---------|
| Project Code | — |
| Project Name | — |
| To Do | Count of `todo` tasks |
| In Progress | Count of `in_progress` tasks |
| In Review | Count of `in_review` tasks |
| Completed | Count of `completed` tasks |
| Blocked | Count of `blocked` tasks |
| Cancelled | Count of `cancelled` tasks |
| Total | Total task count |

Column widths are auto-fitted to content (capped at 40 characters). Header rows are bold.

**Error Responses:**

| Code | Description |
|------|-------------|
| 400 | `project_ids` is missing, empty, contains non-UUID values, or exceeds 20 items |
| 401 | Missing or invalid JWT |

---

## Implementation Notes

### Metric Calculation Details

**Completion Rate**

Computed with a single Django ORM `aggregate()` call using `Count('id', filter=Q(estado='completed'))` against the full task queryset. Relies on the index `idx_task_project_estado` on `(proyecto_id, estado)`. Complexity: O(n tasks) in the database; effectively constant with the index.

**On-Time Rate**

The database does not store a `fecha_completion` field. As a deliberate MVP simplification, `updated_at` (from `BaseModel`) is used as a proxy for the task completion timestamp. This introduces inaccuracy when a completed task is subsequently edited (for comments, tags, etc.), which bumps `updated_at` without the task changing state. The comparison is performed in Python rather than SQL to avoid non-portable date-casting functions.

**Velocity**

Computed over the last N full weeks (default 8), where weeks are aligned to Monday using `TruncWeek('updated_at')`. Weeks with no completed tasks are filled in with `0` in Python after the query, ensuring the response always has exactly `periods` elements. The average divides by the number of weeks that have at least one data point (not by `periods`).

**Burn Rate**

Identical windowing approach to Velocity, but queries `TimesheetEntry` instead of `Task`. Groups by `TruncWeek(fecha)` where `fecha` is the date the timesheet entry was recorded.

**Burn Down**

Uses two queries and one Python accumulation pass:
1. `Task.objects.aggregate(total=Sum('horas_estimadas'))` — gets the total estimated hours.
2. `TimesheetEntry` grouped by `TruncWeek('fecha')` within the project date range — gets weekly hours.

The cumulative burn is computed in Python with `itertools.accumulate(weekly_hours)`. The ideal burn line decreases linearly from `total_hours_estimated` to `0` over `num_weeks` steps: `ideal_hours[i] = max(total_estimated - ideal_step * (i + 1), 0)`.

**Resource Utilization**

Delegates to `calculate_user_workload()` from `resource_services.py` (Feature #4). Only users with at least one active `ResourceAssignment` (`activo = True`) linked to the project are included. If `calculate_user_workload()` raises an exception for a specific user, that user is still included in the response with `assigned_hours`, `capacity_hours`, and `utilization_percentage` set to `0.0`; `registered_hours` is computed directly from `TimesheetEntry` as a fallback.

**Timeline**

Uses `Prefetch('tasks', queryset=..., to_attr='phase_tasks')` to load all phases and their tasks in exactly 2 database queries regardless of the number of phases or tasks. Phase statistics (total_tasks, completed_tasks) are computed in Python over the prefetched list.

**Project Comparison**

Calls `get_project_kpis()` once per project in a Python loop. For a list of N projects this results in N service calls, each of which executes 2–3 database queries. Maximum supported is 20 projects, capping the theoretical query count at 60 for the compare operation. There is no batch optimization in the current implementation.

### Known Limitations (MVP)

| Limitation | Impact | Planned Fix |
|------------|--------|-------------|
| `updated_at` used as `fecha_completion` proxy for On-Time Rate | On-Time Rate is approximate; editing a completed task can skew the metric | Add `Task.fecha_completion: DateField(null=True)` |
| `granularity='month'` not supported in burn-down | Only weekly granularity available | Implement `TruncMonth` path in `get_burn_down_data()` |
| No server-side caching | Repeated calls re-execute all queries | Add Django file-based cache for projects with >200 tasks |
| `metrics` and `date_range` in export-excel are ignored | All metrics always exported; date range not applied | Wire these parameters in `_generate_excel_response()` |
| Compare loops call `get_project_kpis()` per project | N×3 queries for N projects | Batch KPI computation with a single multi-project query |

### Multi-Tenancy Enforcement

Every analytics service function accepts both `project_id` and `company_id` as required arguments. The `company_id` is always sourced from `request.user.company` in the view layer — it is never taken from the request body or query parameters. This means a user cannot access another company's analytics even if they know the project UUID.

The `_get_project_for_company()` view helper calls `get_object_or_404(Project, id=project_pk, company=company, activo=True)`, which ensures a 404 response before the service function is even called if the project-company relationship does not match.

For cross-project endpoints (`compare/` and `export-excel/`), the service layer additionally applies `Project.objects.filter(id__in=project_ids, company_id=company_id)`, silently discarding any IDs that belong to another company.

### Database Indexes Used

| Query | Index |
|-------|-------|
| Task filter by project + status | `idx_task_project_estado` on `(proyecto_id, estado)` |
| Task filter by company | Standard `company_id` FK index |
| TimesheetEntry filter by task project | Join through `tarea__proyecto_id` |
| ResourceAssignment filter by company + task project | FK indexes on `company_id` and `tarea_id` |
