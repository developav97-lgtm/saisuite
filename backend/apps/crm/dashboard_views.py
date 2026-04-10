"""
SaiSuite — CRM: Dashboard Views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from .dashboard_services import CrmDashboardService
from .permissions import CanAccessCrm


class DashboardView(APIView):
    permission_classes = [CanAccessCrm]

    def get(self, request):
        metricas = CrmDashboardService.get_metricas(
            request.user.company,
            periodo_dias=int(request.query_params.get('dias', 30)),
            pipeline_id=request.query_params.get('pipeline'),
            asignado_a=request.query_params.get('asignado_a'),
        )
        return Response(metricas)


class ForecastView(APIView):
    permission_classes = [CanAccessCrm]

    def get(self, request):
        forecast = CrmDashboardService.get_forecast_detalle(
            request.user.company,
            pipeline_id=request.query_params.get('pipeline'),
            asignado_a=request.query_params.get('asignado_a'),
        )
        return Response(forecast)
