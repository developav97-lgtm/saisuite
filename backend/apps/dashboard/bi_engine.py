"""
SaiSuite -- Dashboard: BI Query Engine
Motor que traduce la configuración JSON de un ReportBI a queries Django ORM.
Seguridad: company_id obligatorio en todas las queries. Sin SQL crudo.
"""
import logging
from collections import OrderedDict
from decimal import Decimal

from django.apps import apps
from django.db.models import (
    Sum, Avg, Count, Min, Max,
    QuerySet, F, Value, CharField,
)
from django.db.models.functions import Coalesce

logger = logging.getLogger(__name__)

_AGGREGATION_MAP = {
    'SUM': Sum,
    'AVG': Avg,
    'COUNT': Count,
    'MIN': Min,
    'MAX': Max,
}

# Fuente -> modelo Django
SOURCE_MODEL_MAP = {
    'gl': 'contabilidad.MovimientoContable',
    'facturacion': 'contabilidad.FacturaEncabezado',
    'facturacion_detalle': 'contabilidad.FacturaDetalle',
    'cartera': 'contabilidad.MovimientoCartera',
    'inventario': 'contabilidad.MovimientoInventario',
}

# Definición de campos disponibles por fuente, organizados por categoría
SOURCE_FIELDS = {
    'gl': {
        'Cuenta contable': [
            {'field': 'auxiliar', 'label': 'Código auxiliar', 'type': 'decimal', 'role': 'dimension'},
            {'field': 'auxiliar_nombre', 'label': 'Nombre auxiliar', 'type': 'text', 'role': 'dimension'},
            {'field': 'titulo_codigo', 'label': 'Título código', 'type': 'integer', 'role': 'dimension'},
            {'field': 'titulo_nombre', 'label': 'Título nombre', 'type': 'text', 'role': 'dimension'},
            {'field': 'grupo_codigo', 'label': 'Grupo código', 'type': 'integer', 'role': 'dimension'},
            {'field': 'grupo_nombre', 'label': 'Grupo nombre', 'type': 'text', 'role': 'dimension'},
            {'field': 'cuenta_codigo', 'label': 'Cuenta código', 'type': 'integer', 'role': 'dimension'},
            {'field': 'cuenta_nombre', 'label': 'Cuenta nombre', 'type': 'text', 'role': 'dimension'},
            {'field': 'subcuenta_codigo', 'label': 'Subcuenta código', 'type': 'integer', 'role': 'dimension'},
            {'field': 'subcuenta_nombre', 'label': 'Subcuenta nombre', 'type': 'text', 'role': 'dimension'},
        ],
        'Tercero': [
            {'field': 'tercero_id', 'label': 'ID Tercero', 'type': 'text', 'role': 'dimension'},
            {'field': 'tercero_nombre', 'label': 'Nombre tercero', 'type': 'text', 'role': 'dimension'},
        ],
        'Valores': [
            {'field': 'debito', 'label': 'Débito', 'type': 'decimal', 'role': 'metric'},
            {'field': 'credito', 'label': 'Crédito', 'type': 'decimal', 'role': 'metric'},
        ],
        'Temporal': [
            {'field': 'fecha', 'label': 'Fecha', 'type': 'date', 'role': 'dimension'},
            {'field': 'periodo', 'label': 'Período', 'type': 'text', 'role': 'dimension'},
        ],
        'Dimensiones': [
            {'field': 'departamento_codigo', 'label': 'Departamento código', 'type': 'integer', 'role': 'dimension'},
            {'field': 'departamento_nombre', 'label': 'Departamento nombre', 'type': 'text', 'role': 'dimension'},
            {'field': 'centro_costo_codigo', 'label': 'Centro costo código', 'type': 'integer', 'role': 'dimension'},
            {'field': 'centro_costo_nombre', 'label': 'Centro costo nombre', 'type': 'text', 'role': 'dimension'},
            {'field': 'proyecto_codigo', 'label': 'Proyecto', 'type': 'text', 'role': 'dimension'},
            {'field': 'actividad_codigo', 'label': 'Actividad', 'type': 'text', 'role': 'dimension'},
        ],
        'Documento': [
            {'field': 'tipo', 'label': 'Tipo documento', 'type': 'text', 'role': 'dimension'},
            {'field': 'batch', 'label': 'Batch', 'type': 'integer', 'role': 'dimension'},
            {'field': 'invc', 'label': 'Nro factura', 'type': 'text', 'role': 'dimension'},
            {'field': 'descripcion', 'label': 'Descripción', 'type': 'text', 'role': 'dimension'},
        ],
    },
    'facturacion': {
        'Documento': [
            {'field': 'number', 'label': 'Número', 'type': 'integer', 'role': 'dimension'},
            {'field': 'tipo', 'label': 'Tipo', 'type': 'text', 'role': 'dimension'},
            {'field': 'id_sucursal', 'label': 'Sucursal', 'type': 'integer', 'role': 'dimension'},
            {'field': 'posted', 'label': 'Contabilizado', 'type': 'boolean', 'role': 'dimension'},
            {'field': 'closed', 'label': 'Cerrado', 'type': 'boolean', 'role': 'dimension'},
            {'field': 'comentarios', 'label': 'Comentarios', 'type': 'text', 'role': 'dimension'},
        ],
        'Tercero': [
            {'field': 'tercero_id', 'label': 'ID Tercero', 'type': 'text', 'role': 'dimension'},
            {'field': 'tercero_nombre', 'label': 'Nombre tercero', 'type': 'text', 'role': 'dimension'},
        ],
        'Vendedor': [
            {'field': 'salesman', 'label': 'Código vendedor', 'type': 'integer', 'role': 'dimension'},
            {'field': 'salesman_nombre', 'label': 'Nombre vendedor', 'type': 'text', 'role': 'dimension'},
        ],
        'Temporal': [
            {'field': 'fecha', 'label': 'Fecha', 'type': 'date', 'role': 'dimension'},
            {'field': 'duedate', 'label': 'Vencimiento', 'type': 'date', 'role': 'dimension'},
            {'field': 'periodo', 'label': 'Período', 'type': 'text', 'role': 'dimension'},
        ],
        'Montos': [
            {'field': 'subtotal', 'label': 'Subtotal', 'type': 'decimal', 'role': 'metric'},
            {'field': 'costo', 'label': 'Costo', 'type': 'decimal', 'role': 'metric'},
            {'field': 'iva', 'label': 'IVA', 'type': 'decimal', 'role': 'metric'},
            {'field': 'descuento_global', 'label': 'Descuento global', 'type': 'decimal', 'role': 'metric'},
            {'field': 'total', 'label': 'Total', 'type': 'decimal', 'role': 'metric'},
        ],
    },
    'facturacion_detalle': {
        'Producto': [
            {'field': 'item_codigo', 'label': 'Código producto', 'type': 'text', 'role': 'dimension'},
            {'field': 'item_descripcion', 'label': 'Descripción producto', 'type': 'text', 'role': 'dimension'},
            {'field': 'location', 'label': 'Bodega', 'type': 'text', 'role': 'dimension'},
        ],
        'Cantidades': [
            {'field': 'qty_order', 'label': 'Cantidad ordenada', 'type': 'decimal', 'role': 'metric'},
            {'field': 'qty_ship', 'label': 'Cantidad despachada', 'type': 'decimal', 'role': 'metric'},
        ],
        'Precios': [
            {'field': 'precio_unitario', 'label': 'Precio unitario', 'type': 'decimal', 'role': 'metric'},
            {'field': 'precio_extendido', 'label': 'Precio extendido', 'type': 'decimal', 'role': 'metric'},
            {'field': 'costo_unitario', 'label': 'Costo unitario', 'type': 'decimal', 'role': 'metric'},
        ],
        'Impuestos': [
            {'field': 'valor_iva', 'label': 'Valor IVA', 'type': 'decimal', 'role': 'metric'},
            {'field': 'porc_iva', 'label': '% IVA', 'type': 'decimal', 'role': 'metric'},
            {'field': 'descuento', 'label': 'Descuento', 'type': 'decimal', 'role': 'metric'},
        ],
        'Márgenes': [
            {'field': 'margen_valor', 'label': 'Margen valor', 'type': 'decimal', 'role': 'metric'},
            {'field': 'margen_porcentaje', 'label': 'Margen %', 'type': 'decimal', 'role': 'metric'},
        ],
        'Proyecto': [
            {'field': 'proyecto_codigo', 'label': 'Proyecto', 'type': 'text', 'role': 'dimension'},
        ],
    },
    'cartera': {
        'Tercero': [
            {'field': 'tercero_id', 'label': 'ID Tercero', 'type': 'text', 'role': 'dimension'},
            {'field': 'tercero_nombre', 'label': 'Nombre tercero', 'type': 'text', 'role': 'dimension'},
        ],
        'Clasificación': [
            {'field': 'tipo_cartera', 'label': 'Tipo cartera', 'type': 'text', 'role': 'dimension'},
            {'field': 'cuenta_contable', 'label': 'Cuenta contable', 'type': 'decimal', 'role': 'dimension'},
            {'field': 'tipo', 'label': 'Tipo documento', 'type': 'text', 'role': 'dimension'},
            {'field': 'invc', 'label': 'Nro factura', 'type': 'text', 'role': 'dimension'},
            {'field': 'descripcion', 'label': 'Descripción', 'type': 'text', 'role': 'dimension'},
        ],
        'Temporal': [
            {'field': 'fecha', 'label': 'Fecha', 'type': 'date', 'role': 'dimension'},
            {'field': 'duedate', 'label': 'Vencimiento', 'type': 'date', 'role': 'dimension'},
            {'field': 'periodo', 'label': 'Período', 'type': 'text', 'role': 'dimension'},
        ],
        'Valores': [
            {'field': 'debito', 'label': 'Débito', 'type': 'decimal', 'role': 'metric'},
            {'field': 'credito', 'label': 'Crédito', 'type': 'decimal', 'role': 'metric'},
            {'field': 'saldo', 'label': 'Saldo', 'type': 'decimal', 'role': 'metric'},
        ],
        'Dimensiones': [
            {'field': 'departamento', 'label': 'Departamento', 'type': 'integer', 'role': 'dimension'},
            {'field': 'centro_costo', 'label': 'Centro costo', 'type': 'integer', 'role': 'dimension'},
            {'field': 'proyecto_codigo', 'label': 'Proyecto', 'type': 'text', 'role': 'dimension'},
        ],
    },
    'inventario': {
        'Producto': [
            {'field': 'item_codigo', 'label': 'Código producto', 'type': 'text', 'role': 'dimension'},
            {'field': 'item_descripcion', 'label': 'Descripción producto', 'type': 'text', 'role': 'dimension'},
            {'field': 'location', 'label': 'Bodega', 'type': 'text', 'role': 'dimension'},
        ],
        'Documento': [
            {'field': 'tipo', 'label': 'Tipo documento', 'type': 'text', 'role': 'dimension'},
            {'field': 'batch', 'label': 'Batch', 'type': 'integer', 'role': 'dimension'},
        ],
        'Tercero': [
            {'field': 'tercero_id', 'label': 'ID Tercero', 'type': 'text', 'role': 'dimension'},
        ],
        'Temporal': [
            {'field': 'fecha', 'label': 'Fecha', 'type': 'date', 'role': 'dimension'},
            {'field': 'periodo', 'label': 'Período', 'type': 'text', 'role': 'dimension'},
        ],
        'Valores': [
            {'field': 'cantidad', 'label': 'Cantidad', 'type': 'decimal', 'role': 'metric'},
            {'field': 'valor_unitario', 'label': 'Valor unitario', 'type': 'decimal', 'role': 'metric'},
            {'field': 'costo_peps', 'label': 'Costo PEPS', 'type': 'decimal', 'role': 'metric'},
            {'field': 'total', 'label': 'Total', 'type': 'decimal', 'role': 'metric'},
            {'field': 'saldo_unidades', 'label': 'Saldo unidades', 'type': 'decimal', 'role': 'metric'},
            {'field': 'saldo_pesos', 'label': 'Saldo pesos', 'type': 'decimal', 'role': 'metric'},
        ],
        'Trazabilidad': [
            {'field': 'lote', 'label': 'Lote', 'type': 'text', 'role': 'dimension'},
            {'field': 'serie', 'label': 'Serie', 'type': 'text', 'role': 'dimension'},
            {'field': 'lote_vencimiento', 'label': 'Vencimiento lote', 'type': 'date', 'role': 'dimension'},
        ],
    },
}

