# FEATURE-6-TASK-BREAKDOWN.md
# Advanced Scheduling — Desglose de Épicas y Tareas

**Fecha:** 27 Marzo 2026
**Feature:** #6 — Advanced Scheduling
**Complejidad:** L (Large)
**Estimación:** 2–3 semanas

---

## Hallazgos del análisis de código base

### Lo que ya existe (reusar)
- `TaskDependency`: FS, SS, FF + `retraso_dias` — base para CPM
- `ResourceAssignment`: `porcentaje_asignacion`, `fecha_inicio`, `fecha_fin` — base para leveling
- `ResourceCapacity`: `horas_por_semana` — capacidad máxima por usuario
- `ResourceAvailability`: ausencias aprobadas — descuento de capacidad

### Lo que NO existe (construir)
- Algoritmo CPM (ninguna implementación encontrada en tarea_services.py)
- Tipo de dependencia SF (Start-to-Finish) — **no agregar al MVP**, no es estándar en construcción
- Baselines, Constraints, Scenarios — cero implementación

### Campos reales del modelo Task
| Campo en código | Descripción |
|---|---|
| `fecha_inicio` | Start date |
| `fecha_fin` | End date |
| `horas_estimadas` | Effort |
| `fecha_limite` | Deadline (no scheduling) |

> ⚠️ El feature doc menciona `start_date`/`end_date` — los campos reales son `fecha_inicio`/`fecha_fin`.

---

## ÉPICA 1: Backend — Scheduling Engine

**Descripción:** Algoritmos CPM, auto-scheduling ASAP/ALAP, float calculation.
**Archivos nuevos:** `scheduling_services.py`
**Complejidad:** Alta (algorítmica)

### Tareas

| ID | Tarea | Complejidad | Horas est. |
|----|-------|-------------|-----------|
| SK-01 | Modelo `ProjectBaseline` (snapshot JSON) | Baja | 2h |
| SK-02 | Modelo `TaskConstraint` (8 tipos) | Baja | 1.5h |
| SK-03 | Modelo `WhatIfScenario` (simulaciones) | Baja | 2h |
| SK-04 | Migración 0016 | Baja | 0.5h |
| SK-05 | Serializers (List/Detail/Create para los 3 modelos) | Media | 3h |
| SK-06 | `SchedulingService.topological_sort()` — Kahn's algorithm | Alta | 3h |
| SK-07 | `SchedulingService.forward_pass()` — early start/finish | Alta | 3h |
| SK-08 | `SchedulingService.backward_pass()` — late start/finish | Alta | 2h |
| SK-09 | `SchedulingService.calculate_float()` — total/free float | Media | 2h |
| SK-10 | `SchedulingService.get_critical_path()` — tareas con float=0 | Media | 1h |
| SK-11 | `SchedulingService.auto_schedule_asap()` — reprogramar ASAP | Alta | 4h |
| SK-12 | `SchedulingService.auto_schedule_alap()` — reprogramar ALAP | Media | 2h |
| SK-13 | `SchedulingService.apply_constraints()` — respetar restricciones | Alta | 3h |
| SK-14 | `ResourceLevelingService.detect_overload_periods()` | Alta | 3h |
| SK-15 | `ResourceLevelingService.level_resources()` — mover tareas con float | Alta | 4h |
| SK-16 | `BaselineService.create_baseline()` — snapshot JSON | Media | 2h |
| SK-17 | `BaselineService.compare_to_baseline()` — delta análisis | Media | 2h |
| SK-18 | `WhatIfService.create_scenario()` — clonar + aplicar cambios | Alta | 4h |
| SK-19 | `WhatIfService.run_simulation()` — ejecutar scheduling en clon | Alta | 3h |
| SK-20 | `WhatIfService.compare_scenarios()` — tabla comparativa | Media | 2h |
| SK-21 | Views: 15 endpoints REST | Media | 5h |
| SK-22 | URLs: nuevo prefijo `/api/v1/projects/.../scheduling/` | Baja | 1h |
| SK-23 | Tests: scheduling_services >= 85% cobertura | Alta | 8h |
| SK-24 | `python manage.py check` + migrate | Baja | 0.5h |

**Subtotal Épica 1:** ~62h (~8 días)

---

## ÉPICA 2: Backend — Índices y Performance

**Descripción:** Optimizar queries para scheduling con proyectos grandes.
**Sin archivos nuevos:** Solo migraciones con índices adicionales.

| ID | Tarea | Complejidad | Horas est. |
|----|-------|-------------|-----------|
| SK-25 | Índice `Task(fecha_inicio, fecha_fin)` | Baja | 0.5h |
| SK-26 | Índice `Task(proyecto, estado, fecha_inicio)` | Baja | 0.5h |
| SK-27 | Índice `TaskDependency(tarea_predecesora, tarea_sucesora)` | Baja | 0.5h |
| SK-28 | Prueba de performance: 100/500/1000 tareas | Media | 3h |
| SK-29 | Cache de ruta crítica (Django cache framework, TTL 5min) | Media | 2h |

**Subtotal Épica 2:** ~6.5h

---

## ÉPICA 3: Frontend — Modelos + Servicios Angular

