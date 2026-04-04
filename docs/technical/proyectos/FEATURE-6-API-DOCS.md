# Feature 6 — Advanced Scheduling: API Documentation

## Base URL
All endpoints use the prefix `/api/v1/`.

## Authentication
All endpoints require `Authorization: Bearer <JWT>` header.
The JWT is added automatically by the Angular interceptor.

---

## 1. Scheduling — Auto Schedule

### `POST /projects/{projectId}/scheduling/auto-schedule/`

Calculates optimized start/end dates for all project tasks based on dependencies and constraints.

**Path params**
| Param | Type | Description |
|---|---|---|
| `projectId` | UUID | Project identifier |

**Request body**
```json
{
  "mode": "asap",
  "respect_constraints": true,
  "dry_run": false
}
```
| Field | Type | Values | Description |
|---|---|---|---|
| `mode` | string | `"asap"` \| `"alap"` | As-Soon-As-Possible or As-Late-As-Possible |
| `respect_constraints` | boolean | — | Whether to honor `TaskConstraint` records |
| `dry_run` | boolean | — | If `true`, returns preview without saving changes |

**Response `200 OK`**
```json
{
  "tasks_updated": 12,
  "tasks_unchanged": 3,
  "warnings": [],
  "preview": [
    {
      "task_id": "uuid",
      "task_name": "Diseño arquitectura",
      "old_start": "2026-03-01",
      "old_end": "2026-03-10",
      "new_start": "2026-03-01",
      "new_end": "2026-03-08"
    }
  ]
}
```

---

## 2. Scheduling — Level Resources

### `POST /projects/{projectId}/scheduling/level-resources/`

Adjusts task dates to avoid resource over-allocation.

**Request body**
```json
{
  "max_daily_hours": 8.0,
  "dry_run": false
}
```

**Response `200 OK`**
```json
{
  "tasks_shifted": 5,
  "max_overallocation_before": 14.5,
  "max_overallocation_after": 0.0,
  "preview": [...]
}
```

---

## 3. Scheduling — Critical Path

### `GET /projects/{projectId}/scheduling/critical-path/`

Returns the list of task IDs that form the critical path.

**Response `200 OK`**
```json
{
  "critical_path": ["uuid-task-1", "uuid-task-4", "uuid-task-7"],
  "project_duration_days": 45,
  "calculated_at": "2026-03-27T10:00:00Z"
}
```

---

## 4. Scheduling — Task Float

### `GET /tasks/{taskId}/scheduling/float/`

Returns the total float (slack) in days for a single task.

**Response `200 OK`**
```json
{
  "task_id": "uuid",
  "task_name": "Instalación de equipos",
  "total_float_days": 5,
  "free_float_days": 3,
  "is_critical": false
}
```

---

## 5. Task Constraints — List

### `GET /tasks/{taskId}/constraints/`

Returns all scheduling constraints for a task.

**Response `200 OK`**
```json
[
  {
    "id": "uuid",
    "task": "uuid",
    "constraint_type": "SNET",
    "constraint_date": "2026-04-01",
    "created_at": "2026-03-20T09:00:00Z"
  }
]
```

---

## 6. Task Constraints — Create

### `POST /tasks/{taskId}/constraints/`

Sets a new scheduling constraint for a task.

**Request body**
```json
{
  "constraint_type": "SNET",
  "constraint_date": "2026-04-01"
}
```

**Constraint types**
| Code | Name | Date required |
|---|---|---|
| `ASAP` | As Soon As Possible | No |
| `ALAP` | As Late As Possible | No |
| `SNET` | Start No Earlier Than | Yes |
| `SNLT` | Start No Later Than | Yes |
| `FNET` | Finish No Earlier Than | Yes |
| `FNLT` | Finish No Later Than | Yes |
| `MSO` | Must Start On | Yes |
| `MFO` | Must Finish On | Yes |

**Response `201 Created`** — returns created constraint object.

---

## 7. Task Constraints — Delete

### `DELETE /tasks/{taskId}/constraints/{constraintId}/`

Removes a scheduling constraint.

