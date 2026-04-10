"""
SaiSuite — CRM Tests: Services
Cobertura ≥80% en services.py
"""
import pytest
from decimal import Decimal
from django.utils import timezone
from unittest.mock import patch, MagicMock

from apps.crm.models import (
    CrmPipeline, CrmEtapa, CrmLead, CrmLeadScoringRule,
    CrmOportunidad, CrmActividad, CrmTimelineEvent,
    FuenteLead, TipoActividad, TipoTimelineEvent,
)
from apps.crm.services import (
    PipelineService, EtapaService, LeadService, LeadScoringService,
    OportunidadService, ActividadService, TimelineService,
)


# ─────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────

@pytest.fixture
def company(db):
    from apps.companies.models import Company
    return Company.objects.create(name='Test CRM Co', nit='900001001')


@pytest.fixture
def pipeline(db, company):
    return CrmPipeline.all_objects.create(
        company=company, nombre='Pipeline Principal', es_default=True
    )


@pytest.fixture
def etapa_nuevo(db, pipeline):
    return CrmEtapa.all_objects.create(
        company=pipeline.company, pipeline=pipeline,
        nombre='Nuevo', orden=1, probabilidad=Decimal('10'),
    )


@pytest.fixture
def etapa_ganado(db, pipeline):
    return CrmEtapa.all_objects.create(
        company=pipeline.company, pipeline=pipeline,
        nombre='Ganado', orden=5, probabilidad=Decimal('100'),
        es_ganado=True,
    )


@pytest.fixture
def etapa_perdido(db, pipeline):
    return CrmEtapa.all_objects.create(
        company=pipeline.company, pipeline=pipeline,
        nombre='Perdido', orden=6, probabilidad=Decimal('0'),
        es_perdido=True,
    )


@pytest.fixture
def lead(db, company, pipeline):
    return CrmLead.all_objects.create(
        company=company, nombre='Juan Pérez', empresa='ACME',
        email='juan@acme.com', fuente=FuenteLead.MANUAL, pipeline=pipeline,
    )


@pytest.fixture
def oportunidad(db, company, pipeline, etapa_nuevo):
    return CrmOportunidad.all_objects.create(
        company=company, titulo='Venta ACME',
        pipeline=pipeline, etapa=etapa_nuevo,
        valor_esperado=Decimal('1000000'), probabilidad=Decimal('10'),
    )


# ─────────────────────────────────────────────
# PIPELINE SERVICE
# ─────────────────────────────────────────────

@pytest.mark.django_db
class TestPipelineService:

    def test_create_pipeline(self, company):
        pipeline = PipelineService.create(company, {'nombre': 'Ventas B2B', 'es_default': True})
        assert pipeline.nombre == 'Ventas B2B'
        assert pipeline.company == company
        assert pipeline.es_default is True

    def test_solo_un_default_por_empresa(self, company, pipeline):
        pipeline2 = PipelineService.create(company, {'nombre': 'Pipeline 2', 'es_default': True})
        pipeline.refresh_from_db()
        assert pipeline.es_default is False
        assert pipeline2.es_default is True

    def test_delete_con_oportunidades_falla(self, pipeline, oportunidad):
        with pytest.raises(ValueError, match='oportunidades activas'):
            PipelineService.delete(pipeline)

    def test_get_kanban_agrupa_por_etapa(self, pipeline, etapa_nuevo, oportunidad):
        kanban = PipelineService.get_kanban(pipeline)
        etapas_con_ops = [k for k in kanban if k['total_count'] > 0]
        assert len(etapas_con_ops) >= 1
        assert etapas_con_ops[0]['total_valor'] == Decimal('1000000')


# ─────────────────────────────────────────────
# LEAD SCORING SERVICE
# ─────────────────────────────────────────────

@pytest.mark.django_db
class TestLeadScoringService:

    def test_scoring_campo_not_empty(self, company, lead):
        CrmLeadScoringRule.all_objects.create(
            company=company, nombre='Tiene empresa', campo='empresa',
            operador='not_empty', valor='', puntos=20, orden=1,
        )
        score = LeadScoringService.calcular_score(lead)
        assert score >= 20

    def test_scoring_campo_eq_fuente(self, company, lead):
        CrmLeadScoringRule.all_objects.create(
            company=company, nombre='Fuente manual', campo='fuente',
            operador='eq', valor='manual', puntos=15, orden=1,
        )
        score = LeadScoringService.calcular_score(lead)
        assert score >= 15

    def test_scoring_max_100(self, company, lead):
        for i in range(10):
            CrmLeadScoringRule.all_objects.create(
                company=company, nombre=f'Regla {i}', campo='empresa',
                operador='not_empty', valor='', puntos=20, orden=i,
            )
        score = LeadScoringService.calcular_score(lead)
        assert score <= 100


# ─────────────────────────────────────────────
# LEAD SERVICE
# ─────────────────────────────────────────────

