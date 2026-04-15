"""
SaiSuite -- Dashboard: Tests BIQueryEngine v2
Cubre: FilterTranslator, SOURCE_JOINS_MAP, _get_join_info, get_joins_map,
       nuevas fuentes, limite_registros, endpoint meta/joins/.
"""
import logging
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.test import APIClient

from apps.companies.models import Company
from apps.dashboard.bi_engine import (
    BIQueryEngine,
    FilterTranslator,
    SOURCE_BASE_FILTERS,
    SOURCE_FIELDS,
    SOURCE_JOINS_MAP,
    SOURCE_META,
    SOURCE_MODEL_MAP,
)
from apps.dashboard.services import ReportBIService
from apps.users.models import User

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures compartidos
# ─────────────────────────────────────────────────────────────────────────────

class BIv2BaseTestCase(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name='Empresa BI v2', nit='900222333')
        self.user = User.objects.create_user(
            email='biv2@test.com',
            password='testpass123',
            company=self.company,
        )
        self.engine = BIQueryEngine()


# ─────────────────────────────────────────────────────────────────────────────
# FilterTranslator
# ─────────────────────────────────────────────────────────────────────────────

class FilterTranslatorTest(TestCase):
    """Verifica que cada operador genere el lookup Django correcto."""

    def _translate(self, operator, field, value):
        return FilterTranslator.translate(operator, field, value)

    def test_eq(self):
        include, exclude = self._translate('eq', 'estado', 'A')
        self.assertEqual(include, {'estado': 'A'})
        self.assertEqual(exclude, {})

    def test_neq(self):
        include, exclude = self._translate('neq', 'estado', 'X')
        self.assertEqual(include, {})
        self.assertEqual(exclude, {'estado': 'X'})

    def test_contains(self):
        include, _ = self._translate('contains', 'nombre', 'alo')
        self.assertIn('nombre__icontains', include)
        self.assertEqual(include['nombre__icontains'], 'alo')

    def test_startswith(self):
        include, _ = self._translate('startswith', 'nombre', 'Sa')
        self.assertIn('nombre__istartswith', include)

    def test_endswith(self):
        include, _ = self._translate('endswith', 'nombre', 'Suite')
        self.assertIn('nombre__iendswith', include)

    def test_gt(self):
        include, _ = self._translate('gt', 'valor', 100)
        self.assertEqual(include, {'valor__gt': 100})

    def test_gte(self):
        include, _ = self._translate('gte', 'valor', 100)
        self.assertEqual(include, {'valor__gte': 100})

    def test_lt(self):
        include, _ = self._translate('lt', 'valor', 50)
        self.assertEqual(include, {'valor__lt': 50})

    def test_lte(self):
        include, _ = self._translate('lte', 'valor', 50)
        self.assertEqual(include, {'valor__lte': 50})

    def test_between(self):
        include, _ = self._translate('between', 'fecha', ['2026-01-01', '2026-03-31'])
        self.assertIn('fecha__gte', include)
        self.assertIn('fecha__lte', include)
        self.assertEqual(include['fecha__gte'], '2026-01-01')
        self.assertEqual(include['fecha__lte'], '2026-03-31')

    def test_in(self):
        include, _ = self._translate('in', 'tercero_id', ['1001', '1002'])
        self.assertEqual(include, {'tercero_id__in': ['1001', '1002']})

    def test_is_true(self):
        include, _ = self._translate('is_true', 'es_activo', None)
        self.assertEqual(include, {'es_activo': True})

    def test_is_false(self):
        include, _ = self._translate('is_false', 'es_activo', None)
        self.assertEqual(include, {'es_activo': False})

    def test_invalid_operator_raises(self):
        with self.assertRaises(DjangoValidationError):
            self._translate('like', 'nombre', 'test')


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE_JOINS_MAP / _get_join_info
# ─────────────────────────────────────────────────────────────────────────────

