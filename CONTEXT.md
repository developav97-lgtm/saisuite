# CONTEXT.md - Estado del Proyecto Saicloud

**Ultima actualizacion:** 20 Abril 2026
**Sesion:** Marco agentic v1 + validaciones 4×4 (contabilidad fixed, licencias reportada)

---

## COMPLETADO (09 Abril 2026) — Sistema de Licencias Modular (Fases 1-10)

### Plan: `pure-noodling-owl.md` — 100% implementado

---

### Fase 1-4 — Backend + Frontend base de licencias (sesiones anteriores)

- Eliminado campo `plan` de `CompanyLicense`, agregado `renewal_type`
- `LicensePackage`, `LicensePackageItem` con tipos: `module`, `user_seats`, `ai_tokens`
- `_recalculate_user_quotas()`: `concurrent_users` se calcula automáticamente de paquetes `user_seats`
- `max_users = concurrent_users × 2` siempre
- License builder en tenant-form: módulos/usuarios/tokens desde catálogo con precios y total en tiempo real
- Catálogo de paquetes reorganizado en 3 tabs: Módulos / Usuarios / Tokens IA

---

### Fase 5 — Bloqueo de módulos

**Guard aplicado a rutas:**
- `/proyectos` → `moduleAccessGuard` con `data: { requiredModule: 'proyectos' }`
- `/saidashboard` → `moduleAccessGuard` con `data: { requiredModule: 'dashboard' }`

**Flujo del guard:**
1. Módulo en `license.modules_included` → acceso directo
2. Trial activo → acceso directo
3. Sin acceso → redirige a `/acceso-modulo?module=<code>`

**`ModuleLockedComponent`** (`/acceso-modulo`):
- Sin trial usado + es admin → botón "Iniciar prueba 14 días"
- Trial activo → días restantes + botón "Ir al módulo"
- Trial usado + es admin → botón **"Solicitar licencia"** (abre `LicenseRequestDialogComponent`)
- No es admin → "Contacta al administrador"
- Trial activado → mensaje éxito + botón "Ir al módulo"

---

### Fase 6 — N8N Auto-renovación

Workflows importados en n8n (`http://localhost:5678`):
- `CFO Virtual — SaiDashboard` (id: `4752f503`)
- `Knowledge Base Watcher` (id: `kb-watcher-workflow-001`)
- `Auto Renewal 5 Days` (id: `810333fd`)

**Nota:** Importados como inactivos. Activar manualmente en n8n UI.
**Archivo:** `docker compose exec n8n n8n import:workflow --input=/workflows/<file>.json`

---

### Fase 7 — Email SMTP Google Workspace

**Config en `backend/.env`:**
```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=juan@valmentech.com        # cuenta principal (auth)
EMAIL_HOST_PASSWORD=awjxusxcnkacffdq       # App Password
DEFAULT_FROM_EMAIL=SaiCloud <noreply@valmentech.com>  # alias como FROM
```

**Flujos de email funcionando:**
- Invitación al crear empresa (link activación 72h)
- Recuperación de contraseña
- Notificación de solicitud de licencia al admin ValMen
- Notificación de aprobación/rechazo al company_admin

---

### Fase 8 — Tokens IA: consumo real + bloqueo

**Backend** (`apps/chat/services.py` — `BotResponseService`):
- Antes de llamar OpenAI: `AIUsageService.check_quota(company)`
- Si cuota agotada: crea mensaje de bot con texto de error, NO consume tokens
- Después de responder: `AIUsageService.track_usage()` incrementa `ai_tokens_used`

**Frontend** (`chat-window.component.ts`):
- `aiUsage` signal cargado al abrir conversación bot
- `quotaExceeded = computed()` → `tokens_used >= tokens_quota`
- `tokenPct = computed()` → porcentaje visual
- Barra de progreso en header de bot conversation
- Banner "Cuota agotada" encima del input cuando `quotaExceeded()`
- Input deshabilitado con `[disabled]="isBot() && quotaExceeded()"`
- `loadAIUsage()` se llama al recibir cada respuesta del bot

---

### Fase 9 — Bot: restricción por módulo

**Backend** (`BotResponseService.generate_bot_response()`):
```python
if bot_context and bot_context != 'general':
    if not ModuleTrialService.is_module_accessible(company, bot_context):
        # Crea mensaje de error, NO llama OpenAI
        return
```
- No consume tokens si módulo no licenciado
- Mensaje al usuario: "No tienes acceso al módulo de X. Puedes solicitar prueba o contactar ventas."

---

### Fase 10 — License Builder Package-Driven (tenant-form)

