# PLAN DE CORRECCIÓN COMPLETO — SAICLOUD GESTOR DE PROYECTOS
**Fecha:** 28 Marzo 2026
**Fuentes:** Auditoría técnica (21 gaps) + Validación funcional gestor (5 bugs + 8 gaps + 8 UX)
**Total items únicos:** 34
**Ejecución estimada:** 46–60 horas (2 semanas)

---

## 1. RESUMEN EJECUTIVO

| Severidad | Items | % | Score total | Sprint |
|---|---|---|---|---|
| Crítica | 6 | 18% | 72 | Sprint 1 |
| Alta | 8 | 24% | 71 | Sprint 1–2 |
| Media | 10 | 29% | 66 | Sprint 2 |
| Baja | 10 | 29% | 35 | Backlog |
| **Total** | **34** | | **244** | |

### Deduplicación realizada

| Fuente Auditoría | Fuente Validación | Resultado |
|---|---|---|
| GAP #1 (Tabs faltantes) | GAP-1, GAP-5, GAP-6 | → EPIC-1 |
| GAP #2 (UI Tarifas EVM) | GAP-3 (AC=0) | → EPIC-4 |
| GAP #3 (costs/by-resource errores) | UX-1 (EVM muestra —) | → EPIC-4 |
| GAP #4 (Timesheet no enrutado) | GAP-4 (vista semanal sin ruta) | → EPIC-1 |
| GAP #7 (What-If sin cambios) | GAP-2 (solo nombre/desc) | → EPIC-6 |
| GAP #9 (sin Mis Tareas) | GAP-7 (sin vista Mis Tareas) | → EPIC-3 |
| BUG #1 (Gantt InvalidCharacterError) | BUG-1 | → EPIC-2 |
| BUG #2A (formatDate null crash) | BUG-2A | → EPIC-5 |
| BUG #2B (Tab Equipo vacío) | BUG-2B | → EPIC-5 |
| BUG #3 (Hitos 404) | BUG-3 | → EPIC-7 |
| BUG #4 (cantidad_planificada) | BUG-4 | → EPIC-8 |

---

## 2. TABLA UNIFICADA — 34 ITEMS CON SCORE MATEMÁTICO

**Scoring:** I = Impacto (3=inutilizable, 2=degradado, 1=cosmético) | F = Frecuencia (3=diario, 2=semanal, 1=raro) | E = Esfuerzo fix (3=simple, 2=medio, 1=complejo) | **Score = (I × F) × E**

