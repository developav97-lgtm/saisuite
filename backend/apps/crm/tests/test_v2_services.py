"""
SaiSuite — CRM Tests v2: Sprint UX/Features
Cubre: actividades en leads, round-robin, agenda, asignación masiva.
"""
import pytest
from decimal import Decimal
from django.utils import timezone
from datetime import date, timedelta

from apps.crm.models import (
    CrmPipeline, CrmEtapa, CrmLead, CrmOportunidad, CrmActividad,
    FuenteLead, TipoActividad,
)
from apps.crm.services import LeadService, ActividadService


# ─────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────

@pytest.fixture
def company(db):
    from apps.companies.models import Company
    return Company.objects.create(name='CRM v2 Test Co', nit='900002001')


@pytest.fixture
def pipeline(db, company):
    p = CrmPipeline.all_objects.create(
        company=company, nombre='Pipeline v2', es_default=True
    )
    CrmEtapa.all_objects.create(
        company=company, pipeline=p, nombre='Nuevo', orden=1,
        probabilidad=Decimal('10'),
    )
    return p


@pytest.fixture
def lead(db, company, pipeline):
    return CrmLead.all_objects.create(
        company=company, nombre='Lead v2', empresa='Beta Corp',
        email='lead@beta.com', fuente=FuenteLead.MANUAL, pipeline=pipeline,
    )


@pytest.fixture
def lead2(db, company, pipeline):
    return CrmLead.all_objects.create(
        company=company, nombre='Lead v2 B', empresa='Gamma Corp',
        email='leadb@gamma.com', fuente=FuenteLead.WEBHOOK, pipeline=pipeline,
    )


@pytest.fixture
def seller(db, company):
    from apps.users.models import User
    return User.objects.create_user(
        email='seller_v2@crm.com', password='test1234',
        company=company, role='seller',
    )


@pytest.fixture
def seller2(db, company):
    from apps.users.models import User
    return User.objects.create_user(
        email='seller2_v2@crm.com', password='test1234',
        company=company, role='seller',
    )


@pytest.fixture
def oportunidad(db, company, pipeline):
    etapa = CrmEtapa.all_objects.filter(pipeline=pipeline).first()
    return CrmOportunidad.all_objects.create(
        company=company, titulo='Op v2',
        pipeline=pipeline, etapa=etapa,
        valor_esperado=Decimal('500000'), probabilidad=Decimal('10'),
    )


# ─────────────────────────────────────────────
# ACTIVIDADES EN LEADS
# ─────────────────────────────────────────────

@pytest.mark.django_db
class TestActividadEnLead:

    def test_create_for_lead(self, lead):
        """Crea una actividad asociada a un lead."""
        data = {
            'tipo': TipoActividad.LLAMADA,
            'titulo': 'Llamada inicial',
            'fecha_programada': timezone.now() + timedelta(hours=1),
        }
        act = ActividadService.create_for_lead(lead, data)
        assert act.lead == lead
        assert act.oportunidad is None
        assert act.titulo == 'Llamada inicial'
        assert act.tipo == TipoActividad.LLAMADA

    def test_list_for_lead(self, lead):
        """Lista actividades de un lead."""
        ActividadService.create_for_lead(lead, {
            'tipo': TipoActividad.EMAIL,
            'titulo': 'Email bienvenida',
            'fecha_programada': timezone.now() + timedelta(hours=2),
        })
        ActividadService.create_for_lead(lead, {
            'tipo': TipoActividad.LLAMADA,
            'titulo': 'Seguimiento',
            'fecha_programada': timezone.now() + timedelta(days=1),
            'completada': True,
        })
        todas = ActividadService.list_for_lead(lead)
        assert todas.count() == 2

    def test_list_for_lead_solo_pendientes(self, lead):
        """Filtra solo actividades pendientes."""
        ActividadService.create_for_lead(lead, {
            'tipo': TipoActividad.EMAIL,
            'titulo': 'Email',
            'fecha_programada': timezone.now() + timedelta(hours=2),
        })
        ActividadService.create_for_lead(lead, {
            'tipo': TipoActividad.LLAMADA,
            'titulo': 'Completada',
            'fecha_programada': timezone.now() + timedelta(days=1),
            'completada': True,
        })
        pendientes = ActividadService.list_for_lead(lead, solo_pendientes=True)
        assert pendientes.count() == 1
        assert pendientes.first().titulo == 'Email'

    def test_list_for_lead_no_muestra_oportunidad(self, lead, oportunidad):
        """Las actividades de oportunidad no aparecen en listado de lead."""
        ActividadService.create_for_lead(lead, {
            'tipo': TipoActividad.LLAMADA,
            'titulo': 'Del lead',
            'fecha_programada': timezone.now() + timedelta(hours=1),
        })
        # Actividad directamente en oportunidad
        CrmActividad.all_objects.create(
            company=lead.company,
            oportunidad=oportunidad,
            tipo=TipoActividad.REUNION,
            titulo='De la oportunidad',
            fecha_programada=timezone.now() + timedelta(hours=3),
        )
        leads_acts = ActividadService.list_for_lead(lead)
        assert leads_acts.count() == 1
        assert leads_acts.first().titulo == 'Del lead'


# ─────────────────────────────────────────────
# ROUND-ROBIN
# ─────────────────────────────────────────────

@pytest.mark.django_db
class TestRoundRobin:

    def test_asignar_round_robin_asigna_vendedor(self, lead, seller):
        """Round-robin asigna al único vendedor disponible."""
        assert lead.asignado_a is None
        resultado = LeadService.asignar_round_robin(lead)
        resultado.refresh_from_db()
        assert resultado.asignado_a == seller

    def test_asignar_round_robin_dos_vendedores_equitativo(self, lead, lead2, seller, seller2):
        """Con dos leads y dos vendedores, cada uno recibe uno."""
        r1 = LeadService.asignar_round_robin(lead)
        r2 = LeadService.asignar_round_robin(lead2)
        asignados = {r1.asignado_a_id, r2.asignado_a_id}
        # Ambos vendedores deben haber recibido uno
        assert seller.id in asignados
        assert seller2.id in asignados

    def test_asignar_round_robin_sin_vendedores_no_asigna(self, lead):
        """Sin vendedores activos, el lead queda sin asignar."""
        resultado = LeadService.asignar_round_robin(lead)
        assert resultado.asignado_a is None

    def test_asignar_masivo_round_robin(self, lead, lead2, seller):
        """Asignación masiva de todos los leads sin asignar."""
        assert lead.asignado_a is None
        assert lead2.asignado_a is None
        cantidad = LeadService.asignar_masivo_round_robin(lead.company)
        assert cantidad == 2
        lead.refresh_from_db()
        lead2.refresh_from_db()
        assert lead.asignado_a == seller
        assert lead2.asignado_a == seller

    def test_asignar_masivo_respeta_ya_asignados(self, lead, lead2, seller):
        """La asignación masiva no toca los leads ya asignados."""
        lead.asignado_a = seller
        lead.save()
        cantidad = LeadService.asignar_masivo_round_robin(lead.company)
        # Solo lead2 queda sin asignar
        assert cantidad == 1
        lead.refresh_from_db()
        assert lead.asignado_a == seller  # no cambia

    def test_private_method_delegates_to_public(self, lead, seller):
        """_asignar_round_robin es alias de asignar_round_robin."""
        r1 = LeadService._asignar_round_robin(lead)
        assert r1.asignado_a == seller
