"""
SaiSuite — CRM: Cotización Services
Gestión del ciclo de vida de cotizaciones + PDF + Sync Saiopen.
"""
import logging
from decimal import Decimal
from typing import Any
from django.db import transaction
from django.utils import timezone
from django.template.loader import render_to_string

from .models import (
    CrmCotizacion, CrmLineaCotizacion, CrmOportunidad,
    EstadoCotizacion, CrmTimelineEvent, TipoTimelineEvent,
)
from .services import TimelineService

logger = logging.getLogger(__name__)


class CotizacionService:

    @staticmethod
    def list(oportunidad: CrmOportunidad):
        return CrmCotizacion.all_objects.filter(
            oportunidad=oportunidad
        ).prefetch_related('lineas__producto', 'lineas__impuesto').order_by('-created_at')

    @staticmethod
    def get(cotizacion_id: str, company) -> CrmCotizacion:
        return CrmCotizacion.all_objects.get(id=cotizacion_id, company=company)

    @staticmethod
    @transaction.atomic
    def create(oportunidad: CrmOportunidad, data: dict[str, Any]) -> CrmCotizacion:
        numero = _generar_numero_cotizacion(oportunidad.company)
        cotizacion = CrmCotizacion.objects.create(
            company=oportunidad.company,
            oportunidad=oportunidad,
            numero_interno=numero,
            contacto=data.get('contacto') or oportunidad.contacto,
            titulo=data.get('titulo', f'Cotización {numero}'),
            validez_dias=data.get('validez_dias', 30),
            observaciones=data.get('observaciones', ''),
            condiciones=data.get('condiciones', ''),
        )
        TimelineService.registrar(
            oportunidad, TipoTimelineEvent.COTIZACION_CREADA,
            f'Cotización {numero} creada',
            metadata={'cotizacion_id': str(cotizacion.id)},
        )
        logger.info('crm_cotizacion_creada', extra={'cotizacion_id': str(cotizacion.id)})
        return cotizacion

    @staticmethod
    @transaction.atomic
    def update(cotizacion: CrmCotizacion, data: dict[str, Any]) -> CrmCotizacion:
        if cotizacion.estado not in (EstadoCotizacion.BORRADOR,):
            raise ValueError(f'No se puede editar una cotización en estado "{cotizacion.get_estado_display()}".')
        campos = ['titulo', 'validez_dias', 'fecha_vencimiento', 'observaciones',
                  'condiciones', 'descuento_adicional_p']
        for campo in campos:
            if campo in data:
                setattr(cotizacion, campo, data[campo])
        cotizacion.save()
        CotizacionService._recalcular_totales(cotizacion)
        return cotizacion

    @staticmethod
    def delete(cotizacion: CrmCotizacion):
        if cotizacion.estado not in (EstadoCotizacion.BORRADOR, EstadoCotizacion.RECHAZADA):
            raise ValueError('Solo se pueden eliminar cotizaciones en estado Borrador o Rechazada.')
        cotizacion.delete()

    # ── Líneas ────────────────────────────────

    @staticmethod
    @transaction.atomic
    def add_linea(cotizacion: CrmCotizacion, data: dict[str, Any]) -> CrmLineaCotizacion:
        if cotizacion.estado != EstadoCotizacion.BORRADOR:
            raise ValueError('Solo se pueden agregar líneas a cotizaciones en borrador.')

        max_conteo = CrmLineaCotizacion.all_objects.filter(cotizacion=cotizacion).count()
        conteo = max_conteo + 1

        # Calcular IVA
        impuesto = data.get('impuesto')
        vlr_unitario = Decimal(str(data.get('vlr_unitario', 0)))
        cantidad = Decimal(str(data.get('cantidad', 1)))
        descuento_p = Decimal(str(data.get('descuento_p', 0)))

        base = vlr_unitario * cantidad
        descuento_val = base * (descuento_p / 100)
        base_neta = base - descuento_val
        iva_valor = base_neta * (impuesto.porcentaje if impuesto else Decimal('0'))
        total_parcial = base_neta + iva_valor

        linea = CrmLineaCotizacion.objects.create(
            company=cotizacion.company,
            cotizacion=cotizacion,
            conteo=conteo,
            producto=data.get('producto'),
            descripcion=data.get('descripcion', ''),
            descripcion_adic=data.get('descripcion_adic', ''),
            cantidad=cantidad,
            vlr_unitario=vlr_unitario,
            descuento_p=descuento_p,
            impuesto=impuesto,
            iva_valor=iva_valor,
            total_parcial=total_parcial,
            proyecto=data.get('proyecto', ''),
            actividad=data.get('actividad', ''),
        )
        CotizacionService._recalcular_totales(cotizacion)
        return linea

    @staticmethod
    @transaction.atomic
    def update_linea(linea: CrmLineaCotizacion, data: dict[str, Any]) -> CrmLineaCotizacion:
        campos = ['descripcion', 'descripcion_adic', 'cantidad', 'vlr_unitario', 'descuento_p', 'impuesto']
        for campo in campos:
            if campo in data:
                setattr(linea, campo, data[campo])

        vlr_unitario = linea.vlr_unitario
        cantidad = linea.cantidad
        descuento_p = linea.descuento_p
        impuesto = linea.impuesto

        base = vlr_unitario * cantidad
        descuento_val = base * (descuento_p / 100)
        base_neta = base - descuento_val
        linea.iva_valor = base_neta * (impuesto.porcentaje if impuesto else Decimal('0'))
        linea.total_parcial = base_neta + linea.iva_valor
        linea.save()
        CotizacionService._recalcular_totales(linea.cotizacion)
        return linea

    @staticmethod
    @transaction.atomic
    def delete_linea(linea: CrmLineaCotizacion):
        cotizacion = linea.cotizacion
        linea.delete()
        # Reordenar conteos
        for idx, l in enumerate(CrmLineaCotizacion.all_objects.filter(cotizacion=cotizacion).order_by('conteo'), 1):
            if l.conteo != idx:
                l.conteo = idx
                l.save(update_fields=['conteo'])
        CotizacionService._recalcular_totales(cotizacion)

    @staticmethod
    def _recalcular_totales(cotizacion: CrmCotizacion):
        """Recalcula subtotal, IVA y total desde las líneas."""
        from django.db.models import Sum
        lineas = CrmLineaCotizacion.all_objects.filter(cotizacion=cotizacion)
        agg = lineas.aggregate(
            subtotal=Sum('total_parcial'),
            total_iva=Sum('iva_valor'),
        )
        subtotal = agg['subtotal'] or Decimal('0')
        total_iva = agg['total_iva'] or Decimal('0')

        descuento_p = cotizacion.descuento_adicional_p
        descuento_val = subtotal * (descuento_p / Decimal('100'))
        total = subtotal - descuento_val

        cotizacion.subtotal = subtotal
        cotizacion.descuento_adicional_val = descuento_val
        cotizacion.total_iva = total_iva
        cotizacion.total = total
        cotizacion.save(update_fields=['subtotal', 'descuento_adicional_val', 'total_iva', 'total', 'updated_at'])

    # ── Ciclo de vida ─────────────────────────

    @staticmethod
    @transaction.atomic
    def enviar(cotizacion: CrmCotizacion, email_destino: str = None, usuario=None) -> CrmCotizacion:
        if cotizacion.estado != EstadoCotizacion.BORRADOR:
            raise ValueError('Solo se puede enviar una cotización en estado Borrador.')

        cotizacion.estado = EstadoCotizacion.ENVIADA
        if cotizacion.validez_dias:
            from datetime import timedelta
            cotizacion.fecha_vencimiento = (timezone.now() + timedelta(days=cotizacion.validez_dias)).date()
        cotizacion.save(update_fields=['estado', 'fecha_vencimiento', 'updated_at'])

        # Enviar PDF por email si hay destinatario
        if email_destino or (cotizacion.contacto and cotizacion.contacto.email):
            dest = email_destino or cotizacion.contacto.email
            CotizacionService._enviar_pdf_email(cotizacion, dest)

        TimelineService.registrar(
            cotizacion.oportunidad, TipoTimelineEvent.EMAIL_ENVIADO,
            f'Cotización {cotizacion.numero_interno} enviada',
            usuario=usuario,
            metadata={'cotizacion_id': str(cotizacion.id), 'estado': 'enviada'},
        )
        return cotizacion

    @staticmethod
    @transaction.atomic
    def aceptar(cotizacion: CrmCotizacion, usuario=None) -> CrmCotizacion:
        if cotizacion.estado not in (EstadoCotizacion.ENVIADA, EstadoCotizacion.BORRADOR):
            raise ValueError(f'No se puede aceptar una cotización en estado "{cotizacion.get_estado_display()}".')

        cotizacion.estado = EstadoCotizacion.ACEPTADA
        cotizacion.save(update_fields=['estado', 'updated_at'])

        TimelineService.registrar(
            cotizacion.oportunidad, TipoTimelineEvent.COTIZACION_ACEPT,
            f'Cotización {cotizacion.numero_interno} ACEPTADA por el cliente',
            usuario=usuario,
            metadata={'cotizacion_id': str(cotizacion.id)},
        )

        # Trigger sync a Saiopen (asíncrono via SQS)
        try:
            SyncCotizacionService.push_to_saiopen(cotizacion)
        except Exception as e:
            logger.error('crm_cotizacion_sync_error', extra={
                'cotizacion_id': str(cotizacion.id), 'error': str(e)
            })

        logger.info('crm_cotizacion_aceptada', extra={'cotizacion_id': str(cotizacion.id)})
        return cotizacion

    @staticmethod
    @transaction.atomic
    def rechazar(cotizacion: CrmCotizacion, motivo: str = '', usuario=None) -> CrmCotizacion:
        if cotizacion.estado not in (EstadoCotizacion.ENVIADA, EstadoCotizacion.BORRADOR):
            raise ValueError(f'No se puede rechazar una cotización en estado "{cotizacion.get_estado_display()}".')
        cotizacion.estado = EstadoCotizacion.RECHAZADA
        cotizacion.save(update_fields=['estado', 'updated_at'])
        return cotizacion

    # ── PDF ───────────────────────────────────

    @staticmethod
    def generar_pdf(cotizacion: CrmCotizacion) -> bytes:
        """Genera PDF usando WeasyPrint."""
        import weasyprint

        cotizacion_data = CrmCotizacion.all_objects.prefetch_related(
            'lineas__producto', 'lineas__impuesto'
        ).select_related('oportunidad', 'contacto', 'company').get(id=cotizacion.id)

        html = render_to_string('crm/cotizacion_pdf.html', {
            'cotizacion': cotizacion_data,
            'lineas':     cotizacion_data.lineas.all(),
        })
        pdf_bytes = weasyprint.HTML(string=html).write_pdf()
        return pdf_bytes

    @staticmethod
    def _enviar_pdf_email(cotizacion: CrmCotizacion, email_destino: str):
        """Envía la cotización como adjunto PDF por email."""
        from django.core.mail import EmailMessage
        from django.conf import settings

        pdf = CotizacionService.generar_pdf(cotizacion)
        msg = EmailMessage(
            subject=f'Cotización {cotizacion.numero_interno} — {cotizacion.titulo}',
            body=f'Adjuntamos la cotización {cotizacion.numero_interno}.\n\n{cotizacion.condiciones}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email_destino],
        )
        msg.attach(f'cotizacion_{cotizacion.numero_interno}.pdf', pdf, 'application/pdf')
        msg.send()
        logger.info('crm_cotizacion_pdf_enviada', extra={
            'cotizacion_id': str(cotizacion.id), 'destinatario': email_destino
        })