| ID | Descripción | Severidad | I | F | E | Score | Épica |
|---|---|---|---|---|---|---|---|
| C-01 | Tab Equipo siempre vacío — ResourceAssignment no sincroniza con Task.responsable | Crítica | 3 | 3 | 2 | 18 | EPIC-5 |
| C-02 | Hitos: endpoint /milestones/{id}/generar-factura/ → 404 — no implementado | Crítica | 3 | 2 | 2 | 12 | EPIC-7 |
| C-03 | UI de tarifas de costo por recurso faltante — EVM siempre muestra AC=0 | Crítica | 3 | 2 | 1 | 6 | EPIC-4 |
| C-04 | No hay tab "Tareas" dentro del proyecto — PM debe ir a /proyectos/tareas | Crítica | 3 | 3 | 2 | 18 | EPIC-1 |
| C-05 | Tab "Timesheets" del proyecto faltante — horas del equipo no visibles | Crítica | 3 | 2 | 2 | 12 | EPIC-1 |
| C-06 | Endpoints /costs/by-resource/ y /costs/by-task/ generan error 500/404 | Crítica | 3 | 2 | 2 | 12 | EPIC-4 |
| A-01 | Tab Equipo crash con fecha nula en formatDate() — null check faltante | Alta | 3 | 3 | 3 | 27 | EPIC-5 |
| A-02 | What-If sin UI para definir cambios — modal solo acepta nombre/descripción | Alta | 2 | 2 | 1 | 4 | EPIC-6 |
| A-03 | TaskConstraintsPanelComponent existe pero no integrado en tarea-detail | Alta | 2 | 2 | 3 | 12 | EPIC-6 |
| A-04 | Nivelación de recursos — solo backend, sin UI en Auto-Schedule | Alta | 2 | 1 | 3 | 6 | EPIC-6 |
| A-05 | Vista semanal timesheets — componente existe, ruta activa pero no expuesta en sidebar | Alta | 2 | 3 | 3 | 18 | EPIC-1 |
| A-06 | Lista global de tareas muestra 0 resultados — condición de carrera ngOnInit | Alta | 3 | 3 | 2 | 18 | EPIC-3 |
| A-07 | Tab "Kanban" contextual en proyecto faltante | Alta | 2 | 2 | 2 | 8 | EPIC-1 |
| A-08 | Dashboard multiproyecto sin analytics — solo pantalla de bienvenida | Alta | 2 | 2 | 1 | 4 | EPIC-9 |
| M-01 | Gantt crash InvalidCharacterError al activar Ruta Crítica — IDs con caracteres inválidos | Media | 2 | 3 | 3 | 18 | EPIC-2 |
| M-02 | Bloquea edición de cantidad_planificada en estado Borrador — validación incorrecta | Media | 2 | 2 | 3 | 12 | EPIC-8 |
| M-03 | Vista "Mis Tareas" personal — ruta existe pero sin filtro automático de usuario | Media | 2 | 3 | 2 | 12 | EPIC-3 |
| M-04 | Tipo de tercero muestra "CUSTOMER" en inglés | Media | 1 | 2 | 3 | 6 | EPIC-8 |
| M-05 | Campo cliente en tab General muestra UUID interno en lugar de NIT | Media | 2 | 2 | 2 | 8 | EPIC-8 |
| M-06 | Overlay holgura (Float) solo muestra críticas; tareas no críticas sin dato | Media | 2 | 2 | 2 | 8 | EPIC-2 |
| M-07 | Auto-Schedule dialog no muestra previsualización de cambios propuestos | Media | 2 | 2 | 2 | 8 | EPIC-6 |
| M-08 | Indicador de fase activa sin diferenciación visual de color en la lista | Media | 1 | 3 | 3 | 9 | EPIC-3 |
| M-09 | Botones activar/completar fase no visibles en fase-list | Media | 2 | 2 | 3 | 12 | EPIC-3 |
| M-10 | Reordenamiento de fases — solo campo numérico, sin drag-and-drop visual | Media | 1 | 1 | 1 | 1 | EPIC-9 |
| B-01 | EVM muestra "—" sin tooltip explicativo contextual | Baja | 1 | 2 | 3 | 6 | EPIC-4 |
| B-02 | Gantt sin exportación PDF/imagen para reportes al cliente | Baja | 2 | 2 | 1 | 4 | EPIC-2 |
| B-03 | Formulario tarea no preselecciona proyecto en contexto | Baja | 1 | 3 | 2 | 6 | EPIC-3 |
| B-04 | Tarjetas Kanban sin fecha límite visible | Baja | 1 | 2 | 3 | 6 | EPIC-3 |
| B-05 | Tab "Actividades de Obra" — nombre inadecuado para proyectos no civiles | Baja | 1 | 2 | 3 | 6 | EPIC-8 |
| B-06 | Auto-Schedule sin tabla de impacto por tarea antes de aplicar | Baja | 1 | 2 | 2 | 4 | EPIC-6 |
| B-07 | FloatIndicatorComponent existe pero no integrado en tarea-detail | Baja | 1 | 1 | 3 | 3 | EPIC-2 |
| B-08 | Tipo "Hito" faltante en catálogo de actividades | Baja | 1 | 1 | 2 | 2 | EPIC-8 |
| B-09 | Baselines sin comparación tabular visual baseline vs plan actual | Baja | 1 | 1 | 2 | 2 | EPIC-6 |
| B-10 | Nivelación de recursos no disponible en UI del Auto-Schedule | Baja | 1 | 1 | 2 | 2 | EPIC-6 |

---

## 3. ÉPICAS PRIORIZADAS (9 ÉPICAS)

### EPIC-1 — Tabs Faltantes en Detalle del Proyecto
**Score acumulado:** 56 | **Estimación:** 6–10h | **Agente:** Frontend Developer

**Items:** C-04, C-05, A-05, A-07

