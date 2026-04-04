# FEATURE-7-EXECUTION-PLAN.md
# Budget & Cost Tracking — Plan de Ejecución

**Fecha:** 27 Marzo 2026
**Feature:** #7 — Budget & Cost Tracking
**Stack:** Django 5 + Angular 18 + Angular Material (DEC-011)
**Milestone:** 100% Odoo parity (7/7 features complete)
**Desarrollador:** 1 senior developer (Juan David)

---

## Resumen ejecutivo

Feature #7 introduce seguimiento presupuestario completo a nivel de proyecto y tarea, con cálculo
de Valor Ganado (EVM), snapshots semanales automáticos via Celery, y 6 componentes Angular
integrados en la tab "Budget" de ProyectoDetail. Duración estimada: 2.5 semanas.

---

## Sprint Plan — Visión Global

| Semana | Foco principal | Entregable clave |
|--------|---------------|------------------|
| Semana 1 (dias 1–5) | Backend: modelos, servicios, endpoints | APIs estables, tests >= 85% |
| Semana 2 (dias 6–10) | Frontend: interfaces, servicios, componentes | 6 componentes integrados |
| Semana 2-3 (dias 11–14) | Celery task, testing, validacion, docs | Feature 100% completa |

---

## Semana 1 — Backend Completo

### Dia 1 — Modelos + Migración

**Objetivo:** Base de datos lista, sin deuda de modelos.

**Orden de ejecución:**

```
BG-01  ProjectBudget
       - Campos: project (FK), budget_type (LABOR/MATERIAL/EQUIPMENT/OTHER/TOTAL),
         planned_amount NUMERIC(15,2), currency (default COP), notes, is_approved,
         approved_by (FK User nullable), approved_at
       - Hereda BaseModel (UUID, company, timestamps)
       - unique_together: (project, budget_type)

BG-02  CostEntry
       - Campos: project (FK), task (FK nullable), entry_date DATE,
         cost_type (choices: LABOR/MATERIAL/EQUIPMENT/OTHER),
         description, planned_cost NUMERIC(15,2), actual_cost NUMERIC(15,2),
         quantity NUMERIC(10,3) nullable, unit_price NUMERIC(15,2) nullable,
         reference_document varchar(100) nullable, recorded_by (FK User)
       - Hereda BaseModel

BG-03  BudgetSnapshot
       - Campos: project (FK), snapshot_date DATE,
         planned_value NUMERIC(15,2), earned_value NUMERIC(15,2),
         actual_cost NUMERIC(15,2), budget_at_completion NUMERIC(15,2),
         snapshot_type (choices: MANUAL/WEEKLY_AUTO),
         notes
       - Hereda BaseModel
       - unique_together: (project, snapshot_date, snapshot_type)

BG-04  BudgetAlert
       - Campos: project (FK), alert_type (THRESHOLD_50/THRESHOLD_80/THRESHOLD_100/
         OVERRUN/SCHEDULE_VARIANCE), triggered_at, threshold_pct NUMERIC(5,2),
         current_pct NUMERIC(5,2), is_acknowledged, acknowledged_by nullable,
         acknowledged_at nullable
       - Hereda BaseModel

BG-05  Migración
       → python manage.py makemigrations --name feature_7_budget_models
       → python manage.py migrate
       → python manage.py check
```

**Criterio de salida del dia:** `migrate` exitoso, `check` sin errores, 4 modelos visibles en Django Admin básico.

---

### Dia 2 — Serializers + BudgetService (CRUD + cálculos base)

**Objetivo:** Capa de datos y lógica CRUD lista para usar desde views.

```
BG-06  budget_serializers.py
       - ProjectBudgetListSerializer (pk, budget_type, planned_amount, currency, is_approved)
       - ProjectBudgetDetailSerializer (todos los campos + computed: spent_pct, remaining)
       - ProjectBudgetCreateSerializer (validación: planned_amount > 0)
       - CostEntryListSerializer (pk, entry_date, cost_type, description, actual_cost)
       - CostEntryDetailSerializer (todos los campos)
       - CostEntryCreateSerializer (validación: planned_cost y actual_cost >= 0)
       - BudgetSnapshotSerializer (todos los campos, read-only)
       - BudgetAlertSerializer (todos los campos)
       - BudgetSummarySerializer (planned_total, actual_total, remaining, spent_pct,
                                   cost_variance, schedule_variance, CPI, SPI)

BG-07  budget_services.py — CRUD y agregados
       - get_project_budgets(project_id, company_id) → queryset con select_related
       - create_budget(project_id, company_id, data, user) → ProjectBudget
       - update_budget(budget_id, company_id, data) → ProjectBudget
       - approve_budget(budget_id, company_id, user) → ProjectBudget
       - delete_budget(budget_id, company_id) → None
       - get_cost_entries(project_id, company_id, filters) → queryset
       - create_cost_entry(project_id, company_id, data, user) → CostEntry
       - update_cost_entry(entry_id, company_id, data) → CostEntry
       - delete_cost_entry(entry_id, company_id) → None
```

**Criterio de salida del dia:** Services CRUD importan sin errores, serializers validan datos de prueba.

---

### Dia 3 — EVM Service (nucleo crítico)

