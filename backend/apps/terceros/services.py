"""
SaiSuite — Terceros Services
Toda la lógica de negocio para terceros y direcciones.
"""
import logging
from typing import Any
from django.db.models import Q
from .models import Tercero, TerceroDireccion

logger = logging.getLogger(__name__)


class TerceroService:

    @staticmethod
    def list(company, *, search: str = '', tipo_tercero: str = '', tipo_identificacion: str = '', activo: bool | None = None):
        qs = Tercero.objects.filter(company=company)
        if search:
            qs = qs.filter(
                Q(nombre_completo__icontains=search) |
                Q(numero_identificacion__icontains=search) |
                Q(codigo__icontains=search)
            )
        if tipo_tercero:
            qs = qs.filter(tipo_tercero=tipo_tercero)
        if tipo_identificacion:
            qs = qs.filter(tipo_identificacion=tipo_identificacion)
        if activo is not None:
            qs = qs.filter(activo=activo)
        return qs.order_by('nombre_completo')

    @staticmethod
    def get_by_id(tercero_id: str, company) -> Tercero:
        return Tercero.objects.get(id=tercero_id, company=company)

    @staticmethod
    def create(company, data: dict[str, Any]) -> Tercero:
        # Auto-generar código: usar consecutivo seleccionado por el usuario, fallback a secuencial
        consecutivo_id = data.pop('consecutivo_id', None)
        if not data.get('codigo'):
            from apps.core.services import generar_consecutivo
            codigo = generar_consecutivo(str(consecutivo_id)) if consecutivo_id else None
            if not codigo:
                count = Tercero.all_objects.filter(company=company).count()
                codigo = f'TER-{str(count + 1).zfill(4)}'
            data['codigo'] = codigo
        tercero = Tercero(company=company, **data)
        tercero.save()
        logger.info('tercero_creado', extra={'tercero_id': str(tercero.id), 'codigo': data['codigo']})
        return tercero

    @staticmethod
    def update(tercero: Tercero, data: dict[str, Any]) -> Tercero:
        for field, value in data.items():
            setattr(tercero, field, value)
        tercero.save()
        return tercero

    @staticmethod
    def delete(tercero: Tercero) -> None:
        tercero.activo = False
        tercero.save(update_fields=['activo', 'updated_at'])


class TerceroDireccionService:

    @staticmethod
    def list_by_tercero(tercero_id: str, company) -> list[TerceroDireccion]:
        return list(TerceroDireccion.objects.filter(
            tercero_id=tercero_id,
            company=company,
        ))

    @staticmethod
    def create(tercero: Tercero, data: dict[str, Any]) -> TerceroDireccion:
        if data.get('es_principal'):
            TerceroDireccion.objects.filter(tercero=tercero, es_principal=True).update(es_principal=False)
        direccion = TerceroDireccion(tercero=tercero, company=tercero.company, **data)
        direccion.save()
        return direccion

    @staticmethod
    def update(direccion: TerceroDireccion, data: dict[str, Any]) -> TerceroDireccion:
        if data.get('es_principal'):
            TerceroDireccion.objects.filter(
                tercero=direccion.tercero, es_principal=True,
            ).exclude(id=direccion.id).update(es_principal=False)
        for field, value in data.items():
            setattr(direccion, field, value)
        direccion.save()
        return direccion

    @staticmethod
    def delete(direccion: TerceroDireccion) -> None:
        direccion.delete()


# ── Saiopen Integration (skeleton) ────────────────────────────────────────────

def recibir_tercero_desde_saiopen(company, payload: dict[str, Any]) -> Tercero:
    """
    Crea o actualiza un Tercero a partir de datos enviados por el agente Saiopen.
    Este método es invocado desde el webhook de integración.
    """
    sai_key = payload.get('sai_key') or payload.get('saiopen_id')
    try:
        tercero = Tercero.all_objects.get(company=company, sai_key=sai_key)
    except Tercero.DoesNotExist:
        tercero = None

    data = {
        'tipo_identificacion':   payload.get('tipo_identificacion', 'nit'),
        'numero_identificacion': payload.get('numero_identificacion', ''),
        'razon_social':          payload.get('razon_social', ''),
        'primer_nombre':         payload.get('primer_nombre', ''),
        'segundo_nombre':        payload.get('segundo_nombre', ''),
        'primer_apellido':       payload.get('primer_apellido', ''),
        'segundo_apellido':      payload.get('segundo_apellido', ''),
        'tipo_persona':          payload.get('tipo_persona', 'juridica'),
        'tipo_tercero':          payload.get('tipo_tercero', ''),
        'email':                 payload.get('email', ''),
        'telefono':              payload.get('telefono', ''),
        'celular':               payload.get('celular', ''),
        'saiopen_id':            payload.get('saiopen_id', ''),
        'sai_key':               sai_key,
        'saiopen_synced':        True,
    }

    if tercero:
        TerceroService.update(tercero, data)
        logger.info('tercero_saiopen_actualizado', extra={'sai_key': sai_key})
    else:
        tercero = TerceroService.create(company, data)
        logger.info('tercero_saiopen_creado', extra={'sai_key': sai_key})
    return tercero


def sincronizar_tercero_a_saiopen(tercero: Tercero) -> None:
    """
    Envía un Tercero al agente Saiopen vía SQS.
    TODO: implementar cuando el agente soporte escritura de terceros.
    """
    logger.info(
        'tercero_sync_saiopen_pendiente',
        extra={'tercero_id': str(tercero.id), 'nota': 'SQS no implementado aún'},
    )
