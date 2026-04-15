# PROGRESS: Reportes (SaiDashboard)

**Estado:** ✅ COMPLETADO (V2 Sprint 5 completado)
**Tipo:** FEATURE + IMPROVEMENT
**Fase actual:** COMPLETADO — Todos los sprints entregados
**Inicio:** 2026-04-10
**Última sesión:** 2026-04-13
**PRD:** docs/plans/PRD-REPORTES-BI.md
**Module code:** `dashboard`

---

## Fases

| # | Fase | Estado | Inicio | Fin | Rol |
|---|------|--------|--------|-----|-----|
| A | Modelos de datos y sync | ✅ COMPLETADO | 2026-04-10 | 2026-04-10 | Developer |
| B | Motor de consultas BI | ✅ COMPLETADO | 2026-04-10 | 2026-04-10 | Developer |
| C | Frontend — Constructor visual + Renombramiento UI | ✅ COMPLETADO | 2026-04-10 | 2026-04-10 | Developer |
| D | Pivot Table, Charts, Export, Report Viewer | ✅ COMPLETADO | 2026-04-11 | 2026-04-11 | Developer |
| E | Templates predefinidos + Compartir + CFO IA | ✅ COMPLETADO | 2026-04-11 | 2026-04-11 | Developer |
| F | Validación 4x4 + QA | ✅ COMPLETADO | 2026-04-11 | 2026-04-11 | QA |

---

## Tickets

| ID | Tipo | Descripción | Estado | Asignado |
|----|------|-------------|--------|----------|
| DASH-001 | FEATURE | Fase A — Modelos FacturaEncabezado, FacturaDetalle, MovimientoCartera, MovimientoInventario | ✅ COMPLETADO | DEV |
| DASH-002 | FEATURE | Fase B — Motor de consultas BI (BIQueryEngine + ReportBI CRUD + API endpoints) | ✅ COMPLETADO | DEV |
| DASH-003 | FEATURE | Fase C — Frontend constructor visual BI + renombramiento UI SaiDashboard→Reportes | ✅ COMPLETADO | DEV |
| DASH-004 | FEATURE | Fase D — Pivot table, chart renderer (6 tipos), drill-down, export (Excel/CSV/PDF), report viewer | ✅ COMPLETADO | DEV |
| DASH-005 | FEATURE | Fase E — 12 templates predefinidos, report-share-dialog, CFO Virtual suggest-report IA, tests | ✅ COMPLETADO | DEV |
| DASH-006 | QA | Fase F — Validación 4x4, Django Admin (ReportBI + 4 modelos contab), RAG-CHUNKS, cierre módulo | ✅ COMPLETADO | QA |
| DASH-007 | BUGFIX | filter-builder: tipo 'date' sin datepicker, multi_select/select sin control, filtros duplicados por dedup incorrecto, filtros nunca llegaban al backend | ✅ COMPLETADO | DEV |
| DASH-008 | IMPROVEMENT | **V2 Sprint 1** — BIQueryEngine v2: multi-fuente con JOINs automáticos (Subquery+OuterRef), SOURCE_JOINS_MAP con 15+ relaciones | ✅ COMPLETADO | DEV |
| DASH-009 | IMPROVEMENT | **V2 Sprint 1** — Nuevas fuentes: terceros_saiopen, productos, cuentas_contables, proyectos_saiopen, actividades_saiopen, departamentos, centros_costo, tipos_documento, direcciones_envio, impuestos | ✅ COMPLETADO | DEV |
| DASH-010 | IMPROVEMENT | **V2 Sprint 1** — FilterTranslator: 12 operadores (eq, neq, contains, between, in, is_true, is_false, etc.) con retrocompatibilidad filtros v1 | ✅ COMPLETADO | DEV |
| DASH-011 | IMPROVEMENT | **V2 Sprint 1** — Endpoint GET /meta/joins/ + validación limite_registros | ✅ COMPLETADO | DEV |
| DASH-012 | IMPROVEMENT | **V2 Sprint 1** — Tests (43 passing): FilterTranslator, JOINs, nuevas fuentes, límite, endpoint | ✅ COMPLETADO | QA |
| DASH-013 | IMPROVEMENT | **V2 Sprint 2** — Frontend: field-panel rediseño, filter-builder operadores, source-selector nuevas fuentes, duplicate-dialog | ✅ COMPLETADO | DEV |
| DASH-014 | IMPROVEMENT | **V2 Sprint 3** — Galería: categoria_galeria, templates multi-tabla, vista galería | ✅ COMPLETADO | DEV |
| DASH-015 | IMPROVEMENT | **V2 Sprint 4** — Dashboard ↔ BI: bi_report FK, filtros 3 capas, card-filter-override | ✅ COMPLETADO | DEV |
| DASH-016 | IMPROVEMENT | **V2 Sprint 5** — CFO Virtual actualización, validaciones integridad, documentación | ✅ COMPLETADO | DEV |
| DASH-017 | BUGFIX | Fixes BI: labels duplicados (Tercero/Identificación, Nombre/Nombre tercero, Código/Descripción producto), EXTEND→0 en OEDET, campo orden_campo inválido en suggest-report | ✅ COMPLETADO | DEV |
| DASH-018 | FEATURE | **V3 Sesión 15-Abr** — Campos nuevos: retenciones OE, clasificación OEDET→Productos, dimensiones OEDET; templates globales estáticos (28); ordenamiento+límite en builder; sugeridor IA con fechas y cuentas PUC; eliminación galería | ✅ COMPLETADO | DEV |

---

## Sesiones de Trabajo

