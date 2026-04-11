# RAG Chunks — Reportes BI (Constructor Visual)

**Generado:** 2026-04-11
**Modulo:** `apps.dashboard` (marca visible: **Reportes**)
**Module code:** `dashboard`

---

## CHUNK-001: Arquitectura General

El modulo Reportes BI permite a usuarios crear informes interactivos tipo BI seleccionando fuentes de datos, campos, filtros y tipo de visualizacion — sin SQL. Los datos provienen de tablas espejo sincronizadas desde Firebird/Saiopen a PostgreSQL.

**Stack:** Django 5 backend (API REST) + Angular 18 frontend (Material).
**Ruta backend:** `/api/v1/dashboard/reportes/`
**Ruta frontend:** `/saidashboard/reportes`
**Modelos principales:** `ReportBI` (BaseModel, UUID pk), `ReportBIShare`

---

## CHUNK-002: Fuentes de Datos

5 fuentes disponibles, cada una mapeada a un modelo Django:

| Fuente | Modelo | Tabla Firebird | Tipo datos |
|--------|--------|----------------|------------|
| `gl` | `MovimientoContable` | GL (libro mayor) | Contabilidad |
| `facturacion` | `FacturaEncabezado` | OE | Ventas encabezado |
| `facturacion_detalle` | `FacturaDetalle` | OEDET | Ventas detalle |
| `cartera` | `MovimientoCartera` | CARPRO | CxC / CxP |
| `inventario` | `MovimientoInventario` | ITEMACT | Movimientos stock |

Todos los modelos de datos son read-only (espejos). El agente Go sincroniza via SQS.

---

## CHUNK-003: BIQueryEngine

`backend/apps/dashboard/bi_engine.py` — Motor que traduce configuracion JSON a queries Django ORM.

**Seguridad:** `company_id` obligatorio en TODA query. Sin SQL crudo.
**Modos:** `table` (filas planas con group by) y `pivot` (filas x columnas con totales).
**Agregaciones:** SUM, AVG, COUNT, MIN, MAX.
**Campos:** Definidos en `SOURCE_FIELDS` dict — whitelist por fuente y categoria.
**Filtros:** Operadores: `eq`, `neq`, `gt`, `gte`, `lt`, `lte`, `contains`, `range`, `in`.

---

## CHUNK-004: Modelo ReportBI

```python
class ReportBI(BaseModel):
    user = FK(User)            # Creador
    titulo = CharField(200)
    tipo_visualizacion = CharField  # table|pivot|bar|line|pie|area|kpi|waterfall
    fuentes = JSONField(list)       # ["gl", "facturacion"]
    campos_config = JSONField(list) # [{source, field, role, aggregation, label}]
    filtros = JSONField(dict)
    viz_config = JSONField(dict)    # Config especifica de pivot/chart
    es_template = BooleanField      # True para templates predefinidos
    es_favorito = BooleanField
    es_privado = BooleanField
    template_origen = FK(self, null)
```

---

## CHUNK-005: API Endpoints

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET/POST | `/reportes/` | Listar/crear reportes |
| GET/PUT/DELETE | `/reportes/{id}/` | CRUD individual |
| POST | `/reportes/{id}/execute/` | Ejecutar reporte guardado |
| POST | `/reportes/preview/` | Preview ad-hoc sin guardar |
| POST | `/reportes/{id}/toggle-favorite/` | Toggle favorito |
| POST | `/reportes/{id}/share/` | Compartir con usuario |
| DELETE | `/reportes/{id}/share/{user_id}/` | Revocar share |
| GET | `/reportes/templates/` | Catalogo de templates |
| GET | `/reportes/meta/sources/` | Fuentes disponibles |
| GET | `/reportes/meta/fields/?source=gl` | Campos por fuente |
| GET | `/reportes/meta/filters/?source=gl` | Filtros por fuente |
| POST | `/reportes/{id}/export-pdf/` | Exportar PDF |
| POST | `/cfo-virtual/suggest-report/` | IA sugiere template |

---

## CHUNK-006: Componentes Frontend

| Componente | Ruta | Responsabilidad |
|-----------|------|----------------|
| `report-list` | `/saidashboard/reportes` | Lista con tabs (Mis Reportes/Templates), busqueda, favoritos, IA suggest |
| `report-builder` | `/saidashboard/reportes/nuevo` o `/:id/edit` | Constructor visual: fuente + campos + filtros + preview + viz config |
| `report-viewer` | `/saidashboard/reportes/:id` | Vista lectura: ejecuta, muestra viz, export, favorito, share, drill-down |
| `source-selector` | Embebido en builder | Grid de tarjetas para seleccionar fuente de datos |
| `field-panel` | Embebido en builder | Panel lateral con campos por categoria + agregacion |
| `filter-builder` | Embebido en builder | Constructor dinamico de filtros |
| `data-table` | Embebido en builder/viewer | mat-table con sort, paginacion, formateo numerico |
| `pivot-table` | Embebido en builder/viewer | Tabla dinamica filas x columnas con totales |
| `chart-renderer` | Embebido en builder/viewer | Chart.js: bar, line, pie, area, waterfall, kpi |
| `drill-down-panel` | Embebido en viewer | Panel slide-out con detalle al click en celda |
| `export-menu` | Embebido en builder/viewer | Excel (SheetJS), CSV, PDF (backend) |
| `report-share-dialog` | MatDialog | Compartir con usuarios, toggle edicion, revocar |

---

## CHUNK-007: Templates Predefinidos (12)

