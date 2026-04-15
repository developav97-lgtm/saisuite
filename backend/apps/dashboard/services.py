"""
SaiSuite -- Dashboard: Services
TODA la logica de negocio va aqui. Las views solo orquestan.
"""
import datetime
import logging
from datetime import timedelta

import requests
from django.conf import settings
from django.db import transaction
from django.db.models import Q, QuerySet, Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound

from apps.contabilidad.models import MovimientoContable, ConfiguracionContable
from apps.terceros.models import Tercero
from apps.dashboard.card_catalog import CARD_CATALOG, get_available_cards, get_categories_with_cards
from apps.dashboard.models import (
    Dashboard,
    DashboardCard,
    DashboardShare,
    ModuleTrial,
    ReportBI,
    ReportBIShare,
)
from apps.dashboard.report_engine import ReportEngine
from apps.dashboard.bi_engine import BIQueryEngine

logger = logging.getLogger(__name__)

_TRIAL_DURATION_DAYS = 14
_MODULE_CODE = 'dashboard'

_report_engine = ReportEngine()
_bi_engine = BIQueryEngine()


# ──────────────────────────────────────────────
# Dashboard Service
# ──────────────────────────────────────────────

class DashboardService:
    """Servicio para operaciones CRUD de dashboards."""

    @staticmethod
    def list_dashboards(user, company_id) -> QuerySet:
        """
        Lista dashboards del usuario + dashboards compartidos con el.
        Solo dashboards de la misma empresa.
        """
        own = Dashboard.all_objects.filter(
            user=user,
            company_id=company_id,
        )
        shared_dashboard_ids = DashboardShare.objects.filter(
            compartido_con=user,
            dashboard__company_id=company_id,
        ).values_list('dashboard_id', flat=True)

        return Dashboard.all_objects.filter(
            Q(id__in=own.values_list('id', flat=True))
            | Q(id__in=shared_dashboard_ids)
        ).select_related('user').distinct()

    @staticmethod
    def create_dashboard(user, company_id, data: dict) -> Dashboard:
        """Crea un nuevo dashboard para el usuario."""
        dashboard = Dashboard(
            user=user,
            company_id=company_id,
            titulo=data['titulo'],
            es_privado=data.get('es_privado', True),
            orientacion=data.get('orientacion', 'portrait'),
            filtros_default=data.get('filtros_default', {}),
        )
        dashboard.save()

        logger.info(
            'dashboard_created',
            extra={
                'dashboard_id': str(dashboard.id),
                'user_id': str(user.id),
                'company_id': str(company_id),
            },
        )
        return dashboard

    @staticmethod
    def get_dashboard(dashboard_id, user) -> Dashboard:
        """
        Obtiene un dashboard por ID. Verifica que el usuario tenga acceso.
        """
        try:
            dashboard = Dashboard.all_objects.select_related('user').get(id=dashboard_id)
        except Dashboard.DoesNotExist:
            raise NotFound('Dashboard no encontrado.')

        # Owner has access
        if dashboard.user_id == user.id:
            return dashboard

        # Shared users have access
        if DashboardShare.objects.filter(
            dashboard=dashboard,
            compartido_con=user,
        ).exists():
            return dashboard

        # Staff has access
        if getattr(user, 'is_staff', False) or getattr(user, 'is_superadmin', False):
            return dashboard

        raise PermissionDenied('No tienes acceso a este dashboard.')

    @staticmethod
    def update_dashboard(dashboard_id, user, data: dict) -> Dashboard:
        """Actualiza un dashboard. Solo el dueno puede editar."""
        dashboard = DashboardService.get_dashboard(dashboard_id, user)

        # Check edit permission
        if dashboard.user_id != user.id:
            share = DashboardShare.objects.filter(
                dashboard=dashboard, compartido_con=user,
            ).first()
            if not share or not share.puede_editar:
                raise PermissionDenied('No tienes permiso para editar este dashboard.')

        for field in ('titulo', 'descripcion', 'es_privado', 'orientacion', 'filtros_default'):
            if field in data:
                setattr(dashboard, field, data[field])

        dashboard.save()

        logger.info(
            'dashboard_updated',
            extra={'dashboard_id': str(dashboard_id), 'user_id': str(user.id)},
        )
        return dashboard

    @staticmethod
    def delete_dashboard(dashboard_id, user) -> None:
        """Elimina un dashboard. Solo el dueno puede eliminar."""
        dashboard = DashboardService.get_dashboard(dashboard_id, user)

        if dashboard.user_id != user.id:
            raise PermissionDenied('Solo el creador puede eliminar el dashboard.')

        dashboard.delete()

        logger.info(
            'dashboard_deleted',
            extra={'dashboard_id': str(dashboard_id), 'user_id': str(user.id)},
        )

    @staticmethod
    def set_default(dashboard_id, user) -> Dashboard:
        """Marca un dashboard como default. Solo uno por usuario."""
        dashboard = DashboardService.get_dashboard(dashboard_id, user)

        if dashboard.user_id != user.id:
            raise PermissionDenied('Solo el creador puede marcar como default.')

        with transaction.atomic():
            # Remove default from all other dashboards of this user
            Dashboard.all_objects.filter(
                user=user, es_default=True,
            ).update(es_default=False)

            dashboard.es_default = True
            dashboard.save(update_fields=['es_default', 'updated_at'])

        logger.info(
            'dashboard_set_default',
            extra={'dashboard_id': str(dashboard_id), 'user_id': str(user.id)},
        )
        return dashboard

    @staticmethod
    def toggle_favorite(dashboard_id, user) -> Dashboard:
        """Alterna el estado de favorito."""
        dashboard = DashboardService.get_dashboard(dashboard_id, user)

        dashboard.es_favorito = not dashboard.es_favorito
        dashboard.save(update_fields=['es_favorito', 'updated_at'])

        logger.info(
            'dashboard_toggle_favorite',
            extra={
                'dashboard_id': str(dashboard_id),
                'es_favorito': dashboard.es_favorito,
            },
        )
        return dashboard

    @staticmethod
    def list_shared_with_me(user, company_id) -> QuerySet:
        """Lista dashboards compartidos con el usuario."""
        shared_ids = DashboardShare.objects.filter(
            compartido_con=user,
            dashboard__company_id=company_id,
        ).values_list('dashboard_id', flat=True)

        return Dashboard.all_objects.filter(
            id__in=shared_ids,
        ).select_related('user')

    @staticmethod
    def share_dashboard(dashboard_id, user, target_user_id, puede_editar=False) -> DashboardShare:
        """Comparte un dashboard con otro usuario."""
        dashboard = DashboardService.get_dashboard(dashboard_id, user)

        if dashboard.user_id != user.id:
            raise PermissionDenied('Solo el creador puede compartir el dashboard.')

        if str(target_user_id) == str(user.id):
            raise ValidationError('No puedes compartir un dashboard contigo mismo.')

        # Verify target user exists and is in the same company
        from apps.users.models import User
        try:
            target_user = User.objects.get(id=target_user_id)
        except User.DoesNotExist:
            raise NotFound('Usuario no encontrado.')

        if target_user.company_id != dashboard.company_id:
            raise ValidationError('Solo puedes compartir con usuarios de la misma empresa.')

        share, is_new = DashboardShare.objects.get_or_create(
            dashboard=dashboard,
            compartido_con=target_user,
            defaults={
                'compartido_por': user,
                'puede_editar': puede_editar,
            },
        )

        if not is_new:
            share.puede_editar = puede_editar
            share.save(update_fields=['puede_editar'])

        logger.info(
            'dashboard_shared',
            extra={
                'dashboard_id': str(dashboard_id),
                'target_user_id': str(target_user_id),
                'puede_editar': puede_editar,
            },
        )
        return share

    @staticmethod
    def revoke_share(dashboard_id, share_user_id) -> None:
        """Revoca un share."""
        deleted, _ = DashboardShare.objects.filter(
            dashboard_id=dashboard_id,
            compartido_con_id=share_user_id,
        ).delete()

        if deleted == 0:
            raise NotFound('Share no encontrado.')

        logger.info(
            'dashboard_share_revoked',
            extra={
                'dashboard_id': str(dashboard_id),
                'user_id': str(share_user_id),
            },
        )


