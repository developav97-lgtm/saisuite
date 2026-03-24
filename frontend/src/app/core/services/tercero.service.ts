/**
 * SaiSuite — TerceroService (TRANSVERSAL)
 * Service global para el catálogo de terceros. Compartido entre todos los módulos.
 * API: /api/v1/terceros/
 */
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { TerceroList, TerceroDetail, TerceroCreate, TerceroDireccion } from '../models/tercero.model';

export interface PagedResponse<T> {
  count:   number;
  results: T[];
}

export interface TerceroListParams {
  search?:             string;
  tipo_tercero?:       string;
  tipo_identificacion?: string;
  activo?:             boolean;
  page?:               number;
  page_size?:          number;
}

@Injectable({ providedIn: 'root' })
export class TerceroService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = '/api/v1/terceros';

  list(params: TerceroListParams = {}): Observable<PagedResponse<TerceroList>> {
    let httpParams = new HttpParams();
    if (params.search)              httpParams = httpParams.set('search',              params.search);
    if (params.tipo_tercero)        httpParams = httpParams.set('tipo_tercero',        params.tipo_tercero);
    if (params.tipo_identificacion) httpParams = httpParams.set('tipo_identificacion', params.tipo_identificacion);
    if (params.activo !== undefined) httpParams = httpParams.set('activo',             String(params.activo));
    if (params.page)                httpParams = httpParams.set('page',                String(params.page));
    if (params.page_size)           httpParams = httpParams.set('page_size',           String(params.page_size));

    return this.http.get<PagedResponse<TerceroList>>(`${this.apiUrl}/`, { params: httpParams });
  }

  /** Para selects/autocompletes que necesitan el array directo. */
  listAll(params: Omit<TerceroListParams, 'page' | 'page_size'> = {}): Observable<TerceroList[]> {
    return this.list({ ...params, page_size: 1000 }).pipe(map(r => r.results));
  }

  get(id: string): Observable<TerceroDetail> {
    return this.http.get<TerceroDetail>(`${this.apiUrl}/${id}/`);
  }

  create(data: TerceroCreate): Observable<TerceroDetail> {
    return this.http.post<TerceroDetail>(`${this.apiUrl}/`, data);
  }

  update(id: string, data: Partial<TerceroCreate>): Observable<TerceroDetail> {
    return this.http.patch<TerceroDetail>(`${this.apiUrl}/${id}/`, data);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${id}/`);
  }

  addDireccion(terceroId: string, data: Partial<TerceroDireccion>): Observable<TerceroDireccion> {
    return this.http.post<TerceroDireccion>(`${this.apiUrl}/${terceroId}/direcciones/crear/`, data);
  }

  updateDireccion(terceroId: string, dirId: string, data: Partial<TerceroDireccion>): Observable<TerceroDireccion> {
    return this.http.patch<TerceroDireccion>(`${this.apiUrl}/${terceroId}/direcciones/${dirId}/`, data);
  }

  deleteDireccion(terceroId: string, dirId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${terceroId}/direcciones/${dirId}/eliminar/`);
  }
}
