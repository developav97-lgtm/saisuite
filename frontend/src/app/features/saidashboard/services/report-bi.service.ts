import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import {
  ReportBIListItem,
  ReportBIDetail,
  ReportBICreateRequest,
  ReportBIUpdateRequest,
  ReportBIExecuteRequest,
  ReportBIExecuteResult,
  ReportBIShareRequest,
  ReportBIShare,
  BISuggestResult,
  ReportBIDuplicateRequest,
  ReportBIGalleryGroup,
  StaticTemplate,
} from '../models/report-bi.model';
import { BIFieldCategory, BIFilterDef, BIJoinInfo } from '../models/bi-field.model';

@Injectable({ providedIn: 'root' })
export class ReportBIService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/dashboard/reportes';

  // ── CRUD ───────────────────────────────────────────────────────

  list(): Observable<ReportBIListItem[]> {
    return this.http.get<ReportBIListItem[]>(`${this.baseUrl}/`);
  }

  getById(id: string): Observable<ReportBIDetail> {
    return this.http.get<ReportBIDetail>(`${this.baseUrl}/${id}/`);
  }

  create(data: ReportBICreateRequest): Observable<ReportBIDetail> {
    return this.http.post<ReportBIDetail>(`${this.baseUrl}/`, data);
  }

  update(id: string, data: ReportBIUpdateRequest): Observable<ReportBIDetail> {
    return this.http.put<ReportBIDetail>(`${this.baseUrl}/${id}/`, data);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${id}/`);
  }

  // ── Acciones ─────��─────────────────────────────────────────────

  execute(id: string): Observable<ReportBIExecuteResult> {
    return this.http.post<ReportBIExecuteResult>(`${this.baseUrl}/${id}/execute/`, {});
  }

  preview(data: ReportBIExecuteRequest): Observable<ReportBIExecuteResult> {
    return this.http.post<ReportBIExecuteResult>(`${this.baseUrl}/preview/`, data);
  }

  toggleFavorite(id: string): Observable<{ es_favorito: boolean }> {
    return this.http.post<{ es_favorito: boolean }>(`${this.baseUrl}/${id}/toggle-favorite/`, {});
  }

  // ── Share ────��─────────────────────────────────────────────────

  share(id: string, data: ReportBIShareRequest): Observable<ReportBIShare> {
    return this.http.post<ReportBIShare>(`${this.baseUrl}/${id}/share/`, data);
  }

  revokeShare(id: string, userId: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${id}/share/${userId}/`);
  }

  // ── Export ──────────────────────────────────────────────────

  exportPdf(id: string): Observable<Blob> {
    return this.http.post(`${this.baseUrl}/${id}/export-pdf/`, {}, {
      responseType: 'blob',
    });
  }

  // ── Users (for share dialog) ────────────────────────────

  suggestReport(question: string): Observable<BISuggestResult> {
    return this.http.post<BISuggestResult>(
      '/api/v1/dashboard/cfo-virtual/suggest-report/',
      { question },
    );
  }

  getCompanyUsers(): Observable<{ id: string; email: string; full_name: string }[]> {
    return this.http.get<{ results: { id: string; email: string; full_name: string }[] }>(
      '/api/v1/auth/users/',
      { params: new HttpParams().set('page_size', '200') },
    ).pipe(
      map(res => res.results),
    );
  }

  // ── Metadata ──────���────────────────────────────────────────────

  getTemplates(): Observable<ReportBIListItem[]> {
    return this.http.get<ReportBIListItem[]>(`${this.baseUrl}/templates/`);
  }

  /** Catálogo estático del sistema — global, sin seeding por empresa. */
  getStaticCatalog(): Observable<StaticTemplate[]> {
    return this.http.get<StaticTemplate[]>(`${this.baseUrl}/catalogo/`);
  }


  getSources(): Observable<{ code: string; label: string; description: string; icon: string }[]> {
    return this.http.get<{ code: string; label: string; description: string; icon: string }[]>(
      `${this.baseUrl}/meta/sources/`,
    );
  }

  getFields(source: string): Observable<Record<string, BIFieldCategory['fields']>> {
    const params = new HttpParams().set('source', source);
    return this.http.get<Record<string, BIFieldCategory['fields']>>(
      `${this.baseUrl}/meta/fields/`,
      { params },
    );
  }

  getFilters(source: string): Observable<BIFilterDef[]> {
    const params = new HttpParams().set('source', source);
    return this.http.get<BIFilterDef[]>(`${this.baseUrl}/meta/filters/`, { params });
  }

  getJoins(): Observable<BIJoinInfo[]> {
    return this.http.get<BIJoinInfo[]>(`${this.baseUrl}/meta/joins/`);
  }

  duplicate(id: string, data: ReportBIDuplicateRequest): Observable<ReportBIDetail> {
    return this.http.post<ReportBIDetail>(`${this.baseUrl}/${id}/duplicate/`, data);
  }

  // ── Opciones de filtros ──────────────────────────────────────

  private readonly filtersBase = '/api/v1/dashboard/filters';

  getFilterPeriodos(): Observable<{ periodo: string }[]> {
    return this.http.get<{ periodo: string }[]>(`${this.filtersBase}/periodos/`);
  }

  getFilterTerceros(q: string): Observable<{ id: string; nombre: string; identificacion?: string }[]> {
    const params = new HttpParams().set('q', q);
    return this.http.get<{ id: string; nombre: string; identificacion?: string }[]>(
      `${this.filtersBase}/terceros/`,
      { params },
    );
  }

  getFilterProyectos(): Observable<{ proyecto_codigo: string; proyecto_nombre: string }[]> {
    return this.http.get<{ proyecto_codigo: string; proyecto_nombre: string }[]>(
      `${this.filtersBase}/proyectos/`,
    );
  }

  getFilterDepartamentos(): Observable<{ departamento_codigo: string; departamento_nombre: string }[]> {
    return this.http.get<{ departamento_codigo: string; departamento_nombre: string }[]>(
      `${this.filtersBase}/departamentos/`,
    );
  }

  getFilterCentrosCosto(): Observable<{ centro_costo_codigo: number | string; centro_costo_nombre?: string }[]> {
    return this.http.get<{ centro_costo_codigo: number | string; centro_costo_nombre?: string }[]>(
      `${this.filtersBase}/centros-costo/`,
    );
  }

  getFilterTiposDoc(source: string): Observable<{ tipo: string }[]> {
    const params = new HttpParams().set('source', source);
    return this.http.get<{ tipo: string }[]>(`${this.filtersBase}/tipos-doc/`, { params });
  }

  getFilterActividades(): Observable<{ actividad_codigo: string }[]> {
    return this.http.get<{ actividad_codigo: string }[]>(`${this.filtersBase}/actividades/`);
  }
}
