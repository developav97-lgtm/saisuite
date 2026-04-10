/**
 * SaiSuite — CrmService
 * Servicio para el módulo CRM. API: /api/v1/crm/
 */
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  CrmPipeline, CrmEtapa,
  KanbanColumna,
  CrmLead, CrmLeadCreate,
  CrmOportunidad, CrmOportunidadCreate,
  CrmActividad, CrmActividadCreate, CrmActividadAgenda,
  CrmTimelineEvent,
  CrmCotizacion, CrmCotizacionCreate,
  CrmLineaCotizacion, CrmLineaCotizacionCreate,
  CrmProducto, CrmImpuesto,
  CrmLeadScoringRule,
  CrmDashboard, CrmForecast,
} from '../models/crm.model';

export interface PagedResponse<T> {
  count: number;
  results: T[];
}

export interface LeadListParams {
  search?: string;
  fuente?: string;
  convertido?: boolean;
  asignado_a?: string;
  pipeline?: string;
  ordering?: string;
  page?: number;
  page_size?: number;
}

export interface OportunidadListParams {
  search?: string;
  pipeline?: string;
  etapa?: string;
  asignado_a?: string;
  ordering?: string;
  page?: number;
  page_size?: number;
}

@Injectable({ providedIn: 'root' })
export class CrmService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/crm';

  // ── Pipelines ──────────────────────────────────────────────────────────────

  listPipelines(): Observable<CrmPipeline[]> {
    return this.http.get<CrmPipeline[]>(`${this.base}/pipelines/`);
  }

  createPipeline(data: { nombre: string; es_default?: boolean }): Observable<CrmPipeline> {
    return this.http.post<CrmPipeline>(`${this.base}/pipelines/`, data);
  }

  updatePipeline(id: string, data: Partial<CrmPipeline>): Observable<CrmPipeline> {
    return this.http.patch<CrmPipeline>(`${this.base}/pipelines/${id}/`, data);
  }

  deletePipeline(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/pipelines/${id}/`);
  }

  getKanban(pipelineId: string): Observable<KanbanColumna[]> {
    return this.http.get<KanbanColumna[]>(`${this.base}/pipelines/${pipelineId}/kanban/`);
  }

  // ── Etapas ─────────────────────────────────────────────────────────────────

  createEtapa(pipelineId: string, data: Partial<CrmEtapa>): Observable<CrmEtapa> {
    return this.http.post<CrmEtapa>(`${this.base}/pipelines/${pipelineId}/etapas/`, data);
  }

  updateEtapa(id: string, data: Partial<CrmEtapa>): Observable<CrmEtapa> {
    return this.http.patch<CrmEtapa>(`${this.base}/etapas/${id}/`, data);
  }

  deleteEtapa(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/etapas/${id}/`);
  }

  reordenarEtapas(pipelineId: string, orden: { id: string; orden: number }[]): Observable<void> {
    return this.http.post<void>(`${this.base}/pipelines/${pipelineId}/etapas/reordenar/`, { orden });
  }

  // ── Leads ──────────────────────────────────────────────────────────────────

  listLeads(params: LeadListParams = {}): Observable<PagedResponse<CrmLead>> {
    let p = new HttpParams();
    if (params.search)                   p = p.set('search', params.search);
    if (params.fuente)                   p = p.set('fuente', params.fuente);
    if (params.convertido !== undefined) p = p.set('convertido', String(params.convertido));
    if (params.asignado_a)               p = p.set('asignado_a', params.asignado_a);
    if (params.pipeline)                 p = p.set('pipeline', params.pipeline);
    if (params.ordering)                 p = p.set('ordering', params.ordering);
    if (params.page)                     p = p.set('page', String(params.page));
    if (params.page_size)                p = p.set('page_size', String(params.page_size));
    return this.http.get<PagedResponse<CrmLead>>(`${this.base}/leads/`, { params: p });
  }

  getLead(id: string): Observable<CrmLead> {
    return this.http.get<CrmLead>(`${this.base}/leads/${id}/`);
  }

  createLead(data: CrmLeadCreate): Observable<CrmLead> {
    return this.http.post<CrmLead>(`${this.base}/leads/`, data);
  }

  updateLead(id: string, data: Partial<CrmLeadCreate>): Observable<CrmLead> {
    return this.http.patch<CrmLead>(`${this.base}/leads/${id}/`, data);
  }

  deleteLead(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/leads/${id}/`);
  }

  convertirLead(id: string, data: {
    etapa_id: string;
    valor_esperado?: string;
    asignado_a_id?: string | null;
    crear_tercero?: boolean;
    tercero_id?: string | null;
  }): Observable<CrmOportunidad> {
    return this.http.post<CrmOportunidad>(`${this.base}/leads/${id}/convertir/`, data);
  }

  asignarLead(id: string, usuarioId: string): Observable<CrmLead> {
    return this.http.post<CrmLead>(`${this.base}/leads/${id}/asignar/`, { usuario_id: usuarioId });
  }

  asignarRoundRobin(id: string): Observable<CrmLead> {
    return this.http.post<CrmLead>(`${this.base}/leads/${id}/round-robin/`, {});
  }

  asignarMasivoRoundRobin(): Observable<{ asignados: number }> {
    return this.http.post<{ asignados: number }>(`${this.base}/leads/asignar-masivo/`, {});
  }

  importarLeads(registros: Record<string, string>[]): Observable<{ creados: number; errores: unknown[] }> {
    return this.http.post<{ creados: number; errores: unknown[] }>(`${this.base}/leads/importar/`, { registros });
  }

  // ── Scoring Rules ──────────────────────────────────────────────────────────

  listScoringRules(): Observable<CrmLeadScoringRule[]> {
    return this.http.get<CrmLeadScoringRule[]>(`${this.base}/scoring-rules/`);
  }

  createScoringRule(data: Partial<CrmLeadScoringRule>): Observable<CrmLeadScoringRule> {
    return this.http.post<CrmLeadScoringRule>(`${this.base}/scoring-rules/`, data);
  }

  updateScoringRule(id: string, data: Partial<CrmLeadScoringRule>): Observable<CrmLeadScoringRule> {
    return this.http.patch<CrmLeadScoringRule>(`${this.base}/scoring-rules/${id}/`, data);
  }

  deleteScoringRule(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/scoring-rules/${id}/`);
  }

  // ── Oportunidades ──────────────────────────────────────────────────────────

  listOportunidades(params: OportunidadListParams = {}): Observable<PagedResponse<CrmOportunidad>> {
    let p = new HttpParams();
    if (params.search)    p = p.set('search', params.search);
    if (params.pipeline)  p = p.set('pipeline', params.pipeline);
    if (params.etapa)     p = p.set('etapa', params.etapa);
    if (params.asignado_a) p = p.set('asignado_a', params.asignado_a);
    if (params.ordering)  p = p.set('ordering', params.ordering);
    if (params.page)      p = p.set('page', String(params.page));
    if (params.page_size) p = p.set('page_size', String(params.page_size));
    return this.http.get<PagedResponse<CrmOportunidad>>(`${this.base}/oportunidades/`, { params: p });
  }

  getOportunidad(id: string): Observable<CrmOportunidad> {
    return this.http.get<CrmOportunidad>(`${this.base}/oportunidades/${id}/`);
  }

  createOportunidad(data: CrmOportunidadCreate): Observable<CrmOportunidad> {
    return this.http.post<CrmOportunidad>(`${this.base}/oportunidades/`, data);
  }

  updateOportunidad(id: string, data: Partial<CrmOportunidadCreate>): Observable<CrmOportunidad> {
    return this.http.patch<CrmOportunidad>(`${this.base}/oportunidades/${id}/`, data);
  }

  deleteOportunidad(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/oportunidades/${id}/`);
  }

  moverEtapa(id: string, etapaId: string): Observable<CrmOportunidad> {
    return this.http.post<CrmOportunidad>(`${this.base}/oportunidades/${id}/mover-etapa/`, { etapa_id: etapaId });
  }

  ganarOportunidad(id: string): Observable<CrmOportunidad> {
    return this.http.post<CrmOportunidad>(`${this.base}/oportunidades/${id}/ganar/`, {});
  }

  perderOportunidad(id: string, motivo: string): Observable<CrmOportunidad> {
    return this.http.post<CrmOportunidad>(`${this.base}/oportunidades/${id}/perder/`, { motivo });
  }

  getTimeline(id: string): Observable<CrmTimelineEvent[]> {
    return this.http.get<CrmTimelineEvent[]>(`${this.base}/oportunidades/${id}/timeline/`);
  }

  agregarNota(id: string, descripcion: string): Observable<CrmTimelineEvent> {
    return this.http.post<CrmTimelineEvent>(`${this.base}/oportunidades/${id}/notas/`, { descripcion });
  }

  enviarEmail(id: string, data: { destinatario: string; asunto: string; cuerpo: string }): Observable<void> {
    return this.http.post<void>(`${this.base}/oportunidades/${id}/enviar-email/`, data);
  }

  // ── Actividades ────────────────────────────────────────────────────────────

  listActividades(oportunidadId: string): Observable<CrmActividad[]> {
    return this.http.get<CrmActividad[]>(`${this.base}/oportunidades/${oportunidadId}/actividades/`);
  }

  createActividad(oportunidadId: string, data: CrmActividadCreate): Observable<CrmActividad> {
    return this.http.post<CrmActividad>(`${this.base}/oportunidades/${oportunidadId}/actividades/`, data);
  }

  listActividadesLead(leadId: string): Observable<CrmActividad[]> {
    return this.http.get<CrmActividad[]>(`${this.base}/leads/${leadId}/actividades/`);
  }

  createActividadLead(leadId: string, data: CrmActividadCreate): Observable<CrmActividad> {
    return this.http.post<CrmActividad>(`${this.base}/leads/${leadId}/actividades/`, data);
  }

  updateActividad(id: string, data: Partial<CrmActividad>): Observable<CrmActividad> {
    return this.http.patch<CrmActividad>(`${this.base}/actividades/${id}/`, data);
  }

  completarActividad(id: string, resultado: string): Observable<CrmActividad> {
    return this.http.post<CrmActividad>(`${this.base}/actividades/${id}/completar/`, { resultado });
  }

  // ── Cotizaciones ───────────────────────────────────────────────────────────

  listCotizaciones(oportunidadId: string): Observable<CrmCotizacion[]> {
    return this.http.get<CrmCotizacion[]>(`${this.base}/oportunidades/${oportunidadId}/cotizaciones/`);
  }

  getCotizacion(id: string): Observable<CrmCotizacion> {
    return this.http.get<CrmCotizacion>(`${this.base}/cotizaciones/${id}/`);
  }

  createCotizacion(oportunidadId: string, data: CrmCotizacionCreate): Observable<CrmCotizacion> {
    return this.http.post<CrmCotizacion>(`${this.base}/oportunidades/${oportunidadId}/cotizaciones/crear/`, data);
  }

  updateCotizacion(id: string, data: Partial<CrmCotizacionCreate>): Observable<CrmCotizacion> {
    return this.http.patch<CrmCotizacion>(`${this.base}/cotizaciones/${id}/`, data);
  }

  deleteCotizacion(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/cotizaciones/${id}/`);
  }

  enviarCotizacion(id: string, emailDestino?: string): Observable<CrmCotizacion> {
    return this.http.post<CrmCotizacion>(`${this.base}/cotizaciones/${id}/enviar/`, { email_destino: emailDestino });
  }

  aceptarCotizacion(id: string): Observable<CrmCotizacion> {
    return this.http.post<CrmCotizacion>(`${this.base}/cotizaciones/${id}/aceptar/`, {});
  }

  rechazarCotizacion(id: string): Observable<CrmCotizacion> {
    return this.http.post<CrmCotizacion>(`${this.base}/cotizaciones/${id}/rechazar/`, {});
  }

  getCotizacionPdfUrl(id: string): string {
    return `${this.base}/cotizaciones/${id}/pdf/`;
  }

  // ── Líneas cotización ──────────────────────────────────────────────────────

  addLinea(cotizacionId: string, data: CrmLineaCotizacionCreate): Observable<CrmLineaCotizacion> {
    return this.http.post<CrmLineaCotizacion>(`${this.base}/cotizaciones/${cotizacionId}/lineas/`, data);
  }

  updateLinea(cotizacionId: string, lineaId: string, data: Partial<CrmLineaCotizacionCreate>): Observable<CrmLineaCotizacion> {
    return this.http.patch<CrmLineaCotizacion>(`${this.base}/cotizaciones/${cotizacionId}/lineas/${lineaId}/`, data);
  }

  deleteLinea(cotizacionId: string, lineaId: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/cotizaciones/${cotizacionId}/lineas/${lineaId}/`);
  }

  // ── Catálogo ───────────────────────────────────────────────────────────────

  listProductos(params: { search?: string; grupo?: string; clase?: string } = {}): Observable<CrmProducto[]> {
    let p = new HttpParams();
    if (params.search) p = p.set('search', params.search);
    if (params.grupo)  p = p.set('grupo', params.grupo);
    if (params.clase)  p = p.set('clase', params.clase);
    return this.http.get<CrmProducto[]>(`${this.base}/productos/`, { params: p });
  }

  listImpuestos(): Observable<CrmImpuesto[]> {
    return this.http.get<CrmImpuesto[]>(`${this.base}/impuestos/`);
  }

  // ── Agenda ─────────────────────────────────────────────────────────────────

  getAgenda(params: {
    fecha_desde?: string;
    fecha_hasta?: string;
    solo_pendientes?: boolean;
    asignado_a?: string;
  } = {}): Observable<CrmActividadAgenda[]> {
    let p = new HttpParams();
    if (params.fecha_desde)    p = p.set('fecha_desde', params.fecha_desde);
    if (params.fecha_hasta)    p = p.set('fecha_hasta', params.fecha_hasta);
    if (params.solo_pendientes !== undefined) p = p.set('solo_pendientes', String(params.solo_pendientes));
    if (params.asignado_a)     p = p.set('asignado_a', params.asignado_a);
    return this.http.get<CrmActividadAgenda[]>(`${this.base}/agenda/`, { params: p });
  }

  // ── Dashboard ──────────────────────────────────────────────────────────────

  getDashboard(): Observable<CrmDashboard> {
    return this.http.get<CrmDashboard>(`${this.base}/dashboard/`);
  }

  getForecast(): Observable<CrmForecast> {
    return this.http.get<CrmForecast>(`${this.base}/dashboard/forecast/`);
  }
}
