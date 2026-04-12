"""
SaiSuite -- Dashboard: Views
Las views SOLO orquestan: reciben request -> llaman service -> retornan response.
"""
import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.dashboard.serializers import (
    DashboardListSerializer,
    DashboardDetailSerializer,
    DashboardCreateSerializer,
    DashboardUpdateSerializer,
    DashboardSaveFiltersSerializer,
    DashboardCardSerializer,
    DashboardCardCreateSerializer,
    DashboardCardUpdateSerializer,
    CardLayoutSerializer,
    DashboardShareCreateSerializer,
    CardDataRequestSerializer,
    CardDataResponseSerializer,
    TrialStatusSerializer,
    ReportBIListSerializer,
    ReportBIDetailSerializer,
    ReportBICreateSerializer,
    ReportBIUpdateSerializer,
    ReportBIExecuteSerializer,
    ReportBIShareCreateSerializer,
)
from apps.dashboard.services import (
    DashboardService,
    CardService,
    TrialService,
    FilterService,
    CatalogService,
    ReportService,
    ReportBIService,
    CfoVirtualService,
)

# ReportService.save_default_filters está en ReportService (re-exportado aquí para claridad)

logger = logging.getLogger(__name__)


def _get_company(request):
    """Helper para obtener la company del request."""
    return getattr(request.user, 'effective_company', None) or request.user.company


# ──────────────────────────────────────────────
# Dashboard CRUD
# ──────────────────────────────────────────────

class DashboardListCreateView(APIView):
    """
    GET  /api/v1/dashboard/          -- Lista dashboards del usuario
    POST /api/v1/dashboard/          -- Crea un dashboard
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = _get_company(request)
        if not company:
            return Response(
                {'error': 'Usuario sin empresa asignada'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        dashboards = DashboardService.list_dashboards(request.user, company.id)
        serializer = DashboardListSerializer(dashboards, many=True)
        return Response(serializer.data)

    def post(self, request):
        company = _get_company(request)
        if not company:
            return Response(
                {'error': 'Usuario sin empresa asignada'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = DashboardCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dashboard = DashboardService.create_dashboard(
            user=request.user,
            company_id=company.id,
            data=serializer.validated_data,
        )
        out = DashboardDetailSerializer(dashboard)
        return Response(out.data, status=status.HTTP_201_CREATED)


class DashboardDetailView(APIView):
    """
    GET    /api/v1/dashboard/{id}/   -- Detalle de un dashboard
    PUT    /api/v1/dashboard/{id}/   -- Actualiza un dashboard
    DELETE /api/v1/dashboard/{id}/   -- Elimina un dashboard
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, dashboard_id):
        dashboard = DashboardService.get_dashboard(dashboard_id, request.user)
        serializer = DashboardDetailSerializer(dashboard)
        return Response(serializer.data)

    def put(self, request, dashboard_id):
        serializer = DashboardUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dashboard = DashboardService.update_dashboard(
            dashboard_id=dashboard_id,
            user=request.user,
            data=serializer.validated_data,
        )
        out = DashboardDetailSerializer(dashboard)
        return Response(out.data)

    def delete(self, request, dashboard_id):
        DashboardService.delete_dashboard(dashboard_id, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DashboardSetDefaultView(APIView):
    """POST /api/v1/dashboard/{id}/set-default/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, dashboard_id):
        dashboard = DashboardService.set_default(dashboard_id, request.user)
        out = DashboardDetailSerializer(dashboard)
        return Response(out.data)


class DashboardToggleFavoriteView(APIView):
    """POST /api/v1/dashboard/{id}/toggle-favorite/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, dashboard_id):
        dashboard = DashboardService.toggle_favorite(dashboard_id, request.user)
        out = DashboardDetailSerializer(dashboard)
        return Response(out.data)


class DashboardSharedWithMeView(APIView):
    """GET /api/v1/dashboard/compartidos-conmigo/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = _get_company(request)
        if not company:
            return Response(
                {'error': 'Usuario sin empresa asignada'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        dashboards = DashboardService.list_shared_with_me(request.user, company.id)
        serializer = DashboardListSerializer(dashboards, many=True)
        return Response(serializer.data)


# ──────────────────────────────────────────────
# Cards
# ──────────────────────────────────────────────

class DashboardCardListCreateView(APIView):
    """
    GET  /api/v1/dashboard/{id}/cards/       -- Lista tarjetas
    POST /api/v1/dashboard/{id}/cards/       -- Agrega tarjeta
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, dashboard_id):
        # Verify access
        DashboardService.get_dashboard(dashboard_id, request.user)
        cards = CardService.list_cards(dashboard_id)
        serializer = DashboardCardSerializer(cards, many=True)
        return Response(serializer.data)

    def post(self, request, dashboard_id):
        # Verify access
        DashboardService.get_dashboard(dashboard_id, request.user)

        serializer = DashboardCardCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        card = CardService.add_card(dashboard_id, serializer.validated_data)
        out = DashboardCardSerializer(card)
        return Response(out.data, status=status.HTTP_201_CREATED)


