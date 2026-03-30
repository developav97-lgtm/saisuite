"""
SaiSuite — Companies: Services
Toda la lógica de negocio de empresas aquí.
Las views y serializers no contienen lógica de negocio.
"""
import logging
from datetime import date, timedelta
from rest_framework.exceptions import ValidationError, NotFound

from .models import Company, CompanyModule, CompanyLicense, LicensePayment, LicenseHistory, LicenseRenewal

logger = logging.getLogger(__name__)


class CompanyService:

    @staticmethod
    def list_companies():
        """Retorna todas las empresas ordenadas por nombre."""
        return Company.objects.all().order_by('name')

    @staticmethod
    def get_company(company_id: str) -> Company:
        """Obtiene una empresa por su UUID. Lanza ValidationError si no existe."""
        try:
            return Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            raise ValidationError('Empresa no encontrada.')

    @staticmethod
    def create_company(data: dict) -> Company:
        """
        Crea una nueva empresa.
        Valida que el NIT no esté duplicado antes de crear.
        """
        nit = data.get('nit', '').strip()
        if Company.objects.filter(nit=nit).exists():
            raise ValidationError({'nit': 'Ya existe una empresa con este NIT.'})

        company = Company.objects.create(
            name=data.get('name', '').strip(),
            nit=nit,
            plan=data.get('plan', Company.Plan.STARTER),
            saiopen_enabled=data.get('saiopen_enabled', False),
            saiopen_db_path=data.get('saiopen_db_path', ''),
            is_active=True,
        )
        logger.info(
            'company_created',
            extra={'company_id': str(company.id), 'nit': company.nit, 'company_name': company.name},
        )
        return company

    @staticmethod
    def update_company(company: Company, data: dict) -> Company:
        """
        Actualiza los campos permitidos de una empresa.
        El NIT no se puede modificar.
        """
        allowed_fields = ['name', 'plan', 'saiopen_enabled', 'saiopen_db_path']
        for field in allowed_fields:
            if field in data:
                setattr(company, field, data[field])
        company.save()
        logger.info(
            'company_updated',
            extra={'company_id': str(company.id), 'fields': list(data.keys())},
        )
        return company

    @staticmethod
    def activate_module(company: Company, module: str) -> CompanyModule:
        """
        Activa un módulo para la empresa.
        Si el módulo ya existe pero estaba inactivo, lo reactiva.
        """
        valid_modules = [choice[0] for choice in CompanyModule.Module.choices]
        if module not in valid_modules:
            raise ValidationError({'module': f'Módulo inválido. Opciones: {valid_modules}'})

        obj, created = CompanyModule.objects.get_or_create(
            company=company,
            module=module,
            defaults={'is_active': True},
        )
        if not created and not obj.is_active:
            obj.is_active = True
            obj.save(update_fields=['is_active'])

        logger.info(
            'module_activated',
            extra={'company_id': str(company.id), 'module_name': module, 'is_created': created},
        )
        return obj

    @staticmethod
    def deactivate_module(company: Company, module: str) -> None:
        """
        Desactiva un módulo para la empresa (is_active=False).
        No elimina el registro.
        """
        valid_modules = [choice[0] for choice in CompanyModule.Module.choices]
        if module not in valid_modules:
            raise ValidationError({'module': f'Módulo inválido. Opciones: {valid_modules}'})

        updated = CompanyModule.objects.filter(company=company, module=module).update(is_active=False)
        logger.info(
            'module_deactivated',
            extra={'company_id': str(company.id), 'module_name': module, 'rows_updated': updated},
        )

    @staticmethod
    def get_active_modules(company: Company) -> list[str]:
        """Retorna lista de nombres de módulos activos para la empresa."""
        return list(
            CompanyModule.objects.filter(company=company, is_active=True)
            .values_list('module', flat=True)
        )


