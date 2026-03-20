from django.urls import path
from .views import webhook_tercero_desde_saiopen

urlpatterns = [
    path('saiopen/tercero/', webhook_tercero_desde_saiopen, name='webhook-tercero-saiopen'),
]
