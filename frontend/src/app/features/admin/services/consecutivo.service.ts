import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { ConsecutivoConfig, ConsecutivoCreate, PagedResponse } from '../models/consecutivo.model';

export interface ConsecutivoParams {
  page?:      number;
  page_size?: number;
  search?:    string;
  tipo?:      string;
  activo?:    string;
}

@Injectable({ providedIn: 'root' })
export class ConsecutivoService {
  private readonly http    = inject(HttpClient);
  private readonly baseUrl = '/api/v1/core/consecutivos';

  list(params: ConsecutivoParams = {}): Observable<PagedResponse<ConsecutivoConfig>> {
    let httpParams = new HttpParams();
    if (params.page)      httpParams = httpParams.set('page',      String(params.page));
    if (params.page_size) httpParams = httpParams.set('page_size', String(params.page_size));
    if (params.search)    httpParams = httpParams.set('search',    params.search);
    if (params.tipo)      httpParams = httpParams.set('tipo',      params.tipo);
    if (params.activo !== undefined && params.activo !== '')
                          httpParams = httpParams.set('activo',    params.activo);
    return this.http.get<PagedResponse<ConsecutivoConfig>>(`${this.baseUrl}/`, { params: httpParams });
  }

  /** Devuelve todos los consecutivos sin paginación (para selects/dropdowns). */
  listAll(): Observable<ConsecutivoConfig[]> {
    return this.list({ page_size: 1000 }).pipe(map(r => r.results));
  }

  create(data: ConsecutivoCreate): Observable<ConsecutivoConfig> {
    return this.http.post<ConsecutivoConfig>(`${this.baseUrl}/`, data);
  }

  update(id: string, data: Partial<ConsecutivoCreate>): Observable<ConsecutivoConfig> {
    return this.http.patch<ConsecutivoConfig>(`${this.baseUrl}/${id}/`, data);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${id}/`);
  }
}
