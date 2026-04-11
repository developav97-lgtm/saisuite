# PROGRESS: CRM

**Estado:** ✅ COMPLETADO (v2 — Sprint UX/Features 10 Abril 2026)
**Tipo:** MODULE
**Fase actual:** 10 — COMPLETADO
**Inicio:** 2026-04-10
**Última sesión:** 2026-04-10
**PRD:** docs/plans/PRD-CRM.md
**PLAN:** docs/plans/PLAN-CRM.md

---

## Fases

| # | Fase | Estado | Inicio | Fin | Rol |
|---|------|--------|--------|-----|-----|
| 0 | PRD | ✅ COMPLETADO | 2026-04-10 | 2026-04-10 | Scrum Master |
| 1 | Planificación técnica | ✅ COMPLETADO | 2026-04-10 | 2026-04-10 | Scrum Master |
| 2 | Contexto + CONTEXT.md | ✅ COMPLETADO | 2026-04-10 | 2026-04-10 | Scrum Master |
| 3 | Skills/APIs/Dependencias | ✅ COMPLETADO | 2026-04-10 | 2026-04-10 | Scrum Master |
| 4 | Implementación | ✅ COMPLETADO | 2026-04-10 | 2026-04-10 | Developer |
| 5 | Iteración + QA | ✅ COMPLETADO | 2026-04-10 | 2026-04-10 | Developer + QA |
| 6 | Checkpoint | ✅ COMPLETADO | 2026-04-10 | 2026-04-10 | Scrum Master |
| 7 | Revisión final | ✅ COMPLETADO | 2026-04-10 | 2026-04-10 | Scrum Master |
| 8 | Admin panel | ✅ COMPLETADO | 2026-04-10 | 2026-04-10 | Developer |
| 9 | UI/UX + Docs | ✅ COMPLETADO | 2026-04-10 | 2026-04-10 | Developer + QA |
| 10 | Deploy + Licencia | ✅ COMPLETADO | 2026-04-10 | 2026-04-10 | Developer |

---

## Tickets

| ID | Tipo | Descripción | Estado | Asignado |
|----|------|-------------|--------|----------|
| CRM-001 | MODULE | Módulo CRM completo (MVP v1.0) | ✅ COMPLETADO | — |
| CRM-002 | IMPROVEMENT | Forms lead/oportunidad + dialogs + signals + rutas | ✅ COMPLETADO | DEV |
| CRM-003 | IMPROVEMENT | Tests Angular — service (58) + 3 components | ✅ COMPLETADO | DEV |
| CRM-004 | IMPROVEMENT | Validación 4x4 — dashboard dinámico + bug RouterModule | ✅ COMPLETADO | DEV |
| CRM-005 | IMPROVEMENT | RAG chunks docs/technical/crm/RAG-CHUNKS.md | ✅ COMPLETADO | DEV |
| CRM-006 | BUGFIX | Migración crm 0001_initial no aplicada → 500 en todas las APIs | ✅ COMPLETADO | DEV |
| CRM-007 | BUGFIX | Dashboard módulos hardcodeados (CRM siempre "Próximamente") | ✅ COMPLETADO | DEV |
| CRM-008 | BUGFIX | leads-page RouterModule faltante → error compilación | ✅ COMPLETADO | DEV |
| CRM-009 | BUGFIX | Cotización dark mode — hardcoded hex → var(--sc-*) | ✅ COMPLETADO | DEV |
| CRM-010 | IMPROVEMENT | CRM entry point → /crm/dashboard + reorden sidebar nav | ✅ COMPLETADO | DEV |
| CRM-011 | FEATURE | Lead detail page + edit button en lista | ✅ COMPLETADO | DEV |
| CRM-012 | IMPROVEMENT | Formateo de moneda con separador de miles (ScMoneyInputDirective) | ✅ COMPLETADO | DEV |
| CRM-013 | FEATURE | Acceso rápido Terceros + Catálogo en sidebar CRM | ✅ COMPLETADO | DEV |
| CRM-014 | FEATURE | Actividades en Leads (migración 0002 + UI) — relación polimorfa | ✅ COMPLETADO | DEV |
| CRM-015 | FEATURE | Agenda global CRM — vista semanal + iconos por tipo + filtro pendientes | ✅ COMPLETADO | DEV |
| CRM-016 | IMPROVEMENT | UX asignación post-conversión: select vendedor + crear tercero opcional | ✅ COMPLETADO | DEV |
| CRM-RF43 | FEATURE | PDF export cotizaciones — endpoint + botón UI (ya existía, validado) | ✅ COMPLETADO | DEV |
| CRM-RF23 | FEATURE | Round-robin lead assignment — endpoint individual + masivo + UI | ✅ COMPLETADO | DEV |
| LIC-001 | BUGFIX | Leads table última columna cortada + "onvertic" visual → wrapper div acciones | ✅ COMPLETADO | DEV |
| LIC-002 | BUGFIX | 103 tests fallando por campo `plan` removido de CompanyLicense — 4 test files fix | ✅ COMPLETADO | DEV |
| INF-001 | BUGFIX | CRM Dashboard rendimientos vacíos — field names frontend + filtro vendedores con ops | ✅ COMPLETADO | DEV |
| CONT-001 | FEATURE | Vista GL Contabilidad — endpoint /movimientos/ + GlViewerPageComponent con filtros | ✅ COMPLETADO | DEV |

