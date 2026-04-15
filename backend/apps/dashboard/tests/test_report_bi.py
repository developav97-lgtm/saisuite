"""
SaiSuite -- Dashboard: Tests para ReportBI, BIQueryEngine y ReportBIService.
"""
import logging
from datetime import date
from decimal import Decimal

from django.db import IntegrityError
from django.test import TestCase

from apps.companies.models import Company
from apps.contabilidad.models import MovimientoContable, MovimientoCartera
from apps.dashboard.bi_engine import (
    BIQueryEngine,
    SOURCE_MODEL_MAP,
    SOURCE_FIELDS,
    SOURCE_FILTERS,
    SOURCE_META,
)
from apps.dashboard.models import ReportBI, ReportBIShare
from apps.dashboard.services import ReportBIService
from apps.users.models import User

logger = logging.getLogger(__name__)


class ReportBIModelTest(TestCase):
    """Tests para los modelos ReportBI y ReportBIShare."""

    def setUp(self):
        self.company = Company.objects.create(name='Empresa BI', nit='900111222')
        self.user = User.objects.create_user(
            email='bi@test.com',
            password='testpass123',
            company=self.company,
        )
        self.user2 = User.objects.create_user(
            email='bi2@test.com',
            password='testpass123',
            company=self.company,
        )

    def _create_report(self, **kwargs):
        defaults = {
            'user': self.user,
            'company': self.company,
            'titulo': 'Reporte Test',
            'fuentes': ['gl'],
            'campos_config': [
                {'source': 'gl', 'field': 'tercero_nombre', 'role': 'dimension', 'label': 'Tercero'},
                {'source': 'gl', 'field': 'debito', 'role': 'metric', 'aggregation': 'SUM', 'label': 'Total Débito'},
            ],
            'tipo_visualizacion': 'table',
        }
        defaults.update(kwargs)
        return ReportBI.all_objects.create(**defaults)

    def test_create_report(self):
        report = self._create_report()
        self.assertEqual(report.titulo, 'Reporte Test')
        self.assertEqual(report.fuentes, ['gl'])
        self.assertEqual(report.tipo_visualizacion, 'table')
        self.assertIsNotNone(report.id)
        self.assertIsNotNone(report.created_at)

    def test_str_representation(self):
        report = self._create_report()
        self.assertIn('Reporte Test', str(report))
        self.assertIn(self.user.email, str(report))

    def test_default_values(self):
        report = self._create_report()
        self.assertTrue(report.es_privado)
        self.assertFalse(report.es_favorito)
        self.assertFalse(report.es_template)
        self.assertEqual(report.filtros, {})
        self.assertEqual(report.orden_config, [])
        self.assertIsNone(report.limite_registros)
        self.assertIsNone(report.template_origen)

    def test_share_unique_together(self):
        report = self._create_report()
        ReportBIShare.objects.create(
            reporte=report,
            compartido_con=self.user2,
            compartido_por=self.user,
        )
        with self.assertRaises(IntegrityError):
            ReportBIShare.objects.create(
                reporte=report,
                compartido_con=self.user2,
                compartido_por=self.user,
            )

    def test_share_str(self):
        report = self._create_report()
        share = ReportBIShare.objects.create(
            reporte=report,
            compartido_con=self.user2,
            compartido_por=self.user,
        )
        self.assertIn('Reporte Test', str(share))
        self.assertIn(self.user2.email, str(share))

    def test_cascade_delete_report_deletes_shares(self):
        report = self._create_report()
        ReportBIShare.objects.create(
            reporte=report,
            compartido_con=self.user2,
            compartido_por=self.user,
        )
        report.delete()
        self.assertEqual(ReportBIShare.objects.count(), 0)

    def test_template_origen_set_null(self):
        template = self._create_report(titulo='Template', es_template=True)
        derived = self._create_report(titulo='Derivado', template_origen=template)
        self.assertEqual(derived.template_origen_id, template.id)
        template.delete()
        derived.refresh_from_db()
        self.assertIsNone(derived.template_origen)


