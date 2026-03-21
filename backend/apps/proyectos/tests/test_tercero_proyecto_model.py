"""
SaiSuite — Tests: TerceroProyecto model
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.db import IntegrityError
from django.contrib.auth import get_user_model

from apps.companies.models import Company, CompanyModule
from apps.proyectos.models import Proyecto, Fase, TerceroProyecto, RolTercero

User = get_user_model()


def make_company(nit='905001001'):
    c = Company.objects.create(name='TP Test Co', nit=nit)
    CompanyModule.objects.create(company=c, module='proyectos', is_active=True)
    return c


def make_user(company, email='gtp@test.com'):
    return User.objects.create_user(
        email=email, password='Pass1234!', company=company, role='company_admin', is_active=True
    )


def make_proyecto(company, gerente, codigo='TP-PRY-001'):
    return Proyecto.all_objects.create(
        company=company, gerente=gerente, codigo=codigo,
        nombre='TP Proyecto', tipo='obra_civil',
        cliente_id='111', cliente_nombre='C',
        fecha_inicio_planificada=date.today(),
        fecha_fin_planificada=date.today() + timedelta(days=90),
        presupuesto_total=Decimal('5000000.00'),
    )


def make_fase(proyecto, orden=1):
    return Fase.all_objects.create(
        company=proyecto.company,
        proyecto=proyecto, nombre=f'Fase {orden}', orden=orden,
        fecha_inicio_planificada=date.today(),
        fecha_fin_planificada=date.today() + timedelta(days=60),
    )


def make_tp(proyecto, tercero_id='900111222', rol='cliente', fase=None, **kwargs):
    return TerceroProyecto.all_objects.create(
        company=proyecto.company,
        proyecto=proyecto,
        tercero_id=tercero_id,
        tercero_nombre='Tercero SA',
        rol=rol,
        fase=fase,
        **kwargs,
    )


@pytest.mark.django_db
class TestTerceroProyectoModel:

    def test_crear_tercero_proyecto(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        tp = make_tp(p)
        assert tp.id is not None
        assert tp.proyecto_id == p.id

    def test_activo_por_defecto_true(self):
        c = make_company('905001002')
        g = make_user(c, 'gtp2@test.com')
        p = make_proyecto(c, g, 'TP-PRY-002')
        tp = make_tp(p)
        assert tp.activo is True

    def test_fase_es_opcional(self):
        c = make_company('905001003')
        g = make_user(c, 'gtp3@test.com')
        p = make_proyecto(c, g, 'TP-PRY-003')
        tp = make_tp(p, fase=None)
        assert tp.fase is None

    def test_tercero_fk_es_opcional(self):
        c = make_company('905001004')
        g = make_user(c, 'gtp4@test.com')
        p = make_proyecto(c, g, 'TP-PRY-004')
        tp = make_tp(p)
        assert tp.tercero_fk is None

    def test_roles_disponibles(self):
        roles = [r.value for r in RolTercero]
        assert 'cliente' in roles
        assert 'subcontratista' in roles
        assert 'proveedor' in roles
        assert 'consultor' in roles
        assert 'interventor' in roles
        assert 'supervisor' in roles

    def test_mismo_tercero_multiples_roles_en_proyecto(self):
        c = make_company('905001005')
        g = make_user(c, 'gtp5@test.com')
        p = make_proyecto(c, g, 'TP-PRY-005')
        make_tp(p, '900111222', rol='cliente')
        make_tp(p, '900111222', rol='proveedor')
        assert TerceroProyecto.all_objects.filter(
            proyecto=p, tercero_id='900111222'
        ).count() == 2

    def test_unique_together_proyecto_tercero_rol_fase_con_fase(self):
        """Con fase concreta, (proyecto, tercero_id, rol, fase) es unique."""
        c = make_company('905001006')
        g = make_user(c, 'gtp6@test.com')
        p = make_proyecto(c, g, 'TP-PRY-006')
        f = make_fase(p, orden=1)
        make_tp(p, '900111333', rol='cliente', fase=f)
        with pytest.raises(IntegrityError):
            TerceroProyecto.all_objects.create(
                company=c, proyecto=p,
                tercero_id='900111333', tercero_nombre='X',
                rol='cliente', fase=f,
            )

    def test_mismo_rol_en_diferente_fase(self):
        c = make_company('905001007')
        g = make_user(c, 'gtp7@test.com')
        p = make_proyecto(c, g, 'TP-PRY-007')
        f1 = make_fase(p, orden=1)
        f2 = make_fase(p, orden=2)
        tp1 = make_tp(p, '900111444', rol='subcontratista', fase=f1)
        tp2 = make_tp(p, '900111444', rol='subcontratista', fase=f2)
        assert tp1.id != tp2.id

    def test_tercero_cliente_en_un_proyecto_proveedor_en_otro(self):
        c = make_company('905001008')
        g = make_user(c, 'gtp8@test.com')
        p1 = make_proyecto(c, g, 'TP-PRY-008A')
        p2 = make_proyecto(c, g, 'TP-PRY-008B')
        tp1 = make_tp(p1, '900222333', rol='cliente')
        tp2 = make_tp(p2, '900222333', rol='proveedor')
        assert tp1.rol == 'cliente'
        assert tp2.rol == 'proveedor'

    def test_str_incluye_nombre_rol_y_codigo_proyecto(self):
        c = make_company('905001009')
        g = make_user(c, 'gtp9@test.com')
        p = make_proyecto(c, g, 'TP-PRY-009')
        tp = make_tp(p, rol='cliente')
        s = str(tp)
        assert 'Tercero SA' in s
        assert 'Cliente' in s
        assert 'TP-PRY-009' in s

    def test_company_fk(self):
        c = make_company('905001010')
        g = make_user(c, 'gtp10@test.com')
        p = make_proyecto(c, g, 'TP-PRY-010')
        tp = make_tp(p)
        assert tp.company_id == c.id