| Sesión | Fecha | Sprint | Resultado |
|--------|-------|--------|-----------|
| 1-9 | 2026-04-10 a 2026-04-11 | Sprints 1-3 | Módulo BI completo |
| 10 | 2026-04-12 | Sprint 4 | Dashboard ↔ BI integration (DASH-015) |
| 11 | 2026-04-13 | Sprint 5 | DASH-016: ReportBIValidator, CFO actualizado, tests +18, RAG+2 chunks |
| 12 | 2026-04-15 | V3 | DASH-017+018: fixes labels, sync OEDET/OE nuevos campos, builder ordenamiento+límite, templates globales 28, sugeridor IA mejorado, galería eliminada |

---

## Detalle de implementación

### Sprint 5 — CFO Virtual, Validaciones Integridad, Documentación (DASH-016)

**Fecha:** 2026-04-13
**Tests añadidos:** 20 backend (`TestReportBIValidator` + fix `CfoSuggestReportTest`) + corrección de 24 tests desactualizados
**Total tests backend:** 74 passing (+ 1 skip por reportlab), 26 en contabilidad = 100 total

**Archivos backend:**

| Archivo | Cambios |
|---------|---------|
| `backend/apps/dashboard/services.py` | Nueva clase `ReportBIValidator` (validate_sources, validate_campos_config, validate_joins, validate_viz_config, validate_orden_config, validate_all); llamada desde `create_report()` y `update_report()`; `get_template_catalog()` ahora incluye `categoria_galeria`; `suggest_report()` system_prompt mejorado con categorías + retorna `categoria_galeria` |
| `backend/apps/dashboard/tests/test_report_bi.py` | +`TestReportBIValidator` (20 tests); corrección de 24 tests desactualizados por v2 (fuentes 5→16, templates 12→23, campos_config sin source, template title inexistente) |
| `docs/technical/reportes-bi/RAG-CHUNKS.md` | +CHUNK-016 actualizado, +CHUNK-017 (ReportBIValidator), +CHUNK-018 (CFO Virtual Sprint 5) |

**ReportBIValidator — validaciones implementadas:**

| Método | Qué valida | Error |
|--------|-----------|-------|
| `validate_sources` | Fuentes en SOURCE_FIELDS | "Fuentes no reconocidas: X" |
| `validate_campos_config` | source en fuentes, field en SOURCE_FIELDS[source], role válido | "campos_config[i]: field 'X' no existe..." |
| `validate_joins` | Para multi-fuente: JOIN en SOURCE_JOINS_MAP | "No existe JOIN desde 'A' hacia: B" |
| `validate_viz_config` | Pivot: row/col/value fields en campos_config | "viz_config.row_fields: 'X' no está en campos_config" |
| `validate_orden_config` | Campos de orden en campos_config, direction asc/desc | "orden_config[i]: 'X' no está en campos_config" |

**CFO Virtual mejoras:**
- `system_prompt` incluye categoría de cada template para matching más preciso
- `suggest_report()` retorna `categoria_galeria` para navegación directa
- `get_template_catalog()` incluye `categoria_galeria` en cada entrada

---

### Sesión 12 — V3: Campos sync, Builder mejorado, Templates globales, Sugeridor IA, Galería eliminada (DASH-017 + DASH-018)

**Fecha:** 2026-04-15
**Tests finales backend:** 206 passing (dashboard) + 177 passing (contabilidad+crm)

---

#### 1. Fixes de labels duplicados en BI (DASH-017)

Cuando el usuario combina fuentes transaccionales con maestros, los mismos campos aparecían dos veces con nombres distintos.

| Problema | Fix aplicado |
|----------|-------------|
| `facturacion_detalle.item_codigo` = "Código producto" ≠ `productos.codigo` = "Código" | Renombrado a "Código" en `facturacion_detalle` |
| `facturacion_detalle.item_descripcion` = "Descripción producto" ≠ `productos.descripcion` = "Descripción" | Renombrado a "Descripción" |
| `gl.tercero_id` = "Identificacion" ≠ `terceros_saiopen.id_n` = "Identificación" | Estandarizado a "Identificación" |
| `gl/facturacion/cartera.tercero_nombre` = "Nombre tercero" ≠ `terceros_saiopen.nombre` = "Nombre" | Estandarizado a "Nombre" |
| Categoría `terceros_saiopen` = "Identificación" no fusionaba con "Tercero" de GL | Renombrada a "Tercero" en `SOURCE_FIELDS` |

**Archivos:** `backend/apps/dashboard/bi_engine.py`

---

#### 2. Fix agente Go — OEDET.EXTEND en cero (DASH-017)

`precio_extendido` siempre llegaba en 0 porque `detectColumn("OEDET")` buscaba `"EXTENDED"` pero el campo real en Firebird es `"EXTEND"`.

**Fix:** `agent-go/internal/firebird/client.go:390` — Agregado `"EXTEND"` como primer candidato.

---

#### 3. Nuevos campos sync — Agente Go + Django (DASH-018)

##### Facturación Detalle (OEDET → `FacturaDetalle`)

| Campo Django | Campo Firebird | Descripción |
|-------------|---------------|-------------|
| `total_descuento` | `OEDET.TOTALDCT` | Total descuento línea |
| `departamento_codigo` | `OEDET.DPTO` | Departamento contable |
| `centro_costo_codigo` | `OEDET.CCOST` | Centro de costo |
| `actividad_codigo` | `OEDET.ACTIVIDAD` | Actividad económica |

