"""
SaiSuite — SQS Consumer for Contabilidad Sync
Lee mensajes de la cola SQS enviados por el Agente Go en Windows,
deserializa el payload y llama al SyncService correspondiente.

Tipos de mensaje:
  - gl_batch   → SyncService.process_gl_batch()
  - acct_full  → SyncService.process_acct_full()
  - ref_*      → tablas de referencia (terceros, departamentos, etc.)

Estructura del mensaje SQS (body JSON):
{
  "type": "gl_batch",
  "company_id": "<uuid>",
  "conn_id": "conn_001",
  "timestamp": "2026-04-04T12:00:00Z",
  "data": { ... }
}
"""
import json
import logging
import time
import traceback

import boto3
from botocore.exceptions import ClientError
from django.conf import settings

from apps.contabilidad.services import SyncService
from apps.crm.producto_services import ImpuestoSyncService, ProductoSyncService



logger = logging.getLogger(__name__)


# ── Handlers por tipo de mensaje ─────────────────────────────────────────────

def _handle_gl_batch(company_id: str, data: dict) -> dict:
    """Procesa un batch incremental de movimientos GL."""
    records = data.get('records', [])
    return SyncService.process_gl_batch(company_id=company_id, records=records)


def _handle_acct_full(company_id: str, data: dict) -> dict:
    """Procesa un sync completo del plan de cuentas."""
    records = data.get('records', [])
    logger.info('acct_full_received', extra={'record_count': len(records), 'data_keys': list(data.keys())})
    return SyncService.process_acct_full(company_id=company_id, records=records)


def _handle_oe_batch(company_id: str, data: dict) -> dict:
    """Procesa un batch de encabezados de factura (OE)."""
    records = data.get('records', [])
    return SyncService.process_oe_batch(company_id=company_id, records=records)


def _handle_oedet_batch(company_id: str, data: dict) -> dict:
    """Procesa un batch de líneas de factura (OEDET)."""
    records = data.get('records', [])
    return SyncService.process_oedet_batch(company_id=company_id, records=records)


def _handle_carpro_batch(company_id: str, data: dict) -> dict:
    """Procesa un batch de movimientos de cartera (CARPRO)."""
    records = data.get('records', [])
    return SyncService.process_carpro_batch(company_id=company_id, records=records)


def _handle_itemact_batch(company_id: str, data: dict) -> dict:
    """Procesa un batch de movimientos de inventario (ITEMACT)."""
    records = data.get('records', [])
    return SyncService.process_itemact_batch(company_id=company_id, records=records)


def _handle_reference(table: str, company_id: str, data: dict) -> dict:
    """
    Procesa tablas de referencia (terceros, departamentos, proyectos, actividades).
    table: 'cust', 'cust_batch', 'lista', 'proyectos', 'actividades'
    Para cust/cust_batch se pasa data completo (incluye shipto y tributaria).
    """
    records = data.get('records', [])
    return SyncService.process_reference(
        table=table,
        company_id=company_id,
        records=records,
        data=data,
    )


def _handle_vendedores_full(company_id: str, data: dict) -> dict:
    """Procesa sync completo de vendedores (VENDEDOR) → VendedorSaiopen."""
    records = data.get('records', [])
    return SyncService.process_vendedores(company_id=company_id, records=records)


def _handle_taxauth_full(company_id: str, data: dict) -> dict:
    """Procesa sync completo de impuestos (TAXAUTH) → CrmImpuesto."""
    from apps.companies.models import Company
    records = data.get('records', [])
    try:
        company = Company.objects.get(id=company_id)
        return ImpuestoSyncService.sync_from_payload(company, records)
    except Company.DoesNotExist:
        logger.error('taxauth_company_not_found', extra={'company_id': company_id})
        return {'inserted': 0, 'updated': 0, 'errors': [f'Company {company_id} not found']}


def _handle_item_full(company_id: str, data: dict) -> dict:
    """Procesa sync de productos (ITEM) → CrmProducto."""
    from apps.companies.models import Company
    records = data.get('records', [])
    try:
        company = Company.objects.get(id=company_id)
        return ProductoSyncService.sync_from_payload(company, records)
    except Company.DoesNotExist:
        logger.error('item_company_not_found', extra={'company_id': company_id})
        return {'inserted': 0, 'updated': 0, 'errors': [f'Company {company_id} not found']}


# Mapeo directo de msg_type → table name para el dispatcher
# cust_full y cust_batch incluyen shipto+tributaria atómicamente
_REFERENCE_TYPE_MAP = {
    'cust_full':        'cust',
    'cust_batch':       'cust_batch',
    'lista_full':       'lista',
    'proyectos_full':   'proyectos',
    'actividades_full': 'actividades',
    'tipdoc_full':      'tipdoc',
}