---

## Resumen final de implementación

### Backend (Django 5) — v2

- **Modelos (11):** CrmPipeline, CrmEtapa, CrmLead, CrmLeadScoringRule, CrmOportunidad, CrmActividad, CrmTimelineEvent, CrmImpuesto, CrmProducto, CrmCotizacion, CrmLineaCotizacion
- **Migración `0002`:** `actividad_add_lead_fk` — relación polimorfa actividad→lead (nullable FK)
- **Servicios:** `ActividadService.list_for_lead()`, `create_for_lead()` | `LeadService.asignar_round_robin()`, `asignar_masivo_round_robin()` | `AgendaView` con filtros fecha+pendientes
- **Nuevos endpoints:** `GET/POST leads/{id}/actividades/`, `POST leads/{id}/round-robin/`, `POST leads/asignar-masivo/`, `GET agenda/`
- **Serializers:** `CrmActividadAgendaSerializer` con `contexto_nombre`, `contexto_tipo` | `CrmLeadConvertirSerializer` con `asignado_a_id`
- **Tests:** suite v1 mantiene 47/47 passing | Tests v2 pendientes de ejecución

### Frontend (Angular 18) — v2

- **Rutas nuevas:** `/crm/leads/:id` (detail), `/crm/agenda` — total **9 rutas** lazy-loaded
- **Componentes nuevos (5):** `LeadDetailPageComponent`, `CrmAgendaPageComponent`, `CrmCatalogoPageComponent`, `ActividadLeadDialogComponent`, `CompletarActividadDialogComponent`
- **Directiva:** `ScMoneyInputDirective` — formato `es-CO` con focus/blur handlers
- **Sidebar CRM:** getter (no readonly), Agenda añadida, sección "Acceso rápido" con Terceros+Catálogo
- **CrmService:** 50+ métodos — `listActividadesLead()`, `createActividadLead()`, `getAgenda()`, `asignarRoundRobin()`, `asignarMasivoRoundRobin()`
- **Fix dark mode:** cotizacion-page.component.scss — todos los colores migrados a `var(--sc-*)`

### Licencia y Acceso

- Módulo `crm` activo en `CompanyModule` y `CompanyLicense.modules_included` para "Desarrollo - ValMen Tech"
- Solicitud `dd34960c` aprobada el 2026-04-10

### Documentación

- `docs/technical/crm/RAG-CHUNKS.md` — 15 chunks v1 (actualización v2 pendiente)
- `docs/manuales/crm/` — manual de usuario pendiente actualización v2

### Integración Saiopen

- TAXAUTH → CrmImpuesto (sync via SQS)
- ITEM → CrmProducto (solo lectura en CRM)
- CrmCotizacion → COTIZACI (push al aceptar, `sai_key` = `"{numero}_{tipo}_{empresa}_{sucursal}"`)

### Fixes resueltos en v2

| Bug/Issue | Fix |
|-----------|-----|
| `CrmActividad.oportunidad` no nullable | Nullable FK + migración 0002 |
| `soloPendientes` signal con `[(ngModel)]` | Cambiado a propiedad regular `boolean` |
| `ScMoneyInputDirective` import faltante en dialog | Agregado a imports del componente |
| NG8102 en lead-detail HTML | `fuenteLabel` tipo `Partial<Record<string,string>>` |
| `CRM_NAV` readonly impedía `this.openQuickAccess` | Cambiado de `readonly` a `get` |
| sqs-worker unhealthy — contenedor con código viejo | Rebuild + restart del container |

---

## Sesiones de Trabajo

| Sesión | Fecha | Tickets | Resumen |
|--------|-------|---------|---------|
| 01 | 2026-04-10 | CRM-001 (fases 0-1) | PRD + PLAN. 7 features verticales planificadas. |
| 02 | 2026-04-10 | CRM-001 (fases 2-10) | Backend completo: 11 modelos, 47 tests. Frontend: 5 páginas + kanban CDK. |
| 03 | 2026-04-10 | CRM-002 a CRM-008 | Forms, dialogs, signals, rutas, tests (58+component specs), RAG (15 chunks), migración aplicada, dashboard dinámico, licencia aprobada. |
| 04 | 2026-04-10 | CRM-009 a CRM-RF23 | Sprint v2: dark mode fix, lead detail, agenda, actividades en leads, round-robin, acceso rápido sidebar, directiva moneda, PDF export validado. sqs-worker rebuildeado. |
| 05 | 2026-04-11 | LIC-001, LIC-002, INF-001, CONT-001 | Fixes visuales leads table + rendimientos CRM. Fix 103 tests companies (campo plan removido). GL Contabilidad viewer (backend API + Angular page). 158 tests passing. |
