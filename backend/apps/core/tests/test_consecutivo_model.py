"""
SaiSuite — Tests: ConfiguracionConsecutivo model
Verifica la restricción unique_together(company, prefijo).
"""
import pytest
from django.db import IntegrityError

from apps.companies.models import Company
from apps.core.models import ConfiguracionConsecutivo


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_company(nit='900000001'):
    return Company.objects.create(name='Test Co', nit=nit)


def make_consecutivo(company, prefijo='PRY', tipo='proyecto', **kwargs):
    defaults = dict(
        nombre=f'Consecutivo {prefijo}',
        tipo=tipo,
        subtipo='',
        prefijo=prefijo,
        ultimo_numero=0,
        formato='{prefijo}-{numero:04d}',
        activo=True,
    )
    defaults.update(kwargs)
    return ConfiguracionConsecutivo.all_objects.create(company=company, **defaults)


# ── Tests: unique_together(company, prefijo) ──────────────────────────────────

@pytest.mark.django_db
def test_mismo_prefijo_misma_company_falla():
    """Dos consecutivos con el mismo prefijo en la misma company deben lanzar IntegrityError."""
    company = make_company()
    make_consecutivo(company, prefijo='PRY')

    with pytest.raises(IntegrityError):
        make_consecutivo(company, prefijo='PRY', nombre='Duplicado')


@pytest.mark.django_db
def test_mismo_prefijo_diferente_company_pasa():
    """El mismo prefijo en companies distintas es válido."""
    company_a = make_company(nit='900000001')
    company_b = make_company(nit='900000002')

    c1 = make_consecutivo(company_a, prefijo='PRY')
    c2 = make_consecutivo(company_b, prefijo='PRY')

    assert c1.prefijo == c2.prefijo
    assert c1.company != c2.company


@pytest.mark.django_db
def test_prefijos_diferentes_misma_company_pasan():
    """Prefijos distintos dentro de la misma company son válidos."""
    company = make_company()
    c1 = make_consecutivo(company, prefijo='PRY')
    c2 = make_consecutivo(company, prefijo='ACT')

    assert c1.company == c2.company
    assert c1.prefijo != c2.prefijo


@pytest.mark.django_db
def test_unique_together_ignora_tipo():
    """El tipo NO forma parte de la unicidad: mismo prefijo, distinto tipo → falla igual."""
    company = make_company()
    make_consecutivo(company, prefijo='PRY', tipo='proyecto')

    with pytest.raises(IntegrityError):
        make_consecutivo(company, prefijo='PRY', tipo='actividad')


@pytest.mark.django_db
def test_str_representation():
    """__str__ incluye tipo, nombre y prefijo."""
    company = make_company()
    c = make_consecutivo(company, prefijo='PRY', tipo='proyecto')
    assert 'PRY' in str(c)
    assert 'proyecto' in str(c)


@pytest.mark.django_db
def test_generar_preview():
    """generar_preview retorna el próximo código sin incrementar el contador."""
    company = make_company()
    c = make_consecutivo(company, prefijo='ACT', ultimo_numero=5)
    assert c.generar_preview() == 'ACT-0006'
    assert c.ultimo_numero == 5  # no se modificó