**Descripción:** El detalle del proyecto carece de tabs fundamentales para el flujo de trabajo del PM: Tareas (filtradas por proyecto), Kanban contextual, y timesheets del proyecto. El HTML ya tiene los tabs declarados pero los componentes hijos no reciben `proyectoId` correctamente o tienen condición de carrera al cargarlo.

**Archivos a modificar:**
- `frontend/src/app/features/proyectos/components/proyecto-detail/proyecto-detail.component.html` — verificar integración con `[proyectoId]="p.id"`
- `frontend/src/app/features/proyectos/components/tarea-list/tarea-list.component.ts` — input() signal + effect() para recargar
- `frontend/src/app/features/proyectos/components/tarea-kanban/tarea-kanban.component.ts` — mismo patrón
- `frontend/src/app/core/components/sidebar/sidebar.component.ts` — confirmar ruta timesheets accesible

**Criterio de aceptación:**
1. Tab "Tareas" en proyecto muestra solo las tareas de ese proyecto (>0 si tiene tareas)
2. Tab "Kanban" muestra columnas con tareas filtradas por proyecto
3. Tab "Timesheets" muestra horas del equipo del proyecto
4. `/proyectos/timesheets` accesible desde sidebar

---

### EPIC-2 — Gantt: Estabilidad y Overlays Completos
**Score acumulado:** 29 | **Estimación:** 5–8h | **Agente:** Frontend Developer

**Items:** M-01, M-06, B-07, B-02

**Descripción:** frappe-gantt usa los IDs como atributos SVG. Si se usa el nombre de la tarea como ID (puede tener tildes, espacios), genera `InvalidCharacterError`. La solución es usar el UUID de la tarea. Adicionalmente, completar el overlay de holgura para tareas no críticas e integrar `FloatIndicatorComponent`.

**Archivos a modificar:**
- `frontend/src/app/features/proyectos/components/gantt-view/gantt-view.component.ts` — usar `t.id` (UUID) como ID en frappe-gantt, no el nombre de la tarea
- `gantt-view.component.ts` — en `toggleFloat()`, usar endpoint de float por tarea para no críticas
- Integrar `FloatIndicatorComponent` en `tarea-detail` si no está

**Criterio de aceptación:**
1. Activar "Ruta Crítica" en proyecto con tildes/espacios no lanza `InvalidCharacterError`
2. Barras de tareas críticas se colorean en rojo
3. Overlay de holgura muestra valores para tareas no críticas también

---

### EPIC-3 — Flujo de Tareas: Correcciones UX y Accesibilidad
**Score acumulado:** 63 | **Estimación:** 5–8h | **Agente:** Frontend Developer

**Items:** A-06, M-03, M-08, M-09, B-03, B-04

**Descripción:** La lista global de tareas tiene condición de carrera que produce 0 resultados. "Mis Tareas" existe como ruta pero sin filtro automático de usuario. Mejoras UX: fecha límite en Kanban, preselección de proyecto en formulario, botones de fase visibles.

**Archivos a modificar:**
- `frontend/.../tarea-list/tarea-list.component.ts` — usar `effect()` + `takeUntilDestroyed`, no `ngOnInit()`; en modo `misTareas`, precargar filtro `responsable=currentUser.id`
- `frontend/.../tarea-kanban/tarea-kanban.component.html` — agregar `fecha_limite` en tarjetas
- `frontend/.../tarea-form/tarea-form.component.ts` — preseleccionar proyecto desde query param
- `frontend/.../fase-list/fase-list.component.html` — agregar botones "Activar" y "Completar" con estados

**Criterio de aceptación:**
1. Lista global de tareas muestra resultados al cargar (no 0)
2. `/proyectos/mis-tareas` muestra solo tareas del usuario activo
3. Tarjetas Kanban muestran fecha límite si existe
4. Formulario nueva tarea preselecciona proyecto desde contexto

---

### EPIC-4 — EVM Funcional: Tarifas de Costo y Endpoints
**Score acumulado:** 24 | **Estimación:** 6–10h | **Agente:** Full-Stack

**Items:** C-03, C-06, B-01

**Descripción:** El módulo EVM es inútil sin tarifas de costo configuradas. `CostRateFormComponent` existe pero no está visible en el `BudgetDashboardComponent`. Los endpoints `/costs/by-resource/` y `/costs/by-task/` generan errores. Agregar tooltips explicativos en EVM para valores `—`.

