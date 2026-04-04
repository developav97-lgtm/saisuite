"""
SaiSuite -- Contabilidad: Service Tests
Tests para SyncService: upsert masivo, watermarks, multi-tenant isolation.
"""
import logging
from datetime import date
from decimal import Decimal

from django.test import TestCase

from apps.companies.models import Company
from apps.contabilidad.models import (
    MovimientoContable,
    ConfiguracionContable,
    CuentaContable,
)
from apps.contabilidad.services import SyncService

logger = logging.getLogger(__name__)


def _make_gl_record(conteo, **overrides):
    """Helper para crear un dict de record GL."""
    base = {
        'conteo': conteo,
        'auxiliar': '1105050001.0000',
        'auxiliar_nombre': 'Caja general',
        'titulo_codigo': 1,
        'titulo_nombre': 'Activo',
        'tercero_id': '900111222',
        'tercero_nombre': 'Tercero Test',
        'debito': '1000.00',
        'credito': '0.00',
        'fecha': date(2026, 1, 15),
        'periodo': '2026-01',
    }
    base.update(overrides)
    return base


def _make_acct_record(codigo, descripcion='Cuenta test', **overrides):
    """Helper para crear un dict de record ACCT."""
    base = {
        'codigo': codigo,
        'descripcion': descripcion,
        'nivel': 5,
        'clase': 'A',
        'tipo': '',
        'titulo_codigo': 1,
        'grupo_codigo': 11,
        'cuenta_codigo': 1105,
        'subcuenta_codigo': 110505,
        'posicion_financiera': 0,
    }
    base.update(overrides)
    return base


class SyncServiceGLBatchTest(TestCase):
    """Tests para SyncService.process_gl_batch."""

    def setUp(self):
        self.company = Company.objects.create(
            name='Empresa GL', nit='900111222',
        )
        self.company_b = Company.objects.create(
            name='Empresa GL B', nit='900333444',
        )

    def test_insert_batch(self):
        """Insertar un batch de registros GL nuevos."""
        records = [
            _make_gl_record(1),
            _make_gl_record(2, debito='2000.00'),
            _make_gl_record(3, credito='3000.00', debito='0.00'),
        ]
        result = SyncService.process_gl_batch(self.company.id, records)

        self.assertEqual(result['inserted'], 3)
        self.assertEqual(result['updated'], 0)
        self.assertEqual(result['errors'], [])
        self.assertEqual(
            MovimientoContable.objects.filter(company=self.company).count(), 3,
        )

    def test_upsert_existing(self):
        """Upsert actualiza registros existentes y crea nuevos."""
        # Create initial records
        SyncService.process_gl_batch(
            self.company.id,
            [_make_gl_record(1, debito='100.00')],
        )

        # Upsert: update conteo=1, insert conteo=2
        records = [
            _make_gl_record(1, debito='999.99'),
            _make_gl_record(2, debito='200.00'),
        ]
        result = SyncService.process_gl_batch(self.company.id, records)

        self.assertEqual(result['inserted'], 1)
        self.assertEqual(result['updated'], 1)

        # Verify update applied
        mov = MovimientoContable.objects.get(company=self.company, conteo=1)
        self.assertEqual(mov.debito, Decimal('999.99'))

    def test_empty_batch(self):
        """Un batch vacio retorna ceros."""
        result = SyncService.process_gl_batch(self.company.id, [])
        self.assertEqual(result['inserted'], 0)
        self.assertEqual(result['updated'], 0)

    def test_watermark_updated(self):
        """El watermark se actualiza al maximo conteo del batch."""
        SyncService.process_gl_batch(
            self.company.id,
            [_make_gl_record(50), _make_gl_record(100)],
        )

        config = ConfiguracionContable.objects.get(company=self.company)
        self.assertEqual(config.ultimo_conteo_gl, 100)
        self.assertIsNotNone(config.ultima_sync_gl)

    def test_watermark_does_not_decrease(self):
        """El watermark no baja si un batch tiene conteos menores."""
        SyncService.process_gl_batch(
            self.company.id, [_make_gl_record(200)],
        )
        SyncService.process_gl_batch(
            self.company.id, [_make_gl_record(50)],
        )

        config = ConfiguracionContable.objects.get(company=self.company)
        self.assertEqual(config.ultimo_conteo_gl, 200)

    def test_multi_tenant_isolation(self):
        """Los registros de una empresa no afectan a otra."""
        SyncService.process_gl_batch(
            self.company.id, [_make_gl_record(1)],
        )
        SyncService.process_gl_batch(
            self.company_b.id, [_make_gl_record(1)],
        )

        count_a = MovimientoContable.objects.filter(company=self.company).count()
        count_b = MovimientoContable.objects.filter(company=self.company_b).count()
        self.assertEqual(count_a, 1)
        self.assertEqual(count_b, 1)

    def test_invalid_record_collected_as_error(self):
        """Registros invalidos se reportan como errores sin abortar el batch."""
        records = [
            _make_gl_record(1),
            {'conteo': 'invalid'},  # missing required fields
            _make_gl_record(3),
        ]
        result = SyncService.process_gl_batch(self.company.id, records)

        self.assertTrue(len(result['errors']) > 0)
        # Valid records should still be inserted
        self.assertEqual(result['inserted'], 2)

    def test_sync_error_cleared_on_success(self):
        """sync_error se limpia despues de un batch exitoso."""
        config, _ = ConfiguracionContable.objects.get_or_create(
            company=self.company,
        )
        config.sync_error = 'Previous error'
        config.save()

        SyncService.process_gl_batch(
            self.company.id, [_make_gl_record(1)],
        )

        config.refresh_from_db()
        self.assertEqual(config.sync_error, '')


