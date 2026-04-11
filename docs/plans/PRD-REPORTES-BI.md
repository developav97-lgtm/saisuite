# PRD — Constructor de Reportes BI (Módulo Reportes)
**Versión:** 1.0
**Fecha:** 10 Abril 2026
**Autor:** Juan David + Cowork (Opus)
**Módulo destino:** `apps.dashboard` (marca visible: **Reportes**)
**Fase Metodología:** 1 — Planificación
**Dependencias:** SaiDashboard backend existente, app contabilidad (GL sync), agente Go

---

## 1. RESUMEN EJECUTIVO

Agregar al módulo SaiDashboard (renombrado visualmente a **"Reportes"**) un constructor visual de informes tipo BI que permita a los usuarios seleccionar fuentes de datos (contabilidad, facturación, inventario, cartera), elegir campos/métricas, aplicar filtros y generar tablas, gráficos y tablas dinámicas (pivot) de forma interactiva — sin necesidad de conocer SQL.

Inspirado en la herramienta BI actual del cliente (conexión ODBC + Excel + tablas dinámicas) y en Odoo Spreadsheet (inserción de datos del ERP con fórmulas dinámicas, filtros globales, pivots). La diferencia clave: todo se ejecuta sobre datos ya sincronizados en PostgreSQL, sin conexión directa a Firebird.

---

## 2. PROBLEMA QUE RESUELVE

Actualmente los usuarios de Saiopen generan reportes conectando Excel por ODBC a la base Firebird local. Este flujo tiene limitaciones críticas: requiere conocer las tablas y campos de Firebird, depende de que el PC esté encendido, no permite colaboración, y los reportes son estáticos (snapshots). Con los datos ya sincronizados en Saicloud (GL + próximamente facturación e inventario), podemos ofrecer una experiencia BI moderna, en la nube, colaborativa y en tiempo real.

---

## 3. RENOMBRAMIENTO: SaiDashboard → Reportes

### 3.1 Decisión

Mantener el `module_code = 'dashboard'` en backend (0 migraciones, 0 riesgo). Cambiar **solo la marca visible** en la interfaz a **"Reportes"**.

### 3.2 Cambios necesarios (solo UI/labels)

| Archivo | Cambio | Riesgo |
|---------|--------|--------|
| `frontend/src/app/core/components/sidebar/sidebar.component.ts` | `label: 'SaiDashboard'` → `label: 'Reportes'` en SAIDASHBOARD_NAV y grid de módulos | Bajo |
| `frontend/src/app/features/admin/models/admin.models.ts` | `dashboard: 'SaiDashboard'` → `dashboard: 'Reportes'` en MODULE_LABELS | Bajo |
| `frontend/src/app/features/admin/models/tenant.model.ts` | `dashboard: 'SaiDashboard'` → `dashboard: 'Reportes'` | Bajo |
| `frontend/src/app/features/dashboard/dashboard.component.ts` | Grid item: `label: 'SaiDashboard'` → `label: 'Reportes'`, `description` actualizar | Bajo |
| `docs/manuales/MANUAL-SAIDASHBOARD-SAICLOUD.md` | Actualizar título y referencias | Bajo |

### 3.3 Lo que NO cambia

- `module_code = 'dashboard'` en `ModuleTrial`, `CompanyLicense`, `LicensePackage`
- `apps.dashboard` en Django `INSTALLED_APPS`
- Ruta backend: `/api/v1/dashboard/`
- Ruta frontend: `/saidashboard` (path en URL, no visible al usuario)
- `data: { requiredModule: 'dashboard' }` en routes
- Constante `_MODULE_CODE` en `services.py`
- Tablas de BD, migraciones existentes

### 3.4 Impacto total

~5 archivos, ~10 líneas. Sin migraciones. Sin riesgo de romper permisos, licencias o trials.

---

## 4. ARQUITECTURA DE DATOS — NUEVAS FUENTES

### 4.1 Fuentes actuales (ya sincronizadas)

| Fuente | Modelo Django | Tabla Firebird | Estado |
|--------|--------------|----------------|--------|
| Movimiento contable (GL) | `contabilidad.MovimientoContable` | GL + ACCT + CUST (denormalizado) | ✅ Implementado |
| Configuración contable | `contabilidad.ConfiguracionContable` | N/A | ✅ Implementado |

### 4.2 Fuentes nuevas a sincronizar

#### 4.2.1 Facturación — Modelo `FacturaEncabezado`

```python
# backend/apps/contabilidad/models.py
class FacturaEncabezado(BaseModel):
    """Espejo denormalizado de OE (encabezados de facturación)."""
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, db_index=True)

    # PK Firebird compuesta
    number = models.IntegerField()
    tipo = models.CharField(max_length=3, db_index=True)  # FA, NC, ND, OP, CO, RM, etc.
    id_sucursal = models.SmallIntegerField(default=1)

    # Tercero
    tercero_id = models.CharField(max_length=30, db_index=True)
    tercero_nombre = models.CharField(max_length=120, blank=True)

    # Vendedor
    salesman = models.SmallIntegerField(null=True)
    salesman_nombre = models.CharField(max_length=60, blank=True)

    # Fechas
    fecha = models.DateField(db_index=True)
    duedate = models.DateField(null=True)
    periodo = models.CharField(max_length=7, db_index=True)  # YYYY-MM

    # Montos
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    costo = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    iva = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    descuento_global = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Estado
    posted = models.BooleanField(default=False)
    closed = models.BooleanField(default=False)

    # Moneda
    cod_moneda = models.CharField(max_length=5, blank=True, default='COP')

    # Dimensiones (contabilidad analítica)
    comentarios = models.TextField(blank=True)

    class Meta:
        unique_together = ('company', 'number', 'tipo', 'id_sucursal')
        indexes = [
            models.Index(fields=['company', 'periodo']),
            models.Index(fields=['company', 'tipo', 'fecha']),
            models.Index(fields=['company', 'tercero_id']),
            models.Index(fields=['company', 'salesman']),
        ]
```

