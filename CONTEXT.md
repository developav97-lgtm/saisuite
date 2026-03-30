# CONTEXT.md - Estado del Proyecto Saicloud

**Última actualización:** 29 Marzo 2026
**Sesión:** Feature #8 — Sistema de Licencias Multi-Tenant — COMPLETA (Backend: modelos, migraciones, servicios, middleware, management command. Frontend: pantalla bloqueante, guard, panel superadmin, alertas)

---

## ✅ COMPLETADO (29 Marzo 2026) — Feature #8: Sistema de Licencias Multi-Tenant

### Backend — Chunk 1: Modelos + Migraciones

- ✅ `CompanyLicense` extendido: `concurrent_users`, `modules_included` (JSON), `messages_quota/used`, `ai_tokens_quota/used`, `last_reset_date`, `created_by` (FK User)
- ✅ `LicenseHistory` nuevo modelo: historial de cambios de licencia por tipo (created/renewed/extended/suspended/activated/modified)
- ✅ `UserSession` nuevo modelo en `apps/users`: `session_id` UUID único, `login_time`, `last_activity`, `ip_address`, `user_agent`. Método `is_active()` con timeout 8h. Método `touch()` para actualizar actividad.
- ✅ Migración `0005_license_concurrent_modules_history.py` — companies
- ✅ Migración `0003_usersession.py` — users
- ✅ Fix `check=Q(` → `condition=Q(` en `proyectos/models.py` y migraciones 0015 y 0018 (bug Django 5 CheckConstraint)

### Backend — Chunk 2: Servicios

- ✅ `LicenseService.create_license_with_history()` — crea licencia + registra en historial
- ✅ `LicenseService.update_license_with_history()` — actualiza licencia + detecta tipo de cambio automáticamente
- ✅ `LicenseService.get_license_history()` — historial de una licencia
- ✅ `LicenseService.reset_monthly_usage_all()` — reset masivo de mensajes/tokens
- ✅ `LicenseService.count_active_sessions()` — sesiones activas de empresa
- ✅ `LicenseService.verify_concurrent_limit()` — verifica si puede admitir nuevo usuario
- ✅ `SessionService` (nuevo en `companies/services.py`): `create_session`, `validate_session`, `invalidate_session`, `invalidate_user_sessions`
- ✅ `AuthService.login()` extendido: verifica licencia + concurrencia al login, crea `UserSession`, incluye `session_id` en JWT payload
- ✅ `AuthService.logout()` extendido: invalida `UserSession` al hacer logout

### Backend — Chunk 3: Middleware + Serializers

- ✅ `LicensePermission` extendida: valida `session_id` del JWT en cada request, llama `session.touch()`, bloquea con 401 si sesión inválida
- ✅ `CompanyLicenseSerializer` actualizado: incluye todos los nuevos campos + historial + is_active_and_valid
- ✅ `CompanyLicenseSummarySerializer` — versión ligera para listas
- ✅ `LicenseHistorySerializer` — solo lectura
- ✅ `CompanyLicenseWriteSerializer` — reescrito con Serializer (no ModelSerializer) para incluir nuevos campos
- ✅ `TenantCreateSerializer` — crear empresa + licencia en un paso
- ✅ `TenantWithLicenseSerializer` — empresa con resumen de licencia + usuarios activos + módulos
- ✅ `LicenseSummarySerializer` en users/serializers — incluido en `UserMeSerializer`/`CompanySummarySerializer`

### Backend — Chunk 4: Views + URLs

- ✅ `AdminTenantListView` — GET/POST `/api/v1/admin/tenants/`
- ✅ `AdminTenantDetailView` — GET/PATCH `/api/v1/admin/tenants/{pk}/`
- ✅ `AdminTenantLicenseView` — GET/POST/PATCH `/api/v1/admin/tenants/{pk}/license/`
- ✅ `AdminLicenseHistoryView` — GET `/api/v1/admin/tenants/{pk}/license/history/`
- ✅ `AdminLicensePaymentView` — POST `/api/v1/admin/tenants/{pk}/license/payments/`
- ✅ `AdminTenantActivateView` — POST `/api/v1/admin/tenants/{pk}/activate/`
- ✅ `apps/companies/admin_urls.py` creado
- ✅ `config/urls.py` actualizado: agrega `/api/v1/admin/tenants/`
- ✅ `LoginView` actualizado: pasa ip_address y user_agent al service

### Backend — Chunk 5: Management Command

- ✅ `management/commands/reset_monthly_usage.py` — reset masivo contadores IA
- ✅ Flags: `--dry-run`
- ✅ Scheduling: AWS EventBridge `cron(0 0 1 * ? *)` o `0 0 1 * * /app/manage.py reset_monthly_usage`

### Frontend — Chunk 6: Modelos + Guard + Pantalla bloqueante

