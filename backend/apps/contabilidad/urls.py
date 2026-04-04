"""
SaiSuite -- Contabilidad: URLs
POST endpoints para recibir datos de sync desde el agente.
"""
from django.urls import path

from apps.contabilidad.views import (
    GLBatchSyncView,
    ACCTSyncView,
    SyncStatusView,
)

app_name = 'contabilidad'

urlpatterns = [
    path('sync/gl-batch/', GLBatchSyncView.as_view(), name='sync-gl-batch'),
    path('sync/acct/', ACCTSyncView.as_view(), name='sync-acct'),
    path('sync/status/', SyncStatusView.as_view(), name='sync-status'),
]