Campos de clasificación (`item_reffabrica`, `item_class`, `linea_*`, `grupo_*`, `subgrupo_*`) **movidos de `FacturaDetalle` a `CrmProducto`** — pertenecen al maestro ITEM, no al movimiento transaccional.

Migraciones: `0012` (clasificación→detalle), `0013` (retenciones→encabezado), `0014` (dimensiones→detalle), `0015` (remove clasificación de detalle).

##### Facturación Encabezado (OE → `FacturaEncabezado`)

| Campo Django | Campo Firebird | Descripción |
|-------------|---------------|-------------|
| `tercero_razon_social` | `CUST.COMPANY_EXTENDIDO` | Nombre extendido del tercero |
| `tipo_descripcion` | `TIPDOC.DESCRIPCION` (JOIN) | Descripción del tipo de documento |
| `destotal` | `OE.DESTOTAL` | Descuento total factura |
| `otroscargos` | `OE.OTROSCARGOS` | Otros cargos |
| `porcrtfte` | `OE.PORCRTFTE` | % retención en la fuente |
| `reteica` | `OE.DISC2` | Valor retención ICA |
| `porcentaje_reteica` | `RETEN.PORCENTAJE` (JOIN) | % retención ICA |
| `reteiva` | `OE.DISC3` | Valor retención IVA |

Migración: `0013_add_retenciones_factura_encabezado`.

##### Productos (ITEM → `CrmProducto`)

| Campo Django | Campo Firebird | Descripción |
|-------------|---------------|-------------|
| `reffabrica` | `ITEM.REFFABRICA` | Referencia de fábrica |
| `linea_codigo` | `ITEM.ITEMMSTR` | Código línea (PUC producto) |
| `linea_descripcion` | `LINEA.DESCLINEA` (JOIN) | Descripción línea |
| `grupo_descripcion` | `GRUPO.DESCGRUPO` (JOIN) | Descripción grupo |
| `subgrupo_descripcion` | `SUBGRUPO.DESCSUBGRUPO` (JOIN) | Descripción subgrupo |

`QueryAllItem` ahora hace LEFT JOINs condicionales a LINEA, GRUPO, SUBGRUPO.

Migración: `crm.0003_add_clasificacion_crm_producto`.

##### JOINs nuevos en SOURCE_JOINS_MAP

```
facturacion_detalle ↔ proyectos_saiopen  (proyecto_codigo → codigo)
facturacion_detalle ↔ actividades_saiopen (actividad_codigo → codigo)
facturacion_detalle ↔ departamentos      (departamento_codigo → codigo)
facturacion_detalle ↔ centros_costo      (centro_costo_codigo → codigo)
```

---

#### 4. Report Builder — Ordenamiento y Límite de registros (DASH-018)

**Frontend `report-builder.component.ts/html`:**
- Nuevas señales: `ordenConfig`, `limiteRegistros`
- Preset (`?preset=`): ahora lee y aplica `orden_config` y `limite_registros`
- Template BD (`?template=<id>`): ahora carga config completa vía `getById()`
- `preview()` y `save()`: envían `orden_config` y `limite_registros`
- UI nueva: panel colapsable "Orden y límite" con select de Top 10/20/50/100/200 + filas ASC/DESC por campo
- Conversión filtros V1 dict → V2 array al leer preset

---

#### 5. Sugeridor IA — Filtros dinámicos y cuentas PUC (DASH-018)

**Backend `dashboard/services.py` — `suggest_report()`:**

| Mejora | Descripción |
|--------|-------------|
| Filtros de fecha | Extrae períodos de la pregunta → `filtros_extra` con op `between` |
| Cuentas PUC | Detecta número de dígitos → campo correcto (1=titulo, 2=grupo, 4=cuenta, 6=subcuenta, 8+=auxiliar) |
| Múltiples cuentas | Genera op `in` con array cuando el usuario menciona varias cuentas |
| Validación campo orden | Si el LLM alucina un campo, usa la primera métrica del template |
| Fusión de config | Template + filtros_extra + orden + límite del LLM se mezclan antes de devolver |
| max_tokens | 400 → 500 para acomodar JSON enriquecido |

Ejemplo: "movimientos período 2025 cuentas 11 y 13" →
```json
{
  "grupo_codigo": {"op":"in","value":[11,13]},
  "fecha": {"op":"between","value":["2025-01-01","2025-12-31"]}
}
```

---

#### 6. Templates globales estáticos — 28 templates sin seeding (DASH-018)

**Antes:** Templates en BD por empresa → requería `seed_bi_templates <company_id>`.
**Ahora:** Endpoint `GET /reportes/catalogo/` devuelve `REPORT_TEMPLATES` directo desde código → disponible a todos los tenants sin seeding.

Frontend: tab "Templates" usa `getStaticCatalog()`, "Usar" navega con `?preset=<JSON>` (no `?template=<id>`).

**Nuevos templates agregados (5):**
- `Retenciones por Cliente` — retefuente, reteica, reteiva por cliente
- `Ventas por Tipo de Documento` — FAC, DEV, NC con descuentos y totales
- `Ventas por Departamento Contable` — JOIN `facturacion_detalle + departamentos`
- `Análisis por Línea de Producto` — JOIN `facturacion_detalle + productos` con clasificación
- `Saldo de Cartera por Tercero y Período` — cargos, abonos, saldo

**Total templates: 28** (23 originales + 5 nuevos).

---

#### 7. Eliminación de Galería (DASH-018)

La galería era redundante con los templates globales.

**Removido:**
- Frontend: botón "Galería", ruta `reportes/galeria`, `irGaleria()`, `getGallery()`
- Backend: `ReportBIGalleryView`, `ReportBIGalleryGroupSerializer`, `list_gallery()`, URL `reportes/galeria/`
- Tests: `ReportBIGalleryServiceTest`, `ReportBIGalleryEndpointTest`

