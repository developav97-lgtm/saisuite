# CONTEXT.md - Estado del Proyecto Saicloud

**Ultima actualizacion:** 03 Abril 2026
**Sesion:** 6 Features — Licencias, IA en Chat, Manuales, AWS

---

## COMPLETADO (03 Abril 2026) — 6 Features Transversales

### F6: Sistema de Licencias con Paquetes
- 4 modelos nuevos: `LicensePackage`, `LicensePackageItem`, `MonthlyLicenseSnapshot`, `AIUsageLog`
- 3 services: `PackageService`, `AIUsageService`, `SnapshotService`
- `RenewalService.auto_generate_renewals()` — auto-genera renovaciones 5 dias antes de vencimiento
- API admin: CRUD paquetes, asignar/quitar de licencia, snapshots mensuales, uso IA
- 2 management commands: `auto_generate_renewals` (daily), `generate_monthly_snapshots` (monthly)
- Migracion: `0009_licensepackage_aiusagelog_licensepackageitem_and_more`

### F5: AI Token/Message Tracking
- `AIUsageService` integrado en `CfoVirtualService.ask()` — verifica quota antes, registra uso despues
- n8n workflow actualizado para retornar `usage` (prompt_tokens, completion_tokens, model) de OpenAI
- Endpoints: `GET /licenses/me/ai-usage/` y `/ai-usage/by-user/`

### F3: Asistente IA en Chat
- **Backend:** Campo `is_bot` en User + campo `bot_context` en Conversacion
- `BotResponseService` — procesa mensajes al bot, genera respuesta via CfoVirtualService
- Endpoint: `POST /api/v1/chat/conversaciones/bot/` con body `{ "context": "dashboard" }`
- WebSocket consumer dispara respuesta del bot en thread background
- Migraciones: `users.0006_user_is_bot`, `chat.0005_conversacion_bot_context`
- **Frontend:** `ChatStateService.openBot(context)`, `ChatService.crearConversacionBot()`
- Chat panel detecta bot conversations: icono `smart_toy`, nombre "CFO Virtual"
- Chat window: oculta uploads en bot, typing dice "Analizando...", estilo diferente para msgs bot
- Chat list: icono IA en lugar de avatar para conversaciones bot
- SaiDashboard ai-assistant: boton "Abrir chat completo" → `chatState.openBot('dashboard')`

### F4: Manual SaiDashboard
- `docs/manuales/MANUAL-SAIDASHBOARD-SAICLOUD.md` — 15 secciones basadas en codigo real
- Solo funcionalidades implementadas (verificado contra componentes y modelos)

### F1: Manual Agente Go
- `docs/manuales/MANUAL-AGENTE-SAICLOUD.md` — 11 secciones para usuario no tecnico
- Comandos CLI verificados contra `agent-go/cmd/agent/main.go`
- Incluye configuracion multi-empresa y solucion de problemas

### F2: AWS Infrastructure
- `docs/aws/AWS-INFRASTRUCTURE.md` — documento de tracking de recursos
- Pendiente: crear SQS queues e IAM user (requiere interaccion usuario)

### Archivos creados/modificados esta sesion
**Backend:**
- `backend/apps/companies/models.py` — 4 modelos nuevos
- `backend/apps/companies/services.py` — PackageService, AIUsageService, SnapshotService, RenewalService enhancement
- `backend/apps/companies/serializers.py` — 7 serializers nuevos
- `backend/apps/companies/views.py` — 8 views nuevas
- `backend/apps/companies/urls.py` — rutas actualizadas
- `backend/apps/companies/admin_urls.py` — rutas admin actualizadas
- `backend/apps/companies/package_urls.py` — NUEVO
- `backend/apps/companies/admin.py` — 4 modelos registrados
- `backend/apps/companies/management/commands/auto_generate_renewals.py` — NUEVO
- `backend/apps/companies/management/commands/generate_monthly_snapshots.py` — NUEVO
- `backend/apps/users/models.py` — is_bot field
- `backend/apps/chat/models.py` — bot_context field
- `backend/apps/chat/services.py` — obtener_o_crear_conversacion_bot, BotResponseService
- `backend/apps/chat/views.py` — BotConversacionView
- `backend/apps/chat/urls.py` — ruta bot
- `backend/apps/chat/consumers.py` — trigger bot response
- `backend/apps/dashboard/services.py` — CfoVirtualService con quota + usage tracking
- `backend/apps/dashboard/views.py` — user param a CfoVirtualService
- `backend/config/urls.py` — ruta admin/packages/
- `n8n/workflows/cfo-virtual.json` — retorna usage tokens

