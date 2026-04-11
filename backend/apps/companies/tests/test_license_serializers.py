"""
SaiSuite — Tests: Companies Serializers
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from apps.companies.models import Company, CompanyLicense, LicensePayment
from apps.companies.serializers import (
    CompanyLicenseSerializer,
    CompanyLicenseWriteSerializer,
    LicensePaymentSerializer,
    CompanyCreateSerializer,
    CompanyUpdateSerializer,
    CompanyListSerializer,
    CompanyDetailSerializer,
)


def make_company(nit='900300001'):
    return Company.objects.create(name='Ser Test Co', nit=nit)


def make_license(company, status='active', days_ahead=30):
    return CompanyLicense.objects.create(
        company=company,
        status=status,
        starts_at=date.today() - timedelta(days=1),
        expires_at=date.today() + timedelta(days=days_ahead),
        max_users=10,
    )


# ── CompanyLicenseSerializer ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestCompanyLicenseSerializer:

    def test_serializa_todos_los_campos(self):
        c = make_company()
        lic = make_license(c)
        data = CompanyLicenseSerializer(lic).data
        expected_fields = {
            'id', 'company', 'company_name', 'company_nit',
            'status', 'renewal_type',
            'period', 'period_display',
            'starts_at', 'expires_at', 'max_users', 'concurrent_users',
            'modules_included', 'messages_used',
            'ai_tokens_quota', 'ai_tokens_used',
            'last_reset_date', 'notes',
            'days_until_expiry', 'is_expired', 'is_active_and_valid',
            'created_by', 'created_by_email', 'pending_renewal',
            'payments', 'history',
            'created_at', 'updated_at',
        }
        assert expected_fields == set(data.keys())

    def test_company_name_correcto(self):
        c = make_company('900300002')
        lic = make_license(c)
        data = CompanyLicenseSerializer(lic).data
        assert data['company_name'] == c.name

    def test_days_until_expiry_en_serializer(self):
        c = make_company('900300003')
        lic = make_license(c, days_ahead=20)
        data = CompanyLicenseSerializer(lic).data
        # Colombia TZ may differ from UTC by up to 1 day
        assert data['days_until_expiry'] in [19, 20, 21]

    def test_is_expired_false_cuando_vigente(self):
        c = make_company('900300004')
        lic = make_license(c, days_ahead=10)
        data = CompanyLicenseSerializer(lic).data
        assert data['is_expired'] is False

    def test_is_expired_true_cuando_vencida(self):
        c = make_company('900300005')
        lic = CompanyLicense.objects.create(
            company=c, status='expired',
            starts_at=date.today() - timedelta(days=60),
            expires_at=date.today() - timedelta(days=3),  # 3 days ago, safe in any TZ
        )
        data = CompanyLicenseSerializer(lic).data
        assert data['is_expired'] is True

    def test_payments_es_lista_vacia_sin_pagos(self):
        c = make_company('900300006')
        lic = make_license(c)
        data = CompanyLicenseSerializer(lic).data
        assert data['payments'] == []

    def test_payments_nested_con_pagos(self):
        c = make_company('900300007')
        lic = make_license(c)
        LicensePayment.objects.create(
            license=lic, amount=Decimal('500000'),
            payment_date=date.today(), method='transfer',
        )
        data = CompanyLicenseSerializer(lic).data
        assert len(data['payments']) == 1
        assert Decimal(data['payments'][0]['amount']) == Decimal('500000.00')

    def test_dias_negativos_si_expirada(self):
        c = make_company('900300008')
        lic = CompanyLicense.objects.create(
            company=c, status='expired',
            starts_at=date.today() - timedelta(days=60),
            expires_at=date.today() - timedelta(days=10),
        )
        data = CompanyLicenseSerializer(lic).data
        # Colombia TZ may differ from UTC by up to 1 day
        assert data['days_until_expiry'] <= -9


# ── LicensePaymentSerializer ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestLicensePaymentSerializer:

    def test_serializa_campos_correctos(self):
        c = make_company('900300020')
        lic = make_license(c)
        pay = LicensePayment.objects.create(
            license=lic, amount=Decimal('300000'),
            payment_date=date.today(), method='card',
            reference='TRX-001',
        )
        data = LicensePaymentSerializer(pay).data
        assert set(data.keys()) == {'id', 'amount', 'payment_date', 'method', 'reference', 'notes', 'created_at'}
        assert data['method'] == 'card'
        assert data['reference'] == 'TRX-001'

    def test_id_es_read_only(self):
        ser = LicensePaymentSerializer(data={
            'amount': '100000', 'payment_date': str(date.today()),
            'method': 'cash',
        })
        assert ser.is_valid()
        assert 'id' not in ser.validated_data

    def test_datos_validos_pasa_validacion(self):
        ser = LicensePaymentSerializer(data={
            'amount': '250000.00',
            'payment_date': str(date.today()),
            'method': 'transfer',
        })
        assert ser.is_valid(), ser.errors


# ── CompanyLicenseWriteSerializer ─────────────────────────────────────────────

@pytest.mark.django_db
class TestCompanyLicenseWriteSerializer:

    def test_datos_validos_pasa_validacion(self):
        c = make_company('900300030')
        ser = CompanyLicenseWriteSerializer(data={
            'company': str(c.id),
            'status': 'active',
            'starts_at': str(date.today() - timedelta(days=1)),
            'expires_at': str(date.today() + timedelta(days=30)),
            'max_users': 5,
        })
        assert ser.is_valid(), ser.errors

    def test_starts_at_requerida(self):
        ser = CompanyLicenseWriteSerializer(data={
            'status': 'active',
            'expires_at': str(date.today() + timedelta(days=30)),
        })
        assert not ser.is_valid()
        assert 'starts_at' in ser.errors


# ── CompanyCreateSerializer ───────────────────────────────────────────────────

class TestCompanyCreateSerializer:

    def test_datos_validos_pasa(self):
        ser = CompanyCreateSerializer(data={
            'name': 'Nueva Empresa',
            'nit': '900400001',
        })
        assert ser.is_valid(), ser.errors

    def test_nombre_vacio_falla(self):
        ser = CompanyCreateSerializer(data={'name': '   ', 'nit': '111'})
        assert not ser.is_valid()
        assert 'name' in ser.errors

    def test_nit_vacio_falla(self):
        ser = CompanyCreateSerializer(data={'name': 'Co', 'nit': '   '})
        assert not ser.is_valid()
        assert 'nit' in ser.errors


# ── CompanyUpdateSerializer ───────────────────────────────────────────────────

@pytest.mark.django_db
class TestCompanyUpdateSerializer:

    def test_nit_es_read_only(self):
        c = make_company('900300040')
        ser = CompanyUpdateSerializer(c, data={'name': 'Nuevo Nombre', 'nit': '000000'}, partial=True)
        assert ser.is_valid()
        # nit no está en validated_data al ser read_only
        assert 'nit' not in ser.validated_data

    def test_nombre_vacio_falla(self):
        c = make_company('900300041')
        ser = CompanyUpdateSerializer(c, data={'name': '   '}, partial=True)
        assert not ser.is_valid()
        assert 'name' in ser.errors