# Filtros aplicables por fuente
SOURCE_FILTERS = {
    'gl': [
        {'key': 'fecha_desde', 'label': 'Fecha desde', 'type': 'date', 'field': 'fecha__gte'},
        {'key': 'fecha_hasta', 'label': 'Fecha hasta', 'type': 'date', 'field': 'fecha__lte'},
        {'key': 'periodos', 'label': 'Períodos', 'type': 'multi_select', 'field': 'periodo__in'},
        {'key': 'tercero_ids', 'label': 'Terceros', 'type': 'autocomplete_multi', 'field': 'tercero_id__in'},
        {'key': 'tipo_doc', 'label': 'Tipo documento', 'type': 'multi_select', 'field': 'tipo__in'},
        {'key': 'cuenta_desde', 'label': 'Cuenta desde', 'type': 'decimal', 'field': 'auxiliar__gte'},
        {'key': 'cuenta_hasta', 'label': 'Cuenta hasta', 'type': 'decimal', 'field': 'auxiliar__lte'},
        {'key': 'proyecto_codigos', 'label': 'Proyectos', 'type': 'multi_select', 'field': 'proyecto_codigo__in'},
        {'key': 'departamento_codigos', 'label': 'Departamentos', 'type': 'multi_select', 'field': 'departamento_codigo__in'},
        {'key': 'centro_costo_codigos', 'label': 'Centros de costo', 'type': 'multi_select', 'field': 'centro_costo_codigo__in'},
    ],
    'facturacion': [
        {'key': 'fecha_desde', 'label': 'Fecha desde', 'type': 'date', 'field': 'fecha__gte'},
        {'key': 'fecha_hasta', 'label': 'Fecha hasta', 'type': 'date', 'field': 'fecha__lte'},
        {'key': 'periodos', 'label': 'Períodos', 'type': 'multi_select', 'field': 'periodo__in'},
        {'key': 'tercero_ids', 'label': 'Terceros', 'type': 'autocomplete_multi', 'field': 'tercero_id__in'},
        {'key': 'tipo_doc', 'label': 'Tipo', 'type': 'multi_select', 'field': 'tipo__in'},
        {'key': 'salesman', 'label': 'Vendedor', 'type': 'select', 'field': 'salesman'},
        {'key': 'posted', 'label': 'Contabilizado', 'type': 'boolean', 'field': 'posted'},
        {'key': 'closed', 'label': 'Cerrado', 'type': 'boolean', 'field': 'closed'},
    ],
    'facturacion_detalle': [
        {'key': 'fecha_desde', 'label': 'Fecha desde', 'type': 'date', 'field': 'factura__fecha__gte'},
        {'key': 'fecha_hasta', 'label': 'Fecha hasta', 'type': 'date', 'field': 'factura__fecha__lte'},
        {'key': 'item_codigos', 'label': 'Productos', 'type': 'autocomplete_multi', 'field': 'item_codigo__in'},
        {'key': 'proyecto_codigos', 'label': 'Proyectos', 'type': 'multi_select', 'field': 'proyecto_codigo__in'},
    ],
    'cartera': [
        {'key': 'fecha_desde', 'label': 'Fecha desde', 'type': 'date', 'field': 'fecha__gte'},
        {'key': 'fecha_hasta', 'label': 'Fecha hasta', 'type': 'date', 'field': 'fecha__lte'},
        {'key': 'periodos', 'label': 'Períodos', 'type': 'multi_select', 'field': 'periodo__in'},
        {'key': 'tercero_ids', 'label': 'Terceros', 'type': 'autocomplete_multi', 'field': 'tercero_id__in'},
        {'key': 'tipo_cartera', 'label': 'Tipo cartera', 'type': 'select', 'field': 'tipo_cartera'},
        {'key': 'duedate_desde', 'label': 'Vencimiento desde', 'type': 'date', 'field': 'duedate__gte'},
        {'key': 'duedate_hasta', 'label': 'Vencimiento hasta', 'type': 'date', 'field': 'duedate__lte'},
        {'key': 'proyecto_codigos', 'label': 'Proyectos', 'type': 'multi_select', 'field': 'proyecto_codigo__in'},
    ],
    'inventario': [
        {'key': 'fecha_desde', 'label': 'Fecha desde', 'type': 'date', 'field': 'fecha__gte'},
        {'key': 'fecha_hasta', 'label': 'Fecha hasta', 'type': 'date', 'field': 'fecha__lte'},
        {'key': 'periodos', 'label': 'Períodos', 'type': 'multi_select', 'field': 'periodo__in'},
        {'key': 'item_codigos', 'label': 'Productos', 'type': 'autocomplete_multi', 'field': 'item_codigo__in'},
        {'key': 'location', 'label': 'Bodega', 'type': 'select', 'field': 'location'},
        {'key': 'tipo_doc', 'label': 'Tipo documento', 'type': 'multi_select', 'field': 'tipo__in'},
    ],
}

