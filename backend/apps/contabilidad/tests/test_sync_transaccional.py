"""
Tests para SyncService — tablas transaccionales OE, OEDET, CARPRO, ITEMACT.
"""
from decimal import Decimal

from django.test import TestCase

from apps.companies.models import Company
from apps.contabilidad.models import (
    ConfiguracionContable,
    FacturaEncabezado,
    FacturaDetalle,
    MovimientoCartera,
    MovimientoInventario,
)
from apps.contabilidad.services import SyncService


_nit_counter = iter(range(900100000, 900200000))


def _make_company(name='Test Company'):
    return Company.objects.create(name=name, nit=str(next(_nit_counter)))


def _oe_record(**kwargs):
    defaults = {
        'number': 1,
        'tipo': 'FAC',
        'id_sucursal': 1,
        'tercero_id': 'C001',
        'tercero_nombre': 'Cliente Test',
        'tercero_razon_social': 'Cliente Test S.A.S.',
        'tipo_descripcion': 'Factura de venta',
        'fecha': '2026-01-15',
        'periodo': '2026-01',
        'subtotal': '1000.00',
        'iva': '190.00',
        'descuento_global': '50.00',
        'destotal': '50.00',
        'otroscargos': '0.00',
        'total': '1190.00',
        'porcrtfte': '1.5000',
        'reteica': '15.00',
        'porcentaje_reteica': '0.4140',
        'reteiva': '10.00',
    }
    defaults.update(kwargs)
    return defaults


def _carpro_record(**kwargs):
    defaults = {
        'conteo': 1,
        'tercero_id': 'C001',
        'cuenta_contable': '1305000000',
        'fecha': '2026-01-15',
        'periodo': '2026-01',
        'debito': '1190.00',
        'credito': '0.00',
        'saldo': '1190.00',
        'tipo_cartera': 'CXC',
    }
    defaults.update(kwargs)
    return defaults


def _itemact_record(**kwargs):
    defaults = {
        'conteo': 1,
        'item_codigo': 'PROD001',
        'location': 'BOD',
        'fecha': '2026-01-15',
        'periodo': '2026-01',
        'cantidad': '10.0000',
        'total': '500.00',
    }
    defaults.update(kwargs)
    return defaults


# ─────────────────────────────────────────────────────────────
# OE — FacturaEncabezado
# ─────────────────────────────────────────────────────────────

