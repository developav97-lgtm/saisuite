"""
SaiSuite — Proyectos: Services
TODA la lógica de negocio va aquí. Las views solo orquestan.
"""
import logging
from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, Count, Q, QuerySet
from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied

from apps.proyectos.models import (
    Proyecto, Fase,
    EstadoProyecto,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Excepciones del módulo
# ──────────────────────────────────────────────

class ProyectoException(ValidationError):
    """Base para errores del módulo de proyectos."""


class TransicionEstadoInvalidaException(ProyectoException):
    pass


class PresupuestoExcedidoException(ProyectoException):
    pass


class ProyectoNoEditableException(ProyectoException):
    pass


# ──────────────────────────────────────────────
# Máquina de estados
# ──────────────────────────────────────────────

# Transiciones válidas: estado_actual → [estados_destino]
TRANSICIONES_VALIDAS: dict[str, list[str]] = {
    EstadoProyecto.BORRADOR:     [EstadoProyecto.PLANIFICADO, EstadoProyecto.CANCELADO],
    EstadoProyecto.PLANIFICADO:  [EstadoProyecto.EN_EJECUCION, EstadoProyecto.BORRADOR, EstadoProyecto.CANCELADO],
    EstadoProyecto.EN_EJECUCION: [EstadoProyecto.SUSPENDIDO, EstadoProyecto.CERRADO, EstadoProyecto.CANCELADO],
    EstadoProyecto.SUSPENDIDO:   [EstadoProyecto.EN_EJECUCION, EstadoProyecto.CANCELADO],
    EstadoProyecto.CERRADO:      [],
    EstadoProyecto.CANCELADO:    [],
}

# Estados que permiten edición del proyecto
ESTADOS_EDITABLES = {EstadoProyecto.BORRADOR, EstadoProyecto.PLANIFICADO}


# ──────────────────────────────────────────────
# ProyectoService
# ──────────────────────────────────────────────

class ProyectoService:

    @staticmethod
    def list_proyectos(company=None) -> QuerySet:
        """
        Retorna QuerySet de proyectos activos con anotaciones útiles.
        `company` se pasa explícitamente desde la view para garantizar
        aislamiento multi-tenant con JWT (el middleware no intercepta DRF auth).
        """
        qs = (
            Proyecto.all_objects
            .filter(activo=True)
            .select_related('gerente', 'coordinador', 'company')
            .annotate(fases_count=Count('fases', filter=Q(fases__activo=True)))
        )
        if company is not None:
            qs = qs.filter(company=company)
        return qs

    @staticmethod
    def get_proyecto(proyecto_id: str) -> Proyecto:
        """Retorna proyecto con relaciones cargadas."""
        return (
            Proyecto.objects
            .select_related('gerente', 'coordinador', 'company')
            .prefetch_related('fases')
            .get(id=proyecto_id)
        )

    @staticmethod
    def _generar_codigo(company) -> str:
        """Genera código autoincremental por empresa: PRY-001, PRY-002, ..."""
        ultimo = (
            Proyecto.all_objects
            .filter(company=company)
            .order_by('-created_at')
            .values_list('codigo', flat=True)
            .first()
        )
        if not ultimo or not ultimo.startswith('PRY-'):
            numero = 1
        else:
            try:
                numero = int(ultimo.split('-')[1]) + 1
            except (IndexError, ValueError):
                numero = 1
        return f'PRY-{numero:03d}'

    @staticmethod
    def _validar_gerente(gerente_id: str, company) -> object:
        """Verifica que el gerente pertenece a la misma empresa."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            gerente = User.objects.get(id=gerente_id, company=company)
        except User.DoesNotExist:
            raise ProyectoException(
                {'gerente': 'El gerente debe pertenecer a la misma empresa.'}
            )
        return gerente

    @staticmethod
    def _validar_coordinador(coordinador_id: str | None, company) -> object | None:
        """Verifica que el coordinador pertenece a la misma empresa."""
        if not coordinador_id:
            return None
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            return User.objects.get(id=coordinador_id, company=company)
        except User.DoesNotExist:
            raise ProyectoException(
                {'coordinador': 'El coordinador debe pertenecer a la misma empresa.'}
            )

    @staticmethod
    def create_proyecto(data: dict, user) -> Proyecto:
        """Crea un nuevo proyecto validando reglas de negocio."""
        company = user.company
        gerente_id     = data.pop('gerente')
        coordinador_id = data.pop('coordinador', None)

        gerente     = ProyectoService._validar_gerente(str(gerente_id), company)
        coordinador = ProyectoService._validar_coordinador(
            str(coordinador_id) if coordinador_id else None, company
        )

        # Auto-generar código si no viene
        if not data.get('codigo'):
            data['codigo'] = ProyectoService._generar_codigo(company)

        proyecto = Proyecto(
            company=company,
            gerente=gerente,
            coordinador=coordinador,
            **data,
        )
        proyecto.full_clean()
        proyecto.save()

        logger.info(
            'Proyecto creado',
            extra={'proyecto_id': str(proyecto.id), 'codigo': proyecto.codigo, 'user': user.email},
        )
        return proyecto

    @staticmethod
    def update_proyecto(proyecto: Proyecto, data: dict) -> Proyecto:
        """Actualiza proyecto — solo permitido en estados editables."""
        if proyecto.estado not in ESTADOS_EDITABLES:
            raise ProyectoNoEditableException(
                f'No se puede editar un proyecto en estado "{proyecto.get_estado_display()}".'
            )

        company = proyecto.company
        if 'gerente' in data:
            data['gerente'] = ProyectoService._validar_gerente(str(data['gerente']), company)
        if 'coordinador' in data:
            data['coordinador'] = ProyectoService._validar_coordinador(
                str(data['coordinador']) if data['coordinador'] else None, company
            )

        for campo, valor in data.items():
            setattr(proyecto, campo, valor)

        proyecto.full_clean()
        proyecto.save()

        logger.info('Proyecto actualizado', extra={'proyecto_id': str(proyecto.id)})
        return proyecto

    @staticmethod
    def soft_delete_proyecto(proyecto: Proyecto) -> None:
        """Soft delete: marca proyecto y todas sus fases como inactivos."""
        proyecto.activo = False
        proyecto.save(update_fields=['activo', 'updated_at'])
        proyecto.fases.filter(activo=True).update(activo=False)
        logger.info('Proyecto eliminado (soft)', extra={'proyecto_id': str(proyecto.id)})

    @staticmethod
    def cambiar_estado(proyecto: Proyecto, nuevo_estado: str, forzar: bool = False) -> Proyecto:
        """
        Cambia el estado del proyecto con validación de transiciones y precondiciones.
        """
        estado_actual = proyecto.estado
        transiciones  = TRANSICIONES_VALIDAS.get(estado_actual, [])

        if nuevo_estado not in transiciones:
            raise TransicionEstadoInvalidaException(
                f'No se puede pasar de "{proyecto.get_estado_display()}" '
                f'a "{dict(proyecto.EstadoProyecto.choices).get(nuevo_estado, nuevo_estado)}".'
                if hasattr(proyecto, 'EstadoProyecto')
                else f'Transición de estado inválida: {estado_actual} → {nuevo_estado}.'
            )

        # Precondiciones por transición
        if estado_actual == EstadoProyecto.BORRADOR and nuevo_estado == EstadoProyecto.PLANIFICADO:
            fases_activas = proyecto.fases.filter(activo=True).count()
            if fases_activas == 0:
                raise TransicionEstadoInvalidaException(
                    'Para planificar el proyecto debe tener al menos 1 fase definida.'
                )
            if proyecto.presupuesto_total <= Decimal('0'):
                raise TransicionEstadoInvalidaException(
                    'Para planificar el proyecto debe tener un presupuesto total mayor a cero.'
                )

        if estado_actual == EstadoProyecto.PLANIFICADO and nuevo_estado == EstadoProyecto.EN_EJECUCION:
            if not proyecto.sincronizado_con_saiopen:
                raise TransicionEstadoInvalidaException(
                    'El proyecto debe estar sincronizado con Saiopen antes de iniciar ejecución.'
                )

        if estado_actual == EstadoProyecto.EN_EJECUCION and nuevo_estado == EstadoProyecto.CERRADO:
            if not forzar:
                fases_incompletas = proyecto.fases.filter(
                    activo=True, porcentaje_avance__lt=100
                ).count()
                if fases_incompletas > 0:
                    raise TransicionEstadoInvalidaException(
                        f'Hay {fases_incompletas} fase(s) con avance menor al 100%. '
                        f'Use forzar=True para cerrar igualmente.'
                    )

        # Registrar fecha real de inicio/fin
        if nuevo_estado == EstadoProyecto.EN_EJECUCION and not proyecto.fecha_inicio_real:
            proyecto.fecha_inicio_real = timezone.now().date()
        if nuevo_estado in {EstadoProyecto.CERRADO, EstadoProyecto.CANCELADO}:
            if not proyecto.fecha_fin_real:
                proyecto.fecha_fin_real = timezone.now().date()

        proyecto.estado = nuevo_estado
        proyecto.save(update_fields=['estado', 'fecha_inicio_real', 'fecha_fin_real', 'updated_at'])

        logger.info(
            'Estado de proyecto cambiado',
            extra={
                'proyecto_id': str(proyecto.id),
                'estado_anterior': estado_actual,
                'estado_nuevo': nuevo_estado,
            },
        )
        return proyecto

    @staticmethod
    def get_estado_financiero(proyecto: Proyecto) -> dict:
        """
        Calcula el estado financiero del proyecto:
        presupuesto, ejecutado (docs contables), AIU y desviaciones.
        """
        from django.db.models import Sum as DbSum

        # Presupuesto por categorías (suma de fases activas)
        fases_agg = proyecto.fases.filter(activo=True).aggregate(
            total_mano_obra=DbSum('presupuesto_mano_obra'),
            total_materiales=DbSum('presupuesto_materiales'),
            total_subcontratos=DbSum('presupuesto_subcontratos'),
            total_equipos=DbSum('presupuesto_equipos'),
            total_otros=DbSum('presupuesto_otros'),
        )

        def _d(val) -> Decimal:
            return val or Decimal('0')

        presupuesto_costos = (
            _d(fases_agg['total_mano_obra'])
            + _d(fases_agg['total_materiales'])
            + _d(fases_agg['total_subcontratos'])
            + _d(fases_agg['total_equipos'])
            + _d(fases_agg['total_otros'])
        )

        # AIU sobre costos directos
        aiu_factor = (
            proyecto.porcentaje_administracion
            + proyecto.porcentaje_imprevistos
            + proyecto.porcentaje_utilidad
        ) / Decimal('100')
        precio_venta_aiu = presupuesto_costos * (1 + aiu_factor)

        # Costo ejecutado (documentos contables importados de Saiopen)
        docs_agg = proyecto.documentos.aggregate(ejecutado=DbSum('valor_neto'))
        costo_ejecutado = _d(docs_agg['ejecutado'])

        # Avance financiero
        pct_financiero = (
            (costo_ejecutado / presupuesto_costos * 100)
            if presupuesto_costos > 0
            else Decimal('0')
        )

        # Avance físico (promedio ponderado de fases — simplificado por orden)
        fases_avance = proyecto.fases.filter(activo=True).values_list('porcentaje_avance', flat=True)
        pct_fisico = (
            sum(fases_avance) / len(fases_avance)
            if fases_avance
            else Decimal('0')
        )

        return {
            'presupuesto_total':       str(proyecto.presupuesto_total),
            'presupuesto_costos':      str(presupuesto_costos),
            'precio_venta_aiu':        str(precio_venta_aiu.quantize(Decimal('0.01'))),
            'costo_ejecutado':         str(costo_ejecutado),
            'porcentaje_avance_fisico':  str(round(pct_fisico, 2)),
            'porcentaje_avance_financiero': str(round(pct_financiero, 2)),
            'desviacion_presupuesto':  str((costo_ejecutado - presupuesto_costos).quantize(Decimal('0.01'))),
            'desglose_presupuesto': {
                'mano_obra':    str(_d(fases_agg['total_mano_obra'])),
                'materiales':   str(_d(fases_agg['total_materiales'])),
                'subcontratos': str(_d(fases_agg['total_subcontratos'])),
                'equipos':      str(_d(fases_agg['total_equipos'])),
                'otros':        str(_d(fases_agg['total_otros'])),
            },
            'aiu': {
                'porcentaje_administracion': str(proyecto.porcentaje_administracion),
                'porcentaje_imprevistos':    str(proyecto.porcentaje_imprevistos),
                'porcentaje_utilidad':       str(proyecto.porcentaje_utilidad),
                'valor_aiu':                 str((precio_venta_aiu - presupuesto_costos).quantize(Decimal('0.01'))),
            },
        }


# ──────────────────────────────────────────────
# FaseService
# ──────────────────────────────────────────────

class FaseService:

    @staticmethod
    def list_fases(proyecto: Proyecto) -> QuerySet:
        """Retorna fases activas del proyecto, ordenadas."""
        return proyecto.fases.filter(activo=True).order_by('orden')

    @staticmethod
    def _calcular_presupuesto_fases(proyecto: Proyecto, excluir_fase_id=None) -> Decimal:
        """Suma el presupuesto total de todas las fases activas del proyecto."""
        qs = proyecto.fases.filter(activo=True)
        if excluir_fase_id:
            qs = qs.exclude(id=excluir_fase_id)

        agg = qs.aggregate(
            total=Sum('presupuesto_mano_obra')
                + Sum('presupuesto_materiales')
                + Sum('presupuesto_subcontratos')
                + Sum('presupuesto_equipos')
                + Sum('presupuesto_otros')
        )
        return agg.get('total') or Decimal('0')

    @staticmethod
    @transaction.atomic
    def create_fase(proyecto: Proyecto, data: dict) -> Fase:
        """Crea una fase validando presupuesto y orden."""
        if proyecto.estado in {EstadoProyecto.CERRADO, EstadoProyecto.CANCELADO}:
            raise ProyectoNoEditableException(
                f'No se pueden agregar fases a un proyecto en estado "{proyecto.get_estado_display()}".'
            )

        # Bloquear fila del proyecto para evitar race conditions
        proyecto_locked = Proyecto.all_objects.select_for_update().get(id=proyecto.id)

        # Calcular presupuesto de nueva fase
        nueva_fase_presupuesto = (
            (data.get('presupuesto_mano_obra') or Decimal('0'))
            + (data.get('presupuesto_materiales') or Decimal('0'))
            + (data.get('presupuesto_subcontratos') or Decimal('0'))
            + (data.get('presupuesto_equipos') or Decimal('0'))
            + (data.get('presupuesto_otros') or Decimal('0'))
        )

        presupuesto_actual = FaseService._calcular_presupuesto_fases(proyecto_locked)
        if (presupuesto_actual + nueva_fase_presupuesto) > proyecto_locked.presupuesto_total:
            disponible = proyecto_locked.presupuesto_total - presupuesto_actual
            raise PresupuestoExcedidoException(
                f'El presupuesto de las fases excedería el presupuesto total del proyecto. '
                f'Disponible: {disponible}. Solicitado: {nueva_fase_presupuesto}.'
            )

        # Auto-ordenar si no viene orden
        if 'orden' not in data or data['orden'] is None:
            ultimo_orden = (
                proyecto_locked.fases.filter(activo=True)
                .order_by('-orden')
                .values_list('orden', flat=True)
                .first()
            )
            data['orden'] = (ultimo_orden or 0) + 1

        fase = Fase(
            proyecto=proyecto_locked,
            company=proyecto_locked.company,
            **data,
        )
        fase.full_clean()
        fase.save()

        logger.info(
            'Fase creada',
            extra={'fase_id': str(fase.id), 'proyecto_id': str(proyecto.id), 'orden': fase.orden},
        )
        return fase

    @staticmethod
    @transaction.atomic
    def update_fase(fase: Fase, data: dict) -> Fase:
        """Actualiza una fase validando presupuesto."""
        proyecto_locked = Proyecto.all_objects.select_for_update().get(id=fase.proyecto_id)

        # Calcular nuevo presupuesto de la fase
        nueva_mano_obra    = data.get('presupuesto_mano_obra',    fase.presupuesto_mano_obra)
        nueva_materiales   = data.get('presupuesto_materiales',   fase.presupuesto_materiales)
        nueva_subcontratos = data.get('presupuesto_subcontratos', fase.presupuesto_subcontratos)
        nueva_equipos      = data.get('presupuesto_equipos',      fase.presupuesto_equipos)
        nueva_otros        = data.get('presupuesto_otros',        fase.presupuesto_otros)

        nuevo_presupuesto_fase = (
            nueva_mano_obra + nueva_materiales
            + nueva_subcontratos + nueva_equipos + nueva_otros
        )

        presupuesto_resto = FaseService._calcular_presupuesto_fases(
            proyecto_locked, excluir_fase_id=fase.id
        )
        if (presupuesto_resto + nuevo_presupuesto_fase) > proyecto_locked.presupuesto_total:
            disponible = proyecto_locked.presupuesto_total - presupuesto_resto
            raise PresupuestoExcedidoException(
                f'El presupuesto actualizado excedería el presupuesto total del proyecto. '
                f'Disponible: {disponible}. Solicitado: {nuevo_presupuesto_fase}.'
            )

        for campo, valor in data.items():
            setattr(fase, campo, valor)

        fase.full_clean()
        fase.save()

        logger.info('Fase actualizada', extra={'fase_id': str(fase.id)})
        return fase

    @staticmethod
    def soft_delete_fase(fase: Fase) -> None:
        """Soft delete de la fase."""
        fase.activo = False
        fase.save(update_fields=['activo', 'updated_at'])
        logger.info('Fase eliminada (soft)', extra={'fase_id': str(fase.id)})
