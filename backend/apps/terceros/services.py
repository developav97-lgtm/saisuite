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

# Mapa de normalización de tipo_tercero desde valores Saiopen (inglés) al
# vocabulario español del modelo.  Se aplica en recibir_tercero_desde_saiopen.
SAIOPEN_TIPO_MAP: dict[str, str] = {
    'CUSTOMER':      'cliente',
    'CLIENT':        'cliente',
    'SUPPLIER':      'proveedor',
    'VENDOR':        'proveedor',
    'SUBCONTRACTOR': 'subcontratista',
    'INSPECTOR':     'interventor',
    'CONSULTANT':    'consultor',
    'EMPLOYEE':      'empleado',
    'OTHER':         'otro',
}


def _normalizar_tipo_tercero(valor: str) -> str:
    """
    Convierte el tipo_tercero recibido desde Saiopen al vocabulario español
    del modelo.  Si no hay match en el mapa, retorna el valor original en
    minúsculas para máxima compatibilidad.
    """
    return SAIOPEN_TIPO_MAP.get(valor.upper(), valor.lower())


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
        'tipo_tercero':          _normalizar_tipo_tercero(payload.get('tipo_tercero', '')),
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


# ── TerceroSyncService — doble vía CUST → Tercero ─────────────────────────────

class TerceroSyncService:
    """
    Sincroniza datos de TerceroSaiopen (espejo de CUST) hacia el modelo Tercero
    de la app, que es utilizado por proyectos y otros módulos.
    """

    @staticmethod
    def upsert_from_saiopen(
        company_id,
        terceros_saiopen: list,
        shipto_list: list,
        tributaria_list: list,
    ) -> None:
        """
        Crea o actualiza Terceros en la app a partir de los datos recibidos de Saiopen.

        Reglas:
        - tipo_persona: natural si primer_nombre no vacío en TRIBUTARIA, jurídica si no
        - tipo_identificacion: NIT si jurídica, CC si natural (default)
        - tipo_tercero: cliente > proveedor > empleado (jerarquía)
        - Se sincronizan todos los terceros activos (clientes, proveedores, empleados)
        - Los inactivos no se crean pero sí se actualizan si ya existen
        - numero_identificacion = ID_N (sin dígito de verificación si es NIT)
        - Dirección principal: tomada de ShipTo con succliente=0 si existe
        """
        from apps.terceros.models import Tercero, TipoPersona, TipoIdentificacion, TipoTercero

        # Indexar tributaria y shipto por id_n para lookup O(1)
        trib_by_idn: dict = {}
        for t in tributaria_list:
            trib_by_idn[t.id_n] = t

        shipto_principal: dict = {}
        for s in shipto_list:
            if s.succliente == 0:
                shipto_principal[s.id_n] = s

        # Obtener Terceros existentes vinculados a Saiopen para esta empresa
        existing_map: dict = {
            t.saiopen_id: t
            for t in Tercero.objects.filter(
                company_id=company_id,
                saiopen_id__in=[ts.id_n for ts in terceros_saiopen],
            )
        }

        to_create = []
        to_update = []

        for ts in terceros_saiopen:
            trib = trib_by_idn.get(ts.id_n)
            shipto = shipto_principal.get(ts.id_n)

            # ── Determinar tipo_persona ──────────────────────────────────────
            es_natural = bool(trib and trib.primer_nombre.strip())
            tipo_persona = TipoPersona.NATURAL if es_natural else TipoPersona.JURIDICA

            # ── Determinar tipo_identificacion ───────────────────────────────
            if es_natural:
                tipo_id = TipoIdentificacion.CC
            else:
                tipo_id = TipoIdentificacion.NIT

            # ── Normalizar número de identificación (ID_N sin dígito verif.) ─
            numero_id = str(ts.id_n).strip()

            # ── Determinar tipo_tercero (jerarquía) ──────────────────────────
            if ts.es_cliente:
                tipo_tercero = TipoTercero.CLIENTE
            elif ts.es_proveedor:
                tipo_tercero = TipoTercero.PROVEEDOR
            else:
                tipo_tercero = TipoTercero.EMPLEADO

            # ── Dirección principal desde ShipTo ─────────────────────────────
            direccion = ''
            if shipto:
                partes = filter(None, [shipto.addr1, shipto.addr2])
                direccion = ', '.join(partes)

            # ── Nombre completo ──────────────────────────────────────────────
            if es_natural and trib:
                razon_social = ''
                primer_nombre = trib.primer_nombre.strip()
                segundo_nombre = trib.segundo_nombre.strip()
                primer_apellido = trib.primer_apellido.strip()
                segundo_apellido = trib.segundo_apellido.strip()
            else:
                razon_social = ts.nombre.strip()
                primer_nombre = segundo_nombre = primer_apellido = segundo_apellido = ''

            existing = existing_map.get(ts.id_n)

            if existing:
                # Actualizar campos de contacto/identificación
                existing.nombre_completo = razon_social or ' '.join(filter(None, [
                    primer_nombre, segundo_nombre, primer_apellido, segundo_apellido
                ]))
                existing.razon_social = razon_social
                existing.primer_nombre = primer_nombre
                existing.segundo_nombre = segundo_nombre
                existing.primer_apellido = primer_apellido
                existing.segundo_apellido = segundo_apellido
                existing.email = ts.email or existing.email
                existing.telefono = ts.telefono or existing.telefono
                existing.activo = ts.activo
                existing.saiopen_synced = True
                if direccion:
                    pass  # dirección se maneja en TerceroDireccion, no en Tercero
                to_update.append(existing)
            else:
                # Solo crear si activo
                if not ts.activo:
                    continue

                # Generar código: usar numero_id como base
                codigo = f'SAI-{numero_id}'

                t = Tercero(
                    company_id=company_id,
                    codigo=codigo,
                    tipo_identificacion=tipo_id,
                    numero_identificacion=numero_id,
                    tipo_persona=tipo_persona,
                    tipo_tercero=tipo_tercero,
                    razon_social=razon_social,
                    primer_nombre=primer_nombre,
                    segundo_nombre=segundo_nombre,
                    primer_apellido=primer_apellido,
                    segundo_apellido=segundo_apellido,
                    email=ts.email,
                    telefono=ts.telefono,
                    saiopen_id=ts.id_n,
                    sai_key=ts.id_n,
                    saiopen_synced=True,
                    activo=True,
                )
                to_create.append(t)

        from django.db import transaction
        with transaction.atomic():
            if to_create:
                # bulk_create: save() no se llama → nombre_completo no se auto-calcula
                # Calcularlo antes
                for t in to_create:
                    t.nombre_completo = t._build_nombre_completo()
                Tercero.objects.bulk_create(
                    to_create,
                    ignore_conflicts=True,  # si ya existe (race condition) ignorar
                )
            if to_update:
                Tercero.objects.bulk_update(
                    to_update,
                    fields=[
                        'nombre_completo', 'razon_social',
                        'primer_nombre', 'segundo_nombre',
                        'primer_apellido', 'segundo_apellido',
                        'email', 'telefono', 'activo', 'saiopen_synced',
                    ],
                )

        # ── Sincronizar direcciones desde ShipTo ─────────────────────────────
        if shipto_list:
            TerceroSyncService._sync_shipto_direcciones(company_id, shipto_list)

        logger.info('tercero_sync_from_saiopen', extra={
            'company_id': str(company_id),
            'created_count': len(to_create),
            'updated_count': len(to_update),
        })

    @staticmethod
    def _sync_shipto_direcciones(company_id, shipto_list: list) -> None:
        """
        Upsert de TerceroDireccion a partir de registros ShipToSaiopen.
        - Cada fila de SHIPTO se mapea a una TerceroDireccion.
        - saiopen_linea_id = '{id_n}_{succliente}' — clave de dedup.
        - succliente == 0 → es_principal = True.
        - Si el Tercero vinculado no existe aún se omite silenciosamente.
        """
        from apps.terceros.models import Tercero, TerceroDireccion

        # Obtener todos los Terceros de esta empresa que tienen saiopen_id
        idn_set = {s.id_n for s in shipto_list}
        tercero_map: dict = {
            t.saiopen_id: t
            for t in Tercero.objects.filter(company_id=company_id, saiopen_id__in=idn_set)
        }

        # Clave de dedup: saiopen_linea_id = '{id_n}_{succliente}'
        linea_ids = [f"{s.id_n}_{s.succliente}" for s in shipto_list]
        existing_dirs: dict = {
            d.saiopen_linea_id: d
            for d in TerceroDireccion.objects.filter(
                company_id=company_id,
                saiopen_linea_id__in=linea_ids,
            )
        }

        to_create_dirs = []
        to_update_dirs = []

        for s in shipto_list:
            tercero = tercero_map.get(s.id_n)
            if not tercero:
                continue  # Tercero aún no sincronizado, se procesará en el siguiente ciclo

            linea_id = f"{s.id_n}_{s.succliente}"
            es_principal = (s.succliente == 0)

            nombre_sucursal = s.descripcion.strip() if s.descripcion else (
                'Principal' if es_principal else f'Sucursal {s.succliente}'
            )

            existing = existing_dirs.get(linea_id)
            if existing:
                existing.nombre_sucursal  = nombre_sucursal
                existing.direccion_linea1 = s.addr1 or ''
                existing.direccion_linea2 = s.addr2 or ''
                existing.ciudad           = s.ciudad or ''
                existing.departamento     = s.departamento or ''
                existing.telefono_contacto = s.telefono or ''
                existing.email_contacto   = s.email or ''
                existing.es_principal     = es_principal
                existing.activa           = True
                to_update_dirs.append(existing)
            else:
                to_create_dirs.append(TerceroDireccion(
                    company_id=company_id,
                    tercero=tercero,
                    tipo='principal' if es_principal else 'sucursal',
                    nombre_sucursal=nombre_sucursal,
                    pais='Colombia',
                    departamento=s.departamento or '',
                    ciudad=s.ciudad or '',
                    direccion_linea1=s.addr1 or '',
                    direccion_linea2=s.addr2 or '',
                    telefono_contacto=s.telefono or '',
                    email_contacto=s.email or '',
                    saiopen_linea_id=linea_id,
                    es_principal=es_principal,
                    activa=True,
                ))

        from django.db import transaction
        with transaction.atomic():
            if to_create_dirs:
                TerceroDireccion.objects.bulk_create(to_create_dirs, ignore_conflicts=True)
            if to_update_dirs:
                TerceroDireccion.objects.bulk_update(
                    to_update_dirs,
                    fields=[
                        'nombre_sucursal', 'direccion_linea1', 'direccion_linea2',
                        'ciudad', 'departamento', 'telefono_contacto', 'email_contacto',
                        'es_principal', 'activa',
                    ],
                )

        logger.info('shipto_direcciones_sync', extra={
            'company_id': str(company_id),
            'created_count': len(to_create_dirs),
            'updated_count': len(to_update_dirs),
        })
