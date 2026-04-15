"""
SaiSuite -- Dashboard: BI Query Engine v2
Motor multi-fuente que traduce la configuración JSON de un ReportBI a queries Django ORM.
Seguridad: company_id obligatorio en todas las queries. Sin SQL crudo.

Cambios v2 (2026-04-12):
- Soporte multi-fuente con JOINs automáticos vía Subquery + OuterRef
- 10 nuevas fuentes (terceros_saiopen, productos, cuentas_contables, etc.)
- FilterTranslator con 12 operadores por tipo de campo
- Retrocompatibilidad total con reportes v1 (formato dict de filtros)
"""
import ast
import logging
import operator as _op
from collections import OrderedDict
from decimal import Decimal

from django.apps import apps
from django.core.exceptions import ValidationError
from django.db.models import (
    Avg, Count, F, Max, Min, QuerySet, Subquery, Sum, OuterRef, Value,
    CharField,
)
from django.db.models.functions import Coalesce

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Utilidades de evaluación
# ─────────────────────────────────────────────────────────────────────────────

def _normalize_dim_value(v):
    """
    Convierte un valor de dimensión a representación JSON-safe.
    Decimal a int cuando es entero, a float si tiene decimales.
    """
    if isinstance(v, Decimal):
        f = float(v)
        return int(f) if f == int(f) else f
    return v


_SAFE_OPS = {
    ast.Add: _op.add,
    ast.Sub: _op.sub,
    ast.Mult: _op.mul,
    ast.Div: _op.truediv,
    ast.UAdd: _op.pos,
    ast.USub: _op.neg,
}


