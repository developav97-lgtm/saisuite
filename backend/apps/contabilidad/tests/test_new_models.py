"""
SaiSuite -- Contabilidad: Tests para modelos de facturación, cartera e inventario.
Tests de integridad, constraints unique_together y multi-tenant.
"""
import logging
from datetime import date
from decimal import Decimal

from django.db import IntegrityError
from django.test import TestCase

from apps.companies.models import Company
from apps.contabilidad.models import (
    FacturaEncabezado,
    FacturaDetalle,
    MovimientoCartera,
    MovimientoInventario,
)

logger = logging.getLogger(__name__)


class FacturaEncabezadoModelTest(TestCase):
    """Tests para el modelo FacturaEncabezado."""

    def setUp(self):
        self.company_a = Company.objects.create(name='Empresa A', nit='900111222')
        self.company_b = Company.objects.create(name='Empresa B', nit='900333444')

    def _create_factura(self, company=None, **kwargs):
        defaults = {
            'company': company or self.company_a,
            'number': 1,
            'tipo': 'FA',
            'id_sucursal': 1,
            'tercero_id': '900111222',
            'tercero_nombre': 'Cliente Test',
            'fecha': date(2026, 3, 15),
            'periodo': '2026-03',
            'subtotal': Decimal('1000000.00'),
            'iva': Decimal('190000.00'),
            'total': Decimal('1190000.00'),
        }
        defaults.update(kwargs)
        return FacturaEncabezado.objects.create(**defaults)

    def test_create_factura(self):
        """Una factura encabezado se crea correctamente."""
        fac = self._create_factura()
        self.assertEqual(fac.number, 1)
        self.assertEqual(fac.tipo, 'FA')
        self.assertEqual(fac.total, Decimal('1190000.00'))
        self.assertIsNotNone(fac.sincronizado_en)

    def test_unique_together_company_number_tipo_sucursal(self):
        """No se pueden duplicar (company, number, tipo, id_sucursal)."""
        self._create_factura()
        with self.assertRaises(IntegrityError):
            self._create_factura()

    def test_same_number_different_tipo(self):
        """El mismo number puede existir con diferente tipo."""
        self._create_factura(tipo='FA')
        fac_nc = self._create_factura(tipo='NC')
        self.assertEqual(fac_nc.tipo, 'NC')

    def test_same_number_different_company(self):
        """El mismo number puede existir en empresas diferentes."""
        self._create_factura(company=self.company_a)
        fac_b = self._create_factura(company=self.company_b)
        self.assertEqual(fac_b.company, self.company_b)

    def test_str_representation(self):
        fac = self._create_factura()
        s = str(fac)
        self.assertIn('FA', s)
        self.assertIn('#1', s)

    def test_default_values(self):
        """Valores por defecto se asignan correctamente."""
        fac = self._create_factura()
        self.assertFalse(fac.posted)
        self.assertFalse(fac.closed)
        self.assertEqual(fac.cod_moneda, 'COP')
        self.assertEqual(fac.descuento_global, Decimal('0.00'))

    def test_multi_tenant_isolation(self):
        """Facturas de una empresa no se mezclan con las de otra."""
        self._create_factura(company=self.company_a, number=1)
        self._create_factura(company=self.company_b, number=1)
        self.assertEqual(FacturaEncabezado.objects.filter(company=self.company_a).count(), 1)
        self.assertEqual(FacturaEncabezado.objects.filter(company=self.company_b).count(), 1)