class ProcessOEBatchTest(TestCase):

    def setUp(self):
        self.company = _make_company()

    def test_insert_single_record(self):
        result = SyncService.process_oe_batch(
            company_id=self.company.id,
            records=[_oe_record()],
        )
        self.assertEqual(result['inserted'], 1)
        self.assertEqual(result['updated'], 0)
        self.assertEqual(result['errors'], [])
        self.assertEqual(FacturaEncabezado.objects.filter(company=self.company).count(), 1)

    def test_upsert_existing_record(self):
        SyncService.process_oe_batch(
            company_id=self.company.id,
            records=[_oe_record(total='1190.00')],
        )
        result = SyncService.process_oe_batch(
            company_id=self.company.id,
            records=[_oe_record(total='2380.00')],
        )
        self.assertEqual(result['inserted'], 0)
        self.assertEqual(result['updated'], 1)
        factura = FacturaEncabezado.objects.get(company=self.company, number=1)
        self.assertEqual(factura.total, Decimal('2380.00'))

    def test_batch_multiple_records(self):
        records = [_oe_record(number=i, tipo='FAC') for i in range(1, 6)]
        result = SyncService.process_oe_batch(
            company_id=self.company.id,
            records=records,
        )
        self.assertEqual(result['inserted'], 5)
        self.assertEqual(FacturaEncabezado.objects.filter(company=self.company).count(), 5)

    def test_empty_batch_returns_zeros(self):
        result = SyncService.process_oe_batch(company_id=self.company.id, records=[])
        self.assertEqual(result, {'inserted': 0, 'updated': 0, 'errors': []})

    def test_multi_tenant_isolation(self):
        company_b = _make_company('Empresa B')
        SyncService.process_oe_batch(
            company_id=self.company.id,
            records=[_oe_record(number=1)],
        )
        SyncService.process_oe_batch(
            company_id=company_b.id,
            records=[_oe_record(number=1)],
        )
        self.assertEqual(FacturaEncabezado.objects.filter(company=self.company).count(), 1)
        self.assertEqual(FacturaEncabezado.objects.filter(company=company_b).count(), 1)

    def test_watermark_updated(self):
        SyncService.process_oe_batch(
            company_id=self.company.id,
            records=[_oe_record(number=42)],
        )
        config = ConfiguracionContable.objects.get(company=self.company)
        self.assertEqual(config.ultimo_conteo_oe, 42)
        self.assertIsNotNone(config.ultima_sync_oe)

    def test_invalid_record_skipped_with_error(self):
        bad = {'tipo': 'FAC'}  # falta number y fecha
        result = SyncService.process_oe_batch(
            company_id=self.company.id,
            records=[bad],
        )
        self.assertEqual(result['inserted'], 0)
        self.assertGreater(len(result['errors']), 0)

    def test_retenciones_fields_persisted(self):
        """Nuevos campos de retenciones y cargos se guardan correctamente."""
        SyncService.process_oe_batch(
            company_id=self.company.id,
            records=[_oe_record()],
        )
        factura = FacturaEncabezado.objects.get(company=self.company, number=1)
        self.assertEqual(factura.tercero_razon_social, 'Cliente Test S.A.S.')
        self.assertEqual(factura.tipo_descripcion, 'Factura de venta')
        self.assertEqual(factura.destotal, Decimal('50.00'))
        self.assertEqual(factura.otroscargos, Decimal('0.00'))
        self.assertEqual(factura.porcrtfte, Decimal('1.5000'))
        self.assertEqual(factura.reteica, Decimal('15.00'))
        self.assertEqual(factura.porcentaje_reteica, Decimal('0.4140'))
        self.assertEqual(factura.reteiva, Decimal('10.00'))

    def test_retenciones_empty_when_not_sent(self):
        """Si el agente no envía campos de retenciones, quedan en 0/'' sin error."""
        record = {
            'number': 2,
            'tipo': 'FAC',
            'id_sucursal': 1,
            'tercero_id': 'C002',
            'fecha': '2026-01-20',
            'total': '500.00',
        }
        result = SyncService.process_oe_batch(
            company_id=self.company.id,
            records=[record],
        )
        self.assertEqual(result['inserted'], 1)
        factura = FacturaEncabezado.objects.get(company=self.company, number=2)
        self.assertEqual(factura.tercero_razon_social, '')
        self.assertEqual(factura.tipo_descripcion, '')
        self.assertEqual(factura.reteica, Decimal('0'))
        self.assertEqual(factura.reteiva, Decimal('0'))


# ─────────────────────────────────────────────────────────────
# OEDET — FacturaDetalle
# ─────────────────────────────────────────────────────────────

