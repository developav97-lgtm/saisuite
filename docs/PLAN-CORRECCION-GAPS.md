# PLAN DE CORRECCIÓN DE GAPS — Módulo de Proyectos
**Fecha:** 28 Marzo 2026
**Input:** AUDITORIA-MODULO-PROYECTOS.md
**Total gaps:** 22 (11 con severidad asignada + bugs + parciales priorizados)
**Total épicas:** 9
**Tiempo estimado total:** 46–66 horas

---

## MÉTODO DE SCORING

Fórmula: `Score = (Severidad × 0.4) + (Impacto UX × 0.3) + (Esfuerzo × 0.2) + (Dependencias × 0.1)`

| Variable | Escala |
|---|---|
| Severidad | 🔴 Crítico = 10, 🟡 Alto = 7, 🟢 Medio = 4, ⚪ Bajo = 1 |
| Impacto UX | Bloqueante = 10, Dificulta = 7, Nice-to-have = 4, Cosmético = 1 |
| Esfuerzo | Quick (<4h) = 10, Medium (4–8h) = 7, Large (8–16h) = 4, XL (>16h) = 1 |
| Dependencias | Ninguna = 10, 1–2 gaps = 7, 3+ gaps = 4 |

---

## RESUMEN EJECUTIVO

### Distribución por nivel

| Nivel | Descripción | Épicas | Horas estimadas |
|---|---|---|---|
| 0 | Críticos bloqueantes (AHORA) | 3 | 14–20h |
| 1 | Esta semana | 3 | 16–22h |
| 2 | Próxima semana | 2 | 12–18h |
| 3 | Backlog | 1 | 4–6h |
| **Total** | | **9** | **46–66h** |

### Distribución por agente

| Agente | Épicas | Horas estimadas | % |
|---|---|---|---|
| Frontend Developer | 5 | 20–28h | 43% |
| Full-Stack Developer | 3 | 18–28h | 40% |
| Backend Architect | 1 | 4–6h | 10% |
| Tech Lead (decisión) | 1 | 2–4h | 7% |

---

## NIVEL 0: CRÍTICOS BLOQUEANTES (Ejecutar AHORA)

---

### Epic 1: Ruta y acceso a Timesheet Semanal (2–4h)

**Gaps incluidos:**
- GAP #4: Vista semanal de timesheets no enrutada (componente existe, no accesible)

**Prioridad:** 🔴 CRÍTICA
**Score:** 8.6/10
- Severidad: 🔴 Crítico (10) × 0.4 = 4.0
- Impacto UX: Bloqueante (10) × 0.3 = 3.0
- Esfuerzo: Quick <4h (10) × 0.2 = 2.0
- Dependencias: Ninguna (10) × 0.1 = 1.0 — Total: **10.0/10** → ajustado 8.6

**Impacto:** `TimesheetSemanalComponent` está completamente implementado pero inaccesible. Los usuarios no pueden registrar tiempo en modo grilla semanal. El sidebar de proyectos no tiene enlace a timesheets.

**Tiempo estimado:** 2–4 horas
**Agente:** Frontend Developer (2–4h)

**Tareas detalladas:**
1. **Agregar ruta `timesheets` en proyectos.routes.ts** (Frontend Developer, 0.5h)
   - Problema: La ruta `/proyectos/timesheets` no existe en `PROYECTOS_ROUTES`.
   - Solución: Registrar `TimesheetSemanalComponent` con lazy loading en el array de rutas, antes de `:id`.
   - Archivos a modificar: `frontend/src/app/features/proyectos/proyectos.routes.ts`

2. **Agregar enlace "Timesheets" en el sidebar de Proyectos** (Frontend Developer, 0.5h)
   - Problema: El objeto `PROYECTOS_NAV` en `sidebar.component.ts` no incluye un ítem para timesheets.
   - Solución: Agregar `{ label: 'Timesheets', icon: 'schedule', route: '/proyectos/timesheets' }` en la sección "Gestión de Proyectos" del `PROYECTOS_NAV`.
   - Archivos a modificar: `frontend/src/app/core/components/sidebar/sidebar.component.ts`

3. **Verificar que `TimesheetSemanalComponent` carga sin errores** (Frontend Developer, 1h)
   - Problema: Posibles imports faltantes o errores de compilación al ser accedido desde ruta.
   - Solución: Ejecutar `ng build` y navegar a `/proyectos/timesheets` para confirmar.
   - Archivos afectados: `frontend/src/app/features/proyectos/components/timesheet-semanal/timesheet-semanal.component.ts`

**Dependencias:** Ninguna
**Bloquea:** GAP #1 Tab Timesheets en detalle del proyecto (Epic 3)

**► PROMPT LISTO PARA EJECUTAR:**
```
Agente: Frontend Developer
Contexto: SaiSuite Angular 18 + Angular Material. El componente TimesheetSemanalComponent existe
completamente implementado en:
  frontend/src/app/features/proyectos/components/timesheet-semanal/timesheet-semanal.component.ts
  (selector: 'app-timesheet-semanal')

Pero NO está enrutado — por eso es completamente inaccesible para el usuario.

TAREAS:

1. En frontend/src/app/features/proyectos/proyectos.routes.ts:
   - Agregar una nueva ruta ANTES de ':id' con path: 'timesheets' que cargue
     TimesheetSemanalComponent con lazy loading.
   - Seguir el mismo patrón que las rutas 'tareas', 'actividades', 'configuracion' ya existentes.

2. En frontend/src/app/core/components/sidebar/sidebar.component.ts:
   - Localizar el getter PROYECTOS_NAV (línea ~80).
   - En la sección 'Gestión de Proyectos', agregar después del ítem 'Tareas':
     { label: 'Timesheets', icon: 'schedule', route: '/proyectos/timesheets' }

CRITERIOS DE ACEPTACIÓN:
- La URL /proyectos/timesheets carga el TimesheetSemanalComponent sin errores.
- El ítem 'Timesheets' aparece en el sidebar cuando se está en el módulo de proyectos.
- El enlace del sidebar navega correctamente a /proyectos/timesheets.
- ng build --configuration=production compila sin errores TypeScript.

RESTRICCIONES:
- No modificar el componente TimesheetSemanalComponent.
- Usar sintaxis de lazy loading: loadComponent: () => import(...).then(m => m.TimesheetSemanalComponent)
- strict: true en TypeScript — no introducir tipos any.
```

---

### Epic 2: Corrección de endpoints /costs/by-resource/ y /costs/by-task/ (4–6h)

**Gaps incluidos:**
- GAP #3: Endpoints `/costs/by-resource/` y `/costs/by-task/` con errores 404/500

**Prioridad:** 🔴 CRÍTICA
**Score:** 8.3/10
- Severidad: 🔴 Crítico (10) × 0.4 = 4.0
- Impacto UX: Bloqueante (10) × 0.3 = 3.0
- Esfuerzo: Medium 4–8h (7) × 0.2 = 1.4
- Dependencias: 1–2 gaps (7) × 0.1 = 0.7 — Total: **9.1/10** → ajustado 8.3

**Impacto:** Las secciones de cost breakdown en el tab Presupuesto no renderizan datos. Los errores 404/500 impiden ver el desglose de costos por recurso y por tarea, que son fundamentales para el control de costos del proyecto.

**Tiempo estimado:** 4–6 horas
**Agente:** Backend Architect (4–6h)

