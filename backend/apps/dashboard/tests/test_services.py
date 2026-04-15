"""
SaiSuite -- Dashboard: Service Tests
Tests para DashboardService, CardService, TrialService, FilterService,
CatalogService, ReportService. Multi-tenant isolation.
"""
import logging
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound

from apps.companies.models import Company, CompanyLicense
from apps.users.models import User
from apps.contabilidad.models import (
    MovimientoContable,
    ConfiguracionContable,
)
from apps.contabilidad.services import SyncService
from apps.dashboard.models import (
    Dashboard,
    DashboardCard,
    DashboardShare,
    ModuleTrial,
)
from apps.dashboard.services import (
    DashboardService,
    CardService,
    TrialService,
    FilterService,
    CatalogService,
    ReportService,
)

logger = logging.getLogger(__name__)


def _create_gl_records(company, records_data):
    """Helper: crea registros GL directamente via SyncService."""
    SyncService.process_gl_batch(company.id, records_data)


def _make_gl(conteo, titulo=1, debito='1000.00', credito='0.00', periodo='2026-01', **kw):
    """Helper: crea un dict GL record."""
    base = {
        'conteo': conteo,
        'auxiliar': '1105050001.0000',
        'auxiliar_nombre': 'Cuenta test',
        'titulo_codigo': titulo,
        'titulo_nombre': 'Test',
        'tercero_id': kw.get('tercero_id', '900111222'),
        'tercero_nombre': kw.get('tercero_nombre', 'Tercero Test'),
        'debito': debito,
        'credito': credito,
        'fecha': kw.get('fecha', date(2026, 1, 15)),
        'periodo': periodo,
    }
    for key in ('grupo_codigo', 'cuenta_codigo', 'proyecto_codigo',
                'proyecto_nombre', 'departamento_codigo', 'departamento_nombre',
                'centro_costo_codigo', 'centro_costo_nombre',
                'actividad_codigo', 'actividad_nombre', 'duedate'):
        if key in kw:
            base[key] = kw[key]
    return base


