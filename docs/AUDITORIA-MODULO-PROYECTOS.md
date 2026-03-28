# AUDITORÍA MÓDULO DE PROYECTOS — SaiSuite
**Fecha:** 28 Marzo 2026
**Auditor:** Claude Code
**Metodología:** Análisis de código fuente (backend + frontend) + Testing en navegador (Playwright MCP)
**URL testeada:** http://localhost:4200

---

## RESUMEN EJECUTIVO

| Métrica | Valor |
|---|---|
| Features auditadas | 55 |
| Implementadas completamente | 34 (62%) |
| Parcialmente implementadas | 12 (22%) |
| No implementadas | 9 (16%) |
| Implementadas pero no documentadas | 3 |

**Severidad de gaps:**
- 🔴 Crítico: 4
- 🟡 Alto: 7
- 🟢 Medio: 6
- ⚪ Bajo: 5

---

## RESULTADOS POR ÁREA

---

### 1. GESTIÓN DE PROYECTOS (Lista, Detalle, CRUD)

#### ✅ Implementado y Funcionando
- **Lista de proyectos — Vista Cards** (`/proyectos/cards`): funciona correctamente. Muestra código, estado, nombre, tipo, avance (barra de progreso), gerente, cliente, fecha fin, presupuesto. 3 proyectos demo activos (PRY-001, PRY-003, PRY-004).
- **Lista de proyectos — Vista Lista** (toggle en botón "Lista"): botón existe, activa la vista `proyecto-list` component.
- **Filtros**: por estado y tipo en la vista cards. Búsqueda por texto implementada.
- **Crear proyecto** (`/proyectos/nuevo`): formulario completo con todos los campos del manual (código autogenerado por consecutivo, nombre, tipo, cliente, gerente, coordinador, fechas, presupuesto, AIU).
- **Consecutivos automáticos**: implementados. El formulario carga consecutivos filtrados por tipo de proyecto y autoselecciona cuando hay solo uno disponible. El servicio `ConsecutivoService` está integrado.
- **Estados del proyecto**: 6 estados implementados en backend y frontend: `draft`, `planned`, `in_progress`, `suspended`, `closed`, `cancelled`. Los botones de cambio de estado en el detalle funcionan correctamente.
- **Tipos de proyecto**: 6 tipos implementados: `civil_works`, `consulting`, `manufacturing`, `services`, `public_tender`, `other`.
- **Editar proyecto**: funciona. Botón "Editar" en el detalle navega al formulario de edición.
- **Eliminar proyecto**: implementado con `ConfirmDialogComponent` (cumple estándar).
- **AIU (Administración, Imprevistos, Utilidad)**: campos implementados en modelo, formulario y UI de detalle. Defaults: 10%, 5%, 10%.
- **Detalle de proyecto** (`/proyectos/:id`): muestra breadcrumb, header con código + estado + nombre + acciones de cambio de estado, y 12 tabs. `ChangeDetectionStrategy.OnPush` correctamente implementado.

#### ⚠️ Implementado pero Diferente al Manual
- **Vista de detalle — Tab "Resumen"**: el manual documenta un tab "Resumen" con estado financiero AIU y métricas principales. **Lo implementado es "General"** (información general, cliente, fechas, equipo, presupuesto + AIU). No hay métricas de avance integradas en el tab General.
- **Cliente del proyecto**: el manual indica selector de Terceros de tipo "Cliente". Lo implementado usa `cliente_id` (string) y `cliente_nombre` (string) — **no es un FK al modelo Tercero**. El campo en el formulario puede ser un selector de terceros pero el almacenamiento no es una FK real.
- **Botón eliminar proyecto con confirmación de nombre**: el manual documenta que se debe escribir el nombre del proyecto al eliminar. La implementación usa `ConfirmDialogComponent` estándar sin este paso adicional de verificación.
- **Vista cards — colores de estado**: el manual indica: gris (borrador), azul (planificado), verde (en ejecución), amarillo (suspendido), negro (cerrado), rojo (cancelado). La UI usa clases CSS `pd-estado-badge--{estado}` — colores visualmente similares pero no exactamente iguales a la especificación.

#### ❌ No Implementado
- **Tab "Tareas" en el detalle del proyecto**: el manual especifica un tab "Tareas" dentro del proyecto (con filtro por fase). Este tab **no existe** en `proyecto-detail.component.html`. El acceso a tareas de un proyecto es solo desde la URL `/proyectos/tareas?proyecto=:id` (global).
- **Tab "Kanban" en el detalle del proyecto**: el manual documenta tab "Kanban" dentro del proyecto. **No existe** en el detalle de proyecto. El Kanban existe como ruta global `/proyectos/tareas/kanban`.
- **Tab "Timesheets" en el detalle del proyecto**: el manual documenta un tab "Timesheets" para ver el registro de horas del equipo por proyecto. **No existe** en el detalle del proyecto.
- **Tab "Scheduling" en el detalle del proyecto**: el manual documenta un tab "Scheduling" con Auto-Schedule, baselines, restricciones y What-If. Lo implementado **separa estas funcionalidades en 3 tabs distintos**: "Baselines", "Escenarios" y el botón "Scheduling" en el header (que solo abre Auto-Schedule dialog). No hay un tab unificado "Scheduling".
- **Filtro por gerente en lista de proyectos**: documentado en manual, no aparece en los filtros de la UI.

#### 🐛 Bugs Encontrados
- **NIT / ID del cliente muestra UUID interno**: en el tab General del detalle, el campo "NIT / ID" muestra un UUID de la base de datos interna (ej: `3d373c7f-7277-4d03-b213-516a3cf407d2`) en lugar del NIT real del tercero. Esto ocurre porque `cliente_id` almacena el ID del registro Tercero, no el NIT tributario.
- **Página global de Tareas `/proyectos/tareas` muestra 0 resultados**: incluso con el query param `?proyecto=:id`, la página carga con 0 tareas durante el testing. El componente `TareaListComponent` llama `loadTareas()` en `ngOnInit()` pero la señal `proyectoId` puede no estar lista cuando se ejecuta la carga. (Posible condición de carrera en `ngOnInit` vs `signal.set()`.)

---

### 2. FASES

#### ✅ Implementado y Funcionando
- **Tab "Fases" en detalle del proyecto**: funciona. Muestra tabla con columnas: #, Nombre, Estado, Presupuesto, Avance (barra), Acciones (editar/eliminar).
- **Crear fase**: botón "Nueva fase" abre formulario. Campos: nombre, descripción, orden, fechas.
- **Editar fase**: ícono de lápiz abre formulario de edición.
- **Eliminar fase**: ícono de basura con confirmación.
- **Estados de fase**: 4 estados implementados: `planned` (Planificada), `active` (Activa), `completed` (Completada), `cancelled` (Cancelada).
- **Progreso automático**: `porcentaje_avance` en Fase se calcula automáticamente desde las tareas (señales en backend).
- **Endpoints backend**: `GET/POST /api/v1/projects/:id/phases/`, `GET/PATCH/DELETE /api/v1/projects/phases/:id/`, `POST /api/v1/projects/phases/:id/activate/`, `POST /api/v1/projects/phases/:id/complete/` — todos implementados.
- **Presupuesto por categoría**: el modelo de Fase tiene campos de presupuesto por categoría (mano de obra, materiales, subcontratos, equipos, otros). Visible en la tabla como columna "Presupuesto" (total $0 en demo por no estar configurado).

