# ERRORES ENCONTRADOS — Testing Browser Saicloud

**Fecha de testing:** 28 Marzo 2026
**Tester:** Juan David (CEO/CTO — ValMen Tech)
**Entorno:** http://localhost:4200 (frontend) / http://localhost:8000 (backend)
**Proyectos demo:** Ferretería El Constructor + Droguería SaludTotal
**Versión:** Feature #7 — Budget & Cost Tracking (936 tests pasando)

---

## RESUMEN EJECUTIVO

| Pantalla / Módulo | Crítico | Alto | Medio | Bajo | Total |
|---|:---:|:---:|:---:|:---:|:---:|
| Auth / Login | — | — | — | — | 0 |
| Navegación / Sidebar | — | — | — | — | 0 |
| Terceros | — | — | 1 | — | 1 |
| Usuarios / Tarifas | — | — | — | — | 0 |
| Catálogo de Actividades | — | — | — | — | 0 |
| Proyectos (lista + cards) | — | — | — | — | 0 |
| Fases | — | 1 | — | — | 1 |
| Tareas (lista + kanban) | — | — | — | — | 0 |
| Detalle de Tarea | — | — | — | — | 0 |
| Dependencias | — | — | — | — | 0 |
| Gantt | — | — | — | — | 0 |
| Timesheets / Timer | — | — | — | — | 0 |
| Resource Management | — | — | 1 | — | 1 |
| Analytics | — | 1 | 1 | — | 2 |
| Advanced Scheduling | — | — | — | — | 0 |
| Budget & Cost Tracking | — | — | — | 1 | 1 |
| **TOTAL** | **0** | **2** | **3** | **1** | **6** |

---

## CHECKLIST DE PANTALLAS A REVISAR

> Marcar ✅ cuando se verifica OK, ❌ cuando se encuentra error (documentar abajo).

### FASE 1: Setup Inicial y Navegación

- [ ] Login: `http://localhost:4200/login` — credenciales admin/admin
- [ ] Redirección post-login al selector de módulos
- [ ] Selector de módulos: se muestra SaiCloud correctamente
- [ ] Sidebar: ítems de navegación visibles y activos
- [ ] Toggle Dark Mode / Light Mode
- [ ] Perfil de usuario: datos cargados correctamente
- [ ] Logout y re-login

### FASE 2: Terceros (Clientes / Proveedores)

- [ ] Lista de terceros (estado vacío → empty state con icono + mensaje + botón)
- [ ] Formulario crear tercero: todos los campos visibles (nombre, NIT, tipo, email, teléfono, ciudad)
- [ ] Validaciones del formulario (NIT requerido, email con formato)
- [ ] **Crear:** Ferretería El Constructor S.A.S — NIT: 900.234.567-1 — tipo: cliente
- [ ] **Crear:** Droguería SaludTotal Ltda — NIT: 800.456.789-3 — tipo: cliente
- [ ] Lista con 2 terceros: paginación, columnas correctas
- [ ] Editar tercero: cambios se guardan
- [ ] Detalle de tercero: datos completos
- [ ] Eliminar tercero: dialog de confirmación (MatDialog, NO confirm() nativo)

### FASE 3: Usuarios y Tarifas de Costo

- [ ] Lista de usuarios en admin
- [ ] Crear 10 usuarios (ver PROYECTO-DEMO-A-FERRETERIA.md y PROYECTO-DEMO-B-DROGUERIA.md)
- [ ] Asignar tarifas de costo por recurso (endpoint `/api/v1/projects/resources/cost-rates/`)
- [ ] Validación: no se permite solapamiento de tarifas del mismo recurso
- [ ] Lista de tarifas por recurso

### FASE 4: Catálogo de Actividades

- [ ] Lista de actividades (empty state si vacío)
- [ ] Crear actividad tipo **horas** (ej: "Desarrollo Backend")
- [ ] Crear actividad tipo **unidad** (ej: "Demolición", unidad: m²)
- [ ] Crear actividad tipo **porcentaje** (ej: "Avance General")
- [ ] Crear actividad tipo **hito** (ej: "Entrega de Planos")
- [ ] Crear 20 actividades para cubrir ambos proyectos demo
- [ ] Búsqueda / filtro de actividades
- [ ] Editar actividad
- [ ] Eliminar actividad (con confirmación)

