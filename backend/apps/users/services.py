"""
SaiSuite — Users Services
Toda la lógica de negocio relacionada con usuarios y autenticación.
Las views no contienen lógica de negocio.
"""
import logging
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.db import transaction
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from .models import User, UserCompany
from .serializers import UserMeSerializer

logger = logging.getLogger(__name__)


class AuthService:

    @staticmethod
    def login(email: str, password: str, ip_address: str | None = None, user_agent: str = '') -> dict:
        user: User | None = authenticate(request=None, username=email, password=password)
        if user is None or not user.is_active:
            logger.info('login_failed', extra={'email': email})
            raise AuthenticationFailed('Credenciales inválidas.')

        if not getattr(user, 'company_id', None) and not getattr(user, 'is_staff', False):
            logger.info('login_blocked_sin_company', extra={'user_id': str(user.id), 'email': email})
            raise AuthenticationFailed(
                'Tu usuario no está asociado a ninguna empresa. Contacta al administrador.'
            )

        # Verificar licencia y concurrencia (solo para usuarios normales)
        is_exempt = getattr(user, 'is_superadmin', False) or getattr(user, 'is_staff', False)
        company = getattr(user, 'effective_company', None)

        if not is_exempt and company:
            from apps.companies.services import LicenseService
            from apps.companies.models import CompanyLicense
            try:
                lic = CompanyLicense.objects.get(company=company)
                if not lic.is_active_and_valid:
                    logger.info('login_blocked_license', extra={'user_id': str(user.id), 'status': lic.status})
                    raise AuthenticationFailed(
                        'Tu empresa no tiene una licencia activa. Contacta a ventas@valmentech.com.'
                    )
                # Verificar concurrencia (excluir el usuario actual — tendrá nueva sesión)
                can_access, activos, permitidos = LicenseService.verify_concurrent_limit(
                    company, exclude_user=user
                )
                if not can_access:
                    logger.info('login_blocked_concurrent', extra={
                        'user_id': str(user.id), 'activos': activos, 'permitidos': permitidos
                    })
                    raise AuthenticationFailed(
                        f'Se alcanzó el límite de {permitidos} usuarios simultáneos. '
                        f'Contacta al administrador de tu empresa.'
                    )
            except CompanyLicense.DoesNotExist:
                logger.warning('login_no_license', extra={'user_id': str(user.id), 'company_id': str(company.id)})
                raise AuthenticationFailed(
                    'Tu empresa no tiene una licencia configurada. Contacta a ventas@valmentech.com.'
                )

        # Crear sesión (invalida la anterior del mismo usuario)
        from apps.companies.services import SessionService
        session = SessionService.create_session(user, ip_address=ip_address, user_agent=user_agent)

        # Generar JWT con session_id en el payload
        refresh = RefreshToken.for_user(user)
        refresh['session_id'] = str(session.session_id)
        refresh.access_token['session_id'] = str(session.session_id)

        logger.info('login_success', extra={'user_id': str(user.id), 'session_id': str(session.session_id)})
        return {
            'access':  str(refresh.access_token),
            'refresh': str(refresh),
            'user':    UserMeSerializer(user).data,
        }

    @staticmethod
    def logout(refresh_token_str: str, user=None) -> None:
        try:
            token = RefreshToken(refresh_token_str)
            # Invalidar la sesión asociada al token
            session_id = token.get('session_id')
            if session_id:
                from apps.companies.services import SessionService
                SessionService.invalidate_session(session_id)
            token.blacklist()
            logger.info('logout_success', extra={'user_id': str(user.id) if user else 'unknown'})
        except TokenError:
            raise ValidationError('Token inválido o expirado.')

    @staticmethod
    def refresh(refresh_token_str: str) -> dict:
        try:
            old_refresh = RefreshToken(refresh_token_str)
            user_id = old_refresh['user_id']
            user = User.objects.get(id=user_id)
            old_refresh.blacklist()
            new_refresh = RefreshToken.for_user(user)
        except (TokenError, User.DoesNotExist):
            raise AuthenticationFailed('Token inválido.')
        return {
            'access':  str(new_refresh.access_token),
            'refresh': str(new_refresh),
        }