class BIQueryEngineTest(TestCase):
    """Tests para el motor de consultas BI."""

    def setUp(self):
        self.company = Company.objects.create(name='Empresa Engine', nit='900222333')
        self.engine = BIQueryEngine()

        # Crear datos de prueba en MovimientoContable
        for i in range(5):
            MovimientoContable.objects.create(
                company=self.company,
                conteo=i + 1,
                auxiliar=Decimal('1105050001.0000'),
                auxiliar_nombre='Caja general',
                titulo_codigo=1,
                titulo_nombre='Activo',
                tercero_id='900111222' if i < 3 else '900333444',
                tercero_nombre='Cliente A' if i < 3 else 'Cliente B',
                debito=Decimal('1000000.00'),
                credito=Decimal('0.00'),
                tipo='CE',
                fecha=date(2026, 3, 1 + i),
                periodo='2026-03',
            )

    def test_source_model_map_keys(self):
        # v1: 5 fuentes transaccionales; v2 agregó 10 dimensionales + 1 legacy = 16 total
        original_sources = {'gl', 'facturacion', 'facturacion_detalle', 'cartera', 'inventario'}
        self.assertTrue(original_sources.issubset(set(SOURCE_MODEL_MAP.keys())))
        self.assertEqual(len(SOURCE_MODEL_MAP), 16)

    def test_get_available_sources(self):
        sources = self.engine.get_available_sources()
        # v2: 5 transaccionales + 10 dimensionales Saiopen + 1 legacy = 16
        self.assertEqual(len(sources), 16)
        keys = {s['key'] for s in sources}
        self.assertIn('gl', keys)
        self.assertIn('cartera', keys)

    def test_get_available_fields_gl(self):
        fields = self.engine.get_available_fields('gl')
        self.assertIn('Cuenta contable', fields)
        self.assertIn('Valores', fields)
        self.assertIn('Tercero', fields)

    def test_get_available_fields_invalid(self):
        fields = self.engine.get_available_fields('nonexistent')
        self.assertEqual(fields, {})

    def test_get_available_filters_gl(self):
        filters = self.engine.get_available_filters('gl')
        self.assertTrue(len(filters) > 0)
        keys = {f['key'] for f in filters}
        self.assertIn('fecha_desde', keys)
        self.assertIn('periodos', keys)

    def test_execute_dimensions_only(self):
        class _R:
            fuentes = ['gl']
            campos_config = [
                {'field': 'tercero_nombre', 'role': 'dimension', 'label': 'Tercero'},
            ]
            tipo_visualizacion = 'table'
            filtros = {}
            orden_config = []
            limite_registros = None

        result = self.engine.execute(_R(), self.company.id)
        self.assertIn('columns', result)
        self.assertIn('rows', result)
        self.assertIn('total_count', result)
        self.assertTrue(result['total_count'] > 0)

    def test_execute_with_aggregation(self):
        class _R:
            fuentes = ['gl']
            campos_config = [
                {'field': 'tercero_nombre', 'role': 'dimension', 'label': 'Tercero'},
                {'field': 'debito', 'role': 'metric', 'aggregation': 'SUM', 'label': 'Total Débito'},
            ]
            tipo_visualizacion = 'table'
            filtros = {}
            orden_config = []
            limite_registros = None

        result = self.engine.execute(_R(), self.company.id)
        self.assertEqual(len(result['columns']), 2)
        self.assertEqual(result['columns'][0]['field'], 'tercero_nombre')
        self.assertEqual(result['columns'][1]['field'], 'debito_sum')
        # Should be 2 rows (2 distinct terceros)
        self.assertEqual(len(result['rows']), 2)
        # Check aggregated values
        total_a = [r for r in result['rows'] if r['tercero_nombre'] == 'Cliente A'][0]
        self.assertEqual(total_a['debito_sum'], 3000000.0)

    def test_execute_metrics_only_no_dimensions(self):
        class _R:
            fuentes = ['gl']
            campos_config = [
                {'field': 'debito', 'role': 'metric', 'aggregation': 'SUM', 'label': 'Total'},
            ]
            tipo_visualizacion = 'table'
            filtros = {}
            orden_config = []
            limite_registros = None

        result = self.engine.execute(_R(), self.company.id)
        self.assertEqual(len(result['rows']), 1)
        self.assertEqual(result['rows'][0]['debito_sum'], 5000000.0)

    def test_execute_with_filters(self):
        class _R:
            fuentes = ['gl']
            campos_config = [
                {'field': 'tercero_nombre', 'role': 'dimension', 'label': 'Tercero'},
                {'field': 'debito', 'role': 'metric', 'aggregation': 'SUM', 'label': 'Total'},
            ]
            tipo_visualizacion = 'table'
            filtros = {'tercero_ids': ['900111222']}
            orden_config = []
            limite_registros = None

        result = self.engine.execute(_R(), self.company.id)
        self.assertEqual(len(result['rows']), 1)
        self.assertEqual(result['rows'][0]['tercero_nombre'], 'Cliente A')

    def test_execute_with_ordering(self):
        class _R:
            fuentes = ['gl']
            campos_config = [
                {'field': 'tercero_nombre', 'role': 'dimension', 'label': 'Tercero'},
                {'field': 'debito', 'role': 'metric', 'aggregation': 'SUM', 'label': 'Total'},
            ]
            tipo_visualizacion = 'table'
            filtros = {}
            orden_config = [{'field': 'debito_sum', 'direction': 'desc'}]
            limite_registros = None

        result = self.engine.execute(_R(), self.company.id)
        self.assertEqual(result['rows'][0]['tercero_nombre'], 'Cliente A')

    def test_execute_with_limit(self):
        class _R:
            fuentes = ['gl']
            campos_config = [
                {'field': 'tercero_nombre', 'role': 'dimension', 'label': 'Tercero'},
                {'field': 'debito', 'role': 'metric', 'aggregation': 'SUM', 'label': 'Total'},
            ]
            tipo_visualizacion = 'table'
            filtros = {}
            orden_config = []
            limite_registros = 1

        result = self.engine.execute(_R(), self.company.id)
        self.assertEqual(len(result['rows']), 1)
        self.assertEqual(result['total_count'], 2)

    def test_execute_empty_fuentes(self):
        class _R:
            fuentes = []
            campos_config = []
            tipo_visualizacion = 'table'
            filtros = {}
            orden_config = []
            limite_registros = None

        result = self.engine.execute(_R(), self.company.id)
        self.assertEqual(result['rows'], [])

    def test_execute_invalid_field_ignored(self):
        class _R:
            fuentes = ['gl']
            campos_config = [
                {'field': 'fake_field', 'role': 'dimension', 'label': 'Fake'},
            ]
            tipo_visualizacion = 'table'
            filtros = {}
            orden_config = []
            limite_registros = None

        result = self.engine.execute(_R(), self.company.id)
        self.assertEqual(result['rows'], [])
        self.assertEqual(result['columns'], [])

    def test_execute_pivot(self):
        class _R:
            fuentes = ['gl']
            campos_config = []
            tipo_visualizacion = 'pivot'
            filtros = {}
            orden_config = []
            limite_registros = None
            viz_config = {
                'rows': ['tercero_nombre'],
                'columns': ['periodo'],
                'values': [{'field': 'debito', 'aggregation': 'SUM'}],
            }

        result = self.engine.execute_pivot(_R(), self.company.id)
        self.assertIn('row_headers', result)
        self.assertIn('col_headers', result)
        self.assertIn('data', result)
        self.assertIn('grand_total', result)
        self.assertEqual(len(result['row_headers']), 2)
        self.assertEqual(len(result['col_headers']), 1)

    def test_execute_pivot_empty(self):
        class _R:
            fuentes = []
            campos_config = []
            tipo_visualizacion = 'pivot'
            filtros = {}
            orden_config = []
            limite_registros = None
            viz_config = {}

        result = self.engine.execute_pivot(_R(), self.company.id)
        self.assertEqual(result['row_headers'], [])

    def test_multi_tenant_isolation(self):
        """Engine solo retorna datos de la empresa solicitada."""
        other_company = Company.objects.create(name='Otra Empresa', nit='900999888')
        MovimientoContable.objects.create(
            company=other_company,
            conteo=999,
            auxiliar=Decimal('1105050001.0000'),
            auxiliar_nombre='Caja',
            tercero_id='900999888',
            debito=Decimal('999999.00'),
            credito=Decimal('0.00'),
            fecha=date(2026, 3, 1),
            periodo='2026-03',
        )

        class _R:
            fuentes = ['gl']
            campos_config = [
                {'field': 'debito', 'role': 'metric', 'aggregation': 'SUM', 'label': 'Total'},
            ]
            tipo_visualizacion = 'table'
            filtros = {}
            orden_config = []
            limite_registros = None

        result = self.engine.execute(_R(), self.company.id)
        self.assertEqual(result['rows'][0]['debito_sum'], 5000000.0)


