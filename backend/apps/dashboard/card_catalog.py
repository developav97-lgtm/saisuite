"""
SaiSuite -- Dashboard: Card Catalog
Catalogo estatico de tipos de tarjetas disponibles.
Python dict, NO base de datos.

Cada tarjeta define:
- nombre: Nombre visible
- categoria: Agrupacion funcional
- descripcion: Descripcion para el usuario
- chart_types: Tipos de grafico soportados
- chart_default: Tipo de grafico por defecto
- color: Color identificador (hex)
- icono: Nombre del Material Icon
- requiere: Lista de features que la empresa debe tener habilitadas
"""

# ──────────────────────────────────────────────
# Categorias
# ──────────────────────────────────────────────

CATEGORIAS_CATALOG = {
    'estados_financieros': {
        'nombre': 'Estados Financieros',
        'descripcion': 'Balance general, estado de resultados e indicadores financieros',
        'icono': 'account_balance',
        'orden': 1,
    },
    'costos_gastos': {
        'nombre': 'Costos y Gastos',
        'descripcion': 'Analisis de costos de venta, gastos operacionales y margenes',
        'icono': 'payments',
        'orden': 2,
    },
    'cartera': {
        'nombre': 'Cartera',
        'descripcion': 'Cuentas por cobrar, aging y analisis por tercero',
        'icono': 'receipt_long',
        'orden': 3,
    },
    'proveedores': {
        'nombre': 'Proveedores',
        'descripcion': 'Cuentas por pagar y analisis de proveedores',
        'icono': 'local_shipping',
        'orden': 4,
    },
    'proyectos': {
        'nombre': 'Proyectos',
        'descripcion': 'Costos por proyecto y actividad',
        'icono': 'engineering',
        'orden': 5,
    },
    'comparativos': {
        'nombre': 'Comparativos',
        'descripcion': 'Comparaciones entre periodos y tendencias',
        'icono': 'compare_arrows',
        'orden': 6,
    },
}


# ──────────────────────────────────────────────
# Catalogo de tarjetas
# ──────────────────────────────────────────────