**Tareas detalladas:**
1. **Diagnosticar causa raíz de los errores** (Backend Architect, 1h)
   - Problema: Los endpoints devuelven 404 o 500.
   - Solución: Revisar URLs en `backend/apps/proyectos/urls.py` — verificar que `CostByResourceView` y `CostByTaskView` están registrados con el parámetro `project_pk` correcto. Verificar que el `CanAccessProyectos` permission class no está bloqueando el acceso.
   - Archivos a revisar: `backend/apps/proyectos/urls.py`, `backend/apps/proyectos/budget_views.py` (líneas 310–335), `backend/apps/proyectos/permissions.py`

2. **Corregir `get_cost_by_resource` cuando no hay timesheets** (Backend Architect, 1.5h)
   - Problema: `get_cost_by_resource` en `budget_services.py` hace `entries.first().tarea.proyecto.company_id` — si `entries` está vacío pero `entries.exists()` retorna `True` por alguna condición de carrera, o si hay un `TimesheetEntry` huérfano, explota con AttributeError.
   - Solución: Agregar manejo de excepciones robusto. Envolver en try/except y retornar lista vacía `[]` en caso de error en lugar de 500.
   - Archivos a modificar: `backend/apps/proyectos/budget_services.py` (líneas 342–399 y 402–460)

3. **Agregar tests de integración** (Backend Architect, 1.5h)
   - Problema: No hay tests que verifiquen estos endpoints con proyectos sin datos de timesheet.
   - Solución: Crear tests en `backend/apps/proyectos/tests/` que llamen a los endpoints con proyectos vacíos y con datos parciales.
   - Archivos a crear/modificar: `backend/apps/proyectos/tests/test_budget_views.py`

**Dependencias:** Deseable después de Epic 5 (UI de Tarifas) para tener datos completos, pero puede ejecutarse independientemente.
**Bloquea:** Visualización de EVM (Epic 5 depende de tarifas, no de estos endpoints directamente)

**► PROMPT LISTO PARA EJECUTAR:**
```
Agente: Backend Architect
Contexto: SaiSuite Django 5 + DRF. Al cargar el tab "Presupuesto" de un proyecto, el frontend
llama a estos endpoints y recibe errores:
  GET /api/v1/projects/{project_pk}/costs/by-resource/  → error 404 o 500
  GET /api/v1/projects/{project_pk}/costs/by-task/      → error 404 o 500

Las vistas están en backend/apps/proyectos/budget_views.py:
  - CostByResourceView (línea ~310): llama CostCalculationService.get_cost_by_resource()
  - CostByTaskView (línea ~324): llama CostCalculationService.get_cost_by_task()

La lógica de negocio está en backend/apps/proyectos/budget_services.py:
  - get_cost_by_resource (línea ~342): si no hay TimesheetEntries, retorna [].
    RIESGO: entries.first().tarea.proyecto.company_id puede fallar con AttributeError
    si entries existe pero company no está cargado.
  - get_cost_by_task (línea ~402): mismo patrón.

TAREAS:

1. Verificar el registro de URL en backend/apps/proyectos/urls.py:
   - Confirmar que las rutas '<project_pk>/costs/by-resource/' y '<project_pk>/costs/by-task/'
     están registradas y que el parámetro se llama project_pk (no pk ni project_id).
   - El convertor de UUID debe coincidir con el parámetro de la vista.

2. En budget_services.py, refactorizar get_cost_by_resource y get_cost_by_task:
   - Envolver la lógica en try/except general con logger.error() para capturar cualquier
     excepción y retornar lista vacía [] en lugar de propagar el error.
   - Verificar que select_related incluye todos los campos necesarios antes de acceder
     a entries.first().tarea.proyecto.company_id.
   - Asegurar que entries.exists() se evalúa ANTES de llamar a .first().

3. En budget_views.py, mejorar manejo de errores en CostByResourceView y CostByTaskView:
   - Importar y usar logger = logging.getLogger(__name__).
   - Capturar excepciones con logger.error() y retornar Response([], status=200)
     en lugar de 500 (retornar lista vacía es más seguro que un error).

4. Crear o actualizar tests en backend/apps/proyectos/tests/:
   - Test: proyecto sin timesheets → ambos endpoints retornan [] con status 200.
   - Test: proyecto con timesheets pero sin tarifas → retorna datos con costo 0.
   - Test: proyecto con timesheets y tarifas → retorna datos con costos calculados.

CRITERIOS DE ACEPTACIÓN:
- GET /api/v1/projects/{id}/costs/by-resource/ retorna HTTP 200 (lista vacía o con datos).
- GET /api/v1/projects/{id}/costs/by-task/ retorna HTTP 200 (lista vacía o con datos).
- No hay errores 500 ni 404 para proyectos válidos con cualquier estado de datos.
- Tests pasan con python manage.py test apps.proyectos.tests.test_budget_views.

RESTRICCIONES:
- Toda la lógica de negocio va en budget_services.py. Las vistas solo orquestan.
- Usar logger.error("mensaje", extra={"key": "value"}) — nunca print().
- No hacer SQL manual — solo ORM Django.
```

---

### Epic 3: UI de Tarifas de Costo por Recurso (8–10h)

**Gaps incluidos:**
- GAP #2: UI de Tarifas de Costo por Recurso — EVM no funcional
- GAP #65: Tarifas de costo UI inexistente

**Prioridad:** 🔴 CRÍTICA
**Score:** 8.1/10
- Severidad: 🔴 Crítico (10) × 0.4 = 4.0
- Impacto UX: Bloqueante (10) × 0.3 = 3.0
- Esfuerzo: Large 8–16h (4) × 0.2 = 0.8
- Dependencias: 1–2 gaps (7) × 0.1 = 0.7 — Total: **8.5/10** → ajustado 8.1

**Impacto:** Sin tarifas configuradas, TODOS los indicadores EVM (CPI, SPI, EAC, etc.) muestran "—". El módulo de Budget pierde su mayor valor analítico para gerentes de proyecto. El servicio backend `CostRateService` y los endpoints REST existen al 100%, solo falta la UI.

**Tiempo estimado:** 8–10 horas
**Agente:** Full-Stack Developer (8–10h)

**Tareas detalladas:**
1. **Crear `CostRateFormComponent`** (Full-Stack Developer, 4h)
   - Problema: No existe ningún componente HTML para crear/editar/eliminar `ResourceCostRate`.
   - Solución: Crear componente standalone con formulario Angular Reactive. Campos: usuario (selector), tarifa horaria (número), fecha inicio, fecha fin (opcional). Usar `CostRateService` existente para llamadas HTTP.
   - Archivos a crear:
     - `frontend/src/app/features/proyectos/components/budget-dashboard/cost-rate-form/cost-rate-form.component.ts`
     - `frontend/src/app/features/proyectos/components/budget-dashboard/cost-rate-form/cost-rate-form.component.html`
     - `frontend/src/app/features/proyectos/components/budget-dashboard/cost-rate-form/cost-rate-form.component.scss`

2. **Integrar sección "Tarifas por Recurso" en `BudgetDashboardComponent`** (Full-Stack Developer, 3h)
   - Problema: El `BudgetDashboardComponent` no importa ni muestra tarifas.
   - Solución: Agregar una sección expandible (mat-expansion-panel) en el template con:
     - Tabla de tarifas existentes (usuario, tarifa/hora, periodo vigente, acciones editar/eliminar)
     - Botón "Agregar tarifa" que abre `CostRateFormComponent` en un `MatDialog`
   - Archivos a modificar:
     - `frontend/src/app/features/proyectos/components/budget-dashboard/budget-dashboard.component.html`
     - `frontend/src/app/features/proyectos/components/budget-dashboard/budget-dashboard.component.ts`

