"""
SaiSuite — Tests: Hito model
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.contrib.auth import get_user_model

from apps.companies.models import Company, CompanyModule
from apps.proyectos.models import (
    Proyecto, Fase, DocumentoContable, Hito,
)

User = get_user_model()


def make_company(nit='907001001'):
    c = Company.objects.create(name='Hito Test Co', nit=nit)
    CompanyModule.objects.create(company=c, module='proyectos', is_active=True)
    return c


def make_user(company, email='ghito@test.com'):
    return User.objects.create_user(
        email=email, password='Pass1234!', company=company, role='company_admin', is_active=True
    )


def make_proyecto(company, gerente, codigo='HIT-PRY-001'):
    return Proyecto.all_objects.create(
        company=company, gerente=gerente, codigo=codigo,
        nombre='Hito Proyecto', tipo='obra_civil',
        cliente_id='111', cliente_nombre='C',
        fecha_inicio_planificada=date.today(),
        fecha_fin_planificada=date.today() + timedelta(days=180),
        presupuesto_total=Decimal('10000000.00'),
    )


def make_fase(proyecto, orden=1):
    return Fase.all_objects.create(
        company=proyecto.company,
        proyecto=proyecto, nombre=f'Fase {orden}', orden=orden,
        fecha_inicio_planificada=date.today(),
        fecha_fin_planificada=date.today() + timedelta(days=60),
    )


def make_hito(proyecto, nombre='Hito 1', fase=None, **kwargs):
    defaults = dict(
        porcentaje_proyecto=Decimal('25.00'),
        valor_facturar=Decimal('2500000.00'),
    )
    defaults.update(kwargs)
    return Hito.all_objects.create(
        company=proyecto.company,
        proyecto=proyecto,
        fase=fase,
        nombre=nombre,
        **defaults,
    )


@pytest.mark.django_db
class TestHitoModel:

    def test_crear_hito_con_campos_obligatorios(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        h = make_hito(p)
        assert h.id is not None
        assert h.nombre == 'Hito 1'
        assert h.proyecto_id == p.id

    def test_facturable_por_defecto_true(self):
        c = make_company('907001002')
        g = make_user(c, 'gh2@test.com')
        p = make_proyecto(c, g, 'HIT-PRY-002')
        h = make_hito(p)
        assert h.facturable is True

    def test_facturado_por_defecto_false(self):
        c = make_company('907001003')
        g = make_user(c, 'gh3@test.com')
        p = make_proyecto(c, g, 'HIT-PRY-003')
        h = make_hito(p)
        assert h.facturado is False

    def test_documento_factura_es_opcional(self):
        c = make_company('907001004')
        g = make_user(c, 'gh4@test.com')
        p = make_proyecto(c, g, 'HIT-PRY-004')
        h = make_hito(p)
        assert h.documento_factura is None

    def test_fecha_facturacion_es_opcional(self):
        c = make_company('907001005')
        g = make_user(c, 'gh5@test.com')
        p = make_proyecto(c, g, 'HIT-PRY-005')
        h = make_hito(p)
        assert h.fecha_facturacion is None

    def test_fase_es_opcional(self):
        c = make_company('907001006')
        g = make_user(c, 'gh6@test.com')
        p = make_proyecto(c, g, 'HIT-PRY-006')
        h = make_hito(p, fase=None)
        assert h.fase is None

    def test_hito_con_fase(self):
        c = make_company('907001007')
        g = make_user(c, 'gh7@test.com')
        p = make_proyecto(c, g, 'HIT-PRY-007')
        f = make_fase(p)
        h = make_hito(p, fase=f)
        assert h.fase_id == f.id

    def test_descripcion_es_opcional(self):
        c = make_company('907001008')
        g = make_user(c, 'gh8@test.com')
        p = make_proyecto(c, g, 'HIT-PRY-008')
        h = make_hito(p)
        assert h.descripcion == ''

    def test_porcentaje_proyecto_y_valor_facturar(self):
        c = make_company('907001009')
        g = make_user(c, 'gh9@test.com')
        p = make_proyecto(c, g, 'HIT-PRY-009')
        h = make_hito(p, porcentaje_proyecto=Decimal('30.00'), valor_facturar=Decimal('3000000.00'))
        assert h.porcentaje_proyecto == Decimal('30.00')
        assert h.valor_facturar == Decimal('3000000.00')

    def test_multiples_hitos_por_proyecto(self):
        c = make_company('907001010')
        g = make_user(c, 'gh10@test.com')
        p = make_proyecto(c, g, 'HIT-PRY-010')
        make_hito(p, 'Hito 1', porcentaje_proyecto=Decimal('25.00'), valor_facturar=Decimal('2500000'))
        make_hito(p, 'Hito 2', porcentaje_proyecto=Decimal('25.00'), valor_facturar=Decimal('2500000'))
        make_hito(p, 'Hito 3', porcentaje_proyecto=Decimal('50.00'), valor_facturar=Decimal('5000000'))
        assert Hito.all_objects.filter(proyecto=p).count() == 3

    def test_str_pendiente_cuando_no_facturado(self):
        c = make_company('907001011')
        g = make_user(c, 'gh11@test.com')
        p = make_proyecto(c, g, 'HIT-PRY-011')
        h = make_hito(p, 'Entregable final')
        s = str(h)
        assert 'Pendiente' in s
        assert 'HIT-PRY-011' in s
        assert 'Entregable final' in s

    def test_str_facturado_cuando_facturado(self):
        c = make_company('907001012')
        g = make_user(c, 'gh12@test.com')
        p = make_proyecto(c, g, 'HIT-PRY-012')
        h = make_hito(p, 'Primer corte')
        Hito.all_objects.filter(id=h.id).update(facturado=True)
        h.refresh_from_db()
        s = str(h)
        assert 'Facturado' in s

    def test_hito_vinculado_a_documento(self):
        c = make_company('907001013')
        g = make_user(c, 'gh13@test.com')
        p = make_proyecto(c, g, 'HIT-PRY-013')
        doc = DocumentoContable.all_objects.create(
            company=c, proyecto=p,
            saiopen_doc_id='DOC-HITO-001',
            tipo_documento='factura_venta',
            numero_documento='FAC-H-001',
            fecha_documento=date.today(),
            tercero_id='111', tercero_nombre='Cliente',
            valor_bruto=Decimal('2500000'), valor_neto=Decimal('2500000'),
        )
        h = make_hito(p, 'Hito con documento')
        Hito.all_objects.filter(id=h.id).update(
            facturado=True,
            documento_factura=doc,
            fecha_facturacion=date.today(),
        )
        h.refresh_from_db()
        assert h.documento_factura_id == doc.id
        assert h.fecha_facturacion == date.today()
        assert h.facturado is True

    def test_company_fk(self):
        c = make_company('907001014')
        g = make_user(c, 'gh14@test.com')
        p = make_proyecto(c, g, 'HIT-PRY-014')
        h = make_hito(p)
        assert h.company_id == c.id
