"""
SaiSuite — CRM Services
Toda la lógica de negocio: Pipeline, Etapas, Leads, Oportunidades, Actividades, Timeline.
"""
from __future__ import annotations
import logging
from decimal import Decimal
from typing import Any
from django.db import transaction
from django.db.models import Q, Sum, Count
from django.utils import timezone

from .models import (
    CrmPipeline, CrmEtapa, CrmLead, CrmLeadScoringRule, CrmOportunidad,
    CrmActividad, CrmTimelineEvent, TipoTimelineEvent, FuenteLead,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# PIPELINE SERVICE
# ─────────────────────────────────────────────

class PipelineService:

    @staticmethod
    def list(company):
        return CrmPipeline.objects.filter(company=company).prefetch_related('etapas')

    @staticmethod
    def get(pipeline_id: str, company) -> CrmPipeline:
        return CrmPipeline.objects.get(id=pipeline_id, company=company)

    @staticmethod
    @transaction.atomic
    def create(company, data: dict[str, Any]) -> CrmPipeline:
        # Solo puede haber un pipeline default por empresa
        if data.get('es_default'):
            CrmPipeline.all_objects.filter(company=company, es_default=True).update(es_default=False)

        pipeline = CrmPipeline.objects.create(company=company, **data)
        logger.info('crm_pipeline_creado', extra={'pipeline_id': str(pipeline.id)})
        return pipeline

    @staticmethod
    @transaction.atomic
    def update(pipeline: CrmPipeline, data: dict[str, Any]) -> CrmPipeline:
        if data.get('es_default'):
            CrmPipeline.all_objects.filter(company=pipeline.company, es_default=True).exclude(id=pipeline.id).update(es_default=False)
        for key, value in data.items():
            setattr(pipeline, key, value)
        pipeline.save()
        return pipeline

    @staticmethod
    def delete(pipeline: CrmPipeline):
        if CrmOportunidad.all_objects.filter(pipeline=pipeline).exists():
            raise ValueError('No se puede eliminar un pipeline con oportunidades activas.')
        pipeline.delete()
        logger.info('crm_pipeline_eliminado', extra={'pipeline_id': str(pipeline.id)})

    @staticmethod
    def get_kanban(pipeline: CrmPipeline, *, asignado_a=None, search='', page=1, page_size=50):
        """
        Retorna oportunidades agrupadas por etapa para el Kanban.
        Soporta filtros y paginación por etapa (virtual scroll compatible).
        """
        etapas = CrmEtapa.all_objects.filter(pipeline=pipeline).order_by('orden')
        result = []
        for etapa in etapas:
            qs = CrmOportunidad.all_objects.filter(
                pipeline=pipeline, etapa=etapa, company=pipeline.company,
            ).select_related('contacto', 'asignado_a')

            if asignado_a:
                qs = qs.filter(asignado_a_id=asignado_a)
            if search:
                qs = qs.filter(
                    Q(titulo__icontains=search) |
                    Q(contacto__nombre_completo__icontains=search)
                )

            total_valor = qs.aggregate(t=Sum('valor_esperado'))['t'] or Decimal('0')
            total_count = qs.count()
            offset = (page - 1) * page_size
            oportunidades = list(qs.order_by('-created_at')[offset:offset + page_size])

            result.append({
                'etapa': etapa,
                'oportunidades': oportunidades,
                'total_valor': total_valor,
                'total_count': total_count,
            })
        return result


# ─────────────────────────────────────────────
# ETAPA SERVICE
# ─────────────────────────────────────────────

class EtapaService:

    @staticmethod
    def list(pipeline: CrmPipeline):
        return CrmEtapa.all_objects.filter(pipeline=pipeline).order_by('orden')

    @staticmethod
    def get(etapa_id: str, company) -> CrmEtapa:
        return CrmEtapa.all_objects.get(id=etapa_id, pipeline__company=company)

    @staticmethod
    @transaction.atomic
    def create(pipeline: CrmPipeline, data: dict[str, Any]) -> CrmEtapa:
        # Auto-asignar orden si no se especifica
        if 'orden' not in data or data['orden'] is None:
            max_orden = CrmEtapa.all_objects.filter(pipeline=pipeline).aggregate(
                m=models_max('orden')
            )['m'] or 0
            data['orden'] = max_orden + 1

        etapa = CrmEtapa.objects.create(
            pipeline=pipeline,
            company=pipeline.company,
            **data,
        )
        logger.info('crm_etapa_creada', extra={'etapa_id': str(etapa.id), 'pipeline_id': str(pipeline.id)})
        return etapa

    @staticmethod
    @transaction.atomic
    def update(etapa: CrmEtapa, data: dict[str, Any]) -> CrmEtapa:
        for key, value in data.items():
            setattr(etapa, key, value)
        etapa.save()
        return etapa

    @staticmethod
    def delete(etapa: CrmEtapa):
        if CrmOportunidad.all_objects.filter(etapa=etapa).exists():
            raise ValueError('No se puede eliminar una etapa con oportunidades activas.')
        etapa.delete()

    @staticmethod
    @transaction.atomic
    def reordenar(pipeline: CrmPipeline, orden: list[str]):
        """Recibe lista de IDs de etapas en el nuevo orden."""
        for idx, etapa_id in enumerate(orden):
            CrmEtapa.all_objects.filter(id=etapa_id, pipeline=pipeline).update(orden=idx)
        logger.info('crm_etapas_reordenadas', extra={'pipeline_id': str(pipeline.id)})


def models_max(field):
    from django.db.models import Max
    return Max(field)


# ─────────────────────────────────────────────
# LEAD SCORING SERVICE
# ─────────────────────────────────────────────

class LeadScoringService:

    @staticmethod
    def calcular_score(lead: CrmLead) -> int:
        """Aplica todas las reglas activas y retorna la puntuación total (0-100)."""
        reglas = CrmLeadScoringRule.all_objects.filter(company=lead.company).order_by('orden')
        score = 0
        for regla in reglas:
            valor_campo = getattr(lead, regla.campo, None)
            if valor_campo is None:
                continue
            valor_campo_str = str(valor_campo).lower()

            if regla.operador == 'eq' and valor_campo_str == regla.valor.lower():
                score += regla.puntos
            elif regla.operador == 'contains' and regla.valor.lower() in valor_campo_str:
                score += regla.puntos
            elif regla.operador == 'not_empty' and valor_campo_str:
                score += regla.puntos
            elif regla.operador == 'is_empty' and not valor_campo_str:
                score += regla.puntos
            elif regla.operador == 'gte':
                try:
                    if float(valor_campo) >= float(regla.valor):
                        score += regla.puntos
                except (ValueError, TypeError):
                    pass
            elif regla.operador == 'lte':
                try:
                    if float(valor_campo) <= float(regla.valor):
                        score += regla.puntos
                except (ValueError, TypeError):
                    pass

        return max(0, min(100, score))

    @staticmethod
    def recalcular_lead(lead: CrmLead) -> CrmLead:
        lead.score = LeadScoringService.calcular_score(lead)
        lead.save(update_fields=['score', 'updated_at'])
        return lead


# ─────────────────────────────────────────────
# LEAD SERVICE
# ─────────────────────────────────────────────

class LeadService:

    @staticmethod
    def list(company, *, search='', fuente='', convertido=None, asignado_a=None, pipeline_id=None):
        qs = CrmLead.objects.filter(company=company).select_related('pipeline', 'asignado_a', 'tercero')
        if search:
            qs = qs.filter(
                Q(nombre__icontains=search) |
                Q(empresa__icontains=search) |
                Q(email__icontains=search)
            )
        if fuente:
            qs = qs.filter(fuente=fuente)
        if convertido is not None:
            qs = qs.filter(convertido=convertido)
        if asignado_a:
            qs = qs.filter(asignado_a_id=asignado_a)
        if pipeline_id:
            qs = qs.filter(pipeline_id=pipeline_id)
        return qs.order_by('-created_at')

    @staticmethod
    def get(lead_id: str, company) -> CrmLead:
        return CrmLead.objects.get(id=lead_id, company=company)

    @staticmethod
    @transaction.atomic
    def create(company, data: dict[str, Any]) -> CrmLead:
        lead = CrmLead(company=company, **data)
        lead.score = LeadScoringService.calcular_score(lead)
        lead.save()
        logger.info('crm_lead_creado', extra={'lead_id': str(lead.id), 'fuente': lead.fuente})
        return lead

    @staticmethod
    def create_from_webhook(company, payload: dict) -> CrmLead:
        """Crea un lead desde un webhook externo (formulario web)."""
        data = {
            'nombre':   payload.get('nombre', ''),
            'empresa':  payload.get('empresa', ''),
            'email':    payload.get('email', ''),
            'telefono': payload.get('telefono', ''),
            'cargo':    payload.get('cargo', ''),
            'fuente':   FuenteLead.WEBHOOK,
            'notas':    payload.get('mensaje', ''),
        }
        # Asignar al pipeline default si existe
        pipeline = CrmPipeline.all_objects.filter(company=company, es_default=True).first()
        if pipeline:
            data['pipeline'] = pipeline

        lead = LeadService.create(company, data)
        # Round-robin asignación
        lead = LeadService._asignar_round_robin(lead)
        return lead

    @staticmethod
    def _asignar_round_robin(lead: CrmLead) -> CrmLead:
        """Asigna el lead al vendedor con menos leads activos (uso interno)."""
        return LeadService.asignar_round_robin(lead)

    @staticmethod
    def asignar_round_robin(lead: CrmLead) -> CrmLead:
        """Asigna el lead al vendedor con menos leads activos."""
        from apps.users.models import User
        vendedores = User.objects.filter(
            company=lead.company,
            role='seller',
            is_active=True,
        ).annotate(leads_count=Count('crm_leads')).order_by('leads_count')

        if vendedores.exists():
            lead.asignado_a = vendedores.first()
            lead.save(update_fields=['asignado_a', 'updated_at'])
        return lead

    @staticmethod
    def asignar_masivo_round_robin(company) -> int:
        """Asigna vía round-robin todos los leads sin asignado. Retorna cantidad asignada."""
        leads_sin_asignar = CrmLead.objects.filter(company=company, asignado_a__isnull=True)
        count = 0
        for lead in leads_sin_asignar:
            result = LeadService.asignar_round_robin(lead)
            if result.asignado_a_id:
                count += 1
        return count

    @staticmethod
    @transaction.atomic
    def importar_csv(company, registros: list[dict], pipeline_id=None) -> dict:
        """
        Importa leads masivamente desde CSV/Excel.
        Retorna resumen: creados, errores.
        """
        pipeline = None
        if pipeline_id:
            pipeline = CrmPipeline.all_objects.filter(id=pipeline_id, company=company).first()
        if not pipeline:
            pipeline = CrmPipeline.all_objects.filter(company=company, es_default=True).first()

        creados = 0
        errores = []
        for i, fila in enumerate(registros):
            try:
                data = {
                    'nombre':   fila.get('nombre', '').strip(),
                    'empresa':  fila.get('empresa', '').strip(),
                    'email':    fila.get('email', '').strip(),
                    'telefono': fila.get('telefono', '').strip(),
                    'cargo':    fila.get('cargo', '').strip(),
                    'fuente':   FuenteLead.CSV,
                    'pipeline': pipeline,
                }
                if not data['nombre']:
                    errores.append({'fila': i + 2, 'error': 'Nombre requerido'})
                    continue
                LeadService.create(company, data)
                creados += 1
            except Exception as e:
                errores.append({'fila': i + 2, 'error': str(e)})

        logger.info('crm_leads_importados', extra={'company': str(company.id), 'creados': creados, 'errores': len(errores)})
        return {'creados': creados, 'errores': errores}

    @staticmethod
    @transaction.atomic
    def convertir(lead: CrmLead, data: dict) -> CrmOportunidad:
        """
        Convierte un lead en oportunidad.
        data: {etapa_id, valor_esperado, fecha_cierre_estimada, tercero_id (opcional)}
        """
        if lead.convertido:
            raise ValueError('Este lead ya fue convertido.')

        etapa = CrmEtapa.all_objects.get(id=data['etapa_id'], pipeline__company=lead.company)

        # Vincular o crear Tercero
        tercero = None
        if data.get('tercero_id'):
            from apps.terceros.models import Tercero
            tercero = Tercero.objects.get(id=data['tercero_id'], company=lead.company)
        elif data.get('crear_tercero') and lead.nombre:
            tercero = _crear_tercero_desde_lead(lead)

        # Resolver asignado_a — override desde data o heredar del lead
        asignado_a = lead.asignado_a
        if data.get('asignado_a_id'):
            from apps.users.models import User
            asignado_a = User.objects.filter(id=data['asignado_a_id'], company=lead.company).first() or lead.asignado_a

        oportunidad = OportunidadService.create(lead.company, {
            'titulo':                lead.empresa or lead.nombre,
            'contacto':              tercero,
            'pipeline':              etapa.pipeline,
            'etapa':                 etapa,
            'valor_esperado':        data.get('valor_esperado', Decimal('0')),
            'probabilidad':          etapa.probabilidad,
            'fecha_cierre_estimada': data.get('fecha_cierre_estimada'),
            'asignado_a':            asignado_a,
            'descripcion':           lead.notas,
        })

        lead.convertido    = True
        lead.convertido_en = timezone.now()
        lead.oportunidad   = oportunidad
        lead.tercero       = tercero
        lead.save(update_fields=['convertido', 'convertido_en', 'oportunidad', 'tercero', 'updated_at'])

        TimelineService.registrar(oportunidad, TipoTimelineEvent.LEAD_CONVERTIDO,
            f'Oportunidad creada desde lead: {lead.nombre}', metadata={'lead_id': str(lead.id)})

        logger.info('crm_lead_convertido', extra={'lead_id': str(lead.id), 'oportunidad_id': str(oportunidad.id)})
        return oportunidad

    @staticmethod
    @transaction.atomic
    def asignar(lead: CrmLead, user_id: str) -> CrmLead:
        from apps.users.models import User
        user = User.objects.get(id=user_id, company=lead.company)
        lead.asignado_a = user
        lead.save(update_fields=['asignado_a', 'updated_at'])
        return lead

    @staticmethod
    def update(lead: CrmLead, data: dict) -> CrmLead:
        for key, value in data.items():
            setattr(lead, key, value)
        lead.score = LeadScoringService.calcular_score(lead)
        lead.save()
        return lead

    @staticmethod
    def delete(lead: CrmLead):
        if lead.convertido:
            raise ValueError('No se puede eliminar un lead convertido.')
        lead.delete()


def _crear_tercero_desde_lead(lead: CrmLead):
    """Crea un Tercero básico a partir de los datos del lead."""
    from apps.terceros.models import Tercero, TipoIdentificacion, TipoPersona, TipoTercero
    from apps.core.services import generar_consecutivo

    count = Tercero.all_objects.filter(company=lead.company).count()
    tercero = Tercero(
        company=lead.company,
        codigo=f'TER-{str(count + 1).zfill(4)}',
        tipo_identificacion=TipoIdentificacion.OTRO,
        numero_identificacion='',
        tipo_persona=TipoPersona.NATURAL if not lead.empresa else TipoPersona.JURIDICA,
        tipo_tercero=TipoTercero.CLIENTE,
        razon_social=lead.empresa,
        primer_nombre=lead.nombre if not lead.empresa else '',
        email=lead.email,
        telefono=lead.telefono,
    )
    tercero.save()
    return tercero


# ─────────────────────────────────────────────
# OPORTUNIDAD SERVICE
# ─────────────────────────────────────────────

class OportunidadService:

    @staticmethod
    def list(company, *, search='', pipeline_id=None, etapa_id=None, asignado_a=None, ganada=None, perdida=None):
        qs = CrmOportunidad.objects.filter(company=company).select_related(
            'contacto', 'pipeline', 'etapa', 'asignado_a'
        )
        if search:
            qs = qs.filter(
                Q(titulo__icontains=search) |
                Q(contacto__nombre_completo__icontains=search)
            )
        if pipeline_id:
            qs = qs.filter(pipeline_id=pipeline_id)
        if etapa_id:
            qs = qs.filter(etapa_id=etapa_id)
        if asignado_a:
            qs = qs.filter(asignado_a_id=asignado_a)
        if ganada is not None:
            qs = qs.filter(etapa__es_ganado=ganada)
        if perdida is not None:
            qs = qs.filter(etapa__es_perdido=perdida)
        return qs.order_by('-created_at')

    @staticmethod
    def get(oportunidad_id: str, company) -> CrmOportunidad:
        return CrmOportunidad.objects.get(id=oportunidad_id, company=company)

    @staticmethod
    @transaction.atomic
    def create(company, data: dict[str, Any]) -> CrmOportunidad:
        oportunidad = CrmOportunidad(company=company, **data)
        oportunidad.save()
        logger.info('crm_oportunidad_creada', extra={'oportunidad_id': str(oportunidad.id)})
        return oportunidad

    @staticmethod
    @transaction.atomic
    def update(oportunidad: CrmOportunidad, data: dict[str, Any]) -> CrmOportunidad:
        for key, value in data.items():
            setattr(oportunidad, key, value)
        oportunidad.save()
        return oportunidad

    @staticmethod
    @transaction.atomic
    def mover_etapa(oportunidad: CrmOportunidad, etapa_id: str, usuario=None) -> CrmOportunidad:
        etapa_anterior = oportunidad.etapa
        nueva_etapa = CrmEtapa.all_objects.get(id=etapa_id, pipeline=oportunidad.pipeline)

        if etapa_anterior.id == nueva_etapa.id:
            return oportunidad

        oportunidad.etapa = nueva_etapa
        oportunidad.probabilidad = nueva_etapa.probabilidad
        oportunidad.save(update_fields=['etapa', 'probabilidad', 'updated_at'])

        TimelineService.registrar(
            oportunidad, TipoTimelineEvent.CAMBIO_ETAPA,
            f'Etapa cambiada: {etapa_anterior.nombre} → {nueva_etapa.nombre}',
            usuario=usuario,
            metadata={'etapa_anterior': etapa_anterior.nombre, 'etapa_nueva': nueva_etapa.nombre},
        )
        logger.info('crm_oportunidad_etapa_cambiada', extra={
            'oportunidad_id': str(oportunidad.id),
            'etapa_anterior': str(etapa_anterior.id),
            'etapa_nueva': str(nueva_etapa.id),
        })
        return oportunidad

    @staticmethod
    @transaction.atomic
    def ganar(oportunidad: CrmOportunidad, usuario=None) -> CrmOportunidad:
        etapa_ganado = CrmEtapa.all_objects.filter(
            pipeline=oportunidad.pipeline, es_ganado=True
        ).first()
        if not etapa_ganado:
            raise ValueError('El pipeline no tiene una etapa configurada como "Ganado".')

        oportunidad.etapa      = etapa_ganado
        oportunidad.ganada_en  = timezone.now()
        oportunidad.perdida_en = None
        oportunidad.motivo_perdida = ''
        oportunidad.save(update_fields=['etapa', 'ganada_en', 'perdida_en', 'motivo_perdida', 'updated_at'])

        TimelineService.registrar(
            oportunidad, TipoTimelineEvent.CAMBIO_ETAPA,
            '🏆 Oportunidad marcada como GANADA', usuario=usuario,
        )
        return oportunidad

    @staticmethod
    @transaction.atomic
    def perder(oportunidad: CrmOportunidad, motivo: str, usuario=None) -> CrmOportunidad:
        etapa_perdido = CrmEtapa.all_objects.filter(
            pipeline=oportunidad.pipeline, es_perdido=True
        ).first()
        if not etapa_perdido:
            raise ValueError('El pipeline no tiene una etapa configurada como "Perdido".')
        if not motivo:
            raise ValueError('Debe indicar el motivo de pérdida.')

        oportunidad.etapa          = etapa_perdido
        oportunidad.perdida_en     = timezone.now()
        oportunidad.motivo_perdida = motivo
        oportunidad.save(update_fields=['etapa', 'perdida_en', 'motivo_perdida', 'updated_at'])

        TimelineService.registrar(
            oportunidad, TipoTimelineEvent.CAMBIO_ETAPA,
            f'Oportunidad marcada como PERDIDA. Motivo: {motivo}', usuario=usuario,
        )
        return oportunidad

    @staticmethod
    def delete(oportunidad: CrmOportunidad):
        oportunidad.delete()
        logger.info('crm_oportunidad_eliminada', extra={'oportunidad_id': str(oportunidad.id)})

    @staticmethod
    def enviar_email(oportunidad: CrmOportunidad, asunto: str, cuerpo: str, usuario=None) -> bool:
        """Envía un email en nombre del vendedor y registra en timeline."""
        from django.core.mail import send_mail
        from django.conf import settings

        if not oportunidad.contacto or not oportunidad.contacto.email:
            raise ValueError('El contacto no tiene email registrado.')

        send_mail(
            subject=asunto,
            message=cuerpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[oportunidad.contacto.email],
            fail_silently=False,
        )

        TimelineService.registrar(
            oportunidad, TipoTimelineEvent.EMAIL_ENVIADO,
            f'Email enviado a {oportunidad.contacto.email}: {asunto}',
            usuario=usuario,
            metadata={'asunto': asunto, 'destinatario': oportunidad.contacto.email},
        )
        return True


# ─────────────────────────────────────────────
# ACTIVIDAD SERVICE
# ─────────────────────────────────────────────

class ActividadService:

    @staticmethod
    def list(oportunidad: CrmOportunidad, *, solo_pendientes=False):
        qs = CrmActividad.all_objects.filter(oportunidad=oportunidad).select_related('asignado_a')
        if solo_pendientes:
            qs = qs.filter(completada=False)
        return qs.order_by('fecha_programada')

    @staticmethod
    def list_for_lead(lead: 'CrmLead', *, solo_pendientes=False):
        qs = CrmActividad.all_objects.filter(lead=lead).select_related('asignado_a')
        if solo_pendientes:
            qs = qs.filter(completada=False)
        return qs.order_by('fecha_programada')

    @staticmethod
    def get(actividad_id: str, company) -> CrmActividad:
        from django.db.models import Q
        return CrmActividad.all_objects.get(
            Q(id=actividad_id),
            Q(oportunidad__company=company) | Q(lead__company=company),
        )

    @staticmethod
    @transaction.atomic
    def create(oportunidad: CrmOportunidad, data: dict[str, Any]) -> CrmActividad:
        actividad = CrmActividad.objects.create(
            company=oportunidad.company,
            oportunidad=oportunidad,
            **data,
        )
        ActividadService._actualizar_proxima_actividad(oportunidad)
        logger.info('crm_actividad_creada', extra={'actividad_id': str(actividad.id)})
        return actividad

    @staticmethod
    @transaction.atomic
    def create_for_lead(lead: 'CrmLead', data: dict[str, Any]) -> CrmActividad:
        actividad = CrmActividad.objects.create(
            company=lead.company,
            lead=lead,
            **data,
        )
        logger.info('crm_actividad_lead_creada', extra={'actividad_id': str(actividad.id)})
        return actividad

    @staticmethod
    @transaction.atomic
    def completar(actividad: CrmActividad, resultado: str = '', usuario=None) -> CrmActividad:
        actividad.completada    = True
        actividad.completada_en = timezone.now()
        actividad.resultado     = resultado
        actividad.save(update_fields=['completada', 'completada_en', 'resultado', 'updated_at'])

        if actividad.oportunidad_id:
            TimelineService.registrar(
                actividad.oportunidad, TipoTimelineEvent.ACTIVIDAD_COMP,
                f'{actividad.get_tipo_display()} completada: {actividad.titulo}',
                usuario=usuario,
                metadata={'actividad_id': str(actividad.id), 'resultado': resultado},
            )
            ActividadService._actualizar_proxima_actividad(actividad.oportunidad)
        return actividad

    @staticmethod
    def update(actividad: CrmActividad, data: dict) -> CrmActividad:
        for key, value in data.items():
            setattr(actividad, key, value)
        actividad.save()
        if actividad.oportunidad_id:
            ActividadService._actualizar_proxima_actividad(actividad.oportunidad)
        return actividad

    @staticmethod
    def delete(actividad: CrmActividad):
        oportunidad = actividad.oportunidad if actividad.oportunidad_id else None
        actividad.delete()
        if oportunidad:
            ActividadService._actualizar_proxima_actividad(oportunidad)

    @staticmethod
    def _actualizar_proxima_actividad(oportunidad: CrmOportunidad):
        """Actualiza los campos denormalizados de próxima actividad."""
        proxima = CrmActividad.all_objects.filter(
            oportunidad=oportunidad, completada=False,
        ).order_by('fecha_programada').first()

        oportunidad.proxima_actividad_fecha = proxima.fecha_programada if proxima else None
        oportunidad.proxima_actividad_tipo  = proxima.tipo if proxima else ''
        oportunidad.save(update_fields=['proxima_actividad_fecha', 'proxima_actividad_tipo', 'updated_at'])


# ─────────────────────────────────────────────
# TIMELINE SERVICE
# ─────────────────────────────────────────────

class TimelineService:

    @staticmethod
    def list(oportunidad: CrmOportunidad):
        return CrmTimelineEvent.all_objects.filter(
            oportunidad=oportunidad
        ).select_related('usuario').order_by('-created_at')

    @staticmethod
    def registrar(
        oportunidad: CrmOportunidad,
        tipo: str,
        descripcion: str,
        usuario=None,
        metadata: dict | None = None,
    ) -> CrmTimelineEvent:
        evento = CrmTimelineEvent.objects.create(
            company=oportunidad.company,
            oportunidad=oportunidad,
            tipo=tipo,
            descripcion=descripcion,
            usuario=usuario,
            metadata=metadata or {},
        )
        return evento

    @staticmethod
    def agregar_nota(oportunidad: CrmOportunidad, nota: str, usuario=None) -> CrmTimelineEvent:
        return TimelineService.registrar(
            oportunidad, TipoTimelineEvent.NOTA, nota, usuario=usuario,
        )