**Objetivo:** Cálculos de Valor Ganado correctos y testeados.

```
BG-08  budget_services.py — EVM core
       - calculate_planned_value(project_id, company_id, as_of_date=None) → Decimal
         Lógica: suma planned_amount de tareas completadas segun cronograma
                 hasta as_of_date. Usa Task.fecha_inicio + duracion estimada.
         Fuente de datos: ProjectBudget.planned_amount agregado por tarea % progreso.

       - calculate_earned_value(project_id, company_id, as_of_date=None) → Decimal
         Lógica: BAC * % completado global del proyecto
         % completado = promedio ponderado de Task.progress (ya existe en modelo)

       - calculate_actual_cost(project_id, company_id, as_of_date=None) → Decimal
         Lógica: SUM(CostEntry.actual_cost) filtrado por entry_date <= as_of_date

       - calculate_evm_metrics(project_id, company_id, as_of_date=None) → dict
         Retorna: {
           "planned_value": PV,
           "earned_value": EV,
           "actual_cost": AC,
           "budget_at_completion": BAC,
           "cost_variance": CV = EV - AC,
           "schedule_variance": SV = EV - PV,
           "cost_performance_index": CPI = EV / AC (0.0 si AC == 0),
           "schedule_performance_index": SPI = EV / PV (0.0 si PV == 0),
           "estimate_at_completion": EAC = BAC / CPI (BAC si CPI == 0),
           "estimate_to_complete": ETC = EAC - AC,
           "variance_at_completion": VAC = BAC - EAC,
           "percent_complete": float
         }

BG-09  budget_services.py — Alertas
       - check_and_create_alerts(project_id, company_id) → list[BudgetAlert]
         Lógica: calcular spent_pct = AC/BAC*100; crear alertas para umbrales
                 50%, 80%, 100% si no existen ya. Retornar alertas nuevas creadas.
       - acknowledge_alert(alert_id, company_id, user) → BudgetAlert

BG-10  budget_services.py — Snapshots
       - create_snapshot(project_id, company_id, snapshot_type, notes=None) → BudgetSnapshot
         Lógica: calcula EVM en este momento y persiste como snapshot
       - get_snapshot_history(project_id, company_id, limit=52) → queryset ordenado por fecha
```

**Criterio de salida del dia:** Tests unitarios de EVM pasando con datos ficticios (no requiere BD completa).

---

### Dia 4 — Views + URLs (20+ endpoints)

**Objetivo:** Todos los endpoints REST operativos, verificados con curl/Postman.

```
BG-11  budget_views.py
       Estructura de views (solo orquestan, llaman service):

       ProjectBudgetListCreateView  GET/POST  /api/v1/projects/{pk}/budgets/
       ProjectBudgetDetailView      GET/PATCH/DELETE  /api/v1/projects/{pk}/budgets/{budget_pk}/
       ApproveBudgetView            POST  /api/v1/projects/{pk}/budgets/{budget_pk}/approve/
       BudgetSummaryView            GET   /api/v1/projects/{pk}/budgets/summary/
       EVMMetricsView               GET   /api/v1/projects/{pk}/budgets/evm/?date=YYYY-MM-DD
       CostEntryListCreateView      GET/POST  /api/v1/projects/{pk}/cost-entries/
       CostEntryDetailView          GET/PATCH/DELETE  /api/v1/projects/{pk}/cost-entries/{entry_pk}/
       TaskCostEntriesView          GET   /api/v1/projects/tasks/{task_pk}/cost-entries/
       BudgetSnapshotListView       GET   /api/v1/projects/{pk}/budget-snapshots/
       CreateSnapshotView           POST  /api/v1/projects/{pk}/budget-snapshots/create/
       BudgetAlertListView          GET   /api/v1/projects/{pk}/budget-alerts/
       AcknowledgeAlertView         POST  /api/v1/projects/{pk}/budget-alerts/{alert_pk}/acknowledge/

BG-12  urls.py
       - Agregar 20+ rutas bajo comentario "# Budget — Feature #7"
       - Verificar con: python manage.py show_urls | grep budget

BG-13  Verificación manual
       - curl GET /api/v1/projects/{id}/budgets/summary/ → 200 JSON
       - curl POST /api/v1/projects/{id}/cost-entries/ con payload → 201 JSON
       - curl GET /api/v1/projects/{id}/budgets/evm/ → JSON con 10 campos EVM
       - python manage.py check → 0 issues
```

**Criterio de salida del dia:** 20+ endpoints responden correctamente. `python manage.py check` limpio.

---

### Dia 5 — Celery Task + Tests Backend >= 85%

**Objetivo:** Task semanal automatizada + cobertura de tests suficiente para PR.

