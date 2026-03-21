"""
SaiSuite — Tests: User model + UserManager
"""
import pytest
from django.db import IntegrityError
from apps.users.models import User, UserCompany
from apps.companies.models import Company


def make_company(nit='900000001'):
    return Company.objects.create(name='Empresa Test', nit=nit)


@pytest.mark.django_db
class TestUserManager:

    def test_create_user_requiere_email(self):
        with pytest.raises(ValueError, match='email'):
            User.objects.create_user(email='', password='pass123')

    def test_create_user_normaliza_email(self):
        """Django normaliza solo el dominio (RFC 5321), no la parte local."""
        company = make_company()
        user = User.objects.create_user(
            email='UPPER@EXAMPLE.COM', password='pass123', company=company
        )
        # normalize_email baja el dominio, la parte local queda igual
        assert user.email == 'UPPER@example.com'

    def test_create_superuser_sets_flags(self):
        user = User.objects.create_superuser(email='su@test.com', password='pass123')
        assert user.is_staff is True
        assert user.is_superuser is True

    def test_password_hasheado(self):
        company = make_company('900000009')
        user = User.objects.create_user(
            email='hash@test.com', password='mipassword', company=company
        )
        assert user.password != 'mipassword'
        assert user.check_password('mipassword') is True


@pytest.mark.django_db
class TestUserModel:

    @pytest.fixture
    def company(self):
        return make_company()

    def test_crear_usuario_minimo(self, company):
        user = User.objects.create_user(
            email='test@example.com', password='pass123', company=company
        )
        assert user.id is not None
        assert user.email == 'test@example.com'

    def test_is_active_default_true(self, company):
        user = User.objects.create_user(
            email='active@test.com', password='pass123', company=company
        )
        assert user.is_active is True

    def test_role_default_viewer(self, company):
        user = User.objects.create_user(
            email='viewer@test.com', password='pass123', company=company
        )
        assert user.role == User.Role.VIEWER

    def test_full_name_con_nombres(self, company):
        user = User.objects.create_user(
            email='fn@test.com', password='pass123',
            first_name='Juan', last_name='Pérez', company=company
        )
        assert user.full_name == 'Juan Pérez'

    def test_full_name_sin_nombres_retorna_email(self, company):
        user = User.objects.create_user(
            email='nofullname@test.com', password='pass123', company=company
        )
        assert user.full_name == 'nofullname@test.com'

    def test_full_name_solo_first_name(self, company):
        user = User.objects.create_user(
            email='first@test.com', password='pass123',
            first_name='Ana', company=company
        )
        assert user.full_name == 'Ana'

    def test_str_retorna_email(self, company):
        user = User.objects.create_user(
            email='str@test.com', password='pass123', company=company
        )
        assert str(user) == 'str@test.com'

    def test_email_unico(self, company):
        User.objects.create_user(email='dup@test.com', password='pass123', company=company)
        with pytest.raises(IntegrityError):
            User.objects.create_user(email='dup@test.com', password='pass456', company=company)

    def test_company_fk(self, company):
        user = User.objects.create_user(
            email='fk@test.com', password='pass123', company=company
        )
        assert user.company_id == company.id

    def test_usuario_sin_company(self):
        """Superadmins de ValMen pueden no tener empresa."""
        user = User.objects.create_user(email='noco@test.com', password='pass123')
        assert user.company is None

    def test_roles_disponibles(self):
        roles = [r.value for r in User.Role]
        assert 'company_admin' in roles
        assert 'viewer' in roles
        assert 'valmen_admin' in roles


@pytest.mark.django_db
class TestUserCompanyModel:

    @pytest.fixture
    def company(self):
        return make_company()

    @pytest.fixture
    def user(self, company):
        return User.objects.create_user(
            email='uc@test.com', password='pass123', company=company
        )

    def test_crear_user_company(self, user, company):
        uc = UserCompany.objects.create(user=user, company=company, role='viewer')
        assert uc.id is not None
        assert uc.is_active is True

    def test_is_active_default_true(self, user, company):
        uc = UserCompany.objects.create(user=user, company=company)
        assert uc.is_active is True

    def test_role_default_viewer(self, user, company):
        uc = UserCompany.objects.create(user=user, company=company)
        assert uc.role == User.Role.VIEWER

    def test_unique_together_user_company(self, user, company):
        UserCompany.objects.create(user=user, company=company)
        with pytest.raises(IntegrityError):
            UserCompany.objects.create(user=user, company=company)

    def test_usuario_multiples_empresas(self, user):
        company2 = make_company('800000002')
        uc1 = UserCompany.objects.create(user=user, company=user.company, role='company_admin')
        uc2 = UserCompany.objects.create(user=user, company=company2, role='viewer')
        assert uc1.id != uc2.id
        assert user.user_companies.count() == 2

    def test_str_incluye_email_company_rol(self, user, company):
        uc = UserCompany.objects.create(user=user, company=company, role='viewer')
        s = str(uc)
        assert user.email in s
        assert company.name in s
        assert 'viewer' in s

    def test_modules_access_default_lista_vacia(self, user, company):
        uc = UserCompany.objects.create(user=user, company=company)
        assert uc.modules_access == []

    def test_modules_access_con_valores(self, user, company):
        uc = UserCompany.objects.create(
            user=user, company=company, modules_access=['proyectos', 'ventas']
        )
        assert 'proyectos' in uc.modules_access
