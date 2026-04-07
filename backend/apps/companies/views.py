"""
SaiSuite — Companies: Views
Las views SOLO orquestan: reciben request → llaman service → retornan response.
"""
import logging
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from .models import Company, CompanyLicense, LicensePackage, LicensePackageItem, AgentToken
from .permissions import IsSuperAdmin
from .serializers import (
    CompanyListSerializer,
    CompanyDetailSerializer,
    CompanyCreateSerializer,
    CompanyUpdateSerializer,
    CompanyModuleSerializer,
    CompanyLicenseSerializer,
    CompanyLicenseSummarySerializer,
    CompanyLicenseWriteSerializer,
    LicensePaymentSerializer,
    LicenseHistorySerializer,
    LicenseRenewalSerializer,
    TenantCreateSerializer,
    TenantWithLicenseSerializer,
    LicensePackageSerializer,
    LicensePackageWriteSerializer,
    LicensePackageItemSerializer,
    MonthlyLicenseSnapshotSerializer,
    AIUsageSummarySerializer,
    AIUsagePerUserSerializer,
    AIUsageLogSerializer,
)
from .services import CompanyService, LicenseService, RenewalService, PackageService, AIUsageService

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
        company = getattr(self.request.user, 'effective_company', None)
        if company is None:
            from rest_framework.exceptions import NotFound
            raise NotFound('El usuario no tiene una empresa asignada.')
        return company