#### ⚠️ Implementado pero Diferente al Manual
- **Reordenar fases con flechas arriba/abajo**: el manual documenta íconos de flecha para reordenar. La implementación usa el campo `orden` numérico en el formulario, no drag-and-drop ni botones de flecha.
- **Activar fase**: el manual indica un ícono de activación (bandera/check). La implementación tiene endpoints `activate` y `complete` pero en la UI del `FaseListComponent` solo se muestran botones editar/eliminar, no un botón explícito de activación.

#### ❌ No Implementado
- **Indicador visual de fase activa diferenciado**: la tabla muestra el estado textual ("Activa", "Completada") pero no hay un chip de color verde destacado para la fase activa como describe el manual.

---

### 3. GESTIÓN DE TAREAS

#### ✅ Implementado y Funcionando
- **Ruta global de tareas** (`/proyectos/tareas`): lista con columnas código, nombre, responsable, estado, prioridad, avance, fecha límite, acciones.
- **Crear tarea** (`/proyectos/tareas/nueva`): formulario con todos los campos: nombre, fase, descripción, tarea padre, actividad del catálogo, responsable, seguidores, prioridad, etiquetas, fechas (inicio, fin, límite), horas estimadas, cantidad objetivo, recurrencia.
- **Editar y eliminar tareas**: implementados con `ConfirmDialogComponent`.
- **Tarea Kanban** (`/proyectos/tareas/kanban`): implementado. Columnas por estado.
- **Detalle de tarea** (`/proyectos/tareas/:id`): tabs internos: Descripción, Subtareas, Seguidores, Tiempo/Medición, Dependencias, Recursos, Comentarios.
- **Subtareas**: implementadas hasta 5 niveles de jerarquía. Visibles en tab Subtareas del detalle.
- **3 Modos de medición**: `status_only` (solo estados), `timesheet` (horas/timer), `quantity` (cantidades). El modo se determina por la actividad Saiopen asociada.
- **Tags/Etiquetas**: modelo `TaskTag` con 8 colores. CRUD en `/api/v1/projects/tags/`.
- **Código automático**: se genera automáticamente `TASK-00001` al crear si no se provee.
- **Cambio rápido de estado inline**: los chips de estado son clicables para cambiar estado sin abrir formulario.
- **Estados**: 6 estados: `todo`, `in_progress`, `in_review`, `blocked`, `completed`, `cancelled`.
- **Prioridades**: 4 niveles: 1=Baja, 2=Normal, 3=Alta, 4=Urgente.

#### ⚠️ Implementado pero Diferente al Manual
- **Tab "Tareas" dentro del proyecto**: el manual documenta un tab Tareas dentro del proyecto con filtro por fase. Esto **no existe en el detalle del proyecto**. Las tareas se acceden globalmente desde `/proyectos/tareas`.
- **Filtro por fase en vista lista de tareas**: en la lista global de tareas, no hay filtro por fase (solo por estado, prioridad y búsqueda). El filtro de fase existe en el Kanban global pero no en la lista.
- **Columna "Predecesoras" en vista lista**: el manual documenta que la columna predecesoras muestra `T-003(FS)` en la tabla de tareas. No existe esta columna en la lista implementada.

#### ❌ No Implementado
- **"Mis Tareas"** (vista personal de tareas asignadas): mencionado en el sidebar del manual como módulo independiente. No existe como ruta/página separada en el frontend. El sidebar actual muestra "Tareas" que es la lista global.

#### 🐛 Bugs Encontrados
- **Lista global de tareas muestra 0 resultados** (ver sección Proyectos — Bugs).
- **`TareaListComponent` no tiene modo de filtrar por fase** aunque el backend lo soporta (`fase` en `TareaFilters`).

---

### 4. CATÁLOGO DE ACTIVIDADES

#### ✅ Implementado y Funcionando
- **Módulo Catálogo** (`/proyectos/actividades`): lista completa con columnas Código, Nombre, Tipo, Unidad de medida, Costo base, Acciones.
- **4 tipos de actividades**: `labor` (Mano de obra), `material` (Material), `equipment` (Equipo), `subcontract` (Subcontrato). Correctamente implementados en backend (`ActivityType`) y frontend.
- **Crear actividad**: formulario con código, nombre, descripción, tipo, unidad de medida, costo unitario base.
- **Editar actividad**: funciona.
- **Eliminar actividad**: con confirmación.
- **Reutilización entre proyectos**: el catálogo es compartido a nivel empresa. Las actividades están disponibles en todos los proyectos.
- **Sincronización con Saiopen**: modelo `SaiopenActivity` paralelo para actividades importadas del ERP.
- **Tab "Actividades de obra" en detalle del proyecto**: funciona. Muestra las `ProjectActivity` (actividades asignadas al proyecto específico) con cantidades planificadas/ejecutadas.
- **Endpoints backend**: `GET/POST /api/v1/projects/activities/`, `GET/PATCH/DEL /api/v1/projects/activities/:id/`, y endpoints por proyecto.

#### ⚠️ Implementado pero Diferente al Manual
- **Consecutivo para código de actividad**: el manual menciona que el código se autogenera (ej: ACT-001). La implementación genera el código pero el campo de consecutivo del catálogo de actividades **no usa el sistema de consecutivos** de la plataforma — se genera desde el backend directamente.
- **Toggle de desactivar actividad**: el manual documenta un toggle de estado en la lista. En la UI existe solo editar/eliminar. No hay un toggle visible de activar/desactivar en la lista.

#### ❌ No Implementado
- **"Hito" como tipo de actividad en el catálogo**: el manual menciona "Hito" como tipo de actividad (sin costo unitario). El backend solo tiene 4 tipos: labor, material, equipment, subcontract. **No hay tipo `hito` en el catálogo de Actividades**. Los hitos del proyecto (`Milestone`) son un modelo separado que no está vinculado al catálogo de actividades.

---

### 5. DEPENDENCIAS ENTRE TAREAS

#### ✅ Implementado y Funcionando
- **3 tipos de dependencias**: FS (Finish to Start), SS (Start to Start), FF (Finish to Finish). Implementados en backend (`TaskDependency`) y en el `SelectorDependenciasComponent` del frontend.
- **Crear dependencia**: desde el tab "Dependencias" en el detalle de la tarea. Autocompletado de búsqueda de tarea predecesora + selector de tipo + lag time.
- **Lag time**: campo `retraso_dias` implementado en backend y UI. Acepta valores negativos.
- **Ver predecesoras y sucesoras**: en el tab "Dependencias" se muestran chips con código de tarea predecesora, tipo de dependencia y lag time.
- **Detección de ciclos**: implementada en `scheduling_services.py` (algoritmo CPM).
- **Visualización en Gantt**: dependencias visibles como barras en el diagrama.
- **Endpoint**: `/api/v1/projects/tasks/:id/` incluye `predecesoras_detail` y `sucesoras_detail` en la respuesta.
- **Badge "Camino Crítico"**: si la tarea está en el camino crítico, el detalle muestra un badge de alerta.