class FacturaDetalleModelTest(TestCase):
    """Tests para el modelo FacturaDetalle."""

    def setUp(self):
        self.company = Company.objects.create(name='Empresa Det', nit='900555666')
        self.factura = FacturaEncabezado.objects.create(
            company=self.company,
            number=100,
            tipo='FA',
            id_sucursal=1,
            tercero_id='900555666',
            fecha=date(2026, 3, 1),
            periodo='2026-03',
            total=Decimal('500000.00'),
        )

    def _create_detalle(self, **kwargs):
        defaults = {
            'company': self.company,
            'factura': self.factura,
            'conteo': 1,
            'item_codigo': 'PROD001',
            'item_descripcion': 'Producto de prueba',
            'qty_order': Decimal('10.0000'),
            'qty_ship': Decimal('10.0000'),
            'precio_unitario': Decimal('50000.0000'),
            'precio_extendido': Decimal('500000.00'),
        }
        defaults.update(kwargs)
        return FacturaDetalle.objects.create(**defaults)

    def test_create_detalle(self):
        """Un detalle de factura se crea correctamente."""
        det = self._create_detalle()
        self.assertEqual(det.item_codigo, 'PROD001')
        self.assertEqual(det.qty_ship, Decimal('10.0000'))
        self.assertIsNotNone(det.sincronizado_en)

    def test_unique_together_company_conteo(self):
        """No se pueden duplicar (company, conteo)."""
        self._create_detalle(conteo=1)
        with self.assertRaises(IntegrityError):
            self._create_detalle(conteo=1)

    def test_fk_factura(self):
        """El detalle referencia correctamente a su encabezado."""
        det = self._create_detalle()
        self.assertEqual(det.factura.id, self.factura.id)
        self.assertEqual(self.factura.detalles.count(), 1)

    def test_cascade_delete_factura(self):
        """Al eliminar la factura se eliminan sus detalles."""
        self._create_detalle()
        self.factura.delete()
        self.assertEqual(FacturaDetalle.objects.filter(company=self.company).count(), 0)

    def test_str_representation(self):
        det = self._create_detalle()
        s = str(det)
        self.assertIn('PROD001', s)

    def test_default_values(self):
        det = self._create_detalle()
        self.assertEqual(det.valor_iva, Decimal('0.00'))
        self.assertEqual(det.descuento, Decimal('0.00'))
        self.assertEqual(det.margen_valor, Decimal('0.00'))


class MovimientoCarteraModelTest(TestCase):
    """Tests para el modelo MovimientoCartera."""

    def setUp(self):
        self.company_a = Company.objects.create(name='Empresa Cart A', nit='900111222')
        self.company_b = Company.objects.create(name='Empresa Cart B', nit='900333444')

    def _create_cartera(self, company=None, **kwargs):
        defaults = {
            'company': company or self.company_a,
            'conteo': 1,
            'tercero_id': '900111222',
            'tercero_nombre': 'Cliente Test',
            'cuenta_contable': Decimal('1305050001.0000'),
            'tipo': 'FA',
            'invc': 'FAC-001',
            'fecha': date(2026, 3, 15),
            'duedate': date(2026, 4, 15),
            'periodo': '2026-03',
            'debito': Decimal('1000000.00'),
            'credito': Decimal('0.00'),
            'saldo': Decimal('1000000.00'),
            'tipo_cartera': 'CXC',
        }
        defaults.update(kwargs)
        return MovimientoCartera.objects.create(**defaults)

    def test_create_cartera(self):
        """Un movimiento de cartera se crea correctamente."""
        mov = self._create_cartera()
        self.assertEqual(mov.conteo, 1)
        self.assertEqual(mov.tipo_cartera, 'CXC')
        self.assertEqual(mov.saldo, Decimal('1000000.00'))
        self.assertIsNotNone(mov.sincronizado_en)

    def test_unique_together_company_conteo(self):
        """No se pueden duplicar (company, conteo)."""
        self._create_cartera(conteo=100)
        with self.assertRaises(IntegrityError):
            self._create_cartera(conteo=100)

    def test_same_conteo_different_company(self):
        """El mismo conteo puede existir en empresas diferentes."""
        self._create_cartera(company=self.company_a, conteo=200)
        mov_b = self._create_cartera(company=self.company_b, conteo=200)
        self.assertEqual(mov_b.company, self.company_b)

    def test_tipo_cartera_choices(self):
        """tipo_cartera solo acepta CXC o CXP."""
        mov_cxc = self._create_cartera(conteo=1, tipo_cartera='CXC')
        self.assertEqual(mov_cxc.tipo_cartera, 'CXC')
        mov_cxp = self._create_cartera(conteo=2, tipo_cartera='CXP')
        self.assertEqual(mov_cxp.tipo_cartera, 'CXP')

    def test_str_representation(self):
        mov = self._create_cartera()
        s = str(mov)
        self.assertIn('CXC', s)
        self.assertIn('Cliente Test', s)

    def test_multi_tenant_isolation(self):
        """Movimientos de cartera de una empresa no se mezclan con los de otra."""
        self._create_cartera(company=self.company_a, conteo=1)
        self._create_cartera(company=self.company_b, conteo=1)
        self.assertEqual(MovimientoCartera.objects.filter(company=self.company_a).count(), 1)
        self.assertEqual(MovimientoCartera.objects.filter(company=self.company_b).count(), 1)