### FASE 5: Proyecto A — Ferretería El Constructor

#### 5.1 Proyecto
- [ ] Lista de proyectos (empty state inicial)
- [ ] Formulario crear proyecto: nombre, descripción, fechas, tercero, estado
- [ ] Crear: "Remodelación y Ampliación — Ferretería El Constructor"
- [ ] Vista cards del proyecto
- [ ] Vista lista del proyecto
- [ ] Detalle del proyecto: header con nombre, estado, fechas, progreso
- [ ] Tabs disponibles en detalle (Fases, Tareas, Gantt, Recursos, Analytics, Scheduling, Baselines, Escenarios, Presupuesto)
- [ ] Editar proyecto
- [ ] Cambiar estado del proyecto

#### 5.2 Fases
- [ ] Tab Fases: empty state con botón Agregar
- [ ] Crear Fase 1: "Planificación y Diseño" (fechas: 2026-02-02 a 2026-02-20)
- [ ] Crear Fase 2: "Estructura y Obra Civil" (2026-02-21 a 2026-03-21)
- [ ] Crear Fase 3: "Instalaciones" (2026-03-22 a 2026-04-05)
- [ ] Crear Fase 4: "Acabados y Entrega" (2026-04-06 a 2026-04-11)
- [ ] Reordenar fases (drag o botones de orden)
- [ ] Activar Fase 2 (botón activar visible, solo una activa a la vez)
- [ ] Progreso de fase se actualiza automáticamente

#### 5.3 Tareas
- [ ] Tab Tareas: empty state
- [ ] Crear T1-T4 en Fase 1 (ver estructura en PROYECTO-DEMO-A)
- [ ] Crear T5-T8 en Fase 2
- [ ] Crear T9-T11 en Fase 3
- [ ] Crear T12-T14 en Fase 4
- [ ] Vista lista de tareas: filtro por fase funciona
- [ ] Vista Kanban: columnas todo/en_progreso/completado
- [ ] Kanban filtro de fase: dropdown funciona
- [ ] Detalle de tarea: UI adaptativa según tipo de actividad
  - [ ] Tarea con actividad **horas** → muestra cronómetro + historial timesheets
  - [ ] Tarea con actividad **unidad** → edición inline de cantidad completada
  - [ ] Tarea **hito** → checkbox completado
  - [ ] Tarea **sin actividad** → solo selector de estado
- [ ] Cambiar estado de tarea → progreso de fase se actualiza
- [ ] Marcar T1, T2, T3, T4, T5 como completadas

#### 5.4 Dependencias
- [ ] Crear 12 dependencias (ver tabla en PROYECTO-DEMO-A)
- [ ] Tipos FS y SS funcionan correctamente
- [ ] Lag time se guarda y muestra
- [ ] Tabla de dependencias: lista correcta con lag
- [ ] Error de dependencia circular: mensaje claro

#### 5.5 Gantt
- [ ] Tab Gantt: barras visibles para tareas con fechas
- [ ] Barra de Gantt proporcional a duración
- [ ] Dependencias visibles como líneas/flechas
- [ ] Scroll horizontal y zoom
- [ ] **Overlay Ruta crítica**: toggle activa/desactiva — tareas críticas en rojo
- [ ] **Overlay Holgura**: toggle activa — badges de días de float
- [ ] Auto-Schedule (ASAP): previsualización → aplicar
- [ ] Auto-Schedule respeta restricciones
- [ ] **Overlay Baseline**: toggle activa (después de crear baseline)

#### 5.6 Timesheets y Timer
- [ ] Abrir detalle de tarea con actividad horas (T1)
- [ ] Registrar timesheet manual: fecha, horas, descripción
- [ ] Iniciar timer (cronómetro visible y corriendo)
- [ ] Detener timer → entrada guardada automáticamente
- [ ] Historial de timesheets: lista ordenada
- [ ] Editar timesheet existente
- [ ] Eliminar timesheet