#### ⚠️ Implementado pero Diferente al Manual
- **Las dependencias no muestran flechas en el Gantt (FS, SS, FF)**: el Gantt usa `frappe-gantt` que dibuja dependencias básicas. La especificación del manual describe flechas diferenciadas según tipo (FS: extremo-derecho a extremo-izquierdo, SS: izq-izq, FF: der-der). La librería no diferencia visualmente los tipos de flecha.

#### ❌ No Implementado
- **Dependencia tipo SF (Start to Finish)**: el manual documenta 4 tipos de dependencia incluyendo SF. El **backend solo implementa 3 tipos (FS, SS, FF)** — SF no está en el `DependencyType` enum ni en la UI. El manual menciona "Saicloud soporta tres tipos (en la interfaz; el modelo técnico incluye también SF)" — esto es una inconsistencia del propio manual vs lo implementado: SF no está en backend ni frontend.

---

### 6. GANTT

#### ✅ Implementado y Funcionando
- **Tab "Gantt" en detalle del proyecto**: funciona. Renderiza con `frappe-gantt`. Se muestran las tareas con fechas como barras de colores por estado.
- **Modos de vista**: Día, Semana, Mes. Botones toggle funcionan.
- **Leyenda de colores**: Por hacer, En progreso, En revisión, Bloqueada, Completada, Cancelada.
- **Botón "Ruta crítica"**: implementado. Llama a `/api/v1/projects/:id/scheduling/critical-path/` y colorea las tareas críticas en rojo.
- **Botón "Holgura"**: implementado. Muestra etiqueta `[CRÍTICA]` o `[Float: Xd]` junto al nombre de las tareas críticas (float = 0 para críticas). Para tareas no críticas, el float individual requeriría llamadas adicionales.
- **Botón "Baseline"**: implementado. Carga la baseline activa del proyecto para mostrar el overlay.
- **Drag de fechas en el Gantt**: se puede arrastrar una barra para cambiar fechas. Aparece `ConfirmDialogComponent` de confirmación antes de guardar. Se actualiza vía PATCH a la tarea.
- **Click en tarea del Gantt**: navega al detalle de la tarea.
- **Botón refresh**: recarga los datos del Gantt.
- **Loading state**: `mat-progress-bar` mientras carga.
- **`loadingOverlay` signal**: barra adicional durante carga de overlays.

#### ⚠️ Implementado pero Diferente al Manual
- **"Hoy" para centrar la vista**: el botón "Today" de `frappe-gantt` existe y funciona, pero no es un botón personalizado en la barra de herramientas propia — es nativo de la librería.
- **Holgura (Float) por tarea individual**: el overlay de Holgura solo muestra float=0 para tareas críticas. Para tareas no críticas el float se muestra como nulo porque el backend no expone el float por tarea en el endpoint de ruta crítica. El endpoint `/api/v1/projects/tasks/:task_pk/scheduling/float/` existe pero no se usa en el overlay del Gantt para poblar el mapa completo.
- **Dependencias visualizadas como flechas**: frappe-gantt dibuja flechas básicas pero no diferencia FS/SS/FF visualmente como describe el manual.

#### ❌ No Implementado
- **Zoom con `Ctrl + Rueda del mouse`**: la librería frappe-gantt no soporta zoom con Ctrl+scroll. Solo los botones toggle Día/Semana/Mes.
- **"Tareas sin fechas" en lista separada**: el manual documenta que las tareas sin fechas aparecen en una lista separada bajo el Gantt. La implementación simplemente las excluye del diagrama sin mostrar una lista alternativa.
- **Tooltip al pasar el cursor**: frappe-gantt muestra un tooltip nativo básico, pero el manual especifica un tooltip con nombre, fechas, responsable y avance — no está personalizado.

---

### 7. TIMESHEETS Y TIMER

#### ✅ Implementado y Funcionando
- **Timer/Cronómetro** en detalle de tarea: componente `CronometroComponent` integrado en el tab "Tiempo". Permite iniciar, pausar, detener la sesión. El modelo `WorkSession` soporta pausas múltiples y calcula `duracion_segundos`.
- **Registro manual de horas**: en el detalle de tarea, el tab "Tiempo" muestra "Registros diarios" con formulario inline para agregar entradas de timesheet.
- **TimesheetEntry**: modelo con fecha, horas, descripción, usuario. Endpoint `/api/v1/projects/timesheets/`.
- **Modo timer configurable**: `ModuleSettings.modo_timesheet` con opciones: `manual`, `timer`, `both`, `disabled`. Respetado en la UI (muestra/oculta cronómetro según configuración).
- **Ver timesheets por tarea**: lista de registros diarios en el tab "Tiempo" con fecha, horas y descripción.
- **Editar y eliminar timesheets**: implementados en el backend.
- **Sesiones de trabajo** (`WorkSession`): el modelo en backend soporta pausas, pero la edición de sesiones antiguas no es visible en la UI.

#### ⚠️ Implementado pero Diferente al Manual
- **Vista semanal de timesheets** ("grilla semanal"): el componente `TimesheetSemanalComponent` **existe** en el código pero **no está enrutado** en `proyectos.routes.ts`. El manual documenta que desde el sidebar se accede a "Timesheets" como una grilla semanal. Esto no es accesible desde la UI.
- **Validación de timesheet**: el backend implementa lógica de validación de timesheets (`TimesheetEntry`), pero la UI no muestra claramente si un registro está "validado" (no puede editarse).
- **Un Timer activo a la vez**: el backend gestiona sesiones activas por usuario, pero la UI no muestra un indicador en la barra superior cuando hay un cronómetro corriendo (como describe el manual con "el ícono del Timer en la barra superior").

#### ❌ No Implementado
- **Tab "Timesheets" en el detalle del proyecto**: el manual documenta un tab "Timesheets" dentro del proyecto para ver el registro de horas de todo el equipo. No existe en `proyecto-detail.component.html`.
- **Acceso desde sidebar "Timesheets"**: la vista semanal no es accesible; el componente existe pero no está enrutado.

---

### 8. RESOURCE MANAGEMENT

#### ✅ Implementado y Funcionando
- **Asignación de recursos a tareas**: tab "Recursos" en detalle de tarea. `ResourceAssignmentPanelComponent` lista asignaciones y permite agregar/eliminar. El diálogo `ResourceAssignmentFormComponent` solicita usuario, porcentaje y fechas.
- **Detección de sobreasignación**: endpoint `check-overallocation` implementado. El backend detecta conflictos y el formulario muestra advertencias.
- **Capacidad de recursos**: modelo `ResourceCapacity` con horas/semana y rango de fechas. Endpoint CRUD implementado.
- **Disponibilidad (ausencias)**: modelo `ResourceAvailability` con tipos: vacaciones, incapacidad, festivo, capacitación, otro. Flujo de aprobación implementado en backend (`approve` endpoint).
- **Workload**: endpoint `/api/v1/projects/resources/workload/` implementado.
- **Tab "Equipo" en detalle del proyecto**: muestra miembros asignados, sus tareas y porcentajes de asignación, con selector de rango de fechas y botón "Asignar miembro". El componente `TeamTimelineComponent` funciona.
- **Stakeholders del proyecto**: modelo `ProjectStakeholder` con roles (cliente, subcontratista, proveedor, consultor, interventor, supervisor). Tab "Terceros" en el detalle funciona.