class SyncCotizacionService:
    """Sincroniza cotizaciones aceptadas → Saiopen COTIZACI via SQS."""

    @staticmethod
    def push_to_saiopen(cotizacion: CrmCotizacion):
        """
        Empuja la cotización aceptada a Saiopen vía mensaje SQS.
        El agente Windows crea el registro COTIZACI + DET_PROD y retorna
        el NUMERO asignado, que se almacena de vuelta en cotizacion.sai_numero.
        """
        import boto3
        import json
        from django.conf import settings

        payload = {
            'type':         'crm_cotizacion_aceptada',
            'company_id':   str(cotizacion.company_id),
            'cotizacion_id': str(cotizacion.id),
            'data': {
                'id_cliente':        cotizacion.contacto.saiopen_id if cotizacion.contacto else '',
                'total':             float(cotizacion.total),
                'subtotal':          float(cotizacion.subtotal),
                'dcto_adc_p':        float(cotizacion.descuento_adicional_p),
                'total_iva':         float(cotizacion.total_iva),
                'observaciones':     cotizacion.observaciones,
                'fecha_vencimiento': cotizacion.fecha_vencimiento.isoformat() if cotizacion.fecha_vencimiento else None,
                'lineas': [
                    {
                        'conteo':       linea.conteo,
                        'cod_desc':     linea.producto.sai_key if linea.producto else '',
                        'descripcion':  linea.descripcion,
                        'cantidad':     float(linea.cantidad),
                        'vlr_unitario': float(linea.vlr_unitario),
                        'desctop':      float(linea.descuento_p),
                        'iva':          float(linea.impuesto.porcentaje) if linea.impuesto else 0,
                        'iva_valor':    float(linea.iva_valor),
                        'total_parc':   float(linea.total_parcial),
                        'proyecto':     linea.proyecto,
                        'actividad':    linea.actividad,
                    }
                    for linea in cotizacion.lineas.select_related('producto', 'impuesto').all()
                ],
            },
        }

        if hasattr(settings, 'SQS_QUEUE_URL') and settings.SQS_QUEUE_URL:
            sqs = boto3.client('sqs', region_name=settings.AWS_DEFAULT_REGION)
            sqs.send_message(
                QueueUrl=settings.SQS_QUEUE_URL,
                MessageBody=json.dumps(payload),
            )
            logger.info('crm_cotizacion_sqs_enviada', extra={'cotizacion_id': str(cotizacion.id)})
        else:
            logger.warning('crm_cotizacion_sqs_skip', extra={
                'motivo': 'SQS_QUEUE_URL no configurado', 'cotizacion_id': str(cotizacion.id)
            })

    @staticmethod
    @transaction.atomic
    def recibir_confirmacion(cotizacion_id: str, sai_numero: int, sai_tipo: str, sai_empresa: int, sai_sucursal: int):
        """
        Recibe la confirmación del agente (callback) y actualiza los campos de sync.
        """
        cotizacion = CrmCotizacion.all_objects.get(id=cotizacion_id)
        cotizacion.sai_numero    = sai_numero
        cotizacion.sai_tipo      = sai_tipo
        cotizacion.sai_empresa   = sai_empresa
        cotizacion.sai_sucursal  = sai_sucursal
        cotizacion.sai_key       = f'{sai_numero}_{sai_tipo}_{sai_empresa}_{sai_sucursal}'
        cotizacion.saiopen_synced = True
        cotizacion.save(update_fields=[
            'sai_numero', 'sai_tipo', 'sai_empresa', 'sai_sucursal',
            'sai_key', 'saiopen_synced', 'updated_at',
        ])
        logger.info('crm_cotizacion_sync_confirmada', extra={
            'cotizacion_id': str(cotizacion.id), 'sai_key': cotizacion.sai_key
        })
        return cotizacion

    @staticmethod
    @transaction.atomic
    def anular_desde_saiopen(sai_key: str, company):
        """
        Cuando Saiopen anula una cotización (ANULAR=0), se llama este método
        para actualizar el estado en CRM.
        """
        try:
            cotizacion = CrmCotizacion.all_objects.get(sai_key=sai_key, company=company)
            cotizacion.estado = 'anulada'
            cotizacion.save(update_fields=['estado', 'updated_at'])
            logger.info('crm_cotizacion_anulada_desde_saiopen', extra={'sai_key': sai_key})
        except CrmCotizacion.DoesNotExist:
            logger.warning('crm_cotizacion_anular_not_found', extra={'sai_key': sai_key})


def _generar_numero_cotizacion(company) -> str:
    """Genera un número consecutivo de cotización por empresa."""
    count = CrmCotizacion.all_objects.filter(company=company).count()
    return f'COT-{str(count + 1).zfill(5)}'
