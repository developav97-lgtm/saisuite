/**
 * SaiSuite — TareaService
 * Consume la API REST de tareas en /api/v1/proyectos/tareas/
 */
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { PaginatedResponse } from '../models/paginated-response.model';
import {
  Tarea,
  TareaCreateDTO,
  TareaUpdateDTO,
  TareaFilters,
  FollowerResponse,
} from '../models/tarea.model';

@Injectable({ providedIn: 'root' })
export class TareaService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/proyectos/tareas';

  /**
   * Construye HttpParams a partir de los filtros, omitiendo valores vacíos.
   */
  private buildParams(filters?: TareaFilters): HttpParams {
    let params = new HttpParams();
    if (!filters) return params;

    (Object.keys(filters) as (keyof TareaFilters)[]).forEach(key => {
      const value = filters[key];
      if (value !== undefined && value !== null && value !== '') {
        params = params.set(key, String(value));
      }
    });

    return params;
  }

  /**
   * GET /api/v1/proyectos/tareas/
   * Soporta todos los filtros de TareaFilters (incluyendo proyecto=<id>).
   * El backend devuelve PaginatedResponse<Tarea>; se extrae results automáticamente.
   */
  list(filters?: TareaFilters): Observable<Tarea[]> {
    return this.http.get<PaginatedResponse<Tarea>>(`${this.baseUrl}/`, {
      params: this.buildParams(filters),
    }).pipe(map(r => r.results));
  }

  /**
   * Atajo: listar tareas de un proyecto específico.
   */
  listByProyecto(proyectoId: string, filters?: TareaFilters): Observable<Tarea[]> {
    return this.list({ ...filters, proyecto: proyectoId });
  }

  /**
   * GET /api/v1/proyectos/tareas/{id}/
   */
  getById(id: string): Observable<Tarea> {
    return this.http.get<Tarea>(`${this.baseUrl}/${id}/`);
  }

  /**
   * POST /api/v1/proyectos/tareas/
   */
  create(data: TareaCreateDTO): Observable<Tarea> {
    return this.http.post<Tarea>(`${this.baseUrl}/`, data);
  }

  /**
   * PATCH /api/v1/proyectos/tareas/{id}/
   */
  update(id: string, data: TareaUpdateDTO): Observable<Tarea> {
    return this.http.patch<Tarea>(`${this.baseUrl}/${id}/`, data);
  }

  /**
   * DELETE /api/v1/proyectos/tareas/{id}/
   */
  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${id}/`);
  }

  /**
   * POST /api/v1/proyectos/tareas/{id}/agregar-follower/
   */
  agregarFollower(tareaId: string, userId: string): Observable<FollowerResponse> {
    return this.http.post<FollowerResponse>(
      `${this.baseUrl}/${tareaId}/agregar-follower/`,
      { user_id: userId }
    );
  }

  /**
   * DELETE /api/v1/proyectos/tareas/{id}/quitar-follower/{user_id}/
   */
  quitarFollower(tareaId: string, userId: string): Observable<FollowerResponse> {
    return this.http.delete<FollowerResponse>(
      `${this.baseUrl}/${tareaId}/quitar-follower/${userId}/`
    );
  }

  /**
   * POST /api/v1/proyectos/tareas/{id}/cambiar-estado/
   */
  cambiarEstado(tareaId: string, estado: string): Observable<Tarea> {
    return this.http.post<Tarea>(
      `${this.baseUrl}/${tareaId}/cambiar-estado/`,
      { estado }
    );
  }

  // ── Atajos semánticos ──────────────────────────────────────────────────────

  getMisTareas(filters?: TareaFilters): Observable<Tarea[]> {
    return this.list({ ...filters, solo_mis_tareas: true });
  }

  getVencidas(filters?: TareaFilters): Observable<Tarea[]> {
    return this.list({ ...filters, vencidas: true });
  }

  getSubtareas(tareaPadreId: string): Observable<Tarea[]> {
    return this.list({ tarea_padre: tareaPadreId });
  }

  /**
   * POST /api/v1/proyectos/tareas/{id}/agregar-horas/
   * Suma horas trabajadas manualmente a horas_registradas.
   */
  agregarHoras(tareaId: string, horas: number): Observable<Tarea> {
    return this.http.post<Tarea>(
      `${this.baseUrl}/${tareaId}/agregar-horas/`,
      { horas },
    );
  }

  /**
   * POST /api/v1/proyectos/tareas/{id}/agregar-cantidad/
   * Suma cantidad ejecutada manualmente a cantidad_registrada.
   */
  agregarCantidad(tareaId: string, cantidad: number): Observable<Tarea> {
    return this.http.post<Tarea>(
      `${this.baseUrl}/${tareaId}/agregar-cantidad/`,
      { cantidad },
    );
  }
}