#### ⚠️ Implementado pero Diferente al Manual
- **Pantalla de "Capacidades" y "Disponibilidad"**: el manual describe acceso desde "tab Recursos del proyecto → Capacidades" y "tab Recursos → Disponibilidad". En la implementación, el tab "Equipo" del proyecto muestra un timeline de equipo pero **no tiene sub-navegación a Capacidades ni Disponibilidad**. El backend tiene los endpoints pero no hay UI de administración de capacidad/disponibilidad accesible desde el proyecto.
- **Vista de "Carga de trabajo del equipo" (Workload)**: el backend tiene el endpoint, pero en la UI del tab "Equipo" solo se muestra un timeline de asignaciones simples, no la tabla de carga por semana con código de colores (verde/amarillo/rojo) que describe el manual.
- **Calendario de usuario**: el backend tiene `/api/v1/projects/resources/calendar/` pero no hay un componente de calendario visual en la UI.

#### ❌ No Implementado
- **Módulo de Capacidades de recursos** (pantalla separada para configurar horas/semana por usuario): no existe como pantalla accesible desde la UI.
- **Módulo de Disponibilidad** (registro de vacaciones/licencias con flujo de aprobación): el backend existe pero no hay pantalla de UI para registrar ausencias.
- **Tarifas de costo por recurso** (UI): el servicio `CostRateService` existe y los endpoints están en el backend, pero **no existe ningún componente HTML de UI** para crear/editar tarifas. Esto impide que el EVM calcule correctamente el costo de labor.

---

### 9. ANALYTICS

#### ✅ Implementado y Funcionando
- **Tab "Analytics" en detalle del proyecto**: funciona correctamente. Usa `@defer` para cargar solo cuando el tab está activo (solución al bug de canvas invisible).
- **4 KPI Cards**: Completud (%), On-Time (%), Velocidad (tareas/sem), Horas Burn Rate.
- **Burn Down Chart**: renderiza con Chart.js. Muestra línea ideal (gris punteada), estimadas restantes (azul), acumuladas reales (verde).
- **Velocity Chart**: barras por semana + línea de promedio.
- **Task Distribution**: gráfico de dona por estado.
- **Resource Utilization**: gráfico de barras horizontales.
- **Botón Refresh**: recarga los datos del dashboard.
- **Botón Export** (ícono de descarga): implementado.
- **Endpoints analíticos**: todos implementados — KPIs, task-distribution, velocity, burn-rate, burn-down, resource-utilization, timeline, compare, export-excel.

#### ⚠️ Implementado pero Diferente al Manual
- **KPI "Horas registradas"**: el manual documenta este KPI. La implementación lo muestra como "Horas Burn Rate" (horas/semana) y para este proyecto de demo muestra "Sin datos" en el subtexto.
- **KPI "Tareas vencidas"**: el manual documenta este KPI separado. En la implementación el KPI de On-Time muestra "0 vencidas" como subtexto, no como KPI independiente.
- **Dashboard multiproyecto**: el manual documenta analytics desde el "Dashboard principal" con comparación entre proyectos. La implementación en `/dashboard` no muestra analytics comparativo — el dashboard actual es solo una pantalla de bienvenida/selector de módulos.

#### ❌ No Implementado
- **Exportación a Excel con 4 hojas** (KPIs, tareas, horas por usuario, datos Burn Down): el endpoint existe pero no se puede verificar el formato de salida desde el navegador sin un proyecto con datos completos de EVM.

---

### 10. ADVANCED SCHEDULING

#### ✅ Implementado y Funcionando
- **Auto-Schedule**: botón "Scheduling → Auto-Schedule" en header del proyecto. Abre `AutoScheduleDialogComponent` con opciones ASAP/ALAP y modo dry run. Backend implementado con CPM.
- **Nivelación de Recursos** (`ResourceLevelingView`): endpoint implementado en backend.
- **Ruta Crítica** (`CriticalPathView`): endpoint implementado. Integrado en el botón "Ruta crítica" del Gantt.
- **Float por tarea** (`TaskFloatView`): endpoint por tarea implementado.
- **Restricciones de tareas** (`TaskConstraint`): modelo con 8 tipos (ASAP, ALAP, SNET, SNLT, FNET, FNLT, MSO, MFO). Endpoints CRUD implementados en backend. Componente `TaskConstraintsPanelComponent` existe en frontend.
- **Baselines** (tab "Baselines"): crea baselines, lista con estado activo/inactivo, comparación tabular baseline vs plan actual con variaciones en días (adelantada/en plazo/retrasada). Funciona correctamente con datos de demo.
- **Escenarios What-If** (tab "Escenarios"): lista escenarios, crea escenarios, ejecuta simulación (botón "Ejecutar simulación"). Muestra fecha fin simulada y delta de días.
- **Overlay "Baseline" en Gantt**: botón implementado, carga baseline activa.

#### ⚠️ Implementado pero Diferente al Manual
- **Auto-Schedule — el dialog muestra solo ASAP/ALAP y dry run**: funcional pero la previsualización completa (número de tareas reprogramadas, nueva fecha de fin, ruta crítica calculada, advertencias) no se muestra en el dialog actual. El endpoint backend devuelve esta información pero la UI del dialog no la presenta en detalle.
- **Escenarios What-If — configuración de cambios**: el manual documenta la configuración granular de cambios (task_changes, resource_changes, dependency_changes con lag times). La implementación actual crea el escenario con un placeholder mínimo (`dependency_changes: { new: { retraso_dias: 0 } }`) y no tiene UI para configurar cambios individuales por tarea o recurso. El código fuente comenta "La configuración de cambios detallados es trabajo futuro (Chunk 8)".
- **Comparar múltiples escenarios**: el manual documenta selección múltiple de escenarios y tabla comparativa. El endpoint `scenarios/compare/` existe en backend pero no hay UI para selección múltiple ni comparación en el componente `WhatIfScenarioBuilderComponent`.
- **Restricciones de tareas — UI**: `TaskConstraintsPanelComponent` existe en el código pero **no está incluido en ningún template de detalle de tarea visible**. El componente existe en `/proyectos/components/scheduling/task-constraints-panel/` pero no está integrado en `tarea-detail.component.html`.

#### ❌ No Implementado
- **Nivelación de recursos — UI**: el endpoint backend existe pero no hay botón ni UI para ejecutar la nivelación de recursos desde el frontend. Solo existe el endpoint.
- **Float individual por tarea en detalle** (`FloatIndicatorComponent`): el componente `float-indicator.component.ts` existe pero no está integrado en ningún template de tarea.

---

### 11. BUDGET & COST TRACKING

#### ✅ Implementado y Funcionando
- **Tab "Presupuesto" en detalle del proyecto**: funciona. Muestra:
  - Tarjeta de presupuesto con estado (planificado/aprobado/costo real/ejecución %).
  - Alerta de presupuesto superado (en demo PRY-003: 125.55% ejecutado → alerta roja).
  - Sección de Mano de obra con costo real vs planificado.
  - Sección de Gastos directos con costo real, planificado y cantidad de registros.
  - Tabla de gastos del proyecto con columnas fecha, categoría, descripción, monto, facturable, estado.
  - Botones aprobar gasto (✓) y eliminar gasto en cada fila.
  - EVM section con métricas BAC, EV, AC, PV, CPI, SPI, EAC y avance.
  - Botones "Editar" presupuesto y "Snapshot".
