"""
SaiSuite — Tests: LicensePayment model
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from apps.companies.models import Company, CompanyLicense, LicensePayment


def make_company(nit='900200001'):
    return Company.objects.create(name='Pay Test Co', nit=nit)


def make_license(company):
    return CompanyLicense.objects.create(
        company=company,
        status='active',
        starts_at=date.today() - timedelta(days=1),
        expires_at=date.today() + timedelta(days=30),
    )


def make_payment(license_obj, amount='500000.00', method='transfer'):
    return LicensePayment.objects.create(
        license=license_obj,
        amount=Decimal(amount),
        payment_date=date.today(),
        method=method,
    )


@pytest.mark.django_db
class TestLicensePaymentModel:

    def test_crear_pago_con_license_fk(self):
        c = make_company()
        lic = make_license(c)
        pay = make_payment(lic)
        assert pay.id is not None
        assert pay.license_id == lic.id

    def test_monto_decimal(self):
        c = make_company('900200002')
        lic = make_license(c)
        pay = make_payment(lic, amount='1500000.50')
        assert pay.amount == Decimal('1500000.50')

    def test_metodo_transfer_por_defecto(self):
        c = make_company('900200003')
        lic = make_license(c)
        pay = LicensePayment.objects.create(
            license=lic,
            amount=Decimal('100000'),
            payment_date=date.today(),
        )
        assert pay.method == LicensePayment.Method.TRANSFER

    def test_metodo_cash(self):
        c = make_company('900200004')
        lic = make_license(c)
        pay = make_payment(lic, method='cash')
        assert pay.method == LicensePayment.Method.CASH

    def test_metodo_card(self):
        c = make_company('900200005')
        lic = make_license(c)
        pay = make_payment(lic, method='card')
        assert pay.method == LicensePayment.Method.CARD

    def test_metodos_disponibles(self):
        metodos = [m.value for m in LicensePayment.Method]
        assert 'transfer' in metodos
        assert 'cash' in metodos
        assert 'card' in metodos

    def test_reference_es_opcional(self):
        c = make_company('900200006')
        lic = make_license(c)
        pay = make_payment(lic)
        assert pay.reference == ''

    def test_notes_es_opcional(self):
        c = make_company('900200007')
        lic = make_license(c)
        pay = make_payment(lic)
        assert pay.notes == ''

    def test_reference_con_valor(self):
        c = make_company('900200008')
        lic = make_license(c)
        pay = LicensePayment.objects.create(
            license=lic,
            amount=Decimal('100000'),
            payment_date=date.today(),
            reference='TRX-2026-001',
        )
        assert pay.reference == 'TRX-2026-001'

    def test_created_at_se_genera(self):
        c = make_company('900200009')
        lic = make_license(c)
        pay = make_payment(lic)
        assert pay.created_at is not None

    def test_payment_date_se_guarda(self):
        c = make_company('900200010')
        lic = make_license(c)
        today = date.today()
        pay = LicensePayment.objects.create(
            license=lic, amount=Decimal('50000'), payment_date=today,
        )
        assert pay.payment_date == today

    def test_ordering_por_fecha_desc(self):
        c = make_company('900200011')
        lic = make_license(c)
        p1 = LicensePayment.objects.create(
            license=lic, amount=Decimal('100'), payment_date=date.today() - timedelta(days=5)
        )
        p2 = LicensePayment.objects.create(
            license=lic, amount=Decimal('200'), payment_date=date.today()
        )
        pagos = list(LicensePayment.objects.filter(license=lic))
        assert pagos[0].id == p2.id   # más reciente primero
        assert pagos[1].id == p1.id

    def test_str_incluye_empresa_monto_y_fecha(self):
        c = make_company('900200012')
        lic = make_license(c)
        pay = make_payment(lic, amount='250000')
        s = str(pay)
        assert c.name in s
        assert '250000' in s

    def test_multiples_pagos_por_licencia(self):
        c = make_company('900200013')
        lic = make_license(c)
        make_payment(lic, amount='100000')
        make_payment(lic, amount='200000')
        assert LicensePayment.objects.filter(license=lic).count() == 2
