import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ActividadList, ActividadDetail, ActividadCreate, TipoActividad } from '../models/actividad.model';

interface Paginated<T> { count: number; next: string | null; previous: string | null; results: T[]; }

@Injectable({ providedIn: 'root' })
export class ActividadService {
  private readonly http    = inject(HttpClient);
  private readonly baseUrl = '/api/v1/proyectos/actividades';

  list(search?: string, tipo?: TipoActividad, page = 1, pageSize = 25): Observable<Paginated<ActividadList>> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString());
    if (search) params = params.set('search', search);
    if (tipo)   params = params.set('tipo', tipo);
    return this.http.get<Paginated<ActividadList>>(this.baseUrl + '/', { params });
  }

  getById(id: string): Observable<ActividadDetail> {
    return this.http.get<ActividadDetail>(`${this.baseUrl}/${id}/`);
  }

  create(data: ActividadCreate): Observable<ActividadDetail> {
    return this.http.post<ActividadDetail>(this.baseUrl + '/', data);
  }

  update(id: string, data: Partial<ActividadCreate>): Observable<ActividadDetail> {
    return this.http.patch<ActividadDetail>(`${this.baseUrl}/${id}/`, data);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${id}/`);
  }
}