class BIQueryEngineCarteraTest(TestCase):
    """Tests del engine con fuente de cartera."""

    def setUp(self):
        self.company = Company.objects.create(name='Empresa Cart', nit='900444555')
        self.engine = BIQueryEngine()
        MovimientoCartera.objects.create(
            company=self.company,
            conteo=1,
            tercero_id='900111222',
            tercero_nombre='Cliente X',
            cuenta_contable=Decimal('1305050001.0000'),
            tipo='FA',
            fecha=date(2026, 3, 1),
            periodo='2026-03',
            debito=Decimal('500000.00'),
            saldo=Decimal('500000.00'),
            tipo_cartera='CXC',
        )

    def test_execute_cartera(self):
        class _R:
            fuentes = ['cartera']
            campos_config = [
                {'field': 'tercero_nombre', 'role': 'dimension', 'label': 'Tercero'},
                {'field': 'saldo', 'role': 'metric', 'aggregation': 'SUM', 'label': 'Saldo'},
            ]
            tipo_visualizacion = 'table'
            filtros = {'tipo_cartera': 'CXC'}
            orden_config = []
            limite_registros = None

        result = self.engine.execute(_R(), self.company.id)
        self.assertEqual(len(result['rows']), 1)
        self.assertEqual(result['rows'][0]['saldo_sum'], 500000.0)


