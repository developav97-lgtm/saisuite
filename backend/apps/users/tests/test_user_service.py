"""
SaiSuite — Tests: UserService + AuthService
Cobertura objetivo: cubrir services.py en su totalidad.
"""
import pytest
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.companies.models import Company
from apps.users.models import User, UserCompany
from apps.users.services import AuthService, UserService


def make_company(nit='900000001', name='Test Co'):
    return Company.objects.create(name=name, nit=nit)


def make_user(company, email='u@test.com', password='Pass1234!', role='viewer', active=True):
    return User.objects.create_user(
        email=email, password=password,
        first_name='Test', last_name='User',
        company=company, role=role, is_active=active,
    )


# ── AuthService ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAuthServiceLogin:

    def test_login_exitoso_retorna_tokens_y_usuario(self):
        company = make_company()
        user = make_user(company)
        result = AuthService.login(user.email, 'Pass1234!')
        assert 'access' in result
        assert 'refresh' in result
        assert result['user']['email'] == user.email

    def test_login_password_incorrecto_lanza_excepcion(self):
        company = make_company('900000002')
        user = make_user(company, email='wrong@test.com')
        with pytest.raises(AuthenticationFailed):
            AuthService.login(user.email, 'WrongPassword!')

    def test_login_usuario_inactivo_lanza_excepcion(self):
        company = make_company('900000003')
        user = make_user(company, email='inactive@test.com', active=False)
        with pytest.raises(AuthenticationFailed):
            AuthService.login(user.email, 'Pass1234!')

    def test_login_email_inexistente_lanza_excepcion(self):
        with pytest.raises(AuthenticationFailed):
            AuthService.login('noexiste@test.com', 'Pass1234!')


@pytest.mark.django_db
class TestAuthServiceLogout:

    def test_logout_invalida_refresh_token(self):
        company = make_company('900000010')
        user = make_user(company, email='logout@test.com')
        refresh = RefreshToken.for_user(user)
        # No debe lanzar excepción
        AuthService.logout(str(refresh))

    def test_logout_token_invalido_lanza_validation_error(self):
        with pytest.raises(ValidationError):
            AuthService.logout('token.invalido.aqui')


@pytest.mark.django_db
class TestAuthServiceRefresh:

    def test_refresh_exitoso_retorna_nuevos_tokens(self):
        company = make_company('900000011')
        user = make_user(company, email='refresh@test.com')
        refresh = RefreshToken.for_user(user)
        result = AuthService.refresh(str(refresh))
        assert 'access' in result
        assert 'refresh' in result

    def test_refresh_token_invalido_lanza_excepcion(self):
        with pytest.raises(AuthenticationFailed):
            AuthService.refresh('invalido.token.aqui')


# ── UserService.create_user ───────────────────────────────────────────────────

@pytest.mark.django_db
class TestUserServiceCreateUser:

    def test_crear_usuario_en_empresa(self):
        company = make_company('900000020')
        data = {
            'email': 'nuevo@test.com', 'password': 'Pass1234!',
            'first_name': 'Nuevo', 'last_name': 'Usuario', 'role': 'viewer',
        }
        user = UserService.create_user(company, data)
        assert user.id is not None
        assert user.email == 'nuevo@test.com'
        assert user.company_id == company.id

    def test_crear_usuario_crea_user_company(self):
        company = make_company('900000021')
        data = {'email': 'uc@test.com', 'password': 'Pass1234!'}
        user = UserService.create_user(company, data)
        assert UserCompany.objects.filter(user=user, company=company).exists()

    def test_crear_usuario_email_duplicado_lanza_error(self):
        company = make_company('900000022')
        make_user(company, email='dup@test.com')
        data = {'email': 'dup@test.com', 'password': 'Pass1234!'}
        with pytest.raises(ValidationError, match='email'):
            UserService.create_user(company, data)

    def test_crear_usuario_role_default_viewer(self):
        company = make_company('900000023')
        data = {'email': 'defrol@test.com', 'password': 'Pass1234!'}
        user = UserService.create_user(company, data)
        assert user.role == User.Role.VIEWER


# ── UserService.list_users ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestUserServiceListUsers:

    def test_lista_usuarios_de_empresa(self):
        company = make_company('900000030')
        make_user(company, email='a@test.com')
        make_user(company, email='b@test.com')
        qs = UserService.list_users(company)
        assert qs.count() == 2

    def test_no_incluye_usuarios_de_otra_empresa(self):
        c1 = make_company('900000031')
        c2 = make_company('900000032')
        make_user(c1, email='c1@test.com')
        make_user(c2, email='c2@test.com')
        assert UserService.list_users(c1).count() == 1
        assert UserService.list_users(c2).count() == 1


