"""
SaiSuite — CRM URLs
"""
from django.urls import path
from .views import (
    PipelineViewSet, EtapaViewSet, LeadViewSet, LeadWebhookView,
    LeadScoringRuleViewSet, OportunidadViewSet, ActividadViewSet, AgendaView,
)
from .cotizacion_views import (
    CotizacionViewSet, LineaCotizacionViewSet,
    ProductoListView, ProductoSyncView, ImpuestoListView,
    CotizacionSyncCallbackView,
)
from .dashboard_views import DashboardView, ForecastView

pipeline_list       = PipelineViewSet.as_view({'get': 'list', 'post': 'create'})
pipeline_detail     = PipelineViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'})
pipeline_kanban     = PipelineViewSet.as_view({'get': 'kanban'})

etapa_list          = EtapaViewSet.as_view({'get': 'list', 'post': 'create'})
etapa_detail        = EtapaViewSet.as_view({'patch': 'partial_update', 'delete': 'destroy'})
etapa_reordenar     = EtapaViewSet.as_view({'post': 'reordenar'})

lead_list           = LeadViewSet.as_view({'get': 'list', 'post': 'create'})
lead_detail         = LeadViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'})
lead_convertir      = LeadViewSet.as_view({'post': 'convertir'})
lead_asignar        = LeadViewSet.as_view({'post': 'asignar'})
lead_round_robin    = LeadViewSet.as_view({'post': 'round_robin'})
lead_asignar_masivo = LeadViewSet.as_view({'post': 'asignar_masivo'})
lead_importar       = LeadViewSet.as_view({'post': 'importar'})
lead_act_list       = LeadViewSet.as_view({'get': 'list_actividades', 'post': 'crear_actividad'})

scoring_list        = LeadScoringRuleViewSet.as_view({'get': 'list', 'post': 'create'})
scoring_detail      = LeadScoringRuleViewSet.as_view({'patch': 'partial_update', 'delete': 'destroy'})

op_list             = OportunidadViewSet.as_view({'get': 'list', 'post': 'create'})
op_detail           = OportunidadViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'})
op_mover_etapa      = OportunidadViewSet.as_view({'post': 'mover_etapa'})
op_ganar            = OportunidadViewSet.as_view({'post': 'ganar'})
op_perder           = OportunidadViewSet.as_view({'post': 'perder'})
op_timeline_get     = OportunidadViewSet.as_view({'get': 'timeline'})
op_timeline_post    = OportunidadViewSet.as_view({'post': 'agregar_nota'})
op_email            = OportunidadViewSet.as_view({'post': 'enviar_email'})
op_act_list         = OportunidadViewSet.as_view({'get': 'list_actividades', 'post': 'crear_actividad'})

act_detail          = ActividadViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'})
act_completar       = ActividadViewSet.as_view({'post': 'completar'})

# Cotizaciones
cot_by_op           = CotizacionViewSet.as_view({'get': 'list_by_oportunidad', 'post': 'create'})
cot_detail          = CotizacionViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'})
cot_enviar          = CotizacionViewSet.as_view({'post': 'enviar'})
cot_aceptar         = CotizacionViewSet.as_view({'post': 'aceptar'})
cot_rechazar        = CotizacionViewSet.as_view({'post': 'rechazar'})
cot_pdf             = CotizacionViewSet.as_view({'get': 'pdf'})

linea_list          = LineaCotizacionViewSet.as_view({'get': 'list', 'post': 'create'})
linea_detail        = LineaCotizacionViewSet.as_view({'patch': 'partial_update', 'delete': 'destroy'})