# ──────────────────────────────────────────────
# Card Service
# ──────────────────────────────────────────────

class CardService:
    """Servicio para operaciones CRUD de tarjetas de dashboard."""

    @staticmethod
    def list_cards(dashboard_id) -> QuerySet:
        """Lista tarjetas de un dashboard."""
        return DashboardCard.objects.filter(
            dashboard_id=dashboard_id,
        ).order_by('orden', 'pos_y', 'pos_x')

    @staticmethod
    def add_card(dashboard_id, data: dict) -> DashboardCard:
        """Agrega una tarjeta al dashboard."""
        card_type_code = data['card_type_code']

        # Tipo especial bi_report: referencia a un ReportBI existente
        if card_type_code == 'bi_report':
            bi_report_id = data.get('bi_report_id')
            if not bi_report_id:
                raise ValidationError('bi_report_id es requerido para tarjetas de tipo bi_report.')
            try:
                bi_report = ReportBI.objects.get(id=bi_report_id)
            except ReportBI.DoesNotExist:
                raise NotFound('Reporte BI no encontrado.')

            card = DashboardCard.objects.create(
                dashboard_id=dashboard_id,
                card_type_code='bi_report',
                chart_type=bi_report.tipo_visualizacion,
                bi_report=bi_report,
                pos_x=data.get('pos_x', 0),
                pos_y=data.get('pos_y', 0),
                width=data.get('width', 3),
                height=data.get('height', 2),
                filtros_config=data.get('filtros_config', {}),
                titulo_personalizado=data.get('titulo_personalizado', ''),
                orden=data.get('orden', 0),
            )
            logger.info(
                'bi_report_card_added',
                extra={
                    'dashboard_id': str(dashboard_id),
                    'bi_report_id': str(bi_report_id),
                    'card_id': card.id,
                },
            )
            return card

        # Validate card type exists in catalog
        if card_type_code not in CARD_CATALOG:
            raise ValidationError(f'Tipo de tarjeta no valido: {card_type_code}')

        card = DashboardCard.objects.create(
            dashboard_id=dashboard_id,
            card_type_code=card_type_code,
            chart_type=data.get('chart_type', CARD_CATALOG[card_type_code]['chart_default']),
            pos_x=data.get('pos_x', 0),
            pos_y=data.get('pos_y', 0),
            width=data.get('width', 2),
            height=data.get('height', 2),
            filtros_config=data.get('filtros_config', {}),
            titulo_personalizado=data.get('titulo_personalizado', ''),
            orden=data.get('orden', 0),
        )

        logger.info(
            'card_added',
            extra={
                'dashboard_id': str(dashboard_id),
                'card_type_code': card_type_code,
                'card_id': card.id,
            },
        )
        return card

    @staticmethod
    def update_card(card_id, data: dict) -> DashboardCard:
        """Actualiza una tarjeta."""
        try:
            card = DashboardCard.objects.get(id=card_id)
        except DashboardCard.DoesNotExist:
            raise NotFound('Tarjeta no encontrada.')

        update_fields = []
        for field in (
            'chart_type', 'pos_x', 'pos_y', 'width', 'height',
            'filtros_config', 'titulo_personalizado', 'orden',
        ):
            if field in data:
                setattr(card, field, data[field])
                update_fields.append(field)

        # Actualizar bi_report si se indica
        if 'bi_report_id' in data:
            bi_report_id = data['bi_report_id']
            if bi_report_id is None:
                card.bi_report = None
                update_fields.append('bi_report')
            else:
                try:
                    card.bi_report = ReportBI.objects.get(id=bi_report_id)
                    update_fields.append('bi_report')
                except ReportBI.DoesNotExist:
                    raise NotFound('Reporte BI no encontrado.')

        if update_fields:
            card.save(update_fields=update_fields)

        logger.info(
            'card_updated',
            extra={'card_id': card_id, 'fields': update_fields},
        )
        return card

    @staticmethod
    def delete_card(card_id) -> None:
        """Elimina una tarjeta."""
        deleted, _ = DashboardCard.objects.filter(id=card_id).delete()
        if deleted == 0:
            raise NotFound('Tarjeta no encontrada.')

        logger.info('card_deleted', extra={'card_id': card_id})

    @staticmethod
    def save_layout(dashboard_id, layout_data: list[dict]) -> int:
        """
        Guarda el layout completo de tarjetas (posiciones y tamanios).
        Retorna la cantidad de tarjetas actualizadas.
        """
        count = 0
        with transaction.atomic():
            for item in layout_data:
                updated = DashboardCard.objects.filter(
                    id=item['id'],
                    dashboard_id=dashboard_id,
                ).update(
                    pos_x=item['pos_x'],
                    pos_y=item['pos_y'],
                    width=item['width'],
                    height=item['height'],
                    orden=item.get('orden', 0),
                )
                count += updated

        logger.info(
            'layout_saved',
            extra={'dashboard_id': str(dashboard_id), 'card_count': count},
        )
        return count


# ──────────────────────────────────────────────
# Trial Service
# ──────────────────────────────────────────────

class TrialService:
    """Servicio para gestion de trials de modulos."""

    @staticmethod
    def get_trial_status(company_id) -> dict:
        """
        Retorna el estado de acceso al modulo dashboard.

        Returns:
            {tiene_acceso, tipo_acceso, dias_restantes, expira_en}
        """
        has_access, access_type = TrialService.check_dashboard_access(company_id)

        result = {
            'tiene_acceso': has_access,
            'tipo_acceso': access_type,
            'dias_restantes': None,
            'expira_en': None,
        }

        if access_type == 'trial':
            try:
                trial = ModuleTrial.objects.get(
                    company_id=company_id,
                    module_code=_MODULE_CODE,
                )
                result['dias_restantes'] = trial.dias_restantes()
                result['expira_en'] = trial.expira_en
            except ModuleTrial.DoesNotExist:
                pass

        return result

    @staticmethod
    def activate_trial(company_id) -> ModuleTrial:
        """
        Activa un trial de 14 dias para el modulo dashboard.
        Raises ValidationError si ya existe un trial (activo o expirado).
        """
        if ModuleTrial.objects.filter(
            company_id=company_id,
            module_code=_MODULE_CODE,
        ).exists():
            raise ValidationError(
                'Ya existe un trial para este modulo. Solo se permite un trial por empresa.'
            )

        now = timezone.now()
        trial = ModuleTrial.objects.create(
            company_id=company_id,
            module_code=_MODULE_CODE,
            expira_en=now + timedelta(days=_TRIAL_DURATION_DAYS),
        )

        logger.info(
            'trial_activated',
            extra={
                'company_id': str(company_id),
                'module_code': _MODULE_CODE,
                'expira_en': trial.expira_en.isoformat(),
            },
        )
        return trial

    @staticmethod
    def check_dashboard_access(company_id) -> tuple[bool, str]:
        """
        Verifica si la empresa tiene acceso al modulo dashboard.

        Checks in order:
        1. License includes 'dashboard' module -> (True, 'license')
        2. Active trial -> (True, 'trial')
        3. No access -> (False, 'none')

        Returns:
            (has_access, access_type)
        """
        # Check license first
        from apps.companies.models import CompanyLicense
        try:
            license_obj = CompanyLicense.objects.get(company_id=company_id)
            if license_obj.is_active_and_valid:
                modules = license_obj.modules_included or []
                if _MODULE_CODE in modules:
                    return True, 'license'
        except CompanyLicense.DoesNotExist:
            pass

        # Check active trial
        try:
            trial = ModuleTrial.objects.get(
                company_id=company_id,
                module_code=_MODULE_CODE,
            )
            if trial.esta_activo():
                return True, 'trial'
        except ModuleTrial.DoesNotExist:
            pass

        return False, 'none'


