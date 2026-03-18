"""
SaiSuite — Users Views
Las views solo orquestan: reciben request → llaman service → retornan response.
"""
import logging
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .serializers import LoginSerializer, LogoutSerializer, UserMeSerializer
from .services import AuthService

logger = logging.getLogger(__name__)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = AuthService.login(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        return Response(data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthService.logout(serializer.validated_data["refresh"])
        return Response(status=status.HTTP_200_OK)


class RefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)  # mismos campos: refresh
        serializer.is_valid(raise_exception=True)
        data = AuthService.refresh(serializer.validated_data["refresh"])
        return Response(data, status=status.HTTP_200_OK)


class MeView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class   = UserMeSerializer

    def get_object(self):
        return self.request.user
