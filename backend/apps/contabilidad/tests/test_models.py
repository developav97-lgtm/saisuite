"""
SaiSuite -- Contabilidad: Model Tests
Tests para modelos de contabilidad: integridad, constraints, multi-tenant.
"""
import logging
from datetime import date
from decimal import Decimal

from django.db import IntegrityError
from django.test import TestCase

from apps.companies.models import Company
from apps.contabilidad.models import (
    MovimientoContable,
    ConfiguracionContable,
    CuentaContable,
)

logger = logging.getLogger(__name__)


class MovimientoContableModelTest(TestCase):
    """Tests para el modelo MovimientoContable."""

    def setUp(self):
        self.company_a = Company.objects.create(
            name='Empresa A', nit='900111222',
        )
        self.company_b = Company.objects.create(
            name='Empresa B', nit='900333444',
        )

    def test_create_movimiento(self):
        """Un movimiento contable se crea correctamente."""
        mov = MovimientoContable.objects.create(
            company=self.company_a,
            conteo=1,
            auxiliar=Decimal('1105050001.0000'),
            auxiliar_nombre='Caja general',
            titulo_codigo=1,
            titulo_nombre='Activo',
            tercero_id='900111222',
            tercero_nombre='Empresa A',
            debito=Decimal('1000000.00'),
            credito=Decimal('0.00'),
            fecha=date(2026, 1, 15),
            periodo='2026-01',
        )
        self.assertEqual(mov.conteo, 1)
        self.assertEqual(mov.debito, Decimal('1000000.00'))
        self.assertIsNotNone(mov.sincronizado_en)

    def test_unique_together_company_conteo(self):
        """No se pueden crear dos movimientos con el mismo conteo para la misma empresa."""
        MovimientoContable.objects.create(
            company=self.company_a,
            conteo=100,
            auxiliar=Decimal('1105050001.0000'),
            auxiliar_nombre='Caja',
            tercero_id='900111222',
            debito=Decimal('500.00'),
            credito=Decimal('0.00'),
            fecha=date(2026, 1, 1),
            periodo='2026-01',
        )
        with self.assertRaises(IntegrityError):
            MovimientoContable.objects.create(
                company=self.company_a,
                conteo=100,
                auxiliar=Decimal('2205050001.0000'),
                auxiliar_nombre='CxP',
                tercero_id='900333444',
                debito=Decimal('0.00'),
                credito=Decimal('500.00'),
                fecha=date(2026, 1, 1),
                periodo='2026-01',
            )

    def test_same_conteo_different_company(self):
        """El mismo conteo puede existir en dos empresas diferentes."""
        MovimientoContable.objects.create(
            company=self.company_a,
            conteo=200,
            auxiliar=Decimal('1105050001.0000'),
            auxiliar_nombre='Caja',
            tercero_id='900111222',
            debito=Decimal('100.00'),
            credito=Decimal('0.00'),
            fecha=date(2026, 2, 1),
            periodo='2026-02',
        )
        mov_b = MovimientoContable.objects.create(
            company=self.company_b,
            conteo=200,
            auxiliar=Decimal('1105050001.0000'),
            auxiliar_nombre='Caja',
            tercero_id='900333444',
            debito=Decimal('200.00'),
            credito=Decimal('0.00'),
            fecha=date(2026, 2, 1),
            periodo='2026-02',
        )
        self.assertEqual(mov_b.company, self.company_b)

    def test_str_representation(self):
        """El __str__ muestra periodo, auxiliar, debito y credito."""
        mov = MovimientoContable.objects.create(
            company=self.company_a,
            conteo=300,
            auxiliar=Decimal('4135050001.0000'),
            auxiliar_nombre='Ventas',
            tercero_id='900111222',
            debito=Decimal('0.00'),
            credito=Decimal('5000.00'),
            fecha=date(2026, 3, 15),
            periodo='2026-03',
        )
        self.assertIn('2026-03', str(mov))


class ConfiguracionContableModelTest(TestCase):
    """Tests para el modelo ConfiguracionContable."""

    def setUp(self):
        self.company = Company.objects.create(
            name='Empresa Config', nit='900555666',
        )

    def test_create_configuracion(self):
        """Se crea una configuracion contable por empresa."""
        config = ConfiguracionContable.objects.create(
            company=self.company,
            usa_departamentos_cc=True,
            usa_proyectos_actividades=False,
        )
        self.assertTrue(config.usa_departamentos_cc)
        self.assertFalse(config.usa_proyectos_actividades)
        self.assertEqual(config.ultimo_conteo_gl, 0)

    def test_one_to_one(self):
        """Solo puede haber una configuracion por empresa."""
        ConfiguracionContable.objects.create(company=self.company)
        with self.assertRaises(IntegrityError):
            ConfiguracionContable.objects.create(company=self.company)

    def test_str_representation(self):
        config = ConfiguracionContable.objects.create(
            company=self.company, sync_activo=True,
        )
        self.assertIn('activo', str(config))


class CuentaContableModelTest(TestCase):
    """Tests para el modelo CuentaContable."""

    def setUp(self):
        self.company = Company.objects.create(
            name='Empresa Cuentas', nit='900777888',
        )

    def test_create_cuenta(self):
        """Se crea una cuenta contable correctamente."""
        cuenta = CuentaContable.objects.create(
            company=self.company,
            codigo=Decimal('1105050001.0000'),
            descripcion='Caja general',
            nivel=5,
            clase='A',
            titulo_codigo=1,
            grupo_codigo=11,
            cuenta_codigo=1105,
            subcuenta_codigo=110505,
        )
        self.assertEqual(cuenta.descripcion, 'Caja general')
        self.assertEqual(cuenta.nivel, 5)

    def test_unique_together_company_codigo(self):
        """No se pueden duplicar codigos en la misma empresa."""
        CuentaContable.objects.create(
            company=self.company,
            codigo=Decimal('1105050001.0000'),
            descripcion='Caja',
        )
        with self.assertRaises(IntegrityError):
            CuentaContable.objects.create(
                company=self.company,
                codigo=Decimal('1105050001.0000'),
                descripcion='Caja duplicada',
            )

    def test_str_representation(self):
        cuenta = CuentaContable.objects.create(
            company=self.company,
            codigo=Decimal('4135050001.0000'),
            descripcion='Ventas nacionales',
        )
        self.assertIn('Ventas nacionales', str(cuenta))
