"""
SaiSuite -- Contabilidad: URLs
POST endpoints para recibir datos de sync desde el agente.
"""
from django.urls import path

from apps.contabilidad.views import (
    GLBatchSyncView,
    ACCTSyncView,
    OEBatchSyncView,
    OEDetBatchSyncView,
    CARPROBatchSyncView,
    ITEMACTBatchSyncView,
    SyncStatusView,
    GLMovimientoListView,
)

app_name = 'contabilidad'

urlpatterns = [
    # GL / Contabilidad
    path('sync/gl-batch/', GLBatchSyncView.as_view(), name='sync-gl-batch'),
    path('sync/acct/', ACCTSyncView.as_view(), name='sync-acct'),
    # OE / Facturación
    path('sync/oe-batch/', OEBatchSyncView.as_view(), name='sync-oe-batch'),
    path('sync/oedet-batch/', OEDetBatchSyncView.as_view(), name='sync-oedet-batch'),
    # CARPRO / Cartera
    path('sync/carpro-batch/', CARPROBatchSyncView.as_view(), name='sync-carpro-batch'),
    # ITEMACT / Inventario
    path('sync/itemact-batch/', ITEMACTBatchSyncView.as_view(), name='sync-itemact-batch'),
    # Status y listado
    path('sync/status/', SyncStatusView.as_view(), name='sync-status'),
    path('movimientos/', GLMovimientoListView.as_view(), name='gl-movimientos'),
]
