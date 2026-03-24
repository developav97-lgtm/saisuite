import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';
import {
  ActividadSaiopen,
  ActividadSaiopenDetail,
  ActividadSaiopenCreateDTO,
  ActividadSaiopenUpdateDTO,
} from '../models/actividad-saiopen.model';

interface Paginated<T> { results: T[]; count: number; }

@Injectable({ providedIn: 'root' })
export class ActividadSaiopenService {
  private readonly http   = inject(HttpClient);
  private readonly apiUrl = `${environment.apiUrl}/proyectos/actividades-saiopen`;

  listar(search?: string): Observable<ActividadSaiopen[]> {
    let params = new HttpParams();
    if (search) params = params.set('search', search);
    return this.http.get<Paginated<ActividadSaiopen>>(`${this.apiUrl}/`, { params }).pipe(
      map(r => r.results),
    );
  }

  obtener(id: string): Observable<ActividadSaiopenDetail> {
    return this.http.get<ActividadSaiopenDetail>(`${this.apiUrl}/${id}/`);
  }

  crear(data: ActividadSaiopenCreateDTO): Observable<ActividadSaiopenDetail> {
    return this.http.post<ActividadSaiopenDetail>(`${this.apiUrl}/`, data);
  }

  actualizar(id: string, data: ActividadSaiopenUpdateDTO): Observable<ActividadSaiopenDetail> {
    return this.http.patch<ActividadSaiopenDetail>(`${this.apiUrl}/${id}/`, data);
  }

  eliminar(id: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${id}/`);
  }
}