#### 5.7 Resource Management
- [ ] Tab Recursos en detalle de proyecto (o Task)
- [ ] Asignar Carlos Mendoza a T1 (100%)
- [ ] Asignar Luisa Fernández a T1 y T2
- [ ] Check sobreasignación: `/check-overallocation/`
- [ ] Vista workload del equipo
- [ ] Calendario por usuario

#### 5.8 Analytics
- [ ] Tab Analytics: carga sin error
- [ ] KPIs: completud, tasa a tiempo, horas, eficiencia visibles
- [ ] Burn Down Chart: visible con datos
- [ ] Velocity Chart: visible
- [ ] Task Distribution (dona): visible
- [ ] Resource Utilization (barras): visible
- [ ] Exportar Excel: descarga correctamente

#### 5.9 Advanced Scheduling
- [ ] Botón Scheduling visible en header del proyecto
- [ ] Auto-Schedule ASAP: dialog abre, previsualiza, aplica
- [ ] Restricciones: agregar SNET a T9 (no antes del 22-Mar)
- [ ] Ver restricciones en lista
- [ ] **Crear Baseline** "Plan Original"
- [ ] Baseline aparece en tab Baselines
- [ ] Comparar baseline: tabla fechas baseline vs actual
- [ ] **Escenario What-If** "Refuerzo de equipo Fase 3": crear, correr, ver resultado

#### 5.10 Budget & Cost Tracking
- [ ] Tab Presupuesto: formulario visible
- [ ] Crear presupuesto: total_labor $62M, total_expenses $23M, contingency 10%
- [ ] Guardar presupuesto (estado borrador)
- [ ] **Aprobar presupuesto**: botón aprobar visible
- [ ] Post-aprobación: formulario NO editable (bloqueado)
- [ ] Crear tarifa para Carlos Mendoza: $120,000/h
- [ ] Registrar 9 gastos (ver lista en PROYECTO-DEMO-A)
- [ ] Aprobar gastos aprobables (distintos usuarios si aplica)
- [ ] Dashboard: summary cards visibles (total, labor, gastos, saldo)
- [ ] Alertas de presupuesto: colores correctos según umbral
- [ ] Cost breakdown por recurso: tabla visible
- [ ] Cost breakdown por tarea: tabla visible
- [ ] **EVM Metrics**: BAC, PV, EV, AC, CPI, SPI visibles
- [ ] CPI ~0.66 (rojo), SPI ~0.75 (rojo) — valores esperados
- [ ] Invoice data: GET genera líneas de labor + gastos facturables

### FASE 6: Proyecto B — Droguería SaludTotal

- [ ] Crear proyecto B con todos los datos (ver PROYECTO-DEMO-B)
- [ ] Crear 5 fases con fechas correctas
- [ ] Crear 19 tareas con actividades asignadas
- [ ] Crear 18 dependencias (incluyendo SS)
- [ ] Registrar timesheets en fases 1 y 2 (completadas)
- [ ] Marcar tareas fases 1 y 2 como completadas
- [ ] Crear 2 baselines
- [ ] Crear 2 escenarios what-if
- [ ] Crear presupuesto: labor $95M, gastos $25M, contingencia 8%
- [ ] Registrar 10 gastos
- [ ] EVM: CPI ~1.16 (verde), SPI ~1.00 (verde) — verificar

### FASE 7: Verificación Cruzada

- [ ] Comparar proyectos en Analytics (`POST /api/v1/projects/analytics/compare/`)
- [ ] Exportar Excel ambos proyectos
- [ ] Workload global: ambos proyectos visibles en calendario de equipo
- [ ] Invoice data Proyecto B: labor en tarifas correctas
- [ ] Multi-tenant: datos de empresa no se mezclan (si hay 2 empresas en demo)
- [ ] Gestión semanal snapshot: `python manage.py budget_weekly_snapshot --dry-run`

---

## ERRORES DOCUMENTADOS

> Usar el template a continuación para cada error encontrado.
> Incrementar el contador: ERROR-001, ERROR-002, etc.

### Template

#### ERROR-XXX: [Título corto]

