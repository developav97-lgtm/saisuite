# FEATURE-6-EXECUTION-PLAN.md
# Advanced Scheduling — Plan de Ejecución

**Fecha:** 27 Marzo 2026
**Feature:** #6 — Advanced Scheduling
**Stack:** Django 5 + Angular 18 + Angular Material (DEC-011)

---

## Secuencia de ejecución obligatoria

Seguir el orden definido en CLAUDE.md §5. No invertir pasos.

---

## CHUNK 1 — Modelos + Migración
**Sesión:** 1 (actual)
**Limpiar contexto después de este chunk**

```
SK-01  Modelo ProjectBaseline
SK-02  Modelo TaskConstraint
SK-03  Modelo WhatIfScenario
SK-04  Migración 0016
       → python manage.py makemigrations
       → python manage.py migrate
       → python manage.py check
```

**Criterio de salida:** `migrate` exitoso, `check` sin errores.
**→ /clear aquí**

---

## CHUNK 2 — Serializers + Scheduling Core
**Sesión:** 2
**Limpiar contexto después de este chunk**

```
SK-05  Serializers (9 clases: List/Detail/Create × 3 modelos)
SK-06  SchedulingService.topological_sort()    ← PRIMERO (base de todo)
SK-07  SchedulingService.forward_pass()
SK-08  SchedulingService.backward_pass()
SK-09  SchedulingService.calculate_float()
SK-10  SchedulingService.get_critical_path()
```

**Criterio de salida:** Tests unitarios de CPM pasando (SK-46 parcial).
**→ /clear aquí**

---

## CHUNK 3 — Auto-Schedule + Resource Leveling
**Sesión:** 3
**Limpiar contexto después de este chunk**

```
SK-11  SchedulingService.auto_schedule_asap()
SK-12  SchedulingService.auto_schedule_alap()
SK-13  SchedulingService.apply_constraints()
SK-14  ResourceLevelingService.detect_overload_periods()
SK-15  ResourceLevelingService.level_resources()
```

**Criterio de salida:** Auto-schedule ASAP + ALAP con tests pasando.
**→ /clear aquí**

---

## CHUNK 4 — Baselines + What-If + Views + URLs
**Sesión:** 4
**Limpiar contexto después de este chunk**

```
SK-16  BaselineService.create_baseline()
SK-17  BaselineService.compare_to_baseline()
SK-18  WhatIfService.create_scenario()
SK-19  WhatIfService.run_simulation()
SK-20  WhatIfService.compare_scenarios()
SK-21  Views: 15 endpoints REST
SK-22  URLs: scheduling endpoints
SK-25–SK-29  Índices + cache
```

**Criterio de salida:** `python manage.py check` + Postman/curl manual en todos los endpoints.
**→ /clear aquí**

---

## CHUNK 5 — Tests backend >= 85%
**Sesión:** 5
**Limpiar contexto después de este chunk**

```
SK-45  Tests modelos
SK-46  Tests SchedulingService (completo)
SK-47  Tests ResourceLevelingService
SK-48  Tests BaselineService + WhatIfService
SK-49  Tests views
SK-28  Prueba performance 100/500/1000 tareas
```

**Criterio de salida:** `pytest --cov >= 85%` en scheduling_services.py.
**→ /clear aquí**

---

## CHUNK 6 — Frontend Modelos + Servicios
**Sesión:** 6
**Limpiar contexto después de este chunk**

```
SK-30–SK-32  Interfaces TypeScript (scheduling, baseline, what-if)
SK-33  scheduling.service.ts
SK-34  baseline.service.ts
SK-35  what-if.service.ts
```

**Criterio de salida:** `ng build --configuration=production` sin errores.
**→ /clear aquí**

---

## CHUNK 7 — Frontend Componentes
**Sesión:** 7
**Limpiar contexto después de este chunk**

```
SK-36  AutoScheduleDialogComponent
SK-37  TaskConstraintsPanelComponent
SK-38  BaselineComparisonComponent
SK-39  WhatIfScenarioBuilderComponent
SK-40  FloatIndicatorComponent
SK-42  Botón Auto-Schedule en ProyectoDetail
SK-43  Tab Scheduling en ProyectoDetail
SK-44  TypeScript strict check
```

**Criterio de salida:** Todos los componentes renderizan sin errores en dev.
**→ /clear aquí**

---

## CHUNK 8 — Integración Gantt + Documentación
**Sesión:** 8

```
SK-41  Gantt: baseline bars + critical path + float indicators
SK-50  FEATURE-6-API-DOCS.md
SK-51  FEATURE-6-USER-GUIDE.md
SK-52  Actualizar CONTEXT.md + DECISIONS.md
```

**Criterio de salida:** Feature #6 completa y documentada.

---

## Handoffs críticos

| Handoff | Bloqueante para |
|---------|----------------|
| Chunk 1 completo (modelos) | Chunk 2 puede comenzar |
| Chunk 2 completo (CPM core) | Chunks 3 y 4 pueden comenzar |
| Chunk 4 completo (APIs) | Chunks 6 y 7 pueden comenzar |
| Chunk 5 completo (tests) | PR backend listo para review |

---

## Riesgos y plan de contingencia

### Riesgo 1: Tareas sin fechas
**Síntoma:** `fecha_inicio` o `fecha_fin` nulos en muchas tareas.
**Plan:** Auto-schedule solo procesa tareas con ambas fechas. Las demás quedan excluidas con warning.

### Riesgo 2: Performance > 5s en 1000 tareas
**Síntoma:** Prueba SK-28 falla umbral.
**Plan:** Implementar Celery task async + polling desde frontend (no bloquear UI).

### Riesgo 3: Gantt Frappe API compleja
**Síntoma:** Frappe no permite overlay fácil de baseline bars.
**Plan:** Añadir leyenda separada debajo del Gantt en vez de overlay inline.

### Riesgo 4: Ciclos en dependencias
**Síntoma:** `topological_sort()` detecta ciclo (A→B→A).
**Plan:** Detectar ciclo y retornar error 400 con lista de tareas en conflicto.

---

## Criterios de aceptación finales Feature #6

### Backend ✅
- [ ] 3 modelos nuevos migrados
- [ ] CPM (forward + backward pass) correcto
- [ ] Auto-schedule ASAP y ALAP funciona
- [ ] Resource leveling balancea sin loops infinitos
- [ ] Baselines guardan snapshot JSON
- [ ] What-if simula sin afectar datos reales
- [ ] 15 endpoints REST operativos
- [ ] Tests >= 85% en scheduling_services.py
- [ ] Performance: 100 tareas < 500ms, 500 tareas < 3s

### Frontend ✅
- [ ] AutoScheduleDialog muestra preview antes de aplicar
- [ ] TaskConstraints panel funcional
- [ ] BaselineComparison tabla comparativa
- [ ] WhatIfScenarioBuilder crea y corre simulaciones
- [ ] Gantt muestra ruta crítica en color diferente
- [ ] TypeScript compila sin errores strict

### Funcional ✅
- [ ] PM puede auto-schedule y ver nuevas fechas en Gantt
- [ ] PM puede crear baseline "Original Plan"
- [ ] PM puede simular "qué pasa si agrego un recurso"
- [ ] Sistema detecta y señala ruta crítica automáticamente

---

*Generado: 27 Marzo 2026 — Phase 0 Feature #6*