# ──────────────────────────────────────────────
# Filter Service
# ──────────────────────────────────────────────

class FilterService:
    """Servicio para opciones de filtro disponibles para dashboards."""

    @staticmethod
    def get_available_terceros(company_id, query: str = '') -> list[dict]:
        """
        Retorna terceros disponibles buscando primero en la tabla Tercero
        (módulo terceros) y complementando con terceros únicos de MovimientoContable.
        """
        # 1. Buscar en tabla Tercero (fuente principal)
        qs = Tercero.objects.filter(company_id=company_id)
        if query:
            qs = qs.filter(
                Q(nombre_completo__icontains=query)
                | Q(numero_identificacion__icontains=query)
                | Q(razon_social__icontains=query)
            )
        terceros = [
            {
                'id': str(t.id),
                'nombre': t.nombre_completo or t.razon_social or t.numero_identificacion,
                'identificacion': t.numero_identificacion,
            }
            for t in qs.order_by('nombre_completo')[:50]
        ]

        # 2. Si no hay suficientes, complementar con MovimientoContable
        if len(terceros) < 5:
            mov_qs = MovimientoContable.objects.filter(
                company_id=company_id,
            ).exclude(
                Q(tercero_id__isnull=True) | Q(tercero_id='')
            ).values('tercero_id', 'tercero_nombre').distinct()
            if query:
                mov_qs = mov_qs.filter(
                    Q(tercero_nombre__icontains=query)
                    | Q(tercero_id__icontains=query)
                )
            existing_ids = {t['id'] for t in terceros}
            for row in mov_qs.order_by('tercero_nombre')[:50]:
                if row['tercero_id'] not in existing_ids:
                    terceros.append({
                        'id': row['tercero_id'],
                        'nombre': row['tercero_nombre'] or row['tercero_id'],
                    })

        return terceros[:50]

    @staticmethod
    def get_available_proyectos(company_id) -> list[dict]:
        """Retorna proyectos contables unicos disponibles."""
        return list(
            MovimientoContable.objects.filter(
                company_id=company_id,
            )
            .exclude(proyecto_codigo__isnull=True)
            .exclude(proyecto_codigo='')
            .values('proyecto_codigo', 'proyecto_nombre')
            .distinct()
            .order_by('proyecto_codigo')
        )

    @staticmethod
    def get_available_departamentos(company_id) -> list[dict]:
        """Retorna departamentos unicos disponibles."""
        return list(
            MovimientoContable.objects.filter(
                company_id=company_id,
            )
            .exclude(departamento_codigo__isnull=True)
            .values('departamento_codigo', 'departamento_nombre')
            .distinct()
            .order_by('departamento_codigo')
        )

    @staticmethod
    def get_available_periodos(company_id) -> list[dict]:
        """Retorna periodos contables unicos disponibles."""
        periodos = (
            MovimientoContable.objects.filter(
                company_id=company_id,
            )
            .values_list('periodo', flat=True)
            .distinct()
            .order_by('-periodo')
        )
        return [{'periodo': p} for p in periodos]

    @staticmethod
    def get_available_tipos_doc(company_id, source: str = 'gl') -> list[dict]:
        """Retorna tipos de documento únicos disponibles para la fuente indicada."""
        # Por ahora solo GL (MovimientoContable); se puede extender a otras fuentes
        tipos = (
            MovimientoContable.objects.filter(
                company_id=company_id,
            )
            .exclude(tipo__isnull=True)
            .exclude(tipo='')
            .values_list('tipo', flat=True)
            .distinct()
            .order_by('tipo')
        )
        return [{'tipo': t} for t in tipos]

    @staticmethod
    def get_available_centros_costo(company_id) -> list[dict]:
        """Retorna centros de costo únicos disponibles."""
        centros = (
            MovimientoContable.objects.filter(
                company_id=company_id,
            )
            .exclude(centro_costo_codigo__isnull=True)
            .exclude(centro_costo_codigo=0)
            .values('centro_costo_codigo', 'centro_costo_nombre')
            .distinct()
            .order_by('centro_costo_codigo')
        )
        return list(centros)

    @staticmethod
    def get_available_actividades(company_id) -> list[dict]:
        """Retorna actividades únicas disponibles."""
        actividades = (
            MovimientoContable.objects.filter(
                company_id=company_id,
            )
            .exclude(actividad_codigo__isnull=True)
            .exclude(actividad_codigo='')
            .values_list('actividad_codigo', flat=True)
            .distinct()
            .order_by('actividad_codigo')
        )
        return [{'actividad_codigo': a} for a in actividades]


# ──────────────────────────────────────────────
# Catalog Service
# ──────────────────────────────────────────────

class CatalogService:
    """Servicio para consultar el catalogo de tarjetas."""

    @staticmethod
    def get_available_cards(company_id) -> dict:
        """Retorna tarjetas disponibles para la empresa."""
        config = None
        try:
            config = ConfiguracionContable.objects.get(company_id=company_id)
        except ConfiguracionContable.DoesNotExist:
            pass

        return get_available_cards(config)

    @staticmethod
    def get_categories(company_id) -> list[dict]:
        """Retorna categorias con sus tarjetas disponibles."""
        config = None
        try:
            config = ConfiguracionContable.objects.get(company_id=company_id)
        except ConfiguracionContable.DoesNotExist:
            pass

        return get_categories_with_cards(config)


# ──────────────────────────────────────────────
# Card BI Service — Sprint 4 (filtros 3 capas)
# ──────────────────────────────────────────────

