import threading
from django.db import models

_current_company = threading.local()


def get_current_company():
    return getattr(_current_company, 'company', None)


def set_current_company(company):
    _current_company.company = company


def clear_current_company():
    _current_company.company = None


class CompanyManager(models.Manager):
    """
    Manager que filtra automáticamente por la empresa activa del request.
    Activado por CompanyMiddleware en cada request autenticado.
    """
    def get_queryset(self):
        qs = super().get_queryset()
        company = get_current_company()
        if company is not None:
            return qs.filter(company=company)
        return qs
