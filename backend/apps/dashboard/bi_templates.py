"""
SaiSuite -- Dashboard: BI Report Templates
12 predefined report templates matching PRD section F7.
Each template is a dict matching ReportBI field structure.
"""

REPORT_TEMPLATES = [
    # ──────────────────────────────────────────────
    # 1. Balance de Comprobación
    # ──────────────────────────────────────────────
    {
        'titulo': 'Balance de Comprobación',
        'descripcion': 'Saldos por cuenta contable en un período. Muestra débitos, créditos y saldo neto por auxiliar.',
        'fuentes': ['gl'],
        'campos_config': [
            {'source': 'gl', 'field': 'auxiliar', 'role': 'dimension', 'label': 'Código auxiliar'},
            {'source': 'gl', 'field': 'auxiliar_nombre', 'role': 'dimension', 'label': 'Nombre auxiliar'},
            {'source': 'gl', 'field': 'debito', 'role': 'metric', 'aggregation': 'SUM', 'label': 'Débito'},
            {'source': 'gl', 'field': 'credito', 'role': 'metric', 'aggregation': 'SUM', 'label': 'Crédito'},
        ],
        'tipo_visualizacion': 'table',
        'viz_config': {},
        'filtros': {},
        'orden_config': [{'field': 'auxiliar', 'direction': 'asc'}],
        'limite_registros': None,
    },
    # ──────────────────────────────────────────────
    # 2. Estado de Resultados
    # ──────────────────────────────────────────────
    {
        'titulo': 'Estado de Resultados',
        'descripcion': 'Ingresos - Costos - Gastos = Utilidad. Vista cascada por título contable.',
        'fuentes': ['gl'],
        'campos_config': [
            {'source': 'gl', 'field': 'titulo_codigo', 'role': 'dimension', 'label': 'Título código'},
            {'source': 'gl', 'field': 'titulo_nombre', 'role': 'dimension', 'label': 'Título nombre'},
            {'source': 'gl', 'field': 'debito', 'role': 'metric', 'aggregation': 'SUM', 'label': 'Débito'},
            {'source': 'gl', 'field': 'credito', 'role': 'metric', 'aggregation': 'SUM', 'label': 'Crédito'},
        ],
        'tipo_visualizacion': 'waterfall',
        'viz_config': {},
        'filtros': {},
        'orden_config': [{'field': 'titulo_codigo', 'direction': 'asc'}],
        'limite_registros': None,
    },
    # ──────────────────────────────────────────────
    # 3. Ventas por Vendedor
    # ──────────────────────────────────────────────
    {
        'titulo': 'Ventas por Vendedor',
        'descripcion': 'Tabla dinámica: Vendedor × Mes × Total ventas.',
        'fuentes': ['facturacion'],
        'campos_config': [
            {'source': 'facturacion', 'field': 'salesman_nombre', 'role': 'dimension', 'label': 'Vendedor'},
            {'source': 'facturacion', 'field': 'periodo', 'role': 'dimension', 'label': 'Período'},
            {'source': 'facturacion', 'field': 'total', 'role': 'metric', 'aggregation': 'SUM', 'label': 'Total'},
        ],
        'tipo_visualizacion': 'pivot',
        'viz_config': {
            'row_fields': ['salesman_nombre'],
            'col_fields': ['periodo'],
            'value_fields': [{'field': 'total', 'aggregation': 'SUM'}],
        },
        'filtros': {},
        'orden_config': [],
        'limite_registros': None,
    },
    # ──────────────────────────────────────────────
    # 4. Ventas por Producto (Top 20)
    # ──────────────────────────────────────────────
    {
        'titulo': 'Ventas por Producto (Top 20)',
        'descripcion': 'Productos más vendidos por cantidad o valor. Gráfico de barras.',
        'fuentes': ['facturacion_detalle'],
        'campos_config': [
            {'source': 'facturacion_detalle', 'field': 'item_descripcion', 'role': 'dimension', 'label': 'Producto'},
            {'source': 'facturacion_detalle', 'field': 'precio_extendido', 'role': 'metric', 'aggregation': 'SUM', 'label': 'Venta total'},
            {'source': 'facturacion_detalle', 'field': 'qty_ship', 'role': 'metric', 'aggregation': 'SUM', 'label': 'Cantidad'},
        ],
        'tipo_visualizacion': 'bar',
        'viz_config': {},
        'filtros': {},
        'orden_config': [{'field': 'precio_extendido', 'direction': 'desc'}],
        'limite_registros': 20,
    },
    # ──────────────────────────────────────────────
    # 5. Aging de Cartera CxC
    # ──────────────────────────────────────────────
    {
        'titulo': 'Aging de Cartera CxC',
        'descripcion': 'Vencimiento cuentas por cobrar: corriente, 1-30, 31-60, 61-90, >90 días.',
        'fuentes': ['cartera'],
        'campos_config': [
            {'source': 'cartera', 'field': 'tercero_nombre', 'role': 'dimension', 'label': 'Tercero'},
            {'source': 'cartera', 'field': 'tipo_cartera', 'role': 'dimension', 'label': 'Tipo cartera'},
            {'source': 'cartera', 'field': 'duedate', 'role': 'dimension', 'label': 'Vencimiento'},
            {'source': 'cartera', 'field': 'saldo', 'role': 'metric', 'aggregation': 'SUM', 'label': 'Saldo'},
        ],
        'tipo_visualizacion': 'table',
        'viz_config': {},
        'filtros': {'tipo_cartera': 'CXC'},
        'orden_config': [{'field': 'saldo', 'direction': 'desc'}],
        'limite_registros': None,
    },
    # ──────────────────────────────────────────────
    # 6. Aging de Cartera CxP
    # ──────────────────────────────────────────────
    {
        'titulo': 'Aging de Cartera CxP',
        'descripcion': 'Vencimiento cuentas por pagar: corriente, 1-30, 31-60, 61-90, >90 días.',
        'fuentes': ['cartera'],
        'campos_config': [
            {'source': 'cartera', 'field': 'tercero_nombre', 'role': 'dimension', 'label': 'Tercero'},
            {'source': 'cartera', 'field': 'tipo_cartera', 'role': 'dimension', 'label': 'Tipo cartera'},
            {'source': 'cartera', 'field': 'duedate', 'role': 'dimension', 'label': 'Vencimiento'},
            {'source': 'cartera', 'field': 'saldo', 'role': 'metric', 'aggregation': 'SUM', 'label': 'Saldo'},
        ],
        'tipo_visualizacion': 'table',
        'viz_config': {},
        'filtros': {'tipo_cartera': 'CXP'},
        'orden_config': [{'field': 'saldo', 'direction': 'desc'}],
        'limite_registros': None,
    },
    # ──────────────────────────────────────────────
    # 7. Margen por Producto
    # ──────────────────────────────────────────────
    {
        'titulo': 'Margen por Producto',
        'descripcion': 'Precio vs Costo por producto. Margen absoluto y porcentaje.',
        'fuentes': ['facturacion_detalle'],
        'campos_config': [
            {'source': 'facturacion_detalle', 'field': 'item_codigo', 'role': 'dimension', 'label': 'Código'},
            {'source': 'facturacion_detalle', 'field': 'item_descripcion', 'role': 'dimension', 'label': 'Producto'},
            {'source': 'facturacion_detalle', 'field': 'precio_extendido', 'role': 'metric', 'aggregation': 'SUM', 'label': 'Venta'},
            {'source': 'facturacion_detalle', 'field': 'costo_unitario', 'role': 'metric', 'aggregation': 'SUM', 'label': 'Costo'},
            {'source': 'facturacion_detalle', 'field': 'margen_valor', 'role': 'metric', 'aggregation': 'SUM', 'label': 'Margen $'},
            {'source': 'facturacion_detalle', 'field': 'margen_porcentaje', 'role': 'metric', 'aggregation': 'AVG', 'label': 'Margen %'},
        ],
        'tipo_visualizacion': 'table',
        'viz_config': {},
        'filtros': {},
        'orden_config': [{'field': 'margen_valor', 'direction': 'desc'}],
        'limite_registros': None,
    },
    # ──────────────────────────────────────────────
    # 8. Rotación de Inventario
    # ──────────────────────────────────────────────
    {
        'titulo': 'Rotación de Inventario',
        'descripcion': 'Cantidad movida y saldo por producto. Identifica productos con baja rotación.',
        'fuentes': ['inventario'],
        'campos_config': [
            {'source': 'inventario', 'field': 'item_codigo', 'role': 'dimension', 'label': 'Código'},
            {'source': 'inventario', 'field': 'item_descripcion', 'role': 'dimension', 'label': 'Producto'},
            {'source': 'inventario', 'field': 'location', 'role': 'dimension', 'label': 'Bodega'},
            {'source': 'inventario', 'field': 'cantidad', 'role': 'metric', 'aggregation': 'SUM', 'label': 'Movimiento'},
            {'source': 'inventario', 'field': 'saldo_unidades', 'role': 'metric', 'aggregation': 'SUM', 'label': 'Saldo Uds'},
        ],
        'tipo_visualizacion': 'table',
        'viz_config': {},
        'filtros': {},
        'orden_config': [{'field': 'cantidad', 'direction': 'desc'}],
        'limite_registros': None,
    },
    # ──────────────────────────────────────────────
    # 9. Compras por Proveedor
    # ──────────────────────────────────────────────
    {
        'titulo': 'Compras por Proveedor',
        'descripcion': 'Tabla dinámica: Proveedor × Mes × Total compras.',
        'fuentes': ['facturacion'],
        'campos_config': [
            {'source': 'facturacion', 'field': 'tercero_nombre', 'role': 'dimension', 'label': 'Proveedor'},
            {'source': 'facturacion', 'field': 'periodo', 'role': 'dimension', 'label': 'Período'},
            {'source': 'facturacion', 'field': 'total', 'role': 'metric', 'aggregation': 'SUM', 'label': 'Total'},
        ],
        'tipo_visualizacion': 'pivot',
        'viz_config': {
            'row_fields': ['tercero_nombre'],
            'col_fields': ['periodo'],
            'value_fields': [{'field': 'total', 'aggregation': 'SUM'}],
        },
        'filtros': {'tipo_doc': ['OP', 'FA']},
        'orden_config': [],
        'limite_registros': None,
    },
    # ──────────────────────────────────────────────
    # 10. Gastos por Centro de Costo
    # ──────────────────────────────────────────────
    {
        'titulo': 'Gastos por Centro de Costo',
        'descripcion': 'Tabla dinámica: Centro de costo × Cuenta × Período.',
        'fuentes': ['gl'],
        'campos_config': [
            {'source': 'gl', 'field': 'centro_costo_nombre', 'role': 'dimension', 'label': 'Centro de costo'},
            {'source': 'gl', 'field': 'cuenta_nombre', 'role': 'dimension', 'label': 'Cuenta'},
            {'source': 'gl', 'field': 'periodo', 'role': 'dimension', 'label': 'Período'},
            {'source': 'gl', 'field': 'debito', 'role': 'metric', 'aggregation': 'SUM', 'label': 'Débito'},
            {'source': 'gl', 'field': 'credito', 'role': 'metric', 'aggregation': 'SUM', 'label': 'Crédito'},
        ],
        'tipo_visualizacion': 'pivot',
        'viz_config': {
            'row_fields': ['centro_costo_nombre'],
            'col_fields': ['periodo'],
            'value_fields': [{'field': 'debito', 'aggregation': 'SUM'}],
        },
        'filtros': {'cuenta_desde': 5, 'cuenta_hasta': 5999},
        'orden_config': [],
        'limite_registros': None,
    },
    # ──────────────────────────────────────────────
    # 11. Flujo por Tercero
    # ──────────────────────────────────────────────
    {
        'titulo': 'Flujo por Tercero',
        'descripcion': 'Débitos, créditos y saldo neto por tercero. Identifica principales contrapartes.',
        'fuentes': ['gl'],
        'campos_config': [
            {'source': 'gl', 'field': 'tercero_id', 'role': 'dimension', 'label': 'ID Tercero'},
            {'source': 'gl', 'field': 'tercero_nombre', 'role': 'dimension', 'label': 'Nombre tercero'},
            {'source': 'gl', 'field': 'debito', 'role': 'metric', 'aggregation': 'SUM', 'label': 'Débito'},
            {'source': 'gl', 'field': 'credito', 'role': 'metric', 'aggregation': 'SUM', 'label': 'Crédito'},
        ],
        'tipo_visualizacion': 'table',
        'viz_config': {},
        'filtros': {},
        'orden_config': [{'field': 'debito', 'direction': 'desc'}],
        'limite_registros': None,
    },
    # ──────────────────────────────────────────────
    # 12. Inventario Valorizado
    # ──────────────────────────────────────────────
    {
        'titulo': 'Inventario Valorizado',
        'descripcion': 'Saldo y valor por producto y bodega. Valorización del inventario actual.',
        'fuentes': ['inventario'],
        'campos_config': [
            {'source': 'inventario', 'field': 'item_codigo', 'role': 'dimension', 'label': 'Código'},
            {'source': 'inventario', 'field': 'item_descripcion', 'role': 'dimension', 'label': 'Producto'},
            {'source': 'inventario', 'field': 'location', 'role': 'dimension', 'label': 'Bodega'},
            {'source': 'inventario', 'field': 'saldo_unidades', 'role': 'metric', 'aggregation': 'SUM', 'label': 'Saldo Uds'},
            {'source': 'inventario', 'field': 'saldo_pesos', 'role': 'metric', 'aggregation': 'SUM', 'label': 'Saldo $'},
        ],
        'tipo_visualizacion': 'table',
        'viz_config': {},
        'filtros': {},
        'orden_config': [{'field': 'saldo_pesos', 'direction': 'desc'}],
        'limite_registros': None,
    },
]