class ReportBIServiceTest(TestCase):
    """Tests para ReportBIService (CRUD + ejecución)."""

    def setUp(self):
        self.company = Company.objects.create(name='Empresa Svc', nit='900555666')
        self.user = User.objects.create_user(
            email='svc@test.com',
            password='testpass123',
            company=self.company,
        )
        self.user2 = User.objects.create_user(
            email='svc2@test.com',
            password='testpass123',
            company=self.company,
        )
        self.report_data = {
            'titulo': 'Ventas Q1',
            'fuentes': ['gl'],
            'campos_config': [
                {'source': 'gl', 'field': 'tercero_nombre', 'role': 'dimension', 'label': 'Tercero'},
                {'source': 'gl', 'field': 'debito', 'role': 'metric', 'aggregation': 'SUM', 'label': 'Total'},
            ],
        }

    def test_create_report(self):
        report = ReportBIService.create_report(
            self.user, self.company.id, self.report_data,
        )
        self.assertEqual(report.titulo, 'Ventas Q1')
        self.assertEqual(report.user, self.user)
        self.assertEqual(report.company, self.company)

    def test_list_reports(self):
        ReportBIService.create_report(self.user, self.company.id, self.report_data)
        reports = ReportBIService.list_reports(self.user, self.company.id)
        self.assertEqual(reports.count(), 1)

    def test_get_report_owner(self):
        report = ReportBIService.create_report(
            self.user, self.company.id, self.report_data,
        )
        fetched = ReportBIService.get_report(report.id, self.user)
        self.assertEqual(fetched.id, report.id)

    def test_get_report_no_access(self):
        report = ReportBIService.create_report(
            self.user, self.company.id, self.report_data,
        )
        from rest_framework.exceptions import PermissionDenied
        with self.assertRaises(PermissionDenied):
            ReportBIService.get_report(report.id, self.user2)

    def test_get_report_shared(self):
        report = ReportBIService.create_report(
            self.user, self.company.id, self.report_data,
        )
        ReportBIService.share_report(report.id, self.user, self.user2.id)
        fetched = ReportBIService.get_report(report.id, self.user2)
        self.assertEqual(fetched.id, report.id)

    def test_update_report(self):
        report = ReportBIService.create_report(
            self.user, self.company.id, self.report_data,
        )
        updated = ReportBIService.update_report(
            report.id, self.user, {'titulo': 'Ventas Q2'},
        )
        self.assertEqual(updated.titulo, 'Ventas Q2')

    def test_delete_report(self):
        report = ReportBIService.create_report(
            self.user, self.company.id, self.report_data,
        )
        ReportBIService.delete_report(report.id, self.user)
        self.assertEqual(ReportBI.all_objects.count(), 0)

    def test_delete_report_non_owner_denied(self):
        report = ReportBIService.create_report(
            self.user, self.company.id, self.report_data,
        )
        ReportBIService.share_report(report.id, self.user, self.user2.id)
        from rest_framework.exceptions import PermissionDenied
        with self.assertRaises(PermissionDenied):
            ReportBIService.delete_report(report.id, self.user2)

    def test_toggle_favorite(self):
        report = ReportBIService.create_report(
            self.user, self.company.id, self.report_data,
        )
        self.assertFalse(report.es_favorito)
        updated = ReportBIService.toggle_favorite(report.id, self.user)
        self.assertTrue(updated.es_favorito)
        updated2 = ReportBIService.toggle_favorite(report.id, self.user)
        self.assertFalse(updated2.es_favorito)

    def test_share_report(self):
        report = ReportBIService.create_report(
            self.user, self.company.id, self.report_data,
        )
        share = ReportBIService.share_report(report.id, self.user, self.user2.id)
        self.assertFalse(share.puede_editar)

    def test_share_self_denied(self):
        report = ReportBIService.create_report(
            self.user, self.company.id, self.report_data,
        )
        from rest_framework.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            ReportBIService.share_report(report.id, self.user, self.user.id)

    def test_revoke_share(self):
        report = ReportBIService.create_report(
            self.user, self.company.id, self.report_data,
        )
        ReportBIService.share_report(report.id, self.user, self.user2.id)
        ReportBIService.revoke_share(report.id, self.user2.id)
        self.assertEqual(ReportBIShare.objects.count(), 0)

    def test_execute_preview(self):
        MovimientoContable.objects.create(
            company=self.company,
            conteo=1,
            auxiliar=Decimal('1105050001.0000'),
            auxiliar_nombre='Caja',
            tercero_id='900111222',
            tercero_nombre='Test',
            debito=Decimal('100.00'),
            credito=Decimal('0.00'),
            fecha=date(2026, 3, 1),
            periodo='2026-03',
        )
        result = ReportBIService.execute_preview(self.report_data, self.company.id)
        self.assertIn('columns', result)
        self.assertIn('rows', result)
        self.assertEqual(len(result['rows']), 1)

    def test_get_sources(self):
        sources = ReportBIService.get_sources()
        # v2: 5 transaccionales + 10 dimensionales Saiopen + 1 legacy = 16
        self.assertEqual(len(sources), 16)

    def test_get_fields(self):
        fields = ReportBIService.get_fields('gl')
        self.assertIn('Valores', fields)

    def test_get_fields_invalid_source(self):
        from rest_framework.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            ReportBIService.get_fields('invalid')

    def test_get_filters(self):
        filters = ReportBIService.get_filters('cartera')
        keys = {f['key'] for f in filters}
        self.assertIn('tipo_cartera', keys)

    def test_list_shared_reports(self):
        report = ReportBIService.create_report(
            self.user, self.company.id, self.report_data,
        )
        ReportBIService.share_report(report.id, self.user, self.user2.id)
        reports = ReportBIService.list_reports(self.user2, self.company.id)
        self.assertEqual(reports.count(), 1)

    def test_export_pdf_returns_bytes(self):
        """Test PDF export generates valid bytes. Requiere reportlab instalado."""
        try:
            import reportlab  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest('reportlab no instalado en entorno de test')
        report = ReportBIService.create_report(
            self.user, self.company.id, self.report_data,
        )
        pdf_bytes = ReportBIService.export_pdf(report, self.company.id)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(len(pdf_bytes) > 0)
        # PDF magic bytes
        self.assertTrue(pdf_bytes[:4] == b'%PDF')