class JoinInfoTest(BIv2BaseTestCase):
    """Verifica la resolución bidireccional de relaciones."""

    def test_forward_join_fk(self):
        info = self.engine._get_join_info('facturacion', 'facturacion_detalle')
        self.assertIsNotNone(info)
        self.assertEqual(info['_direction'], 'forward')

    def test_reverse_join_fk(self):
        info = self.engine._get_join_info('facturacion_detalle', 'facturacion')
        self.assertIsNotNone(info)
        self.assertEqual(info['_direction'], 'reverse')

    def test_forward_subquery(self):
        info = self.engine._get_join_info('facturacion', 'terceros_saiopen')
        self.assertIsNotNone(info)
        self.assertEqual(info['type'], 'subquery')

    def test_unreachable_sources_returns_none(self):
        # No existe relación definida entre galería y inventario (ficticios)
        info = self.engine._get_join_info('no_existe_fuente_a', 'no_existe_fuente_b')
        self.assertIsNone(info)

    def test_joins_map_is_non_empty(self):
        self.assertGreater(len(SOURCE_JOINS_MAP), 0)

    def test_get_reachable_from_gl(self):
        reachable = self.engine.get_reachable_from('gl')
        self.assertIn('terceros_saiopen', reachable)
        self.assertIn('cuentas_contables', reachable)
        self.assertIn('proyectos_saiopen', reachable)

    def test_get_reachable_from_facturacion_detalle(self):
        reachable = self.engine.get_reachable_from('facturacion_detalle')
        self.assertIn('inventario', reachable)
        self.assertIn('productos', reachable)


# ─────────────────────────────────────────────────────────────────────────────
# get_joins_map (para el endpoint)
# ─────────────────────────────────────────────────────────────────────────────

class GetJoinsMapTest(BIv2BaseTestCase):
    """Verifica que get_joins_map retorna estructura correcta."""

    def test_returns_list(self):
        joins = self.engine.get_joins_map()
        self.assertIsInstance(joins, list)

    def test_each_entry_has_required_keys(self):
        joins = self.engine.get_joins_map()
        for entry in joins:
            self.assertIn('source_a', entry)
            self.assertIn('source_b', entry)
            self.assertIn('type', entry)
            self.assertIn('join_fields', entry)

    def test_all_joins_covered(self):
        joins = self.engine.get_joins_map()
        self.assertGreaterEqual(len(joins), len(SOURCE_JOINS_MAP))


# ─────────────────────────────────────────────────────────────────────────────
# Nuevas fuentes
# ─────────────────────────────────────────────────────────────────────────────

class NuevasFuentesTest(BIv2BaseTestCase):
    """Verifica que las 10 nuevas fuentes están registradas correctamente."""

    NEW_SOURCES = [
        'terceros_saiopen',
        'direcciones_envio',
        'cuentas_contables',
        'proyectos_saiopen',
        'actividades_saiopen',
        'departamentos',
        'centros_costo',
        'tipos_documento',
        'productos',
        'impuestos',
    ]

    def test_all_new_sources_in_source_model_map(self):
        for s in self.NEW_SOURCES:
            self.assertIn(s, SOURCE_MODEL_MAP, f'Fuente {s} no está en SOURCE_MODEL_MAP')

    def test_all_new_sources_have_fields(self):
        for s in self.NEW_SOURCES:
            self.assertIn(s, SOURCE_FIELDS, f'Fuente {s} no tiene campos en SOURCE_FIELDS')
            self.assertGreater(len(SOURCE_FIELDS[s]), 0, f'Fuente {s} tiene lista de campos vacía')

    def test_all_new_sources_have_meta(self):
        meta_keys = [m['key'] for m in SOURCE_META]
        for s in self.NEW_SOURCES:
            self.assertIn(s, meta_keys, f'Fuente {s} no tiene metadata en SOURCE_META')

    def test_departamentos_base_filter(self):
        self.assertIn('departamentos', SOURCE_BASE_FILTERS)
        self.assertEqual(SOURCE_BASE_FILTERS['departamentos'].get('tipo'), 'DP')

    def test_centros_costo_base_filter(self):
        self.assertIn('centros_costo', SOURCE_BASE_FILTERS)
        self.assertEqual(SOURCE_BASE_FILTERS['centros_costo'].get('tipo'), 'CC')

    def test_terceros_alias_present(self):
        """La fuente 'terceros' sigue presente como alias de retrocompatibilidad."""
        self.assertIn('terceros', SOURCE_MODEL_MAP)

    def test_get_available_sources_includes_new(self):
        sources = self.engine.get_available_sources()
        source_keys = [s['key'] for s in sources]
        for s in self.NEW_SOURCES:
            self.assertIn(s, source_keys)

    def _flatten_fields(self, source: str) -> list[str]:
        """Aplana SOURCE_FIELDS[source] (dict de categorías) a lista de nombres."""
        fields_by_cat = self.engine.get_available_fields(source)
        names = []
        for cat_fields in fields_by_cat.values():
            names.extend(f['field'] for f in cat_fields)
        return names

    def test_get_available_fields_productos(self):
        field_names = self._flatten_fields('productos')
        self.assertIn('codigo', field_names)
        self.assertIn('nombre', field_names)
        self.assertIn('precio_base', field_names)

    def test_get_available_fields_cuentas_contables(self):
        field_names = self._flatten_fields('cuentas_contables')
        self.assertIn('codigo', field_names)
        self.assertIn('descripcion', field_names)