class DashboardCardDetailView(APIView):
    """
    PUT    /api/v1/dashboard/{id}/cards/{card_id}/   -- Actualiza tarjeta
    DELETE /api/v1/dashboard/{id}/cards/{card_id}/   -- Elimina tarjeta
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, dashboard_id, card_id):
        DashboardService.get_dashboard(dashboard_id, request.user)

        serializer = DashboardCardUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        card = CardService.update_card(card_id, serializer.validated_data)
        out = DashboardCardSerializer(card)
        return Response(out.data)

    def delete(self, request, dashboard_id, card_id):
        DashboardService.get_dashboard(dashboard_id, request.user)
        CardService.delete_card(card_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DashboardCardLayoutView(APIView):
    """POST /api/v1/dashboard/{id}/cards/layout/   -- Guarda layout completo"""
    permission_classes = [IsAuthenticated]

    def post(self, request, dashboard_id):
        DashboardService.get_dashboard(dashboard_id, request.user)

        serializer = CardLayoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        count = CardService.save_layout(
            dashboard_id, serializer.validated_data['layout'],
        )
        return Response({'updated': count})


# ──────────────────────────────────────────────
# Share
# ──────────────────────────────────────────────

class DashboardShareView(APIView):
    """
    POST /api/v1/dashboard/{id}/share/              -- Compartir
    DELETE /api/v1/dashboard/{id}/share/{user_id}/   -- Revocar
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, dashboard_id):
        serializer = DashboardShareCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        share = DashboardService.share_dashboard(
            dashboard_id=dashboard_id,
            user=request.user,
            target_user_id=serializer.validated_data['user_id'],
            puede_editar=serializer.validated_data.get('puede_editar', False),
        )
        return Response({
            'user_id': str(share.compartido_con_id),
            'puede_editar': share.puede_editar,
        }, status=status.HTTP_201_CREATED)