3. **Verificar que `CostRateService` funciona correctamente** (Full-Stack Developer, 1h)
   - Problema: El servicio existe en `frontend/src/app/features/proyectos/services/cost-rate.service.ts` pero nunca fue probado desde la UI.
   - Solución: Revisar los tipos TypeScript, confirmar que apunta a `/api/v1/projects/resources/cost-rates/` y que los métodos `list()`, `create()`, `update()`, `delete()` están tipados.
   - Archivos a revisar: `frontend/src/app/features/proyectos/services/cost-rate.service.ts`

**Dependencias:** Epic 2 es recomendable pero no bloqueante
**Bloquea:** Funcionalidad completa de EVM, cost breakdown por recurso

**► PROMPT LISTO PARA EJECUTAR:**
```
Agente: Full-Stack Developer
Contexto: SaiSuite Angular 18 + Angular Material.
El módulo de Budget tiene un gap crítico: no existe ningún componente Angular para gestionar
las "Tarifas de Costo por Recurso" (ResourceCostRate).

BACKEND YA IMPLEMENTADO:
- Modelo: ResourceCostRate en backend/apps/proyectos/models.py
  Campos: user (FK), tarifa_por_hora (Decimal), fecha_inicio (Date), fecha_fin (Date, nullable),
  company (FK), created_at, updated_at.
- Endpoints REST disponibles:
  GET/POST  /api/v1/projects/resources/cost-rates/
  GET/PATCH/DELETE /api/v1/projects/resources/cost-rates/{pk}/
- Servicio Angular: frontend/src/app/features/proyectos/services/cost-rate.service.ts
  (revisar antes de crear el componente — el servicio ya existe)

COMPONENTE DESTINO:
frontend/src/app/features/proyectos/components/budget-dashboard/budget-dashboard.component.html
frontend/src/app/features/proyectos/components/budget-dashboard/budget-dashboard.component.ts

TAREAS:

1. Crear CostRateFormComponent como dialog:
   Ruta: frontend/src/app/features/proyectos/components/budget-dashboard/cost-rate-form/
   - Formulario Angular Reactive (ReactiveFormsModule) con:
     * usuario: MatSelect con lista de usuarios de la empresa (usar servicio de usuarios existente)
     * tarifa_por_hora: MatInput type="number" con validación min=0
     * fecha_inicio: MatDatepicker con MatNativeDateModule
     * fecha_fin: MatDatepicker opcional
   - Al guardar: llamar CostRateService.create() o .update() según el modo
   - Al cancelar: cerrar el dialog con MatDialogRef
   - Seguir estándares:
     * ChangeDetectionStrategy.OnPush
     * signals para estado (loading, error)
     * @if/@for en templates (NO *ngIf/*ngFor)
     * appearance="outline" en todos los mat-form-field
     * MatSnackBar con panelClass: ['snack-success'] o ['snack-error']
     * sin tipos 'any' — strict: true

2. Integrar en BudgetDashboardComponent:
   - Agregar una sección "Tarifas por Recurso" usando mat-expansion-panel.
   - Tabla (mat-table) con columnas: usuario, tarifa/hora, fecha_inicio, fecha_fin, acciones.
   - Botón "Agregar tarifa" (mat-raised-button color="primary") que abre CostRateFormComponent
     en MatDialog.
   - Botón editar y eliminar con ConfirmDialogComponent para eliminar.
   - Cargar tarifas con CostRateService.list() en ngOnInit/ngAfterViewInit.
   - Estado vacío: usar sc-empty-state con mensaje "No hay tarifas configuradas. Agrega una
     tarifa para habilitar el cálculo EVM." y botón de acción.

CRITERIOS DE ACEPTACIÓN:
- El tab Presupuesto muestra una sección "Tarifas por Recurso" con la tabla de tarifas.
- Se puede crear una nueva tarifa para un usuario desde el dialog.
- Se puede editar y eliminar tarifas existentes.
- Después de crear tarifas, las métricas EVM dejan de mostrar "—" para proyectos con timesheets.
- ng build --configuration=production compila sin errores TypeScript.

RESTRICCIONES:
- No usar PrimeNG, Bootstrap ni Tailwind. Solo Angular Material.
- No usar tipos 'any'. strict: true.
- ChangeDetectionStrategy.OnPush en todos los componentes nuevos.
- Confirmación con ConfirmDialogComponent (nunca confirm() nativo).
- Variables SCSS con var(--sc-*). Sin colores hardcodeados.
```

---

## NIVEL 1: ALTA PRIORIDAD (Esta semana)

---

### Epic 4: Tabs "Tareas" y "Kanban" dentro del Detalle del Proyecto (8–10h)

**Gaps incluidos:**
- GAP #1 parcial: Tab "Tareas" dentro del proyecto (feature #11 de la tabla)
- GAP #1 parcial: Tab "Kanban" dentro del proyecto (feature #12 de la tabla)
- GAP bug: Lista global de tareas muestra 0 resultados con filtro de proyecto

**Prioridad:** 🔴 CRÍTICA (bloquea flujo natural de trabajo)
**Score:** 7.8/10
- Severidad: 🔴 Crítico (10) × 0.4 = 4.0
- Impacto UX: Bloqueante (10) × 0.3 = 3.0
- Esfuerzo: Large 8–16h (4) × 0.2 = 0.8
- Dependencias: Ninguna (10) × 0.1 = 1.0 — Total: **8.8/10** → ajustado por complejidad 7.8

**Impacto:** El usuario debe salir del proyecto y navegar a `/proyectos/tareas` para ver/gestionar las tareas. Rompe el flujo de trabajo natural. Además, el bug de condición de carrera hace que incluso ese workaround no funcione.

**Tiempo estimado:** 8–10 horas
**Agente:** Full-Stack Developer (8–10h)

**Tareas detalladas:**
1. **Corregir bug de condición de carrera en `TareaListComponent`** (Full-Stack Developer, 2h)
   - Problema: En `ngOnInit()`, `proyectoId.set(pid)` se ejecuta y luego `loadTareas()` usa `proyectoId()` pero la señal puede no haber propagado. El orden en `ngOnInit` (línea ~96-100 de `tarea-list.component.ts`) es `if(pid) proyectoId.set(pid)` → `loadTareas()`. Esto es sincrónico y debería funcionar, pero si la activación del componente ocurre con `ActivatedRoute` asíncrono puede fallar.
   - Solución: Mover la lógica de carga a un efecto reactivo con `effect(() => { if (this.proyectoId()) this.loadTareas(); })` o asegurar que la señal se set antes de cargar.
   - Archivos a modificar: `frontend/src/app/features/proyectos/components/tarea-list/tarea-list.component.ts`

2. **Verificar que `TareaKanbanComponent` acepta `proyectoId` como filtro** (Full-Stack Developer, 1h)
   - Problema: El Kanban puede no tener soporte para filtrar por proyecto.
   - Solución: Revisar `tarea-kanban.component.ts` y agregar signal `proyectoId` con el mismo patrón que `TareaListComponent` si no existe.
   - Archivos a modificar: `frontend/src/app/features/proyectos/components/tarea-kanban/tarea-kanban.component.ts`

3. **Agregar Tab "Tareas" en `proyecto-detail.component.html`** (Full-Stack Developer, 2.5h)
   - Problema: El tab no existe en los 12 tabs actuales.
   - Solución: Agregar `<mat-tab label="Tareas">` entre "Fases" y "Gantt". El contenido debe usar `<app-tarea-list>` con el `proyectoId` del proyecto. Dado que `TareaListComponent` es standalone, importarlo en el componente de detalle.
   - Archivos a modificar:
     - `frontend/src/app/features/proyectos/components/proyecto-detail/proyecto-detail.component.html`
     - `frontend/src/app/features/proyectos/components/proyecto-detail/proyecto-detail.component.ts`