# ─────────────────────────────────────────────────────────────────────────────
# Validación limite_registros
# ─────────────────────────────────────────────────────────────────────────────

class LimiteRegistrosValidationTest(BIv2BaseTestCase):
    """Verifica que limite_registros sin orden_config lanza ValidationError."""

    def setUp(self):
        super().setUp()

    def test_limite_sin_orden_raises_on_create(self):
        data = {
            'titulo': 'Top 10 sin orden',
            'fuentes': ['gl'],
            'campos_config': [],
            'limite_registros': 10,
            'orden_config': [],  # vacío
        }
        with self.assertRaises(DRFValidationError):
            ReportBIService.create_report(self.user, str(self.company.id), data)

    def test_limite_sin_orden_raises_on_update(self):
        from apps.dashboard.models import ReportBI
        report = ReportBI.objects.create(
            user=self.user,
            company=self.company,
            titulo='Reporte existente',
            fuentes=['gl'],
        )
        data = {
            'limite_registros': 10,
            'orden_config': [],
        }
        with self.assertRaises(DRFValidationError):
            ReportBIService.update_report(str(report.id), self.user, data)

    def test_limite_con_orden_valid(self):
        """No debe lanzar ValidationError si hay orden_config."""
        data = {
            'titulo': 'Top 10 con orden',
            'fuentes': ['gl'],
            'campos_config': [],
            'limite_registros': 10,
            'orden_config': [{'field': 'debito', 'direction': 'desc'}],
        }
        # No debe lanzar excepción
        ReportBIService._validate_limite_registros(data)

    def test_sin_limite_sin_orden_valid(self):
        """Sin limite_registros no valida orden."""
        data = {
            'titulo': 'Sin límite',
            'fuentes': ['gl'],
            'orden_config': [],
        }
        ReportBIService._validate_limite_registros(data)


# ─────────────────────────────────────────────────────────────────────────────
# Endpoint meta/joins/
# ─────────────────────────────────────────────────────────────────────────────

