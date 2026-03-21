"""
SaiSuite — Tests: PasswordReset views + UserListCreate + UserDetail
"""
import pytest
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.companies.models import Company
from apps.users.models import User, UserCompany


def make_company(nit='900000001', name='Test Co'):
    return Company.objects.create(name=name, nit=nit)


def make_user(company, email='u@test.com', password='Pass1234!', role='company_admin'):
    return User.objects.create_user(
        email=email, password=password,
        company=company, role=role, is_active=True,
    )


def auth_client(user):
    client = APIClient()
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return client


# ── Password Reset Request ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPasswordResetRequestView:

    def test_email_existente_retorna_200(self):
        company = make_company()
        user = make_user(company)
        client = APIClient()
        url = reverse('password-reset-request')
        res = client.post(url, {'email': user.email}, format='json')
        assert res.status_code == 200
        assert 'detail' in res.data

    def test_email_inexistente_retorna_200_igualmente(self):
        """No revelar si el email existe — respuesta idéntica."""
        client = APIClient()
        url = reverse('password-reset-request')
        res = client.post(url, {'email': 'noexiste@xyz.com'}, format='json')
        assert res.status_code == 200
        assert 'detail' in res.data

    def test_sin_email_retorna_400(self):
        client = APIClient()
        url = reverse('password-reset-request')
        res = client.post(url, {}, format='json')
        assert res.status_code == 400


# ── Password Reset Confirm ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPasswordResetConfirmView:

    def test_reset_token_valido_retorna_200(self):
        company = make_company('900000002')
        user = make_user(company, email='conf@test.com')
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        client = APIClient()
        url = reverse('password-reset-confirm')
        res = client.post(url, {'uid': uid, 'token': token, 'password': 'NuevoPass123!'}, format='json')
        assert res.status_code == 200
        user.refresh_from_db()
        assert user.check_password('NuevoPass123!')

    def test_reset_token_invalido_retorna_400(self):
        company = make_company('900000003')
        user = make_user(company, email='badtok@test.com')
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        client = APIClient()
        url = reverse('password-reset-confirm')
        res = client.post(url, {'uid': uid, 'token': 'token-invalido', 'password': 'NuevoPass123!'}, format='json')
        assert res.status_code == 400

    def test_reset_uid_invalido_retorna_400(self):
        client = APIClient()
        url = reverse('password-reset-confirm')
        res = client.post(url, {'uid': 'uid-basura', 'token': 'tok', 'password': 'NuevoPass123!'}, format='json')
        assert res.status_code == 400

    def test_reset_campos_faltantes_retorna_400(self):
        client = APIClient()
        url = reverse('password-reset-confirm')
        res = client.post(url, {'uid': 'abc'}, format='json')
        assert res.status_code == 400


# ── UserListCreate ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestUserListCreateView:

    def test_listar_usuarios_empresa(self):
        company = make_company('900000010')
        admin = make_user(company)
        make_user(company, email='otro@test.com', role='viewer')
        client = auth_client(admin)
        url = reverse('user-list-create')
        res = client.get(url)
        assert res.status_code == 200
        # La vista usa paginación estándar: {count, next, previous, results}
        results = res.data.get('results', res.data)
        assert len(results) == 2

    def test_crear_usuario_en_empresa(self):
        company = make_company('900000011')
        admin = make_user(company)
        client = auth_client(admin)
        url = reverse('user-list-create')
        data = {'email': 'new@test.com', 'password': 'Pass1234!', 'role': 'viewer'}
        res = client.post(url, data, format='json')
        assert res.status_code == 201
        assert User.objects.filter(email='new@test.com').exists()

    def test_viewer_no_puede_crear_usuario(self):
        company = make_company('900000012')
        viewer = make_user(company, email='v@test.com', role='viewer')
        client = auth_client(viewer)
        url = reverse('user-list-create')
        res = client.post(url, {'email': 'x@test.com', 'password': 'P1234!'}, format='json')
        assert res.status_code == 403

    def test_no_autenticado_retorna_401(self):
        client = APIClient()
        url = reverse('user-list-create')
        res = client.get(url)
        assert res.status_code == 401


# ── UserDetail ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestUserDetailView:

    def test_obtener_usuario_detalle(self):
        company = make_company('900000020')
        admin = make_user(company)
        otro = make_user(company, email='det@test.com', role='viewer')
        client = auth_client(admin)
        url = reverse('user-detail', args=[otro.id])
        res = client.get(url)
        assert res.status_code == 200
        assert res.data['email'] == otro.email

    def test_actualizar_usuario(self):
        company = make_company('900000021')
        admin = make_user(company)
        otro = make_user(company, email='upd2@test.com', role='viewer')
        client = auth_client(admin)
        url = reverse('user-detail', args=[otro.id])
        res = client.patch(url, {'first_name': 'Actualizado'}, format='json')
        assert res.status_code == 200
        otro.refresh_from_db()
        assert otro.first_name == 'Actualizado'


# ── SwitchCompany ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestSwitchCompanyView:

    def test_switch_exitoso(self):
        c1 = make_company('900000030')
        c2 = make_company('900000031')
        user = make_user(c1)
        UserCompany.objects.create(user=user, company=c2, role='viewer', is_active=True)
        client = auth_client(user)
        url = reverse('auth-switch-company')
        res = client.post(url, {'company_id': str(c2.id)}, format='json')
        assert res.status_code == 200

    def test_switch_empresa_sin_acceso_retorna_400(self):
        c1 = make_company('900000032')
        c2 = make_company('900000033')
        user = make_user(c1)
        client = auth_client(user)
        url = reverse('auth-switch-company')
        res = client.post(url, {'company_id': str(c2.id)}, format='json')
        assert res.status_code == 400