#### 4.2.2 Líneas de Factura — Modelo `FacturaDetalle`

```python
class FacturaDetalle(BaseModel):
    """Espejo denormalizado de OEDET (líneas de factura)."""
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, db_index=True)
    factura = models.ForeignKey(FacturaEncabezado, on_delete=models.CASCADE, related_name='detalles')

    conteo = models.IntegerField()  # PK Firebird

    # Producto
    item_codigo = models.CharField(max_length=30, db_index=True)
    item_descripcion = models.CharField(max_length=120, blank=True)
    location = models.CharField(max_length=3, blank=True)

    # Cantidades
    qty_order = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    qty_ship = models.DecimalField(max_digits=15, decimal_places=4, default=0)

    # Precios
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    precio_extendido = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    costo_unitario = models.DecimalField(max_digits=15, decimal_places=4, default=0)

    # Impuestos y descuentos
    valor_iva = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    porc_iva = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Márgenes
    margen_valor = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    margen_porcentaje = models.DecimalField(max_digits=7, decimal_places=2, default=0)

    # Proyecto
    proyecto_codigo = models.CharField(max_length=10, blank=True)

    class Meta:
        unique_together = ('company', 'conteo')
        indexes = [
            models.Index(fields=['company', 'item_codigo']),
        ]
```

#### 4.2.3 Cartera (CxC/CxP) — Modelo `MovimientoCartera`

```python
class MovimientoCartera(BaseModel):
    """Espejo de CARPRO — saldos de cuentas por cobrar y pagar."""
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, db_index=True)

    conteo = models.IntegerField()  # PK Firebird

    tercero_id = models.CharField(max_length=30, db_index=True)
    tercero_nombre = models.CharField(max_length=120, blank=True)

    cuenta_contable = models.DecimalField(max_digits=18, decimal_places=4)
    tipo = models.CharField(max_length=3)
    batch = models.IntegerField(null=True)
    invc = models.CharField(max_length=15, blank=True)
    descripcion = models.CharField(max_length=120, blank=True)

    fecha = models.DateField(db_index=True)
    duedate = models.DateField(null=True)
    periodo = models.CharField(max_length=7, db_index=True)

    debito = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credito = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    saldo = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    departamento = models.SmallIntegerField(null=True)
    centro_costo = models.SmallIntegerField(null=True)
    proyecto_codigo = models.CharField(max_length=10, blank=True)

    # Tipo: CxC o CxP (derivado de la cuenta contable: 13XX = CxC, 22XX = CxP)
    tipo_cartera = models.CharField(max_length=3, choices=[('CXC', 'Cuentas por Cobrar'), ('CXP', 'Cuentas por Pagar')], db_index=True)

    class Meta:
        unique_together = ('company', 'conteo')
        indexes = [
            models.Index(fields=['company', 'tercero_id', 'tipo_cartera']),
            models.Index(fields=['company', 'periodo']),
            models.Index(fields=['company', 'duedate']),
        ]
```

#### 4.2.4 Movimientos de Inventario — Modelo `MovimientoInventario`

```python
class MovimientoInventario(BaseModel):
    """Espejo de ITEMACT — movimientos transaccionales de inventario."""
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, db_index=True)

    conteo = models.IntegerField()  # PK Firebird

    item_codigo = models.CharField(max_length=30, db_index=True)
    item_descripcion = models.CharField(max_length=120, blank=True)
    location = models.CharField(max_length=3, db_index=True)

    tercero_id = models.CharField(max_length=30, blank=True)
    tipo = models.CharField(max_length=3)  # Tipo documento origen
    batch = models.IntegerField(null=True)

    fecha = models.DateField(db_index=True)
    periodo = models.CharField(max_length=7, db_index=True)

    cantidad = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    valor_unitario = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    costo_peps = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    saldo_unidades = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    saldo_pesos = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    lote = models.CharField(max_length=30, blank=True)
    serie = models.CharField(max_length=50, blank=True)
    lote_vencimiento = models.DateField(null=True)

    class Meta:
        unique_together = ('company', 'conteo')
        indexes = [
            models.Index(fields=['company', 'item_codigo', 'fecha']),
            models.Index(fields=['company', 'location']),
            models.Index(fields=['company', 'periodo']),
        ]
```

### 4.3 Sync incremental del agente Go

Las nuevas tablas se sincronizan igual que GL: el agente Go extrae de Firebird, publica en SQS, y Django consume e inserta/actualiza.

| Tabla Firebird | Watermark | Frecuencia | Batch size |
|----------------|-----------|------------|------------|
| OE + OEDET (join) | `MAX(OE.NUMBER)` por tipo | Cada 15 min | 200 encabezados |
| CARPRO | `MAX(CONTEO)` | Cada 15 min | 500 registros |
| ITEMACT | `MAX(CONTEO)` | Cada 15 min | 500 registros |
| ITEM (referencia) | Sync completo | Cada 24h | Full table |

---

## 5. FUNCIONALIDADES DEL CONSTRUCTOR DE REPORTES BI

