"""
SaiSuite — Users Services
Toda la lógica de negocio relacionada con autenticación.
"""
import logging
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from .models import User
from .serializers import UserMeSerializer

logger = logging.getLogger(__name__)


class AuthService:

    @staticmethod
    def login(email: str, password: str) -> dict:
        user: User | None = authenticate(request=None, username=email, password=password)
        if user is None or not user.is_active:
            logger.info("login_failed", extra={"email": email})
            raise AuthenticationFailed("Credenciales inválidas.")

        refresh = RefreshToken.for_user(user)
        logger.info("login_success", extra={"user_id": str(user.id)})
        return {
            "access":  str(refresh.access_token),
            "refresh": str(refresh),
            "user":    UserMeSerializer(user).data,
        }

    @staticmethod
    def logout(refresh_token_str: str) -> None:
        try:
            RefreshToken(refresh_token_str).blacklist()
            logger.info("logout_success")
        except TokenError:
            raise ValidationError("Token inválido o expirado.")

    @staticmethod
    def refresh(refresh_token_str: str) -> dict:
        try:
            old_refresh = RefreshToken(refresh_token_str)
            user_id = old_refresh["user_id"]
            user = User.objects.get(id=user_id)
            old_refresh.blacklist()
            new_refresh = RefreshToken.for_user(user)
        except (TokenError, User.DoesNotExist):
            raise AuthenticationFailed("Token inválido.")
        return {
            "access":  str(new_refresh.access_token),
            "refresh": str(new_refresh),
        }
