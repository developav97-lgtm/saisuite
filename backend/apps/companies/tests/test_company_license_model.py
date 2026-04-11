"""
SaiSuite — Tests: CompanyLicense model
"""
import pytest
from datetime import date, timedelta
from apps.companies.models import Company, CompanyLicense


def make_company(nit='900100001'):
    return Company.objects.create(name='Lic Test Co', nit=nit)


def make_license(company, status='active', days_ahead=30, days_back=0):
    today = date.today()
    return CompanyLicense.objects.create(
        company=company,
        status=status,
        starts_at=today - timedelta(days=days_back or 1),
        expires_at=today + timedelta(days=days_ahead),
        max_users=5,
    )


@pytest.mark.django_db
class TestCompanyLicenseModel:

    def test_crear_licencia_con_company_fk(self):
        c = make_company()
        lic = make_license(c)
        assert lic.id is not None
        assert lic.company_id == c.id

    def test_estado_por_defecto_trial(self):
        c = make_company('900100002')
        lic = CompanyLicense.objects.create(
            company=c,
            starts_at=date.today(), expires_at=date.today() + timedelta(days=30),
        )
        assert lic.status == CompanyLicense.Status.TRIAL

    def test_estados_disponibles(self):
        statuses = [s.value for s in CompanyLicense.Status]
        assert 'trial' in statuses
        assert 'active' in statuses
        assert 'expired' in statuses
        assert 'suspended' in statuses

    def test_max_users_por_defecto_5(self):
        c = make_company('900100003')
        lic = CompanyLicense.objects.create(
            company=c,
            starts_at=date.today(), expires_at=date.today() + timedelta(days=30),
        )
        assert lic.max_users == 5

    def test_one_to_one_company(self):
        c = make_company('900100006')
        make_license(c)
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            CompanyLicense.objects.create(
                company=c, status='active',
                starts_at=date.today(), expires_at=date.today() + timedelta(days=30),
            )

    def test_is_expired_false_si_vigente(self):
        c = make_company('900100007')
        lic = make_license(c, days_ahead=10)
        assert lic.is_expired is False

    def test_is_expired_true_si_vencida(self):
        c = make_company('900100008')
        lic = CompanyLicense.objects.create(
            company=c, status='expired',
            starts_at=date.today() - timedelta(days=60),
            expires_at=date.today() - timedelta(days=3),  # safe in any TZ
        )
        assert lic.is_expired is True

    def test_days_until_expiry_positivo_si_vigente(self):
        c = make_company('900100009')
        lic = make_license(c, days_ahead=15)
        # Colombia TZ may differ from UTC by up to 1 day
        assert lic.days_until_expiry in [14, 15, 16]

    def test_days_until_expiry_negativo_si_expirada(self):
        c = make_company('900100010')
        lic = CompanyLicense.objects.create(
            company=c, status='expired',
            starts_at=date.today() - timedelta(days=60),
            expires_at=date.today() - timedelta(days=10),
        )
        # Colombia TZ may differ from UTC by up to 1 day
        assert lic.days_until_expiry <= -9

    def test_days_until_expiry_cero_hoy(self):
        c = make_company('900100011')
        lic = CompanyLicense.objects.create(
            company=c, status='active',
            starts_at=date.today() - timedelta(days=1),
            expires_at=date.today(),
        )
        # Colombia TZ may differ by ±1 day
        assert lic.days_until_expiry in [-1, 0, 1]

    def test_notes_es_opcional(self):
        c = make_company('900100012')
        lic = make_license(c)
        assert lic.notes == ''

    def test_str_incluye_empresa_estado_y_fecha(self):
        c = make_company('900100013')
        lic = make_license(c, status='active')
        s = str(lic)
        assert c.name in s
        assert 'Activa' in s

    def test_created_at_se_genera(self):
        c = make_company('900100014')
        lic = make_license(c)
        assert lic.created_at is not None

    def test_licencia_suspendida(self):
        c = make_company('900100015')
        lic = make_license(c, status='suspended')
        assert lic.status == CompanyLicense.Status.SUSPENDED

    def test_licencia_expirada_status(self):
        c = make_company('900100016')
        lic = make_license(c, status='expired')
        assert lic.status == CompanyLicense.Status.EXPIRED