### 5.1 Visión general

El Constructor de Reportes es una nueva sección dentro del módulo **Reportes** (antes SaiDashboard) que convive con las pantallas ya existentes (dashboards de tarjetas predefinidas, libro mayor). La experiencia se divide en:

```
/saidashboard                    → Lista de Mis Dashboards (existente)
/saidashboard/nuevo              → Builder de dashboards de tarjetas (existente)
/saidashboard/reportes           → Lista de Mis Reportes BI (NUEVO)
/saidashboard/reportes/nuevo     → Constructor visual BI (NUEVO)
/saidashboard/reportes/:id       → Visor de reporte guardado (NUEVO)
/saidashboard/reportes/:id/edit  → Editar reporte existente (NUEVO)
/saidashboard/libro-mayor        → Libro Mayor (existente)
```

### 5.2 Funcionalidades core

#### F1. Selector de Fuente de Datos

El usuario selecciona una o varias fuentes de datos disponibles. Las fuentes se presentan como tarjetas con ícono, nombre y descripción. Al seleccionar una fuente se cargan sus campos disponibles.

**Fuentes disponibles:**

| Fuente | Modelo | Ícono | Descripción |
|--------|--------|-------|-------------|
| Contabilidad (GL) | `MovimientoContable` | `account_balance` | Asientos contables, balances, estados financieros |
| Facturación | `FacturaEncabezado` + `FacturaDetalle` | `receipt_long` | Ventas, compras, notas crédito, devoluciones |
| Cartera (CxC/CxP) | `MovimientoCartera` | `payments` | Cuentas por cobrar, cuentas por pagar, aging |
| Inventario | `MovimientoInventario` | `inventory_2` | Entradas, salidas, saldos, rotación |

Cuando el usuario selecciona más de una fuente, el sistema genera automáticamente los JOINs disponibles (por tercero_id, periodo, proyecto_codigo).

#### F2. Selector de Campos (Columnas)

Una vez seleccionada la fuente, se muestra un panel lateral con los campos disponibles organizados por categoría. El usuario arrastra campos al área de construcción o los selecciona con checkbox.

**Categorías de campos (ejemplo para GL):**

| Categoría | Campos |
|-----------|--------|
| Cuenta contable | auxiliar, auxiliar_nombre, titulo_codigo, titulo_nombre, grupo_codigo, grupo_nombre, cuenta_codigo, cuenta_nombre, subcuenta_codigo, subcuenta_nombre |
| Tercero | tercero_id, tercero_nombre |
| Valores | debito, credito, saldo (calculado) |
| Temporal | fecha, periodo, año (derivado), mes (derivado) |
| Dimensiones | departamento_codigo, departamento_nombre, centro_costo_codigo, centro_costo_nombre, proyecto_codigo, actividad_codigo |
| Documento | tipo, batch, invc, descripcion |

Los campos numéricos permiten seleccionar la **función de agregación**: SUM, AVG, COUNT, MIN, MAX. Los campos de texto/fecha son **dimensiones** (agrupadores).

#### F3. Panel de Filtros

Filtros dinámicos que se adaptan a la fuente seleccionada:

| Filtro | Tipo | Aplica a |
|--------|------|----------|
| Rango de fechas | Date range picker | Todas |
| Período | Multi-select (YYYY-MM) | Todas |
| Tercero | Autocomplete multi-select | GL, Facturación, Cartera |
| Tipo documento | Chips select | GL, Facturación, Cartera |
| Cuenta contable | Tree select (PUC jerárquico) | GL, Cartera |
| Producto | Autocomplete multi-select | Facturación, Inventario |
| Bodega/Location | Select | Inventario |
| Vendedor | Select | Facturación |
| Proyecto | Multi-select | Todas (si tienen campo) |
| Centro de costo | Multi-select | GL, Cartera |
| Estado (posted/closed) | Toggle | Facturación |
| Tipo cartera (CxC/CxP) | Radio | Cartera |

Los filtros son **persistentes por reporte**: se guardan como JSON en el modelo del reporte.

#### F4. Tipos de Visualización

El usuario elige cómo presentar los datos:

| Tipo | Icono | Descripción | Mejor para |
|------|-------|-------------|------------|
| **Tabla** | `table_chart` | Tabla con paginación, ordenamiento y totales | Listados detallados, exportación a Excel |
| **Tabla Dinámica (Pivot)** | `pivot_table_chart` | Filas × Columnas × Valores con drill-down | Análisis multidimensional (ej: ventas por vendedor × mes) |
| **Gráfico de Barras** | `bar_chart` | Barras verticales/horizontales | Comparaciones entre categorías |
| **Gráfico de Líneas** | `show_chart` | Línea temporal | Tendencias y evolución |
| **Gráfico de Torta/Dona** | `donut_large` | Distribución porcentual | Composición (ej: ventas por tipo) |
| **Gráfico de Área** | `area_chart` | Área apilada | Evolución acumulativa |
| **KPI Card** | `speed` | Número grande con variación | Indicadores puntuales |
| **Waterfall** | `waterfall_chart` | Cascada | Balance, estado de resultados |

#### F5. Constructor Visual (Builder)

La pantalla principal del constructor se divide en 4 zonas:

