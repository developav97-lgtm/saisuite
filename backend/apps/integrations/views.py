# integrations — views
"""
SaiSuite — Integraciones: Webhooks y endpoints para agentes externos.
"""
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def webhook_tercero_desde_saiopen(request: Request) -> Response:
    """
    Webhook invocado por el agente Saiopen cuando detecta cambios en terceros.
    El agente envía los datos del tercero en Saiopen y este endpoint los upserta en Saisuite.

    Body esperado:
    {
        "sai_key": "1|900123456",
        "saiopen_id": "900123456",
        "tipo_identificacion": "nit",
        "numero_identificacion": "900123456",
        "razon_social": "Empresa ABC S.A.S",
        "tipo_persona": "juridica",
        "tipo_tercero": "proveedor",
        "email": "...",
        "telefono": "..."
    }
    """
    from apps.terceros.services import recibir_tercero_desde_saiopen

    payload = request.data
    company = request.user.company
    logger.info(
        'webhook_tercero_saiopen_recibido',
        extra={'company_id': str(company.id), 'sai_key': payload.get('sai_key')},
    )

    try:
        tercero = recibir_tercero_desde_saiopen(company, payload)
    except Exception as exc:
        logger.error('webhook_tercero_saiopen_error', extra={'error': str(exc)})
        return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'id': str(tercero.id), 'codigo': tercero.codigo}, status=status.HTTP_200_OK)
