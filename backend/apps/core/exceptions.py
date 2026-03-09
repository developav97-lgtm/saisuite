"""SaiSuite — Excepciones base del proyecto."""
from rest_framework.exceptions import APIException
from rest_framework import status


class SaiSuiteException(APIException):
    """Excepción base. Cada dominio define sus propias excepciones heredando de esta."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Error en la operación.'
    default_code = 'saisuite_error'


class SyncException(SaiSuiteException):
    """Error en sincronización con Firebird/SQS."""
    default_detail = 'Error de sincronización con Saiopen.'
    default_code = 'sync_error'
