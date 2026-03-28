# FEATURE-6-UI-WIREFRAMES.md
# Advanced Scheduling — Wireframes UI/UX

**Fecha:** 27 Marzo 2026
**Framework:** Angular Material (DEC-011) — NUNCA PrimeNG
**Referencia canónica:** `docs/standards/UI-UX-STANDARDS.md`

---

## Convenciones generales

- `mat-dialog`: todos los flujos de acción (auto-schedule, crear baseline, crear escenario)
- `mat-table`: listados (baselines, escenarios, constraints)
- `mat-progress-bar`: estado de simulación en ejecución
- `MatSnackBar`: feedback post-acción (`snack-success` / `snack-error`)
- `@if` / `@for`: sintaxis Angular 18 (nunca `*ngIf` / `*ngFor`)
- Variables CSS `var(--sc-*)`: nunca colores hardcodeados

---

## 1. AutoScheduleDialogComponent

**Trigger:** Botón "Auto-Schedule" en toolbar de ProyectoDetail
**Ruta:** `proyecto-detail > toolbar > [Auto-Schedule btn] > MatDialog`

```
┌────────────────────────────────────────────────┐
│  Auto-Schedule — [Nombre del Proyecto]         │
│  ─────────────────────────────────────────── × │
│                                                │
│  Modo de programación                          │
│  ┌─────────────────────────────────────────┐  │
│  │ ( ) ASAP — Iniciar lo antes posible     │  │
│  │ (•) ALAP — Iniciar lo más tarde posible │  │
│  └─────────────────────────────────────────┘  │
│                                                │
│  Opciones                                      │
│  [✓] Respetar restricciones de tareas          │
│  [✓] Considerar disponibilidad de recursos     │
│  [ ] Solo simular (no guardar cambios)          │
│                                                │
│  ── Vista previa ──────────────────────────── │
│  (aparece después de [Calcular])               │
│  ┌─────────────────────────────────────────┐  │
│  │ mat-progress-bar (mientras calcula)     │  │
│  │                                         │  │
│  │ ✓ 12 tareas serán reprogramadas         │  │
│  │ ✓ Fin del proyecto: 15 Mar → 20 Mar     │  │
│  │ ⚠ 3 tareas excluidas (sin fechas)       │  │
│  │ ─ Ruta crítica: 8 tareas                │  │
│  └─────────────────────────────────────────┘  │
│                                                │
│        [Cancelar]  [Calcular]  [Aplicar]      │
│                    (disabled hasta preview)    │
└────────────────────────────────────────────────┘
```

**Flujo:**
1. Usuario configura opciones → clic "Calcular"
2. POST `/auto-schedule/?dry_run=true` → spinner
3. Preview muestra resultado → "Aplicar" se habilita
4. Clic "Aplicar" → POST `/auto-schedule/` sin dry_run
5. MatSnackBar `snack-success` → cerrar dialog → recargar Gantt

**Estados de "Aplicar":**
- `disabled` hasta que preview se ejecute
- `disabled` si dry_run=true forzado (solo consulta)

---

## 2. TaskConstraintsPanelComponent

**Ubicación:** Tab o panel lateral en `tarea-detail`
**Activación:** Nueva tab "Restricciones" en TareaDetail

```
──────────────────────────────────────────────
 Restricciones de Scheduling
──────────────────────────────────────────────
 Agregar restricción

 Tipo  [Must Finish On            ▼]
 Fecha [────────────── 📅]          (si aplica)

 [+ Agregar]

──────────────────────────────────────────────
 Restricciones activas

 ┌────────────────────────────────────────┐
 │ Start No Earlier Than                  │
 │ 01 Mar 2026               [🗑 Eliminar]│
 └────────────────────────────────────────┘
 ┌────────────────────────────────────────┐
 │ ASAP                                   │
 │ (sin fecha)               [🗑 Eliminar]│
 └────────────────────────────────────────┘

 ── Estado vacío ─────────────────────────
 (sc-empty-state si no hay restricciones)
 [icono calendario]
 Sin restricciones de scheduling
 Esta tarea se reprogramará automáticamente
──────────────────────────────────────────────
```

**Tipos con fecha:** `must_start_on`, `must_finish_on`, `start_no_earlier_than`, `start_no_later_than`, `finish_no_earlier_than`, `finish_no_later_than`
**Tipos sin fecha:** `asap`, `alap`
**Validación:** `mat-error` inline si tipo requiere fecha y está vacía.

---

## 3. BaselineComparisonComponent

**Ruta:** Tab "Baselines" en ProyectoDetail
**Componente:** Standalone con su propia lógica

```
──────────────────────────────────────────────────
 Baselines del Proyecto
──────────────────────────────────────────────────
 [+ Crear Baseline]

 Comparar:
 Plan actual  vs  [Original Plan (15 Mar)   ▼]
                  [Calcular comparación]

──────────────────────────────────────────────────
 Resumen de variación (post-cálculo)

 ┌──────────┬───────────┬─────────────────────┐
 │          │  Baseline │  Actual             │
 ├──────────┼───────────┼─────────────────────┤
 │ Fin proy │  15 Mar   │  25 Mar  (+10 días) │
 │ Adelant. │     5     │  🟢                 │
 │ En plazo │    20     │  🟡                 │
 │ Retrasad │     8     │  🔴                 │
 └──────────┴───────────┴─────────────────────┘

──────────────────────────────────────────────────
 Detalle por tarea  (mat-table, paginación 10)

 [Buscar tarea...]

 Tarea       Baseline Ini  Actual Ini  Variación
 ──────────  ────────────  ──────────  ─────────
 Backend API  01 Mar        01 Mar      0 días 🟡
 QA Testing   10 Mar        15 Mar     +5 días 🔴
 Deploy       15 Mar        12 Mar     -3 días 🟢

 [< 1 2 3 >]
──────────────────────────────────────────────────
```

