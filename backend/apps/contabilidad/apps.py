"""
SaiSuite -- Contabilidad App Config
Mirror de datos contables de Saiopen (Firebird GL / ACCT).
"""
from django.apps import AppConfig


class ContabilidadConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.contabilidad'
    app_label = 'contabilidad'
    verbose_name = 'Contabilidad'