**Archivos a modificar:**
- `backend/apps/proyectos/budget_services.py` — corregir `get_cost_by_resource()` y `get_cost_by_task()` para retornar lista vacía (no error) cuando no hay timesheets
- `frontend/.../budget-dashboard/budget-dashboard.component.html` — agregar sección "Tarifas por Recurso" con tabla y botón "Nueva tarifa" (método `openCostRateForm()` ya existe en TS)
- `budget-dashboard.component.html` — agregar `matTooltip` en métricas EVM con valor `—`

**Criterio de aceptación:**
1. Sección "Tarifas por Recurso" visible en Tab Presupuesto
2. Al agregar tarifa + aprobar timesheets, AC, CPI y SPI muestran valores reales
3. `/costs/by-resource/` y `/costs/by-task/` retornan 200 (no 500)
4. Métricas EVM con `—` muestran tooltip explicativo en hover

---

### EPIC-5 — Tab Equipo: Sincronización y Null Safety
**Score acumulado:** 45 | **Estimación:** 6–10h | **Agente:** Full-Stack

**Items:** A-01, C-01

**Descripción:** Dos problemas críticos independientes. (A) `formatDate()` crashea con fecha nula — fix de una línea. (B) `get_team_availability_timeline()` solo consulta `ResourceAssignment`, ignorando `Task.responsable`. El Tab Equipo siempre aparece vacío en el flujo normal de trabajo.

**Archivos a modificar:**
- `frontend/.../team-timeline/team-timeline.component.ts` — añadir `if (!date || isNaN(date.getTime())) return '';` al inicio de `formatDate()`
- `backend/apps/proyectos/resource_services.py` — en `get_team_availability_timeline()`, agregar query de `Task.responsable` y combinar con `ResourceAssignment`; para usuarios sin assignment explícito, generar asignaciones virtuales desde sus tareas

**Criterio de aceptación:**
1. Fecha inválida en rango del Tab Equipo no crashea (retorna silenciosamente)
2. Tab Equipo muestra miembros con `Task.responsable` aunque no tengan `ResourceAssignment`
3. Test unitario Django para el nuevo comportamiento

---

### EPIC-6 — Scheduling Avanzado: What-If, Restricciones, Nivelación
**Score acumulado:** 39 | **Estimación:** 10–16h | **Agente:** Frontend Developer

**Items:** A-02, A-03, A-04, M-07, B-06, B-09, B-10

**Descripción:** Tres funcionalidades incompletas: (a) What-If sin UI para cambios definidos; (b) `TaskConstraintsPanelComponent` implementado pero no integrado en `tarea-detail`; (c) Nivelación de recursos sin UI. Auto-Schedule sin previsualización de impacto.

**Archivos a modificar:**
- `frontend/.../what-if-scenario-builder/what-if-scenario-builder.component.ts` — agregar `FormArray` de cambios con `[task_id, field, new_value]`
- `frontend/.../tarea-detail/tarea-detail.component.html` — importar e integrar `TaskConstraintsPanelComponent`
- `frontend/.../auto-schedule-dialog/auto-schedule-dialog.component.html` — agregar sección de previsualización + opción "Nivelar recursos"

**Criterio de aceptación:**
1. What-If permite agregar cambios (tarea + campo + valor) antes de simular
2. Tab "Restricciones" visible en detalle de tarea
3. Dialog Auto-Schedule tiene opción de nivelar recursos
4. Dialog muestra tabla de impacto (tareas afectadas + delta días)

---

### EPIC-7 — Hitos: Endpoint generar-factura Funcional
**Score acumulado:** 12 | **Estimación:** 2–4h | **Agente:** Full-Stack

**Items:** C-02

**Descripción:** El frontend llama a `/generar-factura/` (español) pero el backend migró a `/generate-invoice/` (inglés) en REFT-09. Fix de una línea en el servicio Angular + verificación del action URL en el ViewSet.

**Archivos a modificar:**
- `frontend/src/app/features/proyectos/services/hito.service.ts` — cambiar `generar-factura/` por `generate-invoice/`
- `backend/apps/proyectos/views.py` — verificar que `@action(url_path='generate-invoice')` está en `MilestoneViewSet`