class DashboardShareRevokeView(APIView):
    """DELETE /api/v1/dashboard/{id}/share/{user_id}/"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, dashboard_id, user_id):
        DashboardService.revoke_share(dashboard_id, user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────
# Reports
# ──────────────────────────────────────────────

class CardDataView(APIView):
    """
    POST /api/v1/dashboard/report/card-data/

    Genera datos para una tarjeta especifica con filtros.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        company = _get_company(request)
        if not company:
            return Response(
                {'error': 'Usuario sin empresa asignada'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CardDataRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = ReportService.get_card_data(
            company_id=company.id,
            card_type_code=serializer.validated_data['card_type_code'],
            filtros=serializer.validated_data.get('filtros', {}),
            card_config=serializer.validated_data.get('card_config', {}),
        )
        out = CardDataResponseSerializer(data)
        return Response(out.data)


# ──────────────────────────────────────────────
# Catalog
# ──────────────────────────────────────────────

class CatalogCardsView(APIView):
    """GET /api/v1/dashboard/catalog/cards/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = _get_company(request)
        if not company:
            return Response(
                {'error': 'Usuario sin empresa asignada'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cards = CatalogService.get_available_cards(company.id)
        # Transform dict to list with code included
        result = [
            {'code': code, **card_def}
            for code, card_def in cards.items()
        ]
        return Response(result)


class CatalogCategoriesView(APIView):
    """GET /api/v1/dashboard/catalog/categories/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = _get_company(request)
        if not company:
            return Response(
                {'error': 'Usuario sin empresa asignada'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        categories = CatalogService.get_categories(company.id)
        return Response(categories)


# ──────────────────────────────────────────────
# Filters
# ──────────────────────────────────────────────

class FilterTercerosView(APIView):
    """GET /api/v1/dashboard/filters/terceros/?q="""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = _get_company(request)
        if not company:
            return Response(
                {'error': 'Usuario sin empresa asignada'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        query = request.query_params.get('q', '')
        result = FilterService.get_available_terceros(company.id, query)
        return Response(result)


class FilterProyectosView(APIView):
    """GET /api/v1/dashboard/filters/proyectos/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = _get_company(request)
        if not company:
            return Response(
                {'error': 'Usuario sin empresa asignada'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = FilterService.get_available_proyectos(company.id)
        return Response(result)


class FilterDepartamentosView(APIView):
    """GET /api/v1/dashboard/filters/departamentos/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = _get_company(request)
        if not company:
            return Response(
                {'error': 'Usuario sin empresa asignada'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = FilterService.get_available_departamentos(company.id)
        return Response(result)


class FilterPeriodosView(APIView):
    """GET /api/v1/dashboard/filters/periodos/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = _get_company(request)
        if not company:
            return Response(
                {'error': 'Usuario sin empresa asignada'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = FilterService.get_available_periodos(company.id)
        return Response(result)


class FilterTiposDocView(APIView):
    """GET /api/v1/dashboard/filters/tipos-doc/?source=gl"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = _get_company(request)
        if not company:
            return Response(
                {'error': 'Usuario sin empresa asignada'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        source = request.query_params.get('source', 'gl')
        result = FilterService.get_available_tipos_doc(company.id, source)
        return Response(result)


class FilterCentrosCostoView(APIView):
    """GET /api/v1/dashboard/filters/centros-costo/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = _get_company(request)
        if not company:
            return Response(
                {'error': 'Usuario sin empresa asignada'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = FilterService.get_available_centros_costo(company.id)
        return Response(result)


class FilterActividadesView(APIView):
    """GET /api/v1/dashboard/filters/actividades/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = _get_company(request)
        if not company:
            return Response(
                {'error': 'Usuario sin empresa asignada'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = FilterService.get_available_actividades(company.id)
        return Response(result)


# ──────────────────────────────────────────────
# Trial
# ──────────────────────────────────────────────

class TrialActivateView(APIView):
    """POST /api/v1/dashboard/trial/activate/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        company = _get_company(request)
        if not company:
            return Response(
                {'error': 'Usuario sin empresa asignada'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        trial = TrialService.activate_trial(company.id)
        return Response({
            'module_code': trial.module_code,
            'iniciado_en': trial.iniciado_en,
            'expira_en': trial.expira_en,
            'dias_restantes': trial.dias_restantes(),
        }, status=status.HTTP_201_CREATED)


class TrialStatusView(APIView):
    """GET /api/v1/dashboard/trial/status/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = _get_company(request)
        if not company:
            return Response(
                {'error': 'Usuario sin empresa asignada'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = TrialService.get_trial_status(company.id)
        out = TrialStatusSerializer(result)
        return Response(out.data)


# ──────────────────────────────────────────────
# CFO Virtual
# ──────────────────────────────────────────────

class DashboardSaveFiltersView(APIView):
    """
    PUT /api/v1/dashboard/{id}/filters/
    Guarda filtros_default en el dashboard. Retorna el dashboard actualizado.
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, dashboard_id):
        serializer = DashboardSaveFiltersSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dashboard = ReportService.save_default_filters(
            dashboard_id=dashboard_id,
            user=request.user,
            filtros=serializer.validated_data['filtros_default'],
        )
        out = DashboardDetailSerializer(dashboard)
        return Response(out.data)


class CfoVirtualView(APIView):
    """
    POST /api/v1/dashboard/cfo-virtual/
    Recibe {question} y retorna {response} del asistente financiero IA.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        question = request.data.get('question', '').strip()
        if not question:
            return Response(
                {'error': 'El campo question es requerido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        company = _get_company(request)
        if not company:
            return Response(
                {'error': 'Usuario sin empresa asignada.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            response_text = CfoVirtualService.ask(question, company, user=request.user)
        except Exception as exc:
            detail = getattr(exc, 'detail', str(exc))
            return Response({'error': str(detail)}, status=status.HTTP_502_BAD_GATEWAY)

        logger.info(
            'cfo_virtual_query',
            extra={'company_id': str(company.id), 'user_id': str(request.user.id)},
        )
        return Response({'response': response_text})


class CfoSuggestReportView(APIView):
    """
    POST /api/v1/dashboard/cfo-virtual/suggest-report/
    Recibe {question} y retorna una sugerencia de reporte BI predefinido.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        question = request.data.get('question', '').strip()
        if not question:
            return Response(
                {'error': 'El campo question es requerido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        company = _get_company(request)
        if not company:
            return Response(
                {'error': 'Usuario sin empresa asignada.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = CfoVirtualService.suggest_report(question, company, user=request.user)
        except Exception as exc:
            detail = getattr(exc, 'detail', str(exc))
            return Response({'error': str(detail)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(result)


# ──────────────────────────────────────────────
# Report BI CRUD
# ──────────────────────────────────────────────

class ReportBIListCreateView(APIView):
    """
    GET  /api/v1/dashboard/reportes/          -- Lista reportes BI del usuario
    POST /api/v1/dashboard/reportes/          -- Crea un reporte BI
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = _get_company(request)
        if not company:
            return Response(
                {'error': 'Usuario sin empresa asignada'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reports = ReportBIService.list_reports(request.user, company.id)
        serializer = ReportBIListSerializer(reports, many=True)
        return Response(serializer.data)

    def post(self, request):
        company = _get_company(request)
        if not company:
            return Response(
                {'error': 'Usuario sin empresa asignada'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ReportBICreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = ReportBIService.create_report(
            request.user, company.id, serializer.validated_data,
        )
        out = ReportBIDetailSerializer(report)
        return Response(out.data, status=status.HTTP_201_CREATED)


class ReportBIDetailView(APIView):
    """
    GET    /api/v1/dashboard/reportes/{id}/   -- Detalle de un reporte BI
    PUT    /api/v1/dashboard/reportes/{id}/   -- Actualizar reporte BI
    DELETE /api/v1/dashboard/reportes/{id}/   -- Eliminar reporte BI
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, report_id):
        report = ReportBIService.get_report(report_id, request.user)
        serializer = ReportBIDetailSerializer(report)
        return Response(serializer.data)

    def put(self, request, report_id):
        serializer = ReportBIUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = ReportBIService.update_report(
            report_id, request.user, serializer.validated_data,
        )
        out = ReportBIDetailSerializer(report)
        return Response(out.data)

    def delete(self, request, report_id):
        ReportBIService.delete_report(report_id, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReportBIToggleFavoriteView(APIView):
    """POST /api/v1/dashboard/reportes/{id}/toggle-favorite/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, report_id):
        report = ReportBIService.toggle_favorite(report_id, request.user)
        return Response({'es_favorito': report.es_favorito})


class ReportBIExecuteView(APIView):
    """
    POST /api/v1/dashboard/reportes/{id}/execute/
    Ejecuta un reporte guardado y retorna los datos.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, report_id):
        company = _get_company(request)
        if not company:
            return Response(
                {'error': 'Usuario sin empresa asignada'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        report = ReportBIService.get_report(report_id, request.user)
        result = ReportBIService.execute_report(report, company.id)
        return Response(result)


class ReportBIPreviewView(APIView):
    """
    POST /api/v1/dashboard/reportes/preview/
    Ejecuta una preview ad-hoc sin guardar el reporte.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        company = _get_company(request)
        if not company:
            return Response(
                {'error': 'Usuario sin empresa asignada'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ReportBIExecuteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = ReportBIService.execute_preview(
            serializer.validated_data, company.id,
        )
        return Response(result)


class ReportBIExportPdfView(APIView):
    """
    POST /api/v1/dashboard/reportes/{id}/export-pdf/
    Genera y retorna un PDF con los datos del reporte.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, report_id):
        company = _get_company(request)
        if not company:
            return Response(
                {'error': 'Usuario sin empresa asignada'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        report = ReportBIService.get_report(report_id, request.user)
        pdf_bytes = ReportBIService.export_pdf(report, company.id)
        from django.http import HttpResponse
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{report.titulo}.pdf"'
        return response


class ReportBIShareView(APIView):
    """
    POST /api/v1/dashboard/reportes/{id}/share/
    Comparte un reporte con otro usuario.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, report_id):
        serializer = ReportBIShareCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ReportBIService.share_report(
            report_id,
            request.user,
            serializer.validated_data['user_id'],
            serializer.validated_data.get('puede_editar', False),
        )
        return Response({'status': 'compartido'}, status=status.HTTP_201_CREATED)


class ReportBIShareRevokeView(APIView):
    """DELETE /api/v1/dashboard/reportes/{id}/share/{user_id}/"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, report_id, user_id):
        ReportBIService.revoke_share(report_id, user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReportBITemplatesView(APIView):
    """GET /api/v1/dashboard/reportes/templates/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = _get_company(request)
        if not company:
            return Response(
                {'error': 'Usuario sin empresa asignada'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        templates = ReportBIService.list_templates(company.id)
        serializer = ReportBIListSerializer(templates, many=True)
        return Response(serializer.data)


# ──────────────────────────────────────────────
# BI Metadata (sources, fields, filters)
# ──────────────────────────────────────────────

class BISourcesView(APIView):
    """GET /api/v1/dashboard/reportes/meta/sources/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sources = ReportBIService.get_sources()
        return Response(sources)


class BIFieldsView(APIView):
    """GET /api/v1/dashboard/reportes/meta/fields/?source=gl"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        source = request.query_params.get('source', '')
        if not source:
            return Response(
                {'error': 'El parámetro source es requerido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        fields = ReportBIService.get_fields(source)
        return Response(fields)


class BIFiltersView(APIView):
    """GET /api/v1/dashboard/reportes/meta/filters/?source=gl"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        source = request.query_params.get('source', '')
        if not source:
            return Response(
                {'error': 'El parámetro source es requerido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        filters = ReportBIService.get_filters(source)
        return Response(filters)
