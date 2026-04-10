"""
SaiSuite — CRM: Dashboard + Forecast Services
"""
import logging
from decimal import Decimal
from datetime import date, timedelta
from django.db.models import Sum, Count, Q, Avg, F
from django.utils import timezone

from .models import CrmOportunidad, CrmLead, CrmActividad, CrmCotizacion

logger = logging.getLogger(__name__)


class CrmDashboardService:

    @staticmethod
    def get_metricas(company, *, periodo_dias=30, pipeline_id=None, asignado_a=None):
        """
        Retorna todas las métricas del dashboard CRM.
        """
        fecha_inicio = timezone.now() - timedelta(days=periodo_dias)
        qs_base = CrmOportunidad.all_objects.filter(company=company)

        if pipeline_id:
            qs_base = qs_base.filter(pipeline_id=pipeline_id)
        if asignado_a:
            qs_base = qs_base.filter(asignado_a_id=asignado_a)

        # Oportunidades activas (no ganadas, no perdidas)
        qs_activas = qs_base.filter(etapa__es_ganado=False, etapa__es_perdido=False)
        qs_ganadas = qs_base.filter(etapa__es_ganado=True, ganada_en__gte=fecha_inicio)
        qs_perdidas = qs_base.filter(etapa__es_perdido=True, perdida_en__gte=fecha_inicio)

        # Ingresos del período
        ingresos_periodo = qs_ganadas.aggregate(t=Sum('valor_esperado'))['t'] or Decimal('0')

        # Forecast: suma(valor_esperado × probabilidad_etapa) de activas
        forecast = Decimal('0')
        for op in qs_activas.select_related('etapa'):
            forecast += op.valor_esperado * (op.etapa.probabilidad / 100)

        # Actividades vencidas (pendientes con fecha pasada)
        actividades_vencidas = CrmActividad.all_objects.filter(
            company=company,
            completada=False,
            fecha_programada__lt=timezone.now(),
        ).count()

        # Leads del período
        leads_periodo = CrmLead.all_objects.filter(
            company=company, created_at__gte=fecha_inicio
        ).count()
        leads_convertidos = CrmLead.all_objects.filter(
            company=company, convertido=True, convertido_en__gte=fecha_inicio
        ).count()
        tasa_conversion = (
            round(leads_convertidos / leads_periodo * 100, 1) if leads_periodo > 0 else 0
        )

        # Funnel por etapa
        funnel = CrmDashboardService.get_funnel(company, pipeline_id=pipeline_id)

        # Rendimiento por vendedor
        rendimiento = CrmDashboardService.get_rendimiento_vendedores(company, fecha_inicio=fecha_inicio)

        return {
            'periodo_dias':          periodo_dias,
            'oportunidades_activas': qs_activas.count(),
            'oportunidades_ganadas': qs_ganadas.count(),
            'oportunidades_perdidas': qs_perdidas.count(),
            'ingresos_periodo':      ingresos_periodo,
            'forecast':              forecast,
            'actividades_vencidas':  actividades_vencidas,
            'leads_periodo':         leads_periodo,
            'leads_convertidos':     leads_convertidos,
            'tasa_conversion':       tasa_conversion,
            'funnel':                funnel,
            'rendimiento_vendedores': rendimiento,
        }

    @staticmethod
    def get_funnel(company, pipeline_id=None):
        """Oportunidades y valor total por etapa (para gráfico funnel)."""
        from .models import CrmEtapa
        qs = CrmEtapa.all_objects.filter(pipeline__company=company)
        if pipeline_id:
            qs = qs.filter(pipeline_id=pipeline_id)

        resultado = []
        for etapa in qs.order_by('pipeline', 'orden'):
            ops = CrmOportunidad.all_objects.filter(company=company, etapa=etapa)
            agg = ops.aggregate(total=Sum('valor_esperado'), count=Count('id'))
            resultado.append({
                'etapa_id':    str(etapa.id),
                'etapa_nombre': etapa.nombre,
                'etapa':        etapa.nombre,
                'pipeline':     etapa.pipeline.nombre,
                'color':        etapa.color,
                'probabilidad': float(etapa.probabilidad),
                'count':        agg['count'] or 0,
                'valor_total':  float(agg['total'] or 0),
                'total_valor':  float(agg['total'] or 0),
                'es_ganado':    etapa.es_ganado,
                'es_perdido':   etapa.es_perdido,
            })
        return resultado

    @staticmethod
    def get_rendimiento_vendedores(company, fecha_inicio=None):
        """Métricas por vendedor: oportunidades, valor, ganadas, conversión."""
        from apps.users.models import User

        if fecha_inicio is None:
            fecha_inicio = timezone.now() - timedelta(days=30)

        # Solo vendedores que tienen al menos 1 oportunidad asignada
        vendedores_con_ops = (
            CrmOportunidad.all_objects
            .filter(company=company, asignado_a__isnull=False)
            .values_list('asignado_a_id', flat=True)
            .distinct()
        )
        vendedores = User.objects.filter(
            company=company, is_active=True, id__in=vendedores_con_ops
        )
        resultado = []

        for vendedor in vendedores:
            ops = CrmOportunidad.all_objects.filter(
                company=company, asignado_a=vendedor, created_at__gte=fecha_inicio
            )
            all_ops = CrmOportunidad.all_objects.filter(company=company, asignado_a=vendedor)
            ganadas = ops.filter(etapa__es_ganado=True)
            agg = all_ops.aggregate(total=Sum('valor_esperado'))
            agg_ganadas = ganadas.aggregate(total=Sum('valor_esperado'))
            total = all_ops.count()
            total_ganadas = ganadas.count()

            resultado.append({
                'vendedor_id':   str(vendedor.id),
                'vendedor':      getattr(vendedor, 'full_name', None) or vendedor.email,
                'oportunidades': total,
                'valor_total':   float(agg['total'] or 0),
                'ganadas':       total_ganadas,
                'valor_ganado':  float(agg_ganadas['total'] or 0),
                'conversion':    round(total_ganadas / total * 100, 1) if total > 0 else 0,
            })

        return sorted(resultado, key=lambda x: x['valor_ganado'], reverse=True)

    @staticmethod
    def get_forecast_detalle(company, pipeline_id=None, asignado_a=None):
        """Forecast detallado: oportunidad × probabilidad."""
        qs = CrmOportunidad.all_objects.filter(
            company=company,
            etapa__es_ganado=False,
            etapa__es_perdido=False,
        ).select_related('etapa', 'contacto', 'asignado_a')

        if pipeline_id:
            qs = qs.filter(pipeline_id=pipeline_id)
        if asignado_a:
            qs = qs.filter(asignado_a_id=asignado_a)

        resultado = []
        for op in qs.order_by('-valor_esperado'):
            resultado.append({
                'oportunidad_id':  str(op.id),
                'titulo':          op.titulo,
                'etapa':           op.etapa.nombre,
                'valor_esperado':  float(op.valor_esperado),
                'probabilidad':    float(op.etapa.probabilidad),
                'valor_ponderado': float(op.valor_ponderado),
                'fecha_cierre':    op.fecha_cierre_estimada.isoformat() if op.fecha_cierre_estimada else None,
                'asignado_a':      getattr(op.asignado_a, 'full_name', '') if op.asignado_a else '',
            })

        total_forecast = sum(r['valor_ponderado'] for r in resultado)
        return {'total_forecast': total_forecast, 'oportunidades': resultado}