```
┌─────────────────────────────────────────────────────────────┐
│  Toolbar: [Fuente ▼] [Guardar] [Exportar ▼] [Compartir]   │
├──────────┬──────────────────────────────────────────────────┤
│          │                                                   │
│  Panel   │           Zona de Preview                         │
│  Campos  │                                                   │
│          │   ┌─────────────────────────────────────────┐    │
│  □ campo1│   │                                         │    │
│  □ campo2│   │    Vista previa en tiempo real           │    │
│  □ campo3│   │    (tabla, gráfico, pivot)               │    │
│  ────────│   │                                         │    │
│  Métricas│   │                                         │    │
│  □ SUM   │   └─────────────────────────────────────────┘    │
│  □ AVG   │                                                   │
│          │   ┌─────────────────────────────────────────┐    │
├──────────┤   │  Configuración de visualización          │    │
│  Panel   │   │  [Tipo ▼] [Agrupar por ▼] [Ordenar ▼]  │    │
│  Filtros │   └─────────────────────────────────────────┘    │
│          │                                                   │
│  Fechas  │                                                   │
│  Tercero │                                                   │
│  ...     │                                                   │
│          │                                                   │
└──────────┴──────────────────────────────────────────────────┘
```

**Interacción principal:**

1. El usuario selecciona la fuente de datos (o múltiples fuentes)
2. El panel izquierdo muestra los campos disponibles organizados por categoría
3. El usuario selecciona campos arrastrando al área de "Columnas" o "Filas" (para pivot) o simplemente marcando checkboxes
4. Para campos numéricos, elige la agregación (SUM por defecto)
5. El preview se actualiza en tiempo real conforme cambia la configuración
6. Los filtros en el panel inferior-izquierdo refinan los datos
7. El selector de tipo de visualización cambia el preview instantáneamente

#### F6. Tabla Dinámica (Pivot Table)

La funcionalidad estrella, inspirada en Odoo y Excel:

**Configuración del Pivot:**

```
┌──────────────────────────────────────────────────┐
│  CONFIGURAR TABLA DINÁMICA                        │
│                                                    │
│  Filas:     [tercero_nombre ▼] [+ Agregar fila]  │
│  Columnas:  [periodo ▼]       [+ Agregar col]    │
│  Valores:   [SUM(debito) ▼]   [+ Agregar valor]  │
│             [SUM(credito) ▼]                      │
│                                                    │
│  [x] Mostrar totales de fila                      │
│  [x] Mostrar totales de columna                   │
│  [x] Mostrar gran total                           │
│  [ ] Mostrar porcentajes                          │
│                                                    │
│  Formato valores: [Moneda COP ▼]                  │
└──────────────────────────────────────────────────┘
```

**Resultado ejemplo (GL por tercero × periodo):**

```
┌──────────────────┬────────────┬────────────┬────────────┬──────────┐
│ Tercero          │ 2026-01    │ 2026-02    │ 2026-03    │ TOTAL    │
├──────────────────┼────────────┼────────────┼────────────┼──────────┤
│ Acme Corp        │ 5.200.000  │ 3.800.000  │ 6.100.000  │15.100.000│
│ Beta SAS         │ 2.100.000  │ 2.500.000  │ 1.900.000  │ 6.500.000│
│ Gamma Ltda       │   800.000  │ 1.200.000  │ 1.500.000  │ 3.500.000│
├──────────────────┼────────────┼────────────┼────────────┼──────────┤
│ TOTAL            │ 8.100.000  │ 7.500.000  │ 9.500.000  │25.100.000│
└──────────────────┴────────────┴────────────┴────────────┴──────────┘
```

**Drill-down:** Click en cualquier celda abre un panel lateral con los registros individuales que componen ese total.

#### F7. Reportes Predefinidos (Templates)

Reportes pre-configurados que el usuario puede usar directamente o como base para personalizar:

| Template | Fuente | Tipo | Descripción |
|----------|--------|------|-------------|
| Balance de Comprobación | GL | Tabla | Saldos por cuenta en un período |
| Estado de Resultados | GL | Waterfall | Ingresos - Costos - Gastos = Utilidad |
| Ventas por Vendedor | Facturación | Pivot | Vendedor × Mes × Total |
| Ventas por Producto (Top 20) | Facturación detalle | Barras | Productos más vendidos por cantidad o valor |
| Aging de Cartera CxC | Cartera | Tabla | Vencimiento: corriente, 1-30, 31-60, 61-90, >90 días |
| Aging de Cartera CxP | Cartera | Tabla | Mismo esquema para cuentas por pagar |
| Margen por Producto | Facturación detalle | Tabla | Precio vs Costo, margen absoluto y % |
| Rotación de Inventario | Inventario | Tabla | Cantidad movida / saldo promedio por producto |
| Compras por Proveedor | Facturación (tipo OP/FA compras) | Pivot | Proveedor × Mes × Total |
| Gastos por Centro de Costo | GL | Pivot | CC × Cuenta × Período |
| Flujo por Tercero | GL | Tabla | Débitos, Créditos, Saldo neto por tercero |
| Inventario Valorizado | Inventario | Tabla | Item × Bodega × Saldo × Valor |

#### F8. Exportación

| Formato | Método | Notas |
|---------|--------|-------|
| Excel (.xlsx) | Frontend genera con SheetJS | Incluye formato, totales, filtros activos |
| PDF | Backend genera con WeasyPrint | Diseño con membrete empresa, filtros aplicados |
| CSV | Frontend genera | Datos crudos sin formato |
| Imagen (PNG) | Frontend captura con html2canvas | Para compartir en chat/email |

#### F9. Compartir y Colaborar

Mismo modelo que `DashboardShare` existente. Los reportes se pueden compartir con otros usuarios de la empresa con permisos de solo lectura o edición.