**Response `204 No Content`**

---

## 8. Baselines — List

### `GET /projects/{projectId}/baselines/`

Returns all baselines for a project.

**Response `200 OK`**
```json
[
  {
    "id": "uuid",
    "name": "Baseline v1",
    "description": "Línea base inicial",
    "created_at": "2026-03-01T08:00:00Z",
    "is_active_baseline": true,
    "task_count": 15
  }
]
```

---

## 9. Baselines — Create

### `POST /projects/{projectId}/baselines/`

Captures a snapshot of all current task dates as a baseline.

**Request body**
```json
{
  "name": "Baseline v1",
  "description": "Línea base inicial",
  "set_as_active": true
}
```

**Response `201 Created`** — returns full baseline detail with task snapshots.

---

## 10. Baselines — Delete

### `DELETE /baselines/{baselineId}/`

Deletes a baseline. **The active baseline cannot be deleted** (returns `400`).

**Response `204 No Content`**

---

## 11. Baselines — Compare

### `GET /baselines/{baselineId}/compare/`

Compares current task dates against the baseline snapshot.

**Response `200 OK`**
```json
{
  "baseline_name": "Baseline v1",
  "summary": {
    "total_tasks": 15,
    "on_schedule": 10,
    "ahead": 2,
    "behind": 3
  },
  "tasks": [
    {
      "task_id": "uuid",
      "task_name": "Diseño arquitectura",
      "baseline_start": "2026-03-01",
      "actual_start": "2026-03-03",
      "start_variance_days": 2,
      "baseline_end": "2026-03-10",
      "actual_end": "2026-03-12",
      "end_variance_days": 2,
      "status": "behind"
    }
  ]
}
```

---

## 12. What-If Scenarios — List

### `GET /projects/{projectId}/scenarios/`

Returns all what-if scenarios for a project.

**Response `200 OK`**
```json
[
  {
    "id": "uuid",
    "name": "Escenario optimista",
    "description": "Reducir duración 20%",
    "created_at": "2026-03-25T14:00:00Z",
    "simulation_run": true,
    "simulation_date": "2026-03-25T14:05:00Z"
  }
]
```

---

## 13. What-If Scenarios — Create

### `POST /projects/{projectId}/scenarios/`

Creates a new what-if scenario definition.

**Request body**
```json
{
  "name": "Escenario optimista",
  "description": "Reducir duración 20%",
  "task_changes": {
    "uuid-task-1": { "duracion_dias": 5 }
  },
  "resource_changes": {},
  "dependency_changes": {
    "new": { "retraso_dias": 0 }
  }
}
```

**Response `201 Created`** — returns scenario object.

---

## 14. What-If Scenarios — Run Simulation

### `POST /scenarios/{scenarioId}/run/`

Runs the simulation and computes the projected schedule for this scenario.

**Request body** — empty `{}`

**Response `200 OK`**
```json
{
  "scenario_id": "uuid",
  "simulation_date": "2026-03-27T10:30:00Z",
  "projected_end_date": "2026-06-15",
  "delta_days": -8,
  "affected_tasks": 12
}
```

---

## 15. What-If Scenarios — Compare

### `POST /scenarios/compare/`

Side-by-side comparison of multiple scenarios.

**Request body**
```json
{
  "scenario_ids": ["uuid-a", "uuid-b"],
  "include_baseline": true
}
```

**Response `200 OK`**
```json
{
  "rows": [
    {
      "task_id": "uuid",
      "task_name": "Diseño arquitectura",
      "baseline_end": "2026-03-10",
      "scenario_a_end": "2026-03-08",
      "scenario_b_end": "2026-03-12"
    }
  ]
}
```

---

## Error responses

| Status | Meaning |
|---|---|
| `400 Bad Request` | Invalid input, constraint conflict, or trying to delete active baseline |
| `401 Unauthorized` | Missing or expired JWT |
| `403 Forbidden` | User lacks permission for this project |
| `404 Not Found` | Project, task, baseline, or scenario not found |
| `409 Conflict` | Circular dependency detected during scheduling |