**Criterio de aceptación:**
1. Click en icono de factura de hito facturable no retorna 404
2. El hito pasa a estado `facturado=True` con fecha de facturación
3. Si el proyecto no está en ejecución, retorna 400 con mensaje claro

---

### EPIC-8 — Correcciones de Lógica de Negocio y Traducción
**Score acumulado:** 34 | **Estimación:** 4–6h | **Agente:** Full-Stack

**Items:** M-02, M-04, M-05, B-05, B-08

**Descripción:** Cuatro correcciones menores pero con impacto real: (1) serializer bloquea `cantidad_planificada` en estado Borrador confundiendo validaciones; (2) tipo tercero en inglés; (3) NIT cliente muestra UUID; (4) nombre "Actividades de Obra" inadecuado.

**Archivos a modificar:**
- `backend/apps/proyectos/serializers.py` — `validate()` de `ProjectActivitySerializer`: la restricción de estado solo aplica a `cantidad_ejecutada`, no a `cantidad_planificada`
- `backend/apps/terceros/serializers.py` — campo `tipo` usando `get_tipo_display()` en español
- `backend/apps/proyectos/serializers.py` — `ProjectSerializer`: exponer `cliente_nit` computado (no UUID)
- `frontend/.../proyecto-detail/proyecto-detail.component.html` — nombre dinámico del tab según tipo de proyecto

**Criterio de aceptación:**
1. PATCH `/projects/{id}/activities/{pk}/` con `{cantidad_planificada: 5}` en estado `draft` → 200
2. PATCH con `{cantidad_ejecutada: 5}` en estado `draft` → 400 con mensaje claro
3. Tipo de tercero muestra "Cliente" / "Proveedor" (no "CUSTOMER")
4. Tab renombrado según tipo de proyecto

---

### EPIC-9 — Dashboard Multiproyecto y Mejoras UX Opcionales
**Score acumulado:** 9 | **Estimación:** 10–16h | **Agente:** Frontend Developer + UI Designer

**Items:** A-08, M-10, B-02

**Descripción:** Dashboard principal sin analytics. El endpoint `analytics/compare/` ya está implementado en backend. Mejoras opcionales de baja prioridad: drag-and-drop para fases, exportación PDF del Gantt.

**Archivos a modificar:**
- `frontend/src/app/features/dashboard/` — implementar `DashboardComponent` con cards de proyectos activos y KPIs usando `/api/v1/projects/analytics/compare/`
- `frontend/.../fase-list/fase-list.component.ts` — CDK DragDrop para reordenar
- `frontend/.../gantt-view/gantt-view.component.ts` — exportación PNG/PDF con `html2canvas` o SVG API

**Criterio de aceptación:**
1. Dashboard muestra resumen de proyectos activos con KPIs
2. Fases se reordenan con drag-and-drop
3. Botón "Exportar" en Gantt genera imagen descargable

---

## 4. ROADMAP 2 SEMANAS

