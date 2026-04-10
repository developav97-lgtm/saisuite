"""
SaiSuite — CRM Tests v2: Views
Cubre endpoints: agenda, lead actividades, round-robin, asignar-masivo.
"""
import pytest
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APIClient

from apps.crm.models import (
    CrmPipeline, CrmEtapa, CrmLead, CrmActividad,
    FuenteLead, TipoActividad,
)
from apps.companies.models import Company, CompanyModule


# ─────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────

@pytest.fixture
def company(db):
    c = Company.objects.create(name='V2 Views Co', nit='900003001')
    CompanyModule.objects.create(company=c, module='crm', is_active=True)
    return c


@pytest.fixture
def admin_user(db, company):
    from apps.users.models import User
    return User.objects.create_user(
        email='admin_v2@test.com', password='test1234',
        company=company, role='company_admin',
    )


@pytest.fixture
def seller(db, company):
    from apps.users.models import User
    return User.objects.create_user(
        email='seller_view@test.com', password='test1234',
        company=company, role='seller',
    )


@pytest.fixture
def api_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def pipeline(db, company):
    p = CrmPipeline.all_objects.create(company=company, nombre='Test Pipeline v2', es_default=True)
    CrmEtapa.all_objects.create(
        company=company, pipeline=p, nombre='Nuevo', orden=1, probabilidad=Decimal('10')
    )
    return p


@pytest.fixture
def lead(db, company, pipeline):
    return CrmLead.all_objects.create(
        company=company, nombre='Test Lead v2', empresa='Acme',
        email='lead_v2@acme.com', fuente=FuenteLead.MANUAL, pipeline=pipeline,
    )


@pytest.fixture
def actividad_lead(db, company, lead):
    return CrmActividad.all_objects.create(
        company=company, lead=lead,
        tipo=TipoActividad.LLAMADA, titulo='Llamada test',
        fecha_programada=timezone.now() + timedelta(hours=2),
    )


# ─────────────────────────────────────────────
# ACTIVIDADES EN LEAD — endpoints
# ─────────────────────────────────────────────

@pytest.mark.django_db
class TestLeadActividadesViews:

    def test_list_actividades_lead(self, api_client, lead, actividad_lead):
        url = f'/api/v1/crm/leads/{lead.id}/actividades/'
        response = api_client.get(url)
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['titulo'] == 'Llamada test'

    def test_list_actividades_lead_vacio(self, api_client, lead):
        url = f'/api/v1/crm/leads/{lead.id}/actividades/'
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.data == []

    def test_crear_actividad_lead(self, api_client, lead):
        url = f'/api/v1/crm/leads/{lead.id}/actividades/'
        payload = {
            'tipo': 'llamada',
            'titulo': 'Nueva llamada',
            'fecha_programada': (timezone.now() + timedelta(days=1)).isoformat(),
        }
        response = api_client.post(url, payload, format='json')
        assert response.status_code == 201
        assert response.data['titulo'] == 'Nueva llamada'
        assert str(response.data['lead']) == str(lead.id)

    def test_crear_actividad_lead_tipo_invalido(self, api_client, lead):
        url = f'/api/v1/crm/leads/{lead.id}/actividades/'
        payload = {
            'tipo': 'tipo_invalido',
            'titulo': 'Inválida',
            'fecha_programada': (timezone.now() + timedelta(days=1)).isoformat(),
        }
        response = api_client.post(url, payload, format='json')
        assert response.status_code == 400

    def test_list_actividades_solo_pendientes(self, api_client, lead, company):
        # Actividad pendiente
        CrmActividad.all_objects.create(
            company=company, lead=lead, tipo=TipoActividad.EMAIL,
            titulo='Pendiente', fecha_programada=timezone.now() + timedelta(hours=1),
        )
        # Actividad completada
        CrmActividad.all_objects.create(
            company=company, lead=lead, tipo=TipoActividad.LLAMADA,
            titulo='Completada', fecha_programada=timezone.now() + timedelta(hours=2),
            completada=True,
        )
        url = f'/api/v1/crm/leads/{lead.id}/actividades/?solo_pendientes=true'
        response = api_client.get(url)
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['titulo'] == 'Pendiente'


# ─────────────────────────────────────────────
# ROUND-ROBIN — endpoints
# ─────────────────────────────────────────────