**Frontend:**
- `frontend/src/app/core/services/chat-state.service.ts` — requestedBotContext, openBot()
- `frontend/src/app/core/components/shell/shell.component.html` — openBotContext binding
- `frontend/src/app/features/chat/models/chat.models.ts` — bot_context field
- `frontend/src/app/features/chat/services/chat.service.ts` — crearConversacionBot()
- `frontend/src/app/features/chat/components/chat-panel/` — bot conversation handling
- `frontend/src/app/features/chat/components/chat-list/` — bot styling
- `frontend/src/app/features/chat/components/chat-window/` — bot UI differences
- `frontend/src/app/features/saidashboard/components/ai-assistant/` — openFullChat()

**Docs:**
- `docs/manuales/MANUAL-AGENTE-SAICLOUD.md` — NUEVO
- `docs/manuales/MANUAL-SAIDASHBOARD-SAICLOUD.md` — NUEVO
- `docs/aws/AWS-INFRASTRUCTURE.md` — NUEVO

---

## COMPLETADO (03 Abril 2026) — SaiDashboard: Pendientes post-agentes A/B/C

### 1. Sidebar — Navegación SaiDashboard
- Agregado `SaiDashboard` al `HOME_NAV` (ícono `bar_chart`)
- Creado `SAIDASHBOARD_NAV` con "Mis Dashboards" y "Nuevo Dashboard"
- `detectModule()` reconoce `/saidashboard`
- Archivo: `frontend/.../sidebar.component.ts`

### 2. CFO Virtual — Endpoint Backend + Workflow n8n
- `CfoVirtualService` en `services.py`: llama webhook n8n con contexto financiero (últimos 12 meses por título contable)
- `CfoVirtualView` en `views.py`: `POST /api/v1/dashboard/cfo-virtual/`
- Workflow n8n importado: `n8n/workflows/cfo-virtual.json` — Webhook → OpenAI gpt-4o-mini → response
- **Modelo IA: OpenAI gpt-4o-mini** (no Anthropic — DEC-046)
- Credencial configurada en n8n como "Header Auth" (no `$env` — más seguro)
- API key en `.env` raíz (gitignored): `OPENAI_API_KEY`
- `requests==2.32.3` agregado a `requirements.txt` e instalado en imagen
- n8n migrado de SQLite → PostgreSQL (schema `n8n`) para evitar timeouts
- Prueba exitosa: `POST /webhook/cfo-virtual` retorna análisis financiero real

### 3. Tests Frontend — 64/64 pasando
- 4 servicios: 100% cobertura de métodos HTTP
- 4 componentes: kpi-card, trial-banner, dashboard-list, ai-assistant
- `tsconfig.spec.saidashboard.json` para ejecutar aislados
- Corregido error pre-existente en `tercero.service.spec.ts`

### 4. Validación 4x4 — Aprobada con fixes
- Desktop Light ✅ | Desktop Dark ✅ | Mobile Light ✅ | Mobile Dark ✅
- **Fixes aplicados:**
  - Topbar action buttons: `44x44px` mínimo en mobile (afecta todos los módulos)
  - Sidebar nav items: `min-height: 44px` (afecta todos los módulos)
  - Dashboard-list header buttons: `min-height: 44px` en mobile
  - Colores hardcodeados → `var(--sc-warning)` y `var(--sc-error)`

### Pendientes menores (no bloqueantes)
- ⏳ Test manual: segunda activación de trial debe retornar error "prueba ya utilizada"
- ⏳ Test manual: Export PDF genera archivo descargable
- ⏳ Test backend: `python manage.py test apps.contabilidad apps.dashboard` (requiere Docker)