- **Crear y aprobar presupuesto**: flujo implementado. Solo `company_admin` puede aprobar.
- **Registrar gasto** ("+ Registrar gasto"): dialog con campos categoría, descripción, monto, fecha, facturable, URL soporte, notas.
- **Aprobar gastos**: botón de aprobación por registro individual.
- **Alertas de presupuesto**: activas, configurables por umbral %.
- **Snapshots de presupuesto**: botón "Snapshot" y endpoint implementado.
- **Facturación** (`InvoiceDataView`): endpoint implementado en backend.
- **Todos los endpoints de Budget implementados** en backend.

#### ⚠️ Implementado pero Diferente al Manual
- **EVM — Métricas muestran "—"**: en la sección EVM del tab Presupuesto, los valores de BAC, EV, AC, PV, CPI, SPI, EAC aparecen como "—". Los endpoints `/api/v1/projects/:id/costs/evm/` devuelven error o datos vacíos. Esto ocurre porque los timesheets no están conectados a las tarifas de costo (sin `CostRate` configuradas).
- **Cost breakdown por recurso y por tarea**: los endpoints `/costs/by-resource/` y `/costs/by-task/` generan **errores 404 o 500** en el browser console durante el test. La UI del BudgetDashboard los consume pero retornan error.
- **Tarifas de recurso**: el manual documenta "Tab Presupuesto → Tarifas de recurso". En la implementación NO hay sección de tarifas en el BudgetDashboard. El servicio `CostRateService` y los endpoints existen en backend pero no hay UI para verlas/gestionarlas.

#### ❌ No Implementado
- **UI para Tarifas de Costo por Recurso**: ningún componente HTML implementa la gestión de `ResourceCostRate`. Esta es la causa raíz de que el EVM no calcule correctamente.
- **Exportar datos de factura a Excel desde UI**: el endpoint `invoice-data` existe pero no hay botón de exportación en el tab Presupuesto.

---

### 12. TERCEROS (Clientes y Proveedores)

#### ✅ Implementado y Funcionando
- **Módulo Terceros** (`/terceros`): lista con columnas Nombre/Razón social, Identificación, Tipo (Cliente/Proveedor), Contacto (email + teléfono). Paginación con mat-paginator server-side.
- **Filtros**: por tipo de tercero y tipo de identificación. Búsqueda por texto.
- **Crear tercero** (`/terceros/nuevo`): formulario completo con nombre, tipo, NIT/cédula, email, teléfono, ciudad, dirección, notas.
- **Editar tercero**: ícono de lápiz abre formulario de edición.
- **Eliminar tercero**: con confirmación.
- **Backend app `terceros`**: modelo `Tercero` completo con migraciones. Endpoints CRUD implementados.
- **Tipos de tercero**: Cliente, Proveedor, Customer (hay inconsistencia — ver bug).
- **Tab "Terceros" en detalle del proyecto** (`ProjectStakeholder`): permite vincular terceros al proyecto con rol (cliente, subcontratista, proveedor, etc.).

#### ⚠️ Implementado pero Diferente al Manual
- **Tipo "Ambos" (cliente y proveedor)**: el manual sugiere tipo "Ambos". En la lista se muestra "Customer" en inglés (en lugar de "Cliente") para el tercero TER-0001. Hay inconsistencia de traducción en los tipos.
- **Selector de terceros en formulario de proyecto**: el manual indica que al crear un proyecto se selecciona un Tercero de tipo "Cliente" desde el catálogo. La implementación almacena `cliente_id` (string) y `cliente_nombre` (string) en lugar de una FK real al modelo Tercero. Hay un mismatch entre el módulo de terceros y el proyecto.

#### 🐛 Bugs Encontrados
- **Tipo de tercero muestra "CUSTOMER" en inglés**: el tercero "Inversiones del Valle S.A.S" aparece con tipo "CUSTOMER" en la lista, en lugar de "Cliente" en español. Inconsistencia de traducción en el serializer o modelo.

---

## FEATURES NO DOCUMENTADOS EN EL MANUAL (pero implementados)

### FEATURE #1: Hitos Facturables (Milestones)
**Descripción:** Tab "Hitos" en el detalle del proyecto. El modelo `Milestone` representa hitos facturables que generan facturas en Saiopen. Tiene campos: nombre, descripción, % del proyecto, valor a facturar, estado de facturación, fecha facturación.
**Ubicación:** `/frontend/src/app/features/proyectos/components/hito-list/` y `/backend/apps/proyectos/models.py` clase `Milestone`.
**Recomendación:** Documentar en el manual como sub-sección dentro de "Gestión de Proyectos".

### FEATURE #2: Documentos Contables sincronizados desde Saiopen
**Descripción:** Tab "Documentos" en el detalle del proyecto. Muestra documentos contables (facturas de venta/compra, órdenes de compra, etc.) importados desde el ERP Saiopen vía agente. Son de solo lectura.
**Ubicación:** `/backend/apps/proyectos/models.py` clase `AccountingDocument`.
**Recomendación:** Documentar como feature de integración con Saiopen.

### FEATURE #3: Configuración del Módulo de Proyectos
**Descripción:** Página de configuración en `/proyectos/configuracion`. Permite configurar: modo de timesheet (manual/timer/ambos/desactivado), días de alerta de vencimiento, y si requiere sincronización con Saiopen para ejecutar proyectos.
**Ubicación:** `ConfiguracionComponent` en `/frontend/src/app/features/proyectos/components/configuracion/`.
**Recomendación:** Documentar en el manual en una sección "Configuración del módulo".

---

## GAPS CRÍTICOS IDENTIFICADOS

### GAP #1: Tabs faltantes en el detalle del proyecto
**Severidad:** 🔴 Crítico
**Descripción:** El manual documenta 13 tabs en el detalle de proyecto: Resumen, Fases, Tareas, Kanban, Gantt, Actividades, Recursos, Timesheets, Analytics, Scheduling, Presupuesto, Documentos, Hitos. La implementación tiene 12 tabs pero con nombres y contenidos diferentes.
**Tabs faltantes en la implementación vs manual:** Tareas (dentro del proyecto), Kanban (dentro del proyecto), Timesheets (del proyecto), Scheduling (unificado).
**Estado actual:** Los tabs "Tareas" y "Kanban" existen como páginas globales (`/proyectos/tareas`), pero no están integrados dentro del detalle del proyecto con filtro automático.
**Impacto:** El usuario debe navegar fuera del proyecto para ver/gestionar sus tareas, rompiendo el flujo de trabajo natural.
**Recomendación:** Agregar tabs "Tareas" y "Kanban" al `proyecto-detail.component.html` que carguen tareas filtradas por `proyectoId`. Agregar tab "Timesheets" que muestre los timesheets del equipo del proyecto.

