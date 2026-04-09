"""
SaiSuite — Companies: Services
Toda la lógica de negocio de empresas aquí.
Las views y serializers no contienen lógica de negocio.
"""
import logging
from datetime import date, timedelta
from rest_framework.exceptions import ValidationError, NotFound

from .models import (Company, CompanyModule, CompanyLicense, LicensePayment,
                      LicenseHistory, LicenseRenewal, LicensePackage,
                      LicensePackageItem, MonthlyLicenseSnapshot, AIUsageLog,
                      AgentToken, ModuleTrial, LicenseRequest)

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
            saiopen_enabled=data.get('saiopen_enabled', False),
            saiopen_db_path=data.get('saiopen_db_path', ''),
            is_active=True,
        )
        # Auto-generate first agent token so the Go agent can connect immediately
        AgentToken.objects.create(company=company, label='Principal')

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
        allowed_fields = ['name', 'saiopen_enabled', 'saiopen_db_path']
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
        allowed = ['status', 'renewal_type', 'starts_at', 'expires_at', 'max_users', 'notes']
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
            notes=f'Licencia creada. Vence: {license_obj.expires_at}. Módulos: {license_obj.modules_included}',
        )

        logger.info('license_created_with_history', extra={
            'license_id': str(license_obj.id),
            'company_id': str(company.id),
        })
        return license_obj

    @staticmethod
    def update_license_with_history(license_obj: CompanyLicense, data: dict, changed_by=None) -> CompanyLicense:
        """
        Actualiza una licencia y registra el cambio en LicenseHistory.
        Detecta si es renovación, extensión, modificación o cambio de estado.
        """
        previous_state = {
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
            'status', 'renewal_type', 'starts_at', 'expires_at', 'max_users',
            'concurrent_users', 'modules_included', 'period',
            'ai_tokens_quota', 'notes',
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
                lic.reset_monthly_usage()
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

    @staticmethod
    def auto_generate_renewals() -> int:
        """
        Auto-genera renovaciones para licencias que expiran en 5 dias o menos
        y no tienen renovacion pendiente/confirmada.
        Llamar diariamente via management command.
        """
        expiring = LicenseService.get_expiring_soon(days=5)
        generated = 0
        for lic in expiring:
            existing = RenewalService.get_pending_renewal(lic)
            if existing:
                continue
            RenewalService.create_renewal(lic, period=lic.period, auto_generated=True)
            generated += 1
        logger.info('auto_renewals_generated', extra={'count': generated})
        return generated


class PackageService:
    """Gestion del catalogo de paquetes y asignacion a licencias."""

    @staticmethod
    def list_packages(package_type: str | None = None):
        qs = LicensePackage.objects.filter(is_active=True)
        if package_type:
            qs = qs.filter(package_type=package_type)
        return qs

    @staticmethod
    def get_package(package_id: str) -> LicensePackage:
        try:
            return LicensePackage.objects.get(id=package_id)
        except LicensePackage.DoesNotExist:
            raise NotFound('Paquete no encontrado.')

    @staticmethod
    def create_package(data: dict) -> LicensePackage:
        code = data.get('code', '').strip()
        if LicensePackage.objects.filter(code=code).exists():
            raise ValidationError({'code': 'Ya existe un paquete con este codigo.'})
        package = LicensePackage.objects.create(**data)
        logger.info('package_created', extra={'package_id': str(package.id), 'code': package.code})
        return package

    @staticmethod
    def update_package(package: LicensePackage, data: dict) -> LicensePackage:
        allowed = ['name', 'description', 'quantity', 'price_monthly', 'price_annual', 'is_active']
        for field in allowed:
            if field in data:
                setattr(package, field, data[field])
        package.save()
        logger.info('package_updated', extra={'package_id': str(package.id)})
        return package

    @staticmethod
    def add_package_to_license(license_obj: CompanyLicense, package: LicensePackage, quantity: int = 1, added_by=None) -> LicensePackageItem:
        """
        Agrega un paquete a una licencia y actualiza los campos correspondientes.
        - module: agrega module_code a modules_included
        - user_seats: recalcula concurrent_users y max_users
        - ai_tokens: suma quantity a ai_tokens_quota
        """
        if LicensePackageItem.objects.filter(license=license_obj, package=package).exists():
            raise ValidationError('Este paquete ya esta asignado a la licencia.')

        item = LicensePackageItem.objects.create(
            license=license_obj, package=package, quantity=quantity, added_by=added_by,
        )

        # Actualizar campos de la licencia segun tipo de paquete
        PackageService._apply_package_to_license(license_obj, package, quantity)

        LicenseHistory.objects.create(
            license=license_obj,
            change_type=LicenseHistory.ChangeType.MODIFIED,
            changed_by=added_by,
            notes=f'Paquete agregado: {package.name} x{quantity}',
        )

        logger.info('package_added_to_license', extra={
            'license_id': str(license_obj.id), 'package_code': package.code, 'qty': quantity,
        })
        return item

    @staticmethod
    def remove_package_from_license(item: LicensePackageItem, removed_by=None) -> None:
        """Quita un paquete de una licencia y revierte los campos."""
        license_obj = item.license
        package = item.package
        quantity = item.quantity

        PackageService._revert_package_from_license(license_obj, package, quantity)

        LicenseHistory.objects.create(
            license=license_obj,
            change_type=LicenseHistory.ChangeType.MODIFIED,
            changed_by=removed_by,
            notes=f'Paquete removido: {package.name} x{quantity}',
        )

        item.delete()
        logger.info('package_removed_from_license', extra={
            'license_id': str(license_obj.id), 'package_code': package.code,
        })

    @staticmethod
    def _apply_package_to_license(license_obj: CompanyLicense, package: LicensePackage, quantity: int):
        """Aplica el efecto de un paquete sobre la licencia."""
        if package.package_type == LicensePackage.PackageType.MODULE:
            modules = list(license_obj.modules_included or [])
            if package.module_code and package.module_code not in modules:
                modules.append(package.module_code)
                license_obj.modules_included = modules
                license_obj.save(update_fields=['modules_included'])
                # Activar CompanyModule correspondiente
                CompanyService.activate_module(license_obj.company, package.module_code)

        elif package.package_type == LicensePackage.PackageType.USER_SEATS:
            PackageService._recalculate_user_quotas(license_obj)

        elif package.package_type == LicensePackage.PackageType.AI_TOKENS:
            license_obj.ai_tokens_quota += package.quantity * quantity
            license_obj.save(update_fields=['ai_tokens_quota'])

    @staticmethod
    def _revert_package_from_license(license_obj: CompanyLicense, package: LicensePackage, quantity: int):
        """Revierte el efecto de un paquete sobre la licencia."""
        if package.package_type == LicensePackage.PackageType.MODULE:
            modules = list(license_obj.modules_included or [])
            if package.module_code in modules:
                modules.remove(package.module_code)
                license_obj.modules_included = modules
                license_obj.save(update_fields=['modules_included'])

        elif package.package_type == LicensePackage.PackageType.USER_SEATS:
            PackageService._recalculate_user_quotas(license_obj)

        elif package.package_type == LicensePackage.PackageType.AI_TOKENS:
            license_obj.ai_tokens_quota = max(0, license_obj.ai_tokens_quota - package.quantity * quantity)
            license_obj.save(update_fields=['ai_tokens_quota'])

    @staticmethod
    def _recalculate_user_quotas(license_obj: CompanyLicense) -> None:
        """
        Recalcula concurrent_users y max_users a partir de los paquetes user_seats asignados.
        concurrent_users = suma total de quantity en paquetes user_seats.
        max_users = concurrent_users * 2.
        """
        total_seats = (
            license_obj.package_items
            .filter(package__package_type=LicensePackage.PackageType.USER_SEATS)
            .select_related('package')
            .values_list('package__quantity', 'quantity')
        )
        concurrent = sum(pkg_qty * item_qty for pkg_qty, item_qty in total_seats)
        license_obj.concurrent_users = max(1, concurrent)
        license_obj.max_users = license_obj.concurrent_users * 2
        license_obj.save(update_fields=['concurrent_users', 'max_users'])


class AIUsageService:
    """Tracking y control de uso de IA por empresa/usuario."""

    @staticmethod
    def check_quota(company: Company) -> dict:
        """
        Verifica si la empresa puede hacer una request IA.
        Retorna {allowed, remaining_messages, remaining_tokens}.
        """
        try:
            lic = CompanyLicense.objects.get(company=company)
        except CompanyLicense.DoesNotExist:
            return {'allowed': False, 'remaining_messages': 0, 'remaining_tokens': 0}

        remaining_tokens = max(0, lic.ai_tokens_quota - lic.ai_tokens_used)

        # Permitido solo si tiene cuota de tokens configurada y no agotada
        if lic.ai_tokens_quota <= 0:
            allowed = False  # No tiene paquete de tokens IA
        elif remaining_tokens <= 0:
            allowed = False  # Cuota agotada
        else:
            allowed = True

        return {
            'allowed': allowed,
            'remaining_messages': 0,
            'remaining_tokens': remaining_tokens,
        }

    @staticmethod
    def record_usage(
        company: Company, user, request_type: str, module_context: str,
        prompt_tokens: int = 0, completion_tokens: int = 0,
        model_used: str = 'gpt-4o-mini', question_preview: str = '',
    ) -> AIUsageLog:
        """Registra una request IA y actualiza contadores de la licencia."""
        total_tokens = prompt_tokens + completion_tokens
        log = AIUsageLog.objects.create(
            company=company,
            user=user,
            request_type=request_type,
            module_context=module_context,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            model_used=model_used,
            question_preview=question_preview[:200],
        )

        # Incrementar contadores en la licencia
        try:
            lic = CompanyLicense.objects.get(company=company)
            lic.messages_used += 1
            lic.ai_tokens_used += total_tokens
            lic.save(update_fields=['messages_used', 'ai_tokens_used'])
        except CompanyLicense.DoesNotExist:
            pass

        logger.info('ai_usage_recorded', extra={
            'company_id': str(company.id), 'user_id': str(user.id),
            'type': request_type, 'tokens': total_tokens,
        })
        return log

    @staticmethod
    def get_usage_summary(company: Company) -> dict:
        """Resumen de uso IA del periodo actual."""
        from django.db.models import Sum, Count
        try:
            lic = CompanyLicense.objects.get(company=company)
        except CompanyLicense.DoesNotExist:
            return {}

        agg = AIUsageLog.objects.filter(company=company).aggregate(
            total_requests=Count('id'),
            total_tokens=Sum('total_tokens'),
            total_prompt=Sum('prompt_tokens'),
            total_completion=Sum('completion_tokens'),
        )

        tokens_used  = lic.ai_tokens_used
        tokens_quota = lic.ai_tokens_quota
        tokens_pct   = round(tokens_used / tokens_quota * 100, 1) if tokens_quota > 0 else 0.0

        return {
            'messages_used':        lic.messages_used,
            'tokens_used':          tokens_used,
            'tokens_quota':         tokens_quota,
            'tokens_pct':           tokens_pct,
            'total_requests':       agg['total_requests'] or 0,
            'total_tokens':         agg['total_tokens'] or 0,
        }

    @staticmethod
    def get_per_user_usage(company: Company) -> list[dict]:
        """Uso de IA agrupado por usuario."""
        from django.db.models import Sum, Count
        return list(
            AIUsageLog.objects.filter(company=company)
            .values('user__id', 'user__email', 'user__first_name', 'user__last_name')
            .annotate(
                requests=Count('id'),
                tokens=Sum('total_tokens'),
            )
            .order_by('-tokens')
        )


class SnapshotService:
    """Generacion de snapshots mensuales de licencias."""

    @staticmethod
    def generate_monthly_snapshots() -> int:
        """
        Genera snapshot del mes actual para todas las licencias activas.
        Idempotente: no duplica si ya existe el snapshot del mes.
        """
        today = date.today()
        first_of_month = today.replace(day=1)
        active_statuses = [CompanyLicense.Status.TRIAL, CompanyLicense.Status.ACTIVE]
        licenses = CompanyLicense.objects.filter(
            status__in=active_statuses,
        ).select_related('company')

        created = 0
        for lic in licenses:
            if MonthlyLicenseSnapshot.objects.filter(license=lic, month=first_of_month).exists():
                continue

            snapshot_data = {
                'company_name': lic.company.name,
                'status': lic.status,
                'period': lic.period,
                'starts_at': str(lic.starts_at),
                'expires_at': str(lic.expires_at),
                'max_users': lic.max_users,
                'concurrent_users': lic.concurrent_users,
                'modules_included': lic.modules_included,
                'messages_used': lic.messages_used,
                'ai_tokens_quota': lic.ai_tokens_quota,
                'ai_tokens_used': lic.ai_tokens_used,
                'packages': list(
                    lic.package_items.values('package__code', 'package__name', 'quantity')
                ),
            }

            MonthlyLicenseSnapshot.objects.create(
                license=lic, month=first_of_month, snapshot=snapshot_data,
            )
            created += 1

        logger.info('monthly_snapshots_generated', extra={'count': created, 'month': str(first_of_month)})
        return created


class ModuleTrialService:
    """
    Gestión de trials de 14 días por módulo por empresa.
    Solo lo activa el company_admin. Una sola vez por empresa/módulo.
    """

    TRIAL_DAYS = 14

    VALID_MODULES = ['proyectos', 'dashboard', 'crm', 'soporte']

    @staticmethod
    def get_status(company: Company, module_code: str) -> dict:
        """
        Retorna el estado de acceso de la empresa a un módulo.
        Orden de verificación:
          1. ¿Está en la licencia activa? → tiene_acceso=True, tipo='license'
          2. ¿Tiene trial activo?         → tiene_acceso=True, tipo='trial'
          3. ¿Tuvo trial (expirado)?      → tiene_acceso=False, tipo='trial_expired'
          4. Sin acceso                   → tiene_acceso=False, tipo='none'
        """
        # 1. Licencia activa incluye el módulo
        try:
            lic = CompanyLicense.objects.get(company=company)
            if lic.is_active_and_valid and module_code in (lic.modules_included or []):
                return {
                    'tiene_acceso': True,
                    'tipo_acceso': 'license',
                    'trial_activo': False,
                    'trial_usado': True,
                    'dias_restantes': None,
                    'expira_en': None,
                }
        except CompanyLicense.DoesNotExist:
            pass

        # 2 & 3. Buscar trial (activo o expirado)
        try:
            trial = ModuleTrial.objects.get(company=company, module_code=module_code)
            if trial.esta_activo:
                return {
                    'tiene_acceso': True,
                    'tipo_acceso': 'trial',
                    'trial_activo': True,
                    'trial_usado': True,
                    'dias_restantes': trial.dias_restantes,
                    'expira_en': trial.expira_en,
                }
            # Trial expirado
            return {
                'tiene_acceso': False,
                'tipo_acceso': 'trial_expired',
                'trial_activo': False,
                'trial_usado': True,
                'dias_restantes': 0,
                'expira_en': trial.expira_en,
            }
        except ModuleTrial.DoesNotExist:
            pass

        # 4. Sin acceso, sin trial previo
        return {
            'tiene_acceso': False,
            'tipo_acceso': 'none',
            'trial_activo': False,
            'trial_usado': False,
            'dias_restantes': None,
            'expira_en': None,
        }

    @staticmethod
    def activate_trial(company: Company, module_code: str, activated_by=None) -> ModuleTrial:
        """
        Activa un trial de 14 días para el módulo indicado.
        Raises ValidationError si:
          - El módulo es inválido
          - Ya existe un trial previo (activo o expirado)
          - El módulo ya está en la licencia activa
        """
        from django.utils import timezone as tz
        if module_code not in ModuleTrialService.VALID_MODULES:
            raise ValidationError(
                {'module_code': f'Módulo inválido. Opciones: {ModuleTrialService.VALID_MODULES}'}
            )

        # Verificar si ya está en licencia activa
        try:
            lic = CompanyLicense.objects.get(company=company)
            if lic.is_active_and_valid and module_code in (lic.modules_included or []):
                raise ValidationError('El módulo ya está incluido en la licencia activa.')
        except CompanyLicense.DoesNotExist:
            pass

        # Verificar si ya existe trial previo
        if ModuleTrial.objects.filter(company=company, module_code=module_code).exists():
            raise ValidationError(
                'Ya existe un trial para este módulo. Solo se permite un trial por empresa.'
            )

        now = tz.now()
        trial = ModuleTrial.objects.create(
            company=company,
            module_code=module_code,
            iniciado_en=now,
            expira_en=now + timedelta(days=ModuleTrialService.TRIAL_DAYS),
        )

        logger.info('module_trial_activated', extra={
            'company_id': str(company.id),
            'module_code': module_code,
            'expira_en': trial.expira_en.isoformat(),
            'activated_by': str(activated_by.id) if activated_by else None,
        })
        return trial

    @staticmethod
    def is_module_accessible(company: Company, module_code: str) -> bool:
        """
        Verifica si la empresa puede acceder a un módulo.
        True si: licencia activa incluye el módulo, o trial activo.
        Usado por el bot IA para restringir consultas por módulo.
        """
        status = ModuleTrialService.get_status(company, module_code)
        return status['tiene_acceso']


class LicensePriceCalculatorService:
    """Calcula el precio total de una licencia basado en paquetes seleccionados."""

    @staticmethod
    def calculate(lines: list[dict], period: str = 'monthly') -> dict:
        """
        lines: [{'package_id': UUID, 'quantity': int}, ...]
        period: 'monthly' | 'annual'
        Retorna: {items: [...], total: Decimal}
        """
        from decimal import Decimal
        items = []
        total = Decimal('0.00')

        for line in lines:
            try:
                pkg = LicensePackage.objects.get(id=line['package_id'], is_active=True)
            except LicensePackage.DoesNotExist:
                raise ValidationError({'package_id': f'Paquete {line["package_id"]} no encontrado.'})

            qty = line.get('quantity', 1)
            unit_price = pkg.price_annual if period == 'annual' else pkg.price_monthly
            subtotal = unit_price * qty

            items.append({
                'package_id': str(pkg.id),
                'package_code': pkg.code,
                'package_name': pkg.name,
                'package_type': pkg.package_type,
                'quantity': qty,
                'unit_price': str(unit_price),
                'subtotal': str(subtotal),
            })
            total += subtotal

        return {
            'period': period,
            'items': items,
            'total': str(total),
        }


class LicenseRequestService:
    """
    Gestión de solicitudes de ampliación de licencia iniciadas por company_admin.
    Tipos:
      user_seats → agrega el paquete a la licencia
      module     → agrega el paquete de módulo a la licencia
      ai_tokens  → reemplaza cualquier paquete ai_tokens existente por el nuevo
    """

    ADMIN_EMAIL = 'juan@valmentech.com'

    @staticmethod
    def create_request(company: Company, package_id: str, request_type: str,
                       notes: str, created_by) -> LicenseRequest:
        package = LicensePackage.objects.filter(id=package_id, is_active=True).first()
        if not package:
            raise ValidationError('Paquete no encontrado o inactivo.')

        # Validar tipo coherente
        type_map = {
            LicenseRequest.RequestType.USER_SEATS: LicensePackage.PackageType.USER_SEATS,
            LicenseRequest.RequestType.MODULE:     LicensePackage.PackageType.MODULE,
            LicenseRequest.RequestType.AI_TOKENS:  LicensePackage.PackageType.AI_TOKENS,
        }
        if package.package_type != type_map.get(request_type):
            raise ValidationError('El tipo de solicitud no coincide con el tipo del paquete.')

        # No duplicar solicitudes pendientes del mismo tipo+paquete
        if LicenseRequest.objects.filter(
            company=company, package=package,
            status=LicenseRequest.Status.PENDING,
        ).exists():
            raise ValidationError('Ya existe una solicitud pendiente para este paquete.')

        req = LicenseRequest.objects.create(
            company=company,
            package=package,
            request_type=request_type,
            notes=notes,
            created_by=created_by,
        )

        LicenseRequestService._notify_admin(req)
        return req

    @staticmethod
    def approve(req: LicenseRequest, reviewed_by) -> LicenseRequest:
        from django.utils import timezone as tz
        from django.core.mail import send_mail
        from django.conf import settings

        if req.status != LicenseRequest.Status.PENDING:
            raise ValidationError('Solo se pueden aprobar solicitudes pendientes.')

        license_obj = LicenseService.get_license(req.company)

        # Para ai_tokens: reemplazar el paquete anterior de la misma cuota
        if req.request_type == LicenseRequest.RequestType.AI_TOKENS:
            existing = LicensePackageItem.objects.filter(
                license=license_obj,
                package__package_type=LicensePackage.PackageType.AI_TOKENS,
            ).select_related('package')
            for item in existing:
                PackageService.remove_package_from_license(item, removed_by=reviewed_by)

        PackageService.add_package_to_license(license_obj, req.package, quantity=1, added_by=reviewed_by)

        req.status      = LicenseRequest.Status.APPROVED
        req.reviewed_by = reviewed_by
        req.reviewed_at = tz.now()
        req.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])

        # Notificar al company_admin
        try:
            admin_user = req.created_by or req.company.users.filter(
                role='company_admin', is_active=True
            ).first()
            if admin_user:
                from django.template.loader import render_to_string
                ctx = {
                    'company_name': req.company.name,
                    'package_name': req.package.name,
                    'request_type': req.get_request_type_display(),
                }
                send_mail(
                    subject=f'[SaiCloud] Tu solicitud fue aprobada — {req.package.name}',
                    message=(
                        f'Hola,\n\nTu solicitud de {req.get_request_type_display()} '
                        f'para el paquete "{req.package.name}" ha sido aprobada y ya está activa en tu licencia.\n\n'
                        f'— Equipo SaiCloud'
                    ),
                    html_message=render_to_string('emails/license_request_approved.html', ctx),
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@valmentech.com'),
                    recipient_list=[admin_user.email],
                    fail_silently=True,
                )
        except Exception:
            pass

        logger.info('license_request_approved', extra={
            'request_id': str(req.id), 'company': req.company.name,
            'package': req.package.code, 'reviewed_by': str(reviewed_by.id),
        })
        return req

    @staticmethod
    def reject(req: LicenseRequest, reviewed_by, review_notes: str = '') -> LicenseRequest:
        from django.utils import timezone as tz
        from django.core.mail import send_mail
        from django.conf import settings

        if req.status != LicenseRequest.Status.PENDING:
            raise ValidationError('Solo se pueden rechazar solicitudes pendientes.')

        req.status       = LicenseRequest.Status.REJECTED
        req.reviewed_by  = reviewed_by
        req.reviewed_at  = tz.now()
        req.review_notes = review_notes
        req.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'review_notes'])

        try:
            admin_user = req.created_by or req.company.users.filter(
                role='company_admin', is_active=True
            ).first()
            if admin_user:
                send_mail(
                    subject=f'[SaiCloud] Solicitud no aprobada — {req.package.name}',
                    message=(
                        f'Hola,\n\nTu solicitud de {req.get_request_type_display()} '
                        f'para el paquete "{req.package.name}" no pudo ser aprobada en este momento.\n\n'
                        f'{"Motivo: " + review_notes if review_notes else ""}\n\n'
                        f'Contáctanos a ventas@valmentech.com para más información.\n\n'
                        f'— Equipo SaiCloud'
                    ),
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@valmentech.com'),
                    recipient_list=[admin_user.email],
                    fail_silently=True,
                )
        except Exception:
            pass

        logger.info('license_request_rejected', extra={
            'request_id': str(req.id), 'company': req.company.name,
        })
        return req

    @staticmethod
    def list_for_company(company: Company):
        return (
            LicenseRequest.objects
            .filter(company=company)
            .select_related('package', 'created_by', 'reviewed_by')
            .order_by('-created_at')
        )

    @staticmethod
    def list_all(status_filter: str | None = None):
        qs = LicenseRequest.objects.select_related('company', 'package', 'created_by', 'reviewed_by')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs.order_by('-created_at')

    @staticmethod
    def _notify_admin(req: LicenseRequest) -> None:
        from django.core.mail import send_mail
        from django.conf import settings
        from django.template.loader import render_to_string

        ctx = {
            'company_name':  req.company.name,
            'company_nit':   req.company.nit,
            'package_name':  req.package.name,
            'package_code':  req.package.code,
            'request_type':  req.get_request_type_display(),
            'quantity':      req.package.quantity,
            'price_monthly': req.package.price_monthly,
            'notes':         req.notes,
            'requester':     req.created_by.email if req.created_by else '—',
        }
        try:
            send_mail(
                subject=f'[SaiCloud] Nueva solicitud de licencia — {req.company.name}',
                message=(
                    f'Nueva solicitud de {req.get_request_type_display()} de {req.company.name} '
                    f'(NIT {req.company.nit}).\n\n'
                    f'Paquete solicitado: {req.package.name} ({req.package.code})\n'
                    f'Precio mensual: ${req.package.price_monthly:,.0f} COP\n\n'
                    f'Nota del cliente: {req.notes or "—"}\n\n'
                    f'Ingresa al panel de administración para aprobar o rechazar esta solicitud.'
                ),
                html_message=render_to_string('emails/license_request_admin.html', ctx),
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@valmentech.com'),
                recipient_list=[LicenseRequestService.ADMIN_EMAIL],
                fail_silently=True,
            )
        except Exception:
            pass