class CompanyMeLogoView(APIView):
    """PATCH /api/v1/companies/me/logo/ — sube o reemplaza el logo de la empresa del usuario."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def patch(self, request):
        company = getattr(request.user, 'effective_company', None)
        if company is None:
            from rest_framework.exceptions import NotFound
            raise NotFound('El usuario no tiene una empresa asignada.')
        if 'logo' not in request.FILES:
            return Response({'error': 'Se requiere el campo logo.'}, status=status.HTTP_400_BAD_REQUEST)
        company.logo = request.FILES['logo']
        company.save(update_fields=['logo', 'updated_at'])
        logger.info('logo_updated', extra={'company_id': str(company.id)})
        return Response(CompanyDetailSerializer(company, context={'request': request}).data)

    def delete(self, request):
        company = getattr(request.user, 'effective_company', None)
        if company is None:
            from rest_framework.exceptions import NotFound
            raise NotFound('El usuario no tiene una empresa asignada.')
        company.logo.delete(save=True)
        logger.info('logo_deleted', extra={'company_id': str(company.id)})
        return Response(status=status.HTTP_204_NO_CONTENT)


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
        company = getattr(request.user, 'effective_company', None)
        if not company:
            return Response({'detail': 'Sin empresa asignada.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            license_obj = LicenseService.get_license(company)
        except Exception:
            return Response({'detail': 'Sin licencia configurada.'}, status=status.HTTP_404_NOT_FOUND)
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


# ── Panel Superadmin — Tenants ────────────────────────────────────────────────

class AdminTenantListView(APIView):
    """
    GET  /api/v1/admin/tenants/ — lista todas las empresas con resumen de licencia.
    POST /api/v1/admin/tenants/ — crea empresa + licencia inicial.
    Solo superadmins.
    """

    permission_classes = [IsSuperAdmin]

    def get(self, request):
        companies = (
            Company.objects.all()
            .prefetch_related('license', 'modules')
            .order_by('name')
        )
        return Response(TenantWithLicenseSerializer(companies, many=True).data)

    def post(self, request):
        serializer = TenantCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        company = CompanyService.create_company({
            'name': d['name'],
            'nit':  d['nit'],
            'plan': d['plan'],
            'saiopen_enabled': d.get('saiopen_enabled', False),
        })

        license_data = {
            'company':          company,
            'plan':             d['plan'],
            'status':           d['license_status'],
            'starts_at':        d['license_starts_at'],
            'period':           d.get('license_period', 'trial'),
            'concurrent_users': d.get('concurrent_users', 1),
            'max_users':        d.get('max_users', 5),
            'modules_included': d.get('modules_included', []),
            'messages_quota':   d.get('messages_quota', 0),
            'ai_tokens_quota':  d.get('ai_tokens_quota', 0),
            'notes':            d.get('license_notes', ''),
        }
        # expires_at is optional override; if provided, use it; otherwise calculated from period
        if d.get('license_expires_at'):
            license_data['expires_at'] = d['license_expires_at']

        LicenseService.create_license_with_history(license_data, created_by=request.user)

        out = TenantWithLicenseSerializer(
            Company.objects.prefetch_related('license', 'modules').get(id=company.id)
        )
        return Response(out.data, status=status.HTTP_201_CREATED)


class AdminTenantDetailView(APIView):
    """
    GET   /api/v1/admin/tenants/{pk}/ — detalle de empresa con licencia completa.
    PATCH /api/v1/admin/tenants/{pk}/ — editar datos de la empresa.
    Solo superadmins.
    """

    permission_classes = [IsSuperAdmin]

    def get(self, request, pk):
        company = CompanyService.get_company(str(pk))
        return Response(TenantWithLicenseSerializer(company).data)

    def patch(self, request, pk):
        company = CompanyService.get_company(str(pk))
        serializer = CompanyUpdateSerializer(company, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = CompanyService.update_company(company, serializer.validated_data)
        return Response(TenantWithLicenseSerializer(updated).data)


class AdminTenantLicenseView(APIView):
    """
    GET  /api/v1/admin/tenants/{pk}/license/ — licencia completa (con historial).
    POST /api/v1/admin/tenants/{pk}/license/ — crea nueva licencia (si no existe aún).
    PATCH /api/v1/admin/tenants/{pk}/license/ — actualiza licencia (renovación/modificación).
    Solo superadmins.
    """

    permission_classes = [IsSuperAdmin]

    def get(self, request, pk):
        company = CompanyService.get_company(str(pk))
        license_obj = LicenseService.get_license(company)
        return Response(CompanyLicenseSerializer(license_obj).data)

    def post(self, request, pk):
        company = CompanyService.get_company(str(pk))
        serializer = CompanyLicenseWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        data['company'] = company
        license_obj = LicenseService.create_license_with_history(data, created_by=request.user)
        return Response(CompanyLicenseSerializer(license_obj).data, status=status.HTTP_201_CREATED)

    def patch(self, request, pk):
        company = CompanyService.get_company(str(pk))
        license_obj = LicenseService.get_license(company)
        serializer = CompanyLicenseWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = LicenseService.update_license_with_history(
            license_obj, serializer.validated_data, changed_by=request.user
        )
        return Response(CompanyLicenseSerializer(updated).data)


class AdminLicenseHistoryView(APIView):
    """
    GET /api/v1/admin/tenants/{pk}/license/history/ — historial de cambios de licencia.
    Solo superadmins.
    """

    permission_classes = [IsSuperAdmin]

    def get(self, request, pk):
        company = CompanyService.get_company(str(pk))
        license_obj = LicenseService.get_license(company)
        history = LicenseService.get_license_history(license_obj)
        return Response(LicenseHistorySerializer(history, many=True).data)


class AdminLicensePaymentView(APIView):
    """
    POST /api/v1/admin/tenants/{pk}/license/payments/ — registra un pago.
    Solo superadmins.
    """

    permission_classes = [IsSuperAdmin]

    def post(self, request, pk):
        company = CompanyService.get_company(str(pk))
        license_obj = LicenseService.get_license(company)
        serializer = LicensePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = LicenseService.add_payment(license_obj, serializer.validated_data)
        return Response(LicensePaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class AdminTenantActivateView(APIView):
    """
    POST /api/v1/admin/tenants/{pk}/activate/ — activa/desactiva empresa.
    Solo superadmins.
    """

    permission_classes = [IsSuperAdmin]

    def post(self, request, pk):
        company = CompanyService.get_company(str(pk))
        is_active = request.data.get('is_active', True)
        company.is_active = bool(is_active)
        company.save(update_fields=['is_active'])
        logger.info('company_activation_changed', extra={
            'company_id': str(company.id), 'is_active': company.is_active
        })
        return Response({'id': str(company.id), 'is_active': company.is_active})


class AdminLicenseRenewalView(APIView):
    """
    GET  /api/v1/admin/tenants/{pk}/license/renewal/ — obtiene renovación pendiente.
    POST /api/v1/admin/tenants/{pk}/license/renewal/ — crea renovación manual.
    """

    permission_classes = [IsSuperAdmin]

    def get(self, request, pk):
        company = CompanyService.get_company(str(pk))
        license_obj = LicenseService.get_license(company)
        renewal = RenewalService.get_pending_renewal(license_obj)
        if not renewal:
            return Response(None)
        return Response(LicenseRenewalSerializer(renewal).data)

    def post(self, request, pk):
        company = CompanyService.get_company(str(pk))
        license_obj = LicenseService.get_license(company)
        period = request.data.get('period')
        if not period or period not in CompanyLicense.PERIOD_DAYS:
            return Response(
                {'period': f'Período requerido. Opciones: {list(CompanyLicense.PERIOD_DAYS.keys())}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        renewal = RenewalService.create_renewal(license_obj, period, auto_generated=False)
        return Response(LicenseRenewalSerializer(renewal).data, status=status.HTTP_201_CREATED)


class AdminRenewalConfirmView(APIView):
    """
    POST /api/v1/admin/tenants/{pk}/license/renewal/confirm/
    Confirma el pago de la renovación pendiente.
    Punto de extensión para futura pasarela de pago.
    """

    permission_classes = [IsSuperAdmin]

    def post(self, request, pk):
        company = CompanyService.get_company(str(pk))
        license_obj = LicenseService.get_license(company)
        renewal = RenewalService.get_pending_renewal(license_obj)
        if not renewal or renewal.status != 'pending':
            return Response(
                {'detail': 'No hay renovación pendiente de confirmación.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        notes = request.data.get('notes', '')
        renewal = RenewalService.confirm_renewal(renewal, confirmed_by=request.user, notes=notes)
        return Response(LicenseRenewalSerializer(renewal).data)


class AdminRenewalCancelView(APIView):
    """
    POST /api/v1/admin/tenants/{pk}/license/renewal/cancel/
    Cancela la renovación pendiente o confirmada.
    """

    permission_classes = [IsSuperAdmin]

    def post(self, request, pk):
        company = CompanyService.get_company(str(pk))
        license_obj = LicenseService.get_license(company)
        renewal = RenewalService.get_pending_renewal(license_obj)
        if not renewal:
            return Response(
                {'detail': 'No hay renovación activa para cancelar.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        renewal = RenewalService.cancel_renewal(renewal, cancelled_by=request.user)
        return Response(LicenseRenewalSerializer(renewal).data)


# ── Paquetes de licencia (Admin) ────────────────────────────────────────────

class AdminPackageListView(APIView):
    """
    GET  /api/v1/admin/packages/ — catalogo de paquetes.
    POST /api/v1/admin/packages/ — crear paquete.
    """

    permission_classes = [IsSuperAdmin]

    def get(self, request):
        package_type = request.query_params.get('type')
        packages = PackageService.list_packages(package_type=package_type)
        return Response(LicensePackageSerializer(packages, many=True).data)

    def post(self, request):
        serializer = LicensePackageWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        package = PackageService.create_package(serializer.validated_data)
        return Response(LicensePackageSerializer(package).data, status=status.HTTP_201_CREATED)


class AdminPackageDetailView(APIView):
    """
    PATCH /api/v1/admin/packages/{pk}/ — editar paquete (nombre, precio, etc.).
    """

    permission_classes = [IsSuperAdmin]

    def get(self, request, pk):
        package = PackageService.get_package(str(pk))
        return Response(LicensePackageSerializer(package).data)

    def patch(self, request, pk):
        package = PackageService.get_package(str(pk))
        serializer = LicensePackageWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = PackageService.update_package(package, serializer.validated_data)
        return Response(LicensePackageSerializer(updated).data)


class AdminLicensePackagesView(APIView):
    """
    GET  /api/v1/admin/tenants/{pk}/license/packages/ — paquetes asignados.
    POST /api/v1/admin/tenants/{pk}/license/packages/ — agregar paquete a licencia.
    """

    permission_classes = [IsSuperAdmin]

    def get(self, request, pk):
        company = CompanyService.get_company(str(pk))
        license_obj = LicenseService.get_license(company)
        items = license_obj.package_items.select_related('package', 'added_by').all()
        return Response(LicensePackageItemSerializer(items, many=True).data)

    def post(self, request, pk):
        company = CompanyService.get_company(str(pk))
        license_obj = LicenseService.get_license(company)
        package_id = request.data.get('package_id')
        quantity = request.data.get('quantity', 1)
        if not package_id:
            return Response({'package_id': 'Requerido.'}, status=status.HTTP_400_BAD_REQUEST)
        package = PackageService.get_package(str(package_id))
        item = PackageService.add_package_to_license(
            license_obj, package, quantity=int(quantity), added_by=request.user,
        )
        return Response(LicensePackageItemSerializer(item).data, status=status.HTTP_201_CREATED)


class AdminLicensePackageRemoveView(APIView):
    """
    DELETE /api/v1/admin/tenants/{pk}/license/packages/{item_pk}/
    Quita un paquete de la licencia.
    """

    permission_classes = [IsSuperAdmin]

    def delete(self, request, pk, item_pk):
        try:
            item = LicensePackageItem.objects.select_related('license', 'package').get(
                id=item_pk, license__company_id=pk,
            )
        except LicensePackageItem.DoesNotExist:
            return Response({'detail': 'Paquete asignado no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        PackageService.remove_package_from_license(item, removed_by=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminLicenseSnapshotsView(APIView):
    """GET /api/v1/admin/tenants/{pk}/license/snapshots/ — snapshots mensuales."""

    permission_classes = [IsSuperAdmin]

    def get(self, request, pk):
        company = CompanyService.get_company(str(pk))
        license_obj = LicenseService.get_license(company)
        snapshots = license_obj.snapshots.all()
        return Response(MonthlyLicenseSnapshotSerializer(snapshots, many=True).data)


# ── Uso de IA ────────────────────────────────────────────────────────────────

class AIUsageMeView(APIView):
    """
    GET /api/v1/companies/licenses/me/ai-usage/ — resumen de uso IA de mi empresa.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = getattr(request.user, 'effective_company', None)
        if not company:
            return Response({'detail': 'Sin empresa asignada.'}, status=status.HTTP_404_NOT_FOUND)
        summary = AIUsageService.get_usage_summary(company)
        return Response(AIUsageSummarySerializer(summary).data)