CARD_CATALOG = {
    # ── Estados Financieros ──
    'BALANCE_GENERAL': {
        'nombre': 'Balance General',
        'categoria': 'estados_financieros',
        'descripcion': 'Activos, pasivos y patrimonio de la empresa',
        'chart_types': ['bar', 'table', 'waterfall'],
        'chart_default': 'bar',
        'color': '#1976D2',
        'icono': 'account_balance',
        'requiere': [],
    },
    'ESTADO_RESULTADOS': {
        'nombre': 'Estado de Resultados',
        'categoria': 'estados_financieros',
        'descripcion': 'Ingresos menos costos y gastos igual utilidad',
        'chart_types': ['waterfall', 'bar', 'table'],
        'chart_default': 'waterfall',
        'color': '#388E3C',
        'icono': 'trending_up',
        'requiere': [],
    },
    'INDICADORES_LIQUIDEZ': {
        'nombre': 'Indicadores de Liquidez',
        'categoria': 'estados_financieros',
        'descripcion': 'Razon corriente, prueba acida y capital de trabajo',
        'chart_types': ['kpi', 'gauge', 'table'],
        'chart_default': 'kpi',
        'color': '#0288D1',
        'icono': 'water_drop',
        'requiere': [],
    },
    'EBITDA': {
        'nombre': 'EBITDA',
        'categoria': 'estados_financieros',
        'descripcion': 'Utilidad antes de intereses, impuestos, depreciacion y amortizacion',
        'chart_types': ['kpi', 'line', 'bar'],
        'chart_default': 'kpi',
        'color': '#7B1FA2',
        'icono': 'show_chart',
        'requiere': [],
    },
    'INGRESOS_VS_EGRESOS': {
        'nombre': 'Ingresos vs Egresos',
        'categoria': 'estados_financieros',
        'descripcion': 'Comparacion visual de ingresos contra egresos',
        'chart_types': ['bar', 'line', 'area'],
        'chart_default': 'bar',
        'color': '#F57C00',
        'icono': 'compare_arrows',
        'requiere': [],
    },
    'ROE_ROA': {
        'nombre': 'ROE / ROA',
        'categoria': 'estados_financieros',
        'descripcion': 'Retorno sobre patrimonio y sobre activos',
        'chart_types': ['kpi', 'gauge', 'bar'],
        'chart_default': 'kpi',
        'color': '#C62828',
        'icono': 'speed',
        'requiere': [],
    },
    'ENDEUDAMIENTO': {
        'nombre': 'Endeudamiento',
        'categoria': 'estados_financieros',
        'descripcion': 'Nivel de endeudamiento y concentracion de deuda',
        'chart_types': ['kpi', 'gauge', 'pie'],
        'chart_default': 'gauge',
        'color': '#AD1457',
        'icono': 'account_balance_wallet',
        'requiere': [],
    },

    # ── Costos y Gastos ──
    'COSTO_VENTAS': {
        'nombre': 'Costo de Ventas',
        'categoria': 'costos_gastos',
        'descripcion': 'Total de costos de ventas del periodo',
        'chart_types': ['kpi', 'line', 'bar'],
        'chart_default': 'kpi',
        'color': '#E64A19',
        'icono': 'shopping_cart',
        'requiere': [],
    },
    'MARGEN_BRUTO_NETO': {
        'nombre': 'Margen Bruto y Neto',
        'categoria': 'costos_gastos',
        'descripcion': 'Margenes de rentabilidad bruta y neta',
        'chart_types': ['kpi', 'bar', 'line'],
        'chart_default': 'kpi',
        'color': '#2E7D32',
        'icono': 'percent',
        'requiere': [],
    },
    'GASTOS_OPERACIONALES': {
        'nombre': 'Gastos Operacionales',
        'categoria': 'costos_gastos',
        'descripcion': 'Desglose de gastos operacionales por grupo contable',
        'chart_types': ['pie', 'bar', 'table'],
        'chart_default': 'pie',
        'color': '#FF6F00',
        'icono': 'pie_chart',
        'requiere': [],
    },
    'GASTOS_POR_DEPARTAMENTO': {
        'nombre': 'Gastos por Departamento',
        'categoria': 'costos_gastos',
        'descripcion': 'Distribucion de gastos por departamento',
        'chart_types': ['bar', 'pie', 'table'],
        'chart_default': 'bar',
        'color': '#5D4037',
        'icono': 'corporate_fare',
        'requiere': ['usa_departamentos_cc'],
    },
    'GASTOS_POR_CENTRO_COSTO': {
        'nombre': 'Gastos por Centro de Costo',
        'categoria': 'costos_gastos',
        'descripcion': 'Distribucion de gastos por centro de costo',
        'chart_types': ['bar', 'pie', 'table'],
        'chart_default': 'bar',
        'color': '#4E342E',
        'icono': 'hub',
        'requiere': ['usa_departamentos_cc'],
    },

    # ── Cartera ──
    'CARTERA_TOTAL': {
        'nombre': 'Cartera Total',
        'categoria': 'cartera',
        'descripcion': 'Total de cuentas por cobrar pendientes',
        'chart_types': ['kpi', 'gauge', 'bar'],
        'chart_default': 'kpi',
        'color': '#1565C0',
        'icono': 'account_balance',
        'requiere': [],
    },
    'AGING_CARTERA': {
        'nombre': 'Aging de Cartera',
        'categoria': 'cartera',
        'descripcion': 'Antiguedad de cartera por rangos de dias vencidos',
        'chart_types': ['bar', 'table', 'pie'],
        'chart_default': 'bar',
        'color': '#0D47A1',
        'icono': 'hourglass_top',
        'requiere': [],
    },
    'TOP_CLIENTES_SALDO': {
        'nombre': 'Top Clientes por Saldo',
        'categoria': 'cartera',
        'descripcion': 'Clientes con mayor saldo pendiente',
        'chart_types': ['bar', 'table', 'pie'],
        'chart_default': 'bar',
        'color': '#1976D2',
        'icono': 'people',
        'requiere': [],
    },
    'MOVIMIENTO_POR_TERCERO': {
        'nombre': 'Movimiento por Tercero',
        'categoria': 'cartera',
        'descripcion': 'Debitos y creditos agrupados por tercero',
        'chart_types': ['table', 'bar'],
        'chart_default': 'table',
        'color': '#1E88E5',
        'icono': 'person_search',
        'requiere': [],
    },

    # ── Proveedores ──
    'CUENTAS_POR_PAGAR': {
        'nombre': 'Cuentas por Pagar',
        'categoria': 'proveedores',
        'descripcion': 'Total de obligaciones con proveedores',
        'chart_types': ['kpi', 'gauge', 'bar'],
        'chart_default': 'kpi',
        'color': '#D32F2F',
        'icono': 'payment',
        'requiere': [],
    },
    'AGING_PROVEEDORES': {
        'nombre': 'Aging de Proveedores',
        'categoria': 'proveedores',
        'descripcion': 'Antiguedad de cuentas por pagar por rangos de dias',
        'chart_types': ['bar', 'table', 'pie'],
        'chart_default': 'bar',
        'color': '#C62828',
        'icono': 'hourglass_bottom',
        'requiere': [],
    },
    'TOP_PROVEEDORES': {
        'nombre': 'Top Proveedores por Saldo',
        'categoria': 'proveedores',
        'descripcion': 'Proveedores con mayor saldo por pagar',
        'chart_types': ['bar', 'table', 'pie'],
        'chart_default': 'bar',
        'color': '#B71C1C',
        'icono': 'local_shipping',
        'requiere': [],
    },

    # ── Proyectos ──
    'COSTO_POR_PROYECTO': {
        'nombre': 'Costo por Proyecto',
        'categoria': 'proyectos',
        'descripcion': 'Costos y gastos agrupados por proyecto contable',
        'chart_types': ['bar', 'pie', 'table'],
        'chart_default': 'bar',
        'color': '#00695C',
        'icono': 'engineering',
        'requiere': ['usa_proyectos_actividades'],
    },
    'COSTO_POR_ACTIVIDAD': {
        'nombre': 'Costo por Actividad',
        'categoria': 'proyectos',
        'descripcion': 'Costos y gastos agrupados por actividad contable',
        'chart_types': ['bar', 'pie', 'table'],
        'chart_default': 'bar',
        'color': '#004D40',
        'icono': 'task',
        'requiere': ['usa_proyectos_actividades'],
    },

    # ── Comparativos ──
    'COMPARATIVO_PERIODOS': {
        'nombre': 'Comparativo de Periodos',
        'categoria': 'comparativos',
        'descripcion': 'Comparacion de ingresos, costos y gastos entre dos periodos',
        'chart_types': ['bar', 'table', 'line'],
        'chart_default': 'bar',
        'color': '#455A64',
        'icono': 'compare',
        'requiere': [],
    },
    'TENDENCIA_MENSUAL': {
        'nombre': 'Tendencia Mensual',
        'categoria': 'comparativos',
        'descripcion': 'Evolucion mensual de ingresos, costos y utilidad',
        'chart_types': ['line', 'area', 'bar'],
        'chart_default': 'line',
        'color': '#37474F',
        'icono': 'timeline',
        'requiere': [],
    },
}