- Módulos vienen del catálogo (`/api/v1/admin/packages/?type=module`)
- Usuarios auto-calculados de paquetes `user_seats` (no editable manualmente)
- Tokens IA por paquetes seleccionables (reemplaza input `ai_tokens_quota`)
- `messages_quota` eliminado de la DB (migración `0014_remove_messages_quota`)
- Total de licencia calculado en tiempo real con `licenseTotal = computed()`

---

### Sistema de Solicitudes de Licencia (nuevo — esta sesión)

#### Backend

**Modelo:** `LicenseRequest` (migración `0015_add_license_request`)
```
company, request_type (user_seats|module|ai_tokens), package (FK),
status (pending|approved|rejected), notes, review_notes,
created_by, reviewed_by, reviewed_at
```

**Service:** `LicenseRequestService`
- `create_request()` — valida tipo coherente con paquete, no duplica pendientes, envía email admin
- `approve()` — aplica paquete a licencia; para `ai_tokens`: reemplaza paquetes existentes del mismo tipo
- `reject()` — guarda review_notes, notifica al company_admin
- `list_for_company()`, `list_all()` — listados

**Endpoints:**
- `GET/POST /api/v1/companies/license-requests/` — company_admin
- `GET /api/v1/admin/tenants/license-requests/?status=pending` — superadmin
- `POST /api/v1/admin/tenants/license-requests/{id}/approve/` — superadmin
- `POST /api/v1/admin/tenants/license-requests/{id}/reject/` — superadmin
- `GET /api/v1/companies/packages/catalog/?type=module` — catálogo para company_admin (sin superadmin)

**Email templates:**
- `backend/templates/emails/license_request_admin.html` — notificación a ValMen
- `backend/templates/emails/license_request_approved.html` — aprobación al cliente

#### Frontend

**Modelos:** `LicenseRequest`, `LicenseRequestType`, `LicenseRequestStatus` en `tenant.model.ts`

**`company-settings` — Tab "Solicitudes":**
- 3 botones: "Solicitar más usuarios", "Solicitar módulo", "Solicitar tokens IA"
- Filtrado inteligente: excluye paquetes base (precio=0), excluye módulos ya en licencia
- `LicenseRequestDialogComponent` — selecciona paquete + nota opcional
- Historial de solicitudes con estado (pending/approved/rejected)

**Admin — `/admin/license-requests`:**
- Tab "Pendientes" con badge de conteo
- Tab "Historial"
- Botones Aprobar/Rechazar con `ReviewDialogComponent` (nota opcional)
- Link en sidebar superadmin: "Solicitudes" (icono `mark_email_unread`)

---

### Paquetes de licencia seedeados en DB

**Módulos (`package_type=module`, precio=0 — incluidos en licencia base):**
- `mod_proyectos` — SaiProyectos
- `mod_dashboard` — SaiDashboard
- `mod_crm` — CRM
- `mod_soporte` — Soporte

**Usuarios (`package_type=user_seats`):**
- `user_seats_base_2` — 2 usuarios base — $0 (incluido)
- `user_seats_add_2` — +2 usuarios — $120.000/mes
- `user_seats_add_5` — +5 usuarios — $250.000/mes
- `user_seats_add_10` — +10 usuarios — $450.000/mes
- `user_seats_add_20` — +20 usuarios — $850.000/mes

**Tokens IA (`package_type=ai_tokens`):**
- `ai_tokens_base_10k` — 10K tokens base — $0 (incluido)
- `ai_tokens_50k` — +50K tokens — $80.000/mes
- `ai_tokens_200k` — +200K tokens — $280.000/mes
- `ai_tokens_500k` — +500K tokens — $600.000/mes

---

## COMPLETADO (09 Abril 2026) — Integración Proyectos ↔ SaiOpen

### Plan: `nifty-growing-sketch.md` — 100% implementado

Conecta el módulo Proyectos con los datos contables de Saiopen (Firebird/GL).

**Nuevos modelos:** `TipdocSaiopen`, campos GL en `AccountingDocument`
**Migraciones:** `contabilidad/0004`, `proyectos/0025`
**Endpoints:** sync GL, asiento contable, vinculación Saiopen, sync actividades
**Agente Go:** `TipdocRecord`, `syncTipdoc()`, watermark `LastSyncTipdoc`
**Frontend:** documento-list con sync GL, `AsientoContableDialogComponent`, vinculación Saiopen

---

## Stack técnico activo

