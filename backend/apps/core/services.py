"""
SaiSuite — Core Services
Servicios transversales reutilizables por cualquier módulo.
"""
import logging
from django.db import transaction

logger = logging.getLogger(__name__)


def generar_consecutivo(consecutivo_id: str) -> str | None:
    """
    Genera el siguiente código para el consecutivo dado.

    Usa SELECT FOR UPDATE para garantizar unicidad en concurrencia.
    Retorna None si el consecutivo no existe o está inactivo — el caller usa fallback.

    Args:
        consecutivo_id: UUID del ConfiguracionConsecutivo a usar.

    Returns:
        Código generado (ej: 'PRY-0001') o None si no hay config activa.
    """
    from apps.core.models import ConfiguracionConsecutivo

    with transaction.atomic():
        try:
            config = (
                ConfiguracionConsecutivo.all_objects
                .select_for_update()
                .get(id=consecutivo_id, activo=True)
            )
        except ConfiguracionConsecutivo.DoesNotExist:
            return None

        config.ultimo_numero += 1
        config.save(update_fields=['ultimo_numero', 'updated_at'])

        codigo = config.formato.format(
            prefijo=config.prefijo,
            numero=config.ultimo_numero,
        )

        logger.info(
            'Consecutivo generado',
            extra={
                'consecutivo_id': consecutivo_id,
                'nombre': config.nombre,
                'codigo': codigo,
            },
        )
        return codigo
