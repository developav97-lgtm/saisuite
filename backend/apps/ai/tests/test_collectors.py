"""
SaiSuite — AI: Tests para DataCollectors
Verifica que cada collector devuelva un string formateado sin errores
y sin ejecutar operaciones de escritura (SOLO LECTURA).
"""
import logging
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.companies.models import Company, CompanyLicense, CompanyModule
from apps.ai.collectors import (
    COLLECTORS,
    ContabilidadCollector,
    DashboardCollector,
    GeneralCollector,
    ProyectosCollector,
    TercerosCollector,
    _fmt_currency,
    _safe_ratio,
)

User = get_user_model()
logger = logging.getLogger(__name__)


# ── Helpers ──────────────────────────────────────────────────────


def _make_company(name='Test SA', nit='900000001'):
    return Company.objects.create(name=name, nit=nit, plan='starter')


def _make_user(company, email='user@test.com', role='company_admin'):
    return User.objects.create_user(
        email=email,
        password='testpass123',
        company=company,
        role=role,
        is_active=True,
    )


# ── Unit tests: helpers ───────────────────────────────────────────


class FmtCurrencyTest(TestCase):

    def test_positive(self):
        result = _fmt_currency(1500000)
        self.assertIn('1,500,000', result)
        self.assertIn('$', result)

    def test_negative(self):
        result = _fmt_currency(-5000)
        self.assertIn('-$', result)

    def test_zero(self):
        self.assertEqual(_fmt_currency(0), '$0')

    def test_none(self):
        self.assertEqual(_fmt_currency(None), '$0')

    def test_decimal(self):
        result = _fmt_currency(Decimal('2500.50'))
        self.assertIn('$', result)


class SafeRatioTest(TestCase):

    def test_normal(self):
        self.assertAlmostEqual(_safe_ratio(1, 4), 0.25)

    def test_zero_denominator(self):
        self.assertEqual(_safe_ratio(10, 0), 0.0)

    def test_none_values(self):
        self.assertEqual(_safe_ratio(None, None), 0.0)


# ── Integration tests: collectors con DB vacía ───────────────────


class DashboardCollectorTest(TestCase):

    def setUp(self):
        self.company = _make_company()

    def test_collect_empty_db(self):
        """Con DB vacía, no debe lanzar excepción y retorna string."""
        result = DashboardCollector().collect(self.company, 'test')
        self.assertIsInstance(result, str)
        self.assertIn('## Resumen Financiero', result)
        self.assertIn('## Balance General', result)

    def test_collect_with_data(self):
        """Con movimientos, el resumen aparece correctamente."""
        from apps.contabilidad.models import MovimientoContable

        anio = date.today().year
        MovimientoContable.objects.create(
            company=self.company,
            conteo=1,
            auxiliar='4135050001.0000',
            auxiliar_nombre='Servicios',
            titulo_codigo=4,
            titulo_nombre='Ingresos',
            grupo_codigo=41,
            grupo_nombre='Operacionales',
            cuenta_codigo=4135,
            cuenta_nombre='Servicios',
            tercero_id='900111222',
            debito=Decimal('0'),
            credito=Decimal('5000000'),
            fecha=date(anio, 1, 15),
            periodo=f'{anio}-01',
        )

        result = DashboardCollector().collect(self.company, 'ingresos')
        self.assertIn('Ingresos', result)
        self.assertIn('5,000,000', result)

    def test_no_cross_tenant_data(self):
        """Los datos de otra empresa no aparecen."""
        from apps.contabilidad.models import MovimientoContable

        otra_empresa = _make_company('Otra SA', '900000002')
        anio = date.today().year
        MovimientoContable.objects.create(
            company=otra_empresa,
            conteo=99,
            auxiliar='4135050001.0000',
            auxiliar_nombre='Servicios',
            titulo_codigo=4,
            titulo_nombre='Ingresos',
            tercero_id='900000000',
            debito=Decimal('0'),
            credito=Decimal('99000000'),
            fecha=date(anio, 1, 1),
            periodo=f'{anio}-01',
        )

        result = DashboardCollector().collect(self.company, 'ingresos')
        # La empresa test no tiene movimientos — ingresos = 0
        self.assertIn('$0', result)