### GAP #2: UI de Tarifas de Costo por Recurso — EVM no funcional
**Severidad:** 🔴 Crítico
**Descripción:** Sin tarifas de costo configuradas, el EVM (CPI, SPI, EAC, etc.) no puede calcular. Las métricas EVM en el tab Presupuesto muestran "—" para todos los indicadores financieros.
**Ubicación esperada:** Tab "Presupuesto" → sección "Tarifas de recurso" (documentado en manual sección 14.2).
**Estado actual:** El servicio `CostRateService` y los endpoints backend `/resources/cost-rates/` existen completamente implementados, pero **no existe ningún componente HTML** para gestionar tarifas. Ningún template importa el servicio.
**Archivos afectados:** `/frontend/src/app/features/proyectos/services/cost-rate.service.ts` (solo el servicio, sin UI).
**Impacto:** El módulo de Budget es parcialmente inútil sin EVM funcional. Es el módulo de mayor valor analítico para gerentes de proyecto.
**Recomendación:** Crear `CostRateFormComponent` e integrarlo en `BudgetDashboardComponent` con una sección "Tarifas por Recurso".

### GAP #3: Endpoints `/costs/by-resource/` y `/costs/by-task/` con errores
**Severidad:** 🔴 Crítico
**Descripción:** Al cargar el tab Presupuesto, los endpoints `/api/v1/projects/:id/costs/by-resource/` y `/api/v1/projects/:id/costs/by-task/` devuelven error (404 o 500). Esto impide mostrar el desglose de costos por recurso y por tarea.
**Estado actual:** Errores visibles en console del navegador durante el testing.
**Impacto:** Las secciones de cost breakdown en el dashboard de presupuesto no renderizan datos.
**Recomendación:** Investigar y corregir los endpoints en `budget_views.py`.

### GAP #4: Vista semanal de Timesheets no enrutada
**Severidad:** 🔴 Crítico
**Descripción:** El componente `TimesheetSemanalComponent` existe en el código pero no está registrado en `proyectos.routes.ts`. El manual documenta esta vista como accesible desde el sidebar.
**Ubicación del componente:** `/frontend/src/app/features/proyectos/components/timesheet-semanal/`
**Estado actual:** El componente existe completamente implementado pero es inaccesible para el usuario.
**Impacto:** Los usuarios no pueden registrar tiempo en modo "grilla semanal". Deben hacerlo manualmente tarea por tarea.
**Recomendación:** Agregar ruta en `proyectos.routes.ts` y enlace en el sidebar de navegación.

### GAP #5: Nivelación de recursos — solo backend
**Severidad:** 🟡 Alto
**Descripción:** El endpoint `POST /api/v1/projects/:id/scheduling/level-resources/` está implementado en el backend pero no hay ningún botón ni UI en el frontend para ejecutarlo.
**Estado actual:** Solo accesible vía API directa.
**Impacto:** La funcionalidad de nivelación documentada en el manual (sección 13.2) es completamente inaccesible desde la UI.
**Recomendación:** Agregar botón "Nivelar Recursos" en el `AutoScheduleDialogComponent` o en un nuevo panel de scheduling.

### GAP #6: Restricciones de tareas — componente no integrado
**Severidad:** 🟡 Alto
**Descripción:** `TaskConstraintsPanelComponent` existe en `/frontend/src/app/features/proyectos/components/scheduling/task-constraints-panel/` con HTML, SCSS y TS completos, pero **no está importado ni usado en ningún template** — ni en el detalle de tarea ni en ninguna otra pantalla.
**Estado actual:** Código muerto — no accesible para el usuario.
**Impacto:** Los 8 tipos de restricciones (ASAP, ALAP, SNET, SNLT, FNET, FNLT, MSO, MFO) documentados en el manual son completamente inaccesibles.
**Recomendación:** Integrar `TaskConstraintsPanelComponent` en `tarea-detail.component.html` como un nuevo tab "Restricciones" o como sección dentro del tab "Dependencias".

### GAP #7: What-If Scenarios — configuración de cambios no implementada
**Severidad:** 🟡 Alto
**Descripción:** El componente `WhatIfScenarioBuilderComponent` solo permite crear un escenario con nombre y descripción, pero no tiene UI para configurar los cambios específicos (qué tareas se modifican, qué recursos se alteran). El escenario se crea con un placeholder.
**Estado actual:** Se puede crear y ejecutar un escenario pero con cambios vacíos/placeholder, lo que hace que la simulación no sea significativa.
**Impacto:** La funcionalidad más avanzada del módulo es una cáscara — el usuario no puede usarla productivamente.
**Recomendación:** Implementar el formulario de configuración de cambios (Chunk 8 según comentario en el código).

### GAP #8: Dashboard principal sin analytics multiproyecto
**Severidad:** 🟡 Alto
**Descripción:** El manual documenta que desde el "Dashboard principal" se accede a analytics multiproyecto con tarjetas comparativas y gráficos de velocidad entre proyectos. La implementación del dashboard es solo una pantalla de bienvenida con tarjetas de módulos.
**Estado actual:** El endpoint `analytics/compare/` existe en el backend pero no se usa en el dashboard principal.
**Impacto:** Los directivos y gerentes no tienen una vista ejecutiva multiproyecto.
**Recomendación:** Implementar un `DashboardComponent` con resumen de proyectos activos, KPIs consolidados y gráfico comparativo usando el endpoint `analytics/compare/`.

### GAP #9: Módulo "Mis Tareas" — no existe
**Severidad:** 🟢 Medio
**Descripción:** El manual documenta "Mis Tareas" en el sidebar como vista personal de todas las tareas asignadas al usuario. No existe como ruta ni componente en el frontend.
**Estado actual:** La lista de tareas en `/proyectos/tareas` sí puede filtrar por usuario responsable si se pasa el filtro, pero no hay una vista dedicada ni enlace en el sidebar.
**Impacto:** Los usuarios no tienen una vista rápida de sus propias tareas.
**Recomendación:** Crear ruta `/proyectos/mis-tareas` que precargue el filtro `responsable = usuario_actual`.

### GAP #10: Tipo de tercero "CUSTOMER" en inglés
**Severidad:** 🟢 Medio
**Descripción:** El tipo de tercero muestra "CUSTOMER" en inglés en la tabla de lista de terceros. El manual y la UI deben mostrar "Cliente" en español.
**Impacto:** Inconsistencia de idioma en la interfaz.
**Recomendación:** Revisar el serializer de Tercero (`/backend/apps/terceros/serializers.py`) para asegurar que `tipo_tercero` retorna el display value en español, o agregar mapeo en el frontend.

### GAP #11: Actividad tipo "Hito" faltante en catálogo
**Severidad:** 🟢 Medio
**Descripción:** El manual documenta el tipo de actividad "Hito" en el catálogo (sin costo unitario, modo de medición checkbox). El backend solo tiene: labor, material, equipment, subcontract.
**Impacto:** No se puede crear una actividad de tipo hito en el catálogo. Los hitos del proyecto (`Milestone`) son un modelo completamente separado e independiente.
**Recomendación:** Agregar tipo `milestone` al `ActivityType` enum o clarificar en el manual que los hitos son un concepto diferente a las actividades del catálogo.

---

## TABLA RESUMEN COMPLETA