class BIJoinsEndpointTest(BIv2BaseTestCase):
    """Tests de integración para GET /api/v1/dashboard/reportes/meta/joins/"""

    def setUp(self):
        super().setUp()
        self.client = APIClient()

    def test_unauthenticated_returns_401(self):
        url = reverse('dashboard:bi-joins')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_returns_200(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:bi-joins')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_response_is_list(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:bi-joins')
        response = self.client.get(url)
        self.assertIsInstance(response.data, list)

    def test_response_entries_have_required_keys(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:bi-joins')
        response = self.client.get(url)
        for entry in response.data:
            self.assertIn('source_a', entry)
            self.assertIn('source_b', entry)
            self.assertIn('type', entry)


# ─────────────────────────────────────────────────────────────────────────────
# ReportBIService.get_joins
# ─────────────────────────────────────────────────────────────────────────────

class ReportBIServiceGetJoinsTest(BIv2BaseTestCase):
    """Verifica que el servicio delega correctamente a la engine."""

    def test_get_joins_returns_list(self):
        result = ReportBIService.get_joins()
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_get_joins_entries_structure(self):
        result = ReportBIService.get_joins()
        for entry in result:
            self.assertIn('source_a', entry)
            self.assertIn('source_b', entry)


# ─────────────────────────────────────────────────────────────────────────────
# ReportBIService.duplicate_report + endpoint /duplicate/
# ─────────────────────────────────────────────────────────────────────────────

class ReportBIDuplicateServiceTest(BIv2BaseTestCase):
    """Verifica la lógica de duplicación de reportes en el servicio."""

    def _create_report(self, titulo='Reporte original'):
        from apps.dashboard.models import ReportBI
        return ReportBI.objects.create(
            user=self.user,
            company=self.company,
            titulo=titulo,
            fuentes=['gl'],
            campos_config=[{'source': 'gl', 'field': 'debito', 'role': 'metric', 'label': 'Débito'}],
            filtros={},
            tipo_visualizacion='table',
        )

    def test_duplicate_creates_new_report(self):
        original = self._create_report()
        from apps.dashboard.models import ReportBI
        count_before = ReportBI.objects.filter(company=self.company).count()
        duplicated = ReportBIService.duplicate_report(original.id, self.user, 'Copia del reporte')
        count_after = ReportBI.objects.filter(company=self.company).count()
        self.assertEqual(count_after, count_before + 1)
        self.assertNotEqual(str(duplicated.id), str(original.id))

    def test_duplicate_copies_config(self):
        original = self._create_report('Original')
        duplicated = ReportBIService.duplicate_report(original.id, self.user, 'Copia')
        self.assertEqual(duplicated.fuentes, original.fuentes)
        self.assertEqual(duplicated.campos_config, original.campos_config)
        self.assertEqual(duplicated.tipo_visualizacion, original.tipo_visualizacion)

    def test_duplicate_resets_meta(self):
        original = self._create_report()
        duplicated = ReportBIService.duplicate_report(original.id, self.user, 'Copia test')
        self.assertEqual(duplicated.titulo, 'Copia test')
        self.assertFalse(duplicated.es_template)
        self.assertFalse(duplicated.es_favorito)
        self.assertTrue(duplicated.es_privado)
        self.assertEqual(str(duplicated.template_origen_id), str(original.id))

    def test_duplicate_assigns_current_user(self):
        """Un usuario puede duplicar un template de galería y el resultado es asignado a él."""
        from apps.dashboard.models import ReportBI
        other_user = type(self.user).objects.create_user(
            email='otro@test.com', password='pass', company=self.company,
        )
        # Crear un template de galería (accesible para todos en la empresa)
        original = ReportBI.objects.create(
            user=self.user, company=self.company,
            titulo='Template galería', fuentes=['gl'],
            campos_config=[], tipo_visualizacion='table',
            es_template=True, categoria_galeria='gerencial',
        )
        duplicated = ReportBIService.duplicate_report(original.id, other_user, 'Copia')
        self.assertEqual(str(duplicated.user_id), str(other_user.id))


class ReportBIDuplicateEndpointTest(BIv2BaseTestCase):
    """Tests de integración para POST /api/v1/dashboard/reportes/{id}/duplicate/"""

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        from apps.dashboard.models import ReportBI
        self.report = ReportBI.objects.create(
            user=self.user,
            company=self.company,
            titulo='Test report',
            fuentes=['gl'],
            campos_config=[],
            tipo_visualizacion='table',
        )

    def test_unauthenticated_returns_401(self):
        url = reverse('dashboard:report-bi-duplicate', kwargs={'report_id': self.report.id})
        response = self.client.post(url, {'titulo': 'Copia'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_duplicate_returns_201(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:report-bi-duplicate', kwargs={'report_id': self.report.id})
        response = self.client.post(url, {'titulo': 'Mi copia'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['titulo'], 'Mi copia')

    def test_duplicate_missing_titulo_returns_400(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:report-bi-duplicate', kwargs={'report_id': self.report.id})
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('titulo', response.data)

    def test_duplicate_blank_titulo_returns_400(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:report-bi-duplicate', kwargs={'report_id': self.report.id})
        response = self.client.post(url, {'titulo': '   '}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class _RemovedGalleryPlaceholder:  # galería eliminada — tests obsoletos removidos
    pass


class ReportBIGalleryEndpointTest(_RemovedGalleryPlaceholder):
    pass  # galería eliminada

    def test_filter_by_categoria(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:report-bi-gallery') + '?categoria=contabilidad'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['categoria'], 'contabilidad')

    def test_reporte_in_group_has_categoria_galeria(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:report-bi-gallery')
        response = self.client.get(url)
class ReportBICategoriaGaleriaCreateTest(BIv2BaseTestCase):
    """Tests de create/update con categoria_galeria."""

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.staff_user = User.objects.create_user(
            email='staff@test.com', password='pass',
            company=self.company, is_staff=True,
        )

    def test_non_staff_cannot_create_template(self):
        """Usuario normal no puede crear es_template=True."""
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:report-bi-list-create')
        data = {
            'titulo': 'Mi template', 'fuentes': ['gl'],
            'es_template': True, 'categoria_galeria': 'contabilidad',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # es_template debe quedar en False para usuario normal
        from apps.dashboard.models import ReportBI
        report = ReportBI.objects.get(id=response.data['id'])
        self.assertFalse(report.es_template)

    def test_staff_can_create_template(self):
        """Staff puede crear es_template=True."""
        self.client.force_authenticate(user=self.staff_user)
        url = reverse('dashboard:report-bi-list-create')
        data = {
            'titulo': 'Template staff', 'fuentes': ['gl'],
            'es_template': True, 'categoria_galeria': 'ventas',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        from apps.dashboard.models import ReportBI
        report = ReportBI.objects.get(id=response.data['id'])
        self.assertTrue(report.es_template)
        self.assertEqual(report.categoria_galeria, 'ventas')


# ─────────────────────────────────────────────────────────────────────────────
# Sprint 4: CardBIService — filtros 3 capas
# ─────────────────────────────────────────────────────────────────────────────

class CardBIServiceApplyOverridesTest(TestCase):
    """Tests para CardBIService._apply_overrides (capa 2)."""

    def _override(self, base, overrides):
        from apps.dashboard.services import CardBIService
        return CardBIService._apply_overrides(base, overrides)

    def test_override_existing_filter_value(self):
        """Override de valor en filtro existente: solo cambia value, no operator."""
        base = [{'source': 'gl', 'field': 'fecha', 'operator': 'between', 'value': ['2025-01-01', '2025-12-31']}]
        overrides = [{'source': 'gl', 'field': 'fecha', 'operator': 'between', 'value': ['2026-01-01', '2026-03-31']}]
        result = self._override(base, overrides)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['value'], ['2026-01-01', '2026-03-31'])
        self.assertEqual(result[0]['operator'], 'between')

    def test_override_adds_new_filter_when_no_match(self):
        """Override sin match por source+field: se agrega como nuevo filtro."""
        base = [{'source': 'gl', 'field': 'cuenta', 'operator': 'eq', 'value': '110505'}]
        overrides = [{'source': 'gl', 'field': 'tercero_id', 'operator': 'in', 'value': ['1001']}]
        result = self._override(base, overrides)
        self.assertEqual(len(result), 2)

    def test_override_empty_overrides_returns_base_unchanged(self):
        """Sin overrides retorna copia exacta de base."""
        base = [{'source': 'gl', 'field': 'fecha', 'operator': 'eq', 'value': '2026-01-01'}]
        result = self._override(base, [])
        self.assertEqual(result, base)
        # Debe ser copia, no la misma referencia
        result[0]['value'] = 'changed'
        self.assertEqual(base[0]['value'], '2026-01-01')

    def test_override_empty_base_appends_override(self):
        """Base vacía + override = lista con el override."""
        overrides = [{'source': 'facturacion', 'field': 'tercero_id', 'operator': 'in', 'value': ['99']}]
        result = self._override([], overrides)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['field'], 'tercero_id')

    def test_override_multiple_overrides_different_fields(self):
        """Múltiples overrides sobre diferentes campos."""
        base = [
            {'source': 'gl', 'field': 'fecha', 'operator': 'between', 'value': ['2025-01-01', '2025-12-31']},
            {'source': 'gl', 'field': 'tipo', 'operator': 'eq', 'value': 'FC'},
        ]
        overrides = [
            {'source': 'gl', 'field': 'fecha', 'operator': 'between', 'value': ['2026-01-01', '2026-06-30']},
            {'source': 'gl', 'field': 'tipo', 'operator': 'eq', 'value': 'ND'},
        ]
        result = self._override(base, overrides)
        self.assertEqual(len(result), 2)
        fecha_f = next(f for f in result if f['field'] == 'fecha')
        tipo_f = next(f for f in result if f['field'] == 'tipo')
        self.assertEqual(fecha_f['value'], ['2026-01-01', '2026-06-30'])
        self.assertEqual(tipo_f['value'], 'ND')


class CardBIServiceApplyDashboardFiltersTest(TestCase):
    """Tests para CardBIService._apply_dashboard_global_filters (capa 3)."""

    def _apply(self, filters, dashboard_filters):
        from apps.dashboard.services import CardBIService
        return CardBIService._apply_dashboard_global_filters(filters, dashboard_filters)

    def test_date_range_override(self):
        """fecha_desde + fecha_hasta actualizan filtro 'between' en campo fecha."""
        filters = [{'source': 'gl', 'field': 'fecha', 'operator': 'between', 'value': ['2025-01-01', '2025-12-31']}]
        result = self._apply(filters, {'fecha_desde': '2026-01-01', 'fecha_hasta': '2026-03-31'})
        self.assertEqual(result[0]['value'], ['2026-01-01', '2026-03-31'])

    def test_date_range_no_match_leaves_filters_unchanged(self):
        """Sin filtro 'between' de fecha: filtros no cambian."""
        filters = [{'source': 'gl', 'field': 'tipo', 'operator': 'eq', 'value': 'FC'}]
        result = self._apply(filters, {'fecha_desde': '2026-01-01', 'fecha_hasta': '2026-03-31'})
        self.assertEqual(result[0]['value'], 'FC')

    def test_periodo_override(self):
        """periodo actualiza filtro con field='periodo'."""
        filters = [{'source': 'gl', 'field': 'periodo', 'operator': 'eq', 'value': '202501'}]
        result = self._apply(filters, {'periodo': '202603'})
        self.assertEqual(result[0]['value'], '202603')

    def test_tercero_ids_override(self):
        """tercero_ids actualiza filtro 'in' en campo tercero_id."""
        filters = [{'source': 'facturacion', 'field': 'tercero_id', 'operator': 'in', 'value': ['1001']}]
        result = self._apply(filters, {'tercero_ids': ['2001', '2002']})
        self.assertEqual(result[0]['value'], ['2001', '2002'])

    def test_tercero_ids_scalar_becomes_list(self):
        """tercero_ids escalar se convierte a lista."""
        filters = [{'source': 'facturacion', 'field': 'tercero_id', 'operator': 'in', 'value': ['1001']}]
        result = self._apply(filters, {'tercero_ids': '3001'})
        self.assertIsInstance(result[0]['value'], list)
        self.assertIn('3001', result[0]['value'])

    def test_empty_dashboard_filters_noop(self):
        """Sin filtros de dashboard: retorna copia sin cambios."""
        filters = [{'source': 'gl', 'field': 'fecha', 'operator': 'between', 'value': ['2025-01-01', '2025-12-31']}]
        result = self._apply(filters, {})
        self.assertEqual(result, filters)
        result[0]['value'] = ['changed']
        self.assertNotEqual(filters[0]['value'], ['changed'])

    def test_does_not_add_new_filters(self):
        """La capa 3 NO agrega filtros nuevos — solo actualiza existentes."""
        filters = [{'source': 'gl', 'field': 'tipo', 'operator': 'eq', 'value': 'FC'}]
        result = self._apply(filters, {'fecha_desde': '2026-01-01', 'fecha_hasta': '2026-03-31', 'periodo': '202601'})
        self.assertEqual(len(result), 1, 'No se deben agregar filtros nuevos')


class CardBIServiceGetSelectableReportsTest(TestCase):
    """Tests para CardBIService.get_selectable_reports."""

    def setUp(self):
        from apps.dashboard.models import ReportBI
        self.company = Company.objects.create(name='Empresa Selectable', nit='900444555')
        self.user = User.objects.create_user(
            email='selectable@test.com', password='testpass', company=self.company,
        )
        # Crear reportes de diferentes tipos
        self.bar_report = ReportBI.objects.create(
            user=self.user, company=self.company,
            titulo='Bar', fuentes=['gl'], tipo_visualizacion='bar',
        )
        self.table_report = ReportBI.objects.create(
            user=self.user, company=self.company,
            titulo='Table', fuentes=['gl'], tipo_visualizacion='table',
        )
        self.pivot_report = ReportBI.objects.create(
            user=self.user, company=self.company,
            titulo='Pivot', fuentes=['gl'], tipo_visualizacion='pivot',
        )
        self.kpi_report = ReportBI.objects.create(
            user=self.user, company=self.company,
            titulo='KPI', fuentes=['gl'], tipo_visualizacion='kpi',
        )

    def test_excludes_table_and_pivot(self):
        """Solo retorna tipos gráficos, excluye table y pivot."""
        from apps.dashboard.services import CardBIService
        qs = CardBIService.get_selectable_reports(self.user, self.company.id)
        titles = list(qs.values_list('titulo', flat=True))
        self.assertIn('Bar', titles)
        self.assertIn('KPI', titles)
        self.assertNotIn('Table', titles)
        self.assertNotIn('Pivot', titles)

    def test_returns_all_chart_viz_types(self):
        """Retorna los 7 tipos gráficos."""
        from apps.dashboard.models import ReportBI
        from apps.dashboard.services import CardBIService
        for viz in ('line', 'pie', 'area', 'waterfall', 'gauge'):
            ReportBI.objects.create(
                user=self.user, company=self.company,
                titulo=viz, fuentes=['gl'], tipo_visualizacion=viz,
            )
        qs = CardBIService.get_selectable_reports(self.user, self.company.id)
        viz_types = set(qs.values_list('tipo_visualizacion', flat=True))
        self.assertTrue(
            {'bar', 'kpi', 'line', 'pie', 'area', 'waterfall', 'gauge'}.issubset(viz_types)
        )

    def test_multi_tenant_isolation(self):
        """No retorna reportes de otra empresa."""
        from apps.dashboard.models import ReportBI
        from apps.dashboard.services import CardBIService
        other_company = Company.objects.create(name='Otra', nit='111222333')
        other_user = User.objects.create_user(
            email='other@test.com', password='testpass', company=other_company,
        )
        ReportBI.objects.create(
            user=other_user, company=other_company,
            titulo='OtroBar', fuentes=['gl'], tipo_visualizacion='bar',
        )
        qs = CardBIService.get_selectable_reports(self.user, self.company.id)
        self.assertFalse(qs.filter(titulo='OtroBar').exists())