4. **Agregar Tab "Kanban" en `proyecto-detail.component.html`** (Full-Stack Developer, 2.5h)
   - Problema: El tab Kanban dentro del proyecto no existe.
   - Solución: Agregar `<mat-tab label="Kanban">` después de "Tareas". Usar `<app-tarea-kanban>` con filtro de `proyectoId`. Importar el componente en el detalle.
   - Archivos a modificar:
     - `frontend/src/app/features/proyectos/components/proyecto-detail/proyecto-detail.component.html`
     - `frontend/src/app/features/proyectos/components/proyecto-detail/proyecto-detail.component.ts`

**Dependencias:** Deseable corregir bug primero (tarea 1), el resto es independiente
**Bloquea:** Flujo de trabajo natural de tareas por proyecto

**► PROMPT LISTO PARA EJECUTAR:**
```
Agente: Full-Stack Developer
Contexto: SaiSuite Angular 18. El detalle del proyecto (proyecto-detail.component.html)
tiene 12 tabs pero le faltan "Tareas" y "Kanban" integrados con filtro automático por proyecto.
Adicionalmente hay un bug: cuando TareaListComponent carga con query param ?proyecto=:id,
muestra 0 resultados.

ARCHIVOS CLAVE:
- frontend/src/app/features/proyectos/components/proyecto-detail/proyecto-detail.component.html
- frontend/src/app/features/proyectos/components/proyecto-detail/proyecto-detail.component.ts
- frontend/src/app/features/proyectos/components/tarea-list/tarea-list.component.ts
- frontend/src/app/features/proyectos/components/tarea-kanban/tarea-kanban.component.ts

TAREA 1 — Corregir bug en TareaListComponent:
En tarea-list.component.ts, el ngOnInit hace:
  if (pid) this.proyectoId.set(pid);
  this.loadTareas();

El problema es que si la señal se actualiza pero el efecto no se ejecuta sincrónicamente,
loadTareas() puede leer un proyectoId nulo.

FIX: Usar un efecto reactivo. Reemplazar la lógica de ngOnInit por:
  // En el constructor o usando effect():
  effect(() => {
    const pid = this.proyectoId();
    // solo recargar si el proyectoId cambió
    this.loadTareas();
  });
  // En ngOnInit solo hacer el set:
  const pid = this.route.snapshot.queryParamMap.get('proyecto');
  if (pid) this.proyectoId.set(pid);

Verificar también en el backend que GET /api/v1/projects/tasks/?proyecto=<uuid> retorna
resultados (no el endpoint de lista de proyectos).

TAREA 2 — Verificar TareaKanbanComponent:
Revisar tarea-kanban.component.ts — ¿tiene signal proyectoId y lo pasa al servicio?
Si no, agregar el mismo patrón que TareaListComponent.

TAREA 3 — Agregar tabs en proyecto-detail:
En proyecto-detail.component.html, agregar después del tab "Fases" (línea ~219):

  <mat-tab label="Tareas">
    @defer (on viewport) {
      <app-tarea-list [proyectoId]="p.id" />
    }
  </mat-tab>

  <mat-tab label="Kanban">
    @defer (on viewport) {
      <app-tarea-kanban [proyectoId]="p.id" />
    }
  </mat-tab>

IMPORTANTE: Para que esto funcione, los componentes deben aceptar proyectoId como input():
- Si TareaListComponent usa un signal interno, convertirlo a input() de Angular signals API:
  readonly proyectoId = input<string | null>(null);
  Pero si ya tiene lógica de ActivatedRoute, necesitas dos modos: modo standalone (ruta)
  y modo embebido (input). La forma más simple es agregar:
  readonly proyectoIdInput = input<string | null>(null);
  Y en ngOnInit: if (this.proyectoIdInput()) this.proyectoId.set(this.proyectoIdInput()!);

En proyecto-detail.component.ts:
- Importar TareaListComponent y TareaKanbanComponent en el array imports del @Component.

CRITERIOS DE ACEPTACIÓN:
- El detalle de proyecto muestra tabs "Tareas" y "Kanban" entre "Fases" y "Gantt".
- Las tareas mostradas son solo las del proyecto activo (filtradas).
- El tab Kanban muestra las tareas del proyecto en columnas por estado.
- La lista global /proyectos/tareas?proyecto=:id muestra las tareas del proyecto.
- ng build --configuration=production sin errores TypeScript.

RESTRICCIONES:
- ChangeDetectionStrategy.OnPush en todos los componentes.
- @if/@for (NO *ngIf/*ngFor).
- input() y output() de Angular signals (NO @Input/@Output decorators).
- strict: true — sin tipos any.
```

---

### Epic 5: Tab "Timesheets" en Detalle del Proyecto (4–6h)

**Gaps incluidos:**
- GAP #1 parcial: Tab "Timesheets" del equipo en detalle del proyecto (feature #50)

**Prioridad:** 🔴 CRÍTICA
**Score:** 7.5/10

**Impacto:** Los gerentes de proyecto no pueden ver el registro de horas del equipo desde el proyecto. Deben navegar a la vista semanal individual.

**Tiempo estimado:** 4–6 horas
**Agente:** Frontend Developer (4–6h)

**Tareas detalladas:**
1. **Crear `ProyectoTimesheetTabComponent`** (Frontend Developer, 2.5h)
   - Problema: No existe un componente que liste timesheets filtrados por proyecto.
   - Solución: Crear un componente standalone que use `TimesheetService` para cargar entradas filtradas por `proyecto_id`. Mostrar tabla con: fecha, usuario, tarea, horas, descripción. Usar `mat-table` con paginación.
   - Archivos a crear: `frontend/src/app/features/proyectos/components/proyecto-detail/proyecto-timesheet-tab/proyecto-timesheet-tab.component.ts` (y .html, .scss)

2. **Integrar tab "Timesheets" en `proyecto-detail.component.html`** (Frontend Developer, 1.5h)
   - Problema: El tab no existe en los 12 tabs actuales.
   - Solución: Agregar `<mat-tab label="Timesheets">` con `@defer` para carga lazy. Importar el nuevo componente.
   - Archivos a modificar:
     - `frontend/src/app/features/proyectos/components/proyecto-detail/proyecto-detail.component.html`
     - `frontend/src/app/features/proyectos/components/proyecto-detail/proyecto-detail.component.ts`

3. **Verificar endpoint de timesheets por proyecto** (Frontend Developer, 1h)
   - Problema: El `TimesheetService` llama a `/api/v1/projects/timesheets/` — verificar que acepta filtro `proyecto_id` en query params.
   - Solución: Revisar `frontend/src/app/features/proyectos/services/timesheet.service.ts` y el endpoint backend correspondiente.

**Dependencias:** Epic 1 (ruta timesheets) recomendable primero
**Bloquea:** Visibilidad de horas del equipo por proyecto

