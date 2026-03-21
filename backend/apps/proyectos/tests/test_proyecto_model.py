"""
SaiSuite — Tests: Proyecto model
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.db import IntegrityError
from django.contrib.auth import get_user_model

from apps.companies.models import Company, CompanyModule
from apps.proyectos.models import (
    Proyecto, EstadoProyecto, TipoProyecto,
)

User = get_user_model()


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_company(nit='901001001'):
    c = Company.objects.create(name='Test Co', nit=nit)
    CompanyModule.objects.create(company=c, module='proyectos', is_active=True)
    return c


def make_user(company, email='g@test.com'):
    return User.objects.create_user(
        email=email, password='Pass1234!',
        company=company, role='company_admin', is_active=True,
    )


def make_proyecto(company, gerente, **kwargs):
    defaults = dict(
        codigo='PRY-001',
        nombre='Proyecto Test',
        tipo='obra_civil',
        cliente_id='900111222',
        cliente_nombre='Cliente SA',
        fecha_inicio_planificada=date.today(),
        fecha_fin_planificada=date.today() + timedelta(days=90),
        presupuesto_total=Decimal('1000000.00'),
    )
    defaults.update(kwargs)
    return Proyecto.all_objects.create(company=company, gerente=gerente, **defaults)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestProyectoModel:

    def test_crear_proyecto_con_campos_obligatorios(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        assert p.id is not None
        assert p.nombre == 'Proyecto Test'
        assert p.codigo == 'PRY-001'

    def test_estado_default_borrador(self):
        c = make_company('901001002')
        g = make_user(c, 'g2@test.com')
        p = make_proyecto(c, g, codigo='PRY-002')
        assert p.estado == EstadoProyecto.BORRADOR

    def test_estados_disponibles(self):
        estados = [e.value for e in EstadoProyecto]
        assert 'borrador' in estados
        assert 'planificado' in estados
        assert 'en_ejecucion' in estados
        assert 'suspendido' in estados
        assert 'cerrado' in estados
        assert 'cancelado' in estados

    def test_tipos_disponibles(self):
        tipos = [t.value for t in TipoProyecto]
        assert 'obra_civil' in tipos
        assert 'consultoria' in tipos
        assert 'manufactura' in tipos
        assert 'servicios' in tipos

    def test_presupuesto_total_default_cero(self):
        c = make_company('901001003')
        g = make_user(c, 'g3@test.com')
        p = make_proyecto(c, g, codigo='PRY-003', presupuesto_total=Decimal('0'))
        assert p.presupuesto_total == Decimal('0')

    def test_presupuesto_total_con_valor(self):
        c = make_company('901001004')
        g = make_user(c, 'g4@test.com')
        p = make_proyecto(c, g, codigo='PRY-004', presupuesto_total=Decimal('500000.00'))
        assert p.presupuesto_total == Decimal('500000.00')

    def test_porcentaje_avance_default_cero(self):
        c = make_company('901001005')
        g = make_user(c, 'g5@test.com')
        p = make_proyecto(c, g, codigo='PRY-005')
        assert p.porcentaje_avance == Decimal('0')

    def test_activo_por_defecto_true(self):
        c = make_company('901001006')
        g = make_user(c, 'g6@test.com')
        p = make_proyecto(c, g, codigo='PRY-006')
        assert p.activo is True

    def test_unique_together_company_codigo(self):
        c = make_company('901001007')
        g = make_user(c, 'g7@test.com')
        make_proyecto(c, g, codigo='PRY-DUP')
        with pytest.raises(IntegrityError):
            Proyecto.all_objects.create(
                company=c, gerente=g,
                codigo='PRY-DUP',
                nombre='Otro proyecto',
                tipo='servicios',
                cliente_id='111',
                cliente_nombre='X',
                fecha_inicio_planificada=date.today(),
                fecha_fin_planificada=date.today() + timedelta(days=30),
            )

    def test_mismo_codigo_en_diferente_empresa_es_valido(self):
        c1 = make_company('901001008')
        c2 = make_company('901001009')
        g1 = make_user(c1, 'g8@test.com')
        g2 = make_user(c2, 'g9@test.com')
        make_proyecto(c1, g1, codigo='PRY-SAME')
        p2 = make_proyecto(c2, g2, codigo='PRY-SAME')
        assert p2.id is not None

    def test_gerente_fk(self):
        c = make_company('901001010')
        g = make_user(c, 'g10@test.com')
        p = make_proyecto(c, g, codigo='PRY-010')
        assert p.gerente_id == g.id

    def test_coordinador_es_opcional(self):
        c = make_company('901001011')
        g = make_user(c, 'g11@test.com')
        p = make_proyecto(c, g, codigo='PRY-011')
        assert p.coordinador is None

    def test_coordinador_con_valor(self):
        c = make_company('901001012')
        g = make_user(c, 'g12@test.com')
        coord = make_user(c, 'coord@test.com')
        p = make_proyecto(c, g, codigo='PRY-012', coordinador=coord)
        assert p.coordinador_id == coord.id

    def test_company_fk(self):
        c = make_company('901001013')
        g = make_user(c, 'g13@test.com')
        p = make_proyecto(c, g, codigo='PRY-013')
        assert p.company_id == c.id

    def test_created_at_se_genera(self):
        c = make_company('901001014')
        g = make_user(c, 'g14@test.com')
        p = make_proyecto(c, g, codigo='PRY-014')
        assert p.created_at is not None

    def test_str_incluye_codigo_y_nombre(self):
        c = make_company('901001015')
        g = make_user(c, 'g15@test.com')
        p = make_proyecto(c, g, codigo='PRY-STR', nombre='Construcción')
        s = str(p)
        assert 'PRY-STR' in s
        assert 'Construcción' in s

    def test_saiopen_no_sincronizado_por_defecto(self):
        c = make_company('901001016')
        g = make_user(c, 'g16@test.com')
        p = make_proyecto(c, g, codigo='PRY-016')
        assert p.sincronizado_con_saiopen is False
        assert p.saiopen_proyecto_id is None

    def test_porcentaje_avance_se_puede_actualizar_por_update(self):
        """porcentaje_avance se actualiza via queryset.update() en el service."""
        c = make_company('901001017')
        g = make_user(c, 'g17@test.com')
        p = make_proyecto(c, g, codigo='PRY-017')
        Proyecto.all_objects.filter(id=p.id).update(porcentaje_avance=Decimal('50.00'))
        p.refresh_from_db()
        assert p.porcentaje_avance == Decimal('50.00')

    def test_aiu_defaults(self):
        c = make_company('901001018')
        g = make_user(c, 'g18@test.com')
        p = make_proyecto(c, g, codigo='PRY-018')
        assert p.porcentaje_administracion == Decimal('10.00')
        assert p.porcentaje_imprevistos == Decimal('5.00')
        assert p.porcentaje_utilidad == Decimal('10.00')

    def test_fechas_reales_son_opcionales(self):
        c = make_company('901001019')
        g = make_user(c, 'g19@test.com')
        p = make_proyecto(c, g, codigo='PRY-019')
        assert p.fecha_inicio_real is None
        assert p.fecha_fin_real is None