| Campo | Valor |
|---|---|
| **ID** | ERROR-XXX |
| **Fecha** | 2026-03-28 |
| **Pantalla** | `/ruta/en/el/app` |
| **Componente Angular** | `nombre-component.component.ts` |
| **Endpoint API** | `GET/POST /api/v1/...` |
| **Tipo** | Visual / Funcional / Datos / Performance / UX |
| **Severidad** | Crítico / Alto / Medio / Bajo |
| **Estado** | Nuevo / En revisión / Corregido |

**Descripción:**
Descripción detallada de qué falla y cuál es el impacto.

**Pasos para reproducir:**
1. Ir a `http://localhost:4200/...`
2. Hacer clic en `...`
3. Ingresar `...`
4. Observar `...`

**Resultado esperado:**
Qué debería ocurrir según el diseño/especificación.

**Resultado actual:**
Qué está pasando realmente.

**Contexto adicional:**
- Navegador: Chrome 123 / Safari 17 / Firefox 124
- Consola: `[pegar error de consola si aplica]`
- Network: `[status code + response si aplica]`
- Screenshot: `docs/testing/screenshots/error-XXX.png`

---

---

#### ERROR-001: Gráficos de Analytics vacíos (sin renderizar)

| Campo | Valor |
|---|---|
| **ID** | ERROR-001 |
| **Fecha** | 2026-03-28 |
| **Pantalla** | `/proyectos/{id}` → tab Analytics |
| **Componente Angular** | `project-analytics.component` (tab Analytics) |
| **Endpoint API** | `GET /api/v1/projects/{id}/analytics/` |
| **Tipo** | Visual / Funcional |
| **Severidad** | Alto |
| **Estado** | Nuevo |

**Descripción:**
El tab Analytics carga los KPIs de resumen correctamente (Completud, On-Time, Velocidad, Horas Burn Rate), pero los 4 gráficos de la sección inferior aparecen vacíos: paneles en blanco sin datos. Afecta: Burn Down Chart, Velocidad del Equipo, Distribución de Tareas (dona) y Utilización de Recursos (barras). El botón "Exportar" está visible pero no se probó.

**Pasos para reproducir:**
1. Ir a `http://localhost:4200/proyectos`
2. Hacer clic en PRY-003 (Ferretería El Constructor)
3. Hacer clic en el tab **Analytics**
4. Observar la sección inferior (Burn Down, Velocidad del equipo, Distribución de tareas, Utilización de recursos)

**Resultado esperado:**
Los 4 gráficos deben mostrar datos: Burn Down con curva de horas registradas vs planificadas, gráfico de velocidad semanal, dona de distribución de estados, barras de utilización por recurso.

**Resultado actual:**
Los 4 paneles aparecen como rectángulos vacíos (imagen en blanco). Los KPIs superiores (36% completud, 0% on-time, 5/sem velocidad, 178.8h/sem burn rate) sí se muestran correctamente.

**Contexto adicional:**
- Navegador: Chrome (Playwright)
- El proyecto PRY-003 tiene 257 timesheet entries, 14 tareas y 5 resource assignments
- Mismo comportamiento esperado en PRY-004
- Screenshot: `pry003-analytics.png`

---

#### ERROR-002: Avance de fases activas muestra 0% en vez del valor real

| Campo | Valor |
|---|---|
| **ID** | ERROR-002 |
| **Fecha** | 2026-03-28 |
| **Pantalla** | `/proyectos/{id}` → tab Fases |
| **Componente Angular** | `project-phases.component` (tab Fases) |
| **Endpoint API** | `GET /api/v1/projects/{id}/phases/` |
| **Tipo** | Datos |
| **Severidad** | Alto |
| **Estado** | Nuevo |

**Descripción:**
Las fases en estado "Activa" muestran 0% de avance en la tabla del tab Fases, aunque las tareas asociadas tienen `porcentaje_completado` configurado (ej: T10 al 82%, T11 al 60%, T12 al 50%, T13 al 70%). Las fases "Completada" muestran 100% correctamente. El problema afecta únicamente a las fases con estado `active`.

