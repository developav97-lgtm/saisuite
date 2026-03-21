"""
SaiSuite — Companies: Services
Toda la lógica de negocio de empresas aquí.
Las views y serializers no contienen lógica de negocio.
"""
import logging
from datetime import date, timedelta
from rest_framework.exceptions import ValidationError, NotFound

from .models import Company, CompanyModule, CompanyLicense, LicensePayment

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
            .filter(expires_at=target, status=CompanyLicense.Status.ACTIVE)
            .select_related('company')
        )
