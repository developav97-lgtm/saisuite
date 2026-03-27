"""
SaiSuite — Tests: Phase model
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.db import IntegrityError
from django.contrib.auth import get_user_model

from apps.companies.models import Company, CompanyModule
from apps.proyectos.models import Project, Phase

User = get_user_model()


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_company(nit='902001001'):
    c = Company.objects.create(name='Phase Test Co', nit=nit)
    CompanyModule.objects.create(company=c, module='proyectos', is_active=True)
    return c


def make_user(company, email='gf@test.com'):
    return User.objects.create_user(
        email=email, password='Pass1234!', company=company, role='company_admin', is_active=True
    )


def make_proyecto(company, gerente, codigo='FASE-PRY-001'):
    return Project.all_objects.create(
        company=company, gerente=gerente,
        codigo=codigo, nombre='Project Phase Test',
        tipo='civil_works',
        cliente_id='111', cliente_nombre='Cliente',
        fecha_inicio_planificada=date.today(),
        fecha_fin_planificada=date.today() + timedelta(days=180),
        presupuesto_total=Decimal('5000000.00'),
    )


def make_fase(proyecto, nombre='Phase 1', orden=1, **kwargs):
    defaults = dict(
        fecha_inicio_planificada=date.today(),
        fecha_fin_planificada=date.today() + timedelta(days=60),
    )
    defaults.update(kwargs)
    return Phase.all_objects.create(
        company=proyecto.company,
        proyecto=proyecto, nombre=nombre, orden=orden, **defaults
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestFaseModel:

    def test_crear_fase_con_campos_obligatorios(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        f = make_fase(p)
        assert f.id is not None
        assert f.nombre == 'Phase 1'

    def test_orden_default_cero(self):
        c = make_company('902001002')
        g = make_user(c, 'gf2@test.com')
        p = make_proyecto(c, g, 'FASE-PRY-002')
        f = Phase.all_objects.create(
            company=c, proyecto=p, nombre='Sin orden',
            fecha_inicio_planificada=date.today(),
            fecha_fin_planificada=date.today() + timedelta(days=30),
        )
        assert f.orden == 0

    def test_porcentaje_avance_default_cero(self):
        c = make_company('902001003')
        g = make_user(c, 'gf3@test.com')
        p = make_proyecto(c, g, 'FASE-PRY-003')
        f = make_fase(p)
        assert f.porcentaje_avance == Decimal('0')

    def test_activo_por_defecto_true(self):
        c = make_company('902001004')
        g = make_user(c, 'gf4@test.com')
        p = make_proyecto(c, g, 'FASE-PRY-004')
        f = make_fase(p)
        assert f.activo is True

    def test_descripcion_por_defecto_vacia(self):
        c = make_company('902001005')
        g = make_user(c, 'gf5@test.com')
        p = make_proyecto(c, g, 'FASE-PRY-005')
        f = make_fase(p)
        assert f.descripcion == ''

    def test_unique_together_proyecto_orden(self):
        c = make_company('902001006')
        g = make_user(c, 'gf6@test.com')
        p = make_proyecto(c, g, 'FASE-PRY-006')
        make_fase(p, orden=1)
        with pytest.raises(IntegrityError):
            Phase.all_objects.create(
                company=c, proyecto=p, nombre='Duplicada', orden=1,
                fecha_inicio_planificada=date.today(),
                fecha_fin_planificada=date.today() + timedelta(days=30),
            )

    def test_multiples_fases_diferente_orden(self):
        c = make_company('902001007')
        g = make_user(c, 'gf7@test.com')
        p = make_proyecto(c, g, 'FASE-PRY-007')
        make_fase(p, 'Phase 1', orden=1)
        make_fase(p, 'Phase 2', orden=2)
        make_fase(p, 'Phase 3', orden=3)
        count = Phase.all_objects.filter(proyecto=p).count()
        assert count == 3

    def test_ordenamiento_por_orden(self):
        c = make_company('902001008')
        g = make_user(c, 'gf8@test.com')
        p = make_proyecto(c, g, 'FASE-PRY-008')
        make_fase(p, 'Phase 3', orden=3)
        make_fase(p, 'Phase 1', orden=1)
        make_fase(p, 'Phase 2', orden=2)
        fases = list(Phase.all_objects.filter(proyecto=p))
        ordenes = [f.orden for f in fases]
        assert ordenes == sorted(ordenes)

    def test_presupuesto_campos_default_cero(self):
        c = make_company('902001009')
        g = make_user(c, 'gf9@test.com')
        p = make_proyecto(c, g, 'FASE-PRY-009')
        f = make_fase(p)
        assert f.presupuesto_mano_obra == Decimal('0')
        assert f.presupuesto_materiales == Decimal('0')
        assert f.presupuesto_subcontratos == Decimal('0')
        assert f.presupuesto_equipos == Decimal('0')
        assert f.presupuesto_otros == Decimal('0')

    def test_presupuesto_con_valores(self):
        c = make_company('902001010')
        g = make_user(c, 'gf10@test.com')
        p = make_proyecto(c, g, 'FASE-PRY-010')
        f = make_fase(
            p,
            presupuesto_mano_obra=Decimal('100000'),
            presupuesto_materiales=Decimal('200000'),
        )
        assert f.presupuesto_mano_obra == Decimal('100000')
        assert f.presupuesto_materiales == Decimal('200000')

    def test_str_incluye_codigo_orden_nombre(self):
        c = make_company('902001011')
        g = make_user(c, 'gf11@test.com')
        p = make_proyecto(c, g, 'FASE-PRY-011')
        f = make_fase(p, 'Cimentación', orden=1)
        s = str(f)
        assert 'FASE-PRY-011' in s
        assert '1' in s
        assert 'Cimentación' in s

    def test_fechas_reales_son_opcionales(self):
        c = make_company('902001012')
        g = make_user(c, 'gf12@test.com')
        p = make_proyecto(c, g, 'FASE-PRY-012')
        f = make_fase(p)
        assert f.fecha_inicio_real is None
        assert f.fecha_fin_real is None

    def test_porcentaje_avance_se_puede_actualizar(self):
        c = make_company('902001013')
        g = make_user(c, 'gf13@test.com')
        p = make_proyecto(c, g, 'FASE-PRY-013')
        f = make_fase(p)
        Phase.all_objects.filter(id=f.id).update(porcentaje_avance=Decimal('75.00'))
        f.refresh_from_db()
        assert f.porcentaje_avance == Decimal('75.00')

    def test_company_fk_desde_proyecto(self):
        c = make_company('902001014')
        g = make_user(c, 'gf14@test.com')
        p = make_proyecto(c, g, 'FASE-PRY-014')
        f = make_fase(p)
        # Phase hereda company de BaseModel
        assert f.company_id == c.id