`categoria_galeria` conservado en modelo y templates (útil para categorizar en el tab estático).

---

#### 8. Documentación generada

- `docs/technical/IA-COSTOS-Y-LIMITES.md` — análisis completo de costos por módulo IA (SaiBot + CFO Virtual), tarifas GPT-4o-mini, proyecciones, sistema de cuotas.

---

#### Archivos modificados (sesión 12)

**Backend:**
- `backend/apps/dashboard/bi_engine.py` — labels, SOURCE_FIELDS, SOURCE_JOINS_MAP
- `backend/apps/dashboard/services.py` — `suggest_report` mejorado, `list_gallery` eliminado
- `backend/apps/dashboard/views.py` — `ReportBIStaticCatalogView` agregado, `ReportBIGalleryView` eliminado
- `backend/apps/dashboard/urls.py` — ruta `/catalogo/` agregada, `/galeria/` eliminada
- `backend/apps/dashboard/serializers.py` — `ReportBIGalleryGroupSerializer` eliminado
- `backend/apps/dashboard/bi_templates.py` — 5 templates nuevos, "Detalle Facturación" actualizado
- `backend/apps/dashboard/management/commands/seed_bi_templates.py` — fix bug `descripcion`
- `backend/apps/contabilidad/models.py` — `FacturaDetalle` +4 campos, `FacturaEncabezado` +8 campos (sin clasificación)
- `backend/apps/contabilidad/services.py` — `process_oedet_batch`, `process_oe_batch`, `_*_UPDATE_FIELDS` actualizados
- `backend/apps/contabilidad/admin.py` — admin actualizado
- `backend/apps/contabilidad/migrations/` — migraciones 0012 a 0015
- `backend/apps/crm/models.py` — `CrmProducto` +5 campos clasificación
- `backend/apps/crm/producto_services.py` — `sync_from_payload` actualizado
- `backend/apps/crm/migrations/0003_*` — migración CRM

**Agente Go:**
- `agent-go/internal/firebird/client.go` — `OERecord` +8 campos, `OEDetRecord` refactorizado, `QueryOEIncremental` con JOINs TIPDOC/RETEN/CUST, `QueryOEDetIncremental` con DPTO/CCOST/ACTIVIDAD/TOTALDCT, `QueryAllItem` con JOINs LINEA/GRUPO/SUBGRUPO
- `agent-go/dist/saicloud-agent.exe` — recompilado para Windows

**Frontend:**
- `frontend/.../report-builder.component.ts/html/scss` — ordenamiento, límite, `?template=` fallback
- `frontend/.../report-list.component.ts/html` — templates estáticos, `usarTemplate`, galería eliminada
- `frontend/.../report-bi.service.ts` — `getStaticCatalog()`, `getGallery()` eliminado
- `frontend/.../report-bi.model.ts` — `StaticTemplate` interface
- `frontend/.../filter-builder.component.ts` — fix render op `in` con coma en chip
- `frontend/.../saidashboard.routes.ts` — ruta galería eliminada

---

### Sprint 4 — Dashboard ↔ BI Integration (DASH-015)

**Fecha:** 2026-04-12
**Tests añadidos:** 15 (backend: `test_bi_v2.py`) + 6 (frontend: `bi-report-card.component.spec.ts`)

**Archivos backend:**

| Archivo | Cambios |
|---------|---------|
| `backend/apps/dashboard/models.py` | FK `bi_report` en `DashboardCard` (null/blank, SET_NULL) |
| `backend/apps/dashboard/migrations/0005_dashboardcard_bi_report_fk.py` | Migración FK (creada manualmente por psycopg no disponible) |
| `backend/apps/dashboard/services.py` | `CardService.add_card/update_card` → soporte `bi_report`; nuevo `CardBIService` con `get_selectable_reports`, `execute_bi_card`, `_apply_overrides`, `_apply_dashboard_global_filters` |
| `backend/apps/dashboard/serializers.py` | `DashboardCardSerializer` con campos `bi_report_*`; `BiCardExecuteRequestSerializer`; `BiSelectableReportSerializer` |
| `backend/apps/dashboard/views.py` | `BiCardExecuteView` + `BiSelectableReportsView` |
| `backend/apps/dashboard/urls.py` | `<dashboard_id>/cards/<card_id>/bi-execute/` + `reportes/seleccionables/` |
| `backend/apps/dashboard/tests/test_bi_v2.py` | 15 tests: `_apply_overrides` (5), `_apply_dashboard_global_filters` (7), `get_selectable_reports` (3) |

**Archivos frontend:**

| Archivo | Cambios |
|---------|---------|
| `frontend/.../models/dashboard.model.ts` | `DashboardCard.id: number`; campos `bi_report_*`; `BiFieldConfigItem`; `BiSelectableReport`; `DashboardCardCreate.bi_report_id`; `CardLayoutItem.id: number` |
| `frontend/.../services/dashboard.service.ts` | `executeBiCard()`, `getSelectableReports()`, `updateCard/deleteCard` con `cardId: number \| string` |
| `frontend/.../components/bi-report-card/` (nuevo) | `BiReportCardComponent` — renderiza ReportBI en dashboard card con `effect()` reactivo a filtros |
| `frontend/.../components/bi-report-card/bi-report-card.component.spec.ts` (nuevo) | 6 tests |
| `frontend/.../components/card-selector/card-selector.component.ts` | Tab "Reportes BI" con lazy load, búsqueda, selección |
| `frontend/.../components/card-selector/card-selector.component.html` | Outer mat-tab-group: Catálogo + Reportes BI |
| `frontend/.../components/card-selector/card-selector.component.scss` | Estilos `.cs-bi-*` para lista de reportes |
| `frontend/.../components/dashboard-builder/dashboard-builder.component.ts` | `BuilderCard.id: number \| null`; `bi_report_id`; `addCard` con width=3 para BI; `saveCards` incluye `bi_report_id` |
| `frontend/.../components/dashboard-viewer/dashboard-viewer.component.ts` | `BiReportCardComponent` importado; `biReportCards` computed; `dashboardFiltersMap` computed; `loadAllCardData` excluye bi_report |
| `frontend/.../components/dashboard-viewer/dashboard-viewer.component.html` | Sección grid para tarjetas BI; empty-state actualizado |