class DashboardServiceTest(TestCase):
    """Tests para DashboardService."""

    def setUp(self):
        self.company = Company.objects.create(
            name='Empresa Dashboard', nit='900111222',
        )
        self.user = User.objects.create_user(
            email='dashtest@empresa.com',
            password='testpass123',
            company=self.company,
        )
        self.user_b = User.objects.create_user(
            email='dashtest_b@empresa.com',
            password='testpass123',
            company=self.company,
        )

    def test_create_dashboard(self):
        """Crear un dashboard."""
        dashboard = DashboardService.create_dashboard(
            user=self.user,
            company_id=self.company.id,
            data={'titulo': 'Test Dashboard'},
        )
        self.assertEqual(dashboard.titulo, 'Test Dashboard')
        self.assertEqual(dashboard.user, self.user)

    def test_list_dashboards(self):
        """Listar dashboards propios."""
        DashboardService.create_dashboard(
            self.user, self.company.id, {'titulo': 'Dashboard 1'},
        )
        DashboardService.create_dashboard(
            self.user, self.company.id, {'titulo': 'Dashboard 2'},
        )
        dashboards = DashboardService.list_dashboards(self.user, self.company.id)
        self.assertEqual(dashboards.count(), 2)

    def test_list_includes_shared(self):
        """La lista incluye dashboards compartidos con el usuario."""
        dashboard = DashboardService.create_dashboard(
            self.user, self.company.id, {'titulo': 'Shared One'},
        )
        DashboardService.share_dashboard(
            dashboard.id, self.user, self.user_b.id,
        )
        dashboards = DashboardService.list_dashboards(self.user_b, self.company.id)
        self.assertEqual(dashboards.count(), 1)

    def test_update_dashboard(self):
        """Actualizar titulo de un dashboard."""
        dashboard = DashboardService.create_dashboard(
            self.user, self.company.id, {'titulo': 'Original'},
        )
        updated = DashboardService.update_dashboard(
            dashboard.id, self.user, {'titulo': 'Updated'},
        )
        self.assertEqual(updated.titulo, 'Updated')

    def test_update_by_non_owner_without_edit_permission(self):
        """Un usuario sin permiso de edicion no puede actualizar."""
        dashboard = DashboardService.create_dashboard(
            self.user, self.company.id, {'titulo': 'Protected'},
        )
        DashboardService.share_dashboard(
            dashboard.id, self.user, self.user_b.id, puede_editar=False,
        )
        with self.assertRaises(PermissionDenied):
            DashboardService.update_dashboard(
                dashboard.id, self.user_b, {'titulo': 'Hacked'},
            )

    def test_delete_by_non_owner(self):
        """Solo el dueno puede eliminar."""
        dashboard = DashboardService.create_dashboard(
            self.user, self.company.id, {'titulo': 'Mine'},
        )
        DashboardService.share_dashboard(
            dashboard.id, self.user, self.user_b.id,
        )
        with self.assertRaises(PermissionDenied):
            DashboardService.delete_dashboard(dashboard.id, self.user_b)

    def test_set_default(self):
        """Solo un dashboard puede ser default por usuario."""
        d1 = DashboardService.create_dashboard(
            self.user, self.company.id, {'titulo': 'D1'},
        )
        d2 = DashboardService.create_dashboard(
            self.user, self.company.id, {'titulo': 'D2'},
        )
        DashboardService.set_default(d1.id, self.user)
        DashboardService.set_default(d2.id, self.user)

        d1.refresh_from_db()
        d2.refresh_from_db()
        self.assertFalse(d1.es_default)
        self.assertTrue(d2.es_default)

    def test_toggle_favorite(self):
        """Toggle favorito cambia el estado."""
        dashboard = DashboardService.create_dashboard(
            self.user, self.company.id, {'titulo': 'Fav'},
        )
        self.assertFalse(dashboard.es_favorito)

        DashboardService.toggle_favorite(dashboard.id, self.user)
        dashboard.refresh_from_db()
        self.assertTrue(dashboard.es_favorito)

        DashboardService.toggle_favorite(dashboard.id, self.user)
        dashboard.refresh_from_db()
        self.assertFalse(dashboard.es_favorito)

    def test_share_and_revoke(self):
        """Compartir y revocar share."""
        dashboard = DashboardService.create_dashboard(
            self.user, self.company.id, {'titulo': 'Share Test'},
        )
        DashboardService.share_dashboard(
            dashboard.id, self.user, self.user_b.id,
        )
        self.assertEqual(DashboardShare.objects.count(), 1)

        DashboardService.revoke_share(dashboard.id, self.user_b.id)
        self.assertEqual(DashboardShare.objects.count(), 0)

    def test_cannot_share_with_self(self):
        """No se puede compartir consigo mismo."""
        dashboard = DashboardService.create_dashboard(
            self.user, self.company.id, {'titulo': 'Self Share'},
        )
        with self.assertRaises(ValidationError):
            DashboardService.share_dashboard(
                dashboard.id, self.user, self.user.id,
            )

    def test_multi_tenant_isolation(self):
        """Los dashboards de una empresa no aparecen en otra."""
        company_b = Company.objects.create(
            name='Empresa B', nit='900333444',
        )
        user_b = User.objects.create_user(
            email='other@empresab.com',
            password='testpass123',
            company=company_b,
        )

        DashboardService.create_dashboard(
            self.user, self.company.id, {'titulo': 'Company A'},
        )
        DashboardService.create_dashboard(
            user_b, company_b.id, {'titulo': 'Company B'},
        )

        dashboards_a = DashboardService.list_dashboards(self.user, self.company.id)
        dashboards_b = DashboardService.list_dashboards(user_b, company_b.id)
        self.assertEqual(dashboards_a.count(), 1)
        self.assertEqual(dashboards_b.count(), 1)


class CardServiceTest(TestCase):
    """Tests para CardService."""

    def setUp(self):
        self.company = Company.objects.create(
            name='Empresa Cards', nit='900444555',
        )
        self.user = User.objects.create_user(
            email='cards@empresa.com',
            password='testpass123',
            company=self.company,
        )
        self.dashboard = DashboardService.create_dashboard(
            self.user, self.company.id, {'titulo': 'Card Test'},
        )

    def test_add_card(self):
        """Agregar una tarjeta al dashboard."""
        card = CardService.add_card(self.dashboard.id, {
            'card_type_code': 'BALANCE_GENERAL',
            'chart_type': 'bar',
        })
        self.assertEqual(card.card_type_code, 'BALANCE_GENERAL')

    def test_add_invalid_card_type(self):
        """Tipo de tarjeta invalido lanza error."""
        with self.assertRaises(ValidationError):
            CardService.add_card(self.dashboard.id, {
                'card_type_code': 'INVALID_CARD',
            })

    def test_update_card(self):
        """Actualizar posicion de una tarjeta."""
        card = CardService.add_card(self.dashboard.id, {
            'card_type_code': 'EBITDA',
        })
        updated = CardService.update_card(card.id, {
            'pos_x': 2, 'pos_y': 1, 'width': 4,
        })
        self.assertEqual(updated.pos_x, 2)
        self.assertEqual(updated.width, 4)

    def test_delete_card(self):
        """Eliminar una tarjeta."""
        card = CardService.add_card(self.dashboard.id, {
            'card_type_code': 'EBITDA',
        })
        CardService.delete_card(card.id)
        self.assertEqual(DashboardCard.objects.count(), 0)

    def test_save_layout(self):
        """Guardar layout masivo de tarjetas."""
        c1 = CardService.add_card(self.dashboard.id, {
            'card_type_code': 'BALANCE_GENERAL',
        })
        c2 = CardService.add_card(self.dashboard.id, {
            'card_type_code': 'EBITDA',
        })

        count = CardService.save_layout(self.dashboard.id, [
            {'id': c1.id, 'pos_x': 0, 'pos_y': 0, 'width': 4, 'height': 3, 'orden': 0},
            {'id': c2.id, 'pos_x': 4, 'pos_y': 0, 'width': 4, 'height': 3, 'orden': 1},
        ])
        self.assertEqual(count, 2)

        c1.refresh_from_db()
        self.assertEqual(c1.width, 4)
        self.assertEqual(c1.pos_x, 0)