class ProyectosCollectorTest(TestCase):

    def setUp(self):
        self.company = _make_company()
        self.user = _make_user(self.company)

    def test_collect_empty_db(self):
        """Con DB vacía no lanza excepción."""
        result = ProyectosCollector().collect(self.company, 'proyectos', self.user)
        self.assertIsInstance(result, str)
        self.assertIn('## Proyectos Activos', result)
        self.assertIn('Sin proyectos activos', result)

    def test_collect_with_project(self):
        """Con proyectos, muestra el código y nombre."""
        from apps.proyectos.models import Project

        Project.all_objects.create(
            company=self.company,
            codigo='PRY-001',
            nombre='Proyecto Test',
            tipo='services',
            estado='in_progress',
            gerente=self.user,
            fecha_inicio_planificada=date.today(),
            fecha_fin_planificada=date.today(),
            presupuesto_total=Decimal('10000000'),
        )

        result = ProyectosCollector().collect(self.company, 'proyectos')
        self.assertIn('PRY-001', result)
        self.assertIn('Proyecto Test', result)


class TercerosCollectorTest(TestCase):

    def setUp(self):
        self.company = _make_company()

    def test_collect_empty_db(self):
        """Con DB vacía no lanza excepción."""
        result = TercerosCollector().collect(self.company, 'terceros')
        self.assertIsInstance(result, str)
        self.assertIn('## Resumen de Terceros', result)

    def test_collect_with_tercero(self):
        """Con terceros, muestra el conteo correcto."""
        from apps.terceros.models import Tercero

        Tercero.all_objects.create(
            company=self.company,
            codigo='T001',
            tipo_identificacion='nit',
            numero_identificacion='900111222',
            razon_social='Cliente Test SAS',
            nombre_completo='Cliente Test SAS',
            tipo_persona='juridica',
            tipo_tercero='cliente',
            activo=True,
        )

        result = TercerosCollector().collect(self.company, 'terceros')
        self.assertIn('Total: 1', result)
        self.assertIn('Activos: 1', result)


class ContabilidadCollectorTest(TestCase):

    def setUp(self):
        self.company = _make_company()

    def test_collect_empty_db(self):
        """Con DB vacía no lanza excepción."""
        result = ContabilidadCollector().collect(self.company, 'saldo')
        self.assertIsInstance(result, str)
        self.assertIn('## Balance de Prueba', result)

    def test_collect_with_movimientos(self):
        """Con movimientos muestra títulos correctamente."""
        from apps.contabilidad.models import MovimientoContable

        MovimientoContable.objects.create(
            company=self.company,
            conteo=1,
            auxiliar='1105050001.0000',
            auxiliar_nombre='Caja',
            titulo_codigo=1,
            titulo_nombre='Activo',
            tercero_id='900000000',
            debito=Decimal('1000000'),
            credito=Decimal('0'),
            fecha=date.today(),
            periodo=date.today().strftime('%Y-%m'),
        )

        result = ContabilidadCollector().collect(self.company, 'balance')
        self.assertIn('Activos', result)
        self.assertIn('1,000,000', result)


class GeneralCollectorTest(TestCase):

    def setUp(self):
        self.company = _make_company()
        self.user = _make_user(self.company)

    def test_collect_no_license(self):
        """Sin licencia no lanza excepción."""
        result = GeneralCollector().collect(self.company, 'info', self.user)
        self.assertIsInstance(result, str)
        self.assertIn('## Información de la Empresa', result)
        self.assertIn('Test SA', result)
        self.assertIn('900000001', result)

    def test_collect_with_modules(self):
        """Con módulos activos los muestra."""
        CompanyModule.objects.create(
            company=self.company,
            module='proyectos',
            is_active=True,
        )

        result = GeneralCollector().collect(self.company, 'módulos')
        self.assertIn('proyectos', result)

    def test_collect_user_info(self):
        """Cuando se pasa user, muestra su información."""
        result = GeneralCollector().collect(self.company, 'usuario', self.user)
        self.assertIn('## Usuario actual', result)
        self.assertIn(self.user.email, result)


# ── Registry test ─────────────────────────────────────────────────


class CollectorsRegistryTest(TestCase):

    def test_all_collectors_registered(self):
        """El registry tiene todos los collectors esperados."""
        expected = {'dashboard', 'contabilidad', 'proyectos', 'terceros', 'general'}
        self.assertEqual(set(COLLECTORS.keys()), expected)

    def test_all_collectors_have_collect_method(self):
        """Todos los collectors implementan collect()."""
        for name, collector in COLLECTORS.items():
            self.assertTrue(
                hasattr(collector, 'collect'),
                f'Collector "{name}" no tiene método collect()',
            )