class ProcessOEDetBatchTest(TestCase):

    def setUp(self):
        self.company = _make_company()
        # Crear factura encabezado previa (requisito FK)
        self.factura = FacturaEncabezado.objects.create(
            company=self.company,
            number=1, tipo='FAC', id_sucursal=1,
            tercero_id='C001',
            fecha='2026-01-15',
            periodo='2026-01',
        )

    def _oedet_record(self, **kwargs):
        defaults = {
            'conteo': 1,
            'factura_number': 1,
            'factura_tipo': 'FAC',
            'factura_id_sucursal': 1,
            'item_codigo': 'PROD001',
            'qty_ship': '5.0000',
            'precio_extendido': '500.00',
            'total_descuento': '10.00',
            'departamento_codigo': 'DP01',
            'centro_costo_codigo': 'CC01',
            'actividad_codigo': 'ACT01',
        }
        defaults.update(kwargs)
        return defaults

    def test_insert_single_detalle(self):
        result = SyncService.process_oedet_batch(
            company_id=self.company.id,
            records=[self._oedet_record()],
        )
        self.assertEqual(result['inserted'], 1)
        self.assertEqual(FacturaDetalle.objects.filter(company=self.company).count(), 1)

    def test_upsert_existing_detalle(self):
        SyncService.process_oedet_batch(
            company_id=self.company.id,
            records=[self._oedet_record(precio_extendido='500.00')],
        )
        result = SyncService.process_oedet_batch(
            company_id=self.company.id,
            records=[self._oedet_record(precio_extendido='750.00')],
        )
        self.assertEqual(result['updated'], 1)
        detalle = FacturaDetalle.objects.get(company=self.company, conteo=1)
        self.assertEqual(detalle.precio_extendido, Decimal('750.00'))

    def test_missing_parent_factura_is_skipped(self):
        result = SyncService.process_oedet_batch(
            company_id=self.company.id,
            records=[self._oedet_record(factura_number=999)],  # no existe
        )
        self.assertEqual(result['inserted'], 0)
        self.assertGreater(len(result['errors']), 0)

    def test_empty_batch_returns_zeros(self):
        result = SyncService.process_oedet_batch(company_id=self.company.id, records=[])
        self.assertEqual(result, {'inserted': 0, 'updated': 0, 'errors': []})

    def test_dimensiones_fields_persisted(self):
        """Campos de dimensiones contables (DPTO/CCOST/ACTIVIDAD) se guardan correctamente."""
        SyncService.process_oedet_batch(
            company_id=self.company.id,
            records=[self._oedet_record()],
        )
        detalle = FacturaDetalle.objects.get(company=self.company, conteo=1)
        self.assertEqual(detalle.departamento_codigo, 'DP01')
        self.assertEqual(detalle.centro_costo_codigo, 'CC01')
        self.assertEqual(detalle.actividad_codigo, 'ACT01')

    def test_clasificacion_empty_when_not_sent(self):
        """Si el agente no envía campos de clasificación, quedan vacíos sin error."""
        record = {
            'conteo': 2,
            'factura_number': 1,
            'factura_tipo': 'FAC',
            'factura_id_sucursal': 1,
            'item_codigo': 'PROD002',
            'qty_ship': '1.0000',
            'precio_extendido': '100.00',
        }
        result = SyncService.process_oedet_batch(
            company_id=self.company.id,
            records=[record],
        )
        self.assertEqual(result['inserted'], 1)
        detalle = FacturaDetalle.objects.get(company=self.company, conteo=2)
        self.assertEqual(detalle.total_descuento, Decimal('0'))
        self.assertEqual(detalle.departamento_codigo, '')

    def test_watermark_updated(self):
        SyncService.process_oedet_batch(
            company_id=self.company.id,
            records=[self._oedet_record(conteo=77)],
        )
        config = ConfiguracionContable.objects.get(company=self.company)
        self.assertEqual(config.ultimo_conteo_oedet, 77)
        self.assertIsNotNone(config.ultima_sync_oedet)


# ─────────────────────────────────────────────────────────────
# CARPRO — MovimientoCartera
# ─────────────────────────────────────────────────────────────