class LicenseService:

    @staticmethod
    def get_license(company: Company) -> CompanyLicense:
        try:
            return CompanyLicense.objects.get(company=company)
        except CompanyLicense.DoesNotExist:
            raise NotFound('Esta empresa no tiene una licencia configurada.')

    @staticmethod
    def get_license_by_id(license_id: str) -> CompanyLicense:
        try:
            return CompanyLicense.objects.select_related('company').get(id=license_id)
        except CompanyLicense.DoesNotExist:
            raise NotFound('Licencia no encontrada.')

    @staticmethod
    def list_licenses():
        return CompanyLicense.objects.select_related('company').all().order_by('expires_at')

    @staticmethod
    def create_license(data: dict) -> CompanyLicense:
        company = data['company']
        if CompanyLicense.objects.filter(company=company).exists():
            raise ValidationError({'company': 'Esta empresa ya tiene una licencia. Use la edición.'})
        license_obj = CompanyLicense.objects.create(**data)
        logger.info('license_created', extra={'license_id': str(license_obj.id), 'company_id': str(company.id)})
        return license_obj

    @staticmethod
    def update_license(license_obj: CompanyLicense, data: dict) -> CompanyLicense:
        allowed = ['plan', 'status', 'starts_at', 'expires_at', 'max_users', 'notes']
        for field in allowed:
            if field in data:
                setattr(license_obj, field, data[field])
        license_obj.save()
        logger.info('license_updated', extra={'license_id': str(license_obj.id)})
        return license_obj

    @staticmethod
    def add_payment(license_obj: CompanyLicense, data: dict) -> LicensePayment:
        payment = LicensePayment.objects.create(license=license_obj, **data)
        logger.info('license_payment_added', extra={'license_id': str(license_obj.id), 'amount': str(payment.amount)})
        return payment

    @staticmethod
    def get_expiring_soon(days: int = 5) -> list[CompanyLicense]:
        """Retorna licencias que expiran dentro de `days` días."""
        target = date.today() + timedelta(days=days)
        return list(
            CompanyLicense.objects
            .filter(
                expires_at__lte=target,
                status__in=[CompanyLicense.Status.ACTIVE, CompanyLicense.Status.TRIAL],
            )
            .select_related('company')
        )

    @staticmethod
    def create_license_with_history(data: dict, created_by=None) -> CompanyLicense:
        """
        Crea una licencia y registra el evento en LicenseHistory.
        Si la empresa ya tiene licencia, lanza ValidationError.
        """
        company = data['company']
        if CompanyLicense.objects.filter(company=company).exists():
            raise ValidationError({'company': 'Esta empresa ya tiene una licencia. Use la renovación.'})

        # Calculate expires_at from period if not explicitly provided
        period = data.get('period', CompanyLicense.Period.TRIAL)
        if 'expires_at' not in data or not data.get('expires_at'):
            starts_at = data.get('starts_at', date.today())
            days = CompanyLicense.PERIOD_DAYS.get(period, 14)
            data['expires_at'] = starts_at + timedelta(days=days)
        data['period'] = period

        if created_by:
            data = {**data, 'created_by': created_by}

        license_obj = CompanyLicense.objects.create(**data)

        LicenseHistory.objects.create(
            license=license_obj,
            change_type=LicenseHistory.ChangeType.CREATED,
            changed_by=created_by,
            notes=f'Licencia creada. Plan: {license_obj.plan}, Vence: {license_obj.expires_at}',
        )

        logger.info('license_created_with_history', extra={
            'license_id': str(license_obj.id),
            'company_id': str(company.id),
            'plan': license_obj.plan,
        })
        return license_obj

    @staticmethod
    def update_license_with_history(license_obj: CompanyLicense, data: dict, changed_by=None) -> CompanyLicense:
        """
        Actualiza una licencia y registra el cambio en LicenseHistory.
        Detecta si es renovación, extensión, modificación o cambio de estado.
        """
        previous_state = {
            'plan':       license_obj.plan,
            'status':     license_obj.status,
            'starts_at':  str(license_obj.starts_at),
            'expires_at': str(license_obj.expires_at),
            'concurrent_users': license_obj.concurrent_users,
            'max_users':  license_obj.max_users,
        }

        # Detectar tipo de cambio
        if 'expires_at' in data and data['expires_at'] != license_obj.expires_at:
            if 'starts_at' in data and data['starts_at'] != license_obj.starts_at:
                change_type = LicenseHistory.ChangeType.RENEWED
            else:
                change_type = LicenseHistory.ChangeType.EXTENDED
        elif 'status' in data and data['status'] == CompanyLicense.Status.SUSPENDED:
            change_type = LicenseHistory.ChangeType.SUSPENDED
        elif 'status' in data and data['status'] == CompanyLicense.Status.ACTIVE:
            change_type = LicenseHistory.ChangeType.ACTIVATED
        else:
            change_type = LicenseHistory.ChangeType.MODIFIED

        # Auto-recalculate expires_at from period when period or starts_at is changed
        if 'period' in data or 'starts_at' in data:
            new_period = data.get('period', license_obj.period)
            new_starts = data.get('starts_at', license_obj.starts_at)
            days = CompanyLicense.PERIOD_DAYS.get(new_period, 14)
            data['expires_at'] = new_starts + timedelta(days=days)
            data['period'] = new_period
            data['starts_at'] = new_starts

        allowed = [
            'plan', 'status', 'starts_at', 'expires_at', 'max_users',
            'concurrent_users', 'modules_included', 'period',
            'messages_quota', 'ai_tokens_quota', 'notes',
        ]
        for field in allowed:
            if field in data:
                setattr(license_obj, field, data[field])
        license_obj.save()

        LicenseHistory.objects.create(
            license=license_obj,
            change_type=change_type,
            changed_by=changed_by,
            previous_state=previous_state,
            notes=data.get('notes', ''),
        )

        logger.info('license_updated_with_history', extra={
            'license_id': str(license_obj.id),
            'change_type': change_type,
        })
        return license_obj

    @staticmethod
    def get_license_history(license_obj: CompanyLicense):
        """Retorna el historial de cambios de una licencia."""
        return LicenseHistory.objects.filter(license=license_obj).select_related('changed_by')

    @staticmethod
    def reset_monthly_usage_all() -> int:
        """
        Resetea contadores de mensajes y tokens para todas las licencias activas.
        Llamar el primer día de cada mes (management command o EventBridge).
        Retorna el número de licencias reseteadas.
        """
        today = date.today()
        active_statuses = [CompanyLicense.Status.TRIAL, CompanyLicense.Status.ACTIVE]
        licenses = CompanyLicense.objects.filter(status__in=active_statuses)
        count = 0
        for lic in licenses:
            lic.reset_monthly_usage()
            count += 1
        logger.info('monthly_usage_reset', extra={'licenses_reset': count, 'date': str(today)})
        return count

    @staticmethod
    def count_active_sessions(company: Company) -> int:
        """Cuenta sesiones activas de usuarios de la empresa (excluyendo timeouts)."""
        from apps.users.models import UserSession
        from django.utils import timezone
        timeout_threshold = timezone.now() - timedelta(minutes=UserSession.SESSION_TIMEOUT_MINUTES)
        return UserSession.objects.filter(
            user__company=company,
            last_activity__gte=timeout_threshold,
        ).exclude(user__is_staff=True).count()

    @staticmethod
    def verify_concurrent_limit(company: Company, exclude_user=None) -> tuple[bool, int, int]:
        """
        Verifica si la empresa puede admitir un nuevo usuario concurrente.
        Retorna (puede_acceder: bool, activos: int, permitidos: int).
        """
        try:
            lic = CompanyLicense.objects.get(company=company)
        except CompanyLicense.DoesNotExist:
            return False, 0, 0

        from apps.users.models import UserSession
        from django.utils import timezone
        timeout_threshold = timezone.now() - timedelta(minutes=UserSession.SESSION_TIMEOUT_MINUTES)
        qs = UserSession.objects.filter(
            user__company=company,
            last_activity__gte=timeout_threshold,
        ).exclude(user__is_staff=True)  # Soporte no cuenta como concurrente
        if exclude_user:
            qs = qs.exclude(user=exclude_user)

        activos = qs.count()
        permitidos = lic.concurrent_users
        return activos < permitidos, activos, permitidos