**Pasos para reproducir:**
1. Ir a `http://localhost:4200/proyectos`
2. Hacer clic en PRY-004 (Droguería SaludTotal)
3. Hacer clic en el tab **Fases (5)**
4. Observar la columna "Avance" para la Fase 3 (Frontend Development — Activa)

**Resultado esperado:**
Fase 3 debería mostrar ~65% de avance (promedio de T10:82%, T11:60%, T12:50%, T13:70%).

**Resultado actual:**
Fase 3 (Frontend Development) muestra 0% a pesar de tener 4 tareas en progreso.

**Contexto adicional:**
- Backend INFO log al crear tareas: `"Avance fase recalculado desde tareas"` — sugiere que el signal sí se ejecuta
- Posible causa: el signal recalcula `porcentaje_avance` desde tareas con estado `completed` únicamente, ignorando tareas `in_progress`
- Fases completadas (F1, F2 en PRY-004) sí muestran 100% correctamente
- Archivo a revisar: señal/receiver en `apps/proyectos/signals.py` o `services.py`

---

#### ERROR-003: Tipo de tercero "CUSTOMER" en inglés (inconsistencia i18n)

| Campo | Valor |
|---|---|
| **ID** | ERROR-003 |
| **Fecha** | 2026-03-28 |
| **Pantalla** | `/terceros` |
| **Componente Angular** | `tercero-list.component` (columna Tipo) |
| **Endpoint API** | `GET /api/v1/terceros/` |
| **Tipo** | Visual / i18n |
| **Severidad** | Medio |
| **Estado** | Nuevo |

**Descripción:**
En la lista de Terceros, la columna "Tipo" muestra el valor sin traducir para el tercero "Inversiones del Valle S.A.S": aparece como "CUSTOMER" (inglés) en lugar de "CLIENTE" (español). Los otros dos terceros muestran "CLIENTE" correctamente con pill/badge estilizado.

**Pasos para reproducir:**
1. Ir a `http://localhost:4200/terceros`
2. Observar la columna "Tipo" para cada registro

**Resultado esperado:**
Todos los terceros tipo cliente deben mostrar "CLIENTE" con el badge azul uniforme.

**Resultado actual:**
- "Droguería SaludTotal S.A.S" → badge "CLIENTE" ✅
- "Ferretería El Constructor S.A.S" → badge "CLIENTE" ✅
- "Inversiones del Valle S.A.S" → texto plano "CUSTOMER" ❌ (sin badge, en inglés)

**Contexto adicional:**
- "Inversiones del Valle" fue creado previamente (PRY-001 preexistente). Los otros dos terceros se crearon durante esta sesión
- Posible causa: el campo `tipo_tercero` de "Inversiones del Valle" tiene un valor diferente en BD (`customer` vs `cliente` o enum distinto)
- Screenshot: `terceros-list.png`

---

#### ERROR-004: NIT/ID del cliente en detalle de proyecto muestra UUID interno

| Campo | Valor |
|---|---|
| **ID** | ERROR-004 |
| **Fecha** | 2026-03-28 |
| **Pantalla** | `/proyectos/{id}` → tab General → sección Cliente |
| **Componente Angular** | `project-detail.component` (sección Cliente) |
| **Endpoint API** | `GET /api/v1/projects/{id}/` |
| **Tipo** | Datos / UX |
| **Severidad** | Medio |
| **Estado** | Nuevo |

**Descripción:**
En el detalle del proyecto, la sección "Cliente" muestra el campo "NIT / ID" con el UUID interno de la tabla `terceros` en lugar del número de NIT real del cliente. Ejemplo: muestra `3d373c7f-7277-4d03-b213-516a3cf407d2` en lugar de `900456789`.

**Pasos para reproducir:**
1. Ir a `http://localhost:4200/proyectos`
2. Hacer clic en PRY-003 (Ferretería El Constructor)
3. Observar la sección "CLIENTE" → campo "NIT / ID"

**Resultado esperado:**
El campo "NIT / ID" debe mostrar el número de identificación tributaria del cliente: `900456789-0` (o en el formato configurado).