**mat-chip-set:** Indicadores de estado con colores `var(--sc-success)`, `var(--sc-warning)`, `var(--sc-danger)`

---

## 4. WhatIfScenarioBuilderComponent

**Ruta:** Tab "Escenarios" en ProyectoDetail
**Layout:** Split-panel (mat-sidenav o dos columnas)

```
──────────────────────────────────────────────────────────
 Escenarios What-If
──────────────────────────────────────────────────────────
 [+ Nuevo Escenario]

 Lista de escenarios (mat-table)
 Nombre                Estado          Resultado   Acciones
 ──────────────────────────────────────────────────────────
 +2 desarrolladores    Simulado 🟢     -7 días     [Ver][🗑]
 Reducir alcance 20%   Pendiente ⏳    —           [Simular][🗑]
 Retraso proveedor     Simulado 🟢     +15 días    [Ver][🗑]

──────────────────────────────────────────────────────────
 Detalle de Escenario (al seleccionar)

 Nombre: +2 desarrolladores
 Descripción: Agregar dos devs en fase backend

 Cambios configurados:
 ─ Tareas: (ninguna)
 ─ Recursos:
   • [Dev #1] 50% en Backend API (01–20 Mar)
   • [Dev #2] 50% en Backend API (01–20 Mar)
 ─ Dependencias: (ninguna)

 Resultado de simulación:
 ┌─────────────────────────────────────┐
 │ Fin actual:      25 Mar 2026        │
 │ Fin simulado:    18 Mar 2026        │
 │ Diferencia:      -7 días  🟢        │
 │ Tareas afectadas: 12                │
 └─────────────────────────────────────┘

                               [Correr Simulación]
──────────────────────────────────────────────────────────
```

**Formulario "Nuevo Escenario":** MatDialog con stepper (nombre/desc → cambios → confirmar).

---

## 5. FloatIndicatorComponent

**Uso:** Badge/chip reutilizable en tarea-detail, tarea-kanban, tabla de tareas.

```
Usos inline:
┌──────────────────────────────────────┐
│ Backend API                          │
│ 📅 01–15 Mar   [Float: 3d] [CRÍTICA] │
└──────────────────────────────────────┘

FloatIndicatorComponent:
- float > 0: mat-chip color='primary'   → "Float: Xd"
- float == 0: mat-chip color='warn'     → "CRÍTICA"
- sin calcular: nada (ng-container vacío)
```

**Input:** `@Input() floatDays: number | null`
**Selector:** `<sc-float-indicator [floatDays]="task.float_days" />`

---

## 6. Mejoras al Gantt existente

**Archivo:** `tarea-gantt` / `gantt` component existente.
**Integración:** Overlay visual sobre barras Frappe Gantt.

```
Gantt mejorado:

 Task Name       Mar 1   Mar 8   Mar 15  Mar 22  Mar 30
 ──────────────────────────────────────────────────────
 Backend API     ████████████████  (actual, azul)
                 ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  (baseline, gris, debajo)
                                  ░░░  (float, punteado)

 QA Testing                ████████████  (actual, azul)
                     ████████  (baseline, gris)    ← adelantó

 Deploy [🔴CRÍTICA]              ████████████████ (rojo - ruta crítica)

 Leyenda:  [══] Actual  [▓▓] Baseline  [░░] Float disponible  [🔴] Ruta crítica
```

**Implementación Angular:**
- Añadir capa SVG/div overlay sobre el Gantt de Frappe
- `SchedulingService.getCriticalPath()` → colorear barras en rojo
- `BaselineService.getActiveBaseline()` → renderizar barras grises
- Botones toggle en toolbar del Gantt:
  ```
  [🔴 Ruta crítica] [📏 Baseline] [📐 Float]
  ```
- Cada botón es `mat-icon-button` con `mat-tooltip`

---

## 7. Integración en ProyectoDetail — nuevas tabs

```
ProyectoDetail tab bar (actual + nuevas):

[Resumen] [Fases] [Tareas] [Gantt] [Recursos] [Analytics] | [Scheduling▼] [Baselines] [Escenarios]

Scheduling (dropdown mat-menu):
  ├ Auto-Schedule → abre AutoScheduleDialogComponent
  ├ Nivelar Recursos → abre confirmación + ejecuta
  └ Ruta Crítica → navega a vista Gantt con CPM activo
```

---

## 8. Integración en TareaDetail — nueva tab

```
TareaDetail tab bar:

[Descripción] [Timesheet] [Comentarios] | [Restricciones] [Float]

Tab "Restricciones" → TaskConstraintsPanelComponent
Tab "Float"         → FloatIndicatorComponent + cálculo bajo demanda
```

---

*Generado: 27 Marzo 2026 — Phase 0 Feature #6*