class SyncServiceACCTTest(TestCase):
    """Tests para SyncService.process_acct_full."""

    def setUp(self):
        self.company = Company.objects.create(
            name='Empresa ACCT', nit='900555666',
        )

    def test_insert_accounts(self):
        """Insertar cuentas del plan de cuentas."""
        records = [
            _make_acct_record('1105050001.0000', 'Caja general'),
            _make_acct_record('1110050001.0000', 'Bancos'),
        ]
        result = SyncService.process_acct_full(self.company.id, records)

        self.assertEqual(result['inserted'], 2)
        self.assertEqual(result['updated'], 0)
        self.assertEqual(result['errors'], [])

    def test_upsert_accounts(self):
        """Upsert actualiza descripcion de cuenta existente."""
        SyncService.process_acct_full(
            self.company.id,
            [_make_acct_record('1105050001.0000', 'Caja v1')],
        )

        result = SyncService.process_acct_full(
            self.company.id,
            [_make_acct_record('1105050001.0000', 'Caja v2')],
        )

        self.assertEqual(result['updated'], 1)

        cuenta = CuentaContable.objects.get(
            company=self.company,
            codigo=Decimal('1105050001.0000'),
        )
        self.assertEqual(cuenta.descripcion, 'Caja v2')

    def test_empty_batch(self):
        """Un batch vacio retorna ceros."""
        result = SyncService.process_acct_full(self.company.id, [])
        self.assertEqual(result['inserted'], 0)

    def test_ultima_sync_acct_updated(self):
        """El timestamp de sync se actualiza."""
        SyncService.process_acct_full(
            self.company.id,
            [_make_acct_record('1105050001.0000')],
        )

        config = ConfiguracionContable.objects.get(company=self.company)
        self.assertIsNotNone(config.ultima_sync_acct)


class SyncServiceStatusTest(TestCase):
    """Tests para SyncService.get_sync_status."""

    def setUp(self):
        self.company = Company.objects.create(
            name='Empresa Status', nit='900777888',
        )

    def test_status_empty(self):
        """Status de empresa sin datos retorna ceros."""
        status = SyncService.get_sync_status(self.company.id)

        self.assertFalse(status['sync_activo'])
        self.assertEqual(status['total_movimientos'], 0)
        self.assertEqual(status['total_cuentas'], 0)
        self.assertEqual(status['ultimo_conteo_gl'], 0)

    def test_status_with_data(self):
        """Status con datos refleja totales correctos."""
        SyncService.process_gl_batch(
            self.company.id,
            [_make_gl_record(1), _make_gl_record(2)],
        )
        SyncService.process_acct_full(
            self.company.id,
            [_make_acct_record('1105050001.0000')],
        )

        status = SyncService.get_sync_status(self.company.id)

        self.assertEqual(status['total_movimientos'], 2)
        self.assertEqual(status['total_cuentas'], 1)
        self.assertEqual(status['ultimo_conteo_gl'], 2)
        self.assertIsNotNone(status['ultima_sync_gl'])
        self.assertIsNotNone(status['ultima_sync_acct'])
