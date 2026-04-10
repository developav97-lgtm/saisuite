"""
SaiSuite — CRM Tests: Views (integración básica)
"""
import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework.test import APIClient

from apps.crm.models import CrmPipeline, CrmEtapa, CrmLead, CrmOportunidad
from apps.companies.models import Company, CompanyModule


@pytest.fixture
def company(db):
    c = Company.objects.create(name='View Test Co', nit='900001003')
    CompanyModule.objects.create(company=c, module='crm', is_active=True)
    return c


@pytest.fixture
def admin_user(db, company):
    from apps.users.models import User
    return User.objects.create_user(
        email='admin@test.com', password='test1234',
        company=company, role='company_admin',
    )


@pytest.fixture
def seller_user(db, company):
    from apps.users.models import User
    return User.objects.create_user(
        email='seller@test.com', password='test1234',
        company=company, role='seller',
    )


@pytest.fixture
def api_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def pipeline(db, company):
    p = CrmPipeline.all_objects.create(company=company, nombre='Test Pipeline', es_default=True)
    CrmEtapa.all_objects.create(company=company, pipeline=p, nombre='Nuevo', orden=1, probabilidad=Decimal('10'))
    CrmEtapa.all_objects.create(company=company, pipeline=p, nombre='Ganado', orden=5, probabilidad=Decimal('100'), es_ganado=True)
    CrmEtapa.all_objects.create(company=company, pipeline=p, nombre='Perdido', orden=6, probabilidad=Decimal('0'), es_perdido=True)
    return p


@pytest.mark.django_db
class TestPipelineViews:

    def test_list_pipelines(self, api_client, pipeline):
        response = api_client.get('/api/v1/crm/pipelines/')
        assert response.status_code == 200
        assert len(response.data) >= 1

    def test_create_pipeline(self, api_client, company):
        response = api_client.post('/api/v1/crm/pipelines/', {'nombre': 'Nuevo Pipeline'}, format='json')
        assert response.status_code == 201
        assert response.data['nombre'] == 'Nuevo Pipeline'

    def test_kanban_view(self, api_client, pipeline):
        response = api_client.get(f'/api/v1/crm/pipelines/{pipeline.id}/kanban/')
        assert response.status_code == 200
        assert isinstance(response.data, list)


@pytest.mark.django_db
class TestLeadViews:

    def test_create_lead(self, api_client, company, pipeline):
        response = api_client.post('/api/v1/crm/leads/', {
            'nombre': 'Test Lead', 'empresa': 'Empresa X',
            'email': 'lead@empresa.com', 'fuente': 'manual',
        }, format='json')
        assert response.status_code == 201
        assert response.data['nombre'] == 'Test Lead'

    def test_list_leads(self, api_client, company):
        response = api_client.get('/api/v1/crm/leads/')
        assert response.status_code == 200

    def test_viewer_no_puede_crear(self, db, company, pipeline):
        from apps.users.models import User
        viewer = User.objects.create_user(
            email='viewer@test.com', password='test', company=company, role='viewer'
        )
        client = APIClient()
        client.force_authenticate(user=viewer)
        response = client.post('/api/v1/crm/leads/', {'nombre': 'X', 'fuente': 'manual'}, format='json')
        assert response.status_code == 403


@pytest.mark.django_db
class TestOportunidadViews:

    def test_create_oportunidad(self, api_client, company, pipeline):
        etapa = CrmEtapa.all_objects.filter(pipeline=pipeline, nombre='Nuevo').first()
        response = api_client.post('/api/v1/crm/oportunidades/', {
            'titulo': 'Op Test', 'pipeline': str(pipeline.id),
            'etapa': str(etapa.id), 'valor_esperado': '500000',
            'probabilidad': '10',
        }, format='json')
        assert response.status_code == 201

    def test_mover_etapa(self, api_client, company, pipeline):
        etapa_nuevo = CrmEtapa.all_objects.filter(pipeline=pipeline, nombre='Nuevo').first()
        etapa_ganado = CrmEtapa.all_objects.filter(pipeline=pipeline, nombre='Ganado').first()
        op = CrmOportunidad.all_objects.create(
            company=company, titulo='Test', pipeline=pipeline,
            etapa=etapa_nuevo, valor_esperado=Decimal('100000'), probabilidad=Decimal('10'),
        )
        response = api_client.post(
            f'/api/v1/crm/oportunidades/{op.id}/mover-etapa/',
            {'etapa_id': str(etapa_ganado.id)}, format='json',
        )
        assert response.status_code == 200
        op.refresh_from_db()
        assert op.etapa.es_ganado is True

    def test_ganar_oportunidad(self, api_client, company, pipeline):
        etapa_nuevo = CrmEtapa.all_objects.filter(pipeline=pipeline, nombre='Nuevo').first()
        op = CrmOportunidad.all_objects.create(
            company=company, titulo='Test', pipeline=pipeline,
            etapa=etapa_nuevo, valor_esperado=Decimal('100000'), probabilidad=Decimal('10'),
        )
        response = api_client.post(f'/api/v1/crm/oportunidades/{op.id}/ganar/')
        assert response.status_code == 200

    def test_perder_oportunidad(self, api_client, company, pipeline):
        etapa_nuevo = CrmEtapa.all_objects.filter(pipeline=pipeline, nombre='Nuevo').first()
        op = CrmOportunidad.all_objects.create(
            company=company, titulo='Test', pipeline=pipeline,
            etapa=etapa_nuevo, valor_esperado=Decimal('100000'), probabilidad=Decimal('10'),
        )
        response = api_client.post(
            f'/api/v1/crm/oportunidades/{op.id}/perder/',
            {'motivo': 'Precio muy alto'}, format='json',
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestDashboardViews:

    def test_dashboard_view(self, api_client, company):
        response = api_client.get('/api/v1/crm/dashboard/')
        assert response.status_code == 200
        assert 'forecast' in response.data
        assert 'funnel' in response.data

    def test_forecast_view(self, api_client, company):
        response = api_client.get('/api/v1/crm/dashboard/forecast/')
        assert response.status_code == 200
        assert 'total_forecast' in response.data