| ID | Tarea | Complejidad | Horas est. |
|----|-------|-------------|-----------|
| SK-30 | Interfaces TS: `SchedulingResult`, `FloatData`, `TaskConstraint` | Baja | 1.5h |
| SK-31 | Interfaces TS: `ProjectBaseline`, `BaselineComparison` | Baja | 1h |
| SK-32 | Interfaces TS: `WhatIfScenario`, `SimulationResult` | Baja | 1h |
| SK-33 | `scheduling.service.ts`: auto-schedule, leveling, float, CPM | Media | 3h |
| SK-34 | `baseline.service.ts`: create, list, compare | Media | 2h |
| SK-35 | `what-if.service.ts`: create, run, compare scenarios | Media | 2h |

**Subtotal Épica 3:** ~10.5h

---

## ÉPICA 4: Frontend — Componentes Angular Material

| ID | Tarea | Complejidad | Horas est. |
|----|-------|-------------|-----------|
| SK-36 | `AutoScheduleDialogComponent` — MatDialog con preview | Media | 4h |
| SK-37 | `TaskConstraintsPanelComponent` — panel lateral con mat-list | Media | 3h |
| SK-38 | `BaselineComparisonComponent` — tabla mat-table comparativa | Media | 4h |
| SK-39 | `WhatIfScenarioBuilderComponent` — formulario + preview | Alta | 5h |
| SK-40 | `FloatIndicatorComponent` — badge/chip reutilizable | Baja | 1.5h |
| SK-41 | Integración Gantt: baseline bars + critical path + float | Alta | 5h |
| SK-42 | Botón "Auto-Schedule" en ProyectoDetail toolbar | Baja | 1h |
| SK-43 | Tab "Scheduling" en ProyectoDetail | Media | 2h |
| SK-44 | TypeScript strict check + compilación limpia | Media | 2h |

**Subtotal Épica 4:** ~27.5h (~3.5 días)

---

## ÉPICA 5: Testing y Validación

| ID | Tarea | Complejidad | Horas est. |
|----|-------|-------------|-----------|
| SK-45 | Tests modelo: ProjectBaseline, TaskConstraint, WhatIfScenario | Media | 3h |
| SK-46 | Tests services: SchedulingService (topological, CPM, float) | Alta | 5h |
| SK-47 | Tests services: ResourceLevelingService | Alta | 4h |
| SK-48 | Tests services: BaselineService, WhatIfService | Media | 4h |
| SK-49 | Tests views: 15 endpoints (auth, permisos, multi-tenant) | Media | 4h |

**Subtotal Épica 5:** ~20h

---

## ÉPICA 6: Documentación

| ID | Tarea | Complejidad | Horas est. |
|----|-------|-------------|-----------|
| SK-50 | `FEATURE-6-API-DOCS.md`: 15 endpoints | Baja | 3h |
| SK-51 | `FEATURE-6-USER-GUIDE.md`: Guía usuario PM | Baja | 2h |
| SK-52 | Actualizar `CONTEXT.md` y `DECISIONS.md` | Baja | 1h |

**Subtotal Épica 6:** ~6h

---

## Resumen de estimación

| Épica | Horas | Días |
|-------|-------|------|
| Backend Scheduling Engine | 62h | 8 días |
| Backend Performance | 6.5h | 1 día |
| Frontend Modelos/Servicios | 10.5h | 1.5 días |
| Frontend Componentes | 27.5h | 3.5 días |
| Testing | 20h | 2.5 días |
| Documentación | 6h | 1 día |
| **TOTAL** | **132.5h** | **~17-18 días** |

> Estimación con 7.5h/día de desarrollo efectivo. Paralelizar épicas 1+2 con épicas 3+4 reduce el timeline real a 10-12 días.

---

## Complejidad algorítmica — Evaluación Go vs Django

### Criterio 1: Alta concurrencia
❌ No aplica — scheduling es batch, no tiempo real.

### Criterio 2: Procesamiento intensivo
⚠️ **CONDICIONAL**:
- <100 tareas: Python OK (<500ms esperado)
- 500 tareas: Python estimado ~2-3s
- 1000 tareas: Python estimado ~5-8s (supera umbral)

**Decisión:** Django + Python para MVP. Si pruebas con 1000 tareas superan 5s → evaluar Celery async o Go microservice en iteración posterior.

### Criterio 3 y 4
❌ No aplican para este caso.

**Veredicto: Django para MVP. Celery task para auto-schedule async si es necesario.**

---

## Riesgos identificados

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|-----------|
| CPM sin fechas completas en tareas | Alta | Alta | Validar `fecha_inicio`/`fecha_fin` antes de scheduling |
| Resource leveling produce loops infinitos | Media | Alta | Límite de iteraciones (max 1000 ciclos) |
| What-If scenarios consumen mucha memoria | Media | Media | Snapshot en JSON, no clonar ORM objects |
| Integración Gantt existente (Frappe) compleja | Media | Media | Investigar API Frappe antes de implementar |
| Task sin `fecha_inicio` rompe CPM | Alta | Alta | `dry_run` mode con warnings previos |

---

*Generado: 27 Marzo 2026 — Phase 0 Feature #6*
