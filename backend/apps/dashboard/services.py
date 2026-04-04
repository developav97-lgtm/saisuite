"""
SaiSuite -- Dashboard: Services
TODA la logica de negocio va aqui. Las views solo orquestan.
"""
import logging
from datetime import timedelta

from django.db import transaction
from django.db.models import Q, QuerySet
from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound

from apps.contabilidad.models import MovimientoContable, ConfiguracionContable
from apps.dashboard.card_catalog import CARD_CATALOG, get_available_cards, get_categories_with_cards
from apps.dashboard.models import (
    Dashboard,
    DashboardCard,
    DashboardShare,
    ModuleTrial,
)
from apps.dashboard.report_engine import ReportEngine

logger = logging.getLogger(__name__)

_TRIAL_DURATION_DAYS = 14
_MODULE_CODE = 'dashboard'

_report_engine = ReportEngine()


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
            descripcion=data.get('descripcion', ''),
            es_privado=data.get('es_privado', True),
            orientacion=data.get('orientacion', 'portrait'),
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

        for field in ('titulo', 'descripcion', 'es_privado', 'orientacion'):
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
        Retorna terceros unicos disponibles en MovimientoContable.
        Soporta busqueda por nombre o ID.
        """
        qs = MovimientoContable.objects.filter(
            company_id=company_id,
        ).values('tercero_id', 'tercero_nombre').distinct()

        if query:
            qs = qs.filter(
                Q(tercero_nombre__icontains=query)
                | Q(tercero_id__icontains=query)
            )

        return list(
            qs.order_by('tercero_nombre')[:50]
        )

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
# Report Service (delegates to ReportEngine)
# ──────────────────────────────────────────────

class ReportService:
    """Servicio para generar datos de reportes para tarjetas."""

    @staticmethod
    def get_card_data(company_id, card_type_code: str, filtros: dict) -> dict:
        """
        Genera los datos para una tarjeta.
        Valida que el card_type_code exista en el catalogo.
        """
        if card_type_code not in CARD_CATALOG:
            raise ValidationError(f'Tipo de tarjeta no valido: {card_type_code}')

        result = _report_engine.get_card_data(company_id, card_type_code, filtros)

        logger.info(
            'card_data_generated',
            extra={
                'company_id': str(company_id),
                'card_type_code': card_type_code,
                'label_count': len(result.get('labels', [])),
            },
        )
        return result