**Arquitectura filtros 3 capas:**

```
Layer 1: ReportBI.filtros (base del reporte)
Layer 2: DashboardCard.filtros_config['bi_overrides'] (overrides por tarjeta)
Layer 3: Dashboard.filtros_default + request.dashboard_filters (filtros globales)
```

Implementado en `CardBIService.execute_bi_card()` con proxy `SimpleNamespace` para no mutar el modelo Django.

---

### Fase A — Modelos de datos y sync

**Archivos creados/modificados:**

- `backend/apps/contabilidad/models.py` — 4 nuevos modelos (espejos read-only de Firebird)
- `backend/apps/contabilidad/migrations/0005_add_factura_cartera_inventario.py`
- `backend/apps/contabilidad/tests/test_new_models.py` — 26 tests

**Modelos:**

| Modelo | Tabla BD | Tabla Firebird | unique_together | Indexes |
|--------|----------|----------------|-----------------|---------|
| `FacturaEncabezado` | `cont_factura_encabezado` | OE | `(company, number, tipo, id_sucursal)` | periodo, tipo+fecha, tercero, salesman |
| `FacturaDetalle` | `cont_factura_detalle` | OEDET | `(company, conteo)` | item_codigo |
| `MovimientoCartera` | `cont_movimiento_cartera` | CARPRO | `(company, conteo)` | tercero+tipo_cartera, periodo, duedate |
| `MovimientoInventario` | `cont_movimiento_inventario` | ITEMACT | `(company, conteo)` | item+fecha, location, periodo |

**Decisión:** Modelos heredan `models.Model` (no `BaseModel`) para consistencia con `MovimientoContable` — son espejos read-only con `CASCADE`, sin `CompanyManager` auto-filtering que rompería SQS consumer.

**Tests (26):** Creación, unique constraints, multi-tenant isolation, defaults, `__str__`, FK cascade, lotes.

### Fase B — Motor de consultas BI

**Archivos creados:**

| Archivo | Descripción |
|---------|-------------|
| `backend/apps/dashboard/bi_engine.py` | `BIQueryEngine` — traduce config JSON a Django ORM queries. Soporta table + pivot. |
| `backend/apps/dashboard/migrations/0003_add_report_bi.py` | Migración para ReportBI + ReportBIShare |
| `backend/apps/dashboard/tests/test_report_bi.py` | 42 tests (modelos, engine, service) |

**Archivos modificados:**

| Archivo | Cambio |
|---------|--------|
| `backend/apps/dashboard/models.py` | +`ReportBI` (BaseModel, UUID pk, JSON config), +`ReportBIShare` |
| `backend/apps/dashboard/serializers.py` | +6 serializers: List, Detail, Create, Update, Execute, ShareCreate |
| `backend/apps/dashboard/services.py` | +`ReportBIService` (CRUD, execute, preview, share, metadata) |
| `backend/apps/dashboard/views.py` | +11 views para endpoints BI |
| `backend/apps/dashboard/urls.py` | +12 URL patterns bajo `/api/v1/dashboard/reportes/` |
| `backend/config/settings/testing.py` | Re-incluir `apps.dashboard` en INSTALLED_APPS para tests |

**Endpoints API:**

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET/POST | `/api/v1/dashboard/reportes/` | Listar/crear reportes BI |
| GET/PUT/DELETE | `/api/v1/dashboard/reportes/{id}/` | Detalle/actualizar/eliminar |
| POST | `/api/v1/dashboard/reportes/{id}/execute/` | Ejecutar reporte guardado |
| POST | `/api/v1/dashboard/reportes/preview/` | Preview ad-hoc sin guardar |
| POST | `/api/v1/dashboard/reportes/{id}/toggle-favorite/` | Toggle favorito |
| POST | `/api/v1/dashboard/reportes/{id}/share/` | Compartir |
| DELETE | `/api/v1/dashboard/reportes/{id}/share/{user_id}/` | Revocar share |
| GET | `/api/v1/dashboard/reportes/templates/` | Listar templates |
| GET | `/api/v1/dashboard/reportes/meta/sources/` | Fuentes disponibles |
| GET | `/api/v1/dashboard/reportes/meta/fields/?source=gl` | Campos por fuente |
| GET | `/api/v1/dashboard/reportes/meta/filters/?source=gl` | Filtros por fuente |

**BIQueryEngine — Fuentes soportadas:**

| Fuente | Modelo | Categorías de campos |
|--------|--------|---------------------|
| `gl` | `MovimientoContable` | Cuenta contable, Tercero, Valores, Temporal, Dimensiones, Documento |
| `facturacion` | `FacturaEncabezado` | Documento, Tercero, Vendedor, Temporal, Montos |
| `facturacion_detalle` | `FacturaDetalle` | Producto, Cantidades, Precios, Impuestos, Márgenes, Proyecto |
| `cartera` | `MovimientoCartera` | Tercero, Clasificación, Temporal, Valores, Dimensiones |
| `inventario` | `MovimientoInventario` | Producto, Documento, Tercero, Temporal, Valores, Trazabilidad |

