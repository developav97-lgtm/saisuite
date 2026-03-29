"""
SaiSuite — Users Views
Las views SOLO orquestan: reciben request → llaman service → retornan response.
"""
import logging
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from apps.companies.serializers import CompanyDetailSerializer
from apps.companies.permissions import IsCompanyAdmin

from .models import UserCompany
from .serializers import (
    LoginSerializer,
    LogoutSerializer,
    UserMeSerializer,
    RegisterSerializer,
    UserCreateSerializer,
    UserListSerializer,
    UserUpdateSerializer,
    UserCompanySummarySerializer,
    SwitchCompanySerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)
from .services import AuthService, UserService

logger = logging.getLogger(__name__)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = AuthService.login(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
        )
        return Response(data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthService.logout(serializer.validated_data['refresh'])
        return Response(status=status.HTTP_200_OK)


class RefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)  # mismos campos: refresh
        serializer.is_valid(raise_exception=True)
        data = AuthService.refresh(serializer.validated_data['refresh'])
        return Response(data, status=status.HTTP_200_OK)


class MeView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class   = UserMeSerializer

    def get_object(self):
        return self.request.user


# ---------------------------------------------------------------------------
# Registro de empresa + primer usuario admin
# ---------------------------------------------------------------------------

class RegisterView(APIView):
    """POST /api/v1/auth/register/ — crea empresa y primer usuario admin. Solo superadmins."""

    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        from apps.companies.permissions import IsSuperAdmin
        return [IsSuperAdmin()]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company, user = UserService.register(serializer.validated_data)

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'access':  str(refresh.access_token),
                'refresh': str(refresh),
                'user':    UserMeSerializer(user).data,
                'company': CompanyDetailSerializer(company).data,
            },
            status=status.HTTP_201_CREATED,
        )


# ---------------------------------------------------------------------------
# Listado y creación de usuarios dentro de una empresa
# ---------------------------------------------------------------------------

class UserListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/auth/users/ — lista usuarios de la empresa del usuario autenticado.
    POST /api/v1/auth/users/ — crea un usuario adicional en la empresa.
    """

    permission_classes = [IsAuthenticated, IsCompanyAdmin]

    def get_queryset(self):
        params = self.request.query_params
        search    = params.get('search', '').strip()
        role      = params.get('role', '').strip()
        is_active_raw = params.get('is_active', None)
        is_active = None
        if is_active_raw == 'true':
            is_active = True
        elif is_active_raw == 'false':
            is_active = False
        return UserService.list_users(
            self.request.user.company,
            search=search,
            role=role,
            is_active=is_active,
        )

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserListSerializer

    def perform_create(self, serializer):
        UserService.create_user(self.request.user.company, serializer.validated_data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = UserService.create_user(request.user.company, serializer.validated_data)
        out = UserListSerializer(user)
        return Response(out.data, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Detalle y actualización de un usuario de la empresa
# ---------------------------------------------------------------------------

class UserDetailView(APIView):
    """
    GET   /api/v1/auth/users/<pk>/ — obtiene un usuario de la empresa.
    PATCH /api/v1/auth/users/<pk>/ — actualiza campos permitidos.
    """

    permission_classes = [IsAuthenticated, IsCompanyAdmin]

    def get(self, request, pk):
        user = UserService.get_user(request.user.company, str(pk))
        return Response(UserListSerializer(user).data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        serializer = UserUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = UserService.update_user(request.user.company, str(pk), serializer.validated_data)
        return Response(UserListSerializer(user).data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Empresas del usuario autenticado
# ---------------------------------------------------------------------------

class UserMeCompaniesView(APIView):
    """GET /api/v1/auth/me/companies/ — todas las empresas activas del usuario."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_companies = (
            UserCompany.objects
            .filter(user=request.user, is_active=True)
            .select_related('company')
        )

        if user_companies.exists():
            data = UserCompanySummarySerializer(user_companies, many=True).data
        else:
            # Fallback: si no hay UserCompany, usar la empresa del FK
            company = getattr(request.user, 'company', None)
            if company:
                data = [
                    {
                        'id':   str(company.id),
                        'name': company.name,
                        'nit':  company.nit,
                        'plan': company.plan,
                        'role': request.user.role,
                    }
                ]
            else:
                data = []

        return Response(data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Cambio de empresa activa
# ---------------------------------------------------------------------------

class SwitchCompanyView(APIView):
    """POST /api/v1/auth/switch-company/ — cambia la empresa activa del usuario."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SwitchCompanySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = UserService.switch_company(
            request.user,
            str(serializer.validated_data['company_id']),
        )
        return Response(UserMeSerializer(user).data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Recuperación de contraseña
# ---------------------------------------------------------------------------

class UserMencionesView(APIView):
    """
    GET /api/v1/auth/users/menciones/?q=juan
    Devuelve usuarios de la empresa para autocompletado de @menciones.
    Accesible a cualquier usuario autenticado (no solo admins).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = getattr(request.user, 'company', None)
        if not company:
            return Response([])
        q = request.query_params.get('q', '').strip()
        from django.contrib.auth import get_user_model
        User = get_user_model()
        qs = User.objects.filter(company=company, is_active=True).exclude(id=request.user.id)
        if q:
            from django.db.models import Q
            qs = qs.filter(
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q) |
                Q(email__icontains=q)
            )
        data = [
            {'id': str(u.id), 'full_name': u.full_name, 'email': u.email}
            for u in qs[:10]
        ]
        return Response(data)


class PasswordResetRequestView(APIView):
    """POST /api/v1/auth/password-reset/ — solicita recuperación de contraseña."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        UserService.request_password_reset(serializer.validated_data['email'])
        # Siempre responde igual para no revelar si el email existe
        return Response(
            {'detail': 'Si el email existe, recibirás un enlace para restablecer tu contraseña.'},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    """POST /api/v1/auth/password-reset/confirm/ — confirma el reset con uid + token."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        UserService.confirm_password_reset(
            uid_b64=serializer.validated_data['uid'],
            token=serializer.validated_data['token'],
            new_password=serializer.validated_data['password'],
        )
        return Response({'detail': 'Contraseña restablecida correctamente.'}, status=status.HTTP_200_OK)