- **Backend:** Django 5 + DRF — `http://localhost:8000` (Docker)
- **Frontend:** Angular 18 (signals, OnPush) — `http://localhost:4200` (**LOCAL, no Docker** — `cd frontend && ng serve`)
- **DB:** PostgreSQL 16 — `localhost:5432` (saisuite_dev) (Docker)
- **n8n:** `http://localhost:5678` (Docker — 3 workflows importados, inactivos)
- **Email:** Google Workspace SMTP — `juan@valmentech.com` + App Password
- **Redis:** Upstash (WebSockets, caché)
- **Storage:** Cloudflare R2 (logos empresa, archivos chat)

> **Nota dev:** `docker compose up -d` levanta solo db, backend, sqs-worker y n8n.
> El frontend NO está en Docker. Levantarlo con: `cd frontend && ng serve`

## Decisiones arquitectónicas vigentes

- `concurrent_users` y `max_users` son **calculados**, nunca editables manualmente
- `messages_quota` eliminado — solo se trackea `messages_used` como contador informativo
- `ai_tokens` en solicitudes: aprobación **reemplaza** el paquete anterior (modelo mensual)
- N8N workflows: siempre importar con ID explícito y sin tags (evita errores FK)
- Google SMTP: `EMAIL_HOST_USER` = cuenta primaria, `DEFAULT_FROM_EMAIL` = alias noreply

---

## COMPLETADO (10 Abril 2026) — CRM v2 Sprint UX/Features

### Módulo: CRM (sesión `SESSION-CRM-2026-04-10.md`)

#### Backend

**`signals.py` — BUGFIX CRÍTICO:**
- Guard `if not instance.oportunidad_id: return` en `actividad_creada_timeline`
- Previene `IntegrityError` (CrmTimelineEvent.oportunidad NOT NULL) para actividades de lead
- Sin esta corrección: `TransactionManagementError` en todos los tests v2

**`services.py` — RF-2.3 Round-Robin:**
- `LeadService.asignar_round_robin(lead)` — asigna al vendedor con mínimo leads (`annotate` + `order_by`)
- `LeadService.asignar_masivo_round_robin(company)` — asigna todos los leads sin asignar, retorna conteo
- `LeadService._asignar_round_robin` ahora delega a `asignar_round_robin` (alias)
- `ActividadService.create_for_lead(lead, data)` — crea actividad con `lead=lead, oportunidad=None`
- `ActividadService.list_for_lead(lead, solo_pendientes=False)` — filtra por lead, excluye oportunidad

**`serializers.py` — asignado_a_nombre:**
- `CrmLeadListSerializer` y `CrmLeadDetailSerializer` ahora incluyen `asignado_a_nombre` (SerializerMethodField)
- Devuelve `full_name` o `email` del vendedor; `null` si no asignado

**`views.py` — nuevos endpoints:**
- `LeadActividadesView` — GET/POST `/leads/{id}/actividades/` (con `?solo_pendientes=true`)
- `round_robin` action — POST `/leads/{id}/round-robin/` (404 si no existe lead)
- `asignar_masivo` action — POST `/leads/asignar-masivo/` (retorna `{asignados: N}`)
- `AgendaView` — GET `/agenda/` (con `?fecha_desde&fecha_hasta&solo_pendientes`)

**`urls.py`:** `asignar-masivo/` declarada ANTES de `<uuid:pk>/` para evitar conflicto de routing

**Tests — 72/72 passing:**
- `test_v2_services.py` (10 tests): actividades en lead, round-robin service
- `test_v2_views.py` (15 tests): agenda API, lead activities views, round-robin views
- `test_license_request_service.py` (22 tests): LicenseRequestService completo

#### Frontend

**`crm.service.ts`:**
- `getLeadActividades(id, params?)` — GET actividades del lead
- `createLeadActividad(id, data)` — POST actividad en lead
- `asignarRoundRobin(id)` — POST round-robin individual
- `asignarMasivoRoundRobin()` — POST asignación masiva

**`leads-page.component.ts/html`:**
- Botón "Auto-asignar" (bulk round-robin) en header
- Ícono `person_add` por fila (visible solo si `!lead.asignado_a_nombre`)
- `asignarRoundRobin(lead, event)` — asigna y actualiza signal `leads()`
- `asignarTodosRoundRobin()` — asigna masivo y recarga lista

**`crm-agenda-page.component.ts`:**
- Corregido: `soloPendientes` cambiado de `readonly signal()` a propiedad boolean regular
- Compatible con `[(ngModel)]`

#### Docker fix

**`docker-compose.yml`:**
- sqs-worker healthcheck: `pgrep -f` → `pidof python` (`pgrep` no disponible en imagen)
- sqs-worker: ✅ healthy

#### Documentación actualizada