**Resultado actual:**
El campo muestra el UUID interno del registro en la tabla `terceros`: `3d373c7f-7277-4d03-b213-516a3cf407d2`.

**Contexto adicional:**
- Causa raíz: el campo `cliente_id` del modelo `Project` se guardó con el UUID del `Tercero` en lugar del `numero_identificacion`
- El modelo `Project` tiene `cliente_id` (CharField) y `cliente_nombre` — se usó el UUID como cliente_id al crear el proyecto
- Fix: al crear proyectos via API, usar `numero_identificacion` del tercero como `cliente_id`, no su PK
- Afecta PRY-003 y PRY-004 (ambos creados durante esta sesión)

---

#### ERROR-005: Varianza Horas Burn Rate muestra -100.0% (cálculo incorrecto)

| Campo | Valor |
|---|---|
| **ID** | ERROR-005 |
| **Fecha** | 2026-03-28 |
| **Pantalla** | `/proyectos/{id}` → tab Analytics → KPI "Horas Burn Rate" |
| **Componente Angular** | `project-analytics.component` (tarjeta Horas Burn Rate) |
| **Endpoint API** | `GET /api/v1/projects/{id}/analytics/` |
| **Tipo** | Datos |
| **Severidad** | Medio |
| **Estado** | Nuevo |

**Descripción:**
El KPI "Horas Burn Rate" muestra "178.8h/sem" con una varianza de "-100.0%". Una varianza de -100% es matemáticamente imposible en el contexto de horas (indicaría 0 horas planificadas como base), o hay un error en la fórmula de cálculo. No queda claro si el valor refleja una eficiencia negativa o un error de división por cero.

**Pasos para reproducir:**
1. Ir a `/proyectos/{id-pry-003}` → tab Analytics
2. Observar tarjeta "Horas Burn Rate"

**Resultado esperado:**
La varianza debería mostrar un porcentaje coherente con las horas planificadas vs registradas (ej: "+15% sobre lo planificado" o "-5% bajo lo planificado"). Si el denominador es 0, mostrar "N/A" en lugar de "-100.0%".

**Resultado actual:**
"178,8h/sem — Varianza: -100.0%" en color verde (contradicción visual: verde sugiere bueno pero -100% es extremo).

**Contexto adicional:**
- Screenshot: `pry003-analytics.png`
- Archivo a revisar: servicio de cálculo de analytics en `apps/proyectos/services.py` (función de burn rate)

---

#### ERROR-006: Tab "Actividades" en detalle de proyecto no muestra las tareas del proyecto

| Campo | Valor |
|---|---|
| **ID** | ERROR-006 |
| **Fecha** | 2026-03-28 |
| **Pantalla** | `/proyectos/{id}` → tab Actividades |
| **Componente Angular** | `project-activities.component` (tab Actividades) |
| **Endpoint API** | `GET /api/v1/projects/{id}/activities/` |
| **Tipo** | UX / Funcional |
| **Severidad** | Bajo |
| **Estado** | Nuevo |

**Descripción:**
El tab "Actividades" en el detalle del proyecto muestra "No hay actividades asignadas a este proyecto" aunque el proyecto tiene 14 tareas (PRY-003). El tab parece estar mostrando `ProjectActivity` (actividades del catálogo Saiopen asignadas al proyecto), no las tareas (`Task`) del proyecto. Esto genera confusión al usuario que esperaría ver el historial de actividad del proyecto.

**Pasos para reproducir:**
1. Ir a `/proyectos/{id-pry-003}` → tab Actividades
2. Observar el empty state

**Resultado esperado:**
El usuario espera ver actividad reciente del proyecto: tareas, timesheets, cambios de estado, comentarios. O bien, si es el catálogo de actividades Saiopen, que haya al menos una explicación de para qué sirve este tab y cómo añadir actividades.

**Resultado actual:**
Empty state "No hay actividades asignadas a este proyecto" con botón "Asignar actividad". No hay contexto que explique que se refiere a actividades del catálogo Saiopen, no a las tareas del proyecto.

