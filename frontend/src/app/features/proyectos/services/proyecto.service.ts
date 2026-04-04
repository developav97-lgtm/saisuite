import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { PaginatedResponse } from '../models/paginated-response.model';
import {
  ProyectoList,
  ProyectoDetail,
  ProyectoCreate,
  EstadoFinanciero,
  EstadoProyecto,
  PlantillaProyecto,
  PlantillaProyectoCreate,
  CreateFromTemplateRequest,
  ImportExcelResult,
} from '../models/proyecto.model';

export interface ProyectoListParams {
  page?: number;
  page_size?: number;
  search?: string;
  estado?: EstadoProyecto;
  tipo?: string;
  gerente_id?: string;
  ordering?: string;
  activo?: boolean;
}

@Injectable({ providedIn: 'root' })
export class ProyectoService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/projects';

  list(params: ProyectoListParams = {}): Observable<PaginatedResponse<ProyectoList>> {
    let httpParams = new HttpParams();
    if (params.page)       httpParams = httpParams.set('page', params.page.toString());
    if (params.page_size)  httpParams = httpParams.set('page_size', params.page_size.toString());
    if (params.search)     httpParams = httpParams.set('search', params.search);
    if (params.estado)     httpParams = httpParams.set('estado', params.estado);
    if (params.tipo)       httpParams = httpParams.set('tipo', params.tipo);
    if (params.gerente_id) httpParams = httpParams.set('gerente_id', params.gerente_id);
    if (params.ordering)   httpParams = httpParams.set('ordering', params.ordering);
    if (params.activo !== undefined) httpParams = httpParams.set('activo', params.activo.toString());

    return this.http.get<PaginatedResponse<ProyectoList>>(
      `${this.baseUrl}/`, { params: httpParams }
    );
  }

  getById(id: string): Observable<ProyectoDetail> {
    return this.http.get<ProyectoDetail>(`${this.baseUrl}/${id}/`);
  }

  create(data: ProyectoCreate): Observable<ProyectoDetail> {
    return this.http.post<ProyectoDetail>(`${this.baseUrl}/`, data);
  }

  update(id: string, data: Partial<ProyectoCreate>): Observable<ProyectoDetail> {
    return this.http.patch<ProyectoDetail>(`${this.baseUrl}/${id}/`, data);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${id}/`);
  }

  cambiarEstado(
    id: string,
    nuevo_estado: EstadoProyecto,
    forzar = false
  ): Observable<ProyectoDetail> {
    return this.http.post<ProyectoDetail>(
      `${this.baseUrl}/${id}/cambiar-estado/`,
      { nuevo_estado, forzar }
    );
  }

  getEstadoFinanciero(id: string): Observable<EstadoFinanciero> {
    return this.http.get<EstadoFinanciero>(`${this.baseUrl}/${id}/estado-financiero/`);
  }

  getCaminoCritico(id: string): Observable<{ tareas_criticas: string[] }> {
    return this.http.get<{ tareas_criticas: string[] }>(
      `${this.baseUrl}/${id}/camino-critico/`,
    );
  }

  getGanttData(id: string): Observable<{ tasks: import('../models/tarea.model').GanttTask[] }> {
    return this.http.get<{ tasks: import('../models/tarea.model').GanttTask[] }>(
      `${this.baseUrl}/${id}/gantt-data/`,
    );
  }

  // ── Exportación PDF ───────────────────────────────────────────────────────

  exportPDF(
    proyectoId: string,
    options?: { includeGantt?: boolean; includeBudget?: boolean },
  ): Observable<Blob> {
    let params = new HttpParams();
    if (options?.includeGantt  !== undefined) params = params.set('include_gantt',   String(options.includeGantt));
    if (options?.includeBudget !== undefined) params = params.set('include_budget',  String(options.includeBudget));
    return this.http.get(
      `${this.baseUrl}/${proyectoId}/export/pdf/`,
      { responseType: 'blob', params },
    );
  }

  // ── Plantillas de Proyecto ────────────────────────────────────────────────

  getTemplates(): Observable<PlantillaProyecto[]> {
    return this.http.get<PlantillaProyecto[]>(`${this.baseUrl}/templates/`);
  }

  createFromTemplate(data: CreateFromTemplateRequest): Observable<ProyectoDetail> {
    return this.http.post<ProyectoDetail>(`${this.baseUrl}/create-from-template/`, data);
  }

  createTemplate(data: PlantillaProyectoCreate): Observable<PlantillaProyecto> {
    return this.http.post<PlantillaProyecto>(`${this.baseUrl}/templates/create/`, data);
  }

  getTemplateDetail(id: string): Observable<PlantillaProyecto> {
    return this.http.get<PlantillaProyecto>(`${this.baseUrl}/templates/${id}/`);
  }

  updateTemplate(id: string, data: PlantillaProyectoCreate): Observable<PlantillaProyecto> {
    return this.http.patch<PlantillaProyecto>(`${this.baseUrl}/templates/${id}/update/`, data);
  }

  deleteTemplate(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/templates/${id}/delete/`);
  }

  // ── Importación Excel ─────────────────────────────────────────────────────

  importFromExcel(formData: FormData): Observable<ImportExcelResult> {
    return this.http.post<ImportExcelResult>(`${this.baseUrl}/import-from-excel/`, formData);
  }

  downloadExcelTemplate(): Observable<Blob> {
    return this.http.get(`${this.baseUrl}/download-excel-template/`, { responseType: 'blob' });
  }
}