def _dispatch(msg_type: str, company_id: str, data: dict) -> dict:
    """Despacha el mensaje al handler correcto."""
    if msg_type == 'gl_batch':
        return _handle_gl_batch(company_id, data)
    if msg_type == 'acct_full':
        return _handle_acct_full(company_id, data)
    if msg_type == 'oe_batch':
        return _handle_oe_batch(company_id, data)
    if msg_type == 'oedet_batch':
        return _handle_oedet_batch(company_id, data)
    if msg_type == 'carpro_batch':
        return _handle_carpro_batch(company_id, data)
    if msg_type == 'itemact_batch':
        return _handle_itemact_batch(company_id, data)
    if msg_type in _REFERENCE_TYPE_MAP:
        return _handle_reference(_REFERENCE_TYPE_MAP[msg_type], company_id, data)
    if msg_type == 'taxauth_full':
        return _handle_taxauth_full(company_id, data)
    if msg_type == 'item_full':
        return _handle_item_full(company_id, data)
    if msg_type == 'vendedores_full':
        return _handle_vendedores_full(company_id, data)
    raise ValueError(f'Unknown message type: {msg_type}')


# ── Procesador de un mensaje individual ──────────────────────────────────────

def process_message(body: str) -> bool:
    """
    Deserializa y procesa un mensaje SQS.
    Retorna True si fue procesado exitosamente (el caller debe borrar el mensaje).
    Retorna False si debe reintentarse (no borrar → SQS lo reencola).
    """
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as e:
        logger.error('sqs_invalid_json', extra={'error': str(e), 'body_preview': body[:200]})
        return True  # JSON inválido no mejora con reintentos — descartar

    msg_type   = payload.get('type', '')
    company_id = payload.get('company_id', '')
    data       = payload.get('data', {})
    conn_id    = payload.get('conn_id', '')

    if not msg_type or not company_id:
        logger.error('sqs_missing_fields', extra={'payload': payload})
        return True  # Mensaje malformado — descartar

    logger.info('sqs_processing', extra={
        'type': msg_type,
        'company_id': company_id,
        'conn_id': conn_id,
    })

    try:
        result = _dispatch(msg_type, company_id, data)
        logger.info('sqs_processed', extra={
            'type': msg_type,
            'company_id': company_id,
            'conn_id': conn_id,
            'inserted': result.get('inserted', 0),
            'updated': result.get('updated', 0),
            'errors': len(result.get('errors', [])),
        })
        return True

    except Exception as e:
        logger.exception('sqs_process_failed: type=%s company=%s error=%s',
                         msg_type, company_id, e)
        return False  # Dejar en cola para reintento


# ── Worker principal ──────────────────────────────────────────────────────────

class SQSWorker:
    """
    Worker que hace long-polling de SQS y despacha mensajes a SyncService.

    Configuración (en settings.py):
        SQS_TO_CLOUD_URL    — URL de la cola
        AWS_ACCESS_KEY_ID   — Credenciales de lectura
        AWS_SECRET_ACCESS_KEY
        AWS_DEFAULT_REGION
    """

    # Cuántos mensajes pedir por ciclo (máx. 10 en SQS estándar)
    BATCH_SIZE = 10
    # Long-polling: esperar hasta 20s si la cola está vacía
    WAIT_SECONDS = 20
    # Visibility timeout: cuántos segundos tiene Django para procesar antes de que SQS lo reencole
    VISIBILITY_TIMEOUT = 120

    def __init__(self):
        self.queue_url = settings.SQS_TO_CLOUD_URL
        self.client = boto3.client(
            'sqs',
            region_name=settings.AWS_DEFAULT_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

    def run(self, max_cycles: int = 0):
        """
        Bucle principal de polling.
        max_cycles=0 → corre indefinidamente (modo producción).
        max_cycles=N → útil para tests.
        """
        if not self.queue_url:
            logger.error('sqs_worker_no_queue_url')
            raise RuntimeError('SQS_TO_CLOUD_URL no está configurada en settings.')

        logger.info('sqs_worker_started', extra={'queue_url': self.queue_url})
        cycles = 0

        while True:
            try:
                self._poll_once()
            except ClientError as e:
                logger.error('sqs_client_error', extra={'error': str(e)})
                time.sleep(5)
            except Exception as e:
                logger.exception('sqs_unexpected_error: %s', e)
                time.sleep(5)

            cycles += 1
            if max_cycles and cycles >= max_cycles:
                break

    def _poll_once(self):
        """Lee un batch de mensajes y los procesa."""
        response = self.client.receive_message(
            QueueUrl=self.queue_url,
            MaxNumberOfMessages=self.BATCH_SIZE,
            WaitTimeSeconds=self.WAIT_SECONDS,
            VisibilityTimeout=self.VISIBILITY_TIMEOUT,
            MessageAttributeNames=['All'],
        )

        messages = response.get('Messages', [])
        if not messages:
            return

        logger.info('sqs_batch_received', extra={'count': len(messages)})

        for msg in messages:
            receipt_handle = msg['ReceiptHandle']
            body = msg.get('Body', '')

            success = process_message(body)

            if success:
                # Borrar el mensaje de la cola — ya fue procesado
                self.client.delete_message(
                    QueueUrl=self.queue_url,
                    ReceiptHandle=receipt_handle,
                )
            else:
                # No borrar → SQS lo reencola automáticamente al vencer el visibility timeout
                logger.warning('sqs_message_left_for_retry', extra={'body_preview': body[:100]})