class CardBIService:
    """
    Servicio para tarjetas de tipo 'bi_report' en el dashboard.
    Implementa el sistema de filtros en 3 capas:
      Capa 1 — Filtros base del ReportBI original
      Capa 2 — Overrides por tarjeta (DashboardCard.filtros_config['bi_overrides'])
      Capa 3 — Filtros globales del dashboard (Dashboard.filtros_default)
    """

    GRAPH_VIZ_TYPES = {'bar', 'line', 'pie', 'area', 'waterfall', 'kpi', 'gauge'}

    # Campos de fecha reconocidos para la capa 3 de filtros
    _DATE_FIELDS = frozenset({
        'fecha', 'fecha_documento', 'fecha_creacion', 'fecha_vencimiento',
        'date', 'fecha_emision', 'fecha_ingreso',
    })

    # Campos de tercero reconocidos para la capa 3 de filtros
    _TERCERO_FIELDS = frozenset({
        'tercero_id', 'tercero', 'id_n', 'cliente_id', 'proveedor_id',
    })

    @staticmethod
    def get_selectable_reports(user, company_id) -> QuerySet:
        """
        Lista reportes BI del usuario + compartidos que pueden usarse como tarjeta.
        Solo tipos gráficos (bar, line, pie, area, waterfall, kpi, gauge).
        No se incluyen table ni pivot porque no caben en una tarjeta de dashboard.
        """
        from django.db.models import Q

        own = ReportBI.all_objects.filter(
            user=user,
            company_id=company_id,
            tipo_visualizacion__in=CardBIService.GRAPH_VIZ_TYPES,
        )
        shared_ids = ReportBIShare.objects.filter(
            compartido_con=user,
            reporte__company_id=company_id,
        ).values_list('reporte_id', flat=True)
        shared = ReportBI.all_objects.filter(
            id__in=shared_ids,
            tipo_visualizacion__in=CardBIService.GRAPH_VIZ_TYPES,
        )

        return (own | shared).select_related('user').distinct()

    @staticmethod
    def execute_bi_card(card_id: int, dashboard_filters: dict) -> dict:
        """
        Ejecuta el reporte BI de una tarjeta aplicando los filtros en 3 capas.

        Args:
            card_id: ID de la DashboardCard (debe ser card_type_code='bi_report')
            dashboard_filters: Filtros globales del dashboard (Dashboard.filtros_default)

        Returns:
            Resultado del BIQueryEngine (columns, rows, total_count)
        """
        import copy
        from types import SimpleNamespace

        try:
            card = DashboardCard.objects.select_related(
                'bi_report', 'dashboard',
            ).get(id=card_id)
        except DashboardCard.DoesNotExist:
            raise NotFound('Tarjeta no encontrada.')

        if card.card_type_code != 'bi_report' or not card.bi_report:
            raise ValidationError(
                'Esta tarjeta no es de tipo bi_report o no tiene reporte BI asociado.'
            )

        report = card.bi_report
        company_id = card.dashboard.company_id

        # ── Capa 1: filtros base del reporte (normalizar a lista) ──────────
        base_filtros = copy.deepcopy(report.filtros or [])
        if isinstance(base_filtros, dict):
            base_filtros = []  # retrocompatibilidad: formato v1 era dict

        # ── Capa 2: overrides por tarjeta ─────────────────────────────────
        card_overrides = (card.filtros_config or {}).get('bi_overrides', [])
        merged = CardBIService._apply_overrides(base_filtros, card_overrides)

        # ── Capa 3: filtros globales del dashboard ─────────────────────────
        final = CardBIService._apply_dashboard_global_filters(merged, dashboard_filters or {})

        # ── Ejecutar vía BIQueryEngine con un proxy del reporte ───────────
        # SimpleNamespace permite pasar los campos del reporte sin mutar el objeto BD
        report_proxy = SimpleNamespace(
            fuentes=report.fuentes,
            campos_config=report.campos_config,
            tipo_visualizacion=report.tipo_visualizacion,
            viz_config=report.viz_config,
            filtros=final,
            orden_config=report.orden_config,
            limite_registros=report.limite_registros,
        )

        engine = BIQueryEngine()
        if report.tipo_visualizacion == 'pivot':
            result = engine.execute_pivot(report_proxy, company_id)
        else:
            result = engine.execute(report_proxy, company_id)

        logger.info(
            'bi_card_executed',
            extra={
                'card_id': card_id,
                'report_id': str(report.id),
                'company_id': str(company_id),
                'filter_count': len(final),
            },
        )
        return result

    # ── Helpers de merge de filtros ────────────────────────────────────────

    @staticmethod
    def _apply_overrides(base_filters: list, overrides: list) -> list:
        """
        Aplica overrides de capa 2 sobre los filtros base.
        Para cada override, busca un filtro coincidente por (source, field)
        y reemplaza SOLO el value. Si no hay coincidencia, agrega el override.
        """
        import copy
        merged = copy.deepcopy(base_filters)

        for override in overrides:
            src = override.get('source')
            field = override.get('field')
            value = override.get('value')

            matched = False
            for f in merged:
                if f.get('source') == src and f.get('field') == field:
                    f['value'] = value
                    matched = True
                    break

            if not matched:
                merged.append(copy.deepcopy(override))

        return merged

    @staticmethod
    def _apply_dashboard_global_filters(filters: list, dashboard_filters: dict) -> list:
        """
        Aplica filtros globales del dashboard sobre los filtros BI (capa 3).
        Solo actualiza filtros EXISTENTES — no agrega nuevos filtros.
        Matching por tipo semántico: fecha, periodo, tercero.
        """
        import copy
        merged = copy.deepcopy(filters)

        fecha_desde = dashboard_filters.get('fecha_desde')
        fecha_hasta = dashboard_filters.get('fecha_hasta')

        if fecha_desde and fecha_hasta:
            # Actualizar primer filtro 'between' en un campo de fecha
            for f in merged:
                if (
                    f.get('operator') == 'between'
                    and f.get('field', '').lower() in CardBIService._DATE_FIELDS
                ):
                    f['value'] = [fecha_desde, fecha_hasta]
                    break

        periodo = dashboard_filters.get('periodo')
        if periodo:
            for f in merged:
                if f.get('field', '').lower() == 'periodo':
                    f['value'] = periodo
                    break

        tercero_ids = dashboard_filters.get('tercero_ids')
        if tercero_ids:
            ids = tercero_ids if isinstance(tercero_ids, list) else [tercero_ids]
            for f in merged:
                if (
                    f.get('operator') in ('in', 'eq')
                    and f.get('field', '').lower() in CardBIService._TERCERO_FIELDS
                ):
                    f['value'] = ids
                    break

        return merged


# ──────────────────────────────────────────────
# Report Service (delegates to ReportEngine)
# ──────────────────────────────────────────────

class ReportService:
    """Servicio para generar datos de reportes para tarjetas."""

    @staticmethod
    def get_card_data(
        company_id, card_type_code: str, filtros: dict, card_config: dict | None = None
    ) -> dict:
        """
        Genera los datos para una tarjeta.
        Valida que el card_type_code exista en el catalogo.
        card_config: configuracion especifica para tarjetas personalizadas.
        """
        if card_type_code not in CARD_CATALOG:
            raise ValidationError(f'Tipo de tarjeta no valido: {card_type_code}')

        result = _report_engine.get_card_data(
            company_id, card_type_code, filtros, card_config or {}
        )

        logger.info(
            'card_data_generated',
            extra={
                'company_id': str(company_id),
                'card_type_code': card_type_code,
                'label_count': len(result.get('labels', [])),
            },
        )
        return result

    @staticmethod
    def save_default_filters(dashboard_id, user, filtros: dict) -> Dashboard:
        """
        Guarda los filtros_default del dashboard.
        Requiere ser dueno o tener puede_editar en el share.
        """
        dashboard = DashboardService.get_dashboard(dashboard_id, user)

        if dashboard.user_id != user.id:
            share = DashboardShare.objects.filter(
                dashboard=dashboard, compartido_con=user,
            ).first()
            if not share or not share.puede_editar:
                raise PermissionDenied('No tienes permiso para guardar filtros en este dashboard.')

        dashboard.filtros_default = filtros
        dashboard.save(update_fields=['filtros_default', 'updated_at'])

        logger.info(
            'dashboard_filters_saved',
            extra={
                'dashboard_id': str(dashboard_id),
                'user_id': str(user.id),
            },
        )
        return dashboard


# ──────────────────────────────────────────────
# Report BI Validator — Integridad de configuración
# ──────────────────────────────────────────────