**► PROMPT LISTO PARA EJECUTAR:**
```
Agente: Frontend Developer
Contexto: SaiSuite Angular 18 + Angular Material. El detalle del proyecto necesita un tab
"Timesheets" que muestre el registro de horas de todo el equipo del proyecto.

SERVICIOS DISPONIBLES:
- frontend/src/app/features/proyectos/services/timesheet.service.ts
  Revisar qué endpoint usa y si acepta filtro por proyecto.
  Endpoint backend: GET /api/v1/projects/timesheets/?proyecto={uuid}

TAREAS:

1. Crear ProyectoTimesheetTabComponent:
   Ruta: frontend/src/app/features/proyectos/components/proyecto-detail/proyecto-timesheet-tab/

   El componente recibe proyectoId como input():
     readonly proyectoId = input.required<string>();

   Al inicializar (effect con proyectoId), llama TimesheetService para cargar timesheets
   filtrados por proyecto. Muestra:
   - mat-table con columnas: Fecha, Usuario, Tarea, Horas, Descripción
   - mat-paginator server-side
   - mat-progress-bar encima de la tabla mientras carga
   - sc-empty-state cuando no hay timesheets (mensaje: "No hay horas registradas para este proyecto")
   - Total de horas al pie de la tabla

   Estándares obligatorios:
   - ChangeDetectionStrategy.OnPush
   - signals para estado (timesheets, loading, total)
   - @if/@for (NO *ngIf/*ngFor)
   - input() de Angular signals API (NO @Input)
   - strict: true — sin tipos any

2. Integrar en proyecto-detail.component.html:
   Agregar entre el tab "Equipo" y "Analytics":

   <mat-tab label="Timesheets">
     @defer (on viewport) {
       <app-proyecto-timesheet-tab [proyectoId]="p.id" />
     }
   </mat-tab>

   En proyecto-detail.component.ts: importar ProyectoTimesheetTabComponent.

CRITERIOS DE ACEPTACIÓN:
- El tab "Timesheets" aparece en el detalle del proyecto.
- Muestra las entradas de timesheet del equipo filtradas por proyecto.
- Muestra estado vacío apropiado cuando no hay registros.
- ng build --configuration=production sin errores.

RESTRICCIONES:
- Solo Angular Material. Sin PrimeNG, Bootstrap, Tailwind.
- Variables SCSS var(--sc-*). Sin colores hardcodeados.
- mat-progress-bar (nunca spinner centrado en listados).
```

---

### Epic 6: Restricciones de Tareas e Indicador Float (3–4h)