class AIUsageByUserView(APIView):
    """
    GET /api/v1/companies/licenses/me/ai-usage/by-user/ — uso IA por usuario.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = getattr(request.user, 'effective_company', None)
        if not company:
            return Response({'detail': 'Sin empresa asignada.'}, status=status.HTTP_404_NOT_FOUND)
        per_user = AIUsageService.get_per_user_usage(company)
        return Response(AIUsagePerUserSerializer(per_user, many=True).data)


class AdminAIUsageView(APIView):
    """GET /api/v1/admin/tenants/{pk}/license/ai-usage/ — uso IA de un tenant."""

    permission_classes = [IsSuperAdmin]

    def get(self, request, pk):
        company = CompanyService.get_company(str(pk))
        summary = AIUsageService.get_usage_summary(company)
        return Response(AIUsageSummarySerializer(summary).data)


class AdminAgentTokenListView(APIView):
    """
    GET  /api/v1/admin/tenants/{pk}/agent-tokens/  — lista tokens del agente
    POST /api/v1/admin/tenants/{pk}/agent-tokens/  — genera un nuevo token
    """
    permission_classes = [IsSuperAdmin]

    def get(self, request, pk):
        tokens = AgentToken.objects.filter(company_id=pk).order_by('-created_at')
        data = [
            {
                'id': str(t.id),
                'token': t.token,
                'label': t.label,
                'is_active': t.is_active,
                'last_used': t.last_used,
                'created_at': t.created_at,
            }
            for t in tokens
        ]
        return Response(data)

    def post(self, request, pk):
        company = CompanyService.get_company(str(pk))
        label = request.data.get('label', '')
        token = AgentToken.objects.create(company=company, label=label)
        return Response({
            'id': str(token.id),
            'token': token.token,
            'label': token.label,
            'is_active': token.is_active,
            'created_at': token.created_at,
        }, status=status.HTTP_201_CREATED)


class AdminAgentTokenRevokeView(APIView):
    """POST /api/v1/admin/tenants/{pk}/agent-tokens/{token_pk}/revoke/"""
    permission_classes = [IsSuperAdmin]

    def post(self, request, pk, token_pk):
        try:
            token = AgentToken.objects.get(id=token_pk, company_id=pk)
        except AgentToken.DoesNotExist:
            return Response({'detail': 'Token no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        token.is_active = False
        token.save(update_fields=['is_active'])
        return Response({'detail': 'Token revocado.'})


class MyAgentTokensView(APIView):
    """
    GET /api/v1/companies/agent-tokens/me/
    Retorna los tokens del agente de la empresa del usuario autenticado (company_admin).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = getattr(request.user, 'company', None)
        if company is None:
            return Response([])
        tokens = AgentToken.objects.filter(company=company, is_active=True).order_by('-created_at')
        data = [
            {
                'id': str(t.id),
                'token': t.token,
                'label': t.label,
                'is_active': t.is_active,
                'last_used': t.last_used,
                'created_at': t.created_at,
            }
            for t in tokens
        ]
        return Response(data)