### Archivos modificados esta sesión (SaiDashboard)
- `frontend/src/app/core/components/sidebar/sidebar.component.ts` — nav SaiDashboard
- `frontend/src/app/core/components/sidebar/sidebar.component.scss` — touch targets
- `frontend/src/app/core/components/topbar/topbar.component.scss` — touch targets mobile
- `backend/apps/dashboard/services.py` — CfoVirtualService
- `backend/apps/dashboard/views.py` — CfoVirtualView
- `backend/apps/dashboard/urls.py` — ruta cfo-virtual/
- `backend/requirements.txt` — requests==2.32.3
- `n8n/workflows/cfo-virtual.json` — workflow OpenAI
- `docker-compose.yml` — n8n con PostgreSQL + OPENAI_API_KEY
- `.env` (raíz, gitignored) — OPENAI_API_KEY
- `frontend/.../dashboard-list.component.scss` — touch targets + colores
- `frontend/src/app/features/saidashboard/services/*.spec.ts` — 4 specs servicios
- `frontend/src/app/features/saidashboard/components/*/**.spec.ts` — 4 specs componentes
- `frontend/tsconfig.spec.saidashboard.json` — tsconfig aislado para tests
- `DECISIONS.md` — DEC-046 (OpenAI en lugar de Anthropic)

---

## ✅ COMPLETADO (03 Abril 2026) — Correcciones UX/Mobile Multi-módulo

### What-If Scenario Builder
- **Fix datepicker**: Material datepicker no funcionaba dentro de `@else` en `mat-form-field`. Solución: separar en dos `mat-form-field` completos (uno en `@if`, otro en `@else`).
- **Fix serialización fecha**: `createScenario()` convierte `Date` → `YYYY-MM-DD` string antes de enviar al backend.
- **Fix tabla escenarios**: columna Estado centrada + tamaño fijo (`flex: 0 0 140px`); columna Impacto alineada a la izquierda.

### Tarea Detail — Responsive
- Sidebar: 320px → 280px, breakpoint 900px → 1200px
- `td-body` y `td-main`: añadido `min-width: 0; overflow: hidden` para respetar grid `1fr`.
- `float-indicator`: cambiado a `display: block; max-width: 100%` para evitar que "HOLGURA" desborde en mobile.

### Restricciones de Tarea (Task Constraints)
- **Fix validation error**: backend usa valores en minúscula (`asap`, `alap`, `must_start_on`, etc.) pero frontend enviaba mayúsculas. Corregido `ConstraintType` y todos los `CONSTRAINT_OPTIONS` a lowercase.

### Actividades del Proyecto (tab Actividades)
- **Fix badge "Mano de obra"**: backend renombró el valor a `'labor'` (migración 0013). Corregida clase CSS `&--mano_obra` → `&--labor`.
- Columnas Tipo, Unidad, Cant. plan/ejec., Avance: centradas con `apl-col-center`.
- Texto "Presupuesto total" en dark mode: cambiado de color hardcodeado a `var(--sc-text-muted)`.

### Terceros — Listado Mobile
- Tabla envuelta en `div.table-responsive` + `min-width: 700px`.
- Columnas con `flex: 0 0` via `:host ::ng-deep` para que no se compriman.
- Columna acciones: `flex: 0 0 112px; flex-shrink: 0` — ambos botones (editar + eliminar) siempre visibles.
- `.tc-nombre__text`: `white-space: nowrap; overflow: hidden; text-overflow: ellipsis`.

### QuickAccess Modal — Editar Tercero / Usuario
- **Root cause**: `NgComponentOutlet` no inyecta `ActivatedRoute` con params de URL.
- **Fix**: `QuickAccessNavigatorService` ahora almacena la URL interceptada y expone `getParam(name)` que extrae params por nombre del patrón de ruta.
- Aplicado en `TerceroFormComponent` y `UserFormComponent`:
  ```typescript
  const id = this.navigator.isActive
    ? this.navigator.getParam('id')
    : this.route.snapshot.paramMap.get('id');
  ```