class SessionService:
    """
    Gestión de sesiones activas de usuario.
    Controla sesión única por usuario y concurrencia por empresa.
    """

    @staticmethod
    def create_session(user, ip_address: str | None = None, user_agent: str = '') -> 'UserSession':
        """
        Crea una nueva sesión para el usuario.
        Elimina la sesión anterior del mismo usuario (sesión única).
        """
        from apps.users.models import UserSession
        # Sesión única: eliminar sesiones anteriores del mismo usuario
        deleted, _ = UserSession.objects.filter(user=user).delete()
        if deleted:
            logger.info('session_replaced', extra={'user_id': str(user.id), 'sessions_deleted': deleted})

        session = UserSession.objects.create(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent or '',
        )
        logger.info('session_created', extra={'user_id': str(user.id), 'session_id': str(session.session_id)})
        return session

    @staticmethod
    def validate_session(session_id: str) -> 'UserSession | None':
        """
        Valida que una sesión exista y esté activa (dentro del timeout).
        Retorna la sesión o None si es inválida/expirada.
        """
        from apps.users.models import UserSession
        try:
            session = UserSession.objects.select_related('user').get(session_id=session_id)
        except UserSession.DoesNotExist:
            return None

        if not session.is_active():
            session.delete()
            logger.info('session_expired_deleted', extra={'session_id': session_id})
            return None

        return session

    @staticmethod
    def invalidate_session(session_id: str) -> bool:
        """Invalida (elimina) una sesión específica. Retorna True si existía."""
        from apps.users.models import UserSession
        deleted, _ = UserSession.objects.filter(session_id=session_id).delete()
        if deleted:
            logger.info('session_invalidated', extra={'session_id': session_id})
        return bool(deleted)

    @staticmethod
    def invalidate_user_sessions(user) -> int:
        """Elimina todas las sesiones de un usuario. Retorna número de sesiones eliminadas."""
        from apps.users.models import UserSession
        deleted, _ = UserSession.objects.filter(user=user).delete()
        logger.info('user_sessions_invalidated', extra={'user_id': str(user.id), 'count': deleted})
        return deleted


