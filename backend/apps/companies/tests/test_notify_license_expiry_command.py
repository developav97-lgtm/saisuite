"""
SaiSuite — Tests: notify_license_expiry management command
"""
import pytest
from datetime import date, timedelta
from unittest.mock import patch
from io import StringIO
from django.core.management import call_command

from apps.companies.models import Company, CompanyLicense
from apps.users.models import User


def make_company(nit='900800001', name='Cmd Test Co'):
    return Company.objects.create(name=name, nit=nit)


def make_license(company, days_ahead=5, status='active'):
    return CompanyLicense.objects.create(
        company=company,
        plan='starter',
        status=status,
        starts_at=date.today() - timedelta(days=1),
        expires_at=date.today() + timedelta(days=days_ahead),
    )


def make_user(company, email='admin@test.com'):
    return User.objects.create_user(
        email=email, password='Pass1234!',
        company=company, is_active=True,
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestNotifyLicenseExpiryCommand:

    def test_comando_ejecuta_sin_errores(self):
        stdout = StringIO()
        call_command('notify_license_expiry', stdout=stdout)
        # Sin errores = éxito

    def test_sin_licencias_expirando_mensaje_apropiado(self):
        stdout = StringIO()
        call_command('notify_license_expiry', '--days', '5', stdout=stdout)
        output = stdout.getvalue()
        assert 'No hay licencias' in output

    def test_detecta_licencias_proximas_por_defecto_5_dias(self):
        c = make_company()
        make_license(c, days_ahead=5)
        make_user(c)
        stdout = StringIO()
        with patch('apps.companies.management.commands.notify_license_expiry.send_mail') as mock_mail:
            call_command('notify_license_expiry', '--days', '5', stdout=stdout)
            assert mock_mail.called

    def test_detecta_licencias_con_argumento_days(self):
        c = make_company('900800002')
        make_license(c, days_ahead=7)
        make_user(c, 'admin2@test.com')
        stdout = StringIO()
        with patch('apps.companies.management.commands.notify_license_expiry.send_mail') as mock_mail:
            call_command('notify_license_expiry', '--days', '7', stdout=stdout)
            assert mock_mail.called

    def test_no_detecta_licencias_con_diferente_vencimiento(self):
        c = make_company('900800003')
        make_license(c, days_ahead=10)  # vence en 10 días
        make_user(c, 'admin3@test.com')
        stdout = StringIO()
        with patch('apps.companies.management.commands.notify_license_expiry.send_mail') as mock_mail:
            call_command('notify_license_expiry', '--days', '5', stdout=stdout)
            assert not mock_mail.called

    def test_dry_run_no_envia_emails(self):
        c = make_company('900800004')
        make_license(c, days_ahead=5)
        make_user(c, 'admin4@test.com')
        stdout = StringIO()
        with patch('apps.companies.management.commands.notify_license_expiry.send_mail') as mock_mail:
            call_command('notify_license_expiry', '--days', '5', '--dry-run', stdout=stdout)
            assert not mock_mail.called

    def test_dry_run_imprime_info(self):
        c = make_company('900800005')
        make_license(c, days_ahead=5)
        make_user(c, 'admin5@test.com')
        stdout = StringIO()
        with patch('django.core.mail.send_mail'):
            call_command('notify_license_expiry', '--days', '5', '--dry-run', stdout=stdout)
        output = stdout.getvalue()
        assert 'DRY-RUN' in output

    def test_empresa_sin_usuarios_con_email_se_omite(self):
        c = make_company('900800006')
        make_license(c, days_ahead=5)
        # No se crea ningún usuario con email
        stdout = StringIO()
        with patch('apps.companies.management.commands.notify_license_expiry.send_mail') as mock_mail:
            call_command('notify_license_expiry', '--days', '5', stdout=stdout)
            assert not mock_mail.called
        assert 'sin admins' in stdout.getvalue() or 'omitido' in stdout.getvalue()

    def test_no_notifica_licencias_suspendidas(self):
        c = make_company('900800007')
        make_license(c, days_ahead=5, status='suspended')
        make_user(c, 'admin7@test.com')
        stdout = StringIO()
        with patch('apps.companies.management.commands.notify_license_expiry.send_mail') as mock_mail:
            call_command('notify_license_expiry', '--days', '5', stdout=stdout)
            assert not mock_mail.called

    def test_no_notifica_licencias_expiradas(self):
        c = make_company('900800008')
        # status='expired' pero expires_at en 5 días (data inconsistente)
        CompanyLicense.objects.create(
            company=c, plan='starter', status='expired',
            starts_at=date.today() - timedelta(days=30),
            expires_at=date.today() + timedelta(days=5),
        )
        make_user(c, 'admin8@test.com')
        stdout = StringIO()
        with patch('apps.companies.management.commands.notify_license_expiry.send_mail') as mock_mail:
            call_command('notify_license_expiry', '--days', '5', stdout=stdout)
            assert not mock_mail.called

    def test_envia_email_con_subject_correcto(self):
        c = make_company('900800009')
        make_license(c, days_ahead=5)
        make_user(c, 'admin9@test.com')
        stdout = StringIO()
        with patch('apps.companies.management.commands.notify_license_expiry.send_mail') as mock_mail:
            call_command('notify_license_expiry', '--days', '5', stdout=stdout)
        call_args = mock_mail.call_args
        assert call_args is not None
        subject = call_args[1].get('subject') or call_args[0][0]
        assert '5 días' in subject
        assert c.name in subject

    def test_envia_email_al_usuario_activo_de_la_empresa(self):
        c = make_company('900800010')
        make_license(c, days_ahead=5)
        user = make_user(c, 'active@test.com')
        # Usuario inactivo — no debe recibir email
        u_inact = User.objects.create_user(
            email='inactive@test.com', password='Pass1234!',
            company=c, is_active=False,
        )
        stdout = StringIO()
        with patch('apps.companies.management.commands.notify_license_expiry.send_mail') as mock_mail:
            call_command('notify_license_expiry', '--days', '5', stdout=stdout)
        call_args = mock_mail.call_args
        recipients = call_args[1].get('recipient_list') or call_args[0][3]
        assert 'active@test.com' in recipients
        assert 'inactive@test.com' not in recipients

    def test_multiples_empresas_envia_multiples_emails(self):
        c1 = make_company('900800011')
        c2 = make_company('900800012')
        make_license(c1, days_ahead=5)
        make_license(c2, days_ahead=5)
        make_user(c1, 'u11@test.com')
        make_user(c2, 'u12@test.com')
        stdout = StringIO()
        with patch('apps.companies.management.commands.notify_license_expiry.send_mail') as mock_mail:
            call_command('notify_license_expiry', '--days', '5', stdout=stdout)
        assert mock_mail.call_count == 2
