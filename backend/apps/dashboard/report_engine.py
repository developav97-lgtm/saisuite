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

    def get_card_data(self, company_id, card_type_code: str, filtros: dict) -> dict:
        """
        Dispatcher principal. Llama al metodo correspondiente al card_type_code.

        Args:
            company_id: UUID de la empresa
            card_type_code: Codigo del tipo de tarjeta (ej: BALANCE_GENERAL)
            filtros: dict con fecha_desde, fecha_hasta, tercero_ids, etc.

        Returns:
            dict con {labels, datasets, summary}
        """
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
        """
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
        """Debitos y creditos agrupados por tercero."""
        qs = self._get_queryset_base(company_id, filtros)

        terceros = (
            qs.values('tercero_id', 'tercero_nombre')
            .annotate(
                total_debito=Coalesce(Sum('debito'), _ZERO),
                total_credito=Coalesce(Sum('credito'), _ZERO),
            )
            .order_by('-total_debito')[:20]
        )

        labels = []
        debitos = []
        creditos = []
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
        """
        qs = self._get_queryset_base(company_id, filtros)

        periodos = (
            qs.values('periodo')
            .annotate(
                total_debito=Coalesce(Sum('debito'), _ZERO),
                total_credito=Coalesce(Sum('credito'), _ZERO),
            )
            .order_by('periodo')
        )

        # We need per-periodo breakdown by titulo
        periodo_list = sorted(set(qs.values_list('periodo', flat=True)))
        if not periodo_list:
            return {'labels': [], 'datasets': [], 'summary': {}}

        # Limit to last 12 periods
        periodo_list = periodo_list[-12:]

        labels = list(periodo_list)
        ingresos_data = []
        costos_data = []
        utilidad_data = []

        for periodo in periodo_list:
            pqs = qs.filter(periodo=periodo)
            ingresos = self._saldo_titulo(pqs, _TITULO_INGRESOS)
            costos = self._saldo_titulo(pqs, _TITULO_COSTOS)
            gastos = self._saldo_titulo(pqs, _TITULO_GASTOS)
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