**Contexto adicional:**
- El modelo `ProjectActivity` es diferente de `Task`. El tab muestra `ProjectActivity`, no `Task`
- Sugerencia: renombrar el tab a "Catálogo Saiopen" o "Actividades Saiopen" para diferenciarlo de las tareas
- O agregar un subtítulo explicativo en el empty state

---

*(Fin de errores de la sesión 2026-03-28)*

---

## ERRORES PRE-EXISTENTES CONOCIDOS

> Estos errores ya están documentados. No volver a reportarlos como nuevos.

### PRE-001: 6 Test Failures Backend (no relacionados con Budget)

| Campo | Valor |
|---|---|
| **ID** | PRE-001 |
| **Fecha detectado** | 28 Marzo 2026 |
| **Tipo** | Tests |
| **Severidad** | Bajo (no afecta funcionalidad en browser) |
| **Estado** | Conocido / Pendiente de corrección |

**Descripción:**
6 tests del backend fallan en el suite completo. No están relacionados con Feature #7 (Budget).
Total suite: 936 pasando + 6 failures pre-existentes.

**Referencia:** `CONTEXT.md` — "6 failures pre-existentes (no relacionados)"

---

### PRE-002: CSS Budget Warning en tarea-detail.component.scss

| Campo | Valor |
|---|---|
| **ID** | PRE-002 |
| **Fecha detectado** | 27 Marzo 2026 |
| **Tipo** | Build Warning |
| **Severidad** | Bajo (warning, no error — build exitoso) |
| **Estado** | Conocido / Pendiente de corrección |

**Descripción:**
`ng build --configuration=production` produce un warning de CSS budget en `tarea-detail.component.scss`.
El build completa exitosamente. No afecta funcionalidad.

**Referencia:** `CONTEXT.md` — "solo error pre-existente tarea-detail.scss budget"

---

## NOTAS DE TESTING

### Datos de acceso
```
URL Frontend:  http://localhost:4200
URL Backend:   http://localhost:8000
URL Admin:     http://localhost:8000/admin
Usuario:       admin
Contraseña:    admin
```

### Cómo verificar llamadas API en el navegador
1. Abrir Chrome DevTools: `F12` o `Ctrl+Shift+I`
2. Ir a pestaña **Network**
3. Filtrar por **Fetch/XHR**
4. Ejecutar la acción en la UI
5. Hacer clic en la request para ver:
   - Status code (200 ✅ / 400 ⚠️ / 500 ❌)
   - Request payload (lo que se envió)
   - Response body (lo que devolvió el API)

### Cómo revisar errores de consola
1. Abrir Chrome DevTools: `F12`
2. Ir a pestaña **Console**
3. Filtrar por **Errors** (botón rojo ❌)
4. Copiar el error completo incluyendo stack trace

### Cómo tomar screenshots para documentar
```
Mac:  Cmd+Shift+4 → seleccionar área
Win:  Win+Shift+S → seleccionar área
```
Guardar en: `docs/testing/screenshots/error-XXX-descripcion.png`

### Criterios de severidad
| Severidad | Criterio |
|---|---|
| **Crítico** | Bloquea flujo principal — no se puede continuar (login falla, crash, 500) |
| **Alto** | Feature importante no funciona pero hay workaround |
| **Medio** | Visual incorrecto o funcionalidad secundaria falla |
| **Bajo** | Cosmético, typo, mejora de UX menor |

### Cómo reportar bugs al equipo
1. Documentar en este archivo siguiendo el template
2. Agregar screenshot en `docs/testing/screenshots/`
3. Identificar archivo Angular/Django responsable si es posible
4. Priorizar por severidad antes de la próxima sesión de desarrollo

### Comandos útiles durante testing
```bash
# Ver logs del backend en tiempo real
cd backend && python manage.py runserver

# Verificar estado de la base de datos
python manage.py dbshell

# Snapshot semanal de presupuesto (dry-run)
python manage.py budget_weekly_snapshot --dry-run

# Correr tests después de cada corrección
python manage.py test apps.proyectos --verbosity=2
```

---

*Última actualización: 28 Marzo 2026*
*Archivo creado para testing de Feature #7 — Budget & Cost Tracking*
