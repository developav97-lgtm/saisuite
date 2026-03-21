"""
SaiSuite — Tests: DocumentoContable model
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.db import IntegrityError
from django.contrib.auth import get_user_model

from apps.companies.models import Company, CompanyModule
from apps.proyectos.models import (
    Proyecto, Fase, DocumentoContable, TipoDocumento,
)

User = get_user_model()


def make_company(nit='906001001'):
    c = Company.objects.create(name='Doc Test Co', nit=nit)
    CompanyModule.objects.create(company=c, module='proyectos', is_active=True)
    return c


def make_user(company, email='gdoc@test.com'):
    return User.objects.create_user(
        email=email, password='Pass1234!', company=company, role='company_admin', is_active=True
    )


def make_proyecto(company, gerente, codigo='DOC-PRY-001'):
    return Proyecto.all_objects.create(
        company=company, gerente=gerente, codigo=codigo,
        nombre='Doc Proyecto', tipo='obra_civil',
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


def make_doc(project, saiopen_id='DOC-001', tipo='factura_venta', fase=None, **kwargs):
    defaults = dict(
        numero_documento='FAC-001',
        fecha_documento=date.today(),
        tercero_id='900555666',
        tercero_nombre='Proveedor SA',
        valor_bruto=Decimal('1000000'),
        valor_neto=Decimal('1000000'),
    )
    defaults.update(kwargs)
    return DocumentoContable.all_objects.create(
        company=project.company,
        proyecto=project,
        fase=fase,
        saiopen_doc_id=saiopen_id,
        tipo_documento=tipo,
        **defaults,
    )


@pytest.mark.django_db
class TestDocumentoContableModel:

    def test_crear_documento_contable(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        doc = make_doc(p)
        assert doc.id is not None
        assert doc.proyecto_id == p.id

    def test_fase_es_opcional(self):
        c = make_company('906001002')
        g = make_user(c, 'gdoc2@test.com')
        p = make_proyecto(c, g, 'DOC-PRY-002')
        doc = make_doc(p, fase=None)
        assert doc.fase is None

    def test_fase_con_valor(self):
        c = make_company('906001003')
        g = make_user(c, 'gdoc3@test.com')
        p = make_proyecto(c, g, 'DOC-PRY-003')
        f = make_fase(p)
        doc = make_doc(p, fase=f)
        assert doc.fase_id == f.id

    def test_tipos_documento_disponibles(self):
        tipos = [t.value for t in TipoDocumento]
        assert 'factura_venta' in tipos
        assert 'factura_compra' in tipos
        assert 'orden_compra' in tipos
        assert 'recibo_caja' in tipos
        assert 'comprobante_egreso' in tipos
        assert 'nomina' in tipos
        assert 'anticipo' in tipos
        assert 'acta_obra' in tipos

    def test_unique_together_company_saiopen_doc_id(self):
        c = make_company('906001004')
        g = make_user(c, 'gdoc4@test.com')
        p = make_proyecto(c, g, 'DOC-PRY-004')
        make_doc(p, saiopen_id='SAI-DUP-001')
        with pytest.raises(IntegrityError):
            DocumentoContable.all_objects.create(
                company=c, proyecto=p,
                saiopen_doc_id='SAI-DUP-001',
                tipo_documento='factura_venta',
                numero_documento='FAC-DUP',
                fecha_documento=date.today(),
                tercero_id='111', tercero_nombre='X',
                valor_bruto=Decimal('100'), valor_neto=Decimal('100'),
            )

    def test_mismo_saiopen_id_en_diferente_empresa(self):
        c1 = make_company('906001005')
        c2 = make_company('906001006')
        g1 = make_user(c1, 'gdoc5@test.com')
        g2 = make_user(c2, 'gdoc6@test.com')
        p1 = make_proyecto(c1, g1, 'DOC-PRY-005')
        p2 = make_proyecto(c2, g2, 'DOC-PRY-006')
        make_doc(p1, saiopen_id='SAI-CROSS-001')
        d2 = make_doc(p2, saiopen_id='SAI-CROSS-001')
        assert d2.id is not None

    def test_valor_descuento_default_cero(self):
        c = make_company('906001007')
        g = make_user(c, 'gdoc7@test.com')
        p = make_proyecto(c, g, 'DOC-PRY-007')
        doc = make_doc(p)
        assert doc.valor_descuento == Decimal('0')

    def test_observaciones_por_defecto_vacia(self):
        c = make_company('906001008')
        g = make_user(c, 'gdoc8@test.com')
        p = make_proyecto(c, g, 'DOC-PRY-008')
        doc = make_doc(p)
        assert doc.observaciones == ''

    def test_multiples_documentos_por_proyecto(self):
        c = make_company('906001009')
        g = make_user(c, 'gdoc9@test.com')
        p = make_proyecto(c, g, 'DOC-PRY-009')
        make_doc(p, 'SAI-001', tipo='factura_venta')
        make_doc(p, 'SAI-002', tipo='orden_compra')
        make_doc(p, 'SAI-003', tipo='anticipo')
        count = DocumentoContable.all_objects.filter(proyecto=p).count()
        assert count == 3

    def test_filtrar_documentos_por_fase(self):
        c = make_company('906001010')
        g = make_user(c, 'gdoc10@test.com')
        p = make_proyecto(c, g, 'DOC-PRY-010')
        f1 = make_fase(p, orden=1)
        f2 = make_fase(p, orden=2)
        make_doc(p, 'SAI-F1-001', fase=f1)
        make_doc(p, 'SAI-F1-002', fase=f1)
        make_doc(p, 'SAI-F2-001', fase=f2)
        make_doc(p, 'SAI-NOFASE', fase=None)
        assert DocumentoContable.all_objects.filter(proyecto=p, fase=f1).count() == 2
        assert DocumentoContable.all_objects.filter(proyecto=p, fase=f2).count() == 1
        assert DocumentoContable.all_objects.filter(proyecto=p, fase=None).count() == 1

    def test_ordering_por_fecha_desc(self):
        c = make_company('906001011')
        g = make_user(c, 'gdoc11@test.com')
        p = make_proyecto(c, g, 'DOC-PRY-011')
        make_doc(p, 'SAI-OLD', fecha_documento=date.today() - timedelta(days=10))
        make_doc(p, 'SAI-NEW', fecha_documento=date.today())
        docs = list(DocumentoContable.all_objects.filter(proyecto=p))
        assert docs[0].saiopen_doc_id == 'SAI-NEW'

    def test_str_incluye_tipo_numero_y_fecha(self):
        c = make_company('906001012')
        g = make_user(c, 'gdoc12@test.com')
        p = make_proyecto(c, g, 'DOC-PRY-012')
        doc = make_doc(p, tipo='factura_compra', numero_documento='FC-999')
        s = str(doc)
        assert 'FC-999' in s

    def test_sincronizado_desde_saiopen_se_genera(self):
        c = make_company('906001013')
        g = make_user(c, 'gdoc13@test.com')
        p = make_proyecto(c, g, 'DOC-PRY-013')
        doc = make_doc(p)
        assert doc.sincronizado_desde_saiopen is not None