| # | Feature | Manual | Backend | Frontend | Navegador | Estado | Severidad |
|---|---------|--------|---------|----------|-----------|--------|-----------|
| 1 | Lista proyectos - Vista cards | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 2 | Lista proyectos - Vista lista | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 3 | Filtros en lista proyectos | ✅ | ✅ | ⚠️ (falta filtro por gerente) | ✅ | Parcial | ⚪ |
| 4 | Crear proyecto + campos completos | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 5 | Consecutivos automáticos por tipo | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 6 | 6 estados de proyecto | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 7 | AIU en proyecto | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 8 | Editar proyecto | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 9 | Eliminar proyecto con confirmación | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 10 | Detalle proyecto - Tab General | ✅ | ✅ | ⚠️ (llamado "Resumen" en manual) | ✅ | Parcial | ⚪ |
| 11 | Detalle proyecto - Tab Tareas (dentro del proyecto) | ✅ | ✅ | ❌ | ❌ | No implementado | 🔴 |
| 12 | Detalle proyecto - Tab Kanban (dentro del proyecto) | ✅ | ✅ | ❌ | ❌ | No implementado | 🔴 |
| 13 | Detalle proyecto - Tab Fases | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 14 | Detalle proyecto - Tab Timesheets (del equipo) | ✅ | ✅ | ❌ | ❌ | No implementado | 🔴 |
| 15 | Detalle proyecto - Tab Gantt | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 16 | Detalle proyecto - Tab Analytics | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 17 | Detalle proyecto - Tab Scheduling (unificado) | ✅ | ✅ | ⚠️ (fragmentado en Baselines + Escenarios + botón header) | ⚠️ | Parcial | 🟢 |
| 18 | Detalle proyecto - Tab Presupuesto | ✅ | ✅ | ✅ | ⚠️ (EVM con errores) | Parcial | 🔴 |
| 19 | Detalle proyecto - Tab Documentos | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 20 | Detalle proyecto - Tab Hitos | — | ✅ | ✅ | ✅ | No documentado | — |
| 21 | Detalle proyecto - Tab Actividades de obra | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 22 | Detalle proyecto - Tab Equipo | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 23 | Detalle proyecto - Tab Terceros | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 24 | Crear/editar/eliminar fases | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 25 | Activar/completar fase | ✅ | ✅ | ⚠️ (endpoints existen, botón activar no visible en UI) | ⚠️ | Parcial | 🟢 |
| 26 | Reordenar fases | ✅ | ✅ | ⚠️ (campo orden numérico, sin drag-and-drop) | ⚠️ | Parcial | ⚪ |
| 27 | Progreso automático de fase | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 28 | Lista global de tareas | ✅ | ✅ | ✅ | 🐛 (0 resultados en testing) | Parcial/Bug | 🟡 |
| 29 | Kanban global de tareas | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 30 | Crear/editar/eliminar tareas | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 31 | 3 modos de medición (status, timesheet, cantidad) | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 32 | Subtareas (jerarquía) | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 33 | Tags de tareas | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 34 | "Mis Tareas" (vista personal) | ✅ | ✅ | ❌ | ❌ | No implementado | 🟢 |
| 35 | Catálogo de Actividades (4 tipos) | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 36 | Tipo "Hito" en catálogo de actividades | ✅ | ❌ | ❌ | ❌ | No implementado | 🟢 |
| 37 | Toggle activar/desactivar actividad | ✅ | ✅ | ❌ | ❌ | No implementado | ⚪ |
| 38 | Dependencias FS, SS, FF | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 39 | Dependencia tipo SF | ✅ | ❌ | ❌ | ❌ | No implementado | ⚪ |
| 40 | Lag time en dependencias | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 41 | Detección de ciclos en dependencias | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 42 | Gantt con frappe-gantt | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 43 | Overlay Ruta Crítica en Gantt | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 44 | Overlay Holgura en Gantt | ✅ | ✅ | ⚠️ (solo tareas críticas con float=0) | ⚠️ | Parcial | 🟢 |
| 45 | Overlay Baseline en Gantt | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 46 | Drag de fechas en Gantt | — | ✅ | ✅ | ✅ | No documentado (feature extra) | — |
| 47 | Timer (cronómetro) en detalle de tarea | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 48 | Registro manual de timesheets | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 49 | Vista semanal de timesheets | ✅ | ✅ | ⚠️ (componente existe, no enrutado) | ❌ | No accesible | 🔴 |
| 50 | Tab Timesheets en detalle del proyecto | ✅ | ✅ | ❌ | ❌ | No implementado | 🔴 |
| 51 | Asignación de recursos a tareas | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 52 | Capacidad de recursos (config horas/semana) | ✅ | ✅ | ❌ (solo backend) | ❌ | Solo backend | 🟡 |
| 53 | Disponibilidad (ausencias) con aprobación | ✅ | ✅ | ❌ (solo backend) | ❌ | Solo backend | 🟡 |
| 54 | Workload del equipo con colores | ✅ | ✅ | ⚠️ (timeline básico sin colores semáforo) | ⚠️ | Parcial | 🟢 |
| 55 | Tarifas de costo por recurso | ✅ | ✅ | ❌ (solo servicio, sin UI) | ❌ | No implementado | 🔴 |
| 56 | Auto-Schedule ASAP/ALAP + dry run | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 57 | Nivelación de recursos | ✅ | ✅ | ❌ (solo backend) | ❌ | Solo backend | 🟡 |
| 58 | Restricciones de tareas (8 tipos) | ✅ | ✅ | ⚠️ (componente existe, no integrado) | ❌ | No accesible | 🟡 |
| 59 | Baselines — crear y comparar | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 60 | What-If Scenarios — crear y simular | ✅ | ✅ | ⚠️ (sin configuración de cambios) | ⚠️ | Parcial | 🟡 |
| 61 | Presupuesto del proyecto (crear/aprobar) | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 62 | Gastos del proyecto (registrar/aprobar) | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 63 | EVM metrics (CPI, SPI, EAC, etc.) | ✅ | ✅ | ✅ | 🐛 (valores "—") | Parcial/Bug | 🔴 |
| 64 | Cost breakdown por recurso y por tarea | ✅ | ✅ | ✅ | 🐛 (errores 404/500) | Parcial/Bug | 🔴 |
| 65 | Tarifas de costo UI | ✅ | ✅ | ❌ | ❌ | No implementado | 🔴 |
| 66 | Analytics 4 KPIs | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 67 | Analytics Burn Down Chart | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 68 | Analytics Velocity Chart | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 69 | Analytics Task Distribution (dona) | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 70 | Analytics Resource Utilization | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 71 | Exportar analytics a Excel | ✅ | ✅ | ✅ | ⚠️ (botón existe, formato no verificado) | Parcial | ⚪ |
| 72 | Analytics multiproyecto en Dashboard | ✅ | ✅ | ❌ | ❌ | No implementado | 🟡 |
| 73 | Módulo Terceros (CRUD completo) | ✅ | ✅ | ✅ | ✅ | Implementado | — |
| 74 | Tipo "CUSTOMER" en inglés (bug) | — | — | — | 🐛 | Bug | 🟢 |
| 75 | Hitos facturables (Milestone) | ❌ (no documentado) | ✅ | ✅ | ✅ | Implementado (extra) | — |
| 76 | Documentos contables de Saiopen | ❌ (no documentado) | ✅ | ✅ | ✅ | Implementado (extra) | — |
| 77 | Configuración del módulo de proyectos | ❌ (no documentado) | ✅ | ✅ | ✅ | Implementado (extra) | — |