urlpatterns = [
    # ── Pipelines ──────────────────────────────────────────────────────────────
    path('pipelines/',                          pipeline_list,      name='crm-pipeline-list'),
    path('pipelines/<uuid:pk>/',                pipeline_detail,    name='crm-pipeline-detail'),
    path('pipelines/<uuid:pk>/kanban/',         pipeline_kanban,    name='crm-pipeline-kanban'),
    path('pipelines/<uuid:pipeline_pk>/etapas/', etapa_list,        name='crm-etapa-list'),
    path('pipelines/<uuid:pipeline_pk>/etapas/reordenar/', etapa_reordenar, name='crm-etapa-reordenar'),
    path('etapas/<uuid:pk>/',                   etapa_detail,       name='crm-etapa-detail'),

    # ── Leads ──────────────────────────────────────────────────────────────────
    path('leads/',                              lead_list,          name='crm-lead-list'),
    path('leads/importar/',                     lead_importar,      name='crm-lead-importar'),
    path('leads/asignar-masivo/',               lead_asignar_masivo, name='crm-lead-asignar-masivo'),
    path('leads/<uuid:pk>/',                    lead_detail,        name='crm-lead-detail'),
    path('leads/<uuid:pk>/convertir/',          lead_convertir,     name='crm-lead-convertir'),
    path('leads/<uuid:pk>/asignar/',            lead_asignar,       name='crm-lead-asignar'),
    path('leads/<uuid:pk>/round-robin/',        lead_round_robin,   name='crm-lead-round-robin'),
    path('leads/<uuid:pk>/actividades/',        lead_act_list,      name='crm-lead-actividades'),
    path('leads/webhook/<str:company_nit>/',  LeadWebhookView.as_view(), name='crm-lead-webhook'),

    # ── Scoring Rules ──────────────────────────────────────────────────────────
    path('scoring-rules/',                      scoring_list,       name='crm-scoring-list'),
    path('scoring-rules/<uuid:pk>/',            scoring_detail,     name='crm-scoring-detail'),

    # ── Oportunidades ──────────────────────────────────────────────────────────
    path('oportunidades/',                      op_list,            name='crm-op-list'),
    path('oportunidades/<uuid:pk>/',            op_detail,          name='crm-op-detail'),
    path('oportunidades/<uuid:pk>/mover-etapa/', op_mover_etapa,    name='crm-op-mover-etapa'),
    path('oportunidades/<uuid:pk>/ganar/',      op_ganar,           name='crm-op-ganar'),
    path('oportunidades/<uuid:pk>/perder/',     op_perder,          name='crm-op-perder'),
    path('oportunidades/<uuid:pk>/timeline/',   op_timeline_get,    name='crm-op-timeline-get'),
    path('oportunidades/<uuid:pk>/notas/',      op_timeline_post,   name='crm-op-nota'),
    path('oportunidades/<uuid:pk>/enviar-email/', op_email,         name='crm-op-email'),
    path('oportunidades/<uuid:pk>/actividades/', op_act_list,       name='crm-op-actividades'),
    path('oportunidades/<uuid:oportunidad_pk>/cotizaciones/', cot_by_op, name='crm-cot-by-op'),
    path('oportunidades/<uuid:oportunidad_pk>/cotizaciones/crear/', cot_by_op, name='crm-cot-crear'),

    # ── Actividades ────────────────────────────────────────────────────────────
    path('actividades/<uuid:pk>/',              act_detail,         name='crm-act-detail'),
    path('actividades/<uuid:pk>/completar/',    act_completar,      name='crm-act-completar'),

    # ── Cotizaciones ───────────────────────────────────────────────────────────
    path('cotizaciones/<uuid:pk>/',             cot_detail,         name='crm-cot-detail'),
    path('cotizaciones/<uuid:pk>/enviar/',      cot_enviar,         name='crm-cot-enviar'),
    path('cotizaciones/<uuid:pk>/aceptar/',     cot_aceptar,        name='crm-cot-aceptar'),
    path('cotizaciones/<uuid:pk>/rechazar/',    cot_rechazar,       name='crm-cot-rechazar'),
    path('cotizaciones/<uuid:pk>/pdf/',         cot_pdf,            name='crm-cot-pdf'),
    path('cotizaciones/<uuid:cotizacion_pk>/lineas/', linea_list,   name='crm-linea-list'),
    path('cotizaciones/<uuid:cotizacion_pk>/lineas/<uuid:pk>/', linea_detail, name='crm-linea-detail'),

    # ── Catálogo ───────────────────────────────────────────────────────────────
    path('productos/',                          ProductoListView.as_view(),    name='crm-productos'),
    path('productos/sync/',                     ProductoSyncView.as_view(),    name='crm-productos-sync'),
    path('impuestos/',                          ImpuestoListView.as_view(),    name='crm-impuestos'),

    # ── Agenda ─────────────────────────────────────────────────────────────────
    path('agenda/',                             AgendaView.as_view(),          name='crm-agenda'),

    # ── Dashboard ──────────────────────────────────────────────────────────────
    path('dashboard/',                          DashboardView.as_view(),       name='crm-dashboard'),
    path('dashboard/forecast/',                 ForecastView.as_view(),        name='crm-forecast'),

    # ── Sync callback (agente interno) ─────────────────────────────────────────
    path('sync/cotizacion-confirmada/',         CotizacionSyncCallbackView.as_view(), name='crm-sync-callback'),
]