@pytest.mark.django_db
class TestRoundRobinViews:

    def test_round_robin_single_lead(self, api_client, lead, seller):
        url = f'/api/v1/crm/leads/{lead.id}/round-robin/'
        response = api_client.post(url, {}, format='json')
        assert response.status_code == 200
        # asignado_a es el objeto UserMinSerializer, o None
        assert response.data['asignado_a'] is not None
        assert response.data['asignado_a_nombre'] is not None

    def test_round_robin_sin_vendedores(self, api_client, lead):
        """Sin vendedores activos retorna el lead sin asignar (200 OK)."""
        url = f'/api/v1/crm/leads/{lead.id}/round-robin/'
        response = api_client.post(url, {}, format='json')
        assert response.status_code == 200
        assert response.data['asignado_a'] is None
        assert response.data['asignado_a_nombre'] is None

    def test_round_robin_lead_no_encontrado(self, api_client):
        import uuid
        url = f'/api/v1/crm/leads/{uuid.uuid4()}/round-robin/'
        response = api_client.post(url, {}, format='json')
        assert response.status_code == 404

    def test_asignar_masivo(self, api_client, lead, seller):
        """Asignación masiva retorna conteo."""
        url = '/api/v1/crm/leads/asignar-masivo/'
        response = api_client.post(url, {}, format='json')
        assert response.status_code == 200
        assert 'asignados' in response.data
        assert response.data['asignados'] >= 1

    def test_asignar_masivo_sin_leads(self, api_client):
        """Sin leads retorna asignados=0."""
        url = '/api/v1/crm/leads/asignar-masivo/'
        response = api_client.post(url, {}, format='json')
        assert response.status_code == 200
        assert response.data['asignados'] == 0


# ─────────────────────────────────────────────
# AGENDA — endpoint
# ─────────────────────────────────────────────

@pytest.mark.django_db
class TestAgendaView:

    def _today_str(self):
        return timezone.now().date().isoformat()

    def _next_week_str(self):
        return (timezone.now().date() + timedelta(days=7)).isoformat()

    def test_agenda_basica(self, api_client, company, lead, actividad_lead):
        url = f'/api/v1/crm/agenda/?fecha_desde={self._today_str()}&fecha_hasta={self._next_week_str()}'
        response = api_client.get(url)
        assert response.status_code == 200
        assert isinstance(response.data, list)
        assert len(response.data) >= 1

    def test_agenda_contexto_lead(self, api_client, company, lead, actividad_lead):
        url = f'/api/v1/crm/agenda/?fecha_desde={self._today_str()}&fecha_hasta={self._next_week_str()}'
        response = api_client.get(url)
        assert response.status_code == 200
        act = response.data[0]
        assert 'contexto_tipo' in act
        assert 'contexto_nombre' in act
        assert act['contexto_tipo'] == 'lead'

    def test_agenda_filtro_solo_pendientes(self, api_client, company, lead):
        # Actividad pendiente
        CrmActividad.all_objects.create(
            company=company, lead=lead, tipo=TipoActividad.LLAMADA,
            titulo='Pendiente', fecha_programada=timezone.now() + timedelta(hours=3),
        )
        # Actividad completada
        CrmActividad.all_objects.create(
            company=company, lead=lead, tipo=TipoActividad.EMAIL,
            titulo='Completada', fecha_programada=timezone.now() + timedelta(hours=4),
            completada=True,
        )
        url = f'/api/v1/crm/agenda/?fecha_desde={self._today_str()}&fecha_hasta={self._next_week_str()}&solo_pendientes=true'
        response = api_client.get(url)
        assert response.status_code == 200
        titulos = [a['titulo'] for a in response.data]
        assert 'Pendiente' in titulos
        assert 'Completada' not in titulos

    def test_agenda_sin_rango_fechas(self, api_client):
        """Sin parámetros de fecha retorna 200 (no error)."""
        response = api_client.get('/api/v1/crm/agenda/')
        assert response.status_code == 200

    def test_agenda_aislamiento_empresa(self, api_client, company, lead):
        """Las actividades de otra empresa no aparecen."""
        from apps.companies.models import Company
        otra_empresa = Company.objects.create(name='Otra Co', nit='900009009')
        otro_lead = CrmLead.all_objects.create(
            company=otra_empresa, nombre='Otro Lead',
            email='otro@co.com', fuente=FuenteLead.MANUAL,
        )
        CrmActividad.all_objects.create(
            company=otra_empresa, lead=otro_lead, tipo=TipoActividad.EMAIL,
            titulo='De otra empresa', fecha_programada=timezone.now() + timedelta(hours=5),
        )
        url = f'/api/v1/crm/agenda/?fecha_desde={self._today_str()}&fecha_hasta={self._next_week_str()}'
        response = api_client.get(url)
        assert response.status_code == 200
        titulos = [a['titulo'] for a in response.data]
        assert 'De otra empresa' not in titulos
