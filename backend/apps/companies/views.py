"""
SaiSuite — Companies: Views
Las views SOLO orquestan: reciben request → llaman service → retornan response.
"""
import logging
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Company
from .permissions import IsSuperAdmin
from .serializers import (
    CompanyListSerializer,
    CompanyDetailSerializer,
    CompanyCreateSerializer,
    CompanyUpdateSerializer,
    CompanyModuleSerializer,
    CompanyLicenseSerializer,
    CompanyLicenseWriteSerializer,
    LicensePaymentSerializer,
)
from .services import CompanyService, LicenseService

logger = logging.getLogger(__name__)


class CompanyViewSet(viewsets.ModelViewSet):
    """
    CRUD de empresas. Solo superadmins pueden ver y gestionar todas las empresas.
    DELETE está deshabilitado — las empresas se desactivan, no se eliminan.
    """

    permission_classes = [IsSuperAdmin]

    def get_queryset(self):
        return CompanyService.list_companies()

    def get_serializer_class(self):
        if self.action == 'list':
            return CompanyListSerializer
        if self.action == 'create':
            return CompanyCreateSerializer
        if self.action in ('update', 'partial_update'):
            return CompanyUpdateSerializer
        return CompanyDetailSerializer

    def perform_create(self, serializer):
        company = CompanyService.create_company(serializer.validated_data)
        # Reemplazar la respuesta con los datos del objeto creado
        self._created_company = company

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        out = CompanyDetailSerializer(self._created_company)
        return Response(out.data, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        CompanyService.update_company(serializer.instance, serializer.validated_data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated = CompanyService.update_company(instance, serializer.validated_data)
        out = CompanyDetailSerializer(updated)
        return Response(out.data)

    def destroy(self, request, *args, **kwargs):
        return Response(
            {'detail': 'Las empresas no se pueden eliminar. Use la acción de desactivar.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )


class CompanyMeView(RetrieveAPIView):
    """GET /api/v1/companies/me/ — empresa del usuario autenticado."""

    permission_classes = [IsAuthenticated]
    serializer_class = CompanyDetailSerializer

    def get_object(self):
        company = getattr(self.request.user, 'company', None)
        if company is None:
            from rest_framework.exceptions import NotFound
            raise NotFound('El usuario no tiene una empresa asignada.')
        return company


class ModuleActivateView(APIView):
    """POST /api/v1/companies/{pk}/modules/activate/ — activa un módulo en la empresa."""

    permission_classes = [IsSuperAdmin]

    def post(self, request, pk):
        company = CompanyService.get_company(str(pk))
        module = request.data.get('module')
        if not module:
            return Response(
                {'module': 'Este campo es requerido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        obj = CompanyService.activate_module(company, module)
        return Response(CompanyModuleSerializer(obj).data, status=status.HTTP_200_OK)


class ModuleDeactivateView(APIView):
    """POST /api/v1/companies/{pk}/modules/deactivate/ — desactiva un módulo en la empresa."""

    permission_classes = [IsSuperAdmin]

    def post(self, request, pk):
        company = CompanyService.get_company(str(pk))
        module = request.data.get('module')
        if not module:
            return Response(
                {'module': 'Este campo es requerido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        CompanyService.deactivate_module(company, module)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Licencias ────────────────────────────────────────────────────────────────

class LicenseListCreateView(APIView):
    """
    GET  /api/v1/companies/licenses/        — lista todas las licencias (superadmin).
    POST /api/v1/companies/licenses/        — crea licencia para una empresa.
    """

    permission_classes = [IsSuperAdmin]

    def get(self, request):
        licenses = LicenseService.list_licenses()
        return Response(CompanyLicenseSerializer(licenses, many=True).data)

    def post(self, request):
        serializer = CompanyLicenseWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        license_obj = LicenseService.create_license(serializer.validated_data)
        return Response(CompanyLicenseSerializer(license_obj).data, status=status.HTTP_201_CREATED)


class LicenseDetailView(APIView):
    """
    GET   /api/v1/companies/licenses/{pk}/  — detalle de licencia.
    PATCH /api/v1/companies/licenses/{pk}/  — actualiza licencia.
    """

    permission_classes = [IsSuperAdmin]

    def get(self, request, pk):
        license_obj = LicenseService.get_license_by_id(str(pk))
        return Response(CompanyLicenseSerializer(license_obj).data)

    def patch(self, request, pk):
        license_obj = LicenseService.get_license_by_id(str(pk))
        serializer = CompanyLicenseWriteSerializer(license_obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = LicenseService.update_license(license_obj, serializer.validated_data)
        return Response(CompanyLicenseSerializer(updated).data)


class LicenseMeView(APIView):
    """GET /api/v1/companies/licenses/me/ — licencia de la empresa del usuario autenticado."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = getattr(request.user, 'company', None)
        if not company:
            return Response({'detail': 'Sin empresa asignada.'}, status=status.HTTP_404_NOT_FOUND)
        license_obj = LicenseService.get_license(company)
        return Response(CompanyLicenseSerializer(license_obj).data)


class LicensePaymentCreateView(APIView):
    """POST /api/v1/companies/licenses/{pk}/payments/ — registra un pago."""

    permission_classes = [IsSuperAdmin]

    def post(self, request, pk):
        license_obj = LicenseService.get_license_by_id(str(pk))
        serializer = LicensePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = LicenseService.add_payment(license_obj, serializer.validated_data)
        return Response(LicensePaymentSerializer(payment).data, status=status.HTTP_201_CREATED)
