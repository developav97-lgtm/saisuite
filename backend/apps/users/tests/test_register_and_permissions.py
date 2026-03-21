"""
SaiSuite — Tests: RegisterView, UserMeCompaniesView, HasModuleAccess, UserService.register
"""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework_simplejwt.tokens import RefreshToken

from apps.companies.models import Company, CompanyModule
from apps.users.models import User, UserCompany
from apps.users.permissions import HasModuleAccess
from apps.users.services import UserService


def make_company(nit='900001001', name='Co'):
    return Company.objects.create(name=name, nit=nit)


def make_user(company, email='u@t.com', password='Pass1234!', role='company_admin',
              is_superadmin=False):
    u = User.objects.create_user(
        email=email, password=password,
        company=company, role=role, is_active=True,
    )
    u.is_superadmin = is_superadmin
    u.is_staff = is_superadmin
    u.save()
    return u


def auth_client(user):
    client = APIClient()
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return client


# ── UserService.register ──────────────────────────────────────────────────────

@pytest.mark.django_db
class TestUserServiceRegister:

    def test_register_crea_empresa_y_usuario(self):
        data = {
            'company_name': 'Nueva Empresa S.A.S.',
            'company_nit':  '123456789',
            'company_plan': 'starter',
            'email':        'admin@nueva.com',
            'password':     'Secure1234!',
            'first_name':   'Admin',
            'last_name':    'Test',
        }
        company, user = UserService.register(data)
        assert company.name == 'Nueva Empresa S.A.S.'
        assert user.email == 'admin@nueva.com'
        assert user.role == User.Role.COMPANY_ADMIN

    def test_register_crea_user_company(self):
        data = {
            'company_name': 'Empresa UC',
            'company_nit':  '987654321',
            'company_plan': 'professional',
            'email':        'uc@empresa.com',
            'password':     'Secure1234!',
            'first_name':   'Test',
            'last_name':    'UC',
        }
        company, user = UserService.register(data)
        assert UserCompany.objects.filter(user=user, company=company).exists()

    def test_register_activa_modulo_proyectos(self):
        data = {
            'company_name': 'Empresa Mod',
            'company_nit':  '111222333',
            'company_plan': 'starter',
            'email':        'mod@empresa.com',
            'password':     'Secure1234!',
            'first_name':   'Mod',
            'last_name':    'Test',
        }
        company, _ = UserService.register(data)
        assert CompanyModule.objects.filter(company=company, module='proyectos', is_active=True).exists()

    def test_register_email_duplicado_lanza_error(self):
        from rest_framework.exceptions import ValidationError
        c = make_company('444555666')
        make_user(c, email='dup2@empresa.com')
        data = {
            'company_name': 'Empresa Dup',
            'company_nit':  '444555667',
            'company_plan': 'starter',
            'email':        'dup2@empresa.com',
            'password':     'Secure1234!',
            'first_name':   'X',
            'last_name':    'X',
        }
        with pytest.raises(ValidationError, match='email'):
            UserService.register(data)


# ── UserMeCompaniesView ───────────────────────────────────────────────────────

@pytest.mark.django_db
class TestUserMeCompaniesView:

    def test_retorna_empresas_del_usuario(self):
        c1 = make_company('900002001')
        c2 = make_company('900002002')
        user = make_user(c1)
        UserCompany.objects.create(user=user, company=c1, role='company_admin', is_active=True)
        UserCompany.objects.create(user=user, company=c2, role='viewer', is_active=True)
        client = auth_client(user)
        url = reverse('user-me-companies')
        res = client.get(url)
        assert res.status_code == 200
        assert len(res.data) == 2

    def test_fallback_a_company_fk_sin_user_company(self):
        """Si no hay UserCompany, retorna empresa del FK del usuario."""
        c = make_company('900002003')
        user = make_user(c)
        client = auth_client(user)
        url = reverse('user-me-companies')
        res = client.get(url)
        assert res.status_code == 200
        assert len(res.data) >= 1

    def test_sin_empresa_retorna_lista_vacia(self):
        """Usuario sin company y sin UserCompany → []."""
        user = User.objects.create_user(email='noco2@t.com', password='Pass1234!')
        client = auth_client(user)
        url = reverse('user-me-companies')
        res = client.get(url)
        assert res.status_code == 200
        assert res.data == []


# ── HasModuleAccess permission ────────────────────────────────────────────────

@pytest.mark.django_db
class TestHasModuleAccess:

    def _make_request(self, user):
        factory = APIRequestFactory()
        req = factory.get('/')
        req.user = user
        return req

    def test_sin_modulo_requerido_pasa(self):
        c = make_company('900003001')
        user = make_user(c)

        class FakeView:
            required_module = None

        perm = HasModuleAccess()
        req = self._make_request(user)
        assert perm.has_permission(req, FakeView()) is True

    def test_con_modulo_activo_pasa(self):
        c = make_company('900003002')
        CompanyModule.objects.create(company=c, module='proyectos', is_active=True)
        user = make_user(c)

        class FakeView:
            required_module = 'proyectos'

        perm = HasModuleAccess()
        req = self._make_request(user)
        assert perm.has_permission(req, FakeView()) is True

    def test_sin_modulo_activo_deniega(self):
        c = make_company('900003003')
        user = make_user(c)

        class FakeView:
            required_module = 'ventas'

        perm = HasModuleAccess()
        req = self._make_request(user)
        assert perm.has_permission(req, FakeView()) is False

    def test_usuario_sin_company_deniega(self):
        user = User.objects.create_user(email='noco3@t.com', password='Pass1234!')

        class FakeView:
            required_module = 'proyectos'

        perm = HasModuleAccess()
        req = self._make_request(user)
        assert perm.has_permission(req, FakeView()) is False

    def test_usuario_no_autenticado_deniega(self):
        from django.contrib.auth.models import AnonymousUser

        class FakeView:
            required_module = 'proyectos'

        perm = HasModuleAccess()
        factory = APIRequestFactory()
        req = factory.get('/')
        req.user = AnonymousUser()
        assert perm.has_permission(req, FakeView()) is False