class UserService:

    @staticmethod
    @transaction.atomic
    def register(data: dict) -> tuple:
        """
        Crea empresa + primer usuario admin en una transacción atómica.
        Retorna (company, user).

        Pasos:
        1. Crear Company via CompanyService
        2. Activar módulo 'proyectos' por defecto
        3. Crear User con role='company_admin', company=company
        4. Crear UserCompany con role='company_admin'
        5. Logging
        """
        from apps.companies.services import CompanyService

        # 1. Crear empresa
        company = CompanyService.create_company({
            'name': data['company_name'],
            'nit':  data['company_nit'],
        })

        # 2. Activar módulo proyectos por defecto
        CompanyService.activate_module(company, 'proyectos')

        # 3. Crear usuario admin
        if User.objects.filter(email=data['email']).exists():
            raise ValidationError({'email': 'Ya existe un usuario con este email.'})

        user = User.objects.create_user(
            email=data['email'],
            password=data['password'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            role=User.Role.COMPANY_ADMIN,
            company=company,
            is_active=True,
        )

        # 4. Crear UserCompany
        UserCompany.objects.create(
            user=user,
            company=company,
            role=User.Role.COMPANY_ADMIN,
            modules_access=['proyectos'],
            is_active=True,
        )

        logger.info(
            'user_registered',
            extra={
                'user_id':    str(user.id),
                'company_id': str(company.id),
                'email':      user.email,
            },
        )
        return company, user

    @staticmethod
    @transaction.atomic
    def create_user(company, data: dict) -> User:
        """
        Crea un usuario adicional en la empresa.

        Pasos:
        1. Validar email único
        2. Crear User con company=company
        3. Crear UserCompany
        4. Logging
        """
        email = data.get('email', '')
        if User.objects.filter(email=email).exists():
            raise ValidationError({'email': 'Ya existe un usuario con este email.'})

        # Validar límite de usuarios de la licencia
        from apps.companies.models import CompanyLicense
        try:
            lic = CompanyLicense.objects.get(company=company)
            current_count = User.objects.filter(company=company, is_active=True).count()
            if current_count >= lic.max_users:
                raise ValidationError({
                    'non_field_errors': [
                        f'Se alcanzó el límite de {lic.max_users} usuario(s) permitido(s) por la licencia.'
                    ]
                })
        except CompanyLicense.DoesNotExist:
            pass  # Sin licencia configurada, permitir creación

        user = User.objects.create_user(
            email=email,
            password=data['password'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            role=data.get('role', User.Role.VIEWER),
            company=company,
            is_active=True,
        )

        UserCompany.objects.create(
            user=user,
            company=company,
            role=data.get('role', User.Role.VIEWER),
            modules_access=data.get('modules_access', []),
            is_active=True,
        )

        logger.info(
            'user_created',
            extra={
                'user_id':    str(user.id),
                'company_id': str(company.id),
                'email':      user.email,
                'role':       user.role,
            },
        )
        return user

    @staticmethod
    def list_users(company, search: str = '', role: str = '', is_active=None):
        """
        Retorna usuarios de la empresa con filtros opcionales.
        - search: busca en email, first_name y last_name
        - role: filtra por rol exacto
        - is_active: True/False o None para todos
        """
        from django.db.models import Q
        qs = User.objects.filter(company=company, is_staff=False, is_superadmin=False)
        if search:
            qs = qs.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        if role:
            qs = qs.filter(role=role)
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        return qs.order_by('email')

    @staticmethod
    def get_user(company, user_id: str) -> User:
        """Obtiene un usuario de la empresa. Lanza ValidationError si no pertenece a ella."""
        try:
            return User.objects.get(id=user_id, company=company)
        except User.DoesNotExist:
            raise ValidationError('Usuario no encontrado en esta empresa.')

    @staticmethod
    @transaction.atomic
    def update_user(company, user_id: str, data: dict) -> User:
        """
        Actualiza campos permitidos de un usuario de la empresa.
        - Campos en User: first_name, last_name, role, is_active
        - modules_access: se actualiza en UserCompany
        """
        user = UserService.get_user(company, user_id)

        # Campos directos en User
        user_fields = {'first_name', 'last_name', 'role', 'is_active'}
        update_fields = []

        for field in user_fields:
            if field in data:
                setattr(user, field, data[field])
                update_fields.append(field)

        if update_fields:
            update_fields.append('updated_at')
            user.save(update_fields=update_fields)

        # modules_access vive en UserCompany
        if 'modules_access' in data:
            UserCompany.objects.filter(user=user, company=company).update(
                modules_access=data['modules_access']
            )

        # Asignación de rol granular
        if 'rol_granular_id' in data:
            from apps.users.models import Role
            rol_id = data['rol_granular_id']
            if rol_id is None:
                user.rol_granular = None
            else:
                try:
                    user.rol_granular = Role.objects.get(id=rol_id, empresa=company)
                except Role.DoesNotExist:
                    from rest_framework.exceptions import ValidationError as DRFValidationError
                    raise DRFValidationError({'rol_granular_id': 'Rol no encontrado en esta empresa.'})
            user.save(update_fields=['rol_granular', 'updated_at'])

        logger.info(
            'user_updated',
            extra={
                'user_id':    str(user.id),
                'company_id': str(company.id),
                'fields':     update_fields + (['modules_access'] if 'modules_access' in data else []),
            },
        )
        return user

    @staticmethod
    @transaction.atomic
    def create_internal_user(data: dict) -> 'User':
        """Crea un usuario interno ValMen Tech (superadmin o soporte), sin company."""
        email = data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError({'email': 'Ya existe un usuario con este email.'})

        user = User.objects.create_user(
            email=email,
            password=data['password'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            is_staff=data.get('is_staff', True),
            is_superadmin=data.get('is_superadmin', False),
            company=None,
            is_active=True,
        )
        logger.info('internal_user_created', extra={'user_id': str(user.id), 'email': user.email})
        return user

    @staticmethod
    def request_password_reset(email: str) -> None:
        """
        Genera token de reset y envía email.
        Siempre retorna sin error (no revela si el email existe).
        """
        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            return  # silencioso — no revelar si el email existe

        uid   = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:4200')
        reset_url = f'{frontend_url}/auth/reset-password?uid={uid}&token={token}'

        ctx = {
            'user_name': f' {user.first_name}' if user.first_name else '',
            'reset_url': reset_url,
        }
        try:
            send_mail(
                subject='[SaiSuite] Recuperación de contraseña',
                message=(
                    f'Hola{ctx["user_name"]},\n\n'
                    f'Recibimos una solicitud para restablecer tu contraseña.\n\n'
                    f'Haz clic en el siguiente enlace (válido por 1 hora):\n{reset_url}\n\n'
                    f'Si no solicitaste esto, ignora este mensaje.\n\n'
                    f'— SaiSuite\n'
                ),
                html_message=render_to_string('emails/password_reset.html', ctx),
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@saisuite.com'),
                recipient_list=[email],
                fail_silently=True,
            )
        except Exception:
            pass  # silencioso — nunca fallar por problemas de email
        logger.info('password_reset_requested', extra={'email': email})

    @staticmethod
    def confirm_password_reset(uid_b64: str, token: str, new_password: str) -> None:
        """Valida token y aplica la nueva contraseña."""
        try:
            uid  = force_str(urlsafe_base64_decode(uid_b64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise ValidationError('El enlace de recuperación es inválido.')

        if not default_token_generator.check_token(user, token):
            raise ValidationError('El enlace ha expirado o ya fue usado.')

        user.set_password(new_password)
        user.save(update_fields=['password'])
        logger.info('password_reset_confirmed', extra={'user_id': str(user.id)})

    @staticmethod
    @transaction.atomic
    def invite_company_admin(company, email: str) -> 'User':
        """
        Crea el usuario administrador de la empresa con is_active=False y
        envía un correo de invitación con link de activación (72h).
        """
        from django.utils import timezone as tz
        from apps.companies.models import Company  # evitar import circular

        if not isinstance(company, Company):
            company = Company.objects.get(pk=company)

        if User.objects.filter(email=email).exists():
            raise ValidationError({'email': 'Ya existe un usuario con este email.'})

        import secrets
        temp_password = secrets.token_urlsafe(16)

        user = User.objects.create_user(
            email=email,
            password=temp_password,
            role=User.Role.COMPANY_ADMIN,
            company=company,
            is_active=False,
            invited_at=tz.now(),
        )

        uid   = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        frontend_url  = getattr(settings, 'FRONTEND_URL', 'http://localhost:4200')
        activate_url  = f'{frontend_url}/auth/activar?uid={uid}&token={token}'

        ctx = {
            'company_name': company.name,
            'activate_url': activate_url,
        }
        try:
            send_mail(
                subject=f'[SaiSuite] Invitación para administrar {company.name}',
                message=(
                    f'Hola,\n\n'
                    f'Has sido invitado como administrador de {company.name} en SaiSuite.\n\n'
                    f'Haz clic en el siguiente enlace para activar tu cuenta y elegir tu contraseña '
                    f'(válido por 72 horas):\n\n{activate_url}\n\n'
                    f'Si recibiste este correo por error, puedes ignorarlo.\n\n'
                    f'— Equipo SaiSuite\n'
                ),
                html_message=render_to_string('emails/invitation.html', ctx),
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@saisuite.com'),
                recipient_list=[email],
                fail_silently=True,
            )
        except Exception:
            pass  # No fallar si hay problemas de correo

        logger.info(
            'company_admin_invited',
            extra={'email': email, 'company_id': str(company.id)},
        )
        return user

    @staticmethod
    def activate_account(uid_b64: str, token: str, new_password: str) -> None:
        """Activa la cuenta de un usuario invitado usando el uid y token del correo."""
        try:
            uid  = force_str(urlsafe_base64_decode(uid_b64))
            user = User.objects.get(pk=uid, is_active=False)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise ValidationError('El enlace de activación es inválido.')

        if not default_token_generator.check_token(user, token):
            raise ValidationError('El enlace ha expirado o ya fue usado.')

        user.set_password(new_password)
        user.is_active = True
        user.save(update_fields=['password', 'is_active', 'updated_at'])
        logger.info('account_activated', extra={'user_id': str(user.id)})

    @staticmethod
    @transaction.atomic
    def switch_company(user: User, company_id: str) -> User:
        """
        Cambia la empresa activa del usuario.
        Valida que el usuario tenga acceso a esa empresa via UserCompany.
        Actualiza user.company y user.role con el rol del UserCompany.
        """
        try:
            user_company = UserCompany.objects.select_related('company').get(
                user=user,
                company__id=company_id,
                is_active=True,
            )
        except UserCompany.DoesNotExist:
            raise ValidationError('No tienes acceso a esta empresa.')

        user.company = user_company.company
        user.role = user_company.role
        user.save(update_fields=['company', 'role', 'updated_at'])

        logger.info(
            'company_switched',
            extra={
                'user_id':    str(user.id),
                'company_id': company_id,
                'new_role':   user.role,
            },
        )
        return user