```
BG-14  tasks.py (Celery)
       - weekly_budget_snapshot_task()
         Decorador: @shared_task(name='budget.weekly_snapshot')
         Schedule: cada lunes 06:00 UTC (en celery beat config)
         Lógica:
           1. Para cada Project activo (status != completed, cancelled)
           2. Llamar create_snapshot(project_id, company_id, 'WEEKLY_AUTO')
           3. Llamar check_and_create_alerts(project_id, company_id)
           4. logger.info con project_id y métricas EVM
           5. Manejar excepciones por proyecto sin detener loop completo

BG-15  Tests — test_budget_models.py
       - TestProjectBudget: crear, unique_together, campos requeridos
       - TestCostEntry: crear con y sin task, validaciones
       - TestBudgetSnapshot: crear, tipos
       - TestBudgetAlert: crear, acknowledge

BG-16  Tests — test_budget_services.py (PRIORITARIO — 85% min)
       - TestBudgetCRUD: crear/editar/eliminar budget y cost entries
       - TestEVMCalculations:
         * test_evm_zero_progress → EV=0, CV=EV-AC negativo
         * test_evm_full_progress → EV=BAC, CV cerca de 0
         * test_evm_partial_progress → CPI > 1 cuando AC < EV
         * test_evm_cpi_zero_actual_cost → no división por cero
         * test_spi_zero_planned_value → no división por cero
       - TestAlerts: umbral 50/80/100, no duplicar alertas existentes
       - TestSnapshots: create_snapshot persiste valores correctos
       - TestWeeklyTask: mock de projects activos, llamadas a services

BG-17  Tests — test_budget_views.py
       - CRUD endpoints con autenticación JWT
       - Autorización: company_id correcto
       - EVM metrics endpoint con y sin parámetro date
       - Snapshot create endpoint

       → pytest apps/proyectos/tests/test_budget* --cov=apps/proyectos/budget_services \
           --cov-report=term-missing
       → Verificar >= 85% en budget_services.py
```

**Criterio de salida del dia:** `pytest --cov >= 85%` en budget_services.py. Celery task sin errores de import.

---

## Semana 2 — Frontend Completo

### Dia 6 — Interfaces TypeScript + Servicios Angular

**Objetivo:** Tipos y servicios listos, cero `any` en toda la feature.

```
FE-01  models/budget.model.ts
       export interface ProjectBudget {
         id: string;
         budget_type: BudgetType;
         planned_amount: string;   // NUMERIC como string de Django
         currency: string;
         is_approved: boolean;
         approved_by?: string;
         approved_at?: string;
         notes?: string;
         created_at: string;
       }
       export type BudgetType = 'LABOR' | 'MATERIAL' | 'EQUIPMENT' | 'OTHER' | 'TOTAL';

       export interface CostEntry {
         id: string;
         project: string;
         task?: string;
         entry_date: string;
         cost_type: CostType;
         description: string;
         planned_cost: string;
         actual_cost: string;
         quantity?: string;
         unit_price?: string;
         reference_document?: string;
         recorded_by: string;
         created_at: string;
       }
       export type CostType = 'LABOR' | 'MATERIAL' | 'EQUIPMENT' | 'OTHER';

       export interface BudgetSummary {
         planned_total: string;
         actual_total: string;
         remaining: string;
         spent_pct: number;
       }

       export interface EVMMetrics {
         planned_value: string;
         earned_value: string;
         actual_cost: string;
         budget_at_completion: string;
         cost_variance: string;
         schedule_variance: string;
         cost_performance_index: number;
         schedule_performance_index: number;
         estimate_at_completion: string;
         estimate_to_complete: string;
         variance_at_completion: string;
         percent_complete: number;
       }

       export interface BudgetSnapshot {
         id: string;
         snapshot_date: string;
         planned_value: string;
         earned_value: string;
         actual_cost: string;
         budget_at_completion: string;
         snapshot_type: 'MANUAL' | 'WEEKLY_AUTO';
         notes?: string;
       }

       export interface BudgetAlert {
         id: string;
         alert_type: AlertType;
         triggered_at: string;
         threshold_pct: number;
         current_pct: number;
         is_acknowledged: boolean;
       }
       export type AlertType =
         'THRESHOLD_50' | 'THRESHOLD_80' | 'THRESHOLD_100' | 'OVERRUN' | 'SCHEDULE_VARIANCE';

FE-02  services/budget.service.ts
       - getBudgets(projectId: string): Observable<ProjectBudget[]>
       - createBudget(projectId: string, data: Partial<ProjectBudget>): Observable<ProjectBudget>
       - updateBudget(projectId: string, budgetId: string, data: Partial<ProjectBudget>): Observable<ProjectBudget>
       - approveBudget(projectId: string, budgetId: string): Observable<ProjectBudget>
       - deleteBudget(projectId: string, budgetId: string): Observable<void>
       - getBudgetSummary(projectId: string): Observable<BudgetSummary>
       - getEVMMetrics(projectId: string, date?: string): Observable<EVMMetrics>
       - getCostEntries(projectId: string, filters?: Record<string, string>): Observable<CostEntry[]>
       - createCostEntry(projectId: string, data: Partial<CostEntry>): Observable<CostEntry>
       - updateCostEntry(projectId: string, entryId: string, data: Partial<CostEntry>): Observable<CostEntry>
       - deleteCostEntry(projectId: string, entryId: string): Observable<void>
       - getSnapshots(projectId: string): Observable<BudgetSnapshot[]>
       - createSnapshot(projectId: string, notes?: string): Observable<BudgetSnapshot>
       - getAlerts(projectId: string): Observable<BudgetAlert[]>
       - acknowledgeAlert(projectId: string, alertId: string): Observable<BudgetAlert>

       → npx tsc --noEmit → 0 errores
       → ng build --configuration=production → 0 errores nuevos
```