class TrialServiceTest(TestCase):
    """Tests para TrialService."""

    def setUp(self):
        self.company = Company.objects.create(
            name='Empresa Trial', nit='900666777',
        )

    def test_activate_trial(self):
        """Activar un trial."""
        trial = TrialService.activate_trial(self.company.id)
        self.assertEqual(trial.module_code, 'dashboard')
        self.assertTrue(trial.esta_activo())
        self.assertEqual(trial.dias_restantes(), 13)  # 14 minus partial day

    def test_cannot_activate_twice(self):
        """No se puede activar un trial dos veces."""
        TrialService.activate_trial(self.company.id)
        with self.assertRaises(ValidationError):
            TrialService.activate_trial(self.company.id)

    def test_trial_status_active(self):
        """Status muestra trial activo."""
        TrialService.activate_trial(self.company.id)
        status = TrialService.get_trial_status(self.company.id)
        self.assertTrue(status['tiene_acceso'])
        self.assertEqual(status['tipo_acceso'], 'trial')

    def test_access_via_license(self):
        """Acceso via licencia tiene prioridad sobre trial."""
        today = date.today()
        CompanyLicense.objects.create(
            company=self.company,
            status='active',
            starts_at=today - timedelta(days=30),
            expires_at=today + timedelta(days=30),
            modules_included=['dashboard'],
        )

        has_access, access_type = TrialService.check_dashboard_access(self.company.id)
        self.assertTrue(has_access)
        self.assertEqual(access_type, 'license')

    def test_no_access(self):
        """Sin licencia ni trial no hay acceso."""
        has_access, access_type = TrialService.check_dashboard_access(self.company.id)
        self.assertFalse(has_access)
        self.assertEqual(access_type, 'none')


class FilterServiceTest(TestCase):
    """Tests para FilterService."""

    def setUp(self):
        self.company = Company.objects.create(
            name='Empresa Filtros', nit='900888999',
        )
        # Create some GL records with diverse data
        records = [
            _make_gl(1, tercero_id='900111', tercero_nombre='Cliente A'),
            _make_gl(2, tercero_id='900222', tercero_nombre='Cliente B'),
            _make_gl(3, proyecto_codigo='P01', proyecto_nombre='Proyecto X'),
            _make_gl(4, departamento_codigo=10, departamento_nombre='Ventas'),
            _make_gl(5, periodo='2026-02', fecha=date(2026, 2, 15)),
        ]
        _create_gl_records(self.company, records)

    def test_get_terceros(self):
        """Retorna terceros unicos."""
        terceros = FilterService.get_available_terceros(self.company.id)
        self.assertTrue(len(terceros) >= 2)

    def test_get_terceros_with_query(self):
        """Busqueda de terceros por nombre."""
        terceros = FilterService.get_available_terceros(self.company.id, 'Cliente A')
        # FilterService retorna {'id', 'nombre'} (normalizado desde GL o Tercero)
        self.assertTrue(any(t['nombre'] == 'Cliente A' for t in terceros))

    def test_get_proyectos(self):
        """Retorna proyectos unicos."""
        proyectos = FilterService.get_available_proyectos(self.company.id)
        self.assertEqual(len(proyectos), 1)
        self.assertEqual(proyectos[0]['proyecto_codigo'], 'P01')

    def test_get_departamentos(self):
        """Retorna departamentos unicos."""
        deptos = FilterService.get_available_departamentos(self.company.id)
        self.assertEqual(len(deptos), 1)

    def test_get_periodos(self):
        """Retorna periodos unicos."""
        periodos = FilterService.get_available_periodos(self.company.id)
        self.assertTrue(len(periodos) >= 2)