#### F10. Integración con CFO Virtual (IA)

El CFO Virtual existente puede sugerir reportes basados en preguntas del usuario. Ejemplo: "¿Quién me debe más dinero?" → genera automáticamente un reporte de Aging CxC ordenado por saldo descendente.

---

## 6. MODELO DE DATOS — REPORTES BI

### 6.1 Nuevo modelo: `ReportBI`

```python
# backend/apps/dashboard/models.py

class ReportBI(BaseModel):
    """Reporte BI personalizado con constructor visual."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reportes_bi')
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE)

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    es_privado = models.BooleanField(default=True)
    es_favorito = models.BooleanField(default=False)
    es_template = models.BooleanField(default=False)  # True para predefinidos

    # Configuración de la fuente de datos
    fuentes = models.JSONField(default=list)
    # Ejemplo: ["gl", "facturacion"]

    # Campos seleccionados con configuración
    campos_config = models.JSONField(default=list)
    # Ejemplo:
    # [
    #   {"source": "gl", "field": "tercero_nombre", "role": "dimension", "label": "Tercero"},
    #   {"source": "gl", "field": "debito", "role": "metric", "aggregation": "SUM", "label": "Total Débito"},
    #   {"source": "gl", "field": "periodo", "role": "column", "label": "Período"}
    # ]

    # Configuración de visualización
    tipo_visualizacion = models.CharField(max_length=20, choices=[
        ('table', 'Tabla'),
        ('pivot', 'Tabla Dinámica'),
        ('bar', 'Barras'),
        ('line', 'Líneas'),
        ('pie', 'Torta'),
        ('area', 'Área'),
        ('kpi', 'KPI'),
        ('waterfall', 'Cascada'),
    ], default='table')

    # Configuración específica del tipo de visualización
    viz_config = models.JSONField(default=dict)
    # Para pivot: {"rows": [...], "columns": [...], "values": [...], "show_totals": true}
    # Para chart: {"x_axis": "...", "y_axis": [...], "stacked": false}
    # Para kpi: {"metric": "...", "comparison_period": "previous_month"}

    # Filtros guardados
    filtros = models.JSONField(default=dict)
    # Ejemplo:
    # {
    #   "fecha_desde": "2026-01-01",
    #   "fecha_hasta": "2026-03-31",
    #   "periodos": ["2026-01", "2026-02", "2026-03"],
    #   "tercero_ids": [],
    #   "tipo_doc": ["FA"],
    #   "cuenta_desde": null,
    #   "cuenta_hasta": null
    # }

    # Ordenamiento
    orden_config = models.JSONField(default=list)
    # Ejemplo: [{"field": "total", "direction": "desc"}]

    # Límite de registros
    limite_registros = models.IntegerField(null=True, blank=True)

    # Template base (si se creó a partir de un template)
    template_origen = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Reporte BI'
        verbose_name_plural = 'Reportes BI'
```

### 6.2 Nuevo modelo: `ReportBIShare`

```python
class ReportBIShare(BaseModel):
    """Compartir reporte BI con otro usuario."""
    reporte = models.ForeignKey(ReportBI, on_delete=models.CASCADE, related_name='shares')
    compartido_con = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    compartido_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reportes_bi_compartidos')
    puede_editar = models.BooleanField(default=False)

    class Meta:
        unique_together = ('reporte', 'compartido_con')
```

---

## 7. BACKEND — MOTOR DE CONSULTAS BI

### 7.1 QueryEngine (nuevo servicio)

```python
# backend/apps/dashboard/bi_engine.py

class BIQueryEngine:
    """Motor que traduce la configuración JSON de un ReportBI a queries Django ORM."""

    SOURCE_MODEL_MAP = {
        'gl': 'contabilidad.MovimientoContable',
        'facturacion': 'contabilidad.FacturaEncabezado',
        'facturacion_detalle': 'contabilidad.FacturaDetalle',
        'cartera': 'contabilidad.MovimientoCartera',
        'inventario': 'contabilidad.MovimientoInventario',
    }

    def execute(self, report: ReportBI) -> dict:
        """Ejecuta el reporte y retorna datos formateados."""
        # 1. Resolver fuente(s) de datos
        # 2. Aplicar filtros
        # 3. Seleccionar campos (dimensions + metrics con aggregation)
        # 4. Agrupar si hay agregaciones
        # 5. Ordenar
        # 6. Limitar
        # 7. Formatear según tipo_visualizacion
        pass

    def get_available_fields(self, source: str) -> list[dict]:
        """Retorna campos disponibles para una fuente."""
        pass

    def get_available_filters(self, source: str) -> list[dict]:
        """Retorna filtros aplicables a una fuente."""
        pass

    def build_pivot_data(self, queryset, config: dict) -> dict:
        """Construye estructura de pivot table."""
        pass

    def get_drill_down(self, report: ReportBI, cell_coords: dict) -> QuerySet:
        """Retorna registros individuales para drill-down de una celda."""
        pass
```

### 7.2 Seguridad

Todas las queries llevan `company=request.user.company` obligatorio. El motor NUNCA expone SQL crudo al frontend; solo acepta configuración JSON validada contra un schema estricto.

### 7.3 Performance