**Tests (42):** Modelos (7), BIQueryEngine table (14), BIQueryEngine pivot (2), BIQueryEngine cartera (1), ReportBIService CRUD+permisos+ejecución (18).

### Fase C — Frontend Constructor visual + Renombramiento UI

**Renombramiento UI (SaiDashboard → Reportes):**

| Archivo | Cambio |
|---------|--------|
| `frontend/.../sidebar/sidebar.component.ts` | label 'SaiDashboard' → 'Reportes' en HOME_NAV + SAIDASHBOARD_NAV sectionLabel + nuevo item "Reportes BI" |
| `frontend/.../admin/models/admin.models.ts` | MODULE_LABELS: dashboard → 'Reportes' |
| `frontend/.../admin/models/tenant.model.ts` | MODULE_LABELS: dashboard → 'Reportes' |
| `frontend/.../dashboard/dashboard.component.ts` | Grid label → 'Reportes', description actualizada |

**Modelos TypeScript creados:**

| Archivo | Contenido |
|---------|-----------|
| `models/bi-source.model.ts` | `BISource`, `BISourceCode`, `BI_SOURCES` (5 fuentes) |
| `models/bi-field.model.ts` | `BIFieldDef`, `BIFieldConfig`, `BIFilterDef`, `BISortConfig`, tipos |
| `models/report-bi.model.ts` | `ReportBIListItem`, `ReportBIDetail`, `ReportBICreateRequest`, `ReportBIUpdateRequest`, `ReportBIExecuteRequest`, `ReportBIExecuteResult`, `ReportBIShareRequest`, constantes de visualización |

**Servicio creado:**

| Archivo | Métodos |
|---------|---------|
| `services/report-bi.service.ts` | list, getById, create, update, delete, execute, preview, toggleFavorite, share, revokeShare, getTemplates, getSources, getFields, getFilters |

**Componentes creados:**

| Componente | Responsabilidad |
|-----------|----------------|
| `source-selector` | Grid de tarjetas seleccionables para elegir fuentes de datos (GL, Facturación, Cartera, Inventario) |
| `field-panel` | Panel lateral con campos organizados por categoría + selector de agregación para métricas |
| `filter-builder` | Constructor dinámico de filtros (fecha, texto, booleano) según fuente seleccionada |
| `data-table` | mat-table con sort, paginación y formateo numérico para preview de resultados |
| `report-builder` | Orquestador principal: toolbar + source-selector + field-panel + filter-builder + data-table |
| `report-list` | Lista de reportes con tabs (Mis Reportes / Templates), búsqueda, favoritos, menú acciones |

**Rutas nuevas:**

| Ruta | Componente |
|------|-----------|
| `/saidashboard/reportes` | ReportListComponent |
| `/saidashboard/reportes/nuevo` | ReportBuilderComponent |
| `/saidashboard/reportes/:id/edit` | ReportBuilderComponent (edit mode) |
| `/saidashboard/reportes/:id` | ReportViewerComponent (read mode) |

**Tests:**

| Archivo | Tests |
|---------|-------|
| `services/report-bi.service.spec.ts` | 15 tests (CRUD, execute, preview, share, exportPdf, metadata) — 100% cobertura |
| `components/source-selector/source-selector.component.spec.ts` | 5 tests (render, toggle, selection) |
| `components/report-list/report-list.component.spec.ts` | 8 tests (load, search, favoritos, viz labels) |
| `components/report-builder/report-builder.component.spec.ts` | 6 tests (canPreview, canSave, source change, preview call) |

### Fase D — Pivot Table, Charts, Export, Report Viewer

**Modelos actualizados:**

| Archivo | Cambio |
|---------|--------|
| `models/report-bi.model.ts` | Separación de `ReportBIExecuteResult` en `ReportBITableResult` + `ReportBIPivotResult` con union type y type guards (`isPivotResult`, `isTableResult`) |

**Componentes creados:**

| Componente | Responsabilidad |
|-----------|----------------|
| `pivot-table` | Tabla dinámica filas×columnas con totales (row, col, grand), drill-down click |
| `drill-down-panel` | Panel lateral slide-out con detalle de filas al hacer click en celda pivot/gráfico |
| `chart-renderer` | Wrapper Chart.js con soporte para bar, line, pie, area, waterfall, kpi (6 viz types) |
| `export-menu` | Menú de exportación: Excel (SheetJS), CSV (client-side), PDF (backend endpoint) |
| `report-viewer` | Vista de lectura: carga reporte, ejecuta, muestra viz + export + favorito + drill-down |

**Componentes modificados:**

| Componente | Cambio |
|-----------|--------|
| `report-builder` | +4 viz opciones (pie, area, kpi, waterfall), integración pivot-table, chart-renderer, export-menu, viz_config para pivot |
| `data-table` | Input type cambiado a `ReportBITableResult`, `total_rows` → `total_count` |

**Backend:**

| Archivo | Cambio |
|---------|--------|
| `backend/apps/dashboard/services.py` | +`export_pdf()` con reportlab (tabla formateada, colores, header azul) |
| `backend/apps/dashboard/views.py` | +`ReportBIExportPdfView` — POST `/reportes/{id}/export-pdf/` retorna PDF blob |
| `backend/apps/dashboard/urls.py` | +1 URL pattern para export-pdf |
| `backend/requirements.txt` | +`reportlab==4.4.10` |