def get_available_cards(config=None) -> dict:
    """
    Retorna solo las tarjetas disponibles para la empresa segun su configuracion contable.

    Args:
        config: ConfiguracionContable o None (retorna todas sin restriccion de requiere)

    Returns:
        dict filtrado del CARD_CATALOG
    """
    if config is None:
        return CARD_CATALOG

    available = {}
    for code, card in CARD_CATALOG.items():
        reqs = card.get('requiere', [])
        if not reqs:
            available[code] = card
            continue

        # Check all requirements
        meets_all = True
        for req in reqs:
            if not getattr(config, req, False):
                meets_all = False
                break

        if meets_all:
            available[code] = card

    return available


def get_categories_with_cards(config=None) -> list[dict]:
    """
    Retorna las categorias con sus tarjetas disponibles.

    Returns:
        list of {code, nombre, descripcion, icono, orden, cards: [...]}
    """
    available = get_available_cards(config)
    categories = {}

    for code, card in available.items():
        cat_key = card['categoria']
        if cat_key not in categories:
            cat_def = CATEGORIAS_CATALOG.get(cat_key, {})
            categories[cat_key] = {
                'code': cat_key,
                'nombre': cat_def.get('nombre', cat_key),
                'descripcion': cat_def.get('descripcion', ''),
                'icono': cat_def.get('icono', 'dashboard'),
                'orden': cat_def.get('orden', 99),
                'cards': [],
            }

        categories[cat_key]['cards'].append({
            'code': code,
            **card,
        })

    result = sorted(categories.values(), key=lambda c: c['orden'])
    return result