| Estrategia | Detalle |
|------------|---------|
| Índices compuestos | Ya definidos en cada modelo (company + periodo, company + tercero, etc.) |
| `select_related` / `values()` | El motor solo trae los campos solicitados, nunca `SELECT *` |
| Paginación server-side | Tablas grandes se paginan (50 rows default, configurable) |
| Cache de resultados | Redis cache por 5 min para reportes con mismo hash(filtros + campos) |
| Timeout de query | 30 segundos máximo; si excede, sugerir agregar más filtros |
| Materialización opcional | Para reportes pesados recurrentes: Celery task que pre-calcula y guarda resultado |

---

## 8. FRONTEND — PANTALLAS Y COMPONENTES

### 8.1 Estructura de componentes Angular

```
frontend/src/app/features/saidashboard/
├── components/
│   ├── ... (existentes: dashboard-list, dashboard-builder, etc.)
│   │
│   ├── report-list/                    ← NUEVO: Lista de reportes BI
│   │   ├── report-list.component.ts
│   │   ├── report-list.component.html
│   │   └── report-list.component.scss
│   │
│   ├── report-builder/                 ← NUEVO: Constructor visual
│   │   ├── report-builder.component.ts
│   │   ├── report-builder.component.html
│   │   └── report-builder.component.scss
│   │
│   ├── report-viewer/                  ← NUEVO: Visor de reporte guardado
│   │   ├── report-viewer.component.ts
│   │   ├── report-viewer.component.html
│   │   └── report-viewer.component.scss
│   │
│   ├── source-selector/                ← NUEVO: Selector de fuente de datos
│   │   ├── source-selector.component.ts
│   │   ├── source-selector.component.html
│   │   └── source-selector.component.scss
│   │
│   ├── field-panel/                    ← NUEVO: Panel lateral de campos
│   │   ├── field-panel.component.ts
│   │   ├── field-panel.component.html
│   │   └── field-panel.component.scss
│   │
│   ├── filter-builder/                 ← NUEVO: Constructor de filtros dinámico
│   │   ├── filter-builder.component.ts
│   │   ├── filter-builder.component.html
│   │   └── filter-builder.component.scss
│   │
│   ├── pivot-table/                    ← NUEVO: Tabla dinámica
│   │   ├── pivot-table.component.ts
│   │   ├── pivot-table.component.html
│   │   └── pivot-table.component.scss
│   │
│   ├── chart-renderer/                 ← NUEVO: Renderizador de gráficos
│   │   ├── chart-renderer.component.ts
│   │   ├── chart-renderer.component.html
│   │   └── chart-renderer.component.scss
│   │
│   ├── data-table/                     ← NUEVO: Tabla de datos con ordenamiento/pag
│   │   ├── data-table.component.ts
│   │   ├── data-table.component.html
│   │   └── data-table.component.scss
│   │
│   ├── drill-down-panel/              ← NUEVO: Panel lateral de drill-down
│   │   ├── drill-down-panel.component.ts
│   │   ├── drill-down-panel.component.html
│   │   └── drill-down-panel.component.scss
│   │
│   └── report-share-dialog/           ← NUEVO: Dialog para compartir reporte
│       ├── report-share-dialog.component.ts
│       ├── report-share-dialog.component.html
│       └── report-share-dialog.component.scss
│
├── models/
│   ├── ... (existentes)
│   ├── report-bi.model.ts              ← NUEVO
│   ├── bi-source.model.ts              ← NUEVO
│   └── bi-field.model.ts               ← NUEVO
│
└── services/
    ├── ... (existentes)
    └── report-bi.service.ts             ← NUEVO
```

### 8.2 Wireframes de pantallas

#### Pantalla 1: Lista de Reportes (`/saidashboard/reportes`)

```
┌──────────────────────────────────────────────────────────────────┐
│  Reportes                                            [+ Nuevo]   │
│                                                                   │
│  [Mis Reportes]  [Compartidos]  [Templates]     🔍 Buscar...    │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ ⭐ Ventas por Vendedor Q1              Pivot  │ Hoy 10:30 │  │
│  │    Facturación · 3 filtros activos              [⋮]       │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │    Balance de Comprobación Mar-2026     Tabla  │ Ayer      │  │
│  │    Contabilidad · Período: 2026-03              [⋮]       │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │    Top 20 Productos por Margen          Barras │ 8 Abr    │  │
│  │    Facturación detalle · Sin filtros            [⋮]       │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  Templates disponibles                                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ 📊       │ │ 📈       │ │ 💰       │ │ 📦       │           │
│  │ Balance  │ │ Estado   │ │ Aging    │ │ Rotación │           │
│  │ Comprob. │ │ Result.  │ │ CxC      │ │ Invent.  │           │
│  │ [Usar]   │ │ [Usar]   │ │ [Usar]   │ │ [Usar]   │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
└──────────────────────────────────────────────────────────────────┘
```

#### Pantalla 2: Constructor Visual (`/saidashboard/reportes/nuevo`)