### Consecutivos (Admin) — Listado Mobile
- Tabla usa `appResponsiveTable` directive (no envolver manualmente — la directiva ya lo hace).
- `min-width: 950px` en `.cl-table` via `:host ::ng-deep` para superar la especificidad del global `600px`.
- Columnas con `flex: 0 0` y `min-width` en `:host ::ng-deep` para que se apliquen.
- Filtros mobile: buscador ocupa fila completa (`flex-basis: 100%`), Tipo y Estado comparten la segunda fila (`flex: 1`).

### Archivos modificados esta sesión
- `frontend/.../what-if-scenario-builder.component.html` — datepicker separado por ramas
- `frontend/.../what-if-scenario-builder.component.ts` — serialización Date→string
- `frontend/.../what-if-scenario-builder.component.scss` — columna Estado centrada
- `frontend/.../tarea-detail.component.scss` — sidebar responsive
- `frontend/.../float-indicator.component.ts` — `:host` block
- `frontend/.../scheduling.model.ts` — ConstraintType lowercase
- `frontend/.../task-constraints-panel.component.ts` — CONSTRAINT_OPTIONS lowercase
- `frontend/.../actividad-proyecto-list.component.scss` — badge labor + centrado
- `frontend/.../actividad-proyecto-list.component.html` — clases centrado
- `frontend/.../tercero-list-page.component.scss` — min-width + ng-deep + ellipsis
- `frontend/.../quick-access-navigator.service.ts` — getParam() + extractParams()
- `frontend/.../tercero-form.component.ts` — navigator.getParam('id')
- `frontend/.../user-form.component.ts` — navigator.getParam('id')
- `frontend/.../consecutivo-list.component.scss` — min-width + ng-deep + filtros mobile
- `frontend/.../consecutivo-list.component.html` — sin wrapper manual (directiva ya lo hace)

---

## ✅ COMPLETADO (01 Abril 2026) — Backlog Módulo Proyectos: Fases 1-4

### Fase 1: Quick Wins Mobile (6 bugs alta prioridad) ✅
- Todos los 6 bugs ya estaban corregidos en sesiones previas
- Tabs scroll, header flex, tablas responsive, Gantt toolbar, dark mode arrows

### Fase 2: Funcionalidades Alta Prioridad (2 features) ✅
- Notificaciones automáticas de tareas: ya implementado (signals.py pre_save/post_save)
- Nivelación de recursos: ya implementado (ResourceLevelingService + wizard frontend)
- **Agregado:** Signal `dependencia_post_save` para notificar ambos responsables al crear TaskDependency

### Fase 3: Mobile Media/Baja (7 bugs responsive) ✅
- 5 de 7 ya estaban corregidos (Float indicator, Baseline table, What-if table, directive, number pipe)
- **Corregido:** Expansion panels spacing en `team-timeline.component.scss` (gap, touch targets mobile)
- **Corregido:** `table-responsive` wrapper en `tercero-list-page.component.html` y `actividad-proyecto-list.component.html`

### Fase 4: Funcionalidades Media/Baja (3 features) ✅
- Exportar Proyecto a PDF: ya implementado (backend WeasyPrint + frontend botón Exportar)
- Plantillas de Proyecto: ya implementado (modelos + migración + management command + PlantillasPage)
- Importar desde Excel: ya implementado (openpyxl + ImportFromExcelDialog + template download)

### Archivos modificados esta sesión
- `backend/apps/proyectos/signals.py` — TaskDependency notification signal
- `frontend/src/app/features/proyectos/components/team-timeline/team-timeline.component.scss` — panel spacing + mobile
- `frontend/src/app/features/terceros/pages/tercero-list-page/tercero-list-page.component.html` — table-responsive
- `frontend/src/app/features/proyectos/components/actividad-proyecto-list/actividad-proyecto-list.component.html` — table-responsive

### Pendiente
- ⏳ Tests E2E (Agente D) para SaiDashboard — diferido a siguiente sesión

---

## ✅ COMPLETADO (01 Abril 2026) — Feature #10: SaiDashboard (BI Financiero)