**Criterio de salida del dia:** Build production limpio con interfaces y servicio.

---

### Dia 7 — Componentes: BudgetSummaryCard + BudgetAlertsPanel

**Objetivo:** Los dos componentes de solo lectura más simples, que se usan como base visual.

```
FE-03  components/budget/budget-summary-card/budget-summary-card.component.ts
       - Input: summary: BudgetSummary
       - Input: evmMetrics: EVMMetrics
       - OnPush, inject()
       - Muestra: planned vs actual en mat-card
         * Barra de progreso mat-progress-bar con color según spent_pct:
           < 80% → primary, 80-100% → warn, > 100% → danger
         * KPIs EVM en grid: CPI, SPI, CV, SV con color condicional
         * EAC con formato de moneda COP

FE-04  components/budget/budget-alerts-panel/budget-alerts-panel.component.ts
       - Input: alerts: BudgetAlert[]
       - Output: alertAcknowledged: EventEmitter<string> (alert_id)
       - OnPush
       - mat-list con mat-icon por tipo de alerta:
         THRESHOLD_50 → 'warning' amarillo
         THRESHOLD_80 → 'warning' naranja
         THRESHOLD_100 → 'error' rojo
         OVERRUN → 'trending_up' rojo
       - Botón "Reconocer" solo si !is_acknowledged
       - Alertas reconocidas se muestran con opacidad 50%
```

**Criterio de salida del dia:** Ambos componentes renderizan en dev sin errores. Mock data suficiente.

---

### Dia 8 — Componentes: CostEntryFormDialog + CostEntryTableComponent

**Objetivo:** CRUD de entradas de costo funcional end-to-end.

```
FE-05  components/budget/cost-entry-form-dialog/cost-entry-form-dialog.component.ts
       - MAT_DIALOG_DATA: { projectId: string, entry?: CostEntry }
       - ReactiveForm con FormBuilder.nonNullable:
         * entry_date: [today, Validators.required]
         * cost_type: ['LABOR', Validators.required]
         * description: ['', [Validators.required, Validators.maxLength(200)]]
         * planned_cost: [0, [Validators.required, Validators.min(0)]]
         * actual_cost: [0, [Validators.required, Validators.min(0)]]
         * task: [null] (mat-select opcional, carga tareas del proyecto)
         * reference_document: ['']
       - Modo crear / editar detectado por presencia de entry en data
       - Submit llama budget.service + MatDialogRef.close(result)
       - Errores inline con @if dentro de mat-form-field
       - Nunca alert(), nunca confirm()

FE-06  components/budget/cost-entry-table/cost-entry-table.component.ts
       - Input: projectId: string
       - OnPush con signals
       - mat-table con columnas: Fecha | Tipo | Descripción | Planeado | Real | Tarea | Acciones
       - mat-progress-bar encima de la tabla (nunca spinner centrado)
       - Fila vacía: sc-empty-state con icono 'receipt_long' + "Sin registros de costo"
         + botón "Agregar costo" (FUERA del mat-table, sigue estandar UI/UX)
       - Acciones: Editar | Eliminar (mat-icon-button con tooltip)
       - Eliminar: MatDialog con ConfirmDialogComponent
       - Paginación client-side (mat-paginator, pageSize: 10)
       - Filtro por cost_type con mat-select
```

**Criterio de salida del dia:** CRUD de cost entries funciona en dev con API real. Confirmación de eliminacion via dialog.

---

### Dia 9 — Componentes: BudgetPlanningTable + EVMChartComponent

**Objetivo:** Planificación de presupuesto y visualización de tendencia EVM.

```
FE-07  components/budget/budget-planning-table/budget-planning-table.component.ts
       - Input: projectId: string
       - OnPush con signals
       - mat-table inline-editable: columnas Tipo | Planeado | Moneda | Aprobado | Acciones
       - Fila de totales al final (no en mat-table, fuera como mat-footer-row nativo)
       - Botón "Aprobar" solo si !is_approved y usuario tiene rol company_admin
       - Agregar nueva línea con botón + debajo de la tabla
       - Edición inline con mat-form-field flotante solo en la fila activa
       - Feedback: MatSnackBar snack-success / snack-error
       - Estado vacío: sc-empty-state "Sin presupuesto planificado" + botón "Planificar"

FE-08  components/budget/evm-chart/evm-chart.component.ts
       - Input: snapshots: BudgetSnapshot[]
       - Input: currentMetrics: EVMMetrics
       - OnPush
       - Gráfico de líneas Chart.js con 3 series:
         * Planned Value (PV) — azul punteado
         * Earned Value (EV) — verde sólido
         * Actual Cost (AC) — rojo sólido
       - Eje X: fechas de snapshots + punto "Hoy" usando currentMetrics
       - Eje Y: moneda formateada (COP)
       - Leyenda con CPI y SPI actuales como chips de color debajo del gráfico
       - NOTA: Reutilizar patrón de Chart.js de Feature #5 (project-analytics-dashboard)
       - ngOnDestroy: chart.destroy() para evitar memory leak
```

