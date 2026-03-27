# Feature #5 — Analytics Dashboard Certification Report
**Fecha:** 2026-03-27
**Revisor:** TestingRealityChecker (Integration Agent)
**Evidencia base:** lectura directa de todos los archivos implementados

---

## Veredicto Final

**NEEDS WORK**

El backend es sólido y casi completo. El frontend tiene tres defectos que bloquean
la certificación: ausencia de `computed()` en el componente, dos suscripciones
manuales sin protección contra memory leak, y divergencias entre el modelo TypeScript
y el contrato del serializer backend. Adicionalmente, el SCSS mezcla colores
hardcodeados con variables `var(--sc-*)`.

---

## Checklist Completo

### Backend

- [OK] `analytics_services.py` existe con al menos 6 funciones de métricas
  Evidencia: 8 funciones declaradas (AN-01 a AN-08) en el archivo, con docstrings
  explícitos. Funciones: `get_project_kpis`, `get_task_distribution`,
  `get_velocity_data`, `get_burn_rate_data`, `get_burn_down_data`,
  `get_resource_utilization`, `compare_projects`, `get_project_timeline`.

- [OK] Cada función recibe `company_id` como parámetro (multi-tenant)
  Evidencia: todas las firmas incluyen `company_id: str`. Líneas 36, 191, 252,
  323, 387, 518, 646, 712.

- [OK] `analytics_views.py` tiene `permission_classes` en cada view
  Evidencia: las 9 clases de view (ProjectKPIsView, ProjectTaskDistributionView,
  ProjectVelocityView, ProjectBurnRateView, ProjectBurnDownView,
  ProjectResourceUtilizationView, ProjectTimelineView, CompareProjectsView,
  ExportExcelView) declaran `permission_classes = [CanAccessProyectos]` en su cuerpo.

- [OK] URLs bajo `/api/v1/projects/` registradas en `urls.py`
  Evidencia: las 9 rutas de analytics estan presentes en `urls.py` lineas 248-295.
  7 rutas con `project_pk` y 2 rutas de nivel superior (`analytics/compare/` y
  `analytics/export-excel/`). Total: 9/9 endpoints especificados.

- [OK] Tests en `test_analytics_services.py` con al menos 20 casos
  Evidencia: 38 metodos `def test_*` contados directamente. Clases de test: 8.
  Cubre AN-01 a AN-08 con variantes de proyecto vacio, multi-tenant isolation,
  timesheets y estructura de retorno.

- [OK] No hay logica de negocio en views (solo llaman services)
  Evidencia: todas las views en `analytics_views.py` siguen el patron
  request -> validacion de parametros -> service call -> serializer -> Response.
  La unica logica en views es parseo de query params (`periods`, `start_date`,
  `end_date`, `granularity`) y construccion del HttpResponse para Excel.
  La funcion `_generate_excel_response` contiene llamadas a services y construccion
  de openpyxl — esto es orquestacion de presentacion, aceptable en una helper
  privada de la vista. No hay calculos de negocio en views.

- [OK] No hay `print()` statements
  Evidencia: busqueda de patron `print(` retorna 0 coincidencias en
  `analytics_services.py` y `analytics_views.py`. Logging correcto con
  `logger.info(..., extra={...})` en todas las funciones.

### Frontend

- [OK] `analytics.model.ts` con interfaces TypeScript (sin `any`)
  Evidencia: 10 interfaces declaradas. No aparece `any` en el archivo.
  Tipos bien definidos: `number`, `string`, `string | null`, `boolean`.

- [OK] `analytics.service.ts` con metodos tipados
  Evidencia: 9 metodos publicos, todos retornan `Observable<T>` tipado con las
  interfaces del modelo. No hay `any`. `inject()` usado en lugar de constructor.

- [OK] `ProjectAnalyticsDashboardComponent` usa `OnPush`
  Evidencia: linea 32 del componente TS: `changeDetection: ChangeDetectionStrategy.OnPush`.

- [OK] Componente usa `input()` (no `@Input()`)
  Evidencia: linea 48: `readonly projectId = input.required<string>();`
  No existe ninguna declaracion `@Input()` en el archivo.

