"""
SaiSuite -- Dashboard: Report Engine
Motor de reportes financieros. Calcula datos para cada tipo de tarjeta.

Cada metodo retorna: {labels: [], datasets: [], summary: {}}
Diseñado para ser consumido por graficos frontend (Chart.js / ngx-charts).
"""
import logging
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum, Q, F, Value, CharField
from django.db.models.functions import Coalesce

from apps.contabilidad.models import MovimientoContable

logger = logging.getLogger(__name__)

# Constantes PUC colombiano
_TITULO_ACTIVO = 1
_TITULO_PASIVO = 2
_TITULO_PATRIMONIO = 3
_TITULO_INGRESOS = 4
_TITULO_GASTOS = 5
_TITULO_COSTOS = 6

# CxC: subcuentas 1305xx (clientes nacionales)
_CXC_GRUPO = 13

# CxP: subcuentas 22xx (proveedores)
_CXP_GRUPO = 22

_ZERO = Decimal('0.00')


def _to_decimal(val) -> Decimal:
    """Convierte un valor a Decimal de forma segura."""
    if val is None:
        return _ZERO
    return Decimal(str(val)).quantize(Decimal('0.01'))


class ReportEngine:
    """Motor de reportes financieros para dashboards."""

    def get_card_data(
        self,
        company_id,
        card_type_code: str,
        filtros: dict,
        card_config: dict | None = None,
    ) -> dict:
        """
        Dispatcher principal. Llama al metodo correspondiente al card_type_code.

        Args:
            company_id: UUID de la empresa
            card_type_code: Codigo del tipo de tarjeta (ej: BALANCE_GENERAL)
            filtros: dict con fecha_desde, fecha_hasta, tercero_ids, etc.
            card_config: dict con configuracion especifica de la tarjeta
                         (para CUSTOM_RANGO_CUENTAS y DISTRIBUCION_POR_PROYECTO)

        Returns:
            dict con {labels, datasets, summary}
        """
        # Tarjetas con configuracion especifica (card_config requerido)
        if card_type_code in ('CUSTOM_RANGO_CUENTAS', 'DISTRIBUCION_POR_PROYECTO', 'MOVIMIENTO_POR_TERCERO'):
            return self._dispatch_config_card(
                company_id, card_type_code, filtros, card_config or {}
            )

        method_map = {
            'BALANCE_GENERAL': self.balance_general,
            'ESTADO_RESULTADOS': self.estado_resultados,
            'INDICADORES_LIQUIDEZ': self.indicadores_liquidez,
            'EBITDA': self.ebitda,
            'INGRESOS_VS_EGRESOS': self.ingresos_vs_egresos,
            'ROE_ROA': self.roe_roa,
            'ENDEUDAMIENTO': self.endeudamiento,
            'COSTO_VENTAS': self.costo_ventas,
            'MARGEN_BRUTO_NETO': self.margen_bruto_neto,
            'GASTOS_OPERACIONALES': self.gastos_operacionales,
            'GASTOS_POR_DEPARTAMENTO': self.gastos_por_departamento,
            'GASTOS_POR_CENTRO_COSTO': self.gastos_por_centro_costo,
            'CARTERA_TOTAL': self.cartera_total,
            'AGING_CARTERA': self.aging_cartera,
            'TOP_CLIENTES_SALDO': self.top_clientes_saldo,
            'MOVIMIENTO_POR_TERCERO': self.movimiento_por_tercero,
            'CUENTAS_POR_PAGAR': self.cuentas_por_pagar,
            'AGING_PROVEEDORES': self.aging_proveedores,
            'TOP_PROVEEDORES': self.top_proveedores,
            'COSTO_POR_PROYECTO': self.costo_por_proyecto,
            'COSTO_POR_ACTIVIDAD': self.costo_por_actividad,
            'COMPARATIVO_PERIODOS': self.comparativo_periodos,
            'TENDENCIA_MENSUAL': self.tendencia_mensual,
            # Nuevas tarjetas
            'INGRESOS_POR_PROYECTO': self.ingresos_por_proyecto,
            'GASTOS_ACTIVIDAD_PROYECTO': self.gastos_actividad_proyecto,
            'FLUJO_CAJA_OPERACIONAL': self.flujo_caja_operacional,
            'ROTACION_CARTERA': self.rotacion_cartera,
            'ROTACION_PROVEEDORES': self.rotacion_proveedores,
            'CONCENTRACION_INGRESOS_TERCERO': self.concentracion_ingresos_tercero,
            'DEUDA_PATRIMONIO_MENSUAL': self.deuda_patrimonio_mensual,
        }

        method = method_map.get(card_type_code)
        if not method:
            logger.warning(
                'card_type_not_found',
                extra={'card_type_code': card_type_code},
            )
            return {'labels': [], 'datasets': [], 'summary': {}}

        return method(company_id, filtros)

    def _get_queryset_base(self, company_id, filtros: dict):
        """
        Base queryset filtrado por company y filtros comunes.

        Filtros soportados:
        - fecha_desde: date
        - fecha_hasta: date
        - periodo: str (YYYY-MM)
        - tercero_ids: list[str]
        - proyecto_codigos: list[str]
        - departamento_codigos: list[int]
        - centro_costo_codigos: list[int]
        """
        qs = MovimientoContable.objects.filter(company_id=company_id)

        fecha_desde = filtros.get('fecha_desde')
        fecha_hasta = filtros.get('fecha_hasta')
        periodo = filtros.get('periodo')
        tercero_ids = filtros.get('tercero_ids')
        proyecto_codigos = filtros.get('proyecto_codigos')
        departamento_codigos = filtros.get('departamento_codigos')
        centro_costo_codigos = filtros.get('centro_costo_codigos')

        if fecha_desde:
            qs = qs.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha__lte=fecha_hasta)
        if periodo:
            if len(str(periodo)) == 4:  # año solo "YYYY" → match todos los meses
                qs = qs.filter(periodo__startswith=periodo)
            else:
                qs = qs.filter(periodo=periodo)
        if tercero_ids:
            qs = qs.filter(tercero_id__in=tercero_ids)
        if proyecto_codigos:
            qs = qs.filter(proyecto_codigo__in=proyecto_codigos)
        if departamento_codigos:
            qs = qs.filter(departamento_codigo__in=departamento_codigos)
        if centro_costo_codigos:
            qs = qs.filter(centro_costo_codigo__in=centro_costo_codigos)

        return qs

    def _sum_by_titulo(self, qs, titulo_codigo: int) -> dict:
        """Suma debitos y creditos para un titulo PUC."""
        result = qs.filter(titulo_codigo=titulo_codigo).aggregate(
            total_debito=Coalesce(Sum('debito'), _ZERO),
            total_credito=Coalesce(Sum('credito'), _ZERO),
        )
        return {
            'debito': _to_decimal(result['total_debito']),
            'credito': _to_decimal(result['total_credito']),
        }

    def _saldo_titulo(self, qs, titulo_codigo: int) -> Decimal:
        """
        Calcula saldo neto de un titulo PUC.
        Activo (1): saldo = debito - credito (naturaleza deudora)
        Pasivo (2), Patrimonio (3): saldo = credito - debito (naturaleza acreedora)
        Ingresos (4): saldo = credito - debito (naturaleza acreedora)
        Gastos (5), Costos (6): saldo = debito - credito (naturaleza deudora)
        """
        sums = self._sum_by_titulo(qs, titulo_codigo)
        if titulo_codigo in (_TITULO_ACTIVO, _TITULO_GASTOS, _TITULO_COSTOS):
            return sums['debito'] - sums['credito']
        return sums['credito'] - sums['debito']

    # ──────────────────────────────────────────────
    # Estados Financieros
    # ──────────────────────────────────────────────

    def balance_general(self, company_id, filtros: dict) -> dict:
        """
        Balance General: Activo = Pasivo + Patrimonio.
        Agrupa por titulo_codigo (niveles 1, 2, 3).
        """
        qs = self._get_queryset_base(company_id, filtros)

        activo = self._saldo_titulo(qs, _TITULO_ACTIVO)
        pasivo = self._saldo_titulo(qs, _TITULO_PASIVO)
        patrimonio = self._saldo_titulo(qs, _TITULO_PATRIMONIO)

        return {
            'labels': ['Activo', 'Pasivo', 'Patrimonio'],
            'datasets': [
                {
                    'label': 'Balance General',
                    'data': [str(activo), str(pasivo), str(patrimonio)],
                },
            ],
            'summary': {
                'activo': str(activo),
                'pasivo': str(pasivo),
                'patrimonio': str(patrimonio),
                'ecuacion_cumple': str(activo == pasivo + patrimonio),
            },
        }

    def estado_resultados(self, company_id, filtros: dict) -> dict:
        """
        Estado de Resultados: Ingresos(4) - Costos(6) - Gastos(5) = Utilidad.
        Si filtros.agrupar_por_mes=True, retorna serie mensual.
        """
        if filtros.get('agrupar_por_mes'):
            return self._estado_resultados_mensual(company_id, filtros)

        qs = self._get_queryset_base(company_id, filtros)

        ingresos = self._saldo_titulo(qs, _TITULO_INGRESOS)
        costos = self._saldo_titulo(qs, _TITULO_COSTOS)
        gastos = self._saldo_titulo(qs, _TITULO_GASTOS)
        utilidad_bruta = ingresos - costos
        utilidad_neta = utilidad_bruta - gastos

        return {
            'labels': ['Ingresos', 'Costos', 'Utilidad Bruta', 'Gastos', 'Utilidad Neta'],
            'datasets': [
                {
                    'label': 'Estado de Resultados',
                    'data': [
                        str(ingresos), str(-costos),
                        str(utilidad_bruta), str(-gastos),
                        str(utilidad_neta),
                    ],
                },
            ],
            'summary': {
                'ingresos': str(ingresos),
                'costos': str(costos),
                'gastos': str(gastos),
                'utilidad_bruta': str(utilidad_bruta),
                'utilidad_neta': str(utilidad_neta),
            },
        }

    def indicadores_liquidez(self, company_id, filtros: dict) -> dict:
        """
        Indicadores de Liquidez:
        - Razon corriente = Activo corriente / Pasivo corriente
        - Prueba acida = (Activo corriente - Inventarios) / Pasivo corriente
        - Capital de trabajo = Activo corriente - Pasivo corriente
        """
        qs = self._get_queryset_base(company_id, filtros)

        # Activo corriente: grupo 11 (disponible) + 12 (inversiones CP) + 13 (deudores)
        # + 14 (inventarios)
        activo_corriente_qs = qs.filter(
            titulo_codigo=_TITULO_ACTIVO,
            grupo_codigo__in=[11, 12, 13, 14],
        )
        ac_sums = activo_corriente_qs.aggregate(
            total_debito=Coalesce(Sum('debito'), _ZERO),
            total_credito=Coalesce(Sum('credito'), _ZERO),
        )
        activo_corriente = _to_decimal(ac_sums['total_debito']) - _to_decimal(ac_sums['total_credito'])

        # Inventarios: grupo 14
        inv_qs = qs.filter(titulo_codigo=_TITULO_ACTIVO, grupo_codigo=14)
        inv_sums = inv_qs.aggregate(
            total_debito=Coalesce(Sum('debito'), _ZERO),
            total_credito=Coalesce(Sum('credito'), _ZERO),
        )
        inventarios = _to_decimal(inv_sums['total_debito']) - _to_decimal(inv_sums['total_credito'])

        # Pasivo corriente: grupo 21 (obligaciones financieras CP) + 22 (proveedores)
        # + 23 (cuentas por pagar CP) + 24 (impuestos)
        pasivo_corriente_qs = qs.filter(
            titulo_codigo=_TITULO_PASIVO,
            grupo_codigo__in=[21, 22, 23, 24],
        )
        pc_sums = pasivo_corriente_qs.aggregate(
            total_debito=Coalesce(Sum('debito'), _ZERO),
            total_credito=Coalesce(Sum('credito'), _ZERO),
        )
        pasivo_corriente = _to_decimal(pc_sums['total_credito']) - _to_decimal(pc_sums['total_debito'])

        razon_corriente = _ZERO
        prueba_acida = _ZERO
        if pasivo_corriente > _ZERO:
            razon_corriente = (activo_corriente / pasivo_corriente).quantize(Decimal('0.01'))
            prueba_acida = ((activo_corriente - inventarios) / pasivo_corriente).quantize(Decimal('0.01'))

        capital_trabajo = activo_corriente - pasivo_corriente

        return {
            'labels': ['Razon Corriente', 'Prueba Acida', 'Capital de Trabajo'],
            'datasets': [
                {
                    'label': 'Indicadores de Liquidez',
                    'data': [str(razon_corriente), str(prueba_acida), str(capital_trabajo)],
                },
            ],
            'summary': {
                'razon_corriente': str(razon_corriente),
                'prueba_acida': str(prueba_acida),
                'capital_trabajo': str(capital_trabajo),
                'activo_corriente': str(activo_corriente),
                'pasivo_corriente': str(pasivo_corriente),
                'inventarios': str(inventarios),
            },
        }

    def ebitda(self, company_id, filtros: dict) -> dict:
        """
        EBITDA = Utilidad Operacional + Depreciacion + Amortizacion.
        Aproximacion: Ingresos - Costos - Gastos (sin filtrar D&A por ahora).
        """
        if filtros.get('agrupar_por_mes'):
            return self._ebitda_mensual(company_id, filtros)

        qs = self._get_queryset_base(company_id, filtros)

        ingresos = self._saldo_titulo(qs, _TITULO_INGRESOS)
        costos = self._saldo_titulo(qs, _TITULO_COSTOS)
        gastos = self._saldo_titulo(qs, _TITULO_GASTOS)
        utilidad_operacional = ingresos - costos - gastos

        # Depreciacion y amortizacion: cuentas 5260 (depreciacion gastos) y 5265 (amortizacion)
        da_qs = qs.filter(
            titulo_codigo=_TITULO_GASTOS,
            cuenta_codigo__in=[5260, 5265],
        )
        da_sums = da_qs.aggregate(
            total_debito=Coalesce(Sum('debito'), _ZERO),
            total_credito=Coalesce(Sum('credito'), _ZERO),
        )
        depreciacion_amortizacion = _to_decimal(da_sums['total_debito']) - _to_decimal(da_sums['total_credito'])

        ebitda_val = utilidad_operacional + depreciacion_amortizacion

        return {
            'labels': ['EBITDA'],
            'datasets': [
                {
                    'label': 'EBITDA',
                    'data': [str(ebitda_val)],
                },
            ],
            'summary': {
                'ebitda': str(ebitda_val),
                'utilidad_operacional': str(utilidad_operacional),
                'depreciacion_amortizacion': str(depreciacion_amortizacion),
            },
        }

    def ingresos_vs_egresos(self, company_id, filtros: dict) -> dict:
        """Ingresos vs Egresos (Costos + Gastos)."""
        if filtros.get('agrupar_por_mes'):
            return self._ingresos_vs_egresos_mensual(company_id, filtros)

        qs = self._get_queryset_base(company_id, filtros)

        ingresos = self._saldo_titulo(qs, _TITULO_INGRESOS)
        costos = self._saldo_titulo(qs, _TITULO_COSTOS)
        gastos = self._saldo_titulo(qs, _TITULO_GASTOS)
        egresos = costos + gastos
        diferencia = ingresos - egresos

        return {
            'labels': ['Ingresos', 'Egresos'],
            'datasets': [
                {
                    'label': 'Ingresos vs Egresos',
                    'data': [str(ingresos), str(egresos)],
                },
            ],
            'summary': {
                'ingresos': str(ingresos),
                'egresos': str(egresos),
                'diferencia': str(diferencia),
            },
        }

    def roe_roa(self, company_id, filtros: dict) -> dict:
        """
        ROE = Utilidad Neta / Patrimonio
        ROA = Utilidad Neta / Activo Total
        """
        qs = self._get_queryset_base(company_id, filtros)

        ingresos = self._saldo_titulo(qs, _TITULO_INGRESOS)
        costos = self._saldo_titulo(qs, _TITULO_COSTOS)
        gastos = self._saldo_titulo(qs, _TITULO_GASTOS)
        utilidad_neta = ingresos - costos - gastos

        activo = self._saldo_titulo(qs, _TITULO_ACTIVO)
        patrimonio = self._saldo_titulo(qs, _TITULO_PATRIMONIO)

        roe = _ZERO
        roa = _ZERO
        if patrimonio != _ZERO:
            roe = ((utilidad_neta / patrimonio) * 100).quantize(Decimal('0.01'))
        if activo != _ZERO:
            roa = ((utilidad_neta / activo) * 100).quantize(Decimal('0.01'))

        return {
            'labels': ['ROE (%)', 'ROA (%)'],
            'datasets': [
                {
                    'label': 'ROE / ROA',
                    'data': [str(roe), str(roa)],
                },
            ],
            'summary': {
                'roe': str(roe),
                'roa': str(roa),
                'utilidad_neta': str(utilidad_neta),
                'patrimonio': str(patrimonio),
                'activo_total': str(activo),
            },
        }

    def endeudamiento(self, company_id, filtros: dict) -> dict:
        """
        Nivel de endeudamiento = Pasivo Total / Activo Total
        Concentracion CP = Pasivo Corriente / Pasivo Total
        """
        qs = self._get_queryset_base(company_id, filtros)

        activo = self._saldo_titulo(qs, _TITULO_ACTIVO)
        pasivo = self._saldo_titulo(qs, _TITULO_PASIVO)

        # Pasivo corriente
        pc_qs = qs.filter(
            titulo_codigo=_TITULO_PASIVO,
            grupo_codigo__in=[21, 22, 23, 24],
        )
        pc_sums = pc_qs.aggregate(
            total_debito=Coalesce(Sum('debito'), _ZERO),
            total_credito=Coalesce(Sum('credito'), _ZERO),
        )
        pasivo_corriente = _to_decimal(pc_sums['total_credito']) - _to_decimal(pc_sums['total_debito'])

        nivel_endeudamiento = _ZERO
        concentracion_cp = _ZERO
        if activo != _ZERO:
            nivel_endeudamiento = ((pasivo / activo) * 100).quantize(Decimal('0.01'))
        if pasivo != _ZERO:
            concentracion_cp = ((pasivo_corriente / pasivo) * 100).quantize(Decimal('0.01'))

        return {
            'labels': ['Nivel Endeudamiento (%)', 'Concentracion CP (%)'],
            'datasets': [
                {
                    'label': 'Endeudamiento',
                    'data': [str(nivel_endeudamiento), str(concentracion_cp)],
                },
            ],
            'summary': {
                'nivel_endeudamiento': str(nivel_endeudamiento),
                'concentracion_cp': str(concentracion_cp),
                'pasivo_total': str(pasivo),
                'activo_total': str(activo),
                'pasivo_corriente': str(pasivo_corriente),
            },
        }

    # ──────────────────────────────────────────────
    # Costos y Gastos
    # ──────────────────────────────────────────────

    def costo_ventas(self, company_id, filtros: dict) -> dict:
        """Total de costos de venta (titulo 6)."""
        if filtros.get('agrupar_por_mes'):
            return self._costo_ventas_mensual(company_id, filtros)

        qs = self._get_queryset_base(company_id, filtros)
        costos = self._saldo_titulo(qs, _TITULO_COSTOS)

        return {
            'labels': ['Costo de Ventas'],
            'datasets': [
                {'label': 'Costo de Ventas', 'data': [str(costos)]},
            ],
            'summary': {'costo_ventas': str(costos)},
        }

    def margen_bruto_neto(self, company_id, filtros: dict) -> dict:
        """Margenes de rentabilidad."""
        if filtros.get('agrupar_por_mes'):
            return self._margen_bruto_neto_mensual(company_id, filtros)

        qs = self._get_queryset_base(company_id, filtros)

        ingresos = self._saldo_titulo(qs, _TITULO_INGRESOS)
        costos = self._saldo_titulo(qs, _TITULO_COSTOS)
        gastos = self._saldo_titulo(qs, _TITULO_GASTOS)

        margen_bruto = _ZERO
        margen_neto = _ZERO
        if ingresos != _ZERO:
            margen_bruto = (((ingresos - costos) / ingresos) * 100).quantize(Decimal('0.01'))
            margen_neto = (((ingresos - costos - gastos) / ingresos) * 100).quantize(Decimal('0.01'))

        return {
            'labels': ['Margen Bruto (%)', 'Margen Neto (%)'],
            'datasets': [
                {'label': 'Margenes', 'data': [str(margen_bruto), str(margen_neto)]},
            ],
            'summary': {
                'margen_bruto': str(margen_bruto),
                'margen_neto': str(margen_neto),
                'ingresos': str(ingresos),
                'costos': str(costos),
                'gastos': str(gastos),
            },
        }

    def gastos_operacionales(self, company_id, filtros: dict) -> dict:
        """Gastos operacionales desglosados por grupo contable."""
        qs = self._get_queryset_base(company_id, filtros)

        grupos = (
            qs.filter(titulo_codigo=_TITULO_GASTOS)
            .values('grupo_codigo', 'grupo_nombre')
            .annotate(
                total_debito=Coalesce(Sum('debito'), _ZERO),
                total_credito=Coalesce(Sum('credito'), _ZERO),
            )
            .order_by('-total_debito')
        )

        labels = []
        data = []
        for g in grupos:
            nombre = g['grupo_nombre'] or f'Grupo {g["grupo_codigo"]}'
            saldo = _to_decimal(g['total_debito']) - _to_decimal(g['total_credito'])
            labels.append(nombre)
            data.append(str(saldo))

        return {
            'labels': labels,
            'datasets': [{'label': 'Gastos Operacionales', 'data': data}],
            'summary': {'total_gastos': str(self._saldo_titulo(qs, _TITULO_GASTOS))},
        }

    def gastos_por_departamento(self, company_id, filtros: dict) -> dict:
        """Gastos agrupados por departamento."""
        qs = self._get_queryset_base(company_id, filtros)

        deptos = (
            qs.filter(titulo_codigo__in=[_TITULO_GASTOS, _TITULO_COSTOS])
            .exclude(departamento_codigo__isnull=True)
            .values('departamento_codigo', 'departamento_nombre')
            .annotate(
                total_debito=Coalesce(Sum('debito'), _ZERO),
                total_credito=Coalesce(Sum('credito'), _ZERO),
            )
            .order_by('-total_debito')
        )

        labels = []
        data = []
        for d in deptos:
            nombre = d['departamento_nombre'] or f'Depto {d["departamento_codigo"]}'
            saldo = _to_decimal(d['total_debito']) - _to_decimal(d['total_credito'])
            labels.append(nombre)
            data.append(str(saldo))

        return {
            'labels': labels,
            'datasets': [{'label': 'Gastos por Departamento', 'data': data}],
            'summary': {'total_registros': len(labels)},
        }

    def gastos_por_centro_costo(self, company_id, filtros: dict) -> dict:
        """Gastos agrupados por centro de costo."""
        qs = self._get_queryset_base(company_id, filtros)

        ccs = (
            qs.filter(titulo_codigo__in=[_TITULO_GASTOS, _TITULO_COSTOS])
            .exclude(centro_costo_codigo__isnull=True)
            .values('centro_costo_codigo', 'centro_costo_nombre')
            .annotate(
                total_debito=Coalesce(Sum('debito'), _ZERO),
                total_credito=Coalesce(Sum('credito'), _ZERO),
            )
            .order_by('-total_debito')
        )

        labels = []
        data = []
        for cc in ccs:
            nombre = cc['centro_costo_nombre'] or f'CC {cc["centro_costo_codigo"]}'
            saldo = _to_decimal(cc['total_debito']) - _to_decimal(cc['total_credito'])
            labels.append(nombre)
            data.append(str(saldo))

        return {
            'labels': labels,
            'datasets': [{'label': 'Gastos por Centro de Costo', 'data': data}],
            'summary': {'total_registros': len(labels)},
        }

    # ──────────────────────────────────────────────
    # Cartera (CxC)
    # ──────────────────────────────────────────────

    def cartera_total(self, company_id, filtros: dict) -> dict:
        """Total de cuentas por cobrar (grupo 13)."""
        qs = self._get_queryset_base(company_id, filtros)

        cxc_qs = qs.filter(grupo_codigo=_CXC_GRUPO)
        sums = cxc_qs.aggregate(
            total_debito=Coalesce(Sum('debito'), _ZERO),
            total_credito=Coalesce(Sum('credito'), _ZERO),
        )
        total = _to_decimal(sums['total_debito']) - _to_decimal(sums['total_credito'])

        return {
            'labels': ['Cartera Total'],
            'datasets': [{'label': 'Cartera', 'data': [str(total)]}],
            'summary': {'cartera_total': str(total)},
        }

    def aging_cartera(self, company_id, filtros: dict) -> dict:
        """
        Aging de cuentas por cobrar agrupado por dias vencidos.
        Buckets: Corriente, 1-30, 31-60, 61-90, +90.
        Usa duedate para calcular antiguedad.
        """
        qs = self._get_queryset_base(company_id, filtros)
        today = date.today()

        cxc_qs = qs.filter(grupo_codigo=_CXC_GRUPO)

        buckets = {
            'Corriente': _ZERO,
            '1-30': _ZERO,
            '31-60': _ZERO,
            '61-90': _ZERO,
            '+90': _ZERO,
        }

        # Get individual records with duedate for aging calculation
        records = cxc_qs.values('duedate').annotate(
            saldo=Sum(F('debito') - F('credito')),
        )

        for rec in records:
            saldo = _to_decimal(rec['saldo'])
            if saldo <= _ZERO:
                continue

            duedate = rec['duedate']
            if duedate is None:
                buckets['Corriente'] += saldo
                continue

            days_past = (today - duedate).days
            if days_past <= 0:
                buckets['Corriente'] += saldo
            elif days_past <= 30:
                buckets['1-30'] += saldo
            elif days_past <= 60:
                buckets['31-60'] += saldo
            elif days_past <= 90:
                buckets['61-90'] += saldo
            else:
                buckets['+90'] += saldo

        labels = list(buckets.keys())
        data = [str(v) for v in buckets.values()]

        return {
            'labels': labels,
            'datasets': [{'label': 'Aging Cartera', 'data': data}],
            'summary': {
                'total': str(sum(buckets.values())),
                'vencido': str(sum(v for k, v in buckets.items() if k != 'Corriente')),
            },
        }

    def top_clientes_saldo(self, company_id, filtros: dict) -> dict:
        """Top 10 clientes por saldo de cartera."""
        qs = self._get_queryset_base(company_id, filtros)

        clientes = (
            qs.filter(grupo_codigo=_CXC_GRUPO)
            .values('tercero_id', 'tercero_nombre')
            .annotate(
                total_debito=Coalesce(Sum('debito'), _ZERO),
                total_credito=Coalesce(Sum('credito'), _ZERO),
            )
            .order_by('-total_debito')[:10]
        )

        labels = []
        data = []
        for c in clientes:
            nombre = c['tercero_nombre'] or c['tercero_id']
            saldo = _to_decimal(c['total_debito']) - _to_decimal(c['total_credito'])
            if saldo > _ZERO:
                labels.append(nombre)
                data.append(str(saldo))

        return {
            'labels': labels,
            'datasets': [{'label': 'Top Clientes', 'data': data}],
            'summary': {'total_clientes': len(labels)},
        }

    def movimiento_por_tercero(self, company_id, filtros: dict) -> dict:
        """Fallback sin config: delega a la versión configurable con defaults."""
        return self.movimiento_por_tercero_config(company_id, filtros, {})

    def movimiento_por_tercero_config(
        self, company_id, filtros: dict, card_config: dict
    ) -> dict:
        """Debitos y creditos de un rango de cuentas agrupados por tercero.

        card_config keys:
            nivel_cuenta: titulo|grupo|cuenta|subcuenta|auxiliar  (default: titulo)
            codigo_desde: int  (default: None → sin filtro)
            codigo_hasta: int  (default: None → sin filtro)
            direccion:    debito|credito|neto  (default: neto — para ordenar)
            top_n:        int  (default: 20)
        """
        _NIVEL_MAP = {
            'titulo': 'titulo_codigo',
            'grupo': 'grupo_codigo',
            'cuenta': 'cuenta_codigo',
            'subcuenta': 'subcuenta_codigo',
            'auxiliar': 'auxiliar',
        }
        nivel = card_config.get('nivel_cuenta', 'titulo')
        campo = _NIVEL_MAP.get(nivel, 'titulo_codigo')
        codigo_desde = card_config.get('codigo_desde')
        codigo_hasta = card_config.get('codigo_hasta')
        top_n = int(card_config.get('top_n') or 20)

        qs = self._get_queryset_base(company_id, filtros)

        if codigo_desde is not None:
            qs = qs.filter(**{f'{campo}__gte': int(codigo_desde)})
        if codigo_hasta is not None:
            qs = qs.filter(**{f'{campo}__lte': int(codigo_hasta)})

        tercero_ids = card_config.get('tercero_ids')
        if tercero_ids:
            qs = qs.filter(tercero_id__in=tercero_ids)

        terceros = (
            qs.values('tercero_id', 'tercero_nombre')
            .annotate(
                total_debito=Coalesce(Sum('debito'), _ZERO),
                total_credito=Coalesce(Sum('credito'), _ZERO),
            )
            .order_by('-total_debito')[:top_n]
        )

        labels, debitos, creditos = [], [], []
        for t in terceros:
            nombre = t['tercero_nombre'] or t['tercero_id']
            labels.append(nombre)
            debitos.append(str(_to_decimal(t['total_debito'])))
            creditos.append(str(_to_decimal(t['total_credito'])))

        return {
            'labels': labels,
            'datasets': [
                {'label': 'Debitos', 'data': debitos},
                {'label': 'Creditos', 'data': creditos},
            ],
            'summary': {'total_terceros': len(labels)},
        }

    # ──────────────────────────────────────────────
    # Proveedores (CxP)
    # ──────────────────────────────────────────────

    def cuentas_por_pagar(self, company_id, filtros: dict) -> dict:
        """Total de cuentas por pagar (grupo 22)."""
        qs = self._get_queryset_base(company_id, filtros)

        cxp_qs = qs.filter(grupo_codigo=_CXP_GRUPO)
        sums = cxp_qs.aggregate(
            total_debito=Coalesce(Sum('debito'), _ZERO),
            total_credito=Coalesce(Sum('credito'), _ZERO),
        )
        total = _to_decimal(sums['total_credito']) - _to_decimal(sums['total_debito'])

        return {
            'labels': ['Cuentas por Pagar'],
            'datasets': [{'label': 'CxP', 'data': [str(total)]}],
            'summary': {'cxp_total': str(total)},
        }

    def aging_proveedores(self, company_id, filtros: dict) -> dict:
        """Aging de cuentas por pagar por dias vencidos."""
        qs = self._get_queryset_base(company_id, filtros)
        today = date.today()

        cxp_qs = qs.filter(grupo_codigo=_CXP_GRUPO)

        buckets = {
            'Corriente': _ZERO,
            '1-30': _ZERO,
            '31-60': _ZERO,
            '61-90': _ZERO,
            '+90': _ZERO,
        }

        records = cxp_qs.values('duedate').annotate(
            saldo=Sum(F('credito') - F('debito')),
        )

        for rec in records:
            saldo = _to_decimal(rec['saldo'])
            if saldo <= _ZERO:
                continue

            duedate = rec['duedate']
            if duedate is None:
                buckets['Corriente'] += saldo
                continue

            days_past = (today - duedate).days
            if days_past <= 0:
                buckets['Corriente'] += saldo
            elif days_past <= 30:
                buckets['1-30'] += saldo
            elif days_past <= 60:
                buckets['31-60'] += saldo
            elif days_past <= 90:
                buckets['61-90'] += saldo
            else:
                buckets['+90'] += saldo

        labels = list(buckets.keys())
        data = [str(v) for v in buckets.values()]

        return {
            'labels': labels,
            'datasets': [{'label': 'Aging Proveedores', 'data': data}],
            'summary': {
                'total': str(sum(buckets.values())),
                'vencido': str(sum(v for k, v in buckets.items() if k != 'Corriente')),
            },
        }

    def top_proveedores(self, company_id, filtros: dict) -> dict:
        """Top 10 proveedores por saldo pendiente."""
        qs = self._get_queryset_base(company_id, filtros)

        proveedores = (
            qs.filter(grupo_codigo=_CXP_GRUPO)
            .values('tercero_id', 'tercero_nombre')
            .annotate(
                total_debito=Coalesce(Sum('debito'), _ZERO),
                total_credito=Coalesce(Sum('credito'), _ZERO),
            )
            .order_by('-total_credito')[:10]
        )

        labels = []
        data = []
        for p in proveedores:
            nombre = p['tercero_nombre'] or p['tercero_id']
            saldo = _to_decimal(p['total_credito']) - _to_decimal(p['total_debito'])
            if saldo > _ZERO:
                labels.append(nombre)
                data.append(str(saldo))

        return {
            'labels': labels,
            'datasets': [{'label': 'Top Proveedores', 'data': data}],
            'summary': {'total_proveedores': len(labels)},
        }

    # ──────────────────────────────────────────────
    # Proyectos
    # ──────────────────────────────────────────────

    def costo_por_proyecto(self, company_id, filtros: dict) -> dict:
        """Costos y gastos agrupados por proyecto contable."""
        qs = self._get_queryset_base(company_id, filtros)

        proyectos = (
            qs.filter(titulo_codigo__in=[_TITULO_COSTOS, _TITULO_GASTOS])
            .exclude(proyecto_codigo__isnull=True)
            .exclude(proyecto_codigo='')
            .values('proyecto_codigo', 'proyecto_nombre')
            .annotate(
                total_debito=Coalesce(Sum('debito'), _ZERO),
                total_credito=Coalesce(Sum('credito'), _ZERO),
            )
            .order_by('-total_debito')
        )

        labels = []
        data = []
        for p in proyectos:
            nombre = p['proyecto_nombre'] or p['proyecto_codigo']
            saldo = _to_decimal(p['total_debito']) - _to_decimal(p['total_credito'])
            labels.append(nombre)
            data.append(str(saldo))

        return {
            'labels': labels,
            'datasets': [{'label': 'Costo por Proyecto', 'data': data}],
            'summary': {'total_proyectos': len(labels)},
        }

    def costo_por_actividad(self, company_id, filtros: dict) -> dict:
        """Costos y gastos agrupados por actividad contable."""
        qs = self._get_queryset_base(company_id, filtros)

        actividades = (
            qs.filter(titulo_codigo__in=[_TITULO_COSTOS, _TITULO_GASTOS])
            .exclude(actividad_codigo__isnull=True)
            .exclude(actividad_codigo='')
            .values('actividad_codigo', 'actividad_nombre')
            .annotate(
                total_debito=Coalesce(Sum('debito'), _ZERO),
                total_credito=Coalesce(Sum('credito'), _ZERO),
            )
            .order_by('-total_debito')
        )

        labels = []
        data = []
        for a in actividades:
            nombre = a['actividad_nombre'] or a['actividad_codigo']
            saldo = _to_decimal(a['total_debito']) - _to_decimal(a['total_credito'])
            labels.append(nombre)
            data.append(str(saldo))

        return {
            'labels': labels,
            'datasets': [{'label': 'Costo por Actividad', 'data': data}],
            'summary': {'total_actividades': len(labels)},
        }

    # ──────────────────────────────────────────────
    # Comparativos
    # ──────────────────────────────────────────────

    def comparativo_periodos(self, company_id, filtros: dict) -> dict:
        """
        Comparacion entre dos periodos.
        Usa filtros: periodo_1 y periodo_2.
        """
        periodo_1 = filtros.get('periodo_1', '')
        periodo_2 = filtros.get('periodo_2', '')

        if not periodo_1 or not periodo_2:
            return {
                'labels': [],
                'datasets': [],
                'summary': {'error': 'Se requieren periodo_1 y periodo_2'},
            }

        qs = MovimientoContable.objects.filter(company_id=company_id)

        result = {}
        for periodo, label in [(periodo_1, 'Periodo 1'), (periodo_2, 'Periodo 2')]:
            pqs = qs.filter(periodo=periodo)
            ingresos = self._saldo_titulo(pqs, _TITULO_INGRESOS)
            costos = self._saldo_titulo(pqs, _TITULO_COSTOS)
            gastos = self._saldo_titulo(pqs, _TITULO_GASTOS)
            result[label] = {
                'ingresos': ingresos,
                'costos': costos,
                'gastos': gastos,
                'utilidad': ingresos - costos - gastos,
            }

        labels = ['Ingresos', 'Costos', 'Gastos', 'Utilidad']
        datasets = [
            {
                'label': periodo_1,
                'data': [
                    str(result['Periodo 1']['ingresos']),
                    str(result['Periodo 1']['costos']),
                    str(result['Periodo 1']['gastos']),
                    str(result['Periodo 1']['utilidad']),
                ],
            },
            {
                'label': periodo_2,
                'data': [
                    str(result['Periodo 2']['ingresos']),
                    str(result['Periodo 2']['costos']),
                    str(result['Periodo 2']['gastos']),
                    str(result['Periodo 2']['utilidad']),
                ],
            },
        ]

        # Calculate variation
        variacion_ingresos = _ZERO
        if result['Periodo 1']['ingresos'] != _ZERO:
            variacion_ingresos = (
                ((result['Periodo 2']['ingresos'] - result['Periodo 1']['ingresos'])
                 / result['Periodo 1']['ingresos']) * 100
            ).quantize(Decimal('0.01'))

        return {
            'labels': labels,
            'datasets': datasets,
            'summary': {
                'periodo_1': periodo_1,
                'periodo_2': periodo_2,
                'variacion_ingresos_pct': str(variacion_ingresos),
            },
        }

    def tendencia_mensual(self, company_id, filtros: dict) -> dict:
        """
        Tendencia mensual de ingresos, costos y utilidad.
        Calcula los ultimos 12 periodos por defecto.
        Usa _aggregate_by_periodo_titulo para evitar N+1.
        """
        qs = self._get_queryset_base(company_id, filtros)

        periodo_list = sorted(set(qs.values_list('periodo', flat=True)))
        if not periodo_list:
            return {'labels': [], 'datasets': [], 'summary': {}}

        periodo_list = periodo_list[-12:]

        # Una sola query en lugar de N queries
        titulos = [_TITULO_INGRESOS, _TITULO_COSTOS, _TITULO_GASTOS]
        by_periodo = self._aggregate_by_periodo_titulo(
            qs.filter(periodo__in=periodo_list), titulos
        )

        labels = list(periodo_list)
        ingresos_data = []
        costos_data = []
        utilidad_data = []

        for periodo in periodo_list:
            p_data = by_periodo.get(periodo, {})
            ingresos = p_data.get(_TITULO_INGRESOS, _ZERO)
            costos = p_data.get(_TITULO_COSTOS, _ZERO)
            gastos = p_data.get(_TITULO_GASTOS, _ZERO)
            utilidad = ingresos - costos - gastos
            ingresos_data.append(str(ingresos))
            costos_data.append(str(costos))
            utilidad_data.append(str(utilidad))

        return {
            'labels': labels,
            'datasets': [
                {'label': 'Ingresos', 'data': ingresos_data},
                {'label': 'Costos + Gastos', 'data': costos_data},
                {'label': 'Utilidad', 'data': utilidad_data},
            ],
            'summary': {
                'total_periodos': len(labels),
            },
        }

    # ──────────────────────────────────────────────
    # Helpers: series mensuales (evitan N+1)
    # ──────────────────────────────────────────────

    def _aggregate_by_periodo_titulo(
        self, qs, titulo_codigos: list
    ) -> dict:
        """
        Agrega en UNA sola query por (periodo, titulo_codigo).
        Retorna {periodo: {titulo_codigo: saldo_neto}}.
        Evita el patron N+1 de titulo por periodo.
        """
        rows = (
            qs.filter(titulo_codigo__in=titulo_codigos)
            .values('periodo', 'titulo_codigo')
            .annotate(
                total_debito=Coalesce(Sum('debito'), _ZERO),
                total_credito=Coalesce(Sum('credito'), _ZERO),
            )
        )

        result: dict = {}
        for row in rows:
            p = row['periodo']
            t = row['titulo_codigo']
            if p not in result:
                result[p] = {}
            debito = _to_decimal(row['total_debito'])
            credito = _to_decimal(row['total_credito'])
            # Naturaleza: activo/gastos/costos = debito-credito; resto = credito-debito
            if t in (_TITULO_ACTIVO, _TITULO_GASTOS, _TITULO_COSTOS):
                result[p][t] = debito - credito
            else:
                result[p][t] = credito - debito

        return result

    def _get_periodos_para_anio(self, qs, filtros: dict) -> list:
        """
        Retorna lista de periodos YYYY-MM.
        Si 'anio' esta en filtros, genera los 12 meses del año.
        Si no, usa los ultimos 12 periodos distintos del queryset.
        """
        anio = filtros.get('anio')
        if anio:
            return [f'{anio}-{m:02d}' for m in range(1, 13)]
        periodos = sorted(qs.values_list('periodo', flat=True).distinct())
        return periodos[-12:]

    def _apply_rango_cuentas(self, qs, card_config: dict):
        """
        Aplica filtros de rango de cuentas PUC segun la configuracion de la tarjeta.
        Retorna el queryset filtrado.
        """
        _nivel_a_campo = {
            'titulo': 'titulo_codigo',
            'grupo': 'grupo_codigo',
            'cuenta': 'cuenta_codigo',
            'subcuenta': 'subcuenta_codigo',
            'auxiliar': 'auxiliar',
        }
        nivel = card_config.get('nivel_cuenta', 'titulo')
        campo = _nivel_a_campo.get(nivel, 'titulo_codigo')
        codigo_desde = card_config.get('codigo_desde')
        codigo_hasta = card_config.get('codigo_hasta')

        if codigo_desde is not None:
            qs = qs.filter(**{f'{campo}__gte': int(codigo_desde)})
        if codigo_hasta is not None:
            qs = qs.filter(**{f'{campo}__lte': int(codigo_hasta)})

        # Filtro de terceros específicos (multi-select desde card_config)
        tercero_ids = card_config.get('tercero_ids')
        if tercero_ids:
            qs = qs.filter(tercero_id__in=tercero_ids)

        return qs

    def _calcular_saldo_con_direccion(
        self, total_debito: Decimal, total_credito: Decimal, direccion: str
    ) -> Decimal:
        """
        Aplica la logica de direccion al calculo del saldo.
        debito: retorna solo debitos.
        credito: retorna solo creditos.
        neto: retorna debito - credito.
        """
        if direccion == 'debito':
            return _to_decimal(total_debito)
        if direccion == 'credito':
            return _to_decimal(total_credito)
        return _to_decimal(total_debito) - _to_decimal(total_credito)

    # ──────────────────────────────────────────────
    # Estado de Resultados mensual (agrupar_por_mes)
    # ──────────────────────────────────────────────

    def _estado_resultados_mensual(self, company_id, filtros: dict) -> dict:
        """Serie mensual del estado de resultados. 1 query via _aggregate_by_periodo_titulo."""
        qs = self._get_queryset_base(company_id, filtros)
        periodos = self._get_periodos_para_anio(qs, filtros)
        if not periodos:
            return {'labels': [], 'datasets': [], 'summary': {}}

        titulos = [_TITULO_INGRESOS, _TITULO_COSTOS, _TITULO_GASTOS]
        by_periodo = self._aggregate_by_periodo_titulo(
            qs.filter(periodo__in=periodos), titulos
        )

        ingresos_data, costos_data, utilidad_data = [], [], []
        for p in periodos:
            pd = by_periodo.get(p, {})
            ingresos = pd.get(_TITULO_INGRESOS, _ZERO)
            costos = pd.get(_TITULO_COSTOS, _ZERO)
            gastos = pd.get(_TITULO_GASTOS, _ZERO)
            ingresos_data.append(str(ingresos))
            costos_data.append(str(costos))
            utilidad_data.append(str(ingresos - costos - gastos))

        return {
            'labels': periodos,
            'datasets': [
                {'label': 'Ingresos', 'data': ingresos_data},
                {'label': 'Costos', 'data': costos_data},
                {'label': 'Utilidad Neta', 'data': utilidad_data},
            ],
            'summary': {
                'anio': filtros.get('anio', ''),
                'total_periodos': len(periodos),
            },
        }

    # ──────────────────────────────────────────────
    # Series mensuales — tarjetas adicionales
    # ──────────────────────────────────────────────

    def _ingresos_vs_egresos_mensual(self, company_id, filtros: dict) -> dict:
        """Serie mensual Ingresos vs Egresos. 1 query via _aggregate_by_periodo_titulo."""
        qs = self._get_queryset_base(company_id, filtros)
        periodos = self._get_periodos_para_anio(qs, filtros)
        if not periodos:
            return {'labels': [], 'datasets': [], 'summary': {}}

        titulos = [_TITULO_INGRESOS, _TITULO_COSTOS, _TITULO_GASTOS]
        by_periodo = self._aggregate_by_periodo_titulo(
            qs.filter(periodo__in=periodos), titulos
        )

        ingresos_data, egresos_data = [], []
        for p in periodos:
            pd = by_periodo.get(p, {})
            ingresos = pd.get(_TITULO_INGRESOS, _ZERO)
            egresos = pd.get(_TITULO_COSTOS, _ZERO) + pd.get(_TITULO_GASTOS, _ZERO)
            ingresos_data.append(str(ingresos))
            egresos_data.append(str(egresos))

        return {
            'labels': periodos,
            'datasets': [
                {'label': 'Ingresos', 'data': ingresos_data},
                {'label': 'Egresos', 'data': egresos_data},
            ],
            'summary': {'anio': filtros.get('anio', ''), 'total_periodos': len(periodos)},
        }

    def _ebitda_mensual(self, company_id, filtros: dict) -> dict:
        """Serie mensual de EBITDA aproximado. 1 query via _aggregate_by_periodo_titulo."""
        qs = self._get_queryset_base(company_id, filtros)
        periodos = self._get_periodos_para_anio(qs, filtros)
        if not periodos:
            return {'labels': [], 'datasets': [], 'summary': {}}

        titulos = [_TITULO_INGRESOS, _TITULO_COSTOS, _TITULO_GASTOS]
        by_periodo = self._aggregate_by_periodo_titulo(
            qs.filter(periodo__in=periodos), titulos
        )

        ebitda_data = []
        for p in periodos:
            pd = by_periodo.get(p, {})
            val = (
                pd.get(_TITULO_INGRESOS, _ZERO)
                - pd.get(_TITULO_COSTOS, _ZERO)
                - pd.get(_TITULO_GASTOS, _ZERO)
            )
            ebitda_data.append(str(val))

        return {
            'labels': periodos,
            'datasets': [{'label': 'EBITDA', 'data': ebitda_data}],
            'summary': {'anio': filtros.get('anio', ''), 'total_periodos': len(periodos)},
        }

    def _costo_ventas_mensual(self, company_id, filtros: dict) -> dict:
        """Serie mensual de costo de ventas. 1 query via _aggregate_by_periodo_titulo."""
        qs = self._get_queryset_base(company_id, filtros)
        periodos = self._get_periodos_para_anio(qs, filtros)
        if not periodos:
            return {'labels': [], 'datasets': [], 'summary': {}}

        by_periodo = self._aggregate_by_periodo_titulo(
            qs.filter(periodo__in=periodos), [_TITULO_COSTOS]
        )

        costos_data = [str(by_periodo.get(p, {}).get(_TITULO_COSTOS, _ZERO)) for p in periodos]

        return {
            'labels': periodos,
            'datasets': [{'label': 'Costo de Ventas', 'data': costos_data}],
            'summary': {'anio': filtros.get('anio', ''), 'total_periodos': len(periodos)},
        }

    def _margen_bruto_neto_mensual(self, company_id, filtros: dict) -> dict:
        """Serie mensual de margenes (%). 1 query via _aggregate_by_periodo_titulo."""
        qs = self._get_queryset_base(company_id, filtros)
        periodos = self._get_periodos_para_anio(qs, filtros)
        if not periodos:
            return {'labels': [], 'datasets': [], 'summary': {}}

        titulos = [_TITULO_INGRESOS, _TITULO_COSTOS, _TITULO_GASTOS]
        by_periodo = self._aggregate_by_periodo_titulo(
            qs.filter(periodo__in=periodos), titulos
        )

        bruto_data, neto_data = [], []
        for p in periodos:
            pd = by_periodo.get(p, {})
            ingresos = pd.get(_TITULO_INGRESOS, _ZERO)
            costos = pd.get(_TITULO_COSTOS, _ZERO)
            gastos = pd.get(_TITULO_GASTOS, _ZERO)
            if ingresos != _ZERO:
                mb = (((ingresos - costos) / ingresos) * 100).quantize(Decimal('0.01'))
                mn = (((ingresos - costos - gastos) / ingresos) * 100).quantize(Decimal('0.01'))
            else:
                mb = mn = _ZERO
            bruto_data.append(str(mb))
            neto_data.append(str(mn))

        return {
            'labels': periodos,
            'datasets': [
                {'label': 'Margen Bruto (%)', 'data': bruto_data},
                {'label': 'Margen Neto (%)', 'data': neto_data},
            ],
            'summary': {'anio': filtros.get('anio', ''), 'total_periodos': len(periodos)},
        }

    # ──────────────────────────────────────────────
    # Dispatcher para tarjetas con config especifica
    # ──────────────────────────────────────────────

    def _dispatch_config_card(
        self, company_id, card_type_code: str, filtros: dict, card_config: dict
    ) -> dict:
        if card_type_code == 'CUSTOM_RANGO_CUENTAS':
            return self.custom_rango_cuentas(company_id, filtros, card_config)
        if card_type_code == 'DISTRIBUCION_POR_PROYECTO':
            return self.distribucion_por_proyecto(company_id, filtros, card_config)
        if card_type_code == 'MOVIMIENTO_POR_TERCERO':
            return self.movimiento_por_tercero_config(company_id, filtros, card_config)
        return {'labels': [], 'datasets': [], 'summary': {}}

    # ──────────────────────────────────────────────
    # Tarjetas personalizadas
    # ──────────────────────────────────────────────

    def custom_rango_cuentas(
        self, company_id, filtros: dict, card_config: dict
    ) -> dict:
        """
        Rango de cuentas PUC personalizado.
        card_config: {nivel_cuenta, codigo_desde, codigo_hasta, direccion,
                      agrupar_por_mes, agrupar_por_cuenta}
        """
        _nivel_a_campo = {
            'titulo': 'titulo_codigo',
            'grupo': 'grupo_codigo',
            'cuenta': 'cuenta_codigo',
            'subcuenta': 'subcuenta_codigo',
            'auxiliar': 'auxiliar',
        }
        nivel = card_config.get('nivel_cuenta', 'titulo')
        campo_nivel = _nivel_a_campo.get(nivel, 'titulo_codigo')

        qs = self._get_queryset_base(company_id, filtros)
        qs = self._apply_rango_cuentas(qs, card_config)
        direccion = card_config.get('direccion', 'neto')
        titulo = card_config.get('titulo_personalizado', 'Rango de Cuentas')

        # Modo: una barra por cuenta individual
        if card_config.get('agrupar_por_cuenta'):
            campo_nombre = campo_nivel.replace('_codigo', '_nombre') if '_codigo' in campo_nivel else None
            group_fields = [campo_nivel]
            if campo_nombre:
                group_fields.append(campo_nombre)

            rows = (
                qs.values(*group_fields)
                .annotate(
                    total_debito=Coalesce(Sum('debito'), _ZERO),
                    total_credito=Coalesce(Sum('credito'), _ZERO),
                )
                .order_by(campo_nivel)
            )
            labels = []
            data = []
            total = _ZERO
            for row in rows:
                codigo = row[campo_nivel]
                nombre = row.get(campo_nombre, '') if campo_nombre else ''
                label = f'{codigo} - {nombre}' if nombre else str(codigo)
                saldo = self._calcular_saldo_con_direccion(
                    row['total_debito'], row['total_credito'], direccion
                )
                labels.append(label)
                data.append(str(saldo))
                total += saldo

            return {
                'labels': labels,
                'datasets': [{'label': titulo, 'data': data}],
                'summary': {
                    'total': str(total),
                    'total_cuentas': len(labels),
                    'nivel_cuenta': nivel,
                },
            }

        # Modo: serie mensual
        if card_config.get('agrupar_por_mes'):
            periodos = self._get_periodos_para_anio(qs, filtros)
            if not periodos:
                return {'labels': [], 'datasets': [], 'summary': {}}

            rows = (
                qs.filter(periodo__in=periodos)
                .values('periodo')
                .annotate(
                    total_debito=Coalesce(Sum('debito'), _ZERO),
                    total_credito=Coalesce(Sum('credito'), _ZERO),
                )
            )
            por_periodo = {r['periodo']: r for r in rows}
            data = []
            for p in periodos:
                r = por_periodo.get(p, {'total_debito': _ZERO, 'total_credito': _ZERO})
                saldo = self._calcular_saldo_con_direccion(
                    r['total_debito'], r['total_credito'], direccion
                )
                data.append(str(saldo))

            return {
                'labels': periodos,
                'datasets': [{'label': titulo, 'data': data}],
                'summary': {
                    'anio': filtros.get('anio', ''),
                    'total_periodos': len(periodos),
                },
            }

        # Modo: total del rango (default)
        sums = qs.aggregate(
            total_debito=Coalesce(Sum('debito'), _ZERO),
            total_credito=Coalesce(Sum('credito'), _ZERO),
        )
        saldo = self._calcular_saldo_con_direccion(
            sums['total_debito'], sums['total_credito'], direccion
        )

        return {
            'labels': [titulo],
            'datasets': [{'label': titulo, 'data': [str(saldo)]}],
            'summary': {
                'saldo': str(saldo),
                'nivel_cuenta': card_config.get('nivel_cuenta', ''),
                'direccion': direccion,
            },
        }

    def distribucion_por_proyecto(
        self, company_id, filtros: dict, card_config: dict
    ) -> dict:
        """
        Distribucion de un rango de cuentas por proyecto contable.
        card_config: {nivel_cuenta, codigo_desde, codigo_hasta, direccion, top_n}
        """
        qs = self._get_queryset_base(company_id, filtros)
        qs = self._apply_rango_cuentas(qs, card_config)
        direccion = card_config.get('direccion', 'neto')
        top_n = int(card_config.get('top_n') or 0) or None
        titulo = card_config.get('titulo_personalizado', 'Distribucion por Proyecto')

        proyectos = (
            qs.exclude(proyecto_codigo__isnull=True)
            .exclude(proyecto_codigo='')
            .values('proyecto_codigo', 'proyecto_nombre')
            .annotate(
                total_debito=Coalesce(Sum('debito'), _ZERO),
                total_credito=Coalesce(Sum('credito'), _ZERO),
            )
            .order_by('-total_debito')
        )
        if top_n:
            proyectos = proyectos[:top_n]

        labels = []
        data = []
        total = _ZERO
        for p in proyectos:
            nombre = p['proyecto_nombre'] or p['proyecto_codigo']
            saldo = self._calcular_saldo_con_direccion(
                p['total_debito'], p['total_credito'], direccion
            )
            labels.append(nombre)
            data.append(str(saldo))
            total += saldo

        return {
            'labels': labels,
            'datasets': [{'label': titulo, 'data': data}],
            'summary': {
                'total': str(total),
                'total_proyectos': len(labels),
            },
        }

    # ──────────────────────────────────────────────
    # Nuevas tarjetas analiticas
    # ──────────────────────────────────────────────

    def ingresos_por_proyecto(self, company_id, filtros: dict) -> dict:
        """Distribucion de ingresos (titulo 4) por proyecto contable."""
        qs = self._get_queryset_base(company_id, filtros)

        proyectos = (
            qs.filter(titulo_codigo=_TITULO_INGRESOS)
            .exclude(proyecto_codigo__isnull=True)
            .exclude(proyecto_codigo='')
            .values('proyecto_codigo', 'proyecto_nombre')
            .annotate(
                total_debito=Coalesce(Sum('debito'), _ZERO),
                total_credito=Coalesce(Sum('credito'), _ZERO),
            )
            .order_by('-total_credito')
        )

        labels = []
        data = []
        total = _ZERO
        for p in proyectos:
            nombre = p['proyecto_nombre'] or p['proyecto_codigo']
            saldo = _to_decimal(p['total_credito']) - _to_decimal(p['total_debito'])
            labels.append(nombre)
            data.append(str(saldo))
            total += saldo

        return {
            'labels': labels,
            'datasets': [{'label': 'Ingresos por Proyecto', 'data': data}],
            'summary': {
                'total_ingresos': str(total),
                'total_proyectos': len(labels),
            },
        }

    def gastos_actividad_proyecto(self, company_id, filtros: dict) -> dict:
        """
        Costos y gastos cruzados por actividad y proyecto.
        Retorna matriz: labels=actividades, datasets=un dataset por proyecto.
        1 sola query con pivot en Python.
        """
        qs = self._get_queryset_base(company_id, filtros)

        rows = (
            qs.filter(titulo_codigo__in=[_TITULO_COSTOS, _TITULO_GASTOS])
            .exclude(actividad_codigo__isnull=True)
            .exclude(actividad_codigo='')
            .exclude(proyecto_codigo__isnull=True)
            .exclude(proyecto_codigo='')
            .values(
                'actividad_codigo', 'actividad_nombre',
                'proyecto_codigo', 'proyecto_nombre',
            )
            .annotate(
                total_debito=Coalesce(Sum('debito'), _ZERO),
                total_credito=Coalesce(Sum('credito'), _ZERO),
            )
        )

        # Pivot en Python
        actividades_map: dict = {}  # {codigo: nombre}
        proyectos_map: dict = {}    # {codigo: nombre}
        data_matrix: dict = {}      # {(act_code, proy_code): saldo}

        for row in rows:
            act_code = row['actividad_codigo']
            act_nombre = row['actividad_nombre'] or act_code
            proy_code = row['proyecto_codigo']
            proy_nombre = row['proyecto_nombre'] or proy_code
            saldo = _to_decimal(row['total_debito']) - _to_decimal(row['total_credito'])

            actividades_map[act_code] = act_nombre
            proyectos_map[proy_code] = proy_nombre
            data_matrix[(act_code, proy_code)] = saldo

        actividades = sorted(actividades_map.keys())
        proyectos = sorted(proyectos_map.keys())
        labels = [actividades_map[a] for a in actividades]

        datasets = []
        for proy_code in proyectos:
            datasets.append({
                'label': proyectos_map[proy_code],
                'data': [
                    str(data_matrix.get((act_code, proy_code), _ZERO))
                    for act_code in actividades
                ],
            })

        return {
            'labels': labels,
            'datasets': datasets,
            'summary': {
                'total_actividades': len(actividades),
                'total_proyectos': len(proyectos),
            },
        }

    def flujo_caja_operacional(self, company_id, filtros: dict) -> dict:
        """
        Flujo de caja operacional mensual.
        Cobros = creditos CxC (grupo 13), Pagos = debitos CxP (grupo 22).
        1 query GROUP BY (periodo, grupo_codigo).
        """
        qs = self._get_queryset_base(company_id, filtros)

        periodos = self._get_periodos_para_anio(qs, filtros)
        if not periodos:
            return {'labels': [], 'datasets': [], 'summary': {}}

        rows = (
            qs.filter(
                periodo__in=periodos,
                grupo_codigo__in=[_CXC_GRUPO, _CXP_GRUPO],
            )
            .values('periodo', 'grupo_codigo')
            .annotate(
                total_debito=Coalesce(Sum('debito'), _ZERO),
                total_credito=Coalesce(Sum('credito'), _ZERO),
            )
        )

        por_periodo: dict = {p: {_CXC_GRUPO: _ZERO, _CXP_GRUPO: _ZERO} for p in periodos}
        for row in rows:
            p = row['periodo']
            g = row['grupo_codigo']
            if p in por_periodo:
                por_periodo[p][g] = (
                    _to_decimal(row['total_debito'])
                    if g == _CXP_GRUPO
                    else _to_decimal(row['total_credito'])
                )

        cobros_data = []
        pagos_data = []
        flujo_data = []
        for p in periodos:
            cobros = por_periodo[p][_CXC_GRUPO]
            pagos = por_periodo[p][_CXP_GRUPO]
            cobros_data.append(str(cobros))
            pagos_data.append(str(pagos))
            flujo_data.append(str(cobros - pagos))

        return {
            'labels': periodos,
            'datasets': [
                {'label': 'Cobros (CxC)', 'data': cobros_data},
                {'label': 'Pagos (CxP)', 'data': pagos_data},
                {'label': 'Flujo Neto', 'data': flujo_data},
            ],
            'summary': {
                'total_periodos': len(periodos),
                'anio': filtros.get('anio', ''),
            },
        }

    def rotacion_cartera(self, company_id, filtros: dict) -> dict:
        """
        Rotacion de cartera en dias.
        Formula: (Saldo CxC / Ingresos) * 365
        """
        qs = self._get_queryset_base(company_id, filtros)

        cxc_sums = qs.filter(grupo_codigo=_CXC_GRUPO).aggregate(
            total_debito=Coalesce(Sum('debito'), _ZERO),
            total_credito=Coalesce(Sum('credito'), _ZERO),
        )
        saldo_cxc = _to_decimal(cxc_sums['total_debito']) - _to_decimal(cxc_sums['total_credito'])
        ingresos = self._saldo_titulo(qs, _TITULO_INGRESOS)

        rotacion = _ZERO
        if ingresos > _ZERO:
            rotacion = (saldo_cxc / ingresos * 365).quantize(Decimal('0.01'))

        return {
            'labels': ['Rotacion de Cartera (dias)'],
            'datasets': [{'label': 'Dias', 'data': [str(rotacion)]}],
            'summary': {
                'rotacion_dias': str(rotacion),
                'saldo_cxc': str(saldo_cxc),
                'ingresos': str(ingresos),
            },
        }

    def rotacion_proveedores(self, company_id, filtros: dict) -> dict:
        """
        Rotacion de proveedores en dias.
        Formula: (Saldo CxP / Costo de Ventas) * 365
        """
        qs = self._get_queryset_base(company_id, filtros)

        cxp_sums = qs.filter(grupo_codigo=_CXP_GRUPO).aggregate(
            total_debito=Coalesce(Sum('debito'), _ZERO),
            total_credito=Coalesce(Sum('credito'), _ZERO),
        )
        saldo_cxp = _to_decimal(cxp_sums['total_credito']) - _to_decimal(cxp_sums['total_debito'])
        costo_ventas = self._saldo_titulo(qs, _TITULO_COSTOS)

        rotacion = _ZERO
        if costo_ventas > _ZERO:
            rotacion = (saldo_cxp / costo_ventas * 365).quantize(Decimal('0.01'))

        return {
            'labels': ['Rotacion de Proveedores (dias)'],
            'datasets': [{'label': 'Dias', 'data': [str(rotacion)]}],
            'summary': {
                'rotacion_dias': str(rotacion),
                'saldo_cxp': str(saldo_cxp),
                'costo_ventas': str(costo_ventas),
            },
        }

    def concentracion_ingresos_tercero(self, company_id, filtros: dict) -> dict:
        """Top 10 terceros por participacion en ingresos (titulo 4)."""
        qs = self._get_queryset_base(company_id, filtros)

        terceros = (
            qs.filter(titulo_codigo=_TITULO_INGRESOS)
            .exclude(tercero_id='')
            .values('tercero_id', 'tercero_nombre')
            .annotate(
                total_debito=Coalesce(Sum('debito'), _ZERO),
                total_credito=Coalesce(Sum('credito'), _ZERO),
            )
            .order_by('-total_credito')[:10]
        )

        labels = []
        data = []
        total = _ZERO
        for t in terceros:
            nombre = t['tercero_nombre'] or t['tercero_id']
            saldo = _to_decimal(t['total_credito']) - _to_decimal(t['total_debito'])
            if saldo > _ZERO:
                labels.append(nombre)
                data.append(str(saldo))
                total += saldo

        return {
            'labels': labels,
            'datasets': [{'label': 'Ingresos por Tercero', 'data': data}],
            'summary': {
                'total_ingresos': str(total),
                'total_terceros': len(labels),
            },
        }

    def deuda_patrimonio_mensual(self, company_id, filtros: dict) -> dict:
        """
        Evolucion mensual del ratio Deuda/Patrimonio.
        Ratio = (Pasivo / Patrimonio) * 100 por periodo.
        1 query via _aggregate_by_periodo_titulo.
        """
        qs = self._get_queryset_base(company_id, filtros)
        periodos = self._get_periodos_para_anio(qs, filtros)
        if not periodos:
            return {'labels': [], 'datasets': [], 'summary': {}}

        titulos = [_TITULO_PASIVO, _TITULO_PATRIMONIO]
        by_periodo = self._aggregate_by_periodo_titulo(
            qs.filter(periodo__in=periodos), titulos
        )

        ratio_data = []
        for p in periodos:
            pd = by_periodo.get(p, {})
            pasivo = pd.get(_TITULO_PASIVO, _ZERO)
            patrimonio = pd.get(_TITULO_PATRIMONIO, _ZERO)
            if patrimonio != _ZERO:
                ratio = (pasivo / patrimonio * 100).quantize(Decimal('0.01'))
            else:
                ratio = _ZERO
            ratio_data.append(str(ratio))

        return {
            'labels': periodos,
            'datasets': [{'label': 'Deuda/Patrimonio (%)', 'data': ratio_data}],
            'summary': {
                'anio': filtros.get('anio', ''),
                'total_periodos': len(periodos),
            },
        }