class ReportBIValidator:
    """
    Valida la integridad de la configuración JSON de un ReportBI antes de persistir.
    Llamado desde ReportBIService.create_report() y update_report().
    Todas las validaciones son ligeras (sin BD), basadas en SOURCE_FIELDS y SOURCE_JOINS_MAP.
    """

    @staticmethod
    def get_valid_source_keys() -> set:
        """Retorna el conjunto de claves de fuente válidas según SOURCE_FIELDS."""
        from apps.dashboard.bi_engine import SOURCE_FIELDS
        return set(SOURCE_FIELDS.keys())

    @staticmethod
    def get_valid_fields_for_source(source: str) -> set:
        """
        Retorna el conjunto de field keys disponibles para una fuente.
        Aplana todas las categorías de SOURCE_FIELDS[source].
        Retorna set vacío si la fuente no tiene definición de campos.
        """
        from apps.dashboard.bi_engine import SOURCE_FIELDS
        source_def = SOURCE_FIELDS.get(source, {})
        return {
            field_def['field']
            for fields in source_def.values()
            for field_def in fields
        }

    @staticmethod
    def validate_sources(fuentes: list) -> None:
        """Valida que todas las fuentes existen en SOURCE_FIELDS."""
        valid = ReportBIValidator.get_valid_source_keys()
        invalid = [s for s in fuentes if s not in valid]
        if invalid:
            raise ValidationError(
                f"Fuentes no reconocidas: {', '.join(invalid)}. "
                f"Disponibles: {', '.join(sorted(valid))}."
            )

    @staticmethod
    def validate_campos_config(campos_config: list, fuentes: list) -> None:
        """
        Valida que cada campo en campos_config:
        - tenga 'source' dentro de las fuentes declaradas
        - tenga 'field' válido en esa fuente (si la fuente tiene definición)
        - tenga 'role' válido ('dimension' | 'metric')
        """
        fuentes_set = set(fuentes)
        # 'column' es válido en pivot (dimensión que actúa como cabecera de columna)
        valid_roles = {'dimension', 'metric', 'column'}
        errors = []

        for i, campo in enumerate(campos_config):
            source = campo.get('source')
            field = campo.get('field', '')
            role = campo.get('role')
            is_calculated = campo.get('is_calculated', False) or str(field).startswith('__calc_')

            if not source:
                errors.append(f"campos_config[{i}]: falta 'source'.")
                continue
            if not field:
                errors.append(f"campos_config[{i}]: falta 'field'.")
                continue

            if source not in fuentes_set:
                errors.append(
                    f"campos_config[{i}]: source '{source}' no está en fuentes {sorted(fuentes_set)}."
                )
                continue

            # Los campos calculados no existen en SOURCE_FIELDS — saltar validación de existencia
            if not is_calculated:
                valid_fields = ReportBIValidator.get_valid_fields_for_source(source)
                if valid_fields and field not in valid_fields:
                    errors.append(
                        f"campos_config[{i}]: field '{field}' no existe en fuente '{source}'."
                    )

            if role and role not in valid_roles:
                errors.append(
                    f"campos_config[{i}]: role '{role}' inválido. Use 'dimension', 'metric' o 'column'."
                )

        if errors:
            raise ValidationError(errors)

    @staticmethod
    def validate_joins(fuentes: list) -> None:
        """
        Para reportes multi-fuente (>1 fuente), verifica que existe un JOIN
        definido en SOURCE_JOINS_MAP desde la fuente primaria a cada fuente secundaria.
        Acepta JOIN directo (forward o reverse).
        """
        if len(fuentes) <= 1:
            return

        from apps.dashboard.bi_engine import SOURCE_JOINS_MAP

        primary = fuentes[0]
        secondary = fuentes[1:]
        reachable = set()
        for (a, b) in SOURCE_JOINS_MAP:
            if a == primary:
                reachable.add(b)
            elif b == primary:
                reachable.add(a)

        unreachable = [s for s in secondary if s not in reachable]
        if unreachable:
            raise ValidationError(
                f"No existe JOIN definido desde '{primary}' hacia: {', '.join(unreachable)}. "
                "Revisa SOURCE_JOINS_MAP en bi_engine.py."
            )

    @staticmethod
    def validate_viz_config(
        viz_config: dict,
        tipo_visualizacion: str,
        campos_config: list,
    ) -> None:
        """
        Para tipo 'pivot': verifica que row_fields, col_fields y value_fields
        referencian field keys que existen en campos_config.
        """
        if tipo_visualizacion != 'pivot' or not viz_config:
            return

        available_fields = {c.get('field') for c in campos_config if c.get('field')}
        errors = []

        for key in ('row_fields', 'col_fields'):
            for f in viz_config.get(key, []):
                if available_fields and f not in available_fields:
                    errors.append(f"viz_config.{key}: '{f}' no está en campos_config.")

        for vf in viz_config.get('value_fields', []):
            f = vf.get('field') if isinstance(vf, dict) else vf
            if f and available_fields and f not in available_fields:
                errors.append(f"viz_config.value_fields: '{f}' no está en campos_config.")

        if errors:
            raise ValidationError(errors)

    @staticmethod
    def validate_orden_config(orden_config: list, campos_config: list) -> None:
        """
        Verifica que los campos usados en orden_config existen en campos_config
        y que la dirección es 'asc' o 'desc'.
        """
        if not orden_config:
            return

        available_fields = {c.get('field') for c in campos_config if c.get('field')}
        valid_directions = {'asc', 'desc'}
        errors = []

        for i, order in enumerate(orden_config):
            f = order.get('field')
            d = order.get('direction', 'asc')
            if f and available_fields and f not in available_fields:
                errors.append(f"orden_config[{i}]: '{f}' no está en campos_config.")
            if d not in valid_directions:
                errors.append(
                    f"orden_config[{i}]: direction '{d}' inválido. Use 'asc' o 'desc'."
                )

        if errors:
            raise ValidationError(errors)

    @staticmethod
    def validate_all(
        fuentes: list,
        campos_config: list,
        viz_config: dict,
        tipo_visualizacion: str,
        orden_config: list,
    ) -> None:
        """
        Ejecuta todas las validaciones de integridad en orden.
        Lanza ValidationError con mensajes descriptivos si algo falla.
        Orden: fuentes → campos → joins → viz_config → orden_config.
        """
        ReportBIValidator.validate_sources(fuentes)
        if campos_config:
            ReportBIValidator.validate_campos_config(campos_config, fuentes)
        ReportBIValidator.validate_joins(fuentes)
        if viz_config:
            ReportBIValidator.validate_viz_config(viz_config, tipo_visualizacion, campos_config)
        ReportBIValidator.validate_orden_config(orden_config, campos_config)


# ──────────────────────────────────────────────
# Report BI Service
# ──────────────────────────────────────────────

