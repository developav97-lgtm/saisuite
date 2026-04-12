# PROGRESS: Reportes (SaiDashboard)

**Estado:** ✅ COMPLETADO
**Tipo:** FEATURE
**Fase actual:** F — Validación 4x4 + QA (completada)
**Inicio:** 2026-04-10
**Última sesión:** 2026-04-11
**Fecha cierre:** 2026-04-11
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

---

## Detalle de implementación

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