```
SPRINT 1 — SEMANA 1 (28 Mar – 4 Abr 2026)
Foco: Bugs críticos + gaps de flujo principal del PM
═══════════════════════════════════════════════════════════════════════

Día 1–2 │ EPIC-7 (Hitos 404 — 2–4h)  +  EPIC-5-A (null-check — 1h)
         │ → Score 39 | Agente: Full-Stack
         │ Items cerrados: C-02, A-01

Día 3–4 │ EPIC-5-B (ResourceAssignment sync — 5–8h)
         │ → Score 18 | Agente: Backend Architect
         │ Items cerrados: C-01

Día 5   │ EPIC-8 (Lógica negocio + traducciones — 4–6h)
         │ → Score 34 | Agente: Full-Stack
         │ Items cerrados: M-02, M-04, M-05, B-05, B-08

                              ↓ FIN SPRINT 1
         Bugs críticos resueltos: BUG-2A, BUG-2B, BUG-3, BUG-4
         Items cerrados: C-01, C-02, A-01, M-02, M-04, M-05, B-05, B-08 (8 items)


SPRINT 2 — SEMANA 2 (5 Abr – 11 Abr 2026)
Foco: Gaps de valor alto + mejoras UX top
═══════════════════════════════════════════════════════════════════════

Día 1–2 │ EPIC-2 (Gantt estabilidad — 5–8h)
         │ → Score 29 | Agente: Frontend Developer
         │ Items cerrados: M-01, M-06, B-07

Día 3   │ EPIC-1 (Tabs faltantes — 6–10h)
         │ → Score 56 | Agente: Frontend Developer
         │ Items cerrados: C-04, C-05, A-05, A-07

Día 4   │ EPIC-3 (Flujo tareas UX — 5–8h)  [paralelo con EPIC-1 si hay 2 devs]
         │ → Score 63 | Agente: Frontend Developer
         │ Items cerrados: A-06, M-03, M-08, M-09, B-03, B-04

Día 5   │ EPIC-4 (EVM + tarifas — 6–10h)
         │ → Score 24 | Agente: Full-Stack
         │ Items cerrados: C-03, C-06, B-01

                              ↓ FIN SPRINT 2
         Items cerrados acumulados: 24 de 34 (71%)


SPRINT 3 — SEMANA 3+ (BACKLOG)
═══════════════════════════════════════════════════════════════════════
│ EPIC-6 (Scheduling avanzado — 10–16h)  → Score 39
│ EPIC-9 (Dashboard + DnD — 10–16h)      → Score 9
│ Items restantes: A-02, A-03, A-04, A-08, M-07, M-10, B-02, B-06, B-09, B-10
```

---

## 5. COMANDOS MULTI-AGENTE LISTOS PARA EJECUTAR

### Comando EPIC-7 — Hitos 404 (ejecutar primero, 2h)

```
TAREA: Corregir endpoint generar-factura en hitos

CONTEXTO: El frontend llama a /generar-factura/ (español) pero tras el rename REFT-09,
el backend expone /generate-invoice/ (inglés). Fix de una línea en el servicio Angular.

ARCHIVOS:
1. frontend/src/app/features/proyectos/services/hito.service.ts
   - Cambiar "generar-factura/" → "generate-invoice/"
2. backend/apps/proyectos/views.py
   - Verificar que MilestoneViewSet tiene @action(url_path='generate-invoice')

CRITERIO:
- POST /api/v1/projects/{id}/milestones/{pk}/generate-invoice/ retorna 200
- Hito pasa a facturado=True con fecha de facturación
- Error de validación retorna 400, no 404
```

---

### Comando EPIC-5-A — Null check formatDate (1h)

```
TAREA: Agregar null-check en TeamTimelineComponent.formatDate()

CONTEXTO: formatDate() en team-timeline.component.ts llama d.getFullYear() sin validar
que d no sea null/undefined. Una fecha inválida crashea el tab con TypeError.

ARCHIVO:
frontend/src/app/features/proyectos/components/team-timeline/team-timeline.component.ts

FIX: Primera línea de formatDate():
  if (!date || isNaN(date.getTime())) return '';

CRITERIO:
- Escribir texto inválido en campo de fecha de rango no crashea la pantalla
- El campo simplemente no actualiza la vista si la fecha es inválida
```

---

### Comando EPIC-5-B — Sincronización ResourceAssignment (5–8h)

```
TAREA: Tab Equipo — sincronizar ResourceAssignment con Task.responsable

CONTEXTO: get_team_availability_timeline() en resource_services.py (línea ~474) solo
consulta ResourceAssignment. Las tareas con Task.responsable asignado no aparecen.

ARCHIVO: backend/apps/proyectos/resource_services.py

ESTRATEGIA (Opción B — menos invasiva):
1. Después de obtener usuario_ids desde ResourceAssignment, agregar:
   task_resp_ids = list(
       Task.objects.filter(
           project_id=proyecto_id,
           responsable__isnull=False,
       ).values_list('responsable_id', flat=True).distinct()
   )
   usuario_ids = list(set(usuario_ids + task_resp_ids))

2. Para usuarios sin ResourceAssignment explícito, generar asignaciones virtuales
   desde sus tareas (fecha_inicio/fin de tarea, porcentaje_asignacion=100)

3. Agregar tests en backend/apps/proyectos/tests/

CRITERIO:
- Tab Equipo muestra miembros con Task.responsable aunque no tengan ResourceAssignment
- No regresión en tests existentes de resource_services
```