**Criterio de salida del dia:** Ambos componentes integran con API real. EVM chart muestra datos de snapshots.

---

### Dia 10 — Integración en ProyectoDetail + Tab "Budget"

**Objetivo:** Feature visible end-to-end desde la UI del proyecto.

```
FE-09  proyecto-detail.component — Tab Budget
       - Agregar tab "Budget" en mat-tab-group de proyecto-detail
       - Usar @defer on viewport para carga lazy de los 5 componentes
       - Layout de la tab:
         * Fila superior: BudgetSummaryCard (ancho completo)
         * Fila alertas: BudgetAlertsPanel (si hay alertas sin reconocer)
         * mat-tab-group secundario dentro del tab Budget:
           - "Presupuesto" → BudgetPlanningTable
           - "Costos" → CostEntryTable
           - "Tendencia EVM" → EVMChart + snapshot history
       - Botón "Crear snapshot manual" en toolbar del tab Budget
       - Estado de carga: mat-progress-bar en header del tab mientras carga

FE-10  Verificación TypeScript + build
       → npx tsc --noEmit → 0 errores strict
       → ng build --configuration=production → 0 errores nuevos
       → Verificar: CPI y SPI se muestran con 2 decimales
       → Verificar: montos en COP con formato colombiano correcto
       → Verificar: alertas de presupuesto aparecen cuando spent_pct > 80%
```

**Criterio de salida del dia:** Feature #7 end-to-end funcional en dev. Todos los componentes renderizan con datos reales.

---

## Semana 2-3 — Testing, Validación y Documentación

### Dia 11 — Testing E2E + Reality Check

**Objetivo:** Validación completa del flujo funcional.

```
QA-01  Flujo completo como company_admin:
       1. Crear proyecto de prueba con 5 tareas
       2. Planificar presupuesto: LABOR=10M, MATERIAL=5M COP
       3. Aprobar presupuesto
       4. Agregar 3 cost entries (LABOR, MATERIAL, LABOR)
       5. Verificar BudgetSummaryCard muestra porcentaje correcto
       6. Crear snapshot manual
       7. Marcar 2 tareas como completadas
       8. Recargar EVM — verificar EV aumenta, SPI/CPI se recalculan
       9. Agregar cost entry que lleve AC > 80% de BAC
       10. Verificar alerta THRESHOLD_80 aparece
       11. Reconocer alerta — verificar desaparece del panel activo

QA-02  Flujo como seller (rol sin permiso de aprobar):
       - Puede ver summary y costos
       - No puede aprobar presupuesto (botón oculto o deshabilitado)
       - No puede eliminar cost entries de otros usuarios

QA-03  Casos edge EVM:
       - Proyecto sin cost entries → EVM sin división por cero
       - Proyecto sin progreso (0%) → EV = 0, SPI = 0
       - Proyecto 100% completado → EV = BAC, idealmente

QA-04  Celery task manual:
       → python manage.py shell -c "from apps.proyectos.tasks import weekly_budget_snapshot_task; weekly_budget_snapshot_task()"
       → Verificar snapshots creados para todos los proyectos activos
       → Verificar logs estructurados en output

QA-05  Recolección de evidencias (capturas de pantalla):
       - BudgetSummaryCard con CPI > 1 (proyecto saludable)
       - BudgetSummaryCard con CPI < 1 (proyecto en riesgo)
       - EVMChart con 3 líneas visibles
       - BudgetAlertsPanel con alerta activa
       - CostEntryTable con datos reales
       - BudgetPlanningTable con fila aprobada
```

---

### Dia 12 — Auditoría de Seguridad + Correcciones

**Objetivo:** Ninguna vulnerabilidad evidente antes del PR.

```
SEC-01  Verificar filtros de company_id en TODOS los queryset de budget_services.py
        → Ningún endpoint retorna datos de otra empresa

SEC-02  Verificar que CostEntry.recorded_by no puede ser sobreescrito por el cliente
        → El campo debe ser set en el service desde request.user, no desde payload

SEC-03  Verificar que approve_budget valida permiso de rol
        → Solo company_admin puede aprobar

SEC-04  Verificar que Celery task no expone datos sensibles en logs
        → Solo project_id y métricas agregadas en logger.info

SEC-05  Verificar NUMERIC(15,2) en todos los campos de dinero
        → Nunca float en serializers ni en respuestas JSON
        → Usar str() para retornar Decimal desde Python (evitar pérdida de precisión)

SEC-06  Verificar que BudgetAlert no se crea duplicada
        → unique_together o check en service antes de crear
```

---

### Dia 13 — Documentación Técnica

**Objetivo:** Todos los endpoints documentados para integraciones futuras.