class RenewalService:
    """Gestión del ciclo de vida de renovaciones de licencia."""

    @staticmethod
    def get_pending_renewal(license_obj: CompanyLicense):
        """Retorna la renovación activa (pending/confirmed) más reciente, o None."""
        return LicenseRenewal.objects.filter(
            license=license_obj,
            status__in=[LicenseRenewal.Status.PENDING, LicenseRenewal.Status.CONFIRMED],
        ).order_by('-created_at').first()

    @staticmethod
    def create_renewal(license_obj: CompanyLicense, period: str, auto_generated: bool = False) -> LicenseRenewal:
        """
        Crea una renovación pendiente.
        Cancela cualquier renovación pending/confirmed previa.
        new_starts_at = expires_at + 1 día
        new_expires_at = new_starts_at + PERIOD_DAYS[period]
        """
        from rest_framework.exceptions import ValidationError as DRFValidationError
        if period not in CompanyLicense.PERIOD_DAYS:
            raise DRFValidationError({'period': f'Período inválido. Opciones: {list(CompanyLicense.PERIOD_DAYS.keys())}'})

        # Cancelar renovaciones previas activas
        LicenseRenewal.objects.filter(
            license=license_obj,
            status__in=[LicenseRenewal.Status.PENDING, LicenseRenewal.Status.CONFIRMED],
        ).update(status=LicenseRenewal.Status.CANCELLED)

        new_starts  = license_obj.expires_at + timedelta(days=1)
        new_expires = new_starts + timedelta(days=CompanyLicense.PERIOD_DAYS[period])

        renewal = LicenseRenewal.objects.create(
            license=license_obj,
            period=period,
            new_starts_at=new_starts,
            new_expires_at=new_expires,
            auto_generated=auto_generated,
        )

        LicenseHistory.objects.create(
            license=license_obj,
            change_type=LicenseHistory.ChangeType.RENEWAL_GENERATED,
            notes=(
                f'Renovación {"auto-generada" if auto_generated else "creada manualmente"}. '
                f'Período: {period}. Inicio: {new_starts}. Vence: {new_expires}.'
            ),
        )

        logger.info('renewal_created', extra={
            'license_id': str(license_obj.id),
            'renewal_id': str(renewal.id),
            'period': period,
            'auto_generated': auto_generated,
        })
        return renewal

    @staticmethod
    def confirm_renewal(renewal: LicenseRenewal, confirmed_by=None, notes: str = '') -> LicenseRenewal:
        """
        Confirma el pago de una renovación.
        pending → confirmed
        Punto de integración para pasarela de pago futura.
        """
        from rest_framework.exceptions import ValidationError as DRFValidationError
        if renewal.status != LicenseRenewal.Status.PENDING:
            raise DRFValidationError('Solo se pueden confirmar renovaciones en estado pendiente.')

        from django.utils import timezone as tz
        renewal.status       = LicenseRenewal.Status.CONFIRMED
        renewal.confirmed_by = confirmed_by
        renewal.confirmed_at = tz.now()
        if notes:
            renewal.notes = notes
        renewal.save()

        LicenseHistory.objects.create(
            license=renewal.license,
            change_type=LicenseHistory.ChangeType.RENEWAL_CONFIRMED,
            changed_by=confirmed_by,
            notes=f'Pago confirmado. Método: {renewal.payment_method}.',
        )

        logger.info('renewal_confirmed', extra={
            'renewal_id': str(renewal.id),
            'confirmed_by': str(confirmed_by.id) if confirmed_by else None,
        })
        return renewal

    @staticmethod
    def activate_due_renewals() -> int:
        """
        Activa renovaciones confirmadas cuya licencia ha vencido.
        Llamar diariamente por management command.
        Retorna el número de renovaciones activadas.
        """
        from django.utils import timezone as tz
        today = date.today()
        confirmed = LicenseRenewal.objects.filter(
            status=LicenseRenewal.Status.CONFIRMED,
        ).select_related('license')

        activated = 0
        for renewal in confirmed:
            lic = renewal.license
            if lic.expires_at < today:
                lic.starts_at  = renewal.new_starts_at
                lic.expires_at = renewal.new_expires_at
                lic.period     = renewal.period
                lic.status     = CompanyLicense.Status.ACTIVE
                lic.save()

                renewal.status       = LicenseRenewal.Status.ACTIVATED
                renewal.activated_at = tz.now()
                renewal.save()

                LicenseHistory.objects.create(
                    license=lic,
                    change_type=LicenseHistory.ChangeType.RENEWAL_ACTIVATED,
                    notes=(
                        f'Renovación activada. '
                        f'Período: {renewal.new_starts_at} → {renewal.new_expires_at}.'
                    ),
                )
                activated += 1

        logger.info('renewals_activated', extra={'count': activated})
        return activated

    @staticmethod
    def cancel_renewal(renewal: LicenseRenewal, cancelled_by=None) -> LicenseRenewal:
        """Cancela una renovación pending o confirmed."""
        from rest_framework.exceptions import ValidationError as DRFValidationError
        if renewal.status == LicenseRenewal.Status.ACTIVATED:
            raise DRFValidationError('No se puede cancelar una renovación ya activada.')

        renewal.status = LicenseRenewal.Status.CANCELLED
        renewal.save()

        LicenseHistory.objects.create(
            license=renewal.license,
            change_type=LicenseHistory.ChangeType.RENEWAL_CANCELLED,
            changed_by=cancelled_by,
            notes='Renovación cancelada.',
        )

        logger.info('renewal_cancelled', extra={'renewal_id': str(renewal.id)})
        return renewal