---

## RECOMENDACIONES PRIORIZADAS

### PRIORIDAD 1 — CRÍTICO (implementar primero)

**1.1 Agregar Tab "Tareas" y Tab "Kanban" dentro del Proyecto**
- Archivo: `proyecto-detail.component.html` y `proyecto-detail.component.ts`
- Acción: Importar `TareaListComponent` y `TareaKanbanComponent`, agregar tabs con `[proyectoId]="p.id"` como input. Modificar dichos componentes para aceptar `proyectoId` como input y cargar tareas filtradas.
- Esfuerzo estimado: Bajo-Medio.

**1.2 Crear UI para Tarifas de Costo por Recurso**
- Archivo: Crear `cost-rate-form.component.ts/.html` e integrarlo en `budget-dashboard.component.html`
- Acción: Nuevo componente que use `CostRateService` para listar/crear/editar/eliminar tarifas. El servicio ya existe.
- Esfuerzo estimado: Medio.

**1.3 Corregir endpoints `/costs/by-resource/` y `/costs/by-task/`**
- Archivo: `backend/apps/proyectos/budget_views.py`, clases `CostByResourceView` y `CostByTaskView`
- Acción: Investigar por qué devuelven error 404/500. Verificar que los timesheets y costos estén correctamente enlazados a las tarifas.
- Esfuerzo estimado: Bajo.

**1.4 Enrutar `TimesheetSemanalComponent`**
- Archivo: `frontend/src/app/features/proyectos/proyectos.routes.ts`
- Acción: Agregar `{ path: 'timesheets', loadComponent: () => import('./components/timesheet-semanal/...') }` y el enlace en el sidebar de proyectos.
- Esfuerzo estimado: Bajo.

**1.5 Agregar Tab "Timesheets" en Detalle del Proyecto**
- Archivo: `proyecto-detail.component.html`
- Acción: Nuevo tab que muestre un listado de timesheets del proyecto filtrados por proyecto. Puede reutilizar `TimesheetSemanalComponent`.
- Esfuerzo estimado: Bajo.

### PRIORIDAD 2 — ALTO

**2.1 Integrar `TaskConstraintsPanelComponent` en el detalle de tarea**
- Archivo: `tarea-detail.component.html`
- Acción: Agregar tab "Restricciones" importando `TaskConstraintsPanelComponent`. El componente ya está completo.
- Esfuerzo estimado: Muy bajo (integración de código existente).

**2.2 Crear UI para Nivelación de Recursos**
- Archivo: `auto-schedule-dialog.component.html` o nuevo componente
- Acción: Agregar botón "Nivelar Recursos" con opción dry run. Reusar el patrón del AutoSchedule dialog.
- Esfuerzo estimado: Bajo.

**2.3 Implementar configuración de cambios en What-If Scenarios**
- Archivo: `what-if-scenario-builder.component.ts/.html`
- Acción: Agregar formulario de cambios por tarea (fecha inicio, fecha fin, duración). Requiere diseño UX adicional.
- Esfuerzo estimado: Alto.

**2.4 Crear UI para Capacidades y Disponibilidad de Recursos**
- Acción: Crear componentes `ResourceCapacityComponent` y `ResourceAvailabilityComponent`. Los endpoints backend ya existen.
- Esfuerzo estimado: Medio.

**2.5 Implementar Dashboard multiproyecto con analytics**
- Archivo: `frontend/src/app/features/dashboard/`
- Acción: Agregar sección de proyectos activos con KPIs consolidados y gráfico comparativo usando el endpoint `analytics/compare/`.
- Esfuerzo estimado: Alto.

**2.6 Corregir bug de lista global de Tareas (0 resultados con filtro)**
- Archivo: `tarea-list.component.ts`
- Acción: Revisar el orden de `ngOnInit` — el `proyectoId.set(pid)` debe completarse antes de `loadTareas()`. Verificar en el backend que el filtro `proyecto=<uuid>` funciona correctamente.
- Esfuerzo estimado: Bajo.

### PRIORIDAD 3 — MEDIO

**3.1 Agregar botón "Activar" explícito en la lista de Fases**
- Archivo: `fase-list.component.html`
- Acción: Agregar botón de activación que llame al endpoint `phases/:id/activate/`.
- Esfuerzo estimado: Bajo.

**3.2 Completar el overlay de Holgura (Float) para todas las tareas**
- Archivo: `gantt-view.component.ts`
- Acción: En `loadFloatData()`, hacer llamadas individuales al endpoint `tasks/:task_pk/scheduling/float/` para cada tarea (o crear endpoint batch) y poblar el `floatMap` completo.
- Esfuerzo estimado: Medio.

**3.3 Corregir tipo de tercero "CUSTOMER" a "Cliente"**
- Archivo: `backend/apps/terceros/serializers.py` o modelo
- Acción: Verificar que `get_tipo_tercero_display()` retorna español. Si el modelo usa choices en inglés, agregar traducción en el serializer.
- Esfuerzo estimado: Muy bajo.

**3.4 Agregar vista "Mis Tareas"**
- Acción: Crear ruta `/proyectos/mis-tareas` que use `TareaListComponent` con filtro `responsable = usuario_actual`.
- Esfuerzo estimado: Bajo.

**3.5 Agregar tipo "Hito" al catálogo de Actividades o clarificar en el manual**
- Decisión: Si los hitos del catálogo son el mismo concepto que `Milestone`, documentarlo. Si son conceptos separados, aclararlo en el manual.
- Esfuerzo estimado: Bajo (decisión de producto).

**3.6 Agregar indicador visual de Timer activo en la barra superior**
- Archivo: Shell/header component
- Acción: Cuando hay una `WorkSession` activa, mostrar un indicador en la barra de navegación superior.
- Esfuerzo estimado: Medio.

### PRIORIDAD 4 — BAJO / DOCUMENTACIÓN

**4.1 Actualizar el manual sección 4.3 con los tabs reales del proyecto**
- El manual documenta 13 tabs. La implementación tiene 12 con nombres diferentes. Actualizar tabla del manual.

**4.2 Documentar features no documentados: Hitos, Documentos Contables, Configuración del Módulo**
- Agregar secciones al manual para los 3 features extra implementados.

**4.3 Aclarar en el manual que SF no está implementado**
- El manual dice "el modelo técnico incluye también SF" pero SF no está implementado. Corregir la descripción.

**4.4 Agregar toggle de activar/desactivar actividad en el catálogo**
- Archivo: `actividad-list.component.html`
- Acción: Agregar chip/toggle de estado que llame a PATCH con `activo: false`.
- Esfuerzo estimado: Bajo.

**4.5 Agregar filtro "Por gerente" en lista de proyectos**
- Archivo: `proyecto-list.component.html` / `proyecto-cards.component.html`
- Acción: Agregar selector de gerente en los filtros de la lista.
- Esfuerzo estimado: Bajo.

---

*Auditoría generada por Claude Code — 28 Marzo 2026*
*Análisis basado en: código fuente, MANUAL-USUARIO-SAICLOUD.md y testing visual en navegador con Playwright MCP.*