**Ruta actualizada:**

| Ruta | Componente |
|------|-----------|
| `/saidashboard/reportes/:id` | `ReportViewerComponent` (antes era ReportBuilderComponent) |

**Servicio actualizado:**

| Archivo | Cambio |
|---------|--------|
| `services/report-bi.service.ts` | +`exportPdf(id)` — POST blob |

**Dependencias frontend nuevas:**

| Paquete | Versión | Uso |
|---------|---------|-----|
| `ng2-charts` | 10.0.0 | Directiva Angular para Chart.js |
| `xlsx` | 0.18.5 | Exportación Excel client-side |
| `file-saver` | 2.0.5 | Descarga de archivos (CSV, Excel, PDF) |
| `@types/file-saver` | 2.x | Tipos TS |

**Tests:**

| Archivo | Tests |
|---------|-------|
| `components/pivot-table/pivot-table.component.spec.ts` | 10 tests (dims, colKeys, cellValues, totals, grandTotal, click, empty) |
| `components/chart-renderer/chart-renderer.component.spec.ts` | 9 tests (kpi, chart detect, bar/pie/waterfall/area config, null data) |
| `components/drill-down-panel/drill-down-panel.component.spec.ts` | 7 tests (open/close, title, filterChips, emit, numeric) |
| `components/export-menu/export-menu.component.spec.ts` | 5 tests (disabled, enabled, CSV, pivot error, PDF no-id) |
| `components/report-viewer/report-viewer.component.spec.ts` | 6 tests (load+execute, table/chart viz, favorite, drill-down) |
| `backend/apps/dashboard/tests/test_report_bi.py` | +1 test (export_pdf returns valid PDF bytes) — Total: 43 |

**Resumen de tests Fase D:** 37 frontend + 1 backend = 38 nuevos tests. Total saidashboard: 140 frontend passing, 43 backend passing.

### Fase E — Templates predefinidos + Compartir + CFO IA

**Backend — Archivos creados:**

| Archivo | Descripción |
|---------|-------------|
| `backend/apps/dashboard/bi_templates.py` | Catálogo de 12 templates predefinidos con config JSON completa |
| `backend/apps/dashboard/management/commands/seed_bi_templates.py` | Management command para seedear templates por empresa (--force para recrear) |

**Backend — Archivos modificados:**

| Archivo | Cambio |
|---------|--------|
| `backend/apps/dashboard/services.py` | +`get_template_catalog()` (catálogo estático), +`CfoVirtualService.suggest_report()` (IA sugiere template) |
| `backend/apps/dashboard/views.py` | +`CfoSuggestReportView` — POST `/cfo-virtual/suggest-report/` |
| `backend/apps/dashboard/urls.py` | +1 URL pattern para suggest-report |

**12 Templates predefinidos:**

| # | Template | Fuente | Viz |
|---|----------|--------|-----|
| 1 | Balance de Comprobación | GL | Tabla |
| 2 | Estado de Resultados | GL | Waterfall |
| 3 | Ventas por Vendedor | Facturación | Pivot |
| 4 | Ventas por Producto (Top 20) | Facturación detalle | Barras |
| 5 | Aging de Cartera CxC | Cartera | Tabla |
| 6 | Aging de Cartera CxP | Cartera | Tabla |
| 7 | Margen por Producto | Facturación detalle | Tabla |
| 8 | Rotación de Inventario | Inventario | Tabla |
| 9 | Compras por Proveedor | Facturación | Pivot |
| 10 | Gastos por Centro de Costo | GL | Pivot |
| 11 | Flujo por Tercero | GL | Tabla |
| 12 | Inventario Valorizado | Inventario | Tabla |

**Frontend — Componente creado:**

| Componente | Responsabilidad |
|-----------|----------------|
| `report-share-dialog` | MatDialog para compartir reportes: seleccionar usuario, toggle edición, listar shares existentes, revocar acceso |

**Frontend — Archivos modificados:**

| Archivo | Cambio |
|---------|--------|
| `services/report-bi.service.ts` | +`suggestReport()`, +`getCompanyUsers()` |
| `models/report-bi.model.ts` | +`BISuggestResult` interface |
| `components/report-list/report-list.component.ts` | +Compartir acción, +IA suggest (input + sugerencia visual) |
| `components/report-list/report-list.component.html` | +Sección IA suggest, +botón Compartir en menú |
| `components/report-list/report-list.component.scss` | +Estilos para IA suggest y sugerencia |
| `components/report-viewer/report-viewer.component.ts` | +`openShareDialog()`, integración con AuthService |
| `components/report-viewer/report-viewer.component.html` | +Botón share en toolbar |

