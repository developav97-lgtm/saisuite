"""
SaiSuite — Tests: Companies views (licencias y empresas)
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.companies.models import Company, CompanyLicense, LicensePayment
from apps.users.models import User


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_company(nit='900700001', name='View Test Co'):
    return Company.objects.create(name=name, nit=nit)


def make_license(company, status='active', days_ahead=30):
    return CompanyLicense.objects.create(
        company=company,
        plan='starter',
        status=status,
        starts_at=date.today() - timedelta(days=1),
        expires_at=date.today() + timedelta(days=days_ahead),
        max_users=5,
    )


def make_superadmin(email='super@test.com'):
    u = User.objects.create_user(email=email, password='Pass1234!', is_active=True)
    u.is_superadmin = True
    u.is_staff = True
    u.save()
    return u


def make_regular_user(company, email='user@test.com'):
    return User.objects.create_user(
        email=email, password='Pass1234!',
        company=company, role='company_admin', is_active=True,
    )


def auth_client(user):
    client = APIClient()
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return client


# ── LicenseListCreateView ─────────────────────────────────────────────────────

@pytest.mark.django_db
class TestLicenseListCreateView:

    def test_listar_licencias_superadmin(self):
        c = make_company()
        make_license(c)
        admin = make_superadmin()
        client = auth_client(admin)
        url = reverse('license-list-create')
        res = client.get(url)
        assert res.status_code == 200
        assert len(res.data) >= 1

    def test_listar_licencias_usuario_normal_403(self):
        c = make_company('900700002')
        user = make_regular_user(c, 'norm@test.com')
        client = auth_client(user)
        url = reverse('license-list-create')
        res = client.get(url)
        assert res.status_code == 403

    def test_crear_licencia_superadmin(self):
        c = make_company('900700003')
        admin = make_superadmin('super2@test.com')
        client = auth_client(admin)
        url = reverse('license-list-create')
        data = {
            'company': str(c.id),
            'plan': 'starter',
            'status': 'active',
            'starts_at': str(date.today() - timedelta(days=1)),
            'expires_at': str(date.today() + timedelta(days=30)),
            'max_users': 5,
        }
        res = client.post(url, data, format='json')
        assert res.status_code == 201
        assert CompanyLicense.objects.filter(company=c).exists()

    def test_crear_licencia_usuario_normal_403(self):
        c = make_company('900700004')
        user = make_regular_user(c, 'norm2@test.com')
        client = auth_client(user)
        url = reverse('license-list-create')
        data = {
            'company': str(c.id),
            'plan': 'starter',
            'status': 'active',
            'starts_at': str(date.today()),
            'expires_at': str(date.today() + timedelta(days=30)),
        }
        res = client.post(url, data, format='json')
        assert res.status_code == 403

    def test_no_autenticado_retorna_401(self):
        client = APIClient()
        url = reverse('license-list-create')
        res = client.get(url)
        assert res.status_code == 401

    def test_crear_duplicado_retorna_400(self):
        c = make_company('900700005')
        make_license(c)
        admin = make_superadmin('super3@test.com')
        client = auth_client(admin)
        url = reverse('license-list-create')
        data = {
            'company': str(c.id),
            'plan': 'professional',
            'status': 'active',
            'starts_at': str(date.today()),
            'expires_at': str(date.today() + timedelta(days=30)),
        }
        res = client.post(url, data, format='json')
        assert res.status_code == 400


# ── LicenseDetailView ─────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestLicenseDetailView:

    def test_obtener_licencia_por_id(self):
        c = make_company('900700010')
        lic = make_license(c)
        admin = make_superadmin('super10@test.com')
        client = auth_client(admin)
        url = reverse('license-detail', args=[lic.id])
        res = client.get(url)
        assert res.status_code == 200
        assert str(res.data['id']) == str(lic.id)

    def test_patch_actualiza_status(self):
        c = make_company('900700011')
        lic = make_license(c)
        admin = make_superadmin('super11@test.com')
        client = auth_client(admin)
        url = reverse('license-detail', args=[lic.id])
        res = client.patch(url, {'status': 'suspended'}, format='json')
        assert res.status_code == 200
        lic.refresh_from_db()
        assert lic.status == 'suspended'

    def test_patch_actualiza_max_users(self):
        c = make_company('900700012')
        lic = make_license(c)
        admin = make_superadmin('super12@test.com')
        client = auth_client(admin)
        url = reverse('license-detail', args=[lic.id])
        res = client.patch(url, {'max_users': 50}, format='json')
        assert res.status_code == 200
        lic.refresh_from_db()
        assert lic.max_users == 50

    def test_usuario_normal_no_puede_ver_403(self):
        c = make_company('900700013')
        lic = make_license(c)
        user = make_regular_user(c, 'norm3@test.com')
        client = auth_client(user)
        url = reverse('license-detail', args=[lic.id])
        res = client.get(url)
        assert res.status_code == 403

    def test_licencia_inexistente_retorna_404(self):
        import uuid
        admin = make_superadmin('super13@test.com')
        client = auth_client(admin)
        url = reverse('license-detail', args=[uuid.uuid4()])
        res = client.get(url)
        assert res.status_code == 404


# ── LicenseMeView ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestLicenseMeView:

    def test_retorna_licencia_de_empresa_del_usuario(self):
        c = make_company('900700020')
        lic = make_license(c)
        user = make_regular_user(c, 'me@test.com')
        client = auth_client(user)
        url = reverse('license-me')
        res = client.get(url)
        assert res.status_code == 200
        assert str(res.data['id']) == str(lic.id)

    def test_usuario_sin_empresa_retorna_404(self):
        user = User.objects.create_user(email='noco@test.com', password='Pass1234!', is_active=True)
        client = auth_client(user)
        url = reverse('license-me')
        res = client.get(url)
        assert res.status_code == 404

    def test_empresa_sin_licencia_retorna_404(self):
        c = make_company('900700021')
        user = make_regular_user(c, 'nolic@test.com')
        client = auth_client(user)
        url = reverse('license-me')
        res = client.get(url)
        assert res.status_code == 404

    def test_no_autenticado_retorna_401(self):
        client = APIClient()
        url = reverse('license-me')
        res = client.get(url)
        assert res.status_code == 401


# ── LicensePaymentCreateView ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestLicensePaymentCreateView:

    def test_crear_pago_superadmin(self):
        c = make_company('900700030')
        lic = make_license(c)
        admin = make_superadmin('super30@test.com')
        client = auth_client(admin)
        url = reverse('license-payment-create', args=[lic.id])
        data = {
            'amount': '500000.00',
            'payment_date': str(date.today()),
            'method': 'transfer',
        }
        res = client.post(url, data, format='json')
        assert res.status_code == 201
        assert LicensePayment.objects.filter(license=lic).count() == 1

    def test_crear_pago_usuario_normal_403(self):
        c = make_company('900700031')
        lic = make_license(c)
        user = make_regular_user(c, 'norm4@test.com')
        client = auth_client(user)
        url = reverse('license-payment-create', args=[lic.id])
        data = {'amount': '100000', 'payment_date': str(date.today()), 'method': 'cash'}
        res = client.post(url, data, format='json')
        assert res.status_code == 403

    def test_licencia_inexistente_retorna_404(self):
        import uuid
        admin = make_superadmin('super31@test.com')
        client = auth_client(admin)
        url = reverse('license-payment-create', args=[uuid.uuid4()])
        res = client.post(url, {'amount': '100', 'payment_date': str(date.today())}, format='json')
        assert res.status_code == 404


# ── CompanyViewSet ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCompanyViewSet:

    def test_listar_empresas_superadmin(self):
        make_company('900700040')
        admin = make_superadmin('super40@test.com')
        client = auth_client(admin)
        url = reverse('company-list')
        res = client.get(url)
        assert res.status_code == 200

    def test_crear_empresa_superadmin(self):
        admin = make_superadmin('super41@test.com')
        client = auth_client(admin)
        url = reverse('company-list')
        data = {'name': 'Nueva Empresa', 'nit': '999000001', 'plan': 'starter'}
        res = client.post(url, data, format='json')
        assert res.status_code == 201
        assert Company.objects.filter(nit='999000001').exists()

    def test_delete_retorna_405(self):
        c = make_company('900700042')
        admin = make_superadmin('super42@test.com')
        client = auth_client(admin)
        url = reverse('company-detail', args=[c.id])
        res = client.delete(url)
        assert res.status_code == 405

    def test_usuario_normal_no_puede_listar_403(self):
        c = make_company('900700043')
        user = make_regular_user(c, 'norm5@test.com')
        client = auth_client(user)
        url = reverse('company-list')
        res = client.get(url)
        assert res.status_code == 403


# ── LicenseMeView — scenarios de negocio ─────────────────────────────────────

@pytest.mark.django_db
class TestLicenseBusinessScenarios:
    """Escenarios críticos de control de acceso."""

    def test_licencia_activa_y_vigente_retorna_datos(self):
        c = make_company('900700050')
        make_license(c, status='active', days_ahead=30)
        user = make_regular_user(c, 'biz1@test.com')
        client = auth_client(user)
        res = client.get(reverse('license-me'))
        assert res.status_code == 200
        assert res.data['is_expired'] is False

    def test_licencia_expirada_is_expired_true(self):
        c = make_company('900700051')
        CompanyLicense.objects.create(
            company=c, plan='starter', status='expired',
            starts_at=date.today() - timedelta(days=60),
            expires_at=date.today() - timedelta(days=1),
        )
        user = make_regular_user(c, 'biz2@test.com')
        client = auth_client(user)
        res = client.get(reverse('license-me'))
        assert res.status_code == 200
        assert res.data['is_expired'] is True

    def test_days_until_expiry_en_respuesta(self):
        c = make_company('900700052')
        make_license(c, status='active', days_ahead=15)
        user = make_regular_user(c, 'biz3@test.com')
        client = auth_client(user)
        res = client.get(reverse('license-me'))
        assert res.status_code == 200
        assert res.data['days_until_expiry'] == 15