class CatalogServiceTest(TestCase):
    """Tests para CatalogService."""

    def setUp(self):
        self.company = Company.objects.create(
            name='Empresa Catalog', nit='900101010',
        )

    def test_get_all_cards_without_config(self):
        """Sin configuracion retorna todas las tarjetas."""
        cards = CatalogService.get_available_cards(self.company.id)
        self.assertIn('BALANCE_GENERAL', cards)
        self.assertIn('ESTADO_RESULTADOS', cards)
        # Cards that require features should also be present (no config = no restriction)
        self.assertIn('GASTOS_POR_DEPARTAMENTO', cards)

    def test_get_cards_with_config_disabled(self):
        """Con configuracion sin departamentos, excluye tarjetas de departamento."""
        ConfiguracionContable.objects.create(
            company=self.company,
            usa_departamentos_cc=False,
            usa_proyectos_actividades=False,
        )
        cards = CatalogService.get_available_cards(self.company.id)
        self.assertIn('BALANCE_GENERAL', cards)
        self.assertNotIn('GASTOS_POR_DEPARTAMENTO', cards)
        self.assertNotIn('COSTO_POR_PROYECTO', cards)

    def test_get_cards_with_config_enabled(self):
        """Con configuracion habilitada, incluye tarjetas especializadas."""
        ConfiguracionContable.objects.create(
            company=self.company,
            usa_departamentos_cc=True,
            usa_proyectos_actividades=True,
        )
        cards = CatalogService.get_available_cards(self.company.id)
        self.assertIn('GASTOS_POR_DEPARTAMENTO', cards)
        self.assertIn('COSTO_POR_PROYECTO', cards)

    def test_get_categories(self):
        """Las categorias tienen estructura correcta."""
        categories = CatalogService.get_categories(self.company.id)
        self.assertTrue(len(categories) > 0)
        first = categories[0]
        self.assertIn('code', first)
        self.assertIn('nombre', first)
        self.assertIn('cards', first)


