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
    TerceroSaiopen,
    ShipToSaiopen,
    TributariaSaiopen,
    ListaSaiopen,
    ProyectoSaiopen,
    ActividadSaiopen,
    TipdocSaiopen,
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
                    fecha=record['fecha'] or None,  # None triggers NOT NULL error caught below
                    duedate=record.get('duedate') or None,
                    periodo=record.get('periodo', ''),
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
                # Agent sends: acct, nvel, class, cdgo_ttl, cdgo_grpo, cdgo_cnta, cdgo_sbcnta
                # Accept both naming conventions (Go agent fields and normalized names)
                codigo_raw = record.get('codigo') or record.get('acct')
                obj = CuentaContable(
                    company_id=company_id,
                    codigo=Decimal(str(codigo_raw)),
                    descripcion=record.get('descripcion', ''),
                    nivel=record.get('nivel') or record.get('nvel') or 0,
                    clase=record.get('clase') or record.get('class', ''),
                    tipo=record.get('tipo', ''),
                    titulo_codigo=record.get('titulo_codigo') or record.get('cdgo_ttl') or 0,
                    grupo_codigo=record.get('grupo_codigo') or record.get('cdgo_grpo') or 0,
                    cuenta_codigo=record.get('cuenta_codigo') or record.get('cdgo_cnta') or 0,
                    subcuenta_codigo=record.get('subcuenta_codigo') or record.get('cdgo_sbcnta') or 0,
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
    def process_reference(table: str, company_id, records: list[dict], data: dict = None) -> dict:
        """
        Dispatcher para tablas de referencia.
        table: 'cust', 'cust_batch', 'lista', 'proyectos', 'actividades'
        data: dict completo del mensaje SQS (solo para cust/cust_batch — incluye shipto y tributaria)
        """
        if table in ('cust', 'cust_batch'):
            return SyncService._process_cust(company_id, records, data or {})
        handlers = {
            'lista':       SyncService._process_lista,
            'proyectos':   SyncService._process_proyectos,
            'actividades': SyncService._process_actividades,
            'tipdoc':      SyncService._process_tipdoc,
        }
        handler = handlers.get(table)
        if handler is None:
            logger.warning('process_reference_unknown_table', extra={'table': table})
            return {'inserted': 0, 'updated': 0, 'errors': [f'Unknown table: {table}']}
        return handler(company_id, records)

    @staticmethod
    def _process_cust(company_id, records: list[dict], data: dict) -> dict:
        """
        Upsert atómico de CUST + SHIPTO + TRIBUTARIA.
        data puede contener 'shipto' y 'tributaria' como listas adicionales.
        Al finalizar dispara la doble vía hacia el modelo Tercero de la app.
        """
        if not records:
            return {'inserted': 0, 'updated': 0, 'errors': []}

        # ── 1. Construir objetos TerceroSaiopen ──────────────────────────────
        def _bool_field(val) -> bool:
            if isinstance(val, bool):
                return val
            return str(val).strip().upper() in ('Y', 'T', 'TRUE', 'S', '1')

        terceros = []
        for r in records:
            id_n = str(r.get('id_n', '')).strip()
            if not id_n:
                continue
            activo = not _bool_field(r.get('inactivo', False))
            fecha_raw = r.get('fecha_creacion', '') or ''
            fecha = None
            if fecha_raw:
                try:
                    from datetime import date
                    fecha = date.fromisoformat(fecha_raw[:10])
                except (ValueError, TypeError):
                    pass
            terceros.append(TerceroSaiopen(
                company_id=company_id,
                id_n=id_n,
                nit=str(r.get('nit', '')).strip(),
                nombre=str(r.get('company', '')).strip(),
                direccion=str(r.get('addr1', '')).strip(),
                ciudad=str(r.get('city', '')).strip(),
                departamento=str(r.get('departamento', '')).strip(),
                telefono=str(r.get('phone1', '')).strip(),
                telefono2=str(r.get('phone2', '')).strip(),
                email=str(r.get('email', '')).strip(),
                es_cliente=_bool_field(r.get('cliente', False)),
                es_proveedor=_bool_field(r.get('proveedor', False)),
                es_empleado=_bool_field(r.get('empleado', False)),
                activo=activo,
                acct=str(r.get('acct', '')).strip(),
                acctp=str(r.get('acctp', '')).strip(),
                regimen=str(r.get('regimen', '')).strip(),
                fecha_creacion=fecha,
                descuento=r.get('descuento') or 0,
                creditlmt=r.get('creditlmt') or 0,
                version_saiopen=int(r.get('version') or 0),
            ))

        existing_ids = set(TerceroSaiopen.objects.filter(
            company_id=company_id,
            id_n__in=[o.id_n for o in terceros],
        ).values_list('id_n', flat=True))

        # ── 2. Construir objetos ShipToSaiopen ───────────────────────────────
        shipto_list = data.get('shipto') or []
        shiptos = []
        for r in shipto_list:
            id_n = str(r.get('id_n', '')).strip()
            if not id_n:
                continue
            suc = int(r.get('succliente') or 0)
            shiptos.append(ShipToSaiopen(
                company_id=company_id,
                id_n=id_n,
                succliente=suc,
                descripcion=str(r.get('descripcion', '')).strip(),
                nombre=str(r.get('company', '')).strip(),
                addr1=str(r.get('addr1', '')).strip(),
                addr2=str(r.get('addr2', '')).strip(),
                ciudad=str(r.get('city', '')).strip(),
                departamento=str(r.get('departamento', '')).strip(),
                cod_dpto=str(r.get('cod_dpto', '')).strip(),
                cod_municipio=str(r.get('cod_municipio', '')).strip(),
                pais=str(r.get('pais', '')).strip(),
                telefono=str(r.get('phone1', '')).strip(),
                email=str(r.get('email', '')).strip(),
                zona=int(r.get('zona') or 0),
                id_vend=int(r.get('id_vend') or 0),
                estado=str(r.get('estado', '')).strip(),
                es_principal=(suc == 0),
            ))

        # ── 3. Construir objetos TributariaSaiopen ───────────────────────────
        trib_list = data.get('tributaria') or []
        tributarias = []
        for r in trib_list:
            id_n = str(r.get('id_n', '')).strip()
            if not id_n:
                continue
            tributarias.append(TributariaSaiopen(
                company_id=company_id,
                id_n=id_n,
                tdoc=int(r.get('tdoc') or 0),
                tipo_contribuyente=int(r.get('tipo_contribuyente') or 0),
                primer_nombre=str(r.get('primer_nombre', '')).strip(),
                segundo_nombre=str(r.get('segundo_nombre', '')).strip(),
                primer_apellido=str(r.get('primer_apellido', '')).strip(),
                segundo_apellido=str(r.get('segundo_apellido', '')).strip(),
            ))

        # ── 4. Upsert atómico de las tres tablas ─────────────────────────────
        with transaction.atomic():
            TerceroSaiopen.objects.bulk_create(
                terceros,
                update_conflicts=True,
                unique_fields=['company', 'id_n'],
                update_fields=[
                    'nit', 'nombre', 'direccion', 'ciudad', 'departamento',
                    'telefono', 'telefono2', 'email',
                    'es_cliente', 'es_proveedor', 'es_empleado', 'activo',
                    'acct', 'acctp', 'regimen', 'fecha_creacion',
                    'descuento', 'creditlmt', 'version_saiopen',
                ],
            )
            if shiptos:
                ShipToSaiopen.objects.bulk_create(
                    shiptos,
                    update_conflicts=True,
                    unique_fields=['company', 'id_n', 'succliente'],
                    update_fields=[
                        'descripcion', 'nombre', 'addr1', 'addr2', 'ciudad',
                        'departamento', 'cod_dpto', 'cod_municipio', 'pais',
                        'telefono', 'email', 'zona', 'id_vend', 'estado', 'es_principal',
                    ],
                )
            if tributarias:
                TributariaSaiopen.objects.bulk_create(
                    tributarias,
                    update_conflicts=True,
                    unique_fields=['company', 'id_n'],
                    update_fields=[
                        'tdoc', 'tipo_contribuyente',
                        'primer_nombre', 'segundo_nombre',
                        'primer_apellido', 'segundo_apellido',
                    ],
                )

        logger.info('cust_processed', extra={
            'company_id': str(company_id),
            'cust': len(terceros),
            'shipto': len(shiptos),
            'tributaria': len(tributarias),
            'existing': len(existing_ids),
        })

        # ── 5. Doble vía → modelo Tercero de la app ──────────────────────────
        try:
            from apps.terceros.services import TerceroSyncService
            TerceroSyncService.upsert_from_saiopen(
                company_id=company_id,
                terceros_saiopen=terceros,
                shipto_list=shiptos,
                tributaria_list=tributarias,
            )
        except Exception:
            logger.exception('cust_tercero_sync_failed', extra={'company_id': str(company_id)})
            # No propagamos — el upsert del espejo ya fue exitoso

        return {
            'inserted': len(terceros) - len(existing_ids),
            'updated': len(existing_ids),
            'errors': [],
        }

    @staticmethod
    def _process_lista(company_id, records: list[dict]) -> dict:
        """Upsert de departamentos y centros de costo desde LISTA de Saiopen."""
        if not records:
            return {'inserted': 0, 'updated': 0, 'errors': []}

        objects = []
        for r in records:
            tipo = str(r.get('tipo', '')).strip().upper()
            codigo = r.get('codigo')
            if not tipo or codigo is None:
                continue
            objects.append(ListaSaiopen(
                company_id=company_id,
                tipo=tipo,
                codigo=int(codigo),
                descripcion=str(r.get('descripcion', '')).strip(),
                activo=str(r.get('dpcc_est', 'A')).strip().upper() != 'I',
            ))

        existing = set(
            ListaSaiopen.objects.filter(
                company_id=company_id,
                tipo__in=[o.tipo for o in objects],
                codigo__in=[o.codigo for o in objects],
            ).values_list('codigo', flat=True)
        )

        with transaction.atomic():
            ListaSaiopen.objects.bulk_create(
                objects,
                update_conflicts=True,
                unique_fields=['company', 'tipo', 'codigo'],
                update_fields=['descripcion', 'activo'],
            )

        logger.info('lista_processed', extra={'company_id': str(company_id), 'total': len(objects)})
        return {'inserted': len(objects) - len(existing), 'updated': len(existing), 'errors': []}

    @staticmethod
    def _process_proyectos(company_id, records: list[dict]) -> dict:
        """Upsert de proyectos Saiopen."""
        if not records:
            return {'inserted': 0, 'updated': 0, 'errors': []}

        objects = []
        errors = []
        for idx, r in enumerate(records):
            codigo = str(r.get('codigo', '')).strip()
            if not codigo:
                continue
            try:
                from datetime import datetime

                def _parse_date(s):
                    if not s:
                        return None
                    try:
                        return datetime.strptime(s[:10], '%Y-%m-%d').date()
                    except ValueError:
                        return None

                objects.append(ProyectoSaiopen(
                    company_id=company_id,
                    codigo=codigo,
                    descripcion=str(r.get('descripcion', '')).strip(),
                    cliente_nit=str(r.get('id_nit', '')).strip(),
                    fecha_inicio=_parse_date(r.get('fecha_i')),
                    fecha_estimada_fin=_parse_date(r.get('fecha_est_t')),
                    costo_estimado=Decimal(str(r.get('costo_est', 0) or 0)),
                    estado=str(r.get('pro_est', '')).strip(),
                ))
            except Exception as exc:
                errors.append(f'Record {idx}: {exc}')

        existing = set(ProyectoSaiopen.objects.filter(
            company_id=company_id,
            codigo__in=[o.codigo for o in objects],
        ).values_list('codigo', flat=True))

        with transaction.atomic():
            ProyectoSaiopen.objects.bulk_create(
                objects,
                update_conflicts=True,
                unique_fields=['company', 'codigo'],
                update_fields=['descripcion', 'cliente_nit', 'fecha_inicio',
                               'fecha_estimada_fin', 'costo_estimado', 'estado'],
            )

        logger.info('proyectos_processed', extra={'company_id': str(company_id), 'total': len(objects)})
        return {'inserted': len(objects) - len(existing), 'updated': len(existing), 'errors': errors}

    @staticmethod
    def _process_actividades(company_id, records: list[dict]) -> dict:
        """Upsert de actividades Saiopen."""
        if not records:
            return {'inserted': 0, 'updated': 0, 'errors': []}

        objects = []
        for r in records:
            codigo = str(r.get('codigo', '')).strip()
            proyecto = str(r.get('proyecto', '')).strip()
            if not codigo:
                continue
            objects.append(ActividadSaiopen(
                company_id=company_id,
                codigo=codigo,
                descripcion=str(r.get('descripcion', '')).strip(),
                proyecto_codigo=proyecto,
                departamento_codigo=int(r.get('dp', 0) or 0),
                centro_costo_codigo=int(r.get('cc', 0) or 0),
            ))

        existing = set(ActividadSaiopen.objects.filter(
            company_id=company_id,
            codigo__in=[o.codigo for o in objects],
        ).values_list('codigo', flat=True))

        with transaction.atomic():
            ActividadSaiopen.objects.bulk_create(
                objects,
                update_conflicts=True,
                unique_fields=['company', 'codigo', 'proyecto_codigo'],
                update_fields=['descripcion', 'departamento_codigo', 'centro_costo_codigo'],
            )

        logger.info('actividades_processed', extra={'company_id': str(company_id), 'total': len(objects)})
        return {'inserted': len(objects) - len(existing), 'updated': len(existing), 'errors': []}

    @staticmethod
    def _process_tipdoc(company_id, records: list[dict]) -> dict:
        """
        Upsert de tipos de documento desde TIPDOC de Saiopen.
        PK Firebird: (CLASE, E, S). CLASE es el valor que aparece en GL.TIPO.
        """
        if not records:
            return {'inserted': 0, 'updated': 0, 'errors': []}

        objects = []
        errors = []
        for idx, r in enumerate(records):
            clase = str(r.get('clase', '')).strip()
            if not clase:
                errors.append(f'Record {idx}: missing clase')
                continue
            try:
                objects.append(TipdocSaiopen(
                    company_id=company_id,
                    clase=clase,
                    e=int(r.get('e', 0) or 0),
                    s=int(r.get('s', 0) or 0),
                    tipo=str(r.get('tipo', '') or '').strip(),
                    consecutivo=int(r.get('consecutivo', 0) or 0),
                    descripcion=str(r.get('descripcion', '') or '').strip(),
                    sigla=str(r.get('sigla', '') or '').strip(),
                    operar=str(r.get('operar', '') or '').strip(),
                    enviafacelect=str(r.get('enviafacelect', '') or '').strip(),
                    prefijo_dian=str(r.get('prefijo_dian', '') or '').strip(),
                ))
            except Exception as exc:
                errors.append(f'Record {idx}: {exc}')

        if not objects:
            return {'inserted': 0, 'updated': 0, 'errors': errors}

        existing = set(TipdocSaiopen.objects.filter(
            company_id=company_id,
            clase__in=[o.clase for o in objects],
        ).values_list('clase', flat=True))

        with transaction.atomic():
            TipdocSaiopen.objects.bulk_create(
                objects,
                update_conflicts=True,
                unique_fields=['company', 'clase', 'e', 's'],
                update_fields=[
                    'tipo', 'consecutivo', 'descripcion', 'sigla',
                    'operar', 'enviafacelect', 'prefijo_dian',
                ],
            )

        logger.info('tipdoc_processed', extra={'company_id': str(company_id), 'total': len(objects)})
        return {'inserted': len(objects) - len(existing), 'updated': len(existing), 'errors': errors}

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
