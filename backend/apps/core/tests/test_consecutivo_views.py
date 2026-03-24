"""
SaiSuite — Tests: ConfiguracionConsecutivo ViewSet
Verifica paginación y filtros en GET /api/v1/core/consecutivos/.
"""
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.companies.models import Company
from apps.core.models import ConfiguracionConsecutivo

User = get_user_model()


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_company(nit='900000099'):
    return Company.objects.create(name='Test Co', nit=nit)


def make_user(company, email='user@test.com'):
    return User.objects.create_user(
        email=email, password='Pass1234!',
        company=company, role='company_admin', is_active=True,
    )


def make_consecutivo(company, prefijo, tipo='proyecto', activo=True, **kwargs):
    return ConfiguracionConsecutivo.all_objects.create(
        company=company,
        nombre=f'Consecutivo {prefijo}',
        tipo=tipo,
        subtipo='',
        prefijo=prefijo,
        ultimo_numero=0,
        formato='{prefijo}-{numero:04d}',
        activo=activo,
        **kwargs,
    )


LIST_URL = '/api/v1/core/consecutivos/'


# ── Tests: paginación ─────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_list_devuelve_estructura_paginada():
    """La respuesta debe tener count y results."""
    company = make_company()
    user = make_user(company)
    make_consecutivo(company, 'PRY')

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get(LIST_URL)

    assert response.status_code == 200
    data = response.json()
    assert 'count' in data
    assert 'results' in data
    assert isinstance(data['results'], list)


@pytest.mark.django_db
def test_paginacion_page_size():
    """El param page_size limita los resultados devueltos."""
    company = make_company()
    user = make_user(company)
    for i in range(10):
        make_consecutivo(company, f'P{i:02d}')

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get(LIST_URL, {'page_size': 3})

    data = response.json()
    assert data['count'] == 10
    assert len(data['results']) == 3


@pytest.mark.django_db
def test_paginacion_segunda_pagina():
    """page=2 devuelve los siguientes items."""
    company = make_company()
    user = make_user(company)
    for i in range(5):
        make_consecutivo(company, f'P{i:02d}')

    client = APIClient()
    client.force_authenticate(user=user)

    r1 = client.get(LIST_URL, {'page_size': 3, 'page': 1}).json()
    r2 = client.get(LIST_URL, {'page_size': 3, 'page': 2}).json()

    ids_p1 = {c['id'] for c in r1['results']}
    ids_p2 = {c['id'] for c in r2['results']}
    assert ids_p1.isdisjoint(ids_p2)


# ── Tests: filtros ────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_filtro_tipo():
    """El param tipo filtra por entidad."""
    company = make_company()
    user = make_user(company)
    make_consecutivo(company, 'PRY', tipo='proyecto')
    make_consecutivo(company, 'ACT', tipo='actividad')
    make_consecutivo(company, 'FAC', tipo='factura')

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get(LIST_URL, {'tipo': 'proyecto'})

    data = response.json()
    assert data['count'] == 1
    assert data['results'][0]['tipo'] == 'proyecto'


@pytest.mark.django_db
def test_filtro_activo_true():
    """El param activo=true filtra solo activos."""
    company = make_company()
    user = make_user(company)
    make_consecutivo(company, 'PRY', activo=True)
    make_consecutivo(company, 'ACT', activo=False)

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get(LIST_URL, {'activo': 'true'})

    data = response.json()
    assert data['count'] == 1
    assert data['results'][0]['activo'] is True


@pytest.mark.django_db
def test_filtro_activo_false():
    """El param activo=false filtra solo inactivos."""
    company = make_company()
    user = make_user(company)
    make_consecutivo(company, 'PRY', activo=True)
    make_consecutivo(company, 'ACT', activo=False)

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get(LIST_URL, {'activo': 'false'})

    data = response.json()
    assert data['count'] == 1
    assert data['results'][0]['activo'] is False


@pytest.mark.django_db
def test_filtro_search_por_prefijo():
    """El param search encuentra por prefijo."""
    company = make_company()
    user = make_user(company)
    make_consecutivo(company, 'PRY', tipo='proyecto')
    make_consecutivo(company, 'ACT', tipo='actividad')

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get(LIST_URL, {'search': 'PRY'})

    data = response.json()
    assert data['count'] == 1
    assert data['results'][0]['prefijo'] == 'PRY'


@pytest.mark.django_db
def test_aislamiento_entre_companies():
    """Un usuario solo ve los consecutivos de su propia company."""
    company_a = make_company(nit='900000091')
    company_b = make_company(nit='900000092')
    user_a = make_user(company_a, email='a@test.com')
    make_consecutivo(company_a, 'PRY')
    make_consecutivo(company_b, 'PRY')

    client = APIClient()
    client.force_authenticate(user=user_a)
    data = client.get(LIST_URL).json()

    assert data['count'] == 1
    assert data['results'][0]['prefijo'] == 'PRY'


@pytest.mark.django_db
def test_sin_autenticacion_retorna_401():
    client = APIClient()
    response = client.get(LIST_URL)
    assert response.status_code == 401