class BITemplatesTest(TestCase):
    """Tests para templates BI predefinidos y el comando seed."""

    def setUp(self):
        self.company = Company.objects.create(name='Empresa Templates', nit='900333444')
        self.user = User.objects.create_user(
            email='tpl@test.com',
            password='testpass123',
            company=self.company,
        )

    def test_template_catalog_has_expected_entries(self):
        from apps.dashboard.bi_templates import REPORT_TEMPLATES
        # 23 templates originales + 5 nuevos con campos de retenciones y dimensiones
        self.assertEqual(len(REPORT_TEMPLATES), 28)

    def test_all_templates_have_required_keys(self):
        from apps.dashboard.bi_templates import REPORT_TEMPLATES
        required = {'titulo', 'descripcion', 'fuentes', 'campos_config',
                    'tipo_visualizacion', 'viz_config', 'filtros',
                    'orden_config', 'limite_registros'}
        for tpl in REPORT_TEMPLATES:
            self.assertTrue(
                required.issubset(tpl.keys()),
                f'Template "{tpl.get("titulo")}" missing keys: {required - tpl.keys()}',
            )

    def test_all_template_sources_are_valid(self):
        from apps.dashboard.bi_templates import REPORT_TEMPLATES
        from apps.dashboard.bi_engine import SOURCE_MODEL_MAP
        valid_sources = set(SOURCE_MODEL_MAP.keys())
        for tpl in REPORT_TEMPLATES:
            for src in tpl['fuentes']:
                self.assertIn(src, valid_sources, f'Invalid source "{src}" in "{tpl["titulo"]}"')

    def test_all_template_fields_are_valid(self):
        from apps.dashboard.bi_templates import REPORT_TEMPLATES
        from apps.dashboard.bi_engine import SOURCE_FIELDS
        for tpl in REPORT_TEMPLATES:
            for campo in tpl['campos_config']:
                src = campo['source']
                field_name = campo['field']
                all_fields = []
                for cat_fields in SOURCE_FIELDS.get(src, {}).values():
                    all_fields.extend(f['field'] for f in cat_fields)
                self.assertIn(
                    field_name, all_fields,
                    f'Field "{field_name}" not in source "{src}" for "{tpl["titulo"]}"',
                )

    def test_seed_command_creates_templates(self):
        from django.core.management import call_command
        call_command('seed_bi_templates', str(self.company.id))
        templates = ReportBI.all_objects.filter(
            company=self.company, es_template=True,
        )
        self.assertEqual(templates.count(), 28)

    def test_seed_command_idempotent(self):
        from django.core.management import call_command
        call_command('seed_bi_templates', str(self.company.id))
        call_command('seed_bi_templates', str(self.company.id))
        templates = ReportBI.all_objects.filter(
            company=self.company, es_template=True,
        )
        self.assertEqual(templates.count(), 28)

    def test_seed_command_force_recreates(self):
        from django.core.management import call_command
        call_command('seed_bi_templates', str(self.company.id))
        first_ids = set(
            ReportBI.all_objects.filter(company=self.company, es_template=True)
            .values_list('id', flat=True),
        )
        call_command('seed_bi_templates', str(self.company.id), '--force')
        second_ids = set(
            ReportBI.all_objects.filter(company=self.company, es_template=True)
            .values_list('id', flat=True),
        )
        self.assertEqual(len(second_ids), 28)
        self.assertTrue(first_ids.isdisjoint(second_ids))

    def test_list_templates_returns_seeded(self):
        from django.core.management import call_command
        call_command('seed_bi_templates', str(self.company.id))
        templates = ReportBIService.list_templates(self.company.id)
        self.assertEqual(templates.count(), 28)

    def test_get_template_catalog_static(self):
        catalog = ReportBIService.get_template_catalog()
        self.assertEqual(len(catalog), 28)
        self.assertIn('titulo', catalog[0])
        self.assertIn('descripcion', catalog[0])
        self.assertIn('categoria_galeria', catalog[0])

    def test_template_unique_titles(self):
        from apps.dashboard.bi_templates import REPORT_TEMPLATES
        titles = [t['titulo'] for t in REPORT_TEMPLATES]
        self.assertEqual(len(titles), len(set(titles)))

    def test_seeded_templates_are_not_private(self):
        from django.core.management import call_command
        call_command('seed_bi_templates', str(self.company.id))
        all_private = ReportBI.all_objects.filter(
            company=self.company, es_template=True, es_privado=True,
        ).count()
        self.assertEqual(all_private, 0)