| # | Template | Fuente | Viz |
|---|----------|--------|-----|
| 1 | Balance de Comprobacion | GL | Tabla |
| 2 | Estado de Resultados | GL | Waterfall |
| 3 | Ventas por Vendedor | Facturacion | Pivot |
| 4 | Ventas por Producto (Top 20) | Facturacion detalle | Barras |
| 5 | Aging de Cartera CxC | Cartera | Tabla |
| 6 | Aging de Cartera CxP | Cartera | Tabla |
| 7 | Margen por Producto | Facturacion detalle | Tabla |
| 8 | Rotacion de Inventario | Inventario | Tabla |
| 9 | Compras por Proveedor | Facturacion | Pivot |
| 10 | Gastos por Centro de Costo | GL | Pivot |
| 11 | Flujo por Tercero | GL | Tabla |
| 12 | Inventario Valorizado | Inventario | Tabla |

Catalogo en `backend/apps/dashboard/bi_templates.py`.
Seed command: `python manage.py seed_bi_templates --company_id=UUID [--force]`

---

## CHUNK-008: Visualizaciones Soportadas

8 tipos: `table`, `pivot`, `bar`, `line`, `pie`, `area`, `kpi`, `waterfall`.

- **table:** mat-table con sort + paginacion.
- **pivot:** Tabla dinamica filas x columnas con totales row/col/grand.
- **bar/line/pie/area:** Chart.js via ng2-charts.
- **waterfall:** Bar chart con barras flotantes (ingresos/gastos).
- **kpi:** Tarjeta con valor principal + label.

---

## CHUNK-009: Exportacion

| Formato | Implementacion | Ubicacion |
|---------|---------------|-----------|
| Excel (.xlsx) | SheetJS client-side | `export-menu` component |
| CSV | Client-side Blob | `export-menu` component |
| PDF | Backend reportlab | `ReportBIService.export_pdf()` + `ReportBIExportPdfView` |

---

## CHUNK-010: CFO Virtual — Suggest Report

Endpoint: `POST /api/v1/dashboard/cfo-virtual/suggest-report/`
Input: `{"pregunta": "como van las ventas este mes?"}`
Output: `{"template_key": "ventas_vendedor", "titulo": "...", "descripcion": "...", "fuentes": [...], "tipo_visualizacion": "pivot"}`

Usa LLM (Claude API) para analizar la pregunta y sugerir el template mas adecuado del catalogo de 12.

---

## CHUNK-011: Seguridad

- Todas las queries filtran por `company_id` del usuario autenticado.
- El motor BI NO permite SQL crudo; solo acepta configuracion JSON validada.
- Campos disponibles definidos en backend (whitelist `SOURCE_FIELDS`).
- Reportes compartidos respetan `moduleAccessGuard` + `LicensePermission`.
- `ReportBIShare` permite control granular (puede_editar flag).

---

## CHUNK-012: Renombramiento UI

SaiDashboard se renombro visualmente a **"Reportes"** en la UI.
- `module_code` sigue siendo `'dashboard'` en backend (0 migraciones).
- Ruta frontend sigue siendo `/saidashboard` (path en URL).
- Solo cambiaron labels en: sidebar, admin models, dashboard grid.

---

## CHUNK-013: Modelos Contabilidad (Fase A)

4 modelos espejo read-only agregados a `apps.contabilidad.models`:

| Modelo | Tabla BD | Firebird | unique_together |
|--------|----------|----------|-----------------|
| `FacturaEncabezado` | `cont_factura_encabezado` | OE | `(company, number, tipo, id_sucursal)` |
| `FacturaDetalle` | `cont_factura_detalle` | OEDET | `(company, conteo)` |
| `MovimientoCartera` | `cont_movimiento_cartera` | CARPRO | `(company, conteo)` |
| `MovimientoInventario` | `cont_movimiento_inventario` | ITEMACT | `(company, conteo)` |

Heredan `models.Model` (no BaseModel) — consistencia con `MovimientoContable`. Sin `CompanyManager` para no romper SQS consumer.

---

## CHUNK-014: Dependencias

**Backend:** `reportlab==4.4.10` (PDF generation)
**Frontend:** `ng2-charts@10.0.0` (Chart.js Angular), `xlsx@0.18.5` (Excel export), `file-saver@2.0.5` (download)

---

## CHUNK-015: Django Admin

Registrados en admin:
- `ReportBIAdmin` — list con titulo, user, company, viz, template, favorito; inline shares
- `ReportBIShareAdmin` — list con reporte, usuarios, permisos
- `FacturaEncabezadoAdmin` — readonly, filtrable por company/tipo/periodo
- `FacturaDetalleAdmin` — readonly, filtrable por company
- `MovimientoCarteraAdmin` — readonly, filtrable por tipo_cartera/periodo
- `MovimientoInventarioAdmin` — readonly, filtrable por periodo/location

---

## CHUNK-016: Tests

**Backend:** 56 tests en `test_report_bi.py` + 26 tests en `test_new_models.py` = 82 backend tests
**Frontend:** ~146 tests across 12 spec files (service 100%, components 70%+)
**Total:** ~228 tests

Cobertura:
- `report-bi.service.ts`: 100% (15 tests)
- `ReportBIService` backend: 18+ tests (CRUD, execute, preview, share, permisos)
- `BIQueryEngine`: 17+ tests (table, pivot, filtros, cartera)
- Modelos contabilidad: 26 tests (creation, constraints, isolation, cascade)