class MovimientoInventarioModelTest(TestCase):
    """Tests para el modelo MovimientoInventario."""

    def setUp(self):
        self.company_a = Company.objects.create(name='Empresa Inv A', nit='900111222')
        self.company_b = Company.objects.create(name='Empresa Inv B', nit='900333444')

    def _create_inventario(self, company=None, **kwargs):
        defaults = {
            'company': company or self.company_a,
            'conteo': 1,
            'item_codigo': 'PROD001',
            'item_descripcion': 'Producto de prueba',
            'location': '001',
            'tipo': 'FA',
            'fecha': date(2026, 3, 15),
            'periodo': '2026-03',
            'cantidad': Decimal('50.0000'),
            'valor_unitario': Decimal('10000.0000'),
            'total': Decimal('500000.00'),
            'saldo_unidades': Decimal('100.0000'),
            'saldo_pesos': Decimal('1000000.00'),
        }
        defaults.update(kwargs)
        return MovimientoInventario.objects.create(**defaults)

    def test_create_inventario(self):
        """Un movimiento de inventario se crea correctamente."""
        mov = self._create_inventario()
        self.assertEqual(mov.item_codigo, 'PROD001')
        self.assertEqual(mov.cantidad, Decimal('50.0000'))
        self.assertEqual(mov.total, Decimal('500000.00'))
        self.assertIsNotNone(mov.sincronizado_en)

    def test_unique_together_company_conteo(self):
        """No se pueden duplicar (company, conteo)."""
        self._create_inventario(conteo=100)
        with self.assertRaises(IntegrityError):
            self._create_inventario(conteo=100)

    def test_same_conteo_different_company(self):
        """El mismo conteo puede existir en empresas diferentes."""
        self._create_inventario(company=self.company_a, conteo=200)
        mov_b = self._create_inventario(company=self.company_b, conteo=200)
        self.assertEqual(mov_b.company, self.company_b)

    def test_str_representation(self):
        mov = self._create_inventario()
        s = str(mov)
        self.assertIn('PROD001', s)
        self.assertIn('2026-03', s)

    def test_lote_fields(self):
        """Campos de lote y serie se guardan correctamente."""
        mov = self._create_inventario(
            conteo=10,
            lote='LOTE-2026-001',
            serie='SN12345',
            lote_vencimiento=date(2027, 12, 31),
        )
        self.assertEqual(mov.lote, 'LOTE-2026-001')
        self.assertEqual(mov.serie, 'SN12345')
        self.assertEqual(mov.lote_vencimiento, date(2027, 12, 31))

    def test_default_values(self):
        """Valores por defecto se asignan correctamente."""
        mov = self._create_inventario()
        self.assertEqual(mov.costo_peps, Decimal('0.0000'))
        self.assertEqual(mov.lote, '')
        self.assertEqual(mov.serie, '')
        self.assertIsNone(mov.lote_vencimiento)

    def test_multi_tenant_isolation(self):
        """Movimientos de inventario de una empresa no se mezclan con los de otra."""
        self._create_inventario(company=self.company_a, conteo=1)
        self._create_inventario(company=self.company_b, conteo=1)
        self.assertEqual(MovimientoInventario.objects.filter(company=self.company_a).count(), 1)
        self.assertEqual(MovimientoInventario.objects.filter(company=self.company_b).count(), 1)