```
┌──────────────────────────────────────────────────────────────────┐
│  ← Reportes    Nuevo Reporte                [Guardar] [Export▼] │
│                                                                   │
│  Paso 1: Seleccionar fuente                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ ✅       │ │ ○        │ │ ○        │ │ ○        │           │
│  │ Contab.  │ │ Factur.  │ │ Cartera  │ │ Invent.  │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
├──────────┬───────────────────────────────────────────────────────┤
│ CAMPOS   │  Visualización: [Tabla ▼] [Pivot] [Barras] [Líneas] │
│          │                                                       │
│ Cuenta   │  ┌─────────────────────────────────────────────────┐ │
│ □ Título │  │                                                 │ │
│ □ Grupo  │  │              Preview en tiempo real              │ │
│ ☑ Cuenta │  │                                                 │ │
│ □ Subct. │  │  ┌──────────┬──────────┬──────────┬──────────┐ │ │
│ ☑ Aux.   │  │  │ Cuenta   │ Nombre   │ Débito   │ Crédito  │ │ │
│          │  │  ├──────────┼──────────┼──────────┼──────────┤ │ │
│ Tercero  │  │  │ 1105     │ Caja     │ 500,000  │ 200,000  │ │ │
│ ☑ Nombre │  │  │ 1110     │ Bancos   │1,200,000 │ 800,000  │ │ │
│ □ ID     │  │  │ 1305     │ CxC      │ 900,000  │ 350,000  │ │ │
│          │  │  │ ...      │          │          │          │ │ │
│ Valores  │  │  └──────────┴──────────┴──────────┴──────────┘ │ │
│ ☑ Débito │  │                                                 │ │
│   SUM ▼  │  │  Mostrando 1-50 de 234 registros    < 1 2 3 > │ │
│ ☑ Crédito│  └─────────────────────────────────────────────────┘ │
│   SUM ▼  │                                                       │
│          │  FILTROS ACTIVOS                                      │
│ Temporal │  Período: 2026-01 a 2026-03  │  [+ Agregar filtro]  │
│ □ Fecha  │                                                       │
│ ☑ Período│                                                       │
│          │                                                       │
│ Dimens.  │                                                       │
│ □ Depto  │                                                       │
│ □ CC     │                                                       │
│ □ Proy.  │                                                       │
└──────────┴───────────────────────────────────────────────────────┘
```

#### Pantalla 3: Vista Pivot Table

```
┌──────────────────────────────────────────────────────────────────┐
│  ← Reportes    Ventas por Vendedor Q1      [Editar] [Export▼]   │
│                                                                   │
│  Configuración Pivot:                                            │
│  Filas: [Vendedor]   Columnas: [Período]   Valores: [SUM Total] │
│                                                                   │
│  Filtros: Tipo=FA  │  Fecha: Ene-Mar 2026  │  Estado: Posted    │
│                                                                   │
│  ┌───────────────┬────────────┬────────────┬────────────┬───────┐│
│  │ Vendedor      │  2026-01   │  2026-02   │  2026-03   │ TOTAL ││
│  ├───────────────┼────────────┼────────────┼────────────┼───────┤│
│  │ Carlos Pérez  │ 12.500.000 │ 15.800.000 │ 18.200.000 │46.5M ││
│  │ Ana García    │  9.800.000 │ 11.200.000 │ 13.500.000 │34.5M ││
│  │ Luis Moreno   │  7.200.000 │  8.100.000 │  9.800.000 │25.1M ││
│  │ María López   │  5.500.000 │  6.300.000 │  7.100.000 │18.9M ││
│  ├───────────────┼────────────┼────────────┼────────────┼───────┤│
│  │ TOTAL         │ 35.000.000 │ 41.400.000 │ 48.600.000 │ 125M ││
│  └───────────────┴────────────┴────────────┴────────────┴───────┘│
│                                                                   │
│  📊 Click en cualquier celda para ver detalle                    │
│                                                                   │
│  ┌── Drill-down: Carlos Pérez × 2026-03 ────────────────────┐   │
│  │ Factura  │ Cliente      │ Fecha    │ Total     │ Estado   │   │
│  │ FA-1234  │ Acme Corp    │ 05/03/26 │ 5.200.000 │ Posted   │   │
│  │ FA-1256  │ Beta SAS     │ 12/03/26 │ 8.100.000 │ Posted   │   │
│  │ FA-1278  │ Gamma Ltda   │ 20/03/26 │ 4.900.000 │ Posted   │   │
│  └───────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

### 8.3 Navegación en Sidebar

```
REPORTES (antes SaiDashboard)
├── Dashboards           → /saidashboard         (existente)
│   ├── Mis Dashboards
│   └── Nuevo Dashboard
├── Reportes BI          → /saidashboard/reportes (NUEVO)
│   ├── Mis Reportes
│   ├── Templates
│   └── Nuevo Reporte
├── Libro Mayor          → /saidashboard/libro-mayor (existente)
└── CFO Virtual          → chat con context=dashboard (existente)
```

---

## 9. API ENDPOINTS NUEVOS

```
# Reportes BI - CRUD
GET    /api/v1/dashboard/reportes/              → Lista reportes del usuario
POST   /api/v1/dashboard/reportes/              → Crear reporte
GET    /api/v1/dashboard/reportes/{id}/         → Detalle reporte
PUT    /api/v1/dashboard/reportes/{id}/         → Actualizar reporte
DELETE /api/v1/dashboard/reportes/{id}/         → Eliminar reporte

# Motor BI
POST   /api/v1/dashboard/reportes/preview/      → Preview (ejecutar sin guardar)
POST   /api/v1/dashboard/reportes/{id}/execute/  → Ejecutar reporte guardado
POST   /api/v1/dashboard/reportes/{id}/drill/    → Drill-down de una celda

# Metadata
GET    /api/v1/dashboard/bi/sources/             → Fuentes disponibles
GET    /api/v1/dashboard/bi/sources/{key}/fields/ → Campos de una fuente
GET    /api/v1/dashboard/bi/sources/{key}/filters/ → Filtros disponibles
GET    /api/v1/dashboard/bi/templates/           → Templates predefinidos

# Compartir
POST   /api/v1/dashboard/reportes/{id}/share/    → Compartir reporte
DELETE /api/v1/dashboard/reportes/{id}/share/{user_id}/ → Quitar acceso