# Metadatos de fuentes para el selector
SOURCE_META = [
    {
        'key': 'gl',
        'label': 'Contabilidad (GL)',
        'icon': 'account_balance',
        'description': 'Asientos contables, balances, estados financieros',
    },
    {
        'key': 'facturacion',
        'label': 'Facturación',
        'icon': 'receipt_long',
        'description': 'Ventas, compras, notas crédito, devoluciones',
    },
    {
        'key': 'facturacion_detalle',
        'label': 'Facturación (Detalle)',
        'icon': 'receipt_long',
        'description': 'Líneas de factura: productos, cantidades, precios, márgenes',
    },
    {
        'key': 'cartera',
        'label': 'Cartera (CxC/CxP)',
        'icon': 'payments',
        'description': 'Cuentas por cobrar, cuentas por pagar, aging',
    },
    {
        'key': 'inventario',
        'label': 'Inventario',
        'icon': 'inventory_2',
        'description': 'Entradas, salidas, saldos, rotación',
    },
]

_DEFAULT_PAGE_SIZE = 50
_MAX_PAGE_SIZE = 5000


class BIQueryEngine:
    """Motor que traduce la configuración JSON de un ReportBI a queries Django ORM."""

    def _get_model(self, source: str):
        """Resuelve el modelo Django a partir del nombre de fuente."""
        model_path = SOURCE_MODEL_MAP.get(source)
        if not model_path:
            return None
        app_label, model_name = model_path.rsplit('.', 1)
        return apps.get_model(app_label, model_name)

    def _get_valid_fields(self, source: str) -> set:
        """Retorna el set de nombres de campo válidos para una fuente."""
        fields = set()
        for category_fields in SOURCE_FIELDS.get(source, {}).values():
            for f in category_fields:
                fields.add(f['field'])
        return fields

    def _apply_filters(self, qs: QuerySet, filtros: dict, source: str) -> QuerySet:
        """Aplica filtros validados al queryset."""
        source_filter_defs = {f['key']: f for f in SOURCE_FILTERS.get(source, [])}
        for key, value in filtros.items():
            if value is None or value == '' or value == []:
                continue
            filter_def = source_filter_defs.get(key)
            if not filter_def:
                continue
            qs = qs.filter(**{filter_def['field']: value})
        return qs

    def execute(self, report, company_id) -> dict:
        """
        Ejecuta el reporte y retorna datos formateados.
        Retorna: {columns: [...], rows: [...], total_count: int}
        """
        if not report.fuentes:
            return {'columns': [], 'rows': [], 'total_count': 0}

        source = report.fuentes[0]
        model = self._get_model(source)
        if not model:
            return {'columns': [], 'rows': [], 'total_count': 0}

        valid_fields = self._get_valid_fields(source)

        # Base queryset con filtro de tenant obligatorio
        qs = model.objects.filter(company_id=company_id)

        # Aplicar filtros
        qs = self._apply_filters(qs, report.filtros or {}, source)

        # Separar dimensiones y métricas
        dimensions = []
        metrics = []
        columns = []
        for campo in (report.campos_config or []):
            field_name = campo.get('field', '')
            if field_name not in valid_fields:
                continue
            role = campo.get('role', 'dimension')
            label = campo.get('label', field_name)
            if role == 'metric':
                agg = campo.get('aggregation', 'SUM').upper()
                if agg not in _AGGREGATION_MAP:
                    agg = 'SUM'
                metrics.append({'field': field_name, 'aggregation': agg, 'label': label})
                columns.append({'field': f'{field_name}_{agg.lower()}', 'label': label, 'type': 'metric'})
            else:
                dimensions.append(field_name)
                columns.append({'field': field_name, 'label': label, 'type': 'dimension'})

        if not dimensions and not metrics:
            return {'columns': [], 'rows': [], 'total_count': 0}

        # Si hay métricas con agregación, agrupar por dimensiones
        if metrics and dimensions:
            qs = qs.values(*dimensions)
            annotations = {}
            for m in metrics:
                agg_func = _AGGREGATION_MAP[m['aggregation']]
                alias = f"{m['field']}_{m['aggregation'].lower()}"
                annotations[alias] = agg_func(m['field'])
            qs = qs.annotate(**annotations)
        elif metrics and not dimensions:
            # Solo métricas sin dimensiones = una fila de totales
            annotations = {}
            for m in metrics:
                agg_func = _AGGREGATION_MAP[m['aggregation']]
                alias = f"{m['field']}_{m['aggregation'].lower()}"
                annotations[alias] = agg_func(m['field'])
            result = qs.aggregate(**annotations)
            row = {}
            for key, val in result.items():
                row[key] = float(val) if val is not None else 0
            return {'columns': columns, 'rows': [row], 'total_count': 1}
        else:
            # Solo dimensiones, sin agregación
            qs = qs.values(*dimensions)

        # Ordenar
        order_fields = []
        for o in (report.orden_config or []):
            field = o.get('field', '')
            direction = o.get('direction', 'asc')
            # Validar que el campo existe en columns
            valid_order_fields = {c['field'] for c in columns}
            if field in valid_order_fields:
                order_fields.append(f'-{field}' if direction == 'desc' else field)
        if order_fields:
            qs = qs.order_by(*order_fields)

        # Total antes de limitar
        total_count = qs.count()

        # Limitar
        limit = report.limite_registros or _DEFAULT_PAGE_SIZE
        limit = min(limit, _MAX_PAGE_SIZE)
        rows = list(qs[:limit])

        # Serializar Decimals a float para JSON
        for row in rows:
            for key, val in row.items():
                if isinstance(val, Decimal):
                    row[key] = float(val)

        return {
            'columns': columns,
            'rows': rows,
            'total_count': total_count,
        }

    def execute_pivot(self, report, company_id) -> dict:
        """
        Ejecuta un reporte en modo pivot table.
        viz_config debe tener: {rows: [...], columns: [...], values: [...]}
        Retorna: {row_headers, col_headers, data, row_totals, col_totals, grand_total}
        """
        if not report.fuentes:
            return self._empty_pivot()

        source = report.fuentes[0]
        model = self._get_model(source)
        if not model:
            return self._empty_pivot()

        valid_fields = self._get_valid_fields(source)
        viz = report.viz_config or {}

        row_fields = [f for f in (viz.get('rows') or []) if f in valid_fields]
        col_fields = [f for f in (viz.get('columns') or []) if f in valid_fields]
        value_configs = viz.get('values') or []

        if not row_fields or not value_configs:
            return self._empty_pivot()

        # Base queryset
        qs = model.objects.filter(company_id=company_id)
        qs = self._apply_filters(qs, report.filtros or {}, source)

        # Agrupar por filas + columnas
        group_fields = row_fields + col_fields
        qs = qs.values(*group_fields)

        # Anotar valores
        annotations = {}
        for vc in value_configs:
            field = vc.get('field', '')
            agg = vc.get('aggregation', 'SUM').upper()
            if field not in valid_fields or agg not in _AGGREGATION_MAP:
                continue
            alias = f"{field}_{agg.lower()}"
            annotations[alias] = _AGGREGATION_MAP[agg](field)

        if not annotations:
            return self._empty_pivot()

        qs = qs.annotate(**annotations)
        data_rows = list(qs)

        # Construir estructura de pivot
        row_keys = OrderedDict()
        col_keys = OrderedDict()
        cells = {}

        for row in data_rows:
            rk = tuple(row.get(f) for f in row_fields)
            ck = tuple(row.get(f) for f in col_fields) if col_fields else ('total',)

            row_key_str = '|'.join(str(v) for v in rk)
            col_key_str = '|'.join(str(v) for v in ck)

            if row_key_str not in row_keys:
                row_keys[row_key_str] = {f: row.get(f) for f in row_fields}
            if col_key_str not in col_keys:
                col_keys[col_key_str] = {f: row.get(f) for f in col_fields} if col_fields else {'total': 'Total'}

            cell_values = {}
            for alias in annotations:
                val = row.get(alias)
                cell_values[alias] = float(val) if isinstance(val, Decimal) else (val or 0)
            cells[f'{row_key_str}___{col_key_str}'] = cell_values

        # Calcular totales de fila y columna
        row_totals = {}
        col_totals = {}
        grand_total = {alias: 0 for alias in annotations}

        for rk_str in row_keys:
            row_totals[rk_str] = {alias: 0 for alias in annotations}
            for ck_str in col_keys:
                cell = cells.get(f'{rk_str}___{ck_str}', {})
                for alias in annotations:
                    val = cell.get(alias, 0)
                    row_totals[rk_str][alias] += val

        for ck_str in col_keys:
            col_totals[ck_str] = {alias: 0 for alias in annotations}
            for rk_str in row_keys:
                cell = cells.get(f'{rk_str}___{ck_str}', {})
                for alias in annotations:
                    val = cell.get(alias, 0)
                    col_totals[ck_str][alias] += val
                    grand_total[alias] += val

        return {
            'row_headers': list(row_keys.values()),
            'col_headers': list(col_keys.values()),
            'data': cells,
            'row_totals': row_totals,
            'col_totals': col_totals,
            'grand_total': grand_total,
            'value_aliases': list(annotations.keys()),
        }

    def get_available_sources(self) -> list:
        """Retorna metadatos de todas las fuentes disponibles."""
        return SOURCE_META

    def get_available_fields(self, source: str) -> dict:
        """Retorna campos disponibles organizados por categoría para una fuente."""
        return SOURCE_FIELDS.get(source, {})

    def get_available_filters(self, source: str) -> list:
        """Retorna filtros aplicables a una fuente."""
        return SOURCE_FILTERS.get(source, [])

    @staticmethod
    def _empty_pivot() -> dict:
        return {
            'row_headers': [],
            'col_headers': [],
            'data': {},
            'row_totals': {},
            'col_totals': {},
            'grand_total': {},
            'value_aliases': [],
        }
