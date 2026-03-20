/**
 * SaiSuite — TerceroService (TRANSVERSAL)
 * Service global para el catálogo de terceros. Compartido entre todos los módulos.
 * API: /api/v1/terceros/
 */
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { TerceroList, TerceroDetail, TerceroCreate, TerceroDireccion } from '../models/tercero.model';

interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface TerceroListParams {
  search?: string;
  tipo_tercero?: string;
  activo?: boolean;
  page_size?: number;
}

@Injectable({ providedIn: 'root' })
export class TerceroService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = '/api/v1/terceros';

  list(params: TerceroListParams = {}): Observable<TerceroList[]> {
    const queryParams: Record<string, string> = {};
    if (params.search)       queryParams['search']       = params.search;
    if (params.tipo_tercero) queryParams['tipo_tercero'] = params.tipo_tercero;
    if (params.activo !== undefined) queryParams['activo'] = String(params.activo);
    if (params.page_size)    queryParams['page_size']    = String(params.page_size);

    return this.http
      .get<PaginatedResponse<TerceroList> | TerceroList[]>(`${this.apiUrl}/`, { params: queryParams })
      .pipe(
        map(r => (r as PaginatedResponse<TerceroList>).results ?? (r as TerceroList[])),
      );
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