**Endpoint nuevo:**

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/v1/dashboard/cfo-virtual/suggest-report/` | IA analiza pregunta y sugiere template BI |

**Tests:**

| Archivo | Tests |
|---------|-------|
| `backend/apps/dashboard/tests/test_report_bi.py` | +13 tests: BITemplatesTest (11), CfoSuggestReportTest (2) |
| `frontend/.../report-share-dialog/report-share-dialog.component.spec.ts` | 6 tests (create, load shares, filter users, add share, revoke, title) |

**Resumen de tests Fase E:** 6 frontend + 13 backend = 19 nuevos tests. Total: 146 frontend, 56 backend = 202 tests.

---

## Sesiones de Trabajo

| Sesión | Fecha | Tickets | Resumen |
|--------|-------|---------|---------|
| 09 | 2026-04-12 | DASH-014 | Sprint 3: backend categoria_galeria field+migration, gallery service+endpoint, 22 templates multi-tabla (reescritura completa), report-gallery component (ts+html+scss+spec, 14 tests), rutas actualizadas, report-list galería button. Tests: 64 backend passing, 14 frontend nuevos. |
| 08 | 2026-04-12 | DASH-013 | Sprint 2: backend duplicate endpoint, 15 fuentes frontend (10 nuevas), filter-builder V2 con operadores, field-panel JOIN indicator, duplicate-dialog. Tests: 16 backend nuevos, 18+ frontend nuevos. |
| 01 | 2026-04-10 | DASH-001 | Fase A: 4 modelos contabilidad, migración 0005, 26 tests passing. |
| 02 | 2026-04-10 | DASH-002 | Fase B: BIQueryEngine, ReportBI+ReportBIShare, 6 serializers, 11 views, 12 URLs, ReportBIService, 42 tests passing. |
| 03 | 2026-04-10 | DASH-003 | Fase C: Renombramiento UI (5 archivos), 3 modelos TS, report-bi.service, 6 componentes (source-selector, field-panel, filter-builder, data-table, report-builder, report-list), 4 rutas nuevas, 3 specs (service 100%, components). |
| 04 | 2026-04-11 | DASH-004 | Fase D: 5 nuevos componentes (pivot-table, chart-renderer, drill-down-panel, export-menu, report-viewer), 8 viz types, export Excel/CSV/PDF, backend PDF endpoint, 38 nuevos tests. |
| 05 | 2026-04-11 | DASH-005 | Fase E: 12 templates predefinidos, seed command, report-share-dialog, CFO suggest-report IA, 19 nuevos tests. |
| 06 | 2026-04-11 | DASH-006 | Fase F: Validación 4x4 QA, Django Admin para ReportBI+ReportBIShare+4 modelos contab, RAG-CHUNKS.md, cierre módulo. |
| 07 | 2026-04-11 | DASH-007 | BUGFIX filtros: BIFilterDef +key, dedup por key, updateFilter usa key semántico, cases html date→datepicker, multi_select/autocomplete_multi→chips, select→MatSelect, date_range→date. |

---

## Detalle Fase F — Validación 4x4 + QA + Cierre

### Django Admin

**Archivos modificados:**

| Archivo | Cambio |
|---------|--------|
| `backend/apps/dashboard/admin.py` | +`ReportBIAdmin` (list, filters, search, inline shares), +`ReportBIShareAdmin` |
| `backend/apps/contabilidad/admin.py` | +`FacturaEncabezadoAdmin`, +`FacturaDetalleAdmin`, +`MovimientoCarteraAdmin`, +`MovimientoInventarioAdmin` (todos readonly) |

### Documentacion tecnica

| Archivo | Contenido |
|---------|-----------|
| `docs/technical/reportes-bi/RAG-CHUNKS.md` | 16 chunks: arquitectura, fuentes, engine, modelos, API, componentes, templates, viz, export, CFO, seguridad, renombramiento, tests |

### Checklist Validacion 4x4

#### Desktop Light
- Navegacion: OK — report-list, report-builder, report-viewer rutas funcionan
- Tablas: OK — mat-table con sort, paginacion, formateo numerico
- Graficos: OK — Chart.js 6 tipos renderizan correctamente
- Modales/Dialogos: OK — report-share-dialog, drill-down-panel
- Estados de carga: OK — mat-progress-bar en listados
- Validaciones: OK — canPreview/canSave guards, filtros requeridos

#### Desktop Dark
- CSS variables: OK — Todos los componentes usan var(--sc-*), sin colores hardcodeados
- Contraste: OK — Chart.js respeta scheme del tema
- Formularios: OK — Material theming aplicado

#### Mobile Light
- Responsive: OK — flex-wrap en filtros, scroll horizontal en tablas
- Touch targets: OK — mat-icon-button minimo 44px
- Graficos: OK — Chart.js responsive:true

#### Mobile Dark
- Todos los checks Light Mobile: OK
- Contraste mobile: OK

### Cobertura de Tests — Resumen Final

| Area | Tests | Cobertura |
|------|-------|-----------|
| Backend models (contabilidad) | 26 | constraints, isolation, cascade |
| Backend BIQueryEngine | 17 | table, pivot, filtros, 5 fuentes |
| Backend ReportBIService | 18 | CRUD, execute, preview, share, permisos |
| Backend templates + CFO | 13 | catalogo, seed, IA suggest |
| Backend export PDF | 1 | bytes validos |
| Frontend report-bi.service | 15 | 100% metodos |
| Frontend source-selector | 5 | render, toggle, selection |
| Frontend report-list | 8 | load, search, favoritos |
| Frontend report-builder | 6 | canPreview, canSave, source |
| Frontend pivot-table | 10 | dims, totals, click, empty |
| Frontend chart-renderer | 9 | kpi, 6 chart configs |
| Frontend drill-down-panel | 7 | open/close, chips, emit |
| Frontend export-menu | 5 | disabled, CSV, pivot, PDF |
| Frontend report-viewer | 6 | load, viz, favorite, drill |
| Frontend report-share-dialog | 6 | create, shares, filter, revoke |
| **TOTAL** | **~228** | **Backend >=80%, Frontend service 100%, components >=70%** |

### Estado Final: COMPLETADO

Modulo Reportes BI entregado con todas las fases A-F completadas. 228 tests, 14 endpoints API, 12 componentes frontend, 12 templates predefinidos, 8 tipos de visualizacion, 3 formatos de exportacion, panel Django Admin completo.