- ✅ `auth.models.ts` actualizado: `LicenseSummary`, `CompanySummary.license`, `UserProfile.is_staff`
- ✅ `license.guard.ts` creado: redirige a `/license-expired` si sin licencia válida. Exentos: superadmin, staff.
- ✅ `app.routes.ts` actualizado: `licenseGuard` en rutas privadas
- ✅ `LicenseExpiredComponent` mejorado: 2 modos (`no_license` y `session_expired` por query param)
- ✅ `auth.interceptor.ts` actualizado: detecta "otro dispositivo" en 401 → redirige a `/license-expired?reason=session_expired`
- ✅ `AuthService.clearStoragePublic()` expuesto para el interceptor

### Frontend — Chunk 7: Panel Superadmin Tenants

- ✅ `tenant.model.ts` — todos los tipos TypeScript (Tenant, TenantLicense, LicenseHistory, LicensePayment, etc.)
- ✅ `tenant.service.ts` — listTenants, getTenant, createTenant, updateTenant, setTenantActive, getLicense, createLicense, updateLicense, getLicenseHistory, addPayment
- ✅ `TenantListComponent` — tabla con chips de estado, días hasta vencimiento, usuarios activos, acciones
- ✅ `TenantFormComponent` — formulario tabs (empresa / licencia / historial), crear y editar
- ✅ `admin.routes.ts` actualizado: rutas `/admin/tenants`, `/admin/tenants/nuevo`, `/admin/tenants/:id`
- ✅ `SidebarComponent` actualizado: inyecta AuthService, muestra "Tenants (Superadmin)" solo para superadmins/staff

### Frontend — Chunk 8: Alertas de Vencimiento

- ✅ `ShellComponent` actualizado: `licenseWarning` signal (computed), banner de alerta con 3 niveles
  - 30-8 días: warning amarillo
  - 7-2 días: danger rojo claro
  - 1 día: critical rojo + animación pulse
- ✅ Banner descartable con botón X

### Estado de tests

- ⚠️ Tests unitarios del sistema de licencias pendientes (deuda técnica)
- ✅ `python manage.py check` — 0 issues
- ✅ `npx tsc --noEmit` — 0 errores TypeScript
- ✅ `ng build --configuration=production` — compila (solo errores de budget pre-existentes)

### Endpoints disponibles — Feature #8 (Sistema de Licencias)

```
GET/POST  /api/v1/admin/tenants/
GET/PATCH /api/v1/admin/tenants/{pk}/
POST      /api/v1/admin/tenants/{pk}/activate/
GET/POST/PATCH /api/v1/admin/tenants/{pk}/license/
GET       /api/v1/admin/tenants/{pk}/license/history/
POST      /api/v1/admin/tenants/{pk}/license/payments/
```

### Decisiones

- DEC-030: Extender CompanyLicense vs nuevo modelo
- DEC-031: LicensePermission como DRF Permission vs Middleware WSGI

---

**Sesión:** Feature #7 — Budget & Cost Tracking — COMPLETA (Chunks 1-10: modelos, migraciones, servicios, vistas, URLs, tests services, Angular, tests vistas, management command, documentación)

---

## ✅ COMPLETADO (28 Marzo 2026) — Feature #7 COMPLETA: Budget & Cost Tracking

### Chunk 1 — Modelos + Migraciones + Serializers (BG-01 a BG-06)
- ✅ `models.py`: `ResourceCostRate`, `ProjectBudget`, `ProjectExpense`, `BudgetSnapshot`, `ExpenseCategory` (TextChoices)
- ✅ `migration 0018_feature_7_budget_models.py`: Generada con `makemigrations`
- ✅ `migration 0019_feature_7_budget_indexes.py`: Índice parcial único `WHERE end_date IS NULL` via RunSQL + 2 índices compuestos de performance
- ✅ `budget_serializers.py`: 14 serializers — Lista/Detalle/Write para ResourceCostRate, Budget, Expense; BudgetSnapshot read-only; CostSummary, CostBreakdownResource/Task, BudgetVariance, BudgetAlert, EvmMetrics, InvoiceLineItem/Data

### Chunk 2 — Services (BG-07 a BG-14)
- ✅ `budget_services.py`: 7 clases de servicio
  - `CostCalculationService`: `_build_rate_index` (O(2-4) queries), `_resolve_rate`, `get_labor_cost`, `get_expense_cost`, `get_total_cost`, `get_budget_variance`, `get_cost_by_resource`, `get_cost_by_task`
  - `EVMService`: `get_evm_metrics` (BAC, PV, EV, AC, CV, SV, CPI, SPI, EAC, ETC, TCPI, VAC, schedule_health, cost_health)
  - `BudgetManagementService`: `set_project_budget` (bloqueado si aprobado), `approve_budget`, `check_budget_alerts`
  - `ExpenseService`: `create_expense`, `list_expenses`, `approve_expense` (segregación de funciones), `update_expense`, `delete_expense`
  - `ResourceCostRateService`: `get_active_rate`, `_validate_overlap` (álgebra de intervalos), `create_rate`, `update_rate`, `delete_rate`
  - `BudgetSnapshotService`: `create_snapshot` (idempotente), `list_snapshots`
  - `InvoiceService`: `generate_invoice_data` (labor lines + gastos aprobados facturables)

