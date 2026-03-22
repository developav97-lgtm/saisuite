"""
SaiSuite — Fixtures de pytest para el módulo de Proyectos.
Extiende el conftest.py global del backend.
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest

from apps.companies.models import Company, CompanyModule
from apps.proyectos.models import Proyecto, Tarea


# ── Helpers locales ───────────────────────────────────────────────────────────

_NIT = [990_000_000]
_EMAIL = [0]


def _nit():
    _NIT[0] += 1
    return str(_NIT[0])


def _email():
    _EMAIL[0] += 1
    return f'conf_user_{_EMAIL[0]}@test.com'


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def company_con_modulo():
    """Empresa con módulo de proyectos activo."""
    from django.contrib.auth import get_user_model
    c = Company.objects.create(name='Proyectos Test Co', nit=_nit())
    CompanyModule.objects.create(company=c, module='proyectos', is_active=True)
    return c


@pytest.fixture
def user(company):
    """Sobreescribe el fixture global para asegurar role correcto."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(
        email=_email(),
        password='Pass1234!',
        company=company,
        role='company_admin',
        is_active=True,
    )


@pytest.fixture
def proyecto(company, user):
    """Proyecto en estado 'en_ejecucion' listo para crear tareas."""
    return Proyecto.all_objects.create(
        company=company,
        gerente=user,
        codigo=f'PRY-{_nit()}',
        nombre='Proyecto Test Services',
        tipo='obra_civil',
        estado='en_ejecucion',
        cliente_id='111',
        cliente_nombre='Cliente Test',
        fecha_inicio_planificada=date.today(),
        fecha_fin_planificada=date.today() + timedelta(days=90),
        presupuesto_total=Decimal('10000000.00'),
    )


@pytest.fixture
def tarea_simple(proyecto, user):
    """Tarea sin subtareas en estado 'por_hacer'."""
    return Tarea.objects.create(
        company=proyecto.company,
        proyecto=proyecto,
        nombre='Tarea simple',
        responsable=user,
        estado='por_hacer',
    )


@pytest.fixture
def tarea_con_subtareas(proyecto, tarea_simple):
    """
    Retorna tarea_simple con 3 subtareas en estado 'por_hacer'.
    El fixture se llama 'tarea_con_subtareas' para mayor claridad en los tests.
    """
    for i in range(3):
        Tarea.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            nombre=f'Subtarea {i + 1}',
            tarea_padre=tarea_simple,
            porcentaje_completado=0,
            estado='por_hacer',
        )
    tarea_simple.refresh_from_db()
    return tarea_simple