class ReportBIService:
    """Servicio para operaciones CRUD y ejecución de reportes BI."""

    @staticmethod
    def list_reports(user, company_id) -> QuerySet:
        """Lista reportes del usuario + compartidos."""
        own = ReportBI.all_objects.filter(user=user, company_id=company_id)
        shared_ids = ReportBIShare.objects.filter(
            compartido_con=user,
            reporte__company_id=company_id,
        ).values_list('reporte_id', flat=True)
        return ReportBI.all_objects.filter(
            Q(id__in=own.values_list('id', flat=True))
            | Q(id__in=shared_ids)
        ).select_related('user').distinct()

    @staticmethod
    def list_templates(company_id) -> QuerySet:
        """Lista reportes template disponibles."""
        return ReportBI.all_objects.filter(
            company_id=company_id,
            es_template=True,
        ).select_related('user')

    @staticmethod
    @staticmethod
    def get_template_catalog() -> list:
        """Retorna el catálogo estático de templates predefinidos (sin BD)."""
        from apps.dashboard.bi_templates import REPORT_TEMPLATES
        return [
            {
                'titulo': t['titulo'],
                'descripcion': t['descripcion'],
                'fuentes': t['fuentes'],
                'tipo_visualizacion': t['tipo_visualizacion'],
                'categoria_galeria': t.get('categoria_galeria'),
            }
            for t in REPORT_TEMPLATES
        ]

    @staticmethod
    def create_report(user, company_id, data: dict) -> ReportBI:
        """Crea un nuevo reporte BI."""
        ReportBIService._validate_limite_registros(data)
        ReportBIValidator.validate_all(
            fuentes=data.get('fuentes', []),
            campos_config=data.get('campos_config', []),
            viz_config=data.get('viz_config', {}),
            tipo_visualizacion=data.get('tipo_visualizacion', 'table'),
            orden_config=data.get('orden_config', []),
        )
        es_template = data.get('es_template', False)
        # Solo staff puede crear templates de galería
        if es_template and not (getattr(user, 'is_staff', False) or getattr(user, 'is_superadmin', False)):
            es_template = False

        report = ReportBI(
            user=user,
            company_id=company_id,
            titulo=data['titulo'],
            es_privado=data.get('es_privado', True),
            es_template=es_template,
            fuentes=data['fuentes'],
            campos_config=data.get('campos_config', []),
            tipo_visualizacion=data.get('tipo_visualizacion', 'table'),
            viz_config=data.get('viz_config', {}),
            filtros=data.get('filtros', {}),
            orden_config=data.get('orden_config', []),
            limite_registros=data.get('limite_registros'),
            categoria_galeria=data.get('categoria_galeria'),
        )
        template_id = data.get('template_origen')
        if template_id:
            report.template_origen_id = template_id
        report.save()

        logger.info(
            'report_bi_created',
            extra={
                'report_id': str(report.id),
                'user_id': str(user.id),
                'company_id': str(company_id),
            },
        )
        return report

    @staticmethod
    def get_report(report_id, user) -> ReportBI:
        """Obtiene un reporte por ID. Verifica acceso."""
        try:
            report = ReportBI.all_objects.select_related('user').get(id=report_id)
        except ReportBI.DoesNotExist:
            raise NotFound('Reporte no encontrado.')

        if report.user_id == user.id:
            return report

        if ReportBIShare.objects.filter(reporte=report, compartido_con=user).exists():
            return report

        if getattr(user, 'is_staff', False) or getattr(user, 'is_superadmin', False):
            return report

        # Templates de galería son accesibles (lectura/duplicación) para todos en la empresa
        if report.es_template:
            user_company_id = getattr(user, 'company_id', None)
            if str(report.company_id) == str(user_company_id):
                return report

        raise PermissionDenied('No tienes acceso a este reporte.')

    @staticmethod
    def update_report(report_id, user, data: dict) -> ReportBI:
        """Actualiza un reporte BI. Solo dueño o con permiso de edición."""
        ReportBIService._validate_limite_registros(data)
        report = ReportBIService.get_report(report_id, user)

        if report.user_id != user.id:
            share = ReportBIShare.objects.filter(
                reporte=report, compartido_con=user,
            ).first()
            if not share or not share.puede_editar:
                raise PermissionDenied('No tienes permiso para editar este reporte.')

        # Validar integridad con la config resultante (actual + cambios del request)
        fuentes = data.get('fuentes', report.fuentes)
        campos_config = data.get('campos_config', report.campos_config)
        viz_config = data.get('viz_config', report.viz_config)
        tipo_visualizacion = data.get('tipo_visualizacion', report.tipo_visualizacion)
        orden_config = data.get('orden_config', report.orden_config)
        ReportBIValidator.validate_all(fuentes, campos_config, viz_config, tipo_visualizacion, orden_config)

        updatable = (
            'titulo', 'es_privado', 'es_favorito',
            'fuentes', 'campos_config', 'tipo_visualizacion',
            'viz_config', 'filtros', 'orden_config', 'limite_registros',
            'categoria_galeria',
        )
        for field in updatable:
            if field in data:
                setattr(report, field, data[field])

        # Solo staff puede cambiar es_template
        if 'es_template' in data:
            if getattr(user, 'is_staff', False) or getattr(user, 'is_superadmin', False):
                report.es_template = data['es_template']

        report.save()

        logger.info(
            'report_bi_updated',
            extra={'report_id': str(report_id), 'user_id': str(user.id)},
        )
        return report

    @staticmethod
    def delete_report(report_id, user) -> None:
        """Elimina un reporte BI. Solo el dueño."""
        report = ReportBIService.get_report(report_id, user)
        if report.user_id != user.id:
            raise PermissionDenied('Solo el creador puede eliminar el reporte.')
        report.delete()
        logger.info(
            'report_bi_deleted',
            extra={'report_id': str(report_id), 'user_id': str(user.id)},
        )

    @staticmethod
    @transaction.atomic
    def duplicate_report(report_id, user, titulo: str) -> 'ReportBI':
        """Duplica un reporte BI. Cualquier usuario con acceso puede duplicar."""
        report = ReportBIService.get_report(report_id, user)
        duplicated = ReportBI(
            user=user,
            company_id=report.company_id,
            titulo=titulo,
            fuentes=report.fuentes,
            campos_config=report.campos_config,
            filtros=report.filtros,
            orden_config=report.orden_config,
            tipo_visualizacion=report.tipo_visualizacion,
            viz_config=report.viz_config,
            limite_registros=report.limite_registros,
            es_privado=True,
            es_favorito=False,
            es_template=False,
            template_origen_id=report.id,
        )
        duplicated.save()
        logger.info(
            'report_bi_duplicated',
            extra={'original_id': str(report.id), 'new_id': str(duplicated.id), 'user_id': str(user.id)},
        )
        return duplicated

    @staticmethod
    def toggle_favorite(report_id, user) -> ReportBI:
        """Alterna favorito."""
        report = ReportBIService.get_report(report_id, user)
        report.es_favorito = not report.es_favorito
        report.save(update_fields=['es_favorito', 'updated_at'])
        return report

    @staticmethod
    def execute_report(report, company_id) -> dict:
        """Ejecuta el motor BI para un reporte guardado."""
        if report.tipo_visualizacion == 'pivot':
            return _bi_engine.execute_pivot(report, company_id)
        return _bi_engine.execute(report, company_id)

    @staticmethod
    def execute_preview(data: dict, company_id) -> dict:
        """
        Ejecuta una preview ad-hoc sin guardar.
        Construye un objeto temporal con la config recibida.
        """
        class _AdHocReport:
            pass

        r = _AdHocReport()
        r.fuentes = data.get('fuentes', [])
        r.campos_config = data.get('campos_config', [])
        r.tipo_visualizacion = data.get('tipo_visualizacion', 'table')
        r.viz_config = data.get('viz_config', {})
        r.filtros = data.get('filtros', [])
        r.orden_config = data.get('orden_config', [])
        r.limite_registros = data.get('limite_registros')

        if r.tipo_visualizacion == 'pivot':
            return _bi_engine.execute_pivot(r, company_id)
        return _bi_engine.execute(r, company_id)

    @staticmethod
    def share_report(report_id, user, target_user_id, puede_editar=False) -> ReportBIShare:
        """Comparte un reporte con otro usuario."""
        report = ReportBIService.get_report(report_id, user)

        if report.user_id != user.id:
            raise PermissionDenied('Solo el creador puede compartir el reporte.')

        if str(target_user_id) == str(user.id):
            raise ValidationError('No puedes compartir un reporte contigo mismo.')

        from apps.users.models import User
        try:
            target_user = User.objects.get(id=target_user_id)
        except User.DoesNotExist:
            raise NotFound('Usuario no encontrado.')

        if target_user.company_id != report.company_id:
            raise ValidationError('Solo puedes compartir con usuarios de la misma empresa.')

        share, is_new = ReportBIShare.objects.get_or_create(
            reporte=report,
            compartido_con=target_user,
            defaults={
                'compartido_por': user,
                'puede_editar': puede_editar,
            },
        )
        if not is_new:
            share.puede_editar = puede_editar
            share.save(update_fields=['puede_editar'])

        logger.info(
            'report_bi_shared',
            extra={
                'report_id': str(report_id),
                'target_user_id': str(target_user_id),
            },
        )
        return share

    @staticmethod
    def revoke_share(report_id, share_user_id) -> None:
        """Revoca un share."""
        deleted, _ = ReportBIShare.objects.filter(
            reporte_id=report_id,
            compartido_con_id=share_user_id,
        ).delete()
        if deleted == 0:
            raise NotFound('Share no encontrado.')

    @staticmethod
    def export_pdf(report, company_id) -> bytes:
        """Genera un PDF simple con los datos del reporte."""
        import io
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

        result = ReportBIService.execute_report(report, company_id)
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=landscape(A4))
        elements = []
        styles = getSampleStyleSheet()

        # Title
        elements.append(Paragraph(report.titulo, styles['Title']))
        elements.append(Spacer(1, 12))

        if 'columns' in result and 'rows' in result:
            # Table result
            cols = result['columns']
            header = [c if isinstance(c, str) else c.get('label', c.get('field', '')) for c in cols]
            col_keys = [c if isinstance(c, str) else c.get('field', '') for c in cols]
            table_data = [header]
            for row in result['rows'][:500]:
                table_data.append([
                    str(row.get(k, '')) for k in col_keys
                ])
            t = Table(table_data, repeatRows=1)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565c0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ]))
            elements.append(t)
        elif 'row_headers' in result:
            # Pivot result
            elements.append(Paragraph('Tabla dinámica exportada.', styles['Normal']))

        doc.build(elements)
        return buf.getvalue()

    @staticmethod
    def get_sources():
        """Retorna fuentes disponibles."""
        return _bi_engine.get_available_sources()

    @staticmethod
    def get_fields(source: str):
        """Retorna campos disponibles para una fuente."""
        fields = _bi_engine.get_available_fields(source)
        if not fields:
            raise ValidationError(f'Fuente no válida: {source}')
        return fields

    @staticmethod
    def get_filters(source: str):
        """Retorna filtros aplicables a una fuente."""
        filters = _bi_engine.get_available_filters(source)
        if not filters:
            raise ValidationError(f'Fuente no válida: {source}')
        return filters

    @staticmethod
    def get_joins() -> list:
        """Retorna el mapa de relaciones entre fuentes para el frontend."""
        return _bi_engine.get_joins_map()

    @staticmethod
    def _validate_limite_registros(data: dict) -> None:
        """Valida que si hay límite de registros, exista al menos un ordenamiento."""
        if data.get('limite_registros') and not data.get('orden_config'):
            raise ValidationError(
                'Para usar límite de registros debe definir al menos un ordenamiento.'
            )