### Chunk 3-4 — Views + URLs (BG-15 a BG-28)
- ✅ `budget_views.py`: 15 APIViews — ProjectBudgetView, BudgetApproveView, BudgetVarianceView, BudgetAlertsView, BudgetSnapshotListView, CostTotalView, CostByResourceView, CostByTaskView, EVMMetricsView, InvoiceDataView, ProjectExpenseListView, ProjectExpenseDetailView, ExpenseApproveView, CostRateListView, CostRateDetailView
- ✅ `urls.py`: 15 nuevas rutas bajo `# Budget & Cost Tracking — Feature #7`

### Chunk 5 — Tests (BG-53 a BG-58)
- ✅ `tests/test_budget_services.py`: 73 tests, 93% cobertura de `budget_services.py`
- ✅ Fix: `'created'` → `'is_new'` en logging (LogRecord conflict con campo reservado)

### Chunk 6 — Angular Models + Services (BG-34 a BG-37)
- ✅ `models/budget.model.ts`: 20+ interfaces TypeScript — ResourceCostRate, ProjectBudget, ProjectExpense, BudgetSnapshot, CostSummary, CostBreakdown*, BudgetVariance, BudgetAlert, EvmMetrics, InvoiceData, etc.
- ✅ `services/budget.service.ts`: getBudget, createBudget, updateBudget, approveBudget, getVariance, getAlerts, getSnapshots, createSnapshot, getTotalCost, getCostByResource, getCostByTask, getEvmMetrics, getInvoiceData
- ✅ `services/expense.service.ts`: getExpenses, createExpense, getExpense, updateExpense, deleteExpense, approveExpense
- ✅ `services/cost-rate.service.ts`: getRates, getRate, createRate, updateRate, deleteRate

### Chunk 7 — Angular Budget Dashboard (BG-38 a BG-46)
- ✅ `components/budget-dashboard/budget-dashboard.component.ts/.html/.scss` — Dashboard completo: alertas, summary cards, EVM metrics, formulario presupuesto inline, formulario gastos inline, tabla gastos con aprobación/eliminación, cost breakdown table con @defer on viewport
- ✅ `proyecto-detail.component.ts/.html`: Tab "Presupuesto" (Tab 12) con @defer on viewport

### Chunk 8 — Management Command (BG-47)
- ✅ `management/commands/budget_weekly_snapshot.py` — Django management command (en lugar de Celery, DEC-029)
- ✅ Flags: `--dry-run`, `--project-id <uuid>`, `--company-id <uuid>`
- ✅ Loop con try/except por proyecto: un fallo no detiene el resto
- ✅ Scheduling: AWS EventBridge `cron(0 6 ? * MON *)` o cron del sistema `0 6 * * 1`

### Chunk 9 — Tests de Vistas (BG-59 a BG-65)
- ✅ `tests/test_budget_command.py`: 13 tests — no-projects warning, skip sin presupuesto, snapshot creado, idempotente, dry-run, filtros project-id/company-id, proyectos cerrados excluidos, error en uno no detiene otros, resumen
- ✅ `tests/test_budget_views.py`: 60 tests — todos los endpoints con GET/POST/PATCH/DELETE, 200/201/400/403/404, multi-tenant isolation
- ✅ 3 bugs corregidos en `budget_views.py`: `approver_user_id`→`approved_by_user_id`, `CostTotalView` kwargs inválidos, `EVMMetricsView` as_of_date no parseado
- ✅ 1 bug corregido en `budget_services.py`: `approve_expense` ahora lanza `PermissionDenied` para self-approval y re-lanza `DoesNotExist` para not found

### Chunk 10 — Documentación (BG-66 a BG-70)
- ✅ `docs/FEATURE-7-API-DOCS.md` — 15 endpoints documentados con ejemplos JSON, errores, reglas de negocio, management command
- ✅ `DECISIONS.md` — DEC-028 (EVM simplificado), DEC-029 (management command vs Celery)
- ✅ `CONTEXT.md` — este bloque