### Agente A — Go Agent (agent-go/) ✅ COMPLETADO
- ✅ 23 archivos creados en agent-go/
- ✅ cmd/agent/main.go — CLI: config|serve|install|uninstall|status|test
- ✅ internal/config/config.go — AgentConfig multi-conexión con watermark embebido
- ✅ internal/firebird/client.go — Driver nakagami, query GL incremental denormalizada
- ✅ internal/sync/orchestrator.go — goroutine por conexión habilitada
- ✅ internal/sync/gl_sync.go — sync incremental por CONTEO
- ✅ internal/sync/reference_sync.go — sync ACCT/CUST/LISTA/PROYECTOS/ACTIVIDADES
- ✅ internal/api/client.go — HTTP client con retry + JWT Bearer
- ✅ internal/configurator/ — servidor web embebido :8765 con go:embed
- ✅ internal/winsvc/ — Windows Service install/uninstall (platform-specific)
- ✅ 3 test files (config, gl_sync, handlers)
- ✅ `go mod tidy` + `go build ./...` — compila sin errores

### Agente B — Backend Django ✅ COMPLETADO
- ✅ apps/contabilidad/ — 12 archivos
  - MovimientoContable (GL denormalizado, unique_together company+conteo)
  - ConfiguracionContable (OneToOne, watermark, features)
  - CuentaContable (espejo PUC)
  - SyncService: process_gl_batch (bulk_create update_conflicts), process_acct_full, get_sync_status
  - 3 endpoints sync: gl-batch, acct, status
- ✅ apps/dashboard/ — 14 archivos
  - Dashboard (BaseModel), DashboardCard, DashboardShare, ModuleTrial
  - card_catalog.py — 22 tarjetas en 6 categorías (código, no BD)
  - report_engine.py — ReportEngine con 22 métodos de cálculo
  - DashboardService, CardService, TrialService, FilterService, CatalogService, ReportService
  - 20 URL patterns: CRUD + cards + shares + reports + catalog + filters + trial
  - Admin: readonly MovimientoContable, editable ConfiguracionContable, Dashboard con inline cards
  - Tests: test_models.py + test_services.py para ambas apps
- ✅ INSTALLED_APPS actualizado: apps.contabilidad, apps.dashboard
- ✅ config/urls.py actualizado: /api/v1/contabilidad/ y /api/v1/dashboard/
- ✅ makemigrations + migrate aplicados (0001_initial para ambas apps)

### Agente C — Frontend Angular ✅ COMPLETADO
- ✅ features/saidashboard/ — 20+ archivos
- ✅ 4 modelos: dashboard, card-catalog, report-filter, trial
- ✅ 4 servicios: dashboard, report, card-catalog, trial
- ✅ 1 guard: dashboard-license (checks trial/license)
- ✅ saidashboard.routes.ts (lazy-loaded: list, builder/:id, nuevo, :id)
- ✅ 10 componentes:
  - dashboard-list — home con tabla/cards toggle, favoritos, compartidos
  - dashboard-viewer — vista readonly con KPIs + charts + filtros + export PDF
  - dashboard-builder — editor drag & drop + resize + sidebar catálogo
  - chart-card — wrapper ngx-echarts (bar/line/pie/area/waterfall/gauge)
  - kpi-card — tarjeta indicador numérico
  - filter-panel — fecha range + terceros + proyectos + períodos
  - card-selector — MatDialog catálogo por categoría
  - share-dialog — compartir con usuarios
  - trial-banner — banner prueba activa
  - ai-assistant — panel CFO Virtual
- ✅ npm: echarts, ngx-echarts, angular-resizable-element, jspdf, html2canvas instalados

### Integración (Orquestador) ✅ COMPLETADO
- ✅ Card "SaiDashboard" agregada al selector de módulos (dashboard.component.ts)
- ✅ Ruta /saidashboard en app.routes.ts
- ✅ DEC-042 a DEC-045 en DECISIONS.md (echarts, GL denormalizado, Go agent, ModuleTrial)

### Verificación Completa
- ✅ `python manage.py check` — 0 issues
- ✅ `makemigrations contabilidad dashboard` → 0001_initial para ambas apps
- ✅ `migrate` — aplicado sin errores
- ✅ `go mod tidy` + `go build ./...` — compila sin errores
- ✅ `ng build --configuration=production` — build exitoso (solo warnings pre-existentes)
- ✅ Validación 4x4: responsive mobile (breakpoints 768/480px), dark mode (var(--sc-*)), touch targets 44px
- ✅ Budget angular.json actualizado: initial 2MB, componentStyle 16KB
- ⏳ Tests E2E (Agente D) — pendiente para siguiente sesión

