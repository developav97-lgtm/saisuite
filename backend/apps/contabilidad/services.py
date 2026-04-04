"""
SaiSuite -- Contabilidad: Services
TODA la logica de negocio va aqui. Las views solo orquestan.
"""
import logging
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.contabilidad.models import (
    MovimientoContable,
    ConfiguracionContable,
    CuentaContable,
)

logger = logging.getLogger(__name__)


class SyncService:
    """Servicio de sincronizacion de datos contables desde Saiopen."""

    # Campos que se actualizan en un upsert de GL (todos excepto company y conteo)
    _GL_UPDATE_FIELDS = [
        'auxiliar', 'auxiliar_nombre',
        'titulo_codigo', 'titulo_nombre',
        'grupo_codigo', 'grupo_nombre',
        'cuenta_codigo', 'cuenta_nombre',
        'subcuenta_codigo', 'subcuenta_nombre',
        'tercero_id', 'tercero_nombre',
        'debito', 'credito',
        'tipo', 'batch', 'invc', 'descripcion',
        'fecha', 'duedate', 'periodo',
        'departamento_codigo', 'departamento_nombre',
        'centro_costo_codigo', 'centro_costo_nombre',
        'proyecto_codigo', 'proyecto_nombre',
        'actividad_codigo', 'actividad_nombre',
    ]

    # Campos que se actualizan en un upsert de ACCT (todos excepto company y codigo)
    _ACCT_UPDATE_FIELDS = [
        'descripcion', 'nivel', 'clase', 'tipo',
        'titulo_codigo', 'grupo_codigo', 'cuenta_codigo',
        'subcuenta_codigo', 'posicion_financiera',
    ]

    @staticmethod
    def process_gl_batch(company_id, records: list[dict]) -> dict:
        """
        Upsert masivo de registros GL usando bulk_create(update_conflicts=True).

        unique_fields = ['company', 'conteo']
        update_fields = todos los campos excepto company y conteo.

        Actualiza el watermark en ConfiguracionContable al finalizar.

        Returns:
            dict con {inserted, updated, errors}
        """
        if not records:
            return {'inserted': 0, 'updated': 0, 'errors': []}

        errors = []
        objects_to_upsert = []
        max_conteo = 0

        for idx, record in enumerate(records):
            try:
                conteo = record['conteo']
                if conteo > max_conteo:
                    max_conteo = conteo

                obj = MovimientoContable(
                    company_id=company_id,
                    conteo=conteo,
                    auxiliar=Decimal(str(record.get('auxiliar', 0))),
                    auxiliar_nombre=record.get('auxiliar_nombre', ''),
                    titulo_codigo=record.get('titulo_codigo'),
                    titulo_nombre=record.get('titulo_nombre', ''),
                    grupo_codigo=record.get('grupo_codigo'),
                    grupo_nombre=record.get('grupo_nombre', ''),
                    cuenta_codigo=record.get('cuenta_codigo'),
                    cuenta_nombre=record.get('cuenta_nombre', ''),
                    subcuenta_codigo=record.get('subcuenta_codigo'),
                    subcuenta_nombre=record.get('subcuenta_nombre', ''),
                    tercero_id=record.get('tercero_id', ''),
                    tercero_nombre=record.get('tercero_nombre', ''),
                    debito=Decimal(str(record.get('debito', 0))),
                    credito=Decimal(str(record.get('credito', 0))),
                    tipo=record.get('tipo', ''),
                    batch=record.get('batch'),
                    invc=record.get('invc', ''),
                    descripcion=record.get('descripcion', ''),
                    fecha=record['fecha'],
                    duedate=record.get('duedate'),
                    periodo=record['periodo'],
                    departamento_codigo=record.get('departamento_codigo'),
                    departamento_nombre=record.get('departamento_nombre', ''),
                    centro_costo_codigo=record.get('centro_costo_codigo'),
                    centro_costo_nombre=record.get('centro_costo_nombre', ''),
                    proyecto_codigo=record.get('proyecto_codigo'),
                    proyecto_nombre=record.get('proyecto_nombre', ''),
                    actividad_codigo=record.get('actividad_codigo'),
                    actividad_nombre=record.get('actividad_nombre', ''),
                )
                objects_to_upsert.append(obj)
            except (KeyError, ValueError, TypeError) as exc:
                errors.append(f'Record {idx}: {exc}')

        if not objects_to_upsert:
            return {'inserted': 0, 'updated': 0, 'errors': errors}

        # Count existing records to determine inserted vs updated
        existing_conteos = set(
            MovimientoContable.objects.filter(
                company_id=company_id,
                conteo__in=[o.conteo for o in objects_to_upsert],
            ).values_list('conteo', flat=True)
        )

        with transaction.atomic():
            MovimientoContable.objects.bulk_create(
                objects_to_upsert,
                update_conflicts=True,
                unique_fields=['company', 'conteo'],
                update_fields=SyncService._GL_UPDATE_FIELDS,
            )

            # Update watermark
            config, _ = ConfiguracionContable.objects.get_or_create(
                company_id=company_id,
            )
            if max_conteo > config.ultimo_conteo_gl:
                config.ultimo_conteo_gl = max_conteo
            config.ultima_sync_gl = timezone.now()
            config.sync_error = ''
            config.save(update_fields=[
                'ultimo_conteo_gl', 'ultima_sync_gl', 'sync_error',
            ])

        inserted = len(objects_to_upsert) - len(existing_conteos)
        updated = len(existing_conteos)

        logger.info(
            'gl_batch_processed',
            extra={
                'company_id': str(company_id),
                'inserted': inserted,
                'updated': updated,
                'error_count': len(errors),
                'max_conteo': max_conteo,
            },
        )

        return {
            'inserted': inserted,
            'updated': updated,
            'errors': errors,
        }

    @staticmethod
    def process_acct_full(company_id, records: list[dict]) -> dict:
        """
        Full sync of chart of accounts. Upsert by (company, codigo).

        Returns:
            dict con {inserted, updated, errors}
        """
        if not records:
            return {'inserted': 0, 'updated': 0, 'errors': []}

        errors = []
        objects_to_upsert = []

        for idx, record in enumerate(records):
            try:
                obj = CuentaContable(
                    company_id=company_id,
                    codigo=Decimal(str(record['codigo'])),
                    descripcion=record.get('descripcion', ''),
                    nivel=record.get('nivel', 0),
                    clase=record.get('clase', ''),
                    tipo=record.get('tipo', ''),
                    titulo_codigo=record.get('titulo_codigo', 0),
                    grupo_codigo=record.get('grupo_codigo', 0),
                    cuenta_codigo=record.get('cuenta_codigo', 0),
                    subcuenta_codigo=record.get('subcuenta_codigo', 0),
                    posicion_financiera=record.get('posicion_financiera', 0),
                )
                objects_to_upsert.append(obj)
            except (KeyError, ValueError, TypeError) as exc:
                errors.append(f'Record {idx}: {exc}')

        if not objects_to_upsert:
            return {'inserted': 0, 'updated': 0, 'errors': errors}

        # Count existing to determine inserted vs updated
        existing_codigos = set(
            CuentaContable.objects.filter(
                company_id=company_id,
                codigo__in=[o.codigo for o in objects_to_upsert],
            ).values_list('codigo', flat=True)
        )

        with transaction.atomic():
            CuentaContable.objects.bulk_create(
                objects_to_upsert,
                update_conflicts=True,
                unique_fields=['company', 'codigo'],
                update_fields=SyncService._ACCT_UPDATE_FIELDS,
            )

            # Update watermark
            config, _ = ConfiguracionContable.objects.get_or_create(
                company_id=company_id,
            )
            config.ultima_sync_acct = timezone.now()
            config.sync_error = ''
            config.save(update_fields=['ultima_sync_acct', 'sync_error'])

        inserted = len(objects_to_upsert) - len(existing_codigos)
        updated = len(existing_codigos)

        logger.info(
            'acct_full_processed',
            extra={
                'company_id': str(company_id),
                'inserted': inserted,
                'updated': updated,
                'error_count': len(errors),
            },
        )

        return {
            'inserted': inserted,
            'updated': updated,
            'errors': errors,
        }

    @staticmethod
    def get_sync_status(company_id) -> dict:
        """
        Returns sync status from ConfiguracionContable plus counts.

        Returns:
            dict with sync config fields + total_movimientos + total_cuentas
        """
        config, _ = ConfiguracionContable.objects.get_or_create(
            company_id=company_id,
        )

        total_movimientos = MovimientoContable.objects.filter(
            company_id=company_id,
        ).count()

        total_cuentas = CuentaContable.objects.filter(
            company_id=company_id,
        ).count()

        return {
            'sync_activo': config.sync_activo,
            'usa_departamentos_cc': config.usa_departamentos_cc,
            'usa_proyectos_actividades': config.usa_proyectos_actividades,
            'ultimo_conteo_gl': config.ultimo_conteo_gl,
            'ultima_sync_gl': config.ultima_sync_gl,
            'ultima_sync_acct': config.ultima_sync_acct,
            'sync_error': config.sync_error,
            'total_movimientos': total_movimientos,
            'total_cuentas': total_cuentas,
        }