```
DOC-01  docs/FEATURE-7-API-DOCS.md
        - 20+ endpoints con método, URL, autenticación, request body y response body
        - Ejemplos JSON reales (no ficticios)
        - Sección especial: EVM — explicación de cada métrica con fórmula
        - Sección especial: Celery task — cómo configurar el schedule en producción

DOC-02  docs/FEATURE-7-USER-GUIDE.md (en español)
        - Cómo planificar un presupuesto paso a paso
        - Cómo registrar costos reales
        - Cómo interpretar las métricas EVM (CPI, SPI, EAC en lenguaje no técnico)
        - Cómo gestionar alertas de presupuesto
        - Qué hace el snapshot semanal automático

DOC-03  Actualizar CONTEXT.md
        - Marcar Feature #7 como completa
        - Listar todos los endpoints creados
        - Estado de la deuda técnica

DOC-04  Actualizar DECISIONS.md
        - DEC-028: Estrategia de cálculo de EVM (qué datos usa cada métrica)
        - DEC-029: Celery beat vs cron para snapshots semanales
        - DEC-030: Moneda (COP por defecto, preparado para multi-moneda futura)
```

---

### Dia 14 — Cierre, PR y Revisión Final

**Objetivo:** Feature #7 lista para merge. Milestone 7/7 cerrado.

```
CL-01  Revisión final de cobertura
       → pytest apps/proyectos/tests/test_budget* --cov=apps/proyectos/budget_services
       → Confirmar >= 85%

CL-02  Build final
       → ng build --configuration=production
       → 0 errores nuevos (warnings CSS pre-existentes de Feature #6 son aceptables)
       → npx tsc --noEmit

CL-03  Limpiar código
       → Eliminar console.log y print() olvidados
       → Verificar que ningún TODO quede sin resolver en archivos nuevos

CL-04  Commit y PR
       → git add [archivos específicos de Feature #7]
       → Commit: "feat(budget): add budget & cost tracking with EVM metrics"
       → PR con descripción: endpoints, componentes, Celery task, cobertura

CL-05  Milestone check
       → Features completadas: 1 Proyectos, 2 Tareas, 3 Gantt, 4 Recursos,
         5 Analytics, 6 Scheduling, 7 Budget = 7/7 ✓
       → Odoo parity: 100% ✓
```

---

## Ruta Crítica

Los siguientes bloques son secuenciales y no pueden paralelizarse. Un retraso en cualquiera
bloquea el siguiente.

```
[BG-01 Modelos]
      ↓
[BG-05 Migración]
      ↓
[BG-06 Serializers] + [BG-07 CRUD Services]
      ↓
[BG-08 EVM Service]  ← CRITICO: base de toda la lógica de valor
      ↓
[BG-11 Views + URLs]
      ↓
[FE-01 Interfaces TS]
      ↓
[FE-02 budget.service.ts]
      ↓
[FE-03 a FE-08 Componentes]  ← Pueden paralelizarse entre sí
      ↓
[FE-09 Integración ProyectoDetail]
      ↓
[QA-01 a QA-05 Testing E2E]
```

**Bloqueo más probable:** BG-08 (EVM). Los cálculos de EV y PV dependen de que Task tenga
datos de progreso y fechas correctos. Si los datos del proyecto de prueba están incompletos,
el EVM retornará ceros y será difícil validar. Preparar datos de prueba reales el Dia 1.

---

## Checklist de Handoff entre Fases

### Handoff 1: Modelos → Servicios (fin Dia 1)

- [ ] `python manage.py migrate` ejecutado sin errores
- [ ] `python manage.py check` → 0 issues
- [ ] Los 4 modelos tienen `company` FK heredado de BaseModel
- [ ] `NUMERIC(15,2)` en todos los campos monetarios (verificar con `\d` en psql)
- [ ] Django Admin básico muestra los 4 modelos

### Handoff 2: Backend → Frontend (fin Dia 5)

- [ ] Los 20+ endpoints responden 200/201 con datos reales en Postman/curl
- [ ] Endpoint EVM retorna los 10 campos definidos (sin KeyError en producción)
- [ ] Tests >= 85% en budget_services.py (ejecutar y capturar output)
- [ ] Celery task importa sin errores: `from apps.proyectos.tasks import weekly_budget_snapshot_task`
- [ ] No hay división por cero cuando AC=0 o PV=0
- [ ] Autenticación JWT funciona en todos los endpoints
- [ ] Ningún endpoint filtra por company incorrecto (probar con 2 empresas en dev)

### Handoff 3: Frontend → Testing (fin Dia 10)

- [ ] `npx tsc --noEmit` → 0 errores
- [ ] `ng build --configuration=production` → 0 errores nuevos
- [ ] Tab "Budget" visible en ProyectoDetail sin errores de consola
- [ ] BudgetSummaryCard muestra datos reales (no mock)
- [ ] EVMChart renderiza con al menos 1 punto de datos
- [ ] CostEntry CRUD funciona end-to-end (crear, editar, eliminar con confirm)
- [ ] Ningún `any` en archivos nuevos de Feature #7

### Handoff 4: Testing → Documentación (fin Dia 12)

- [ ] Capturas de pantalla del flujo completo guardadas en `docs/evidence/feature-7/`
- [ ] Casos edge EVM validados (AC=0, progreso=0, progreso=100)
- [ ] Celery task ejecutada manualmente sin errores
- [ ] Auditoría de seguridad completada (todos los SEC-XX)
- [ ] Ningún dato de otra empresa accesible vía API

---

## Mitigación de Riesgos

### Riesgo 1: Complejidad del cálculo de EV (Earned Value)