### Decisiones tomadas
- DEC-042: ngx-echarts para gráficos (no Chart.js/ApexCharts/D3)
- DEC-043: GL denormalizado en PostgreSQL (no joins en runtime)
- DEC-044: Agente Go standalone para sync (Criterio 3)
- DEC-045: ModuleTrial independiente (no extender CompanyLicense)
- Ruta: /saidashboard (no /dashboard que es el selector de módulos — DEC-024)

---

## ✅ COMPLETADO (30 Marzo 2026) — Feature #9 FASE 4: Chat Frontend

### Frontend — Componentes (6)
- ✅ `ChatFabComponent`: Boton flotante fixed bottom-right, badge unread, desplaza cuando panel abierto
- ✅ `ChatPanelComponent`: Panel 420px slide-in, header con back/close, alterna lista/chat
- ✅ `ChatListComponent`: Busqueda usuarios, lista conversaciones con preview y badge
- ✅ `ChatWindowComponent`: Mensajes con burbujas, read receipts, typing indicator, scroll infinito
- ✅ `MessageInputComponent`: Textarea autosize, deteccion `[` y `@` para autocomplete
- ✅ `AutocompleteDropdownComponent`: Dropdown flotante entidades/usuarios

### Frontend — Servicios (2)
- ✅ `ChatService`: 7 metodos HTTP (conversaciones, mensajes, autocomplete)
- ✅ `ChatSocketService`: WebSocket con signals reactivos, reconexion exponential backoff

### Frontend — Integracion
- ✅ Shell: FAB + Panel integrados en shell.component.ts/html
- ✅ Build: 0 errores (solo warnings pre-existentes)
- ✅ Validado en navegador: 7 screenshots en reports/fase_4/

---

## ✅ COMPLETADO (30 Marzo 2026) — Feature #9 FASE 3: Chat Backend

### Backend — Modelos
- ✅ `Conversacion`: 1-to-1 entre dos usuarios, unique_together(company, p1, p2), index(company, -ultimo_mensaje_at)
- ✅ `Mensaje`: texto + HTML procesado + imagen R2 + reply threading + read tracking
- ✅ Migración 0001_initial aplicada

### Backend — Services
- ✅ `ChatService.obtener_o_crear_conversacion()` — UUID normalization, idempotente
- ✅ `ChatService.enviar_mensaje()` — procesa contenido + WS push + notificación destinatario + menciones
- ✅ `ChatService.listar_mensajes()` — paginado con validación de participante
- ✅ `ChatService.marcar_leido()` — read receipt + WS push
- ✅ `ChatService.procesar_enlaces()` — [PRY-001] → HTML link (bleach sanitizado)
- ✅ `ChatService.procesar_menciones()` — @Usuario → span HTML + notificación

### Backend — API REST (6 endpoints)
- ✅ GET/POST `/api/v1/chat/conversaciones/`
- ✅ GET `/api/v1/chat/conversaciones/{id}/mensajes/`
- ✅ POST `/api/v1/chat/conversaciones/{id}/mensajes/enviar/`
- ✅ POST `/api/v1/chat/mensajes/{id}/marcar-leido/`
- ✅ GET `/api/v1/chat/autocomplete/entidades/`
- ✅ GET `/api/v1/chat/autocomplete/usuarios/`

### Backend — WebSocket
- ✅ `ChatConsumer` en `ws/chat/` — 7 eventos (new_message, message_read, typing, new_conversation, send_message, mark_read, join_conversation)
- ✅ ASGI routing combinado con notifications

### Tests — 69/69 passing
- ✅ 5 model tests + 25 service tests + 21 view tests + 11 WebSocket tests + 7 notification regression tests

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
- **Último milestone:** Backlog Módulo Proyectos 100% cerrado (Fases 1-4: 13 bugs + 5 features + 2 signals)
- **Features completadas:** #1-#10 (Core → Scheduling → Budget → Licencias → Chat → SaiDashboard)
- **Backlog Proyectos:** 100% completado — 0 items pendientes

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