class ProcessCARPROBatchTest(TestCase):

    def setUp(self):
        self.company = _make_company()

    def test_insert_single_record(self):
        result = SyncService.process_carpro_batch(
            company_id=self.company.id,
            records=[_carpro_record()],
        )
        self.assertEqual(result['inserted'], 1)
        self.assertEqual(MovimientoCartera.objects.filter(company=self.company).count(), 1)

    def test_upsert_updates_saldo(self):
        SyncService.process_carpro_batch(
            company_id=self.company.id,
            records=[_carpro_record(saldo='1190.00')],
        )
        SyncService.process_carpro_batch(
            company_id=self.company.id,
            records=[_carpro_record(saldo='0.00')],
        )
        mov = MovimientoCartera.objects.get(company=self.company, conteo=1)
        self.assertEqual(mov.saldo, Decimal('0.00'))

    def test_cxp_tipo_cartera(self):
        SyncService.process_carpro_batch(
            company_id=self.company.id,
            records=[_carpro_record(tipo_cartera='CXP')],
        )
        mov = MovimientoCartera.objects.get(company=self.company)
        self.assertEqual(mov.tipo_cartera, 'CXP')

    def test_multi_tenant_isolation(self):
        company_b = _make_company('Empresa B')
        SyncService.process_carpro_batch(
            company_id=self.company.id,
            records=[_carpro_record(conteo=1)],
        )
        SyncService.process_carpro_batch(
            company_id=company_b.id,
            records=[_carpro_record(conteo=1)],
        )
        self.assertEqual(MovimientoCartera.objects.filter(company=self.company).count(), 1)
        self.assertEqual(MovimientoCartera.objects.filter(company=company_b).count(), 1)

    def test_empty_batch_returns_zeros(self):
        result = SyncService.process_carpro_batch(company_id=self.company.id, records=[])
        self.assertEqual(result, {'inserted': 0, 'updated': 0, 'errors': []})

    def test_watermark_updated(self):
        SyncService.process_carpro_batch(
            company_id=self.company.id,
            records=[_carpro_record(conteo=55)],
        )
        config = ConfiguracionContable.objects.get(company=self.company)
        self.assertEqual(config.ultimo_conteo_carpro, 55)
        self.assertIsNotNone(config.ultima_sync_carpro)


# ─────────────────────────────────────────────────────────────
# ITEMACT — MovimientoInventario
# ─────────────────────────────────────────────────────────────

class ProcessITEMACTBatchTest(TestCase):

    def setUp(self):
        self.company = _make_company()

    def test_insert_single_record(self):
        result = SyncService.process_itemact_batch(
            company_id=self.company.id,
            records=[_itemact_record()],
        )
        self.assertEqual(result['inserted'], 1)
        self.assertEqual(MovimientoInventario.objects.filter(company=self.company).count(), 1)

    def test_upsert_updates_costo_promedio(self):
        SyncService.process_itemact_batch(
            company_id=self.company.id,
            records=[_itemact_record(costo_promedio='5000.0000')],
        )
        SyncService.process_itemact_batch(
            company_id=self.company.id,
            records=[_itemact_record(costo_promedio='6000.0000')],
        )
        mov = MovimientoInventario.objects.get(company=self.company, conteo=1)
        self.assertEqual(mov.costo_promedio, Decimal('6000.0000'))

    def test_lote_vencimiento_null_allowed(self):
        result = SyncService.process_itemact_batch(
            company_id=self.company.id,
            records=[_itemact_record(lote_vencimiento=None)],
        )
        self.assertEqual(result['errors'], [])
        mov = MovimientoInventario.objects.get(company=self.company)
        self.assertIsNone(mov.lote_vencimiento)

    def test_batch_multiple_records(self):
        records = [_itemact_record(conteo=i, item_codigo=f'PROD{i:03d}') for i in range(1, 11)]
        result = SyncService.process_itemact_batch(
            company_id=self.company.id,
            records=records,
        )
        self.assertEqual(result['inserted'], 10)
        self.assertEqual(MovimientoInventario.objects.filter(company=self.company).count(), 10)

    def test_empty_batch_returns_zeros(self):
        result = SyncService.process_itemact_batch(company_id=self.company.id, records=[])
        self.assertEqual(result, {'inserted': 0, 'updated': 0, 'errors': []})

    def test_watermark_updated(self):
        SyncService.process_itemact_batch(
            company_id=self.company.id,
            records=[_itemact_record(conteo=88)],
        )
        config = ConfiguracionContable.objects.get(company=self.company)
        self.assertEqual(config.ultimo_conteo_itemact, 88)
        self.assertIsNotNone(config.ultima_sync_itemact)

    def test_multi_tenant_isolation(self):
        company_b = _make_company('Empresa B')
        SyncService.process_itemact_batch(
            company_id=self.company.id,
            records=[_itemact_record(conteo=1)],
        )
        SyncService.process_itemact_batch(
            company_id=company_b.id,
            records=[_itemact_record(conteo=1)],
        )
        self.assertEqual(MovimientoInventario.objects.filter(company=self.company).count(), 1)
        self.assertEqual(MovimientoInventario.objects.filter(company=company_b).count(), 1)