- `docs/technical/crm/RAG-CHUNKS.md` v1.1 — chunks 16, 17, 18 nuevos; chunks 3, 6, 10, 12, 13, 14, 15 actualizados
- `docs/manuales/MANUAL-CRM-SAICLOUD.md` v1.1 — Round-Robin, Actividades en Lead, Agenda (sección 11 nueva)
- `PROGRESS-CRM.md` — tickets CRM-009 a RF-2.3 actualizados/cerrados

---

---

## COMPLETADO (11 Abril 2026) — Fixes + GL Contabilidad

### LIC-001: Visual leads table
- `display: flex` en `td` de mat-table rompe el grid → wrapper `div.acciones-cell`
- "Convertido" chip recortado → `mat-icon-button` con `check_circle` + tooltip
- `.mat-column-acciones { width: 176px }` para columna consistente

### LIC-002: 103 tests companies fallando
- Campo `plan` removido de `CompanyLicense` en sesión anterior, tests no actualizados
- 5 archivos corregidos: `test_company_model.py`, `test_company_license_model.py`, `test_license_payment_model.py`, `test_license_services.py`, `test_license_views.py`, `test_license_serializers.py`, `test_notify_license_expiry_command.py`
- `CompanyLicenseWriteSerializer` le faltaba campo `company` (PrimaryKeyRelatedField) → agregado
- Tests timezone-robustos (Colombia UTC-5 vs UTC): `expires_at - 3 days` en vez de `-1 day`
- **158/158 tests passing**

### INF-001: CRM Dashboard rendimientos vacíos
- Frontend usaba `v.nombre`, `v.oportunidades_activas`, `v.ganadas_mes`, `v.valor_ganado_mes`
- Backend retorna `v.vendedor`, `v.oportunidades`, `v.ganadas`, `v.valor_ganado`
- Backend filtraba todos los 14 usuarios → ahora solo vendedores con al menos 1 oportunidad

### CONT-001: GL Contabilidad viewer
- **Backend:** `GLMovimientoListView` (`GET /api/v1/contabilidad/movimientos/`) con filtros: `periodo`, `titulo_codigo`, `tercero_id`, `tipo`, `fecha_inicio`, `fecha_fin`, `search`
- **Frontend:** `features/contabilidad/` — `GlViewerPageComponent` (tabla + filtros reactivos), `ContabilidadService`
- **Sidebar:** entrada "Contabilidad GL" en HOME_NAV + `CONTABILIDAD_NAV` propio
- **Ruta:** `/contabilidad` en `app.routes.ts` (lazy-loaded)

## COMPLETADO (20 Abril 2026) — Marco agentic + validaciones 4×4

### IMP-VAL-001: Validación 4×4 GL Contabilidad + fixes críticos
- **Reporte:** `docs/plans/VALIDACION-4x4-CONTABILIDAD.md` (23 issues: 4🔴 + 8🟡 + 11🔵)
- **Fixes aplicados:** CRIT-1/2/3/4 + MAY-1/2/3/4/5/6/7/8 (todos los mayores)
- **Refactor:** migrado a `sc-page/sc-card/sc-empty-state/sc-status-chip` canónicos, SCSS 168→96 líneas, MatPaginator server-side, tokens reales

### IMP-VAL-002: Validación 4×4 Sistema de Licencias
- **Reporte:** `docs/plans/VALIDACION-4x4-LICENCIAS.md` (31 issues: 9🔴 + 13🟡 + 9🔵)
- **Score:** 5.3/10 NEEDS WORK — fixes deferidos como tickets BUGFIX/IMP-LIC-201 a 207
- **Componentes auditados:** `license-requests`, `license-request-dialog`, `license-expired`

### Marco agentic SaiSuite
- **18 agentes** project-scoped en `.claude/agents/`
- **Orquestador** con invocaciones reales (Skill tool + Agent tool), delega según `.claude/PHASE-MAP.md`
- **Hooks:** SessionStart (lee PROGRESS activos), PreToolUse Bash (bloquea git push sin Fase 7 aprobada)
- **Scripts:** `validate-marco.sh` (9 checks), `telemetry.sh` / `telemetry-stats.sh`
- **Manual:** `docs/technical/MARCO-AGENTIC-SAISUITE.md`

---

## Próximas prioridades (pendientes REALES)

- **🔴 BUGFIX-LIC-201 a 207** — 7 tickets deferidos de la validación de licencias (bloquean producción). Arranque sugerido: ticket autónomo de los 4 críticos en una sesión.
- **🟡 Re-validación 4×4 visual con backend activo** — los fixes del GL Contabilidad ya se aplicaron y compilan, pero falta screenshot-check real con Django corriendo.
- **🔵 Activar workflows N8N en producción** (auto-renovación, KB watcher) — acción manual en n8n UI.