def _eval_node(node, ctx):
    """Evalúa un nodo AST restringido a aritmética simple + variables de ctx."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.Name):
        return float(ctx[node.id])
    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left, ctx)
        right = _eval_node(node.right, ctx)
        fn = _SAFE_OPS.get(type(node.op))
        if fn is None:
            raise ValueError(f'Operador no permitido: {type(node.op).__name__}')
        return fn(left, right)
    if isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand, ctx)
        fn = _SAFE_OPS.get(type(node.op))
        if fn is None:
            raise ValueError(f'Operador unario no permitido: {type(node.op).__name__}')
        return fn(operand)
    raise ValueError(f'Nodo AST no permitido: {type(node).__name__}')


def _safe_eval_formula(formula: str, context: dict) -> float | None:
    """
    Evalúa una fórmula aritmética simple con variables del contexto.
    Solo permite: constantes numéricas, variables conocidas, +, -, *, /.
    Retorna None si la fórmula es inválida o hay división por cero.
    """
    try:
        tree = ast.parse(formula.strip(), mode='eval')
        return _eval_node(tree.body, context)
    except (ZeroDivisionError, KeyError, ValueError, TypeError, SyntaxError):
        return None


_AGGREGATION_MAP = {
    'SUM': Sum,
    'AVG': Avg,
    'COUNT': Count,
    'MIN': Min,
    'MAX': Max,
}


# ─────────────────────────────────────────────────────────────────────────────
# Mapas de fuentes → modelos Django
# ─────────────────────────────────────────────────────────────────────────────

SOURCE_MODEL_MAP = {
    # Fuentes v1 — Transaccionales
    'gl': 'contabilidad.MovimientoContable',
    'facturacion': 'contabilidad.FacturaEncabezado',
    'facturacion_detalle': 'contabilidad.FacturaDetalle',
    'cartera': 'contabilidad.MovimientoCartera',
    'inventario': 'contabilidad.MovimientoInventario',
    'terceros': 'terceros.Tercero',            # alias legacy: mantener compatibilidad
    # Fuentes v2 — Maestros/Dimensiones Saiopen
    'terceros_saiopen': 'contabilidad.TerceroSaiopen',
    'direcciones_envio': 'contabilidad.ShipToSaiopen',
    'cuentas_contables': 'contabilidad.CuentaContable',
    'proyectos_saiopen': 'contabilidad.ProyectoSaiopen',
    'actividades_saiopen': 'contabilidad.ActividadSaiopen',
    'departamentos': 'contabilidad.ListaSaiopen',   # filtro base: tipo='DP'
    'centros_costo': 'contabilidad.ListaSaiopen',   # filtro base: tipo='CC'
    'tipos_documento': 'contabilidad.TipdocSaiopen',
    # Fuentes v2 — CRM
    'productos': 'crm.CrmProducto',
    'impuestos': 'crm.CrmImpuesto',
}

# Filtros base aplicados automáticamente al obtener el queryset de una fuente.
# Garantiza que ListaSaiopen se filtre correctamente por tipo.
SOURCE_BASE_FILTERS = {
    'departamentos': {'tipo': 'DP'},
    'centros_costo': {'tipo': 'CC'},
}

# ─────────────────────────────────────────────────────────────────────────────
# Campos disponibles por fuente
# ─────────────────────────────────────────────────────────────────────────────

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
            {'field': 'tercero_id', 'label': 'Identificación', 'type': 'text', 'role': 'dimension'},
            {'field': 'tercero_nombre', 'label': 'Nombre', 'type': 'text', 'role': 'dimension'},
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
            {'field': 'tipo', 'label': 'Tipo', 'type': 'text', 'role': 'dimension'},
            {'field': 'batch', 'label': 'Número', 'type': 'integer', 'role': 'dimension'},
            {'field': 'invc', 'label': 'Número cruce', 'type': 'text', 'role': 'dimension'},
            {'field': 'cruce', 'label': 'Tipo cruce', 'type': 'text', 'role': 'dimension'},
            {'field': 'descripcion', 'label': 'Descripción', 'type': 'text', 'role': 'dimension'},
        ],
    },
    'facturacion': {
        'Documento': [
            {'field': 'number', 'label': 'Número', 'type': 'integer', 'role': 'dimension'},
            {'field': 'tipo', 'label': 'Tipo', 'type': 'text', 'role': 'dimension'},
            {'field': 'tipo_descripcion', 'label': 'Tipo documento', 'type': 'text', 'role': 'dimension'},
            {'field': 'id_sucursal', 'label': 'Sucursal', 'type': 'integer', 'role': 'dimension'},
            {'field': 'posted', 'label': 'Contabilizado', 'type': 'boolean', 'role': 'dimension'},
            {'field': 'comentarios', 'label': 'Comentarios', 'type': 'text', 'role': 'dimension'},
        ],
        'Tercero': [
            {'field': 'tercero_id', 'label': 'Identificación', 'type': 'text', 'role': 'dimension'},
            {'field': 'tercero_nombre', 'label': 'Nombre', 'type': 'text', 'role': 'dimension'},
            {'field': 'tercero_razon_social', 'label': 'Razón social', 'type': 'text', 'role': 'dimension'},
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
            {'field': 'destotal', 'label': 'Descuento total', 'type': 'decimal', 'role': 'metric'},
            {'field': 'otroscargos', 'label': 'Otros cargos', 'type': 'decimal', 'role': 'metric'},
            {'field': 'total', 'label': 'Total', 'type': 'decimal', 'role': 'metric'},
        ],
        'Retenciones': [
            {'field': 'porcrtfte', 'label': '% Retefuente', 'type': 'decimal', 'role': 'metric'},
            {'field': 'reteica', 'label': 'Reteica', 'type': 'decimal', 'role': 'metric'},
            {'field': 'porcentaje_reteica', 'label': '% Reteica', 'type': 'decimal', 'role': 'metric'},
            {'field': 'reteiva', 'label': 'Reteiva', 'type': 'decimal', 'role': 'metric'},
        ],
    },
    'facturacion_detalle': {
        'Producto': [
            {'field': 'item_codigo', 'label': 'Código', 'type': 'text', 'role': 'dimension'},
            {'field': 'item_descripcion', 'label': 'Descripción', 'type': 'text', 'role': 'dimension'},
            {'field': 'location', 'label': 'Bodega', 'type': 'text', 'role': 'dimension'},
        ],
        'Cantidades': [
            {'field': 'qty_order', 'label': 'Cantidad pedida', 'type': 'decimal', 'role': 'metric'},
            {'field': 'qty_ship', 'label': 'Cantidad', 'type': 'decimal', 'role': 'metric'},
        ],
        'Precios': [
            {'field': 'precio_unitario', 'label': 'Precio unitario', 'type': 'decimal', 'role': 'metric'},
            {'field': 'precio_extendido', 'label': 'Subtotal línea', 'type': 'decimal', 'role': 'metric'},
            {'field': 'costo_unitario', 'label': 'Costo unitario', 'type': 'decimal', 'role': 'metric'},
        ],
        'Impuestos': [
            {'field': 'valor_iva', 'label': 'Valor IVA', 'type': 'decimal', 'role': 'metric'},
            {'field': 'porc_iva', 'label': '% IVA', 'type': 'decimal', 'role': 'metric'},
            {'field': 'descuento', 'label': 'Descuento', 'type': 'decimal', 'role': 'metric'},
            {'field': 'total_descuento', 'label': 'Total descuento', 'type': 'decimal', 'role': 'metric'},
        ],
        'Márgenes': [
            {'field': 'margen_valor', 'label': 'Margen valor', 'type': 'decimal', 'role': 'metric'},
            {'field': 'margen_porcentaje', 'label': 'Margen %', 'type': 'decimal', 'role': 'metric'},
        ],
        'Dimensiones': [
            {'field': 'proyecto_codigo', 'label': 'Proyecto', 'type': 'text', 'role': 'dimension'},
            {'field': 'departamento_codigo', 'label': 'Departamento', 'type': 'text', 'role': 'dimension'},
            {'field': 'centro_costo_codigo', 'label': 'Centro costo', 'type': 'text', 'role': 'dimension'},
            {'field': 'actividad_codigo', 'label': 'Actividad', 'type': 'text', 'role': 'dimension'},
        ],
    },
    'cartera': {
        'Tercero': [
            {'field': 'tercero_id', 'label': 'Identificación', 'type': 'text', 'role': 'dimension'},
            {'field': 'tercero_nombre', 'label': 'Nombre', 'type': 'text', 'role': 'dimension'},
        ],
        'Clasificación': [
            {'field': 'tipo_cartera', 'label': 'Tipo cartera', 'type': 'text', 'role': 'dimension'},
            {'field': 'cuenta_contable', 'label': 'Cuenta contable', 'type': 'decimal', 'role': 'dimension'},
            {'field': 'tipo', 'label': 'Tipo', 'type': 'text', 'role': 'dimension'},
            {'field': 'invc', 'label': 'Cruce', 'type': 'text', 'role': 'dimension'},
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
            {'field': 'location', 'label': 'Bodega', 'type': 'text', 'role': 'dimension'},
        ],
        'Documento': [
            {'field': 'tipo', 'label': 'Tipo', 'type': 'text', 'role': 'dimension'},
            {'field': 'batch', 'label': 'Número', 'type': 'integer', 'role': 'dimension'},
        ],
        'Tercero': [
            {'field': 'tercero_id', 'label': 'Identificación', 'type': 'text', 'role': 'dimension'},
        ],
        'Temporal': [
            {'field': 'fecha', 'label': 'Fecha', 'type': 'date', 'role': 'dimension'},
            {'field': 'periodo', 'label': 'Período', 'type': 'text', 'role': 'dimension'},
        ],
        'Valores': [
            {'field': 'cantidad', 'label': 'Cantidad', 'type': 'decimal', 'role': 'metric'},
            {'field': 'valor_unitario', 'label': 'Valor unitario', 'type': 'decimal', 'role': 'metric'},
            {'field': 'costo_promedio', 'label': 'Costo promedio', 'type': 'decimal', 'role': 'metric'},
            {'field': 'total', 'label': 'Total', 'type': 'decimal', 'role': 'metric'},
        ],
        'Trazabilidad': [
            {'field': 'lote', 'label': 'Lote', 'type': 'text', 'role': 'dimension'},
            {'field': 'serie', 'label': 'Serie', 'type': 'text', 'role': 'dimension'},
            {'field': 'lote_vencimiento', 'label': 'Vencimiento lote', 'type': 'date', 'role': 'dimension'},
        ],
    },
    'terceros': {
        'Identificación': [
            {'field': 'codigo', 'label': 'Código', 'type': 'text', 'role': 'dimension'},
            {'field': 'tipo_identificacion', 'label': 'Tipo ID', 'type': 'text', 'role': 'dimension'},
            {'field': 'numero_identificacion', 'label': 'Número ID', 'type': 'text', 'role': 'dimension'},
            {'field': 'nombre_completo', 'label': 'Nombre completo', 'type': 'text', 'role': 'dimension'},
            {'field': 'tipo_persona', 'label': 'Tipo persona', 'type': 'text', 'role': 'dimension'},
            {'field': 'tipo_tercero', 'label': 'Tipo tercero', 'type': 'text', 'role': 'dimension'},
        ],
        'Contacto': [
            {'field': 'email', 'label': 'Email', 'type': 'text', 'role': 'dimension'},
            {'field': 'telefono', 'label': 'Teléfono', 'type': 'text', 'role': 'dimension'},
            {'field': 'celular', 'label': 'Celular', 'type': 'text', 'role': 'dimension'},
        ],
        'Estado': [
            {'field': 'activo', 'label': 'Activo', 'type': 'boolean', 'role': 'dimension'},
            {'field': 'saiopen_synced', 'label': 'Sincronizado con Saiopen', 'type': 'boolean', 'role': 'dimension'},
        ],
    },
    # ── Nuevas fuentes v2 ──────────────────────────────────────────────────
    'terceros_saiopen': {
        'Tercero': [
            {'field': 'id_n', 'label': 'Identificación', 'type': 'text', 'role': 'dimension'},
            {'field': 'nit', 'label': 'NIT', 'type': 'text', 'role': 'dimension'},
            {'field': 'nombre', 'label': 'Nombre', 'type': 'text', 'role': 'dimension'},
        ],
        'Tipo': [
            {'field': 'es_cliente', 'label': 'Es cliente', 'type': 'boolean', 'role': 'dimension'},
            {'field': 'es_proveedor', 'label': 'Es proveedor', 'type': 'boolean', 'role': 'dimension'},
            {'field': 'es_empleado', 'label': 'Es empleado', 'type': 'boolean', 'role': 'dimension'},
            {'field': 'regimen', 'label': 'Régimen', 'type': 'text', 'role': 'dimension'},
            {'field': 'activo', 'label': 'Activo', 'type': 'boolean', 'role': 'dimension'},
        ],
        'Contacto': [
            {'field': 'direccion', 'label': 'Dirección', 'type': 'text', 'role': 'dimension'},
            {'field': 'ciudad', 'label': 'Ciudad', 'type': 'text', 'role': 'dimension'},
            {'field': 'departamento', 'label': 'Departamento', 'type': 'text', 'role': 'dimension'},
            {'field': 'telefono', 'label': 'Teléfono', 'type': 'text', 'role': 'dimension'},
            {'field': 'email', 'label': 'Email', 'type': 'text', 'role': 'dimension'},
        ],
        'Financiero': [
            {'field': 'creditlmt', 'label': 'Límite de crédito', 'type': 'decimal', 'role': 'metric'},
        ],
    },
    'direcciones_envio': {
        'Dirección': [
            {'field': 'succliente', 'label': 'Sucursal cliente', 'type': 'text', 'role': 'dimension'},
            {'field': 'descripcion', 'label': 'Descripción', 'type': 'text', 'role': 'dimension'},
            {'field': 'nombre', 'label': 'Nombre', 'type': 'text', 'role': 'dimension'},
            {'field': 'addr1', 'label': 'Dirección', 'type': 'text', 'role': 'dimension'},
            {'field': 'ciudad', 'label': 'Ciudad', 'type': 'text', 'role': 'dimension'},
            {'field': 'departamento', 'label': 'Departamento', 'type': 'text', 'role': 'dimension'},
            {'field': 'zona', 'label': 'Zona', 'type': 'text', 'role': 'dimension'},
        ],
        'Contacto': [
            {'field': 'telefono', 'label': 'Teléfono', 'type': 'text', 'role': 'dimension'},
            {'field': 'email', 'label': 'Email', 'type': 'text', 'role': 'dimension'},
        ],
    },
    'cuentas_contables': {
        'Jerarquía PUC': [
            {'field': 'codigo', 'label': 'Código cuenta', 'type': 'decimal', 'role': 'dimension'},
            {'field': 'descripcion', 'label': 'Descripción', 'type': 'text', 'role': 'dimension'},
            {'field': 'nivel', 'label': 'Nivel', 'type': 'integer', 'role': 'dimension'},
            {'field': 'clase', 'label': 'Clase', 'type': 'text', 'role': 'dimension'},
            {'field': 'tipo', 'label': 'Tipo', 'type': 'text', 'role': 'dimension'},
            {'field': 'titulo_codigo', 'label': 'Título código', 'type': 'text', 'role': 'dimension'},
            {'field': 'grupo_codigo', 'label': 'Grupo código', 'type': 'text', 'role': 'dimension'},
            {'field': 'cuenta_codigo', 'label': 'Cuenta código', 'type': 'text', 'role': 'dimension'},
            {'field': 'subcuenta_codigo', 'label': 'Subcuenta código', 'type': 'text', 'role': 'dimension'},
            {'field': 'posicion_financiera', 'label': 'Posición financiera', 'type': 'text', 'role': 'dimension'},
        ],
    },
    'proyectos_saiopen': {
        'Proyecto': [
            {'field': 'codigo', 'label': 'Código', 'type': 'text', 'role': 'dimension'},
            {'field': 'descripcion', 'label': 'Descripción', 'type': 'text', 'role': 'dimension'},
            {'field': 'cliente_nit', 'label': 'NIT cliente', 'type': 'text', 'role': 'dimension'},
            {'field': 'estado', 'label': 'Estado', 'type': 'text', 'role': 'dimension'},
        ],
        'Fechas': [
            {'field': 'fecha_inicio', 'label': 'Fecha inicio', 'type': 'date', 'role': 'dimension'},
            {'field': 'fecha_estimada_fin', 'label': 'Fecha estimada fin', 'type': 'date', 'role': 'dimension'},
        ],
        'Financiero': [
            {'field': 'costo_estimado', 'label': 'Costo estimado', 'type': 'decimal', 'role': 'metric'},
        ],
    },
    'actividades_saiopen': {
        'Actividad': [
            {'field': 'codigo', 'label': 'Código', 'type': 'text', 'role': 'dimension'},
            {'field': 'descripcion', 'label': 'Descripción', 'type': 'text', 'role': 'dimension'},
            {'field': 'proyecto_codigo', 'label': 'Proyecto', 'type': 'text', 'role': 'dimension'},
            {'field': 'departamento_codigo', 'label': 'Departamento', 'type': 'text', 'role': 'dimension'},
            {'field': 'centro_costo_codigo', 'label': 'Centro de costo', 'type': 'text', 'role': 'dimension'},
        ],
    },
    'departamentos': {
        'Departamento': [
            {'field': 'codigo', 'label': 'Código', 'type': 'integer', 'role': 'dimension'},
            {'field': 'descripcion', 'label': 'Descripción', 'type': 'text', 'role': 'dimension'},
            {'field': 'activo', 'label': 'Activo', 'type': 'boolean', 'role': 'dimension'},
        ],
    },
    'centros_costo': {
        'Centro de costo': [
            {'field': 'codigo', 'label': 'Código', 'type': 'integer', 'role': 'dimension'},
            {'field': 'descripcion', 'label': 'Descripción', 'type': 'text', 'role': 'dimension'},
            {'field': 'activo', 'label': 'Activo', 'type': 'boolean', 'role': 'dimension'},
        ],
    },
    'tipos_documento': {
        'Tipo de documento': [
            {'field': 'clase', 'label': 'Clase', 'type': 'text', 'role': 'dimension'},
            {'field': 'tipo', 'label': 'Tipo', 'type': 'text', 'role': 'dimension'},
            {'field': 'descripcion', 'label': 'Descripción', 'type': 'text', 'role': 'dimension'},
            {'field': 'sigla', 'label': 'Sigla', 'type': 'text', 'role': 'dimension'},
        ],
    },
    'productos': {
        'Producto': [
            {'field': 'codigo', 'label': 'Código', 'type': 'text', 'role': 'dimension'},
            {'field': 'nombre', 'label': 'Nombre', 'type': 'text', 'role': 'dimension'},
            {'field': 'descripcion', 'label': 'Descripción', 'type': 'text', 'role': 'dimension'},
            {'field': 'reffabrica', 'label': 'Ref. fábrica', 'type': 'text', 'role': 'dimension'},
            {'field': 'unidad_venta', 'label': 'Unidad de venta', 'type': 'text', 'role': 'dimension'},
            {'field': 'is_active', 'label': 'Activo', 'type': 'boolean', 'role': 'dimension'},
        ],
        'Clasificación': [
            {'field': 'clase', 'label': 'Clase', 'type': 'text', 'role': 'dimension'},
            {'field': 'linea_codigo', 'label': 'Código línea', 'type': 'text', 'role': 'dimension'},
            {'field': 'linea_descripcion', 'label': 'Línea', 'type': 'text', 'role': 'dimension'},
            {'field': 'grupo', 'label': 'Código grupo', 'type': 'text', 'role': 'dimension'},
            {'field': 'grupo_descripcion', 'label': 'Grupo', 'type': 'text', 'role': 'dimension'},
            {'field': 'subgrupo_descripcion', 'label': 'Subgrupo', 'type': 'text', 'role': 'dimension'},
        ],
        'Precios': [
            {'field': 'precio_base', 'label': 'Precio base', 'type': 'decimal', 'role': 'metric'},
        ],
    },
    'impuestos': {
        'Impuesto': [
            {'field': 'nombre', 'label': 'Nombre', 'type': 'text', 'role': 'dimension'},
            {'field': 'porcentaje', 'label': 'Porcentaje', 'type': 'decimal', 'role': 'metric'},
        ],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Filtros legacy por fuente (formato v1 — compatibilidad)
# ─────────────────────────────────────────────────────────────────────────────

SOURCE_FILTERS = {
    'gl': [
        {'key': 'fecha_desde', 'label': 'Fecha desde', 'type': 'date', 'field': 'fecha__gte'},
        {'key': 'fecha_hasta', 'label': 'Fecha hasta', 'type': 'date', 'field': 'fecha__lte'},
        {'key': 'periodos', 'label': 'Períodos', 'type': 'multi_select', 'field': 'periodo__in'},
        {'key': 'tercero_ids', 'label': 'Terceros', 'type': 'autocomplete_multi', 'field': 'tercero_id__in'},
        {'key': 'tipo_doc', 'label': 'Tipo', 'type': 'multi_select', 'field': 'tipo__in'},
        {'key': 'cuenta_desde', 'label': 'Cuenta desde', 'type': 'decimal', 'field': 'auxiliar__gte'},
        {'key': 'cuenta_hasta', 'label': 'Cuenta hasta', 'type': 'decimal', 'field': 'auxiliar__lte'},
        {'key': 'proyecto_codigos', 'label': 'Proyectos', 'type': 'multi_select', 'field': 'proyecto_codigo__in'},
        {'key': 'departamento_codigos', 'label': 'Departamentos', 'type': 'multi_select', 'field': 'departamento_codigo__in'},
        {'key': 'centro_costo_codigos', 'label': 'Centros de costo', 'type': 'multi_select', 'field': 'centro_costo_codigo__in'},
        {'key': 'actividad_codigos', 'label': 'Actividades', 'type': 'multi_select', 'field': 'actividad_codigo__in'},
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
        {'key': 'tipo_doc', 'label': 'Tipo', 'type': 'multi_select', 'field': 'tipo__in'},
    ],
    'terceros': [
        {'key': 'tipo_tercero', 'label': 'Tipo tercero', 'type': 'select', 'field': 'tipo_tercero'},
        {'key': 'tipo_persona', 'label': 'Tipo persona', 'type': 'select', 'field': 'tipo_persona'},
        {'key': 'tipo_identificacion', 'label': 'Tipo ID', 'type': 'select', 'field': 'tipo_identificacion'},
        {'key': 'activo', 'label': 'Solo activos', 'type': 'boolean', 'field': 'activo'},
    ],
    # Nuevas fuentes v2 (filtros básicos)
    'terceros_saiopen': [
        {'key': 'es_cliente', 'label': 'Solo clientes', 'type': 'boolean', 'field': 'es_cliente'},
        {'key': 'es_proveedor', 'label': 'Solo proveedores', 'type': 'boolean', 'field': 'es_proveedor'},
        {'key': 'activo', 'label': 'Solo activos', 'type': 'boolean', 'field': 'activo'},
    ],
    'productos': [
        {'key': 'clase', 'label': 'Clase', 'type': 'select', 'field': 'clase'},
        {'key': 'grupo', 'label': 'Grupo', 'type': 'select', 'field': 'grupo'},
        {'key': 'is_active', 'label': 'Solo activos', 'type': 'boolean', 'field': 'is_active'},
    ],
    'proyectos_saiopen': [
        {'key': 'estado', 'label': 'Estado', 'type': 'select', 'field': 'estado'},
    ],
    'cuentas_contables': [
        {'key': 'nivel', 'label': 'Nivel', 'type': 'select', 'field': 'nivel'},
        {'key': 'clase', 'label': 'Clase', 'type': 'select', 'field': 'clase'},
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# Metadatos de fuentes para el selector del frontend
# ─────────────────────────────────────────────────────────────────────────────

SOURCE_META = [
    # Fuentes transaccionales
    {
        'key': 'gl',
        'label': 'Contabilidad (GL)',
        'icon': 'account_balance',
        'description': 'Asientos contables, balances, estados financieros',
        'group': 'transaccional',
    },
    {
        'key': 'facturacion',
        'label': 'Facturación',
        'icon': 'receipt_long',
        'description': 'Ventas, compras, notas crédito, devoluciones',
        'group': 'transaccional',
    },
    {
        'key': 'facturacion_detalle',
        'label': 'Facturación (Detalle)',
        'icon': 'receipt_long',
        'description': 'Líneas de factura: productos, cantidades, precios, márgenes',
        'group': 'transaccional',
    },
    {
        'key': 'cartera',
        'label': 'Cartera (CxC/CxP)',
        'icon': 'payments',
        'description': 'Cuentas por cobrar, cuentas por pagar, aging',
        'group': 'transaccional',
    },
    {
        'key': 'inventario',
        'label': 'Inventario',
        'icon': 'inventory_2',
        'description': 'Entradas, salidas, saldos, rotación',
        'group': 'transaccional',
    },
    # Fuentes dimensionales v2
    {
        'key': 'terceros_saiopen',
        'label': 'Terceros (Saiopen)',
        'icon': 'people',
        'description': 'Maestro de terceros: clientes, proveedores, empleados con datos de Saiopen',
        'group': 'dimensional',
    },
    {
        'key': 'productos',
        'label': 'Productos',
        'icon': 'inventory',
        'description': 'Catálogo de productos sincronizado desde Saiopen',
        'group': 'dimensional',
    },
    {
        'key': 'cuentas_contables',
        'label': 'Cuentas Contables',
        'icon': 'account_tree',
        'description': 'Plan Único de Cuentas (PUC) con jerarquía completa',
        'group': 'dimensional',
    },
    {
        'key': 'proyectos_saiopen',
        'label': 'Proyectos',
        'icon': 'folder_special',
        'description': 'Proyectos contables con costo estimado y cliente',
        'group': 'dimensional',
    },
    {
        'key': 'actividades_saiopen',
        'label': 'Actividades',
        'icon': 'task',
        'description': 'Actividades de proyectos con departamento y centro de costo',
        'group': 'dimensional',
    },
    {
        'key': 'departamentos',
        'label': 'Departamentos',
        'icon': 'business',
        'description': 'Lista de departamentos contables (Saiopen)',
        'group': 'dimensional',
    },
    {
        'key': 'centros_costo',
        'label': 'Centros de Costo',
        'icon': 'center_focus_strong',
        'description': 'Lista de centros de costo contables (Saiopen)',
        'group': 'dimensional',
    },
    {
        'key': 'tipos_documento',
        'label': 'Tipos de Documento',
        'icon': 'description',
        'description': 'Catálogo de tipos de documento de Saiopen',
        'group': 'dimensional',
    },
    {
        'key': 'direcciones_envio',
        'label': 'Direcciones de Envío',
        'icon': 'local_shipping',
        'description': 'Sucursales y direcciones de envío de terceros',
        'group': 'dimensional',
    },
    {
        'key': 'impuestos',
        'label': 'Impuestos',
        'icon': 'percent',
        'description': 'Tarifas de impuesto (IVA, INC, etc.) de Saiopen',
        'group': 'dimensional',
    },
    # Legacy
    {
        'key': 'terceros',
        'label': 'Terceros (SaiSuite)',
        'icon': 'person',
        'description': 'Terceros operativos de SaiSuite (clientes, proveedores y contactos)',
        'group': 'dimensional',
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# Mapa de JOINs entre fuentes (grafo de relaciones)
# ─────────────────────────────────────────────────────────────────────────────
# Las relaciones están almacenadas en la dirección "natural" y se buscan
# en ambas direcciones mediante _get_join_info().
#
# type: 'fk'       → FK Django directa (usar F('fk_field__campo') para forward)
# type: 'subquery' → Subquery + OuterRef (para fuentes sin FK Django)
# join_fields: [(campo_local, campo_remoto), ...]

SOURCE_JOINS_MAP = {
    # ── Transaccional ↔ Transaccional ─────────────────────────────────────
    ('facturacion', 'facturacion_detalle'): {
        'type': 'fk',
        'description': 'Facturación ↔ Detalle de factura',
        'fk_field': 'factura',          # FK field en facturacion_detalle
        'join_fields': [],
    },
    ('gl', 'facturacion'): {
        'type': 'subquery',
        'description': 'GL ↔ Facturación vía tipo + batch=number',
        'join_fields': [
            ('tipo', 'tipo'),
            ('batch', 'number'),
        ],
    },
    ('gl', 'cartera'): {
        'type': 'subquery',
        'description': 'GL ↔ Cartera vía tercero_id + tipo + batch',
        'join_fields': [
            ('tercero_id', 'tercero_id'),
            ('tipo', 'tipo'),
            ('batch', 'batch'),
        ],
    },
    ('facturacion_detalle', 'inventario'): {
        'type': 'subquery',
        'description': 'Detalle factura ↔ Inventario vía item_codigo',
        'join_fields': [('item_codigo', 'item_codigo')],
    },
    # ── Transaccional ↔ Maestro terceros ──────────────────────────────────
    ('facturacion', 'terceros_saiopen'): {
        'type': 'subquery',
        'description': 'Facturación ↔ Tercero Saiopen vía tercero_id',
        'join_fields': [('tercero_id', 'id_n')],
    },
    ('gl', 'terceros_saiopen'): {
        'type': 'subquery',
        'description': 'GL ↔ Tercero Saiopen vía tercero_id',
        'join_fields': [('tercero_id', 'id_n')],
    },
    ('cartera', 'terceros_saiopen'): {
        'type': 'subquery',
        'description': 'Cartera ↔ Tercero Saiopen vía tercero_id',
        'join_fields': [('tercero_id', 'id_n')],
    },
    ('inventario', 'terceros_saiopen'): {
        'type': 'subquery',
        'description': 'Inventario ↔ Tercero Saiopen vía tercero_id',
        'join_fields': [('tercero_id', 'id_n')],
    },
    # ── Transaccional ↔ Productos ─────────────────────────────────────────
    ('facturacion_detalle', 'productos'): {
        'type': 'subquery',
        'description': 'Detalle factura ↔ Productos vía item_codigo',
        'join_fields': [('item_codigo', 'codigo')],
    },
    # ── Detalle factura ↔ Maestros de dimensiones ─────────────────────────
    ('facturacion_detalle', 'proyectos_saiopen'): {
        'type': 'subquery',
        'description': 'Detalle factura ↔ Proyectos vía proyecto_codigo',
        'join_fields': [('proyecto_codigo', 'codigo')],
    },
    ('facturacion_detalle', 'actividades_saiopen'): {
        'type': 'subquery',
        'description': 'Detalle factura ↔ Actividades vía actividad_codigo',
        'join_fields': [('actividad_codigo', 'codigo')],
    },
    ('facturacion_detalle', 'departamentos'): {
        'type': 'subquery',
        'description': 'Detalle factura ↔ Departamentos vía departamento_codigo',
        'join_fields': [('departamento_codigo', 'codigo')],
    },
    ('facturacion_detalle', 'centros_costo'): {
        'type': 'subquery',
        'description': 'Detalle factura ↔ Centros de costo vía centro_costo_codigo',
        'join_fields': [('centro_costo_codigo', 'codigo')],
    },
    ('inventario', 'productos'): {
        'type': 'subquery',
        'description': 'Inventario ↔ Productos vía item_codigo',
        'join_fields': [('item_codigo', 'codigo')],
    },
    # ── GL ↔ Maestros contables ────────────────────────────────────────────
    ('gl', 'cuentas_contables'): {
        'type': 'subquery',
        'description': 'GL ↔ Cuentas contables vía auxiliar',
        'join_fields': [('auxiliar', 'codigo')],
    },
    ('gl', 'proyectos_saiopen'): {
        'type': 'subquery',
        'description': 'GL ↔ Proyectos vía proyecto_codigo',
        'join_fields': [('proyecto_codigo', 'codigo')],
    },
    ('gl', 'actividades_saiopen'): {
        'type': 'subquery',
        'description': 'GL ↔ Actividades vía actividad_codigo',
        'join_fields': [('actividad_codigo', 'codigo')],
    },
    ('gl', 'departamentos'): {
        'type': 'subquery',
        'description': 'GL ↔ Departamentos vía departamento_codigo (tipo=DP)',
        'join_fields': [('departamento_codigo', 'codigo')],
    },
    ('gl', 'centros_costo'): {
        'type': 'subquery',
        'description': 'GL ↔ Centros de costo vía centro_costo_codigo (tipo=CC)',
        'join_fields': [('centro_costo_codigo', 'codigo')],
    },
    # ── Maestros entre sí ─────────────────────────────────────────────────
    ('terceros_saiopen', 'direcciones_envio'): {
        'type': 'subquery',
        'description': 'Tercero Saiopen ↔ Direcciones de envío vía id_n',
        'join_fields': [('id_n', 'id_n')],
    },
    ('productos', 'impuestos'): {
        'type': 'fk',
        'description': 'Productos ↔ Impuesto (FK directa)',
        'fk_field': 'impuesto',
        'join_fields': [],
    },
}

_DEFAULT_PAGE_SIZE = 50
_MAX_PAGE_SIZE = 5000


# ─────────────────────────────────────────────────────────────────────────────
# FilterTranslator — formato v2 de filtros
# ─────────────────────────────────────────────────────────────────────────────

class FilterTranslator:
    """
    Traduce filtros en formato v2 (lista de {source, field, operator, value})
    a operaciones Django ORM (.filter() / .exclude()).

    Operadores soportados por tipo:
    - Texto: eq, neq, contains, startswith, endswith, in
    - Numérico: eq, neq, gt, gte, lt, lte, between, in
    - Fecha: eq, gt, gte, lt, lte, between
    - Booleano: is_true, is_false
    """

    # Retorna (filter_kwargs, exclude_kwargs)
    _OPS = {
        'eq':         lambda f, v: ({f: v}, {}),
        'neq':        lambda f, v: ({}, {f: v}),
        'contains':   lambda f, v: ({f'{f}__icontains': v}, {}),
        'startswith': lambda f, v: ({f'{f}__istartswith': v}, {}),
        'endswith':   lambda f, v: ({f'{f}__iendswith': v}, {}),
        'gt':         lambda f, v: ({f'{f}__gt': v}, {}),
        'gte':        lambda f, v: ({f'{f}__gte': v}, {}),
        'lt':         lambda f, v: ({f'{f}__lt': v}, {}),
        'lte':        lambda f, v: ({f'{f}__lte': v}, {}),
        'between':    lambda f, v: ({f'{f}__gte': v[0], f'{f}__lte': v[1]}, {}),
        'in':         lambda f, v: ({f'{f}__in': v}, {}),
        'is_true':    lambda f, v: ({f: True}, {}),
        'is_false':   lambda f, v: ({f: False}, {}),
    }

    @classmethod
    def translate(cls, operator: str, field: str, value) -> tuple[dict, dict]:
        """
        Traduce un operador + campo + valor a (filter_kwargs, exclude_kwargs).
        Lanza ValidationError si el operador no es válido.
        """
        if operator not in cls._OPS:
            raise ValidationError(f'Operador no soportado: {operator}')
        return cls._OPS[operator](field, value)

    @classmethod
    def apply_to_queryset(
        cls,
        qs: QuerySet,
        filtros: list,
        source: str,
        valid_fields: set,
    ) -> QuerySet:
        """
        Aplica los filtros del nuevo formato al queryset para una fuente específica.
        Solo procesa filtros cuyo 'source' coincida.
        """
        for item in filtros:
            if not isinstance(item, dict):
                continue
            if item.get('source') != source:
                continue
            field = item.get('field', '')
            operator = item.get('operator', 'eq')
            value = item.get('value')

            if not field or value is None or value == '' or value == []:
                continue
            if field not in valid_fields:
                logger.warning('bi_filter_invalid_field', extra={'source': source, 'field': field})
                continue
            if operator not in cls._OPS:
                logger.warning('bi_filter_invalid_operator', extra={'operator': operator})
                continue

            try:
                filter_kw, exclude_kw = cls._OPS[operator](field, value)
                if filter_kw:
                    qs = qs.filter(**filter_kw)
                if exclude_kw:
                    qs = qs.exclude(**exclude_kw)
            except (TypeError, ValueError, KeyError) as exc:
                logger.warning(
                    'bi_filter_error',
                    extra={'field': field, 'operator': operator, 'error': str(exc)},
                )
        return qs


# ─────────────────────────────────────────────────────────────────────────────
# BIQueryEngine
# ─────────────────────────────────────────────────────────────────────────────

class BIQueryEngine:
    """
    Motor BI v2: soporte multi-fuente con JOINs automáticos vía Subquery+OuterRef.
    Soporta dos formatos de filtros:
    - v1 (legacy): dict { key: value }  — retrocompatible
    - v2 (nuevo):  list [{ source, field, operator, value }]
    """

    # ── Helpers de modelo y campos ────────────────────────────────────────

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

    # ── Filtros legacy (v1) ───────────────────────────────────────────────

    def _apply_filters(self, qs: QuerySet, filtros: dict, source: str) -> QuerySet:
        """Aplica filtros en formato dict legacy (v1) al queryset."""
        source_filter_defs = {f['key']: f for f in SOURCE_FILTERS.get(source, [])}
        for key, value in filtros.items():
            if value is None or value == '' or value == []:
                continue
            filter_def = source_filter_defs.get(key)
            if not filter_def:
                continue
            qs = qs.filter(**{filter_def['field']: value})
        return qs

    # ── JOINs multi-fuente ────────────────────────────────────────────────

    def _get_join_info(self, source_a: str, source_b: str) -> dict | None:
        """
        Busca información de join entre dos fuentes en ambas direcciones.
        Retorna el join_info enriquecido con '_direction' y '_from'/'_to'.
        """
        direct = SOURCE_JOINS_MAP.get((source_a, source_b))
        if direct:
            return {**direct, '_direction': 'forward', '_from': source_a, '_to': source_b}
        reverse = SOURCE_JOINS_MAP.get((source_b, source_a))
        if reverse:
            return {**reverse, '_direction': 'reverse', '_from': source_b, '_to': source_a}
        return None

    def _get_reachable_sources(self, primary: str) -> set:
        """Retorna el set de fuentes alcanzables desde la fuente primaria en un salto."""
        reachable = set()
        for (a, b) in SOURCE_JOINS_MAP:
            if a == primary:
                reachable.add(b)
            elif b == primary:
                reachable.add(a)
        return reachable

    def _apply_joins(
        self,
        qs: QuerySet,
        primary_source: str,
        sec_fields_by_source: dict,
        filtros_v2: list,
        company_id,
    ) -> tuple[QuerySet, dict]:
        """
        Anota el queryset principal con campos de fuentes secundarias usando Subquery.

        sec_fields_by_source: {source: [field_name, ...]}
        filtros_v2: filtros en formato v2 (lista)

        Returns:
            (qs_anotado, annotation_map)
            annotation_map: {(source, field_name): annotation_key_en_qs}
        """
        annotation_map: dict[tuple, str] = {}

        for sec_source, sec_fields in sec_fields_by_source.items():
            if not sec_fields:
                continue

            join_info = self._get_join_info(primary_source, sec_source)
            if not join_info:
                logger.warning(
                    'bi_join_not_found',
                    extra={'primary': primary_source, 'secondary': sec_source},
                )
                continue

            sec_model = self._get_model(sec_source)
            if sec_model is None:
                continue

            sec_valid = self._get_valid_fields(sec_source)
            base_filters = SOURCE_BASE_FILTERS.get(sec_source, {})

            for field_name in sec_fields:
                if field_name not in sec_valid:
                    continue

                # Nombre de anotación: prefijo 'sec_' para evitar colisiones con campos nativos
                ann_key = f'sec_{sec_source}_{field_name}'

                # ── FK directa: usar F() para delegar al ORM de Django ──
                if join_info['type'] == 'fk':
                    fk_field = join_info['fk_field']
                    if join_info['_direction'] == 'reverse':
                        # primary=facturacion_detalle → secondary=facturacion
                        # El FK está en facturacion_detalle.factura → acceso directo
                        fk_path = f'{fk_field}__{field_name}'
                        qs = qs.annotate(**{ann_key: F(fk_path)})
                    else:
                        # primary=facturacion → secondary=facturacion_detalle (1:M)
                        # Subquery para obtener el primer detalle (semántica: primer match)
                        sec_qs = sec_model.objects.filter(
                            **{f'{fk_field}_id': OuterRef('pk')},
                            company_id=OuterRef('company_id'),
                        )
                        if filtros_v2:
                            sec_qs = FilterTranslator.apply_to_queryset(
                                sec_qs, filtros_v2, sec_source, sec_valid,
                            )
                        qs = qs.annotate(**{ann_key: Subquery(sec_qs.values(field_name)[:1])})

                # ── FK directa productos→impuestos ─────────────────────
                elif join_info['type'] == 'fk' and sec_source == 'impuestos':
                    fk_field = join_info['fk_field']
                    fk_path = f'{fk_field}__{field_name}'
                    qs = qs.annotate(**{ann_key: F(fk_path)})

                # ── Subquery correlacionado ─────────────────────────────
                else:
                    join_pairs = join_info.get('join_fields', [])
                    sec_qs = sec_model.objects.filter(
                        company_id=OuterRef('company_id'),
                        **base_filters,
                    )
                    for local_f, remote_f in join_pairs:
                        sec_qs = sec_qs.filter(**{remote_f: OuterRef(local_f)})

                    if filtros_v2:
                        sec_qs = FilterTranslator.apply_to_queryset(
                            sec_qs, filtros_v2, sec_source, sec_valid,
                        )

                    qs = qs.annotate(**{ann_key: Subquery(sec_qs.values(field_name)[:1])})

                annotation_map[(sec_source, field_name)] = ann_key

        return qs, annotation_map

    # ── Execute principal ─────────────────────────────────────────────────

    def execute(self, report, company_id) -> dict:
        """
        Ejecuta el reporte y retorna datos formateados.
        Soporta multi-fuente con JOINs automáticos.
        Retorna: {columns: [...], rows: [...], total_count: int}
        """
        if not report.fuentes:
            return {'columns': [], 'rows': [], 'total_count': 0}

        primary_source = report.fuentes[0]
        secondary_sources = report.fuentes[1:] if len(report.fuentes) > 1 else []

        model = self._get_model(primary_source)
        if not model:
            return {'columns': [], 'rows': [], 'total_count': 0}

        primary_valid = self._get_valid_fields(primary_source)
        filtros = report.filtros or {}
        is_new_fmt = isinstance(filtros, list)

        # Base queryset con filtro de tenant obligatorio
        qs = model.objects.filter(company_id=company_id)

        # Aplicar filtros del primary source
        if is_new_fmt:
            qs = FilterTranslator.apply_to_queryset(qs, filtros, primary_source, primary_valid)
        else:
            qs = self._apply_filters(qs, filtros, primary_source)

        # ── Multi-fuente: resolver anotaciones para campos secundarios ──
        annotation_map: dict[tuple, str] = {}
        if secondary_sources:
            sec_fields_by_source: dict[str, list] = {}
            for campo in (report.campos_config or []):
                src = campo.get('source', primary_source)
                fld = campo.get('field', '')
                if src in secondary_sources and fld and not campo.get('is_calculated'):
                    sec_fields_by_source.setdefault(src, [])
                    if fld not in sec_fields_by_source[src]:
                        sec_fields_by_source[src].append(fld)

            # Incluir también campos referenciados en filtros secundarios aunque no
            # estén en campos_config — necesarios para aplicar el HAVING correctamente.
            for item in (filtros if is_new_fmt else []):
                if not isinstance(item, dict):
                    continue
                src = item.get('source', '')
                fld = item.get('field', '')
                if src in secondary_sources and fld:
                    sec_fields_by_source.setdefault(src, [])
                    if fld not in sec_fields_by_source[src]:
                        sec_fields_by_source[src].append(fld)

            if sec_fields_by_source:
                qs, annotation_map = self._apply_joins(
                    qs,
                    primary_source,
                    sec_fields_by_source,
                    filtros if is_new_fmt else [],
                    company_id,
                )

        # ── Construir dimensiones, métricas y calculados ──────────────────
        dimensions: list[str] = []
        metrics: list[dict] = []
        calc_fields_table: list[dict] = []
        field_to_alias: dict[str, str] = {}
        columns: list[dict] = []

        for campo in (report.campos_config or []):
            src = campo.get('source', primary_source)
            field_name = campo.get('field', '')
            label = campo.get('label', field_name)

            # Campo calculado (cross-source)
            if campo.get('is_calculated'):
                formula = campo.get('formula', '')
                if field_name and formula:
                    calc_fields_table.append({
                        'field_alias': field_name,
                        'formula': formula,
                        'label': label,
                    })
                    columns.append({'field': field_name, 'label': label, 'type': 'metric'})
                continue

            # Resolver nombre de campo en el queryset
            if src == primary_source:
                if field_name not in primary_valid:
                    continue
                resolved = field_name
            else:
                resolved = annotation_map.get((src, field_name))
                if not resolved:
                    continue  # fuente secundaria sin join disponible

            role = campo.get('role', 'dimension')
            if role == 'metric':
                agg = campo.get('aggregation', 'SUM').upper()
                if agg not in _AGGREGATION_MAP:
                    agg = 'SUM'
                # Alias único: incluye source para multi-fuente
                if src == primary_source:
                    alias = f'{field_name}_{agg.lower()}'
                else:
                    alias = f'{src}_{field_name}_{agg.lower()}'
                metrics.append({
                    'field': resolved,
                    'aggregation': agg,
                    'label': label,
                    'alias': alias,
                })
                field_to_alias[field_name] = alias
                columns.append({'field': alias, 'label': label, 'type': 'metric'})
            else:
                dimensions.append(resolved)
                # Para el frontend, exponer el nombre de la anotación como 'field'
                columns.append({'field': resolved, 'label': label, 'type': 'dimension'})

        if not dimensions and not metrics and not calc_fields_table:
            return {'columns': [], 'rows': [], 'total_count': 0}

        # ── GROUP BY + aggregation ─────────────────────────────────────────
        if metrics and dimensions:
            qs = qs.values(*dimensions)
            annotations = {}
            for m in metrics:
                annotations[m['alias']] = _AGGREGATION_MAP[m['aggregation']](m['field'])
            qs = qs.annotate(**annotations)

        elif metrics and not dimensions:
            # Solo métricas sin dimensiones → una fila de totales
            annotations = {}
            for m in metrics:
                annotations[m['alias']] = _AGGREGATION_MAP[m['aggregation']](m['field'])
            result = qs.aggregate(**annotations)
            row = {k: float(v) if v is not None else 0 for k, v in result.items()}
            if calc_fields_table:
                ctx = {f: row.get(a, 0) for f, a in field_to_alias.items()}
                for cf in calc_fields_table:
                    row[cf['field_alias']] = _safe_eval_formula(cf['formula'], ctx) or 0
            return {'columns': columns, 'rows': [row], 'total_count': 1}

        else:
            # Solo dimensiones, sin agregación
            qs = qs.values(*dimensions)

        # ── Filtros de fuentes secundarias como HAVING/WHERE post-join ────
        # Los filtros de fuentes secundarias se aplican sobre el queryset ya
        # agrupado/anotado porque actúan sobre el valor agregado (HAVING) o
        # sobre la anotación sec_* (WHERE en la anotación externa).
        if is_new_fmt:
            for item in filtros:
                if not isinstance(item, dict):
                    continue
                src = item.get('source')
                if not src or src == primary_source:
                    continue  # los de la fuente primaria ya se aplicaron antes
                field = item.get('field', '')
                operator = item.get('operator', 'eq')
                value = item.get('value')
                if not field or value is None or value == '':
                    continue
                # Preferir alias de métrica (HAVING), si no existe usar clave de anotación (WHERE)
                filter_field = field_to_alias.get(field) or annotation_map.get((src, field))
                if not filter_field:
                    continue
                # Convertir a Decimal para comparaciones numéricas seguras
                try:
                    coerced = Decimal(str(value)) if not isinstance(value, (list, bool)) else value
                except Exception:
                    coerced = value
                try:
                    filter_kw, exclude_kw = FilterTranslator.translate(operator, filter_field, coerced)
                    if filter_kw:
                        qs = qs.filter(**filter_kw)
                    if exclude_kw:
                        qs = qs.exclude(**exclude_kw)
                except Exception as exc:
                    logger.warning(
                        'bi_sec_filter_error',
                        extra={'field': filter_field, 'operator': operator, 'error': str(exc)},
                    )

        # ── Ordenamiento ───────────────────────────────────────────────────
        valid_order = {c['field'] for c in columns}
        order_fields: list[str] = []
        for o in (report.orden_config or []):
            fld = o.get('field', '')
            direction = o.get('direction', 'asc')
            if fld in valid_order:
                order_fields.append(f'-{fld}' if direction == 'desc' else fld)
        if order_fields:
            qs = qs.order_by(*order_fields)

        # Total antes de limitar
        total_count = qs.count()

        # ── Límite de registros ───────────────────────────────────────────
        # En vista previa el frontend envía limite_registros=30.
        # En el visor (reporte guardado) limite_registros es null → devolver todos (_MAX_PAGE_SIZE).
        limit = report.limite_registros if report.limite_registros else _MAX_PAGE_SIZE
        limit = min(limit, _MAX_PAGE_SIZE)
        rows = list(qs[:limit])

        # ── Normalizar Decimals ───────────────────────────────────────────
        for row in rows:
            for key, val in list(row.items()):
                if isinstance(val, Decimal):
                    row[key] = _normalize_dim_value(val)

        # ── Campos calculados ─────────────────────────────────────────────
        if calc_fields_table:
            for row in rows:
                ctx = {f: float(row.get(a) or 0) for f, a in field_to_alias.items()}
                for cf in calc_fields_table:
                    row[cf['field_alias']] = _safe_eval_formula(cf['formula'], ctx) or 0

        return {
            'columns': columns,
            'rows': rows,
            'total_count': total_count,
        }

    # ── Execute pivot ─────────────────────────────────────────────────────

    def execute_pivot(self, report, company_id) -> dict:
        """
        Ejecuta un reporte en modo pivot table. Soporta multi-fuente.
        viz_config debe tener: {rows: [...], columns: [...], values: [...]}
        Retorna: {row_headers, col_headers, data, row_totals, col_totals, grand_total}
        """
        if not report.fuentes:
            return self._empty_pivot()

        primary_source = report.fuentes[0]
        secondary_sources = report.fuentes[1:] if len(report.fuentes) > 1 else []

        model = self._get_model(primary_source)
        if not model:
            return self._empty_pivot()

        primary_valid = self._get_valid_fields(primary_source)
        viz = report.viz_config or {}
        filtros = report.filtros or {}
        is_new_fmt = isinstance(filtros, list)

        # Base queryset
        qs = model.objects.filter(company_id=company_id)
        if is_new_fmt:
            qs = FilterTranslator.apply_to_queryset(qs, filtros, primary_source, primary_valid)
        else:
            qs = self._apply_filters(qs, filtros, primary_source)

        # ── Resolución de campos de fuentes secundarias en viz_config ──
        annotation_map: dict[tuple, str] = {}
        if secondary_sources:
            # Recopilar todos los campos de fuentes secundarias mencionados en viz_config
            all_viz_fields = (
                (viz.get('rows') or [])
                + (viz.get('columns') or [])
                + [vc.get('field', '') for vc in (viz.get('values') or []) if not vc.get('is_calculated')]
            )
            sec_fields_by_source: dict[str, list] = {}
            for campo_entry in (report.campos_config or []):
                src = campo_entry.get('source', primary_source)
                fld = campo_entry.get('field', '')
                if src in secondary_sources and fld in all_viz_fields:
                    sec_fields_by_source.setdefault(src, [])
                    if fld not in sec_fields_by_source[src]:
                        sec_fields_by_source[src].append(fld)

            # Incluir campos de filtros secundarios aunque no estén en viz_config
            for item in (filtros if is_new_fmt else []):
                if not isinstance(item, dict):
                    continue
                src = item.get('source', '')
                fld = item.get('field', '')
                if src in secondary_sources and fld:
                    sec_fields_by_source.setdefault(src, [])
                    if fld not in sec_fields_by_source[src]:
                        sec_fields_by_source[src].append(fld)

            if sec_fields_by_source:
                qs, annotation_map = self._apply_joins(
                    qs, primary_source, sec_fields_by_source,
                    filtros if is_new_fmt else [], company_id,
                )

        # ── Resolver campos pivot a nombres en el queryset ────────────────
        def _resolve(fld: str, src: str = primary_source) -> str | None:
            """Retorna el nombre de campo/anotación para usar en el queryset."""
            if src == primary_source:
                return fld if fld in primary_valid else None
            return annotation_map.get((src, fld))

        # campo_source para métricas (last-wins está bien, los nombres de métrica no suelen repetirse)
        campo_source = {}
        for ce in (report.campos_config or []):
            campo_source[ce.get('field', '')] = ce.get('source', primary_source)

        # Para dimensiones (filas/columnas) usamos una cola FIFO por campo.
        # Si el mismo campo existe en dos fuentes, la primera aparición usa la fuente primaria
        # y la segunda usa la secundaria (sec_*), preservando AMBAS dimensiones.
        _dim_srcs: dict[str, list] = {}
        for ce in (report.campos_config or []):
            fld = ce.get('field', '')
            src = ce.get('source', primary_source)
            _dim_srcs.setdefault(fld, []).append(src)

        row_fields_raw = viz.get('rows') or []
        col_fields_raw = viz.get('columns') or []
        value_configs = viz.get('values') or []

        _row_srcs = {k: list(v) for k, v in _dim_srcs.items()}
        _seen_row: set = set()
        row_fields = []
        for f in row_fields_raw:
            srcs = _row_srcs.get(f, [])
            src = srcs.pop(0) if srcs else primary_source
            r = _resolve(f, src)
            if r and r not in _seen_row:
                _seen_row.add(r)
                row_fields.append(r)

        _col_srcs = {k: list(v) for k, v in _dim_srcs.items()}
        _seen_col: set = set()
        col_fields = []
        for f in col_fields_raw:
            srcs = _col_srcs.get(f, [])
            src = srcs.pop(0) if srcs else primary_source
            r = _resolve(f, src)
            if r and r not in _seen_col:
                _seen_col.add(r)
                col_fields.append(r)

        if not row_fields or not value_configs:
            return self._empty_pivot()

        # Agrupar por filas + columnas
        group_fields = row_fields + col_fields
        qs = qs.values(*group_fields)

        # Separar métricas normales de calculadas
        annotations: dict[str, object] = {}
        calc_fields: list[dict] = []
        field_to_alias: dict[str, str] = {}

        for vc in value_configs:
            field = vc.get('field', '')
            src = campo_source.get(field, primary_source)
            if vc.get('is_calculated'):
                formula = vc.get('formula', '')
                if field and formula:
                    calc_fields.append({'alias': field, 'formula': formula})
            else:
                agg = vc.get('aggregation', 'SUM').upper()
                resolved = _resolve(field, src)
                if resolved and agg in _AGGREGATION_MAP:
                    alias = f'{field}_{agg.lower()}'
                    annotations[alias] = _AGGREGATION_MAP[agg](resolved)
                    field_to_alias[field] = alias

        if not annotations and not calc_fields:
            return self._empty_pivot()

        qs = qs.annotate(**annotations)

        # ── Filtros de fuentes secundarias como HAVING post-GROUP BY ──────
        filtros_pivot = report.filtros or []
        if isinstance(filtros_pivot, list):
            for item in filtros_pivot:
                if not isinstance(item, dict):
                    continue
                src = item.get('source')
                if not src or src == primary_source:
                    continue
                field = item.get('field', '')
                operator = item.get('operator', 'eq')
                value = item.get('value')
                if not field or value is None or value == '':
                    continue
                filter_field = field_to_alias.get(field) or annotation_map.get((src, field))
                if not filter_field:
                    continue
                try:
                    coerced = Decimal(str(value)) if not isinstance(value, (list, bool)) else value
                except Exception:
                    coerced = value
                try:
                    filter_kw, exclude_kw = FilterTranslator.translate(operator, filter_field, coerced)
                    if filter_kw:
                        qs = qs.filter(**filter_kw)
                    if exclude_kw:
                        qs = qs.exclude(**exclude_kw)
                except Exception as exc:
                    logger.warning(
                        'bi_sec_filter_pivot_error',
                        extra={'field': filter_field, 'operator': operator, 'error': str(exc)},
                    )

        # ── Límite de registros para pivot ────────────────────────────────
        # En vista previa (limite_registros=30) limita filas agrupadas.
        # En el visor (limite_registros=null) devuelve hasta _MAX_PAGE_SIZE.
        pivot_limit = report.limite_registros if report.limite_registros else _MAX_PAGE_SIZE
        pivot_limit = min(pivot_limit, _MAX_PAGE_SIZE)
        data_rows = list(qs[:pivot_limit])

        # ── Construir estructura de pivot ─────────────────────────────────
        row_keys: OrderedDict = OrderedDict()
        col_keys: OrderedDict = OrderedDict()
        cells: dict = {}
        no_col = not col_fields

        for row in data_rows:
            rk = tuple(_normalize_dim_value(row.get(f)) for f in row_fields)
            ck = (
                tuple(_normalize_dim_value(row.get(f)) for f in col_fields)
                if col_fields else ('Total',)
            )
            rk_str = '|'.join('' if v is None else str(v) for v in rk)
            ck_str = '|'.join('' if v is None else str(v) for v in ck)

            if rk_str not in row_keys:
                row_keys[rk_str] = {f: _normalize_dim_value(row.get(f)) for f in row_fields}
            if ck_str not in col_keys:
                col_keys[ck_str] = (
                    {f: _normalize_dim_value(row.get(f)) for f in col_fields}
                    if col_fields else {'_total': 'Total'}
                )

            cell_values: dict = {}
            for alias in annotations:
                val = row.get(alias)
                cell_values[alias] = float(val) if isinstance(val, Decimal) else (val or 0)

            ctx = {f: cell_values.get(a, 0) for f, a in field_to_alias.items()}
            for cf in calc_fields:
                cell_values[cf['alias']] = _safe_eval_formula(cf['formula'], ctx) or 0

            cells[f'{rk_str}___{ck_str}'] = cell_values

        # ── Totales ────────────────────────────────────────────────────────
        row_totals: dict = {}
        col_totals: dict = {}
        grand_total: dict = {alias: 0 for alias in annotations}

        for rk_str in row_keys:
            row_totals[rk_str] = {alias: 0 for alias in annotations}
            for ck_str in col_keys:
                cell = cells.get(f'{rk_str}___{ck_str}', {})
                for alias in annotations:
                    row_totals[rk_str][alias] += cell.get(alias, 0)
            ctx = {f: row_totals[rk_str].get(a, 0) for f, a in field_to_alias.items()}
            for cf in calc_fields:
                row_totals[rk_str][cf['alias']] = _safe_eval_formula(cf['formula'], ctx) or 0

        for ck_str in col_keys:
            col_totals[ck_str] = {alias: 0 for alias in annotations}
            for rk_str in row_keys:
                cell = cells.get(f'{rk_str}___{ck_str}', {})
                for alias in annotations:
                    val = cell.get(alias, 0)
                    col_totals[ck_str][alias] += val
                    grand_total[alias] += val
            ctx = {f: col_totals[ck_str].get(a, 0) for f, a in field_to_alias.items()}
            for cf in calc_fields:
                col_totals[ck_str][cf['alias']] = _safe_eval_formula(cf['formula'], ctx) or 0

        ctx_grand = {f: grand_total.get(a, 0) for f, a in field_to_alias.items()}
        for cf in calc_fields:
            grand_total[cf['alias']] = _safe_eval_formula(cf['formula'], ctx_grand) or 0

        # Etiquetas de métricas
        value_labels: dict = {}
        for campo in (report.campos_config or []):
            if campo.get('role') == 'metric':
                if campo.get('is_calculated'):
                    alias = campo.get('field', '')
                else:
                    fn = campo.get('field', '')
                    agg = (campo.get('aggregation') or 'SUM').upper()
                    alias = f'{fn}_{agg.lower()}'
                value_labels[alias] = campo.get('label', alias)

        all_aliases = list(annotations.keys()) + [cf['alias'] for cf in calc_fields]

        return {
            'row_headers': list(row_keys.values()),
            'col_headers': list(col_keys.values()),
            'data': cells,
            'row_totals': row_totals,
            'col_totals': col_totals,
            'grand_total': grand_total,
            'value_aliases': all_aliases,
            'no_column_mode': no_col,
            'value_labels': value_labels,
        }

    # ── Metadata endpoints ────────────────────────────────────────────────

    def get_available_sources(self) -> list:
        """Retorna metadatos de todas las fuentes disponibles."""
        return SOURCE_META

    def get_available_fields(self, source: str) -> dict:
        """Retorna campos disponibles organizados por categoría para una fuente."""
        return SOURCE_FIELDS.get(source, {})

    def get_available_filters(self, source: str) -> list:
        """Retorna filtros legacy aplicables a una fuente."""
        return SOURCE_FILTERS.get(source, [])

    def get_joins_map(self) -> list:
        """
        Retorna el mapa de relaciones disponibles entre fuentes.
        Usado por el frontend para mostrar el indicador de relaciones.
        """
        result = []
        for (src_a, src_b), info in SOURCE_JOINS_MAP.items():
            result.append({
                'source_a': src_a,
                'source_b': src_b,
                'description': info.get('description', ''),
                'type': info['type'],
                'join_fields': info.get('join_fields', []),
            })
        return result

    def get_reachable_from(self, source: str) -> list[str]:
        """Retorna las fuentes alcanzables en un salto desde la fuente dada."""
        return sorted(self._get_reachable_sources(source))

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
            'no_column_mode': False,
            'value_labels': {},
        }