**Probabilidad:** Alta. EV = BAC * % completado es una simplificación; el % completado
del proyecto ya existe pero puede no ser preciso si las tareas no tienen estimaciones de esfuerzo.

**Impacto:** EVM metrics incorrectas → alertas falsas → pérdida de confianza del usuario.

**Mitigación:**
- Dia 3: Implementar EV como `BAC * project.progress` (usa campo existente Task.progress).
  Es menos preciso que EV ponderado por esfuerzo, pero es correcto para MVP.
- Documentar explícitamente en la User Guide que EV usa % completado promedio de tareas.
- DEC-028: Registrar esta simplificación en DECISIONS.md para revisión futura.
- Test específico: `test_evm_partial_progress` valida que EV = BAC * 0.5 cuando progreso = 50%.

**Plan B:** Si la simplificación genera quejas de usuarios, implementar EV ponderado por
`planned_cost` de cada tarea en una iteración futura (sin cambiar el API contract).

---

### Riesgo 2: Precision de dinero en Python/JSON

**Probabilidad:** Media. Python `Decimal` pierde precisión si se convierte a `float`
en algún punto del serializer o del template Angular.

**Impacto:** Montos incorrectos mostrados en UI. Error de redondeo acumulativo en EAC/ETC.

**Mitigación:**
- Todos los campos de dinero en serializers: `DecimalField(max_digits=15, decimal_places=2, coerce_to_string=True)`
- En Angular: manejar como `string`, nunca como `number`. Usar `parseFloat()` solo para mostrar
  con pipe `currency`, nunca para cálculos en el frontend.
- Test: `test_decimal_precision` verifica que `1/3 * 3` no produce `0.9999999`.
- En EVM: todos los cálculos intermedios permanecen como `Decimal` hasta el `return`.

---

### Riesgo 3: Multi-moneda futura

**Probabilidad:** Media. El cliente puede pedir soporte multi-moneda (USD/EUR) en 3-6 meses.

**Impacto:** Si no se prepara el modelo ahora, migrar después requiere cambiar todas las
tablas de money.

**Mitigación:**
- Dia 1: Agregar campo `currency = CharField(max_length=3, default='COP')` en ProjectBudget y CostEntry.
  No implementar conversión de monedas ahora, solo guardar el campo.
- Todas las operaciones EVM asumen misma moneda (no mezclar COP y USD).
- Agregar validación en service: si el proyecto tiene budgets en diferentes monedas, lanzar
  `ValidationError` con mensaje claro en lugar de calcular incorrectamente.
- DEC-030: Documentar que multi-moneda es posible pero no implementado en MVP.

---

### Riesgo 4: Performance de EVM en proyectos grandes

**Probabilidad:** Baja para MVP. Proyectos típicos tienen < 200 tareas.

**Impacto:** EVMMetricsView lenta (> 3s) en proyectos con 1000+ cost entries.

**Mitigación:**
- Usar `aggregate()` de Django para sumas (una sola query SQL, no loop Python).
- Agregar `select_related` en todos los querysets de budget_services.
- Si la query de EVM supera 500ms en pruebas: agregar `cached_property` con Django cache (1 min TTL).
- Invalidar cache al crear/actualizar CostEntry o Task.

---

### Riesgo 5: Celery Beat no configurado en dev

**Probabilidad:** Alta. El ambiente de dev puede no tener Celery Beat corriendo.

**Impacto:** Los snapshots semanales no se ejecutan. El gráfico EVM queda sin datos históricos.

**Mitigación:**
- Dia 10: Agregar botón "Crear snapshot manual" en el tab Budget (FE-09).
  Así el desarrollador puede generar snapshots para pruebas sin Celery.
- En User Guide: documentar que el snapshot automático requiere Celery Beat activo en producción.
- En docs: agregar instrucción de configuración de Celery Beat para AWS ECS.

---

## Definición de Done — Feature #7

Feature #7 se considera COMPLETA cuando se cumplen TODOS los siguientes criterios:

### Backend
- [ ] 4 modelos migrados y en producción (ProjectBudget, CostEntry, BudgetSnapshot, BudgetAlert)
- [ ] 20+ endpoints REST operativos con autenticación JWT
- [ ] EVM: 10 métricas calculadas correctamente (PV, EV, AC, BAC, CV, SV, CPI, SPI, EAC, VAC)
- [ ] Celery task `weekly_budget_snapshot_task` funciona sin errores
- [ ] Tests >= 85% en budget_services.py (`pytest --cov`)
- [ ] `python manage.py check` → 0 issues
- [ ] Ningún campo monetario usa `float` (verificado con grep)
- [ ] Company isolation: ningún endpoint retorna datos de otra empresa

### Frontend
- [ ] 6 componentes creados con `ChangeDetectionStrategy.OnPush`
- [ ] `npx tsc --noEmit` → 0 errores strict
- [ ] `ng build --configuration=production` → 0 errores nuevos
- [ ] Tab "Budget" integrada en ProyectoDetail con carga lazy
- [ ] Cero uso de `any` en archivos de Feature #7
- [ ] Estado vacío con `sc-empty-state` en CostEntryTable y BudgetPlanningTable
- [ ] Confirmación de eliminación via `MatDialog` con `ConfirmDialogComponent`
- [ ] Feedback via `MatSnackBar` en todas las acciones CRUD