@pytest.mark.django_db
class TestLeadService:

    def test_create_lead(self, company):
        lead = LeadService.create(company, {
            'nombre': 'María García', 'empresa': 'Corp SA',
            'email': 'mg@corp.com', 'fuente': FuenteLead.MANUAL,
        })
        assert lead.id is not None
        assert lead.nombre == 'María García'

    def test_importar_csv(self, company):
        registros = [
            {'nombre': 'Lead 1', 'empresa': 'Corp A', 'email': 'a@a.com'},
            {'nombre': 'Lead 2', 'empresa': 'Corp B', 'email': 'b@b.com'},
            {'nombre': '',       'empresa': 'Sin nombre', 'email': ''},  # error
        ]
        resultado = LeadService.importar_csv(company, registros)
        assert resultado['creados'] == 2
        assert len(resultado['errores']) == 1

    def test_convertir_lead(self, company, lead, pipeline, etapa_nuevo):
        oportunidad = LeadService.convertir(lead, {
            'etapa_id': str(etapa_nuevo.id),
            'valor_esperado': Decimal('500000'),
        })
        lead.refresh_from_db()
        assert lead.convertido is True
        assert lead.oportunidad == oportunidad
        assert oportunidad.titulo == lead.empresa or oportunidad.titulo == lead.nombre

    def test_convertir_lead_ya_convertido_falla(self, company, lead, etapa_nuevo):
        LeadService.convertir(lead, {'etapa_id': str(etapa_nuevo.id)})
        lead.refresh_from_db()
        with pytest.raises(ValueError, match='ya fue convertido'):
            LeadService.convertir(lead, {'etapa_id': str(etapa_nuevo.id)})

    def test_webhook_crea_lead(self, company):
        lead = LeadService.create_from_webhook(company, {
            'nombre': 'Web Lead', 'empresa': 'Web Corp',
            'email': 'web@corp.com', 'telefono': '3001234567',
        })
        assert lead.fuente == FuenteLead.WEBHOOK
        assert lead.nombre == 'Web Lead'


# ─────────────────────────────────────────────
# OPORTUNIDAD SERVICE
# ─────────────────────────────────────────────

@pytest.mark.django_db
class TestOportunidadService:

    def test_create_oportunidad(self, company, pipeline, etapa_nuevo):
        op = OportunidadService.create(company, {
            'titulo': 'Nueva Oportunidad',
            'pipeline': pipeline,
            'etapa': etapa_nuevo,
            'valor_esperado': Decimal('2000000'),
            'probabilidad': Decimal('10'),
        })
        assert op.titulo == 'Nueva Oportunidad'
        assert op.valor_ponderado == Decimal('200000')

    def test_mover_etapa_registra_timeline(self, company, oportunidad, etapa_ganado):
        OportunidadService.mover_etapa(oportunidad, str(etapa_ganado.id))
        oportunidad.refresh_from_db()
        assert oportunidad.etapa == etapa_ganado
        eventos = CrmTimelineEvent.all_objects.filter(oportunidad=oportunidad, tipo=TipoTimelineEvent.CAMBIO_ETAPA)
        assert eventos.exists()

    def test_ganar_oportunidad(self, company, oportunidad, etapa_ganado):
        OportunidadService.ganar(oportunidad)
        oportunidad.refresh_from_db()
        assert oportunidad.etapa.es_ganado is True
        assert oportunidad.ganada_en is not None

    def test_ganar_sin_etapa_ganado_falla(self, company, pipeline, etapa_nuevo):
        op = OportunidadService.create(company, {
            'titulo': 'Test', 'pipeline': pipeline,
            'etapa': etapa_nuevo, 'valor_esperado': Decimal('0'), 'probabilidad': Decimal('0'),
        })
        with pytest.raises(ValueError, match='etapa configurada como "Ganado"'):
            OportunidadService.ganar(op)

    def test_perder_requiere_motivo(self, company, oportunidad, etapa_perdido):
        with pytest.raises(ValueError, match='motivo'):
            OportunidadService.perder(oportunidad, motivo='')

    def test_perder_oportunidad(self, company, oportunidad, etapa_perdido):
        OportunidadService.perder(oportunidad, motivo='Precio alto')
        oportunidad.refresh_from_db()
        assert oportunidad.etapa.es_perdido is True
        assert oportunidad.motivo_perdida == 'Precio alto'


# ─────────────────────────────────────────────
# ACTIVIDAD SERVICE
# ─────────────────────────────────────────────

@pytest.mark.django_db
class TestActividadService:

    def test_create_actividad(self, company, oportunidad):
        from datetime import timedelta
        actividad = ActividadService.create(oportunidad, {
            'tipo': TipoActividad.LLAMADA,
            'titulo': 'Llamada de seguimiento',
            'fecha_programada': timezone.now() + timedelta(days=1),
        })
        assert actividad.completada is False
        oportunidad.refresh_from_db()
        assert oportunidad.proxima_actividad_tipo == TipoActividad.LLAMADA

    def test_completar_actividad_registra_timeline(self, company, oportunidad):
        from datetime import timedelta
        actividad = ActividadService.create(oportunidad, {
            'tipo': TipoActividad.REUNION,
            'titulo': 'Reunión inicial',
            'fecha_programada': timezone.now() + timedelta(days=2),
        })
        ActividadService.completar(actividad, resultado='Reunión exitosa')
        actividad.refresh_from_db()
        assert actividad.completada is True
        assert actividad.resultado == 'Reunión exitosa'

        eventos = CrmTimelineEvent.all_objects.filter(
            oportunidad=oportunidad, tipo=TipoTimelineEvent.ACTIVIDAD_COMP
        )
        assert eventos.exists()


# ─────────────────────────────────────────────
# TIMELINE SERVICE
# ─────────────────────────────────────────────

@pytest.mark.django_db
class TestTimelineService:

    def test_agregar_nota(self, company, oportunidad):
        evento = TimelineService.agregar_nota(oportunidad, 'Nota de prueba')
        assert evento.tipo == TipoTimelineEvent.NOTA
        assert evento.descripcion == 'Nota de prueba'

    def test_list_timeline_orden_descendente(self, company, oportunidad):
        TimelineService.agregar_nota(oportunidad, 'Nota 1')
        TimelineService.agregar_nota(oportunidad, 'Nota 2')
        eventos = TimelineService.list(oportunidad)
        assert eventos.count() >= 2
        # Más reciente primero
        assert eventos[0].created_at >= eventos[1].created_at
