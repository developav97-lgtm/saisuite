/**
 * SaiSuite — ResourceService (Feature #4)
 * Comunicación con los endpoints de Resource Management.
 */
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  ResourceAssignmentList,
  ResourceAssignmentDetail,
  ResourceAssignmentCreate,
  ResourceCapacity,
  ResourceCapacityCreate,
  ResourceAvailability,
  ResourceAvailabilityCreate,
  OverallocationResult,
  UserWorkload,
  TeamAvailabilityUser,
  UserCalendar,
} from '../models/resource.model';

@Injectable({ providedIn: 'root' })
export class ResourceService {
  private readonly http    = inject(HttpClient);
  private readonly baseUrl = '/api/v1/projects';

  // ── Assignments ──────────────────────────────────────────────────────────

  listAssignments(tareaId: string): Observable<ResourceAssignmentList[]> {
    return this.http.get<ResourceAssignmentList[]>(
      `${this.baseUrl}/tasks/${tareaId}/assignments/`
    );
  }

  createAssignment(
    tareaId: string,
    data: ResourceAssignmentCreate
  ): Observable<ResourceAssignmentDetail> {
    return this.http.post<ResourceAssignmentDetail>(
      `${this.baseUrl}/tasks/${tareaId}/assignments/`,
      data
    );
  }

  getAssignment(tareaId: string, id: string): Observable<ResourceAssignmentDetail> {
    return this.http.get<ResourceAssignmentDetail>(
      `${this.baseUrl}/tasks/${tareaId}/assignments/${id}/`
    );
  }

  deleteAssignment(tareaId: string, id: string): Observable<void> {
    return this.http.delete<void>(
      `${this.baseUrl}/tasks/${tareaId}/assignments/${id}/`
    );
  }

  checkOverallocation(
    tareaId: string,
    usuarioId: string,
    startDate: string,
    endDate: string,
    threshold?: string
  ): Observable<OverallocationResult> {
    let params = new HttpParams()
      .set('usuario_id', usuarioId)
      .set('start_date', startDate)
      .set('end_date', endDate);
    if (threshold) params = params.set('threshold', threshold);
    return this.http.get<OverallocationResult>(
      `${this.baseUrl}/tasks/${tareaId}/assignments/check-overallocation/`,
      { params }
    );
  }

  // ── Capacity ─────────────────────────────────────────────────────────────

  listCapacities(usuarioId?: string): Observable<ResourceCapacity[]> {
    let params = new HttpParams();
    if (usuarioId) params = params.set('usuario_id', usuarioId);
    return this.http.get<ResourceCapacity[]>(
      `${this.baseUrl}/resources/capacity/`, { params }
    );
  }

  createCapacity(data: ResourceCapacityCreate): Observable<ResourceCapacity> {
    return this.http.post<ResourceCapacity>(
      `${this.baseUrl}/resources/capacity/`, data
    );
  }

  updateCapacity(id: string, data: Partial<ResourceCapacityCreate>): Observable<ResourceCapacity> {
    return this.http.patch<ResourceCapacity>(
      `${this.baseUrl}/resources/capacity/${id}/`, data
    );
  }

  deleteCapacity(id: string): Observable<void> {
    return this.http.delete<void>(
      `${this.baseUrl}/resources/capacity/${id}/`
    );
  }

  // ── Availability (ausencias) ──────────────────────────────────────────────

  listAvailabilities(params: {
    usuarioId?: string;
    aprobado?: boolean;
    tipo?: string;
  } = {}): Observable<ResourceAvailability[]> {
    let httpParams = new HttpParams();
    if (params.usuarioId)              httpParams = httpParams.set('usuario_id', params.usuarioId);
    if (params.aprobado !== undefined)  httpParams = httpParams.set('aprobado', String(params.aprobado));
    if (params.tipo)                    httpParams = httpParams.set('tipo', params.tipo);
    return this.http.get<ResourceAvailability[]>(
      `${this.baseUrl}/resources/availability/`, { params: httpParams }
    );
  }

  createAvailability(data: ResourceAvailabilityCreate): Observable<ResourceAvailability> {
    return this.http.post<ResourceAvailability>(
      `${this.baseUrl}/resources/availability/`, data
    );
  }

  deleteAvailability(id: string): Observable<void> {
    return this.http.delete<void>(
      `${this.baseUrl}/resources/availability/${id}/`
    );
  }

  approveAvailability(id: string, aprobar: boolean): Observable<ResourceAvailability> {
    return this.http.post<ResourceAvailability>(
      `${this.baseUrl}/resources/availability/${id}/approve/`,
      { aprobar }
    );
  }

  // ── Workload ──────────────────────────────────────────────────────────────

  getWorkload(
    usuarioId: string,
    startDate: string,
    endDate: string
  ): Observable<UserWorkload> {
    const params = new HttpParams()
      .set('usuario_id', usuarioId)
      .set('start_date', startDate)
      .set('end_date', endDate);
    return this.http.get<UserWorkload>(
      `${this.baseUrl}/resources/workload/`, { params }
    );
  }

  // ── Team availability timeline ────────────────────────────────────────────

  getTeamTimeline(
    proyectoId: string,
    startDate: string,
    endDate: string
  ): Observable<TeamAvailabilityUser[]> {
    const params = new HttpParams()
      .set('start_date', startDate)
      .set('end_date', endDate);
    return this.http.get<TeamAvailabilityUser[]>(
      `${this.baseUrl}/${proyectoId}/team-availability/`, { params }
    );
  }

  // ── User calendar ─────────────────────────────────────────────────────────

  getUserCalendar(
    usuarioId: string,
    startDate: string,
    endDate: string
  ): Observable<UserCalendar> {
    const params = new HttpParams()
      .set('usuario_id', usuarioId)
      .set('start_date', startDate)
      .set('end_date', endDate);
    return this.http.get<UserCalendar>(
      `${this.baseUrl}/resources/calendar/`, { params }
    );
  }
}