class CfoSuggestReportTest(TestCase):
    """Tests para CfoVirtualService.suggest_report."""

    def setUp(self):
        self.company = Company.objects.create(name='Empresa Suggest', nit='900555666')
        self.user = User.objects.create_user(
            email='suggest@test.com',
            password='testpass123',
            company=self.company,
        )

    def test_suggest_report_returns_dict_with_expected_keys(self):
        """Test the suggest_report method structure (mocked)."""
        from unittest.mock import patch, MagicMock
        import json

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': json.dumps({
                        'template_titulo': 'Aging de CxC',
                        'explanation': 'Este reporte muestra el aging de cartera.',
                    }),
                },
            }],
            'usage': {'prompt_tokens': 50, 'completion_tokens': 30},
            'model': 'gpt-4o-mini',
        }
        mock_response.raise_for_status = MagicMock()

        with patch('apps.dashboard.services.requests.post', return_value=mock_response), \
             patch('apps.dashboard.services.settings', OPENAI_API_KEY='test-key'), \
             patch('apps.companies.services.AIUsageService.check_quota', return_value={'allowed': True}), \
             patch('apps.companies.services.AIUsageService.record_usage'):
            from apps.dashboard.services import CfoVirtualService
            result = CfoVirtualService.suggest_report('¿Quién me debe?', self.company, self.user)

        self.assertIn('template_titulo', result)
        self.assertIn('explanation', result)
        self.assertIn('config', result)
        self.assertIn('categoria_galeria', result)
        self.assertEqual(result['template_titulo'], 'Aging de CxC')
        self.assertEqual(result['categoria_galeria'], 'cuentas_cobrar')
        self.assertIsNotNone(result['config'])

    def test_suggest_report_no_match(self):
        """Test suggest_report when no template matches."""
        from unittest.mock import patch, MagicMock
        import json

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': json.dumps({
                        'template_titulo': None,
                        'explanation': 'No hay template para eso.',
                    }),
                },
            }],
            'usage': {'prompt_tokens': 50, 'completion_tokens': 20},
            'model': 'gpt-4o-mini',
        }
        mock_response.raise_for_status = MagicMock()

        with patch('apps.dashboard.services.requests.post', return_value=mock_response), \
             patch('apps.dashboard.services.settings', OPENAI_API_KEY='test-key'), \
             patch('apps.companies.services.AIUsageService.check_quota', return_value={'allowed': True}), \
             patch('apps.companies.services.AIUsageService.record_usage'):
            from apps.dashboard.services import CfoVirtualService
            result = CfoVirtualService.suggest_report('¿Cómo está el clima?', self.company, self.user)

        self.assertIsNone(result['template_titulo'])
        self.assertIsNone(result['config'])