# ──────────────────────────────────────────────
# CFO Virtual Service
# ──────────────────────────────────────────────

_TITULO_LABELS = {
    '1': 'Activo', '2': 'Pasivo', '3': 'Patrimonio',
    '4': 'Ingresos', '5': 'Gastos', '6': 'Costos',
    '7': 'Costos de Producción',
}


class CfoVirtualService:
    """
    Servicio CFO Virtual — llama al workflow n8n que consulta OpenAI
    con contexto financiero resumido de la empresa.
    Integra control de cuota IA y registro de uso por usuario.
    """

    @staticmethod
    def ask(question: str, company, user=None) -> str:
        """
        Llama directamente a OpenAI con contexto financiero de la empresa.
        Verifica cuota IA antes de enviar y registra uso despues.
        """
        from apps.companies.services import AIUsageService

        # Verificar cuota IA
        quota = AIUsageService.check_quota(company)
        if not quota['allowed']:
            raise ValidationError(
                'Has alcanzado el limite de uso de IA este mes. '
                f'Mensajes restantes: {quota["remaining_messages"]}, '
                f'Tokens restantes: {quota["remaining_tokens"]}.'
            )

        openai_api_key = getattr(settings, 'OPENAI_API_KEY', '')
        if not openai_api_key:
            raise ValidationError('El asistente de IA no está configurado.')

        context = CfoVirtualService._build_financial_context(company)
        año = context.pop('año_analizado', '')
        periodo = context.pop('periodo', '')
        lines = [f'Resumen financiero año {año} ({periodo}) de {company.name}:']
        for k, v in context.items():
            if k.endswith('_pct'):
                lines.append(f'- {k.replace("_", " ")}: {v:.1f}%')
            elif isinstance(v, (int, float)):
                lines.append(f'- {k.replace("_", " ")}: ${v:,.0f} COP')
            else:
                lines.append(f'- {k.replace("_", " ")}: {v}')
        context_str = '\n'.join(lines)

        system_prompt = (
            f'Eres el CFO Virtual de {company.name}, un asistente financiero experto en '
            'contabilidad colombiana (PUC) y análisis de PyMEs. '
            'Tienes acceso COMPLETO a los datos financieros reales de la empresa proporcionados en el mensaje. '
            'SIEMPRE usa esos datos para responder con números específicos. '
            'Responde en español, de forma concisa y práctica.'
        )

        payload = {
            'model': 'gpt-4o-mini',
            'max_tokens': 1024,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': f'{context_str}\n\nPregunta: {question}'},
            ],
        }

        try:
            resp = requests.post(
                'https://api.openai.com/v1/chat/completions',
                json=payload,
                headers={
                    'Authorization': f'Bearer {openai_api_key}',
                    'Content-Type': 'application/json',
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            response_text = data['choices'][0]['message']['content']

            # Registrar uso de tokens
            usage = data.get('usage', {})
            if user:
                AIUsageService.record_usage(
                    company=company,
                    user=user,
                    request_type='cfo_virtual',
                    module_context='dashboard',
                    prompt_tokens=usage.get('prompt_tokens', 0),
                    completion_tokens=usage.get('completion_tokens', 0),
                    model_used=data.get('model', 'gpt-4o-mini'),
                    question_preview=question[:200],
                )

            return response_text
        except requests.exceptions.Timeout:
            logger.warning('cfo_virtual_timeout', extra={'company_id': str(company.id)})
            raise ValidationError('El asistente tardó demasiado. Intenta de nuevo.')
        except requests.exceptions.RequestException as exc:
            logger.error('cfo_virtual_error', extra={'error': str(exc), 'company_id': str(company.id)})
            raise ValidationError('No se pudo conectar con el asistente financiero.')

    @staticmethod
    def _build_financial_context(company) -> dict:
        """
        Construye un resumen financiero enriquecido para el CFO Virtual.
        Incluye el año en curso (enero-diciembre) y métricas derivadas en español claro.
        """
        today = timezone.now().date()

        # Usar el año con el último movimiento registrado (puede ser año anterior si aún no hay datos del actual)
        last_mov = (
            MovimientoContable.objects
            .filter(company=company)
            .order_by('-fecha')
            .values_list('fecha', flat=True)
            .first()
        )
        year = last_mov.year if last_mov else today.year

        # Año completo: enero 1 — diciembre 31 (o hoy si es el año en curso)
        fecha_inicio = datetime.date(year, 1, 1)
        fecha_fin = min(datetime.date(year, 12, 31), today)

        rows = (
            MovimientoContable.objects
            .filter(company=company, fecha__gte=fecha_inicio, fecha__lte=fecha_fin)
            .values('titulo_codigo')
            .annotate(debito=Sum('debito'), credito=Sum('credito'))
        )

        totals: dict = {}
        for row in rows:
            ttl = str(row['titulo_codigo'] or '')
            key = ttl[:1]
            if key not in totals:
                totals[key] = {'debito': 0.0, 'credito': 0.0}
            totals[key]['debito'] += float(row['debito'] or 0)
            totals[key]['credito'] += float(row['credito'] or 0)

        def get(titulo, side):
            return totals.get(titulo, {}).get(side, 0.0)

        ingresos = get('4', 'credito') - get('4', 'debito')
        costos = get('6', 'debito') - get('6', 'credito')
        gastos = get('5', 'debito') - get('5', 'credito')
        utilidad_bruta = ingresos - costos
        utilidad_operacional = utilidad_bruta - gastos
        activo_total = get('1', 'debito') - get('1', 'credito')
        pasivo_total = get('2', 'credito') - get('2', 'debito')
        patrimonio = get('3', 'credito') - get('3', 'debito')
        margen_bruto = (utilidad_bruta / ingresos * 100) if ingresos else 0
        margen_operacional = (utilidad_operacional / ingresos * 100) if ingresos else 0

        context = {
            'año_analizado': str(year),
            'periodo': f'01/01/{year} al {fecha_fin.strftime("%d/%m/%Y")}',
            'Ingresos_netos_COP': round(ingresos, 2),
            'Costos_de_ventas_COP': round(costos, 2),
            'Utilidad_bruta_COP': round(utilidad_bruta, 2),
            'Gastos_operacionales_COP': round(gastos, 2),
            'Utilidad_operacional_COP': round(utilidad_operacional, 2),
            'Activo_total_COP': round(activo_total, 2),
            'Pasivo_total_COP': round(pasivo_total, 2),
            'Patrimonio_COP': round(patrimonio, 2),
            'Margen_bruto_pct': round(margen_bruto, 1),
            'Margen_operacional_pct': round(margen_operacional, 1),
        }
        return context

    @staticmethod
    def suggest_report(question: str, company, user=None) -> dict:
        """
        Analiza una pregunta del usuario y sugiere un template de reporte BI.
        Usa OpenAI para mapear la intención a los templates predefinidos del catálogo.
        Retorna: {template_titulo, explanation, categoria_galeria, config} o
                 {template_titulo: null, explanation, categoria_galeria: null, config: null}
                 si ningún template aplica.
        """
        import json as json_module
        from apps.companies.services import AIUsageService
        from apps.dashboard.bi_templates import REPORT_TEMPLATES

        quota = AIUsageService.check_quota(company)
        if not quota['allowed']:
            raise ValidationError('Has alcanzado el límite de uso de IA este mes.')

        openai_api_key = getattr(settings, 'OPENAI_API_KEY', '')
        if not openai_api_key:
            raise ValidationError('El asistente de IA no está configurado.')

        template_catalog = json_module.dumps(
            [
                {
                    'titulo': t['titulo'],
                    'descripcion': t['descripcion'],
                    'fuentes': t['fuentes'],
                    'categoria': t.get('categoria_galeria', ''),
                }
                for t in REPORT_TEMPLATES
            ],
            ensure_ascii=False,
        )

        system_prompt = (
            'Eres un asistente BI especializado en análisis financiero y contable para empresas colombianas. '
            'Tu tarea es: (1) elegir el reporte predefinido más adecuado, y (2) personalizar sus filtros, '
            'ordenamiento y límite según lo que el usuario solicita.\n\n'
            'Templates disponibles:\n'
            f'{template_catalog}\n\n'
            'REGLAS:\n'
            '- Elige el template cuyo título/descripción mejor responda la pregunta.\n'
            '- Si el usuario menciona un período (mes, trimestre, año, año completo), extrae el rango de fechas exacto '
            'como filtro. Ejemplo: "diciembre 2025" → {"op":"between","value":["2025-12-01","2025-12-31"]}. '
            '"2025" solo → {"op":"between","value":["2025-01-01","2025-12-31"]}.\n'
            '- CUENTAS CONTABLES (PUC colombiano — jerarquía exacta):\n'
            '  Cuando el usuario menciona "cuenta X", "cuentas X", "grupo X" donde X es un número:\n'
            '  Cuenta única: usa op "eq". Varias cuentas del mismo nivel: usa op "in" con array.\n'
            '  * 1 dígito (ej: 1, 2) → campo "titulo_codigo". '
            'Ej: "clase 1" → {"titulo_codigo":{"op":"eq","value":1}}.\n'
            '  * 2 dígitos (ej: 11, 13, 24) → campo "grupo_codigo". '
            'Ej: "cuentas 11" → {"grupo_codigo":{"op":"eq","value":11}}. '
            '"cuentas 11 y 13" → {"grupo_codigo":{"op":"in","value":[11,13]}}.\n'
            '  * 4 dígitos → campo "cuenta_codigo". '
            'Ej: "cuentas 1105 y 1110" → {"cuenta_codigo":{"op":"in","value":[1105,1110]}}.\n'
            '  * 6 dígitos → campo "subcuenta_codigo".\n'
            '  * 8+ dígitos → campo "auxiliar". '
            'Ej: "auxiliares 13997501 y 14050505" → {"auxiliar":{"op":"in","value":[13997501,14050505]}}.\n'
            '  Si las cuentas tienen distintos niveles de dígitos, usa el campo del nivel más bajo (más dígitos).\n'
            '  Estos filtros solo aplican cuando el template usa la fuente "gl".\n'
            '- Si el usuario pide "top N" o un ranking, ajusta limite_registros y asegura que orden_campo '
            'apunte a la métrica principal en dirección desc.\n'
            '- orden_campo debe ser el nombre exacto de un campo en campos_config del template elegido.\n'
            '- Si ningún template aplica, devuelve template_titulo como null.\n\n'
            'Responde SOLO con JSON válido (sin markdown, sin bloques de código):\n'
            '{"template_titulo": "nombre exacto o null", '
            '"explanation": "1-2 oraciones explicando por qué este reporte responde la pregunta", '
            '"filtros_extra": {"titulo_codigo": {"op": "eq", "value": 11}, "fecha": {"op": "between", "value": ["YYYY-MM-DD","YYYY-MM-DD"]}}, '
            '"orden_campo": "nombre_campo_o_null", '
            '"orden_direccion": "desc", '
            '"limite_registros": null}'
            '\nNota: filtros_extra puede ser {} si no hay filtros específicos. orden_campo puede ser null.'
        )

        payload = {
            'model': 'gpt-4o-mini',
            'max_tokens': 500,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': question},
            ],
        }

        try:
            resp = requests.post(
                'https://api.openai.com/v1/chat/completions',
                json=payload,
                headers={
                    'Authorization': f'Bearer {openai_api_key}',
                    'Content-Type': 'application/json',
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            response_text = data['choices'][0]['message']['content']

            usage = data.get('usage', {})
            if user:
                AIUsageService.record_usage(
                    company=company,
                    user=user,
                    request_type='bi_suggest',
                    module_context='dashboard',
                    prompt_tokens=usage.get('prompt_tokens', 0),
                    completion_tokens=usage.get('completion_tokens', 0),
                    model_used=data.get('model', 'gpt-4o-mini'),
                    question_preview=question[:200],
                )

            parsed = json_module.loads(response_text)
            titulo = parsed.get('template_titulo')
            explanation = parsed.get('explanation', '')

            if not titulo:
                return {
                    'template_titulo': None,
                    'explanation': explanation,
                    'categoria_galeria': None,
                    'config': None,
                }

            template = next(
                (t for t in REPORT_TEMPLATES if t['titulo'] == titulo),
                None,
            )
            if not template:
                return {
                    'template_titulo': None,
                    'explanation': explanation,
                    'categoria_galeria': None,
                    'config': None,
                }

            # Personalizar config con los ajustes del LLM (filtros, orden, límite).
            config = dict(template)
            filtros_extra = parsed.get('filtros_extra') or {}

            existing_filtros = config.get('filtros') or {}
            if isinstance(existing_filtros, list):
                # V2 (array de filtros): convertir filtros_extra dict → entries V2 y agregar.
                config['filtros'] = list(existing_filtros)
                if isinstance(filtros_extra, dict) and filtros_extra:
                    src = config.get('fuentes', [''])[0]
                    for field, cond in filtros_extra.items():
                        if isinstance(cond, dict) and 'op' in cond:
                            config['filtros'].append({
                                'source': src, 'field': field,
                                'op': cond['op'], 'value': cond.get('value'),
                            })
            else:
                # V1 (dict) o vacío: actualizar directamente.
                config['filtros'] = dict(existing_filtros)
                if isinstance(filtros_extra, dict):
                    config['filtros'].update(filtros_extra)

            orden_campo = parsed.get('orden_campo')
            # Validar que el campo exista en campos_config del template.
            # Si el LLM alucina un nombre, usar la primera métrica disponible.
            valid_fields = {c['field'] for c in config.get('campos_config', [])}
            if orden_campo and orden_campo not in valid_fields:
                # Fallback: primera métrica del template
                orden_campo = next(
                    (c['field'] for c in config.get('campos_config', []) if c.get('role') == 'metric'),
                    None,
                )
            if orden_campo:
                orden_dir = parsed.get('orden_direccion', 'desc')
                if orden_dir not in ('asc', 'desc'):
                    orden_dir = 'desc'
                config['orden_config'] = [{'field': orden_campo, 'direction': orden_dir}]

            limite = parsed.get('limite_registros')
            if isinstance(limite, int) and limite > 0:
                config['limite_registros'] = limite

            return {
                'template_titulo': titulo,
                'explanation': explanation,
                'categoria_galeria': template.get('categoria_galeria'),
                'config': config,
            }
        except requests.exceptions.Timeout:
            logger.warning('bi_suggest_timeout', extra={'company_id': str(company.id)})
            raise ValidationError('El asistente tardó demasiado. Intenta de nuevo.')
        except (requests.exceptions.RequestException, json_module.JSONDecodeError) as exc:
            logger.error('bi_suggest_error', extra={'error': str(exc), 'company_id': str(company.id)})
            raise ValidationError('No se pudo obtener la sugerencia del asistente.')
