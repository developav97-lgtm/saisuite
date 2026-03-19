import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { ActividadProyecto, ActividadProyectoCreate } from '../models/actividad.model';

interface Paginated<T> { count: number; next: string | null; previous: string | null; results: T[]; }

@Injectable({ providedIn: 'root' })
export class ActividadProyectoService {
  private readonly http    = inject(HttpClient);
  private readonly baseUrl = '/api/v1/proyectos';

  listByProyecto(proyectoId: string, faseId?: string): Observable<ActividadProyecto[]> {
    let url = `${this.baseUrl}/${proyectoId}/actividades/`;
    if (faseId) url += `?fase=${faseId}`;
    return this.http
      .get<Paginated<ActividadProyecto> | ActividadProyecto[]>(url)
      .pipe(map(r => (r as Paginated<ActividadProyecto>).results ?? (r as ActividadProyecto[])));
  }

  asignar(proyectoId: string, data: ActividadProyectoCreate): Observable<ActividadProyecto> {
    return this.http.post<ActividadProyecto>(`${this.baseUrl}/${proyectoId}/actividades/`, data);
  }

  update(proyectoId: string, apId: string, data: Partial<ActividadProyectoCreate>): Observable<ActividadProyecto> {
    return this.http.patch<ActividadProyecto>(`${this.baseUrl}/${proyectoId}/actividades/${apId}/`, data);
  }

  desasignar(proyectoId: string, apId: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${proyectoId}/actividades/${apId}/`);
  }
}