class TestReportBIValidator(TestCase):
    """Tests para ReportBIValidator — validaciones de integridad de configuración."""

    def setUp(self):
        from apps.dashboard.services import ReportBIValidator
        self.validator = ReportBIValidator

    # ── validate_sources ─────────────────────────────────────────────────────

    def test_validate_sources_valid(self):
        """Fuentes válidas no lanzan excepción."""
        self.validator.validate_sources(['gl', 'facturacion'])  # no debe lanzar

    def test_validate_sources_invalid(self):
        """Fuente desconocida lanza ValidationError con el nombre inválido."""
        from rest_framework.exceptions import ValidationError
        with self.assertRaises(ValidationError) as ctx:
            self.validator.validate_sources(['gl', 'fuente_inexistente'])
        self.assertIn('fuente_inexistente', str(ctx.exception.detail))

    # ── validate_campos_config ────────────────────────────────────────────────

    def test_validate_campos_config_valid(self):
        """Campos con source y field correctos no lanzan excepción."""
        self.validator.validate_campos_config(
            [{'source': 'gl', 'field': 'debito', 'role': 'metric'}],
            ['gl'],
        )

    def test_validate_campos_config_source_not_in_fuentes(self):
        """Campo con source que no está en fuentes lanza ValidationError."""
        from rest_framework.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.validator.validate_campos_config(
                [{'source': 'cartera', 'field': 'saldo', 'role': 'metric'}],
                ['gl'],  # cartera no está en fuentes
            )

    def test_validate_campos_config_unknown_field(self):
        """Campo con field inexistente en la fuente lanza ValidationError."""
        from rest_framework.exceptions import ValidationError
        with self.assertRaises(ValidationError) as ctx:
            self.validator.validate_campos_config(
                [{'source': 'gl', 'field': 'campo_falso', 'role': 'dimension'}],
                ['gl'],
            )
        self.assertIn('campo_falso', str(ctx.exception.detail))

    def test_validate_campos_config_invalid_role(self):
        """Role inválido lanza ValidationError."""
        from rest_framework.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.validator.validate_campos_config(
                [{'source': 'gl', 'field': 'debito', 'role': 'invalid_role'}],
                ['gl'],
            )

    def test_validate_campos_config_missing_source(self):
        """Campo sin 'source' lanza ValidationError."""
        from rest_framework.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.validator.validate_campos_config(
                [{'field': 'debito', 'role': 'metric'}],
                ['gl'],
            )

    # ── validate_joins ────────────────────────────────────────────────────────

    def test_validate_joins_single_source(self):
        """Una sola fuente no requiere JOIN — no lanza excepción."""
        self.validator.validate_joins(['gl'])

    def test_validate_joins_valid_pair(self):
        """Par con JOIN definido en SOURCE_JOINS_MAP no lanza excepción."""
        self.validator.validate_joins(['facturacion', 'facturacion_detalle'])

    def test_validate_joins_no_join_defined(self):
        """Par sin JOIN definido lanza ValidationError."""
        from rest_framework.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            # gl e impuestos no tienen JOIN directo
            self.validator.validate_joins(['gl', 'impuestos'])

    # ── validate_viz_config ───────────────────────────────────────────────────

    def test_validate_viz_config_non_pivot_ignored(self):
        """Para tipo != pivot, viz_config con cualquier contenido no lanza excepción."""
        self.validator.validate_viz_config(
            {'invalid_key': 'anything'},
            'bar',
            [{'source': 'gl', 'field': 'debito', 'role': 'metric'}],
        )

    def test_validate_viz_config_pivot_valid(self):
        """viz_config pivot válido (campos existen en campos_config) no lanza."""
        self.validator.validate_viz_config(
            {
                'row_fields': ['vendedor'],
                'col_fields': ['periodo'],
                'value_fields': [{'field': 'total', 'aggregation': 'SUM'}],
            },
            'pivot',
            [
                {'source': 'facturacion', 'field': 'vendedor', 'role': 'dimension'},
                {'source': 'facturacion', 'field': 'periodo', 'role': 'dimension'},
                {'source': 'facturacion', 'field': 'total', 'role': 'metric'},
            ],
        )

    def test_validate_viz_config_pivot_missing_field(self):
        """viz_config pivot con campo no en campos_config lanza ValidationError."""
        from rest_framework.exceptions import ValidationError
        with self.assertRaises(ValidationError) as ctx:
            self.validator.validate_viz_config(
                {'row_fields': ['campo_inexistente'], 'col_fields': ['periodo'], 'value_fields': []},
                'pivot',
                [{'source': 'facturacion', 'field': 'periodo', 'role': 'dimension'}],
            )
        self.assertIn('campo_inexistente', str(ctx.exception.detail))

    # ── validate_orden_config ─────────────────────────────────────────────────

    def test_validate_orden_config_valid(self):
        """Orden con campo existente y dirección válida no lanza excepción."""
        self.validator.validate_orden_config(
            [{'field': 'debito', 'direction': 'desc'}],
            [{'source': 'gl', 'field': 'debito', 'role': 'metric'}],
        )

    def test_validate_orden_config_invalid_direction(self):
        """Dirección inválida ('DESC' en mayúsculas) lanza ValidationError."""
        from rest_framework.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.validator.validate_orden_config(
                [{'field': 'debito', 'direction': 'DESC'}],  # debe ser lowercase
                [{'source': 'gl', 'field': 'debito', 'role': 'metric'}],
            )

    def test_validate_orden_config_unknown_field(self):
        """Campo de ordenamiento no en campos_config lanza ValidationError."""
        from rest_framework.exceptions import ValidationError
        with self.assertRaises(ValidationError) as ctx:
            self.validator.validate_orden_config(
                [{'field': 'campo_fantasma', 'direction': 'asc'}],
                [{'source': 'gl', 'field': 'debito', 'role': 'metric'}],
            )
        self.assertIn('campo_fantasma', str(ctx.exception.detail))

    # ── validate_all integración ──────────────────────────────────────────────

    def test_validate_all_valid_config(self):
        """Configuración completa válida no lanza excepción."""
        self.validator.validate_all(
            fuentes=['facturacion'],
            campos_config=[
                {'source': 'facturacion', 'field': 'tercero_nombre', 'role': 'dimension'},
                {'source': 'facturacion', 'field': 'total', 'role': 'metric'},
            ],
            viz_config={},
            tipo_visualizacion='table',
            orden_config=[{'field': 'total', 'direction': 'desc'}],
        )

    def test_validate_all_invalid_source_stops_early(self):
        """Fuente inválida en validate_all lanza antes de llegar a campos."""
        from rest_framework.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.validator.validate_all(
                fuentes=['fuente_inexistente'],
                campos_config=[{'source': 'fuente_inexistente', 'field': 'x'}],
                viz_config={},
                tipo_visualizacion='table',
                orden_config=[],
            )

    # ── suggest_report retorna categoria_galeria ──────────────────────────────

    def test_suggest_report_returns_categoria_galeria(self):
        """suggest_report ahora incluye categoria_galeria en la respuesta."""
        from unittest.mock import patch, MagicMock
        import json
        from apps.companies.models import Company
        from apps.users.models import User

        company = Company.objects.create(name='Test Co Suggest', nit='900877665')
        user = User.objects.create_user(
            email='bi.suggest@test.com', password='pass', company=company,
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': json.dumps({
                'template_titulo': 'Ventas por Vendedor',
                'explanation': 'Muestra ventas por vendedor.',
            })}}],
            'usage': {'prompt_tokens': 40, 'completion_tokens': 20},
            'model': 'gpt-4o-mini',
        }
        mock_response.raise_for_status = MagicMock()

        with patch('apps.dashboard.services.requests.post', return_value=mock_response), \
             patch('apps.dashboard.services.settings', OPENAI_API_KEY='test-key'), \
             patch('apps.companies.services.AIUsageService.check_quota', return_value={'allowed': True}), \
             patch('apps.companies.services.AIUsageService.record_usage'):
            from apps.dashboard.services import CfoVirtualService
            result = CfoVirtualService.suggest_report('¿Cómo van las ventas?', company, user)

        self.assertIn('categoria_galeria', result)
        self.assertEqual(result['template_titulo'], 'Ventas por Vendedor')
        self.assertEqual(result['categoria_galeria'], 'ventas')
        self.assertIsNotNone(result['config'])