# ── UserService.get_user ──────────────────────────────────────────────────────

@pytest.mark.django_db
class TestUserServiceGetUser:

    def test_obtener_usuario_existente(self):
        company = make_company('900000040')
        user = make_user(company, email='get@test.com')
        result = UserService.get_user(company, str(user.id))
        assert result.id == user.id

    def test_usuario_de_otra_empresa_lanza_error(self):
        c1 = make_company('900000041')
        c2 = make_company('900000042')
        user = make_user(c1, email='other@test.com')
        with pytest.raises(ValidationError):
            UserService.get_user(c2, str(user.id))

    def test_uuid_inexistente_lanza_error(self):
        company = make_company('900000043')
        import uuid
        with pytest.raises(ValidationError):
            UserService.get_user(company, str(uuid.uuid4()))


# ── UserService.update_user ───────────────────────────────────────────────────

@pytest.mark.django_db
class TestUserServiceUpdateUser:

    def test_actualizar_nombre(self):
        company = make_company('900000050')
        user = make_user(company, email='upd@test.com')
        updated = UserService.update_user(company, str(user.id), {'first_name': 'Nuevo'})
        assert updated.first_name == 'Nuevo'

    def test_actualizar_role(self):
        company = make_company('900000051')
        user = make_user(company, email='role@test.com')
        updated = UserService.update_user(company, str(user.id), {'role': 'company_admin'})
        assert updated.role == 'company_admin'

    def test_actualizar_modules_access(self):
        company = make_company('900000052')
        user = make_user(company, email='mods@test.com')
        UserCompany.objects.create(user=user, company=company)
        UserService.update_user(company, str(user.id), {'modules_access': ['proyectos']})
        uc = UserCompany.objects.get(user=user, company=company)
        assert 'proyectos' in uc.modules_access

    def test_actualizar_is_active(self):
        company = make_company('900000053')
        user = make_user(company, email='deact@test.com')
        updated = UserService.update_user(company, str(user.id), {'is_active': False})
        assert updated.is_active is False

    def test_sin_cambios_no_falla(self):
        company = make_company('900000054')
        user = make_user(company, email='noop@test.com')
        updated = UserService.update_user(company, str(user.id), {})
        assert updated.id == user.id


# ── UserService.switch_company ────────────────────────────────────────────────

@pytest.mark.django_db
class TestUserServiceSwitchCompany:

    def test_switch_company_valido(self):
        c1 = make_company('900000060')
        c2 = make_company('900000061')
        user = make_user(c1, email='sw@test.com')
        UserCompany.objects.create(user=user, company=c2, role='viewer', is_active=True)
        updated = UserService.switch_company(user, str(c2.id))
        assert updated.company_id == c2.id

    def test_switch_company_sin_acceso_lanza_error(self):
        c1 = make_company('900000062')
        c2 = make_company('900000063')
        user = make_user(c1, email='swbad@test.com')
        with pytest.raises(ValidationError, match='acceso'):
            UserService.switch_company(user, str(c2.id))


# ── UserService.request_password_reset ───────────────────────────────────────

@pytest.mark.django_db
class TestUserServicePasswordReset:

    def test_request_reset_email_existente_no_lanza_error(self):
        company = make_company('900000070')
        user = make_user(company, email='reset@test.com')
        # No debe lanzar — respuesta silenciosa
        UserService.request_password_reset(user.email)

    def test_request_reset_email_inexistente_no_lanza_error(self):
        # No debe lanzar aunque el email no exista
        UserService.request_password_reset('noexiste@test.com')

    def test_confirm_reset_token_valido(self):
        company = make_company('900000071')
        user = make_user(company, email='confirm@test.com')
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        UserService.confirm_password_reset(uid, token, 'NuevaPass123!')
        user.refresh_from_db()
        assert user.check_password('NuevaPass123!')

    def test_confirm_reset_token_invalido_lanza_error(self):
        company = make_company('900000072')
        user = make_user(company, email='badtoken@test.com')
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        with pytest.raises(ValidationError, match='expirado|inválido'):
            UserService.confirm_password_reset(uid, 'token-invalido', 'NuevaPass123!')

    def test_confirm_reset_uid_invalido_lanza_error(self):
        with pytest.raises(ValidationError, match='inválido'):
            UserService.confirm_password_reset('uid-basura-xxx', 'token', 'NuevaPass123!')
