"""
SaiSuite — CRM: Producto + Impuesto Sync Service
Sincroniza ITEM y TAXAUTH desde Saiopen hacia CrmProducto y CrmImpuesto.
"""
import logging
from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from .models import CrmImpuesto, CrmProducto

logger = logging.getLogger(__name__)


class ImpuestoSyncService:
    """Sincroniza TAXAUTH de Saiopen → CrmImpuesto."""

    @staticmethod
    @transaction.atomic
    def sync_from_payload(company, taxauth_records: list[dict]) -> dict:
        """
        Recibe lista de registros TAXAUTH y sincroniza CrmImpuesto.
        Formato esperado:
        [{'codigo': 1, 'authority': 'IVA 19%', 'rate': 0.19}, ...]
        """
        creados = 0
        actualizados = 0

        for record in taxauth_records:
            sai_key = str(record['codigo'])
            porcentaje = Decimal(str(record.get('rate', 0)))

            impuesto, created = CrmImpuesto.all_objects.update_or_create(
                company=company,
                sai_key=sai_key,
                defaults={
                    'nombre':         record.get('authority', f'Impuesto {sai_key}'),
                    'porcentaje':     porcentaje,
                    'saiopen_synced': True,
                },
            )
            if created:
                creados += 1
            else:
                actualizados += 1

        logger.info('crm_impuestos_sync', extra={
            'company': str(company.id),
            'creados': creados,
            'actualizados': actualizados,
        })
        return {'creados': creados, 'actualizados': actualizados}


class ProductoSyncService:
    """
    Sincroniza ITEM de Saiopen → CrmProducto (unidireccional Saiopen → CRM).
    Los productos se gestionan en Saiopen, el CRM los usa como catálogo de solo lectura.
    """

    @staticmethod
    @transaction.atomic
    def sync_from_payload(company, item_records: list[dict]) -> dict:
        """
        Recibe lista de registros ITEM y sincroniza CrmProducto.
        Formato esperado de cada registro:
        {
          'item': 'COD001', 'descripcion': 'Producto A', 'price': 50000,
          'uofmsales': 'UND', 'class': 'A', 'grupo': 'G1',
          'impoventa': 'IVA 19%',  # nombre del TAXAUTH.AUTHORITY
          'estado': 'True'
        }
        """
        creados = 0
        actualizados = 0
        errores = []
        ahora = timezone.now()

        for record in item_records:
            sai_key = str(record.get('item', '')).strip()
            if not sai_key:
                continue

            # Resolver impuesto por nombre o sai_key
            impuesto = None
            impoventa = str(record.get('impoventa', '')).strip()
            if impoventa:
                impuesto = CrmImpuesto.all_objects.filter(
                    company=company
                ).filter(
                    models_q(nombre__icontains=impoventa) |
                    models_q(sai_key=impoventa)
                ).first()

            activo = str(record.get('estado', 'True')).lower() in ('true', '1', 's', 'si')

            try:
                producto, created = CrmProducto.all_objects.update_or_create(
                    company=company,
                    sai_key=sai_key,
                    defaults={
                        'codigo':         sai_key,
                        'nombre':         str(record.get('descripcion', sai_key))[:200],
                        'precio_base':    Decimal(str(record.get('price', 0))),
                        'unidad_venta':   str(record.get('uofmsales', ''))[:20],
                        'clase':          str(record.get('class', ''))[:10],
                        'grupo':          str(record.get('grupo', ''))[:10],
                        'impuesto':       impuesto,
                        'saiopen_synced': True,
                        'ultima_sync':    ahora,
                        'is_active':      activo,
                    },
                )
                if created:
                    creados += 1
                else:
                    actualizados += 1
            except Exception as e:
                errores.append({'item': sai_key, 'error': str(e)})
                logger.warning('crm_producto_sync_error', extra={'item': sai_key, 'error': str(e)})

        logger.info('crm_productos_sync', extra={
            'company': str(company.id),
            'creados': creados,
            'actualizados': actualizados,
            'errores': len(errores),
        })
        return {'creados': creados, 'actualizados': actualizados, 'errores': errores}

    @staticmethod
    def list(company, *, search='', grupo='', clase=''):
        from django.db.models import Q
        qs = CrmProducto.objects.filter(company=company, is_active=True).select_related('impuesto')
        if search:
            qs = qs.filter(
                Q(nombre__icontains=search) |
                Q(codigo__icontains=search)
            )
        if grupo:
            qs = qs.filter(grupo=grupo)
        if clase:
            qs = qs.filter(clase=clase)
        return qs.order_by('nombre')


def models_q(**kwargs):
    from django.db.models import Q
    return Q(**kwargs)