- [FAIL] Componente usa signals (`signal()`) pero NO usa `computed()`
  Evidencia: el componente declara 6 signals con `signal()` (lineas 51-56).
  Busqueda de `computed(` retorna 0 coincidencias. Los helpers `kpiClass()`,
  `budgetClass()` y `formatVariance()` son metodos normales en lugar de
  `computed()` derivados de los signals de kpis. Esto es un incumplimiento
  del estandar del proyecto Angular (CLAUDE.md: "Use `computed()` for derived
  state"). Al menos `kpiClass` y `budgetClass` deberian ser signals computados
  derivados de `kpis()`.

- [OK] `ngOnDestroy` destruye charts (no memory leak de Charts)
  Evidencia: `ngOnDestroy(): void { this.destroyCharts(); }` en linea 70-72.
  `destroyCharts()` llama `c.destroy()` en cada Chart y resetea el array
  (lineas 126-129). Correcto.

- [FAIL] Dos suscripciones manuales sin proteccion contra memory leak
  Evidencia: el componente implementa `OnDestroy` y destruye charts, pero las
  dos suscripciones a Observables (`forkJoin(...).subscribe()` en linea 84 y
  `this.analyticsService.exportExcel(...).subscribe()` en linea 290) no usan
  `takeUntilDestroyed`, `AsyncPipe`, ni ningun mecanismo de cancelacion.
  Si el componente se destruye mientras la peticion HTTP esta en vuelo (navegacion
  rapida entre tabs), los callbacks `next` y `error` se ejecutaran sobre un
  componente destruido. El estandar del proyecto exige proteccion explicita
  ("Nunca suscripcion manual sin unsubscribe").

- [OK] `@defer (on viewport)` en proyecto-detail
  Evidencia: `proyecto-detail.component.html` lineas 257-263:
  ```
  @defer (on viewport) {
    <app-project-analytics-dashboard [projectId]="p.id" />
  } @placeholder { ... }
  ```
  Implementado correctamente.

- [OK] Chart.js registrado en `main.ts`
  Evidencia: `main.ts` lineas 4-5:
  ```
  import { Chart, registerables } from 'chart.js';
  Chart.register(...registerables);
  ```
  Registrado globalmente antes del bootstrap.

- [OK] Sin `any` en TypeScript
  Evidencia: busqueda de `any` en `analytics.model.ts` y `analytics.service.ts`
  retorna 0 coincidencias. En el componente tampoco aparece. Correcto.

- [OK] Sin `*ngIf` / `*ngFor` (usa `@if` / `@for`)
  Evidencia: el template del dashboard usa `@if (loading())`, `@if (!loading() && kpis(); as k)`,
  `@if (!loading() && !kpis())`. No hay `*ngIf` ni `*ngFor` en el archivo.

- [FAIL] SCSS mezcla colores hardcodeados con variables `var(--sc-*)`
  Evidencia en `project-analytics-dashboard.component.scss`:
  - Linea 30: `color: var(--sc-primary, #1976d2);` — uso correcto de variable con fallback
  - Linea 36: `color: var(--sc-text-muted, #6b7280);` — uso correcto de variable con fallback
  - Linea 45: `color: var(--sc-text-primary, #111827);` — uso correcto de variable con fallback
  - Linea 55: `color: #4caf50;` — COLOR HARDCODEADO SIN VARIABLE
  - Linea 59: `color: #ffc107;` — COLOR HARDCODEADO SIN VARIABLE
  - Linea 63: `color: #f44336;` — COLOR HARDCODEADO SIN VARIABLE
  El estandar del proyecto exige: "variables `var(--sc-*)` siempre, sin colores
  hardcodeados". Los colores de tendencia (`--up`, `--warn`, `--danger`) deberian
  ser `var(--sc-success)`, `var(--sc-warning)`, `var(--sc-danger)`.
  Nota: los colores hardcodeados en el TS del componente (Chart.js datasets) son
  una limitacion aceptable dado que Chart.js no tiene acceso al CSS del documento,
  pero los que estan en el SCSS son completamente evitables.

### Funcional

- [OK] KPIs calculados correctamente (completion_rate es % no fraccion)
  Evidencia: `analytics_services.py` lineas 72-77:
  ```python
  completion_rate = (
      round(completed_tasks / total_tasks * 100, 2)
      if total_tasks > 0
      else 0.0
  )
  ```
  El resultado es 0-100 (porcentaje), no 0-1. Correcto.

- [OK] Burn down usa acumulativo (itertools.accumulate)
  Evidencia: `analytics_services.py` linea 19: `from itertools import accumulate`.
  Linea 472: `cumulative_hours = list(accumulate(weekly_hours))`.
  La lista de horas registradas se acumula correctamente antes de calcular
  `hours_remaining`. Correcto.

- [OK] Multi-tenant: views filtran por `request.user.company`
  Evidencia: todas las views usan `_get_project_for_company(project_pk, company)`
  donde `company = getattr(request.user, 'company', None)`. Esta funcion llama
  `get_object_or_404(Project, id=project_pk, company=company, activo=True)`.
  Los services reciben `company_id=str(project.company_id)` extraido del objeto
  ya validado. Multi-tenant correcto, sin posibilidad de IDOR.

- [OK] Export Excel retorna blob con content-type correcto
  Evidencia: `analytics_views.py` linea 539-542:
  ```python
  response = HttpResponse(
      content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  )
  response['Content-Disposition'] = 'attachment; filename="analytics_report.xlsx"'
  ```
  Content-type XLSX correcto. El frontend en `analytics.service.ts` linea 77
  hace `{ responseType: 'blob' }`. Correcto.

- [FAIL] `TaskDistribution` en frontend no incluye campo `cancelled`
  Evidencia: el backend serializer `TaskDistributionSerializer` incluye
  `cancelled = serializers.IntegerField(read_only=True)` y el servicio
  `get_task_distribution()` devuelve la clave `cancelled`. Sin embargo,
  la interfaz TypeScript `TaskDistribution` en `analytics.model.ts` (lineas 14-28)
  no declara el campo `cancelled`. El template del dashboard tampoco lo muestra
  en el grafico de donut (linea 232 del componente solo lista 5 estados, omitiendo
  `cancelled`). Esto es una divergencia entre backend y frontend: datos enviados
  que el frontend ignora silenciosamente.

- [FAIL] `ResourceUtilization` en frontend no incluye campo `user_email`
  Evidencia: el backend `ResourceUtilizationSerializer` devuelve `user_email`
  (campo EmailField). La interfaz TypeScript `ResourceUtilization` en
  `analytics.model.ts` (lineas 55-62) no declara `user_email`. La interfaz
  tampoco declara `user_name` como ausente — si lo declara — pero `user_email`
  si falta completamente. Divergencia entre contrato backend y modelo frontend.

- [FAIL] `TimelinePhase` en frontend tiene campo `completion_rate` inexistente en backend
  Evidencia: el backend `TimelinePhaseSerializer` no expone `completion_rate`
  (expone `progress: FloatField`). La interfaz TypeScript `TimelinePhase`
  (lineas 87-96) declara `completion_rate: number` en lugar de `progress: number`.
  El campo correcto del backend es `progress`. Esta es una divergencia que causaria
  que `completion_rate` sea siempre `undefined` al consumir el API.

---

## Issues Bloqueantes (NEEDS WORK)

Los siguientes items deben corregirse antes de aprobar:

1. **Suscripciones sin cancelacion (memory leak potencial)**
   Archivo: `project-analytics-dashboard.component.ts` lineas 84 y 290.
   Fix requerido: usar `DestroyRef` con `takeUntilDestroyed()` en ambas
   suscripciones, o refactorizar `loadData()` para exponer un Observable
   consumido con `async pipe`.

2. **`computed()` ausente en el componente**
   Archivo: `project-analytics-dashboard.component.ts`.
   Fix requerido: convertir al menos los helpers `kpiClass()` y `budgetClass()`
   en `computed()` signals derivados de `kpis()`. Esto alinea con el estandar
   del proyecto y mejora la reactividad con OnPush.

3. **Campo `cancelled` ausente en interfaz `TaskDistribution`**
   Archivo: `analytics.model.ts`.
   Fix requerido: agregar `cancelled: number` a la interfaz y la clave
   correspondiente a `percentages`. El grafico de donut deberia incluir
   "Canceladas" como segmento.

4. **Campo `user_email` ausente en interfaz `ResourceUtilization`**
   Archivo: `analytics.model.ts`.
   Fix requerido: agregar `user_email: string` a la interfaz para reflejar
   exactamente el serializer backend.

5. **Campo `completion_rate` incorrecto en interfaz `TimelinePhase`**
   Archivo: `analytics.model.ts`.
   Fix requerido: renombrar `completion_rate` a `progress` para coincidir
   con el campo `progress: FloatField` del `TimelinePhaseSerializer` backend.
   Si ambos se necesitan, el backend debe exponerlos con el mismo nombre.

---

## Issues No Bloqueantes

Los siguientes son mejoras recomendadas pero no criticas para el funcionamiento:

1. **Colores hardcodeados en SCSS (`.pad-kpi__trend--up/warn/danger`)**
   Archivo: `project-analytics-dashboard.component.scss` lineas 55, 59, 63.
   Recomendacion: reemplazar con `var(--sc-success)`, `var(--sc-warning)`,
   `var(--sc-danger)` para cumplir el estandar de variables CSS del proyecto.

2. **`VelocityDataPoint[]` tipado incorrecto en `getVelocity()` y `getBurnRate()`**
   El servicio declara que `getVelocity()` retorna `Observable<VelocityDataPoint[]>`
   pero el backend envuelve los datos en `{ periods: N, data: [...] }`. El
   componente asigna directamente `data.velocity` al signal, lo que fallaria
   si el backend retorna el wrapper. Requiere verificacion contra el contrato
   real o ajuste del tipo de retorno a `{ periods: number; data: VelocityDataPoint[] }`.

3. **Test de acumulativo de burn down no verifica con datos reales**
   `TestGetBurnDownDataAccumulation.test_hours_remaining_is_decreasing_or_equal`
   crea tareas pero no crea `TimesheetEntry`. La prueba verifica que
   `hours_remaining` no aumenta, pero como no hay timesheets, todos los puntos
   tienen `hours_remaining = 40.0` (sin cambio). La prueba pasa pero no
   valida el camino de codigo del acumulativo. Se recomienda agregar un caso
   con TimesheetEntry para validar la disminucion real.

4. **`_generate_excel_response` en analytics_views.py — importacion local de Project**
   Linea 451: `from apps.proyectos.models import Project` dentro de la funcion.
   Project ya esta importado en el top del modulo (linea 48). La importacion
   local es redundante y puede causar confusion.

5. **Granularity 'month' expuesta en el servicio pero no soportada en backend**
   `analytics.service.ts` linea 47 firma: `granularity: 'week' | 'month' = 'week'`.
   El backend en `ProjectBurnDownView` linea 219 solo acepta `'week'` y devuelve
   400 para cualquier otro valor. El tipo del servicio angular crea una falsa
   expectativa de soporte para 'month'.

---

## Metricas

- Tests backend: 38 test methods definidos. Estado de ejecucion: no verificado
  en este reporte (requiere entorno con base de datos). Estructura de tests
  es correcta y coherente.
- Endpoints implementados: 9/9 registrados en urls.py.
- Funciones de servicio backend: 8/8 (AN-01 a AN-08).
- Componentes Angular creados: 1 (ProjectAnalyticsDashboardComponent).
- TypeScript strict: basado en revision de codigo, no se usa `any`. Cumple.
- Issues bloqueantes: 5
- Issues no bloqueantes: 5

---

## Resumen por Capa

| Capa | Estado | Calificacion |
|---|---|---|
| analytics_services.py | Solido. Multi-tenant, logging correcto, accumulate correcto | B+ |
| analytics_views.py | Correcto. Permisos, orquestacion limpia | B+ |
| analytics_serializers.py | Completo. Read-only, bien tipado | A- |
| urls.py | Completo. 9/9 endpoints | A |
| test_analytics_services.py | 38 casos, buena cobertura de escenarios | B+ |
| analytics.model.ts | Tres divergencias con el backend | C+ |
| analytics.service.ts | Tipado de velocity/burn-rate incorrecto, sin `any` | B- |
| dashboard component TS | OnPush, input(), signals. Falta computed(), suscripciones sin cleanup | C+ |
| dashboard component HTML | @if/@for, @defer, empty state, sin *ngIf | A- |
| dashboard component SCSS | Mezcla var(--sc-*) con hardcoded hex | C+ |

**Calificacion global: B- / NEEDS WORK**

---

**Integration Agent:** TestingRealityChecker
**Fecha de evaluacion:** 2026-03-27
**Evidencia base:** lectura directa de 11 archivos implementados
**Re-evaluacion requerida:** despues de corregir los 5 issues bloqueantes