### Estado de tests
- ✅ 936 tests pasando (up from 775 al inicio de Feature #7), 6 failures pre-existentes (no relacionados)
- ✅ Cobertura `budget_services.py`: 93% (target 85%)
- ✅ Cobertura `budget_views.py`: ~82% (target 80%)

### Endpoints disponibles — Feature #7
- GET/POST/PATCH `/api/v1/projects/{id}/budget/`
- POST         `/api/v1/projects/{id}/budget/approve/`
- GET          `/api/v1/projects/{id}/budget/variance/`
- GET          `/api/v1/projects/{id}/budget/alerts/`
- GET/POST     `/api/v1/projects/{id}/budget/snapshots/`
- GET          `/api/v1/projects/{id}/costs/total/`
- GET          `/api/v1/projects/{id}/costs/by-resource/`
- GET          `/api/v1/projects/{id}/costs/by-task/`
- GET          `/api/v1/projects/{id}/costs/evm/`
- GET          `/api/v1/projects/{id}/invoice-data/`
- GET/POST     `/api/v1/projects/{id}/expenses/`
- GET/PATCH/DEL `/api/v1/projects/expenses/{pk}/`
- POST         `/api/v1/projects/expenses/{pk}/approve/`
- GET/POST     `/api/v1/projects/resources/cost-rates/`
- GET/PATCH/DEL `/api/v1/projects/resources/cost-rates/{pk}/`

### Criterio de salida Feature #7 completa
- ✅ 936 tests pasando, 6 failures pre-existentes
- ✅ 93% cobertura budget_services.py
- ✅ 15 endpoints documentados
- ✅ DEC-028 y DEC-029 en DECISIONS.md

---

**Sesión:** Feature #6 — Advanced Scheduling — COMPLETA (Chunk 8: Gantt overlays + documentación)

---

## 📊 ESTADO ACTUAL

### Proyecto
- **Nombre:** Saicloud (SaiSuite)
- **Stack:** Django 5 + Angular 18 + PostgreSQL 16 + n8n + AWS
- **Fase:** Desarrollo activo
- **Último milestone:** Feature #7 — Budget & Cost Tracking completa (15 endpoints, 7 servicios, dashboard Angular, management command semanal, 936 tests)

---

## ✅ COMPLETADO (27 Marzo 2026) — Feature #6 Chunk 8: Gantt Overlays + Documentación

### SK-41: Gantt Scheduling Overlays
- ✅ `gantt-view.component.ts`: Toggle buttons + `showCriticalPath`/`showFloat`/`showBaseline` signals; `loadCriticalPath()`, `loadFloatData()`, `loadActiveBaseline()`, `rerenderGantt()` methods; `initGantt()` now delegates to `rerenderGantt()`
- ✅ `gantt-view.component.html`: 3 overlay toggle buttons (Ruta crítica, Holgura, Baseline) + loading overlay `mat-progress-bar` + baseline active chip
- ✅ `gantt-view.component.scss`: `.gv-overlay-toggles`, `.gv-overlay-active`, `.gv-baseline-chip`; `.critical-task` CSS rule `fill: var(--sc-danger, #e53935) !important`

### SK-50: API Docs
- ✅ `docs/FEATURE-6-API-DOCS.md` — 15 endpoints documentados (auto-schedule, level-resources, critical-path, float, constraints CRUD, baselines CRUD + compare, scenarios CRUD + run + compare)

### SK-51: User Guide
- ✅ `docs/FEATURE-6-USER-GUIDE.md` — Guía completa para gerentes de proyecto: Auto-Schedule, Gantt overlays, Baselines, What-If, Restricciones, FAQ

### SK-52: CONTEXT.md + DECISIONS.md actualización
- ✅ Este bloque de contexto
- ✅ `DECISIONS.md` — DEC-026: DisableMigrations en testing, DEC-027: Gantt overlay renderizado

### Criterio de salida Feature #6 completa
- ✅ `npx tsc --noEmit` — 0 errores TypeScript strict
- ✅ Backend: 71/71 tests, 85% cobertura scheduling_services.py
- ✅ 15 endpoints documentados
- ✅ Guía de usuario en español para PMs

---

## ✅ COMPLETADO (27 Marzo 2026) — Feature #6 Chunk 7: Frontend Componentes

### Componentes creados
- ✅ `components/scheduling/float-indicator/float-indicator.component.ts` — SK-40: Badge chip reutilizable (isCritical → "CRÍTICA" rojo, floatDays > 0 → "Float: Xd" azul)
- ✅ `components/scheduling/auto-schedule-dialog/` — SK-36: Dialog dos fases (configurar ASAP/ALAP → Calcular dry_run → preview → Aplicar)
- ✅ `components/scheduling/task-constraints-panel/` — SK-37: Panel add/list/delete restricciones con 8 ConstraintTypes y datepicker condicional
- ✅ `components/scheduling/baseline-comparison/` — SK-38: mat-table comparativa baseline vs actual con paginación client-side y badges de estado
- ✅ `components/scheduling/what-if-scenario-builder/` — SK-39: Lista + detalle de escenarios, crear inline, correr simulación
- ✅ `proyecto-detail.component.ts/.html` — SK-42/SK-43: Botón Scheduling (mat-menu) + 2 nuevas tabs (Baselines, Escenarios) con @defer on viewport

### Criterio de salida
- ✅ `npx tsc --noEmit` — 0 errores TypeScript strict
- ✅ `ng build --configuration=production` — 0 errores nuevos (solo error pre-existente tarea-detail.scss budget)
- ✅ Todos los componentes con ChangeDetectionStrategy.OnPush, input() signals, inject(), @if/@for

---

## ✅ COMPLETADO (27 Marzo 2026) — Feature #6 Chunk 6: Frontend Modelos + Servicios

### Archivos creados
- ✅ `frontend/src/app/features/proyectos/models/scheduling.model.ts` — SK-30: `ConstraintType`, `TaskConstraint`, `AutoScheduleRequest/Result`, `LevelResourcesRequest/Result`, `CriticalPathResponse`, `FloatData`
- ✅ `frontend/src/app/features/proyectos/models/baseline.model.ts` — SK-31: `ProjectBaselineList`, `ProjectBaselineDetail`, `CreateBaselineRequest`, `BaselineComparison`, `BaselineComparisonTask`
- ✅ `frontend/src/app/features/proyectos/models/what-if.model.ts` — SK-32: `WhatIfScenarioList`, `WhatIfScenarioDetail`, `CreateWhatIfScenarioRequest`, `ScenarioComparisonRow`, `CompareScenarioRequest`
- ✅ `frontend/src/app/features/proyectos/services/scheduling.service.ts` — SK-33: `autoSchedule`, `levelResources`, `getCriticalPath`, `getTaskFloat`, `getConstraints`, `setConstraint`, `deleteConstraint`
- ✅ `frontend/src/app/features/proyectos/services/baseline.service.ts` — SK-34: `list`, `create`, `get`, `delete`, `compare`
- ✅ `frontend/src/app/features/proyectos/services/what-if.service.ts` — SK-35: `list`, `create`, `get`, `delete`, `runSimulation`, `compare`

### Criterio de salida
- ✅ `npx tsc --noEmit` — 0 errores TypeScript strict
- ✅ `ng build --configuration=production` — 0 errores (warnings de CSS budget son pre-existentes de tarea-detail.component.scss)

### Deuda técnica resuelta en Chunk 5 (backend)
- ✅ `DisableMigrations` en testing.py — fix definitivo del bug SQLite FK enforcement
- ✅ `CheckConstraint(condition=...)` en models.py — Django 6.0 compatibility
- ✅ `_TaskProxy.activo` eliminado de scheduling_services.py — Task sin campo activo
- ✅ 71/71 tests backend pasando, 85% cobertura scheduling_services.py

---

## ✅ COMPLETADO (27 Marzo 2026) — Feature #5: Reporting & Analytics

### Backend completado
- ✅ **analytics_services.py**: 8 funciones — `get_project_kpis`, `get_task_distribution`, `get_velocity_data`, `get_burn_rate_data`, `get_burn_down_data`, `get_resource_utilization`, `compare_projects`, `get_project_timeline`
- ✅ **analytics_views.py**: 9 APIViews — `ProjectKPIsView`, `ProjectTaskDistributionView`, `ProjectVelocityView`, `ProjectBurnRateView`, `ProjectBurnDownView`, `ProjectResourceUtilizationView`, `ProjectTimelineView`, `CompareProjectsView`, `ExportExcelView`
- ✅ **analytics_serializers.py**: 13 serializers read-only + 2 request serializers (`CompareProjectsRequestSerializer`, `ExportExcelRequestSerializer`)
- ✅ **urls.py**: 9 nuevas rutas bajo `# Analytics — Feature #5`
- ✅ Zero nuevos modelos — todo calculado desde datos existentes
- ✅ Exportación Excel con openpyxl (3 hojas: Summary, KPIs, Task Distribution)

### Endpoints disponibles — Feature #5
- `GET  /api/v1/projects/{id}/analytics/kpis/`
- `GET  /api/v1/projects/{id}/analytics/task-distribution/`
- `GET  /api/v1/projects/{id}/analytics/velocity/?periods=8`
- `GET  /api/v1/projects/{id}/analytics/burn-rate/?periods=8`
- `GET  /api/v1/projects/{id}/analytics/burn-down/?granularity=week`
- `GET  /api/v1/projects/{id}/analytics/resource-utilization/`
- `GET  /api/v1/projects/{id}/analytics/timeline/`
- `POST /api/v1/projects/analytics/compare/`
- `POST /api/v1/projects/analytics/export-excel/`

### Frontend completado
- ✅ **analytics.model.ts**: 13 interfaces TypeScript + 2 request interfaces
- ✅ **analytics.service.ts**: 9 métodos (`getKPIs`, `getTaskDistribution`, `getVelocity`, `getBurnRate`, `getBurnDown`, `getResourceUtilization`, `getTimeline`, `compareProjects`, `exportExcel`)
- ✅ **project-analytics-dashboard**: Componente OnPush con forkJoin paralelo + 4 gráficos Chart.js (burn down, velocity, task distribution doughnut, resource utilization horizontal bar)

### Documentación generada — Feature #5
- ✅ `docs/FEATURE-5-API-DOCS.md` — 9 endpoints documentados con ejemplos JSON
- ✅ `docs/FEATURE-5-USER-GUIDE.md` — Guía para gerentes y coordinadores (español)
- ✅ `docs/FEATURE-5-ARCHITECTURE.md` — Decisiones de diseño y cálculo de métricas

### Decisiones de diseño — Feature #5
- Sin nuevos modelos de BD — métricas calculadas on-the-fly desde `Task`, `TimesheetEntry`, `ResourceAssignment`, `ResourceCapacity`
- Caché: Django file-based cuando sea necesario (Redis no requerido en MVP)
- PDF: jsPDF en frontend (evita dependencias del servidor)
- Excel: openpyxl en backend (streaming como Blob)
- On-Time Rate usa `updated_at` como proxy de `fecha_completion` (limitación conocida MVP)
- Burn Down usa `itertools.accumulate` en Python (evita window functions SQL no portables)

---

## ✅ COMPLETADO (27 Marzo 2026) — Feature #4: Resource Management

### Backend completado
- ✅ **Modelos** (migration 0015): `ResourceAssignment`, `ResourceCapacity`, `ResourceAvailability`, `AvailabilityType`
- ✅ **Seed**: 3 registros `ResourceCapacity` (40h/semana) para usuarios existentes
- ✅ **Django Admin**: 3 admin classes con fieldsets
- ✅ **Serializers** (9 clases): List/Detail/Create para assignments; Capacity; Availability + Create; WorkloadSummary; TeamAvailability
- ✅ **Services** (`resource_services.py`): BK-11 a BK-18 — assign, remove, overallocation, workload, team timeline, capacity, availability, approve
- ✅ **Views** (6 clases): `ResourceAssignmentViewSet`, `ResourceCapacityViewSet`, `ResourceAvailabilityViewSet`, `WorkloadView`, `TeamAvailabilityView`, `UserCalendarView`
- ✅ **URLs** (BK-25): 11 nuevas rutas bajo `/api/v1/projects/`
- ✅ `python manage.py check` — 0 issues

### Endpoints disponibles — Feature #4
- `GET/POST   /api/v1/projects/tasks/{task_pk}/assignments/`
- `GET/DEL    /api/v1/projects/tasks/{task_pk}/assignments/{pk}/`
- `GET        /api/v1/projects/tasks/{task_pk}/assignments/check-overallocation/`
- `GET/POST   /api/v1/projects/resources/capacity/`
- `GET/PATCH/DEL /api/v1/projects/resources/capacity/{pk}/`
- `GET/POST   /api/v1/projects/resources/availability/`
- `GET/DEL    /api/v1/projects/resources/availability/{pk}/`
- `POST       /api/v1/projects/resources/availability/{pk}/approve/`
- `GET        /api/v1/projects/resources/workload/`
- `GET        /api/v1/projects/resources/calendar/`
- `GET        /api/v1/projects/{proyecto_pk}/team-availability/`

### Pendiente — Feature #4 (deuda técnica)
- [ ] Tests: BK-26 test_resource_models, BK-27 test_resource_services (85% min), BK-28 test_resource_views
- [ ] Angular FE-1–FE-10: 8 componentes (ResourceAssignmentCard, ResourceCalendar, WorkloadChart, TeamTimeline, ResourcePanel, AvailabilityForm, CapacityForm, OverallocationBadge)
- [ ] Integración: Tab "Recursos" en TareaDetail (IT-1), avatares en Gantt (IT-2), Tab "Equipo" en ProyectoDetail (IT-3)

---

## ✅ COMPLETADO RECIENTEMENTE (26 Marzo 2026)

### Rename Completo Español → Inglés (REFT-01–REFT-21)
**Tiempo:** ~3 sesiones
**Complejidad:** XL

**Cambios principales:**
- ✅ Migration 0013: 13 `RenameModel` + 11 `AlterField` + 11 `RunSQL` data migrations
- ✅ Todos los modelos renombrados: `Proyecto→Project`, `Fase→Phase`, `Tarea→Task`, `SesionTrabajo→WorkSession`, `TareaDependencia→TaskDependency`, `TerceroProyecto→ProjectStakeholder`, `DocumentoContable→AccountingDocument`, `Hito→Milestone`, `Actividad→Activity`, `ActividadProyecto→ProjectActivity`, `ActividadSaiopen→SaiopenActivity`, `EtiquetaTarea→TaskTag`, `ConfiguracionModulo→ModuleSettings`
- ✅ TextChoices en inglés: `por_hacer→todo`, `en_progreso→in_progress`, `completada→completed`, etc.
- ✅ Related names en inglés: `fases→phases`, `tareas→tasks`, `subtareas→subtasks`, etc.
- ✅ URLs: `/api/v1/proyectos/` → `/api/v1/projects/`, path segments en inglés
- ✅ Todos los aliases de compatibilidad eliminados (REFT-10)
- ✅ 365 tests backend pasando (REFT-11)
- ✅ Angular: status values, URLs y modelos actualizados (REFT-12–16)
- ✅ Management command `migrar_actividades_a_tareas` actualizado
- ✅ URL deprecated `/api/v1/proyectos/` eliminada (REFT-21)

**Decisiones:** DEC-010 (snake_case API), DEC-011 (Angular Material), y decisions de rename en DECISIONS.md

---

## ✅ COMPLETADO (24 Marzo 2026)

### Refactor Arquitectura Proyectos
**Tiempo:** 2 días (23-24 Marzo)  
**Complejidad:** XL  

**Backend Django:**
- ✅ Modelo `ActividadSaiopen` (catálogo maestro reutilizable)
- ✅ Modelo `Fase` actualizado (estado, orden, solo 1 activa)
- ✅ Modelo `Tarea` refactorizado (sin FK proyecto, con FK actividad_saiopen)
- ✅ Campos `cantidad_registrada`, `cantidad_objetivo`
- ✅ Signals progreso automático (Tarea → Fase → Proyecto)
- ✅ `FaseService.activar_fase()`
- ✅ 4 migraciones ejecutadas
- ✅ 19 tests corregidos (services, signals, views)

**Frontend Angular:**
- ✅ Service `ActividadSaiopenService`
- ✅ Autocomplete actividades en formulario
- ✅ **Detalle Tarea con UI Adaptativa** (3 modos):
  - `solo_estados`: Solo selector estado (sin actividad)
  - `timesheet`: Cronómetro + horas (actividad en horas)
  - `cantidad`: Campo clickeable + edición inline (actividad en días/m³/ton)
- ✅ **Kanban con Filtro de Fase**
- ✅ **Activar Fase en FaseList** (columna estado + botón)

**Métricas:**
- Archivos modificados: ~35
- Líneas de código: ~6,500
- Tests corregidos: 19
- Decisiones arquitectónicas: 3 (DEC-020, DEC-021, DEC-022)

---

## 🗂️ ESTRUCTURA ACTUAL

### Backend (Django)
```
apps/proyectos/
├── models/
│   ├── proyecto.py
│   ├── fase.py (estado, orden)
│   ├── tarea.py (sin FK proyecto, con actividad_saiopen)
│   └── actividad_saiopen.py (NUEVO - catálogo compartido)
├── services/
│   ├── proyecto_service.py
│   ├── fase_service.py (activar_fase)
│   └── tarea_service.py
├── serializers/
│   ├── actividad_saiopen_serializer.py (NUEVO)
│   └── tarea_serializer.py (actualizado)
├── views/
│   ├── fase_viewset.py (endpoint activar)
│   └── tarea_viewset.py (endpoint actualizar-cantidad)
└── signals.py (progreso automático)
```

### Frontend (Angular)
```
frontend/src/app/proyectos/
├── models/
│   ├── actividad-saiopen.model.ts (NUEVO)
│   └── tarea.model.ts (actualizado)
├── services/
│   ├── actividad-saiopen.service.ts (NUEVO)
│   ├── fase.service.ts (obtenerFaseActiva, activar)
│   └── tarea.service.ts (actualizarCantidad)
├── components/
│   ├── tarea-form/ (autocomplete actividad)
│   ├── tarea-detail/ (UI adaptativa 3 modos)
│   ├── tarea-kanban/ (filtro fase)
│   └── fase-list/ (columna estado + activar)
```

---

## 📋 DECISIONES ARQUITECTÓNICAS

### DEC-020: Jerarquía Estricta Proyecto → Fases → Tareas
- **Estado:** ✅ Activa
- **Fecha:** 24 Marzo 2026
- **Cambio principal:** Eliminado FK `tarea.proyecto` (redundante)
- **Razón:** Modelo más limpio, progreso automático predecible
- **Consecuencia:** Todas las tareas DEBEN tener fase

### DEC-021: ActividadSaiopen como Catálogo Compartido
- **Estado:** ✅ Activa
- **Fecha:** 24 Marzo 2026
- **Cambio principal:** Actividades reutilizables entre proyectos
- **Razón:** Compatibilidad con Saiopen (ERP local)
- **Consecuencia:** Sincronización vía SQS desde Saiopen

### DEC-022: Medición de Progreso según Unidad de Actividad
- **Estado:** ✅ Activa
- **Fecha:** 24 Marzo 2026
- **Cambio principal:** UI adaptativa según `unidad_medida`
- **Razón:** Cada actividad se mide naturalmente (horas/días/m³)
- **Consecuencia:** 3 modos de UI en detalle de tarea

**Decisiones previas activas:** DEC-001 a DEC-019 (ver DECISIONS.md)

---

## 🚧 PENDIENTES

### Prioridad Alta
- [ ] REFT-22–REFT-27: Angular features pendientes (ModuleLauncher, sidebar contextual, Kanban/Lista toggle, Project cards view, E2E verify)
- [ ] Tabs de Fases en Detalle Proyecto

### Prioridad Media
- [ ] Endpoint Comparación Saiopen (`GET /api/v1/projects/{id}/comparacion-saiopen/`)
- [ ] Sincronización Actividades desde Saiopen (agente + SQS)

### Prioridad Baja
- [ ] Documentación técnica actualizada
- [ ] Panel Admin para SaiopenActivity

---

## 🧪 PRUEBAS PENDIENTES

**Guía completa:** https://www.notion.so/32dee9c3690a810187f7fe510faee8aa

### Casos de Prueba
1. **Detalle Tarea UI Adaptativa:**
   - Caso 1: Tarea sin actividad (solo estados)
   - Caso 2: Tarea con actividad en horas (timesheet)
   - Caso 3: Tarea con actividad en m³ (edición inline)

2. **Kanban con Filtro de Fase:**
   - Dropdown aparece al seleccionar proyecto
   - Filtrado funciona correctamente
   - Limpiar filtros resetea todo

3. **Activar Fase:**
   - Columna estado visible
   - Botón activar solo en planificadas
   - Confirmación + recarga

---

## 📚 DOCUMENTACIÓN

### Notion
- **Metodología:** https://www.notion.so/31dee9c3690a81668fc3cd5080240bb7
- **Decisiones:** https://www.notion.so/323ee9c3690a817e9919cf7f810289fe
- **Refactor Completado:** https://www.notion.so/32dee9c3690a813a8b9fcd45b0f05c60
- **Guía de Pruebas:** https://www.notion.so/32dee9c3690a810187f7fe510faee8aa

### Archivos Locales
- `CLAUDE.md` — Reglas permanentes del proyecto
- `DECISIONS.md` — Decisiones arquitectónicas (DEC-XXX)
- `ERRORS.md` — Registro de errores resueltos
- `CONTEXT.md` — Este archivo (estado sesión a sesión)

### Documentos Base
- `docs/base-reference/Infraestructura_SaiSuite_v2.docx`
- `docs/base-reference/Flujo_Feature_SaiSuite_v1.docx`
- `docs/base-reference/Estandares_Codigo_SaiSuite_v1.docx`
- `docs/base-reference/Esquema_BD_SaiSuite_v1.docx`
- `docs/base-reference/AWS_Setup_SaiSuite_v1.docx`

---

## 🎯 PRÓXIMA SESIÓN — Feature #6 sugerida

### Opción A: Completar deuda técnica Feature #4
Prioridad alta si el cliente va a usar el módulo de recursos pronto.

1. Tests backend Feature #4: `test_resource_models`, `test_resource_services` (cobertura 85% mínimo), `test_resource_views`
2. Componentes Angular Feature #4: `ResourceAssignmentCard`, `ResourceCalendar`, `WorkloadChart`, `TeamTimeline`
3. Integración: Tab "Recursos" en TareaDetail, Tab "Equipo" en ProyectoDetail

**Prerequisitos:**
- `python manage.py migrate` (ya ejecutado, solo verificar)
- `ng serve`

### Opción B: Feature #6 — Notificaciones y Alertas
Notificaciones en tiempo real cuando: tarea vence, presupuesto supera umbral, recurso sobreasignado.

**Stack sugerido:** Django Channels + WebSocket o polling periódico (más simple).
**Decisión pendiente:** Redis para WebSockets vs. polling cada 60s (sin infraestructura adicional).

### Opción C: Feature #6 — Portal de cliente / Stakeholders
Vista de solo lectura para stakeholders externos: progreso del proyecto, hitos, documentos.
Sin autenticación JWT propia — token de acceso público por proyecto.

### Opción D: Completar Analytics — Mejoras MVP
1. Agregar campo `Task.fecha_completion` (migration + signal) para On-Time Rate preciso
2. Implementar granularidad `month` en burn-down
3. Conectar parámetros `metrics` y `date_range` en export-excel

**Recomendación:** Opción A primero (deuda técnica Feature #4), luego Feature #6 Notificaciones.

---

## 📞 CONTACTO & RECURSOS

- **Desarrollador:** Juan David (Fundador, CEO, CTO)
- **Empresa:** ValMen Tech
- **Email:** juan@valmentech.com
- **Repositorio:** (Git local, sin remote por ahora)

---

*Última sesión: 27 Marzo 2026*
*Estado: Feature #5 Analytics completa — 9 endpoints, 4 gráficos Chart.js, exportación Excel, documentación FASE 4 generada*
*Listo para: Feature #4 deuda técnica (tests + Angular FE) o Feature #6 nueva*