---

### Comando EPIC-8 — Lógica negocio + traducciones (4–6h)

```
TAREA: Corregir validación cantidad_planificada + traducciones de terceros

CONTEXTO PRINCIPAL: ProjectActivitySerializer.validate() bloquea cantidad_planificada
en estado Borrador mezclando la validación con cantidad_ejecutada.

ARCHIVOS:
1. backend/apps/proyectos/serializers.py
   - validate() de ProjectActivitySerializer: la restricción de estado debe aplicarse
     SOLO a cantidad_ejecutada. cantidad_planificada es editable en cualquier estado.

2. backend/apps/terceros/serializers.py
   - Campo tipo: usar get_tipo_display() para retornar "Cliente" no "CUSTOMER"

3. frontend/.../proyecto-detail/proyecto-detail.component.html
   - Tab "Actividades de Obra": nombre dinámico según tipo de proyecto

CRITERIO:
- PATCH con {cantidad_planificada: 5} en estado draft → 200
- PATCH con {cantidad_ejecutada: 5} en estado draft → 400 con mensaje claro
- Tipo de tercero muestra español en la UI
```

---

### Comando EPIC-2 — Gantt estabilidad (5–8h)

```
TAREA: Corregir crash InvalidCharacterError en Gantt al activar Ruta Crítica

CONTEXTO: frappe-gantt usa los IDs como atributos SVG. Si el ID contiene tildes,
espacios o caracteres especiales (ej: nombre de tarea), genera InvalidCharacterError.
Los UUIDs de Django solo tienen hex + guiones — son siempre válidos como IDs SVG.

ARCHIVO: frontend/.../gantt-view/gantt-view.component.ts

INVESTIGAR: Método que construye array de tareas para frappe-gantt
- Si campo `id` usa el nombre de la tarea → cambiar a usar t.id (UUID puro)
- Verificar que criticalTaskIds del endpoint /critical-path/ usa los mismos UUIDs

TAMBIÉN:
- En toggleFloat(), llamar endpoint individual /tasks/{id}/scheduling/float/ para
  tareas no críticas y poblar floatMap con sus valores

CRITERIO:
- Activar "Ruta Crítica" en proyecto con tareas con tildes/espacios no lanza errores
- Overlay de holgura muestra valores reales para todas las tareas
```

---

### Comando EPIC-1 — Tabs faltantes en proyecto (6–10h)

```
TAREA: Hacer funcionales los tabs Tareas, Kanban y Timesheets en detalle del proyecto

CONTEXTO: proyecto-detail.component.html ya tiene los tabs declarados. El problema es
que los componentes hijos posiblemente no reciben proyectoId como input() signal o
tienen condición de carrera en la carga de datos.

ARCHIVOS:
1. frontend/.../proyecto-detail/proyecto-detail.component.html
   - Verificar que tabs pasan [proyectoId]="p.id" a los componentes hijos

2. frontend/.../tarea-list/tarea-list.component.ts
   - Verificar input() proyectoId signal
   - Usar effect() para recargar cuando proyectoId cambia (no ngOnInit)

3. frontend/.../tarea-kanban/tarea-kanban.component.ts
   - Mismo patrón con effect()

CRITERIO:
- Tab "Tareas" muestra tareas del proyecto (>0 si tiene tareas)
- Tab "Kanban" muestra columnas filtradas por proyecto
- Tab "Timesheets" muestra horas del equipo del proyecto
```

---

### Comando EPIC-3 — Flujo de tareas UX (5–8h)

```
TAREA: Corregir condición de carrera en lista de tareas + mejoras UX

CONTEXTO: Lista global de tareas produce 0 resultados por condición de carrera en
ngOnInit(). Mis Tareas existe como ruta pero sin filtro automático.

ARCHIVOS:
1. frontend/.../tarea-list/tarea-list.component.ts
   - Reemplazar ngOnInit con effect() + takeUntilDestroyed
   - En modo misTareas, precargar filtro responsable=currentUser.id

2. frontend/.../tarea-kanban/tarea-kanban.component.html
   - Agregar fecha_limite visible en tarjetas

3. frontend/.../tarea-form/tarea-form.component.ts
   - Si query param proyecto presente, preseleccionar en formulario

4. frontend/.../fase-list/fase-list.component.html
   - Agregar botones "Activar" y "Completar" con guards de estado

CRITERIO:
- Lista de tareas muestra resultados al cargar
- /proyectos/mis-tareas muestra solo tareas del usuario activo
- Tarjetas Kanban muestran fecha límite
```