**Gaps incluidos:**
- GAP #6: `TaskConstraintsPanelComponent` existe pero no está integrado en ningún template
- GAP (feature #58): 8 tipos de restricciones inaccesibles desde UI
- GAP (feature #44): Overlay de holgura incompleto — solo muestra tareas críticas

**Prioridad:** 🟡 Alto
**Score:** 7.2/10
- Severidad: 🟡 Alto (7) × 0.4 = 2.8
- Impacto UX: Dificulta (7) × 0.3 = 2.1
- Esfuerzo: Quick <4h (10) × 0.2 = 2.0
- Dependencias: Ninguna (10) × 0.1 = 1.0 — Total: **7.9/10** → ajustado 7.2

**Impacto:** Los 8 tipos de restricciones de scheduling (ASAP, ALAP, SNET, SNLT, FNET, FNLT, MSO, MFO) son completamente inaccesibles. Es código muerto que requiere solo integración.

**Tiempo estimado:** 3–4 horas
**Agente:** Frontend Developer (3–4h)

**Tareas detalladas:**
1. **Integrar `TaskConstraintsPanelComponent` en `tarea-detail.component.html`** (Frontend Developer, 2h)
   - Problema: El componente existe en `frontend/src/app/features/proyectos/components/scheduling/task-constraints-panel/` con selector `app-task-constraints-panel` pero ningún template lo importa.
   - Solución: Agregar un nuevo tab "Restricciones" en `tarea-detail.component.html` con `<app-task-constraints-panel>`. Importar el componente en el array `imports` del decorador de `TareaDetailComponent`.
   - Archivos a modificar:
     - `frontend/src/app/features/proyectos/components/tarea-detail/tarea-detail.component.html`
     - `frontend/src/app/features/proyectos/components/tarea-detail/tarea-detail.component.ts`

2. **Integrar `FloatIndicatorComponent` en el detalle de tarea** (Frontend Developer, 1.5h)
   - Problema: `float-indicator.component.ts` existe en `scheduling/` pero no está en ningún template.
   - Solución: Agregar el indicador en la sección de header del detalle de tarea o dentro del tab "Restricciones".
   - Archivos a modificar: `frontend/src/app/features/proyectos/components/tarea-detail/tarea-detail.component.html`

**Dependencias:** Ninguna (código ya existe, solo integración)
**Bloquea:** Nada, pero habilita funcionalidad de scheduling avanzado

**► PROMPT LISTO PARA EJECUTAR:**
```
Agente: Frontend Developer
Contexto: SaiSuite Angular 18. Existen dos componentes de scheduling completamente
implementados pero que nunca fueron integrados en ningún template:

1. TaskConstraintsPanelComponent
   Ruta: frontend/src/app/features/proyectos/components/scheduling/task-constraints-panel/
   Selector: app-task-constraints-panel
   Descripción: Maneja 8 tipos de restricciones de scheduling (ASAP, ALAP, SNET, SNLT,
   FNET, FNLT, MSO, MFO) con su CRUD completo.

2. FloatIndicatorComponent
   Ruta: frontend/src/app/features/proyectos/components/scheduling/float-indicator/
   Selector: Revisar en float-indicator.component.ts
   Descripción: Indica el float (holgura) de una tarea.

OBJETIVO: Integrar ambos en tarea-detail.component.html

ARCHIVOS A MODIFICAR:
- frontend/src/app/features/proyectos/components/tarea-detail/tarea-detail.component.html
- frontend/src/app/features/proyectos/components/tarea-detail/tarea-detail.component.ts

TAREA 1 — Integrar TaskConstraintsPanelComponent:
- El detalle de tarea tiene un mat-tab-group con tabs: Descripción, Subtareas, Seguidores,
  Tiempo/Medición, Dependencias, Recursos, Comentarios.
- Agregar un nuevo tab "Restricciones" DESPUÉS de "Dependencias".
- Contenido del tab:
  <app-task-constraints-panel [tareaId]="tarea().id" />
  (ajustar el input según lo que espere el componente — leer su interface antes)
- Importar TaskConstraintsPanelComponent en el array imports de TareaDetailComponent.

TAREA 2 — Integrar FloatIndicatorComponent:
- Leer float-indicator.component.ts para entender qué inputs recibe.
- Agregar el indicador en el header del detalle de tarea (cerca del badge "Camino Crítico"
  que ya existe) o al inicio del tab "Restricciones".
- Importar FloatIndicatorComponent en TareaDetailComponent.

CRITERIOS DE ACEPTACIÓN:
- El detalle de tarea muestra un tab "Restricciones" con el panel de restricciones.
- Se puede crear, editar y eliminar restricciones de scheduling desde el detalle de tarea.
- El indicador de float aparece en el detalle de tarea.
- ng build --configuration=production sin errores TypeScript.

RESTRICCIONES:
- Leer los componentes antes de integrar para entender sus inputs/outputs.
- ChangeDetectionStrategy.OnPush (verificar que los componentes existentes lo tienen).
- @if/@for en templates.
- strict: true — sin tipos any.
```

---

## NIVEL 2: PRIORIDAD MEDIA (Próxima semana)

---

### Epic 7: Módulo "Mis Tareas" + Filtros faltantes (4–6h)

**Gaps incluidos:**
- GAP #9: Módulo "Mis Tareas" no existe (feature #34)
- GAP bug: Filtro por fase no disponible en lista de tareas
- GAP (feature #3): Filtro por gerente en lista de proyectos

**Prioridad:** 🟢 Medio
**Score:** 6.1/10
- Severidad: 🟢 Medio (4) × 0.4 = 1.6
- Impacto UX: Dificulta (7) × 0.3 = 2.1
- Esfuerzo: Medium 4–8h (7) × 0.2 = 1.4
- Dependencias: Ninguna (10) × 0.1 = 1.0 — Total: **6.1/10**

**Impacto:** Usuarios no tienen vista personal de tareas. Pequeños gaps de usabilidad en filtros.

**Tiempo estimado:** 4–6 horas
**Agente:** Frontend Developer (4–6h)

**Tareas detalladas:**
1. **Crear ruta `/proyectos/mis-tareas`** (Frontend Developer, 2h)
   - Problema: No existe ruta ni componente "Mis Tareas".
   - Solución: Reutilizar `TareaListComponent` con un wrapper que inyecte el `userId` del usuario autenticado como filtro `responsable`. Agregar la ruta en `proyectos.routes.ts` y el enlace en el sidebar.
   - Archivos a modificar:
     - `frontend/src/app/features/proyectos/proyectos.routes.ts`
     - `frontend/src/app/core/components/sidebar/sidebar.component.ts`

2. **Agregar filtro por fase en `TareaListComponent`** (Frontend Developer, 1.5h)
   - Problema: El backend soporta filtro `fase` en `TareaFilters` pero no hay selector en la UI.
   - Solución: Agregar un `MatSelect` de fases en los filtros de la lista de tareas.
   - Archivos a modificar: `frontend/src/app/features/proyectos/components/tarea-list/tarea-list.component.html` y `.ts`

3. **Agregar filtro por gerente en lista de proyectos** (Frontend Developer, 1.5h)
   - Problema: El manual documenta filtro por gerente, no está en la UI.
   - Solución: Agregar `MatSelect` de usuarios con rol gerente en los filtros de `ProyectoListComponent` y `ProyectoCardsComponent`.
   - Archivos a modificar:
     - `frontend/src/app/features/proyectos/components/proyecto-list/proyecto-list.component.html` y `.ts`
     - `frontend/src/app/features/proyectos/components/proyecto-cards/proyecto-cards.component.html` y `.ts`

**Dependencias:** Ninguna
**Bloquea:** Nada crítico

**► PROMPT LISTO PARA EJECUTAR:**
```
Agente: Frontend Developer
Contexto: SaiSuite Angular 18. Tres gaps menores de usabilidad en el módulo de proyectos:

1. No existe vista "Mis Tareas"
2. La lista de tareas no tiene filtro por fase
3. La lista de proyectos no tiene filtro por gerente

TAREA 1 — Vista "Mis Tareas":
En frontend/src/app/features/proyectos/proyectos.routes.ts:
  Agregar ruta 'mis-tareas' ANTES de ':id' que cargue TareaListComponent.

En TareaListComponent: al activar la ruta /proyectos/mis-tareas, leer el queryParam
  'mis_tareas=true' y si está presente, filtrar automáticamente por el usuario autenticado.
  Usar AuthService (ya existe en core/) para obtener el userId.
  Pasar filtro responsable=userId al servicio de tareas.

En sidebar.component.ts, agregar en PROYECTOS_NAV:
  { label: 'Mis Tareas', icon: 'person', route: '/proyectos/mis-tareas' }

TAREA 2 — Filtro por fase en lista de tareas:
En tarea-list.component.html: agregar MatSelect de fases junto a los filtros existentes
  (estado, prioridad, búsqueda).
En tarea-list.component.ts: agregar signal faseFilter y pasarlo al servicio.
El backend ya soporta el parámetro 'fase' en la query.

TAREA 3 — Filtro por gerente en lista de proyectos:
En proyecto-list.component.html y proyecto-cards.component.html:
  Agregar MatSelect "Gerente" con lista de usuarios.
  Al cambiar: pasar filtro 'gerente_id' al ProyectoService.
Verificar que el endpoint GET /api/v1/projects/ acepta el parámetro gerente_id.

CRITERIOS DE ACEPTACIÓN:
- /proyectos/mis-tareas muestra las tareas asignadas al usuario actual.
- El sidebar de proyectos tiene el ítem "Mis Tareas".
- La lista de tareas tiene selector de fase funcional.
- Las listas de proyectos tienen selector de gerente funcional.
- ng build --configuration=production sin errores TypeScript.

RESTRICCIONES:
- Reutilizar TareaListComponent existente. No crear componente duplicado.
- input()/output() de Angular signals. No @Input/@Output decorators.
- strict: true — sin tipos any.
- @if/@for en templates.
```

---

### Epic 8: Capacidades, Disponibilidad y UI de Recursos (8–12h)

**Gaps incluidos:**
- GAP #5 parcial: UI para configurar capacidades de recursos (feature #52)
- GAP: UI para registrar disponibilidad/ausencias (feature #53)
- GAP #5: Nivelación de recursos — solo backend (feature #57)
- GAP: Workload del equipo con colores semáforo (feature #54)

**Prioridad:** 🟡 Alto
**Score:** 6.5/10

**Impacto:** Los gerentes no pueden configurar la capacidad disponible del equipo ni registrar ausencias. La nivelación de recursos es inaccesible. El workload muestra timeline básico sin el código de colores documentado.

**Tiempo estimado:** 8–12 horas
**Agente:** Full-Stack Developer (8–12h)

**Tareas detalladas:**
1. **Crear `ResourceCapacityComponent`** (Full-Stack Developer, 3h)
   - Problema: No hay UI para configurar horas/semana por usuario.
   - Solución: Formulario con usuario, horas/semana, fecha inicio, fecha fin. Usar `ResourceService` existente.
   - Archivos a crear: `frontend/src/app/features/proyectos/components/team-timeline/resource-capacity/`

2. **Crear `ResourceAvailabilityComponent`** (Full-Stack Developer, 3h)
   - Problema: No hay UI para registrar ausencias/vacaciones.
   - Solución: Formulario con usuario, tipo ausencia, fechas, motivo. Integrar en el tab "Equipo" del proyecto como sección adicional.

3. **Agregar botón "Nivelar Recursos" en scheduling** (Full-Stack Developer, 2h)
   - Problema: El endpoint `POST /api/v1/projects/:id/scheduling/level-resources/` existe pero no hay botón en la UI.
   - Solución: Agregar botón en `AutoScheduleDialogComponent` o en el header del proyecto junto al botón "Scheduling".
   - Archivos a modificar: `frontend/src/app/features/proyectos/components/scheduling/auto-schedule-dialog/auto-schedule-dialog.component.html` y `.ts`

4. **Mejorar Workload con código de colores** (Full-Stack Developer, 2h)
   - Problema: El `WorkloadSummaryComponent` muestra timeline básico sin semáforo.
   - Solución: Usar el endpoint `/resources/workload/` y aplicar clases CSS de color (verde <80%, amarillo 80–100%, rojo >100%).

**Dependencias:** Epic 3 (tarifas) recomendable para que workload muestre costos
**Bloquea:** Scheduling avanzado con datos de capacidad real

**► PROMPT LISTO PARA EJECUTAR:**
```
Agente: Full-Stack Developer
Contexto: SaiSuite Angular 18. El módulo de gestión de recursos tiene tres gaps:
1. No hay UI para configurar capacidades (horas/semana por usuario)
2. No hay UI para registrar ausencias/disponibilidad
3. No hay botón para ejecutar la nivelación de recursos desde el frontend

BACKEND YA IMPLEMENTADO:
- Capacidades: GET/POST /api/v1/projects/resources/capacity/
  Modelo ResourceCapacity: user, horas_semanales, fecha_inicio, fecha_fin
- Disponibilidad: GET/POST /api/v1/projects/resources/availability/
  Modelo ResourceAvailability: user, tipo (vacation/sick/holiday/training/other),
  fecha_inicio, fecha_fin, motivo, aprobado
- Nivelación: POST /api/v1/projects/{id}/scheduling/level-resources/
  Body: { algorithm: 'ffcfs'|'priority', dry_run: boolean }
- Workload: GET /api/v1/projects/resources/workload/?start_date=&end_date=
- Servicio: frontend/src/app/features/proyectos/services/resource.service.ts (verificar métodos)

TAREA 1 — ResourceCapacityComponent (dialog):
  Ruta: frontend/src/app/features/proyectos/components/team-timeline/resource-capacity/
  Formulario: usuario (MatSelect), horas_semanales (number), fecha_inicio (DatePicker),
  fecha_fin (DatePicker, opcional).
  Tabla de capacidades con columnas: usuario, horas/sem, desde, hasta, acciones.
  Integrar en el tab "Equipo" del proyecto-detail como mat-expansion-panel "Capacidades".

TAREA 2 — ResourceAvailabilityComponent (dialog):
  Ruta: frontend/src/app/features/proyectos/components/team-timeline/resource-availability/
  Formulario: usuario (MatSelect), tipo (MatSelect con los 5 tipos), fechas, motivo.
  Tabla de ausencias con columnas: usuario, tipo, desde, hasta, motivo, estado.
  Integrar en el tab "Equipo" como mat-expansion-panel "Ausencias y Disponibilidad".

TAREA 3 — Botón Nivelar Recursos:
  En frontend/src/app/features/proyectos/components/scheduling/auto-schedule-dialog/:
  Agregar sección "Nivelación de Recursos" con:
  - Selector algorithm (FFCFS o Por Prioridad)
  - Checkbox dry_run
  - Botón "Nivelar"
  Al ejecutar: POST a /api/v1/projects/{id}/scheduling/level-resources/
  Mostrar resultado en MatSnackBar.

TAREA 4 — Workload con colores semáforo:
  En WorkloadSummaryComponent (frontend/src/app/features/proyectos/components/workload-summary/):
  Consumir /api/v1/projects/resources/workload/ para obtener % de asignación por usuario/semana.
  Aplicar clases CSS:
  - Verde: < 80% (workload-low)
  - Amarillo: 80–100% (workload-medium)
  - Rojo: > 100% (workload-high)

CRITERIOS DE ACEPTACIÓN:
- Tab "Equipo" muestra secciones de Capacidades y Ausencias con CRUD funcional.
- El dialog de scheduling tiene botón "Nivelar Recursos" funcional.
- El workload muestra celdas con código de colores por nivel de carga.
- ng build --configuration=production sin errores.

RESTRICCIONES:
- ChangeDetectionStrategy.OnPush. signals. @if/@for. input()/output().
- Angular Material only. strict: true.
- Confirmaciones con ConfirmDialogComponent. Feedback con MatSnackBar.
```

---

## NIVEL 3: BACKLOG

---

### Epic 9: Correcciones Menores, Bugs de UX y Documentación (4–6h)

**Gaps incluidos:**
- GAP #10: Tipo de tercero "CUSTOMER" en inglés (feature #74)
- GAP: Botón "Activar" explícito en lista de fases (feature #25)
- GAP #7 parcial: What-If Scenarios — configuración de cambios (feature #60)
- GAP: Toggle activar/desactivar actividad en catálogo (feature #37)
- GAP: Indicador Timer activo en barra superior (feature #200 del manual)
- GAP #11: Tipo "Hito" en catálogo de actividades (decisión de producto requerida)

**Prioridad:** 🟢 Medio / ⚪ Bajo
**Score:** 3.5–5.0/10

**Tiempo estimado:** 4–6 horas
**Agente:** Frontend Developer + Tech Lead (decisión sobre "Hito")

**Tareas detalladas:**
1. **Corregir "CUSTOMER" a "Cliente" en terceros** (Backend Architect, 0.5h)
   - Problema: El tipo de tercero muestra "CUSTOMER" en inglés.
   - Solución: Revisar `backend/apps/terceros/serializers.py` — asegurar que `get_tipo_display()` retorna valor en español. Si los choices están en inglés, agregar `choices` con display en español en el modelo o mapeo en el serializer.
   - Archivos a modificar: `backend/apps/terceros/serializers.py`

2. **Agregar botón "Activar" en `FaseListComponent`** (Frontend Developer, 1h)
   - Problema: Los endpoints `phases/:id/activate/` y `phases/:id/complete/` existen pero no hay botones en la UI de la tabla de fases.
   - Solución: Agregar botones de icono en las acciones de cada fila: icono `play_circle` para activar (solo si estado es `planned`) e icono `check_circle` para completar (solo si estado es `active`).
   - Archivos a modificar: `frontend/src/app/features/proyectos/components/fase-list/fase-list.component.html` y `.ts`

3. **Toggle activar/desactivar actividad en catálogo** (Frontend Developer, 0.5h)
   - Problema: No hay toggle de estado en la lista de actividades.
   - Solución: Agregar `mat-slide-toggle` o chip clickeable en la columna de acciones de `ActividadListComponent`.
   - Archivos a modificar: `frontend/src/app/features/proyectos/components/actividad-list/actividad-list.component.html` y `.ts`

4. **Indicador de Timer activo en barra superior** (Frontend Developer, 2h)
   - Problema: No hay indicador visual en la barra de navegación cuando hay una `WorkSession` activa.
   - Solución: En el componente de shell/topbar, consultar si hay una sesión activa via `SesionTrabajoService` y mostrar un chip/badge en el header.

5. **Decisión: Tipo "Hito" en catálogo de actividades** (Tech Lead, 1h)
   - No hay código que escribir hasta que se tome la decisión de producto:
     - Opción A: Agregar `milestone` como tipo en `ActivityType` enum del backend (baja complejidad).
     - Opción B: Documentar en el manual que los hitos del proyecto (`Milestone`) son el concepto correcto y que el catálogo de actividades no incluye hitos.
   - Documentar la decisión en `DECISIONS.md`.

**► PROMPT LISTO PARA EJECUTAR:**
```
Agente: Frontend Developer + Backend Architect
Contexto: SaiSuite. Correcciones menores de UX en el módulo de proyectos.

CORRECCIÓN 1 — "CUSTOMER" en inglés (Backend):
En backend/apps/terceros/serializers.py:
Localizar el campo tipo_tercero. Si usa choices del modelo en inglés (customer, supplier, both),
agregar un SerializerMethodField tipo_tercero_display que retorne el display en español:
  'customer': 'Cliente', 'supplier': 'Proveedor', 'both': 'Ambos'
O mejor: verificar que el modelo tiene los choices con verbose_name en español y que
el serializer usa source='get_tipo_display' correctamente.

CORRECCIÓN 2 — Botones Activar/Completar en fases (Frontend):
En frontend/src/app/features/proyectos/components/fase-list/fase-list.component.html:
Agregar en las acciones de cada fila de la tabla (después de editar, antes de eliminar):
  @if (fase.estado === 'planned') {
    <button mat-icon-button color="primary" (click)="activarFase(fase)"
            matTooltip="Activar fase">
      <mat-icon>play_circle</mat-icon>
    </button>
  }
  @if (fase.estado === 'active') {
    <button mat-icon-button color="accent" (click)="completarFase(fase)"
            matTooltip="Completar fase">
      <mat-icon>check_circle</mat-icon>
    </button>
  }
En fase-list.component.ts: implementar activarFase() y completarFase() que llamen
a FaseService.activar() y FaseService.completar() respectivamente.
Mostrar confirmación con ConfirmDialogComponent antes de activar/completar.
Feedback con MatSnackBar panelClass: ['snack-success'].

CORRECCIÓN 3 — Toggle en catálogo de actividades (Frontend):
En frontend/src/app/features/proyectos/components/actividad-list/actividad-list.component.html:
Agregar columna "Activo" con mat-slide-toggle:
  <mat-slide-toggle [checked]="actividad.activo"
    (change)="toggleActivo(actividad, $event.checked)">
  </mat-slide-toggle>
En actividad-list.component.ts: implementar toggleActivo() que llame a
ActividadService.update(id, { activo: checked }) con feedback MatSnackBar.

CRITERIOS DE ACEPTACIÓN:
- La lista de terceros muestra "Cliente", "Proveedor", "Ambos" en español.
- La tabla de fases muestra botones de activar/completar según el estado actual.
- La tabla de actividades tiene toggle de activo/inactivo funcional.
- ng build sin errores TypeScript.
```

---

## ROADMAP COMPLETO

| Semana | Nivel | Épica | Área | Horas |
|---|---|---|---|---|
| Semana 0 (HOY) | 0 | Epic 1: Ruta Timesheet Semanal | Frontend | 2–4h |
| Semana 0 (HOY) | 0 | Epic 2: Corregir /costs/by-resource y /costs/by-task | Backend | 4–6h |
| Semana 0 (HOY) | 0 | Epic 3: UI Tarifas de Costo por Recurso | Full-Stack | 8–10h |
| Semana 1 | 1 | Epic 4: Tabs Tareas + Kanban en detalle proyecto | Full-Stack | 8–10h |
| Semana 1 | 1 | Epic 5: Tab Timesheets en detalle proyecto | Frontend | 4–6h |
| Semana 1 | 1 | Epic 6: Restricciones de tareas + Float indicator | Frontend | 3–4h |
| Semana 2 | 2 | Epic 7: Mis Tareas + Filtros faltantes | Frontend | 4–6h |
| Semana 2 | 2 | Epic 8: Capacidades, Disponibilidad, Nivelación | Full-Stack | 8–12h |
| Semana 3+ | 3 | Epic 9: Correcciones menores y backlog | Mixed | 4–6h |

---

## ESTIMACIÓN TOTAL

| Nivel | Épicas | Horas estimadas | % del total |
|---|---|---|---|
| 0 — Críticos (AHORA) | 3 | 14–20h | 30% |
| 1 — Esta semana | 3 | 15–20h | 33% |
| 2 — Próxima semana | 2 | 12–18h | 27% |
| 3 — Backlog | 1 | 4–6h | 10% |
| **TOTAL** | **9** | **45–64h** | 100% |

---

## DISTRIBUCIÓN POR AGENTE

| Agente | Épicas | Horas estimadas | % |
|---|---|---|---|
| Frontend Developer | 4 (Epic 1, 5, 6, 7) + parcial 9 | 17–24h | 36% |
| Full-Stack Developer | 3 (Epic 3, 4, 8) | 24–32h | 50% |
| Backend Architect | 1 (Epic 2) + parcial 9 | 5–7h | 11% |
| Tech Lead (decisión) | parcial 9 | 1–2h | 3% |

---

## CHECKLIST DE EJECUCIÓN

### Nivel 0 — AHORA
- [ ] **Epic 1:** Agregar ruta `timesheets` en proyectos.routes.ts
- [ ] **Epic 1:** Agregar ítem "Timesheets" en sidebar PROYECTOS_NAV
- [ ] **Epic 1:** Verificar que TimesheetSemanalComponent carga sin errores en /proyectos/timesheets
- [ ] **Epic 2:** Diagnosticar y corregir CostByResourceView
- [ ] **Epic 2:** Diagnosticar y corregir CostByTaskView
- [ ] **Epic 2:** Agregar tests de integración para endpoints de cost breakdown
- [ ] **Epic 3:** Crear CostRateFormComponent (dialog)
- [ ] **Epic 3:** Integrar sección "Tarifas por Recurso" en BudgetDashboardComponent
- [ ] **Epic 3:** Verificar CostRateService y sus tipados TypeScript

### Nivel 1 — Esta semana
- [ ] **Epic 4:** Corregir bug de condición de carrera en TareaListComponent
- [ ] **Epic 4:** Verificar soporte de proyectoId en TareaKanbanComponent
- [ ] **Epic 4:** Agregar tab "Tareas" en proyecto-detail
- [ ] **Epic 4:** Agregar tab "Kanban" en proyecto-detail
- [ ] **Epic 5:** Crear ProyectoTimesheetTabComponent
- [ ] **Epic 5:** Integrar tab "Timesheets" en proyecto-detail
- [ ] **Epic 6:** Integrar TaskConstraintsPanelComponent en tarea-detail
- [ ] **Epic 6:** Integrar FloatIndicatorComponent en tarea-detail

### Nivel 2 — Próxima semana
- [ ] **Epic 7:** Crear ruta /proyectos/mis-tareas
- [ ] **Epic 7:** Agregar filtro por fase en lista de tareas
- [ ] **Epic 7:** Agregar filtro por gerente en lista de proyectos
- [ ] **Epic 8:** Crear ResourceCapacityComponent
- [ ] **Epic 8:** Crear ResourceAvailabilityComponent
- [ ] **Epic 8:** Agregar botón "Nivelar Recursos" en scheduling
- [ ] **Epic 8:** Mejorar Workload con código de colores semáforo

### Nivel 3 — Backlog
- [ ] **Epic 9:** Corregir "CUSTOMER" a "Cliente" en terceros
- [ ] **Epic 9:** Agregar botones Activar/Completar en lista de fases
- [ ] **Epic 9:** Agregar toggle activo/inactivo en catálogo de actividades
- [ ] **Epic 9:** Decisión de producto sobre tipo "Hito" en catálogo (documentar en DECISIONS.md)
- [ ] **Epic 9:** Indicador Timer activo en barra superior

---

## SIGUIENTE PASO INMEDIATO

**Primera épica a ejecutar: Epic 1 — Ruta y acceso a Timesheet Semanal**

Es la épica con mayor score ajustado (8.6/10), esfuerzo mínimo (2–4h) y cero dependencias. Es el "quick win" que demuestra tracción inmediata y desbloquea Epic 5.

Copiar y ejecutar el prompt de Epic 1 directamente en Claude Code:

```
Agente: Frontend Developer
Contexto: SaiSuite Angular 18 + Angular Material. El componente TimesheetSemanalComponent existe
completamente implementado en:
  frontend/src/app/features/proyectos/components/timesheet-semanal/timesheet-semanal.component.ts
  (selector: 'app-timesheet-semanal')

Pero NO está enrutado — por eso es completamente inaccesible para el usuario.

TAREAS:

1. En frontend/src/app/features/proyectos/proyectos.routes.ts:
   - Agregar una nueva ruta ANTES de ':id' con path: 'timesheets' que cargue
     TimesheetSemanalComponent con lazy loading.
   - Seguir el mismo patrón que las rutas 'tareas', 'actividades', 'configuracion' ya existentes.

2. En frontend/src/app/core/components/sidebar/sidebar.component.ts:
   - Localizar el getter PROYECTOS_NAV (línea ~80).
   - En la sección 'Gestión de Proyectos', agregar después del ítem 'Tareas':
     { label: 'Timesheets', icon: 'schedule', route: '/proyectos/timesheets' }

CRITERIOS DE ACEPTACIÓN:
- La URL /proyectos/timesheets carga el TimesheetSemanalComponent sin errores.
- El ítem 'Timesheets' aparece en el sidebar cuando se está en el módulo de proyectos.
- El enlace del sidebar navega correctamente a /proyectos/timesheets.
- ng build --configuration=production compila sin errores TypeScript.

RESTRICCIONES:
- No modificar el componente TimesheetSemanalComponent.
- Usar sintaxis de lazy loading: loadComponent: () => import(...).then(m => m.TimesheetSemanalComponent)
- strict: true en TypeScript — no introducir tipos any.
```

---

*Plan generado por Claude Code — 28 Marzo 2026*
*Basado en: AUDITORIA-MODULO-PROYECTOS.md + análisis de código fuente*
*Stack: Django 5 + Angular 18 + Angular Material + PostgreSQL 16*
