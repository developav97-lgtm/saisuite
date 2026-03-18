"""
SaiSuite — Companies: Services
Toda la lógica de negocio de empresas aquí.
Las views y serializers no contienen lógica de negocio.
"""
import logging
from rest_framework.exceptions import ValidationError

from .models import Company, CompanyModule

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
            extra={'company_id': str(company.id), 'nit': company.nit, 'name': company.name},
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
            extra={'company_id': str(company.id), 'module': module, 'created': created},
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
            extra={'company_id': str(company.id), 'module': module, 'rows_updated': updated},
        )

    @staticmethod
    def get_active_modules(company: Company) -> list[str]:
        """Retorna lista de nombres de módulos activos para la empresa."""
        return list(
            CompanyModule.objects.filter(company=company, is_active=True)
            .values_list('module', flat=True)
        )