class ReportServiceTest(TestCase):
    """Tests para ReportService y ReportEngine."""

    def setUp(self):
        self.company = Company.objects.create(
            name='Empresa Reportes', nit='900202020',
        )
        # Create GL records that represent a basic set of accounting data
        records = [
            # Activos (titulo 1)
            _make_gl(1, titulo=1, debito='50000.00', credito='0.00',
                     grupo_codigo=11, cuenta_codigo=1105),
            _make_gl(2, titulo=1, debito='30000.00', credito='0.00',
                     grupo_codigo=13, cuenta_codigo=1305),
            _make_gl(3, titulo=1, debito='10000.00', credito='0.00',
                     grupo_codigo=14, cuenta_codigo=1435),
            # Pasivos (titulo 2)
            _make_gl(10, titulo=2, debito='0.00', credito='20000.00',
                     grupo_codigo=22, cuenta_codigo=2205),
            _make_gl(11, titulo=2, debito='0.00', credito='10000.00',
                     grupo_codigo=23, cuenta_codigo=2335),
            # Patrimonio (titulo 3)
            _make_gl(20, titulo=3, debito='0.00', credito='60000.00',
                     grupo_codigo=31, cuenta_codigo=3105),
            # Ingresos (titulo 4)
            _make_gl(30, titulo=4, debito='0.00', credito='100000.00',
                     grupo_codigo=41, cuenta_codigo=4135),
            # Gastos (titulo 5)
            _make_gl(40, titulo=5, debito='25000.00', credito='0.00',
                     grupo_codigo=51, cuenta_codigo=5105),
            _make_gl(41, titulo=5, debito='15000.00', credito='0.00',
                     grupo_codigo=52, cuenta_codigo=5205),
            # Costos (titulo 6)
            _make_gl(50, titulo=6, debito='40000.00', credito='0.00',
                     grupo_codigo=61, cuenta_codigo=6135),
        ]
        _create_gl_records(self.company, records)

    def test_balance_general(self):
        """Balance general calcula activo, pasivo y patrimonio."""
        result = ReportService.get_card_data(
            self.company.id, 'BALANCE_GENERAL', {},
        )
        self.assertEqual(len(result['labels']), 3)
        self.assertIn('activo', result['summary'])
        self.assertIn('pasivo', result['summary'])
        self.assertIn('patrimonio', result['summary'])

        activo = Decimal(result['summary']['activo'])
        self.assertEqual(activo, Decimal('90000.00'))

    def test_estado_resultados(self):
        """Estado de resultados calcula utilidad neta."""
        result = ReportService.get_card_data(
            self.company.id, 'ESTADO_RESULTADOS', {},
        )
        utilidad_neta = Decimal(result['summary']['utilidad_neta'])
        # Ingresos(100k) - Costos(40k) - Gastos(40k) = 20k
        self.assertEqual(utilidad_neta, Decimal('20000.00'))

    def test_indicadores_liquidez(self):
        """Indicadores de liquidez calculan razon corriente."""
        result = ReportService.get_card_data(
            self.company.id, 'INDICADORES_LIQUIDEZ', {},
        )
        razon = Decimal(result['summary']['razon_corriente'])
        # AC = 50k(11) + 30k(13) + 10k(14) = 90k
        # PC = 20k(22) + 10k(23) = 30k
        # RC = 90/30 = 3.00
        self.assertEqual(razon, Decimal('3.00'))

    def test_margen_bruto_neto(self):
        """Margenes de rentabilidad."""
        result = ReportService.get_card_data(
            self.company.id, 'MARGEN_BRUTO_NETO', {},
        )
        margen_bruto = Decimal(result['summary']['margen_bruto'])
        # (100k - 40k) / 100k * 100 = 60%
        self.assertEqual(margen_bruto, Decimal('60.00'))

    def test_empty_company(self):
        """Empresa sin datos retorna resultado vacio."""
        empty_company = Company.objects.create(
            name='Empresa Vacia', nit='900303030',
        )
        result = ReportService.get_card_data(
            empty_company.id, 'BALANCE_GENERAL', {},
        )
        self.assertEqual(result['summary']['activo'], '0.00')
        self.assertEqual(result['summary']['pasivo'], '0.00')

    def test_invalid_card_type(self):
        """Tipo de tarjeta invalido lanza error."""
        with self.assertRaises(ValidationError):
            ReportService.get_card_data(
                self.company.id, 'INVALID_TYPE', {},
            )

    def test_filter_by_periodo(self):
        """Filtrar por periodo reduce los datos."""
        result = ReportService.get_card_data(
            self.company.id, 'BALANCE_GENERAL',
            {'periodo': '2026-01'},
        )
        # Should have data (all records are in 2026-01)
        activo = Decimal(result['summary']['activo'])
        self.assertTrue(activo > 0)

    def test_filter_by_nonexistent_periodo(self):
        """Filtrar por periodo sin datos retorna ceros."""
        result = ReportService.get_card_data(
            self.company.id, 'BALANCE_GENERAL',
            {'periodo': '2099-12'},
        )
        activo = Decimal(result['summary']['activo'])
        self.assertEqual(activo, Decimal('0.00'))

    def test_costo_ventas(self):
        """Costo de ventas retorna total titulo 6."""
        result = ReportService.get_card_data(
            self.company.id, 'COSTO_VENTAS', {},
        )
        costos = Decimal(result['summary']['costo_ventas'])
        self.assertEqual(costos, Decimal('40000.00'))

    def test_gastos_operacionales(self):
        """Gastos operacionales desglosados por grupo."""
        result = ReportService.get_card_data(
            self.company.id, 'GASTOS_OPERACIONALES', {},
        )
        self.assertTrue(len(result['labels']) > 0)
        total = Decimal(result['summary']['total_gastos'])
        self.assertEqual(total, Decimal('40000.00'))

    def test_tendencia_mensual(self):
        """Tendencia mensual retorna datos por periodo."""
        result = ReportService.get_card_data(
            self.company.id, 'TENDENCIA_MENSUAL', {},
        )
        self.assertIn('2026-01', result['labels'])
        self.assertEqual(len(result['datasets']), 3)

    def test_comparativo_periodos_missing_params(self):
        """Comparativo sin periodos retorna error en summary."""
        result = ReportService.get_card_data(
            self.company.id, 'COMPARATIVO_PERIODOS', {},
        )
        self.assertIn('error', result['summary'])

    def test_multi_tenant_isolation(self):
        """Los reportes de una empresa no mezclan datos de otra."""
        company_b = Company.objects.create(
            name='Empresa B Reportes', nit='900404040',
        )
        _create_gl_records(company_b, [
            _make_gl(1, titulo=1, debito='999999.00', credito='0.00'),
        ])

        result_a = ReportService.get_card_data(
            self.company.id, 'BALANCE_GENERAL', {},
        )
        result_b = ReportService.get_card_data(
            company_b.id, 'BALANCE_GENERAL', {},
        )

        activo_a = Decimal(result_a['summary']['activo'])
        activo_b = Decimal(result_b['summary']['activo'])
        self.assertNotEqual(activo_a, activo_b)