---

### Comando EPIC-4 — EVM funcional (6–10h)

```
TAREA: Hacer funcional el módulo EVM con UI de tarifas

BACKEND:
backend/apps/proyectos/budget_services.py
- Corregir get_cost_by_resource() y get_cost_by_task() para retornar [] cuando
  no hay timesheets (no lanzar excepción no capturada)

FRONTEND:
frontend/.../budget-dashboard/budget-dashboard.component.html
- Agregar sección "Tarifas por Recurso" con tabla de ResourceCostRate
  (método openCostRateForm() ya existe en el .ts)
- Agregar matTooltip en métricas EVM que muestran "—":
  "Se calcula cuando existen timesheets aprobados y tarifas de recurso configuradas"

CRITERIO:
- Sección "Tarifas por Recurso" visible con tabla y botón "Nueva tarifa"
- Al agregar tarifa + timesheets aprobados, AC/CPI/SPI muestran valores reales
- /costs/by-resource/ y /costs/by-task/ retornan 200 sin errores
```

---

### Comando EPIC-6 — Scheduling avanzado (10–16h, Sprint 3)

```
TAREA: Completar funcionalidades de scheduling incompletas

1. RESTRICCIONES (Quick win — 1h):
   frontend/.../tarea-detail/tarea-detail.component.html
   - Importar TaskConstraintsPanelComponent (ya implementado)
   - Agregar como sección/tab "Restricciones" con [tareaId]="tarea.id"

2. NIVELACIÓN EN AUTO-SCHEDULE (3h):
   frontend/.../auto-schedule-dialog/auto-schedule-dialog.component.html
   - Agregar checkbox "Nivelar recursos después de programar"
   - Si activo, llamar endpoint level-resources después del auto-schedule

3. WHAT-IF CON CAMBIOS (8h):
   frontend/.../what-if-scenario-builder/what-if-scenario-builder.component.ts
   - Agregar FormArray 'task_changes' con: task_id (autocomplete), field (select),
     new_value (input)
   - Mapear al payload { task_changes: { [task_id]: { [field]: new_value } } }

CRITERIO:
- Tab "Restricciones" visible en tarea-detail
- What-If permite definir cambios (duración, responsable, fecha_fin)
- Auto-Schedule tiene opción de nivelar recursos
```

---

## 6. ARCHIVOS CRÍTICOS PARA IMPLEMENTACIÓN

```
Backend Django:
├── backend/apps/proyectos/resource_services.py     # EPIC-5-B
├── backend/apps/proyectos/serializers.py           # EPIC-8
├── backend/apps/proyectos/budget_services.py       # EPIC-4
├── backend/apps/proyectos/views.py                 # EPIC-7
└── backend/apps/terceros/serializers.py            # EPIC-8

Frontend Angular:
├── frontend/src/app/features/proyectos/components/
│   ├── team-timeline/team-timeline.component.ts   # EPIC-5-A
│   ├── gantt-view/gantt-view.component.ts         # EPIC-2
│   ├── proyecto-detail/proyecto-detail.component.html  # EPIC-1
│   ├── tarea-list/tarea-list.component.ts         # EPIC-1, EPIC-3
│   ├── tarea-kanban/tarea-kanban.component.ts     # EPIC-1, EPIC-3
│   ├── budget-dashboard/budget-dashboard.component.html  # EPIC-4
│   ├── scheduling/what-if-scenario-builder/       # EPIC-6
│   ├── scheduling/auto-schedule-dialog/           # EPIC-6
│   └── tarea-detail/tarea-detail.component.html  # EPIC-6
└── frontend/src/app/features/proyectos/services/
    └── hito.service.ts                            # EPIC-7
```

---

*Generado: 28 Marzo 2026 | Basado en auditoría técnica + validación funcional gestor de proyectos*
*Siguiente actualización: Al completar Sprint 1 (4 Abr 2026)*