# Exportar
GET    /api/v1/dashboard/reportes/{id}/export/xlsx/  → Exportar a Excel
GET    /api/v1/dashboard/reportes/{id}/export/pdf/   → Exportar a PDF
```

---

## 10. FASES DE IMPLEMENTACIÓN (para el Orquestador)

### Fase A: Modelos de datos y sync (Backend)

1. Crear modelos `FacturaEncabezado`, `FacturaDetalle`, `MovimientoCartera`, `MovimientoInventario` en `apps/contabilidad/`
2. Generar migraciones
3. Actualizar agente Go para sincronizar OE, OEDET, CARPRO, ITEMACT
4. Crear consumer SQS para las nuevas tablas
5. Tests de modelos y sync

### Fase B: Motor de consultas BI (Backend)

1. Crear `ReportBI` y `ReportBIShare` en `apps/dashboard/`
2. Implementar `BIQueryEngine` en `bi_engine.py`
3. Crear serializers para ReportBI
4. Implementar views y URLs
5. Implementar endpoints de metadata (sources, fields, filters)
6. Tests del motor: queries correctos, filtros, agregaciones, pivot
7. Tests de seguridad: company isolation, permisos

### Fase C: Constructor visual (Frontend)

1. Renombramiento visual: "SaiDashboard" → "Reportes" en sidebar y labels
2. Crear modelos TypeScript (`report-bi.model.ts`, etc.)
3. Crear `report-bi.service.ts`
4. Implementar `source-selector` component
5. Implementar `field-panel` component
6. Implementar `filter-builder` component
7. Implementar `data-table` component
8. Implementar `report-builder` (orquesta los anteriores)
9. Implementar `report-list` component
10. Actualizar rutas

### Fase D: Pivot Table y gráficos (Frontend)

1. Implementar `pivot-table` component
2. Implementar `drill-down-panel` component
3. Implementar `chart-renderer` (wrapper sobre chart.js o similar)
4. Implementar exportación (Excel, PDF, CSV)
5. Implementar `report-viewer` (modo lectura)

### Fase E: Templates y compartir

1. Crear templates predefinidos (seed data)
2. Implementar `report-share-dialog`
3. Integrar con CFO Virtual (sugerencia de reportes por IA)
4. Tests E2E

### Fase F: Revisión y validación

1. Revisión final (skill `saicloud-revision-final`)
2. Validación UI/UX (skill `saicloud-validacion-ui`)
3. Panel Admin para ReportBI
4. Documentación técnica y manual de usuario

---

## 11. TECNOLOGÍAS FRONTEND RECOMENDADAS

| Necesidad | Librería | Justificación |
|-----------|----------|---------------|
| Gráficos | **Chart.js** via ng2-charts | Ya compatible con Angular Material, ligero, soporta bar/line/pie/area/doughnut |
| Waterfall chart | Chart.js plugin o custom | Se puede implementar como bar chart con barras flotantes |
| Tablas con sort/pag | **Angular Material Table** (`mat-table`) | Estándar del proyecto (DEC-011), sort y paginator nativos |
| Pivot table | **Custom component** | No existe componente Material para pivot; construir sobre mat-table con lógica de agrupación |
| Drag & drop campos | **Angular CDK DragDrop** | Parte del CDK, ya disponible |
| Tree select (PUC) | **mat-tree** + checkbox | Selector jerárquico de cuentas contables |
| Date range | **mat-date-range-input** | Nativo de Material |
| Export Excel | **SheetJS (xlsx)** | Ya usado en el proyecto, genera .xlsx client-side |
| Export PDF | **Backend (WeasyPrint)** | Genera PDF server-side con template |

---

## 12. CONSIDERACIONES DE SEGURIDAD

- Todas las queries SIEMPRE filtran por `company_id` del usuario autenticado
- El motor BI NO permite SQL crudo; solo acepta configuración JSON validada
- Los campos disponibles se definen en el backend (whitelist), no en el frontend
- Rate limiting: máximo 10 ejecuciones de reporte por minuto por usuario
- Timeout de query: 30 segundos; si excede, respuesta 408 con sugerencia de filtros
- Los reportes compartidos respetan los permisos de módulo (`moduleAccessGuard` + `LicensePermission`)

---

## 13. MÉTRICAS DE ÉXITO

| Métrica | Objetivo |
|---------|----------|
| Tiempo de carga de reporte promedio | < 3 segundos para datasets < 50k registros |
| Reportes creados por usuario/mes | > 5 (indica adopción) |
| Templates usados vs custom | 60/40 inicialmente, tendiendo a más custom |
| Exportaciones/mes | > 20 por empresa activa |

---

## 14. DECISIONES PENDIENTES

| # | Decisión | Opciones | Quién decide |
|---|----------|----------|--------------|
| 1 | Librería de gráficos definitiva | Chart.js vs ECharts vs Plotly | Juan David |
| 2 | Sync de OE/OEDET: ¿incremental por NUMBER o full periódico? | Watermark vs Full diario | Arquitecto |
| 3 | ¿Materializar reportes pesados con Celery? | Sí (cache en BD) vs No (siempre live) | Post-MVP |
| 4 | ¿Permitir cross-source joins en v1? | Sí vs Solo v2 | Juan David |

---

*Este PRD es la entrada para el Orquestador. Ejecutar con: `FEATURE type=FEATURE, trigger="Constructor de Reportes BI para módulo Reportes"`*

*Última actualización: 10 Abril 2026*