### Funcional
- [ ] Flujo completo validado: planificar → aprobar → registrar costos → ver EVM
- [ ] Alertas se crean automáticamente al superar umbrales
- [ ] Snapshot manual funciona desde la UI
- [ ] Rol company_admin puede aprobar, rol seller no puede
- [ ] Capturas de pantalla de evidencia guardadas en `docs/evidence/feature-7/`

### Documentación
- [ ] `docs/FEATURE-7-API-DOCS.md` con 20+ endpoints documentados
- [ ] `docs/FEATURE-7-USER-GUIDE.md` en español
- [ ] `CONTEXT.md` actualizado con Feature #7 completa
- [ ] `DECISIONS.md` con DEC-028, DEC-029, DEC-030

---

## Plan de Rollback

Si una fase se bloquea y no puede resolverse en 1 dia adicional, aplicar el rollback
correspondiente para no detener el proyecto completo.

### Si Backend se bloquea en EVM (Dia 3)

**Síntoma:** Cálculo de EV incorrecto en todos los casos de prueba.

**Rollback:**
1. Comentar `calculate_evm_metrics()` y retornar objeto con valores 0.
2. Marcar endpoints de EVM como `[WIP]` en la documentación.
3. Continuar con CRUD de budgets y cost entries (funciona independientemente).
4. Resolver EVM en sesión separada con casos de prueba más detallados.
5. Frontend: mostrar "EVM no disponible" en el componente EVMChart hasta que el backend esté listo.

**Tiempo máximo de rollback:** 30 minutos.

---

### Si Frontend se bloquea en EVMChart (Dia 9)

**Síntoma:** Chart.js no renderiza correctamente las 3 series con los datos de snapshots.

**Rollback:**
1. Reemplazar EVMChart con una tabla simple `mat-table` que muestre los snapshots.
2. Columnas: Fecha | PV | EV | AC | CPI | SPI.
3. Reutilizar patrón de `mat-table` ya usado en BaselineComparison (Feature #6).
4. Crear la versión Chart.js en una sesión separada.
5. La feature es funcional sin el gráfico visual.

**Tiempo máximo de rollback:** 45 minutos.

---

### Si Celery task bloquea el Dia 5

**Síntoma:** `weekly_budget_snapshot_task` falla en import o en ejecución.

**Rollback:**
1. Remover el decorador `@shared_task` temporalmente.
2. Convertir la función en una función Python regular que llama los services.
3. Exponer un endpoint `POST /api/v1/projects/budget-snapshots/run-weekly/`
   protegido con `is_staff=True` que ejecuta la misma lógica.
4. En producción: trigger vía cron que llama ese endpoint.
5. Celery task se reintegra en iteración siguiente cuando el ambiente esté listo.

**Tiempo máximo de rollback:** 20 minutos.

---

### Si los tests no alcanzan 85% en Dia 5

**Síntoma:** `pytest --cov` muestra 70-84% en budget_services.py.

**Acción (no rollback — ajuste de alcance):**
1. Identificar las funciones sin cobertura (output de `--cov-report=term-missing`).
2. Priorizar tests de EVM calculations (alto riesgo de regresión).
3. Marcar las funciones de bajo riesgo (get_project_budgets, get_cost_entries) como
   "cubiertos por integration tests" en el PR.
4. Añadir al backlog: tests adicionales en la siguiente sesión de mantenimiento.
5. El mínimo aceptable para PR es 80% (umbral del CLAUDE.md) si 85% no es alcanzable el Dia 5.

---

## Secuencia de Ejecución — Chunks por Sesión

Siguiendo el patrón de Features 5 y 6, cada chunk representa una sesión de trabajo.
Limpiar contexto (`/clear`) entre chunks para mantener el contexto del LLM manejable.

| Chunk | Sesión | Contenido | Criterio de salida |
|-------|--------|-----------|-------------------|
| 1 | 1 | BG-01–BG-05: Modelos + Migración | `migrate` exitoso |
| 2 | 2 | BG-06–BG-07: Serializers + CRUD services | Services importan sin errores |
| 3 | 3 | BG-08–BG-10: EVM + Alertas + Snapshots | Tests EVM pasando |
| 4 | 4 | BG-11–BG-13: Views + URLs | 20+ endpoints verificados en Postman |
| 5 | 5 | BG-14–BG-17: Celery task + Tests >= 85% | pytest --cov >= 85% |
| 6 | 6 | FE-01–FE-02: Interfaces TS + budget.service.ts | ng build sin errores |
| 7 | 7 | FE-03–FE-06: 4 componentes (summary, alerts, form, table) | Componentes renderizan en dev |
| 8 | 8 | FE-07–FE-09: Planning table + EVM chart + integración | Feature e2e funcional |
| 9 | 9 | QA-01–SEC-06: Testing + auditoría + docs + cierre | Feature #7 DONE |

---

*Generado: 27 Marzo 2026 — Phase 0 Feature #7*
*Milestone: 100% Odoo parity — Feature 7 de 7*
