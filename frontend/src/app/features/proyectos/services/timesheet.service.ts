import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  TimesheetEntry,
  TimesheetEntryCreate,
  TimesheetFilters,
  SesionTrabajo,
} from '../models/timesheet.model';

@Injectable({ providedIn: 'root' })
export class TimesheetService {
  private readonly http      = inject(HttpClient);
  private readonly baseUrl   = '/api/v1/projects/timesheets';
  private readonly tareaBase = '/api/v1/projects/tasks';

  // ── Registro manual ────────────────────────────────────────────────────────

  list(filters: TimesheetFilters = {}): Observable<TimesheetEntry[]> {
    let params = new HttpParams();
    if (filters.tarea)        params = params.set('tarea', filters.tarea);
    if (filters.fecha_inicio) params = params.set('fecha_inicio', filters.fecha_inicio);
    if (filters.fecha_fin)    params = params.set('fecha_fin', filters.fecha_fin);
    if (filters.validado !== undefined)
      params = params.set('validado', String(filters.validado));
    return this.http.get<TimesheetEntry[]>(`${this.baseUrl}/`, { params });
  }

  create(data: TimesheetEntryCreate): Observable<TimesheetEntry> {
    return this.http.post<TimesheetEntry>(`${this.baseUrl}/`, data);
  }

  update(id: string, data: Partial<TimesheetEntryCreate>): Observable<TimesheetEntry> {
    return this.http.patch<TimesheetEntry>(`${this.baseUrl}/${id}/`, data);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${id}/`);
  }

  misHoras(fechaInicio: string, fechaFin: string): Observable<TimesheetEntry[]> {
    const params = new HttpParams()
      .set('fecha_inicio', fechaInicio)
      .set('fecha_fin', fechaFin);
    return this.http.get<TimesheetEntry[]>(`${this.baseUrl}/mis_horas/`, { params });
  }

  validar(entryId: string): Observable<TimesheetEntry> {
    return this.http.post<TimesheetEntry>(`${this.baseUrl}/${entryId}/validar/`, {});
  }

  // ── Timer (SesionTrabajo) ──────────────────────────────────────────────────

  iniciarSesion(tareaId: string): Observable<SesionTrabajo> {
    return this.http.post<SesionTrabajo>(
      `${this.tareaBase}/${tareaId}/sesiones/iniciar/`, {},
    );
  }

  pausarSesion(tareaId: string, sesionId: string): Observable<SesionTrabajo> {
    return this.http.post<SesionTrabajo>(
      `${this.tareaBase}/${tareaId}/sesiones/${sesionId}/pausar/`, {},
    );
  }

  reanudarSesion(tareaId: string, sesionId: string): Observable<SesionTrabajo> {
    return this.http.post<SesionTrabajo>(
      `${this.tareaBase}/${tareaId}/sesiones/${sesionId}/reanudar/`, {},
    );
  }

  detenerSesion(tareaId: string, sesionId: string, notas = ''): Observable<SesionTrabajo> {
    return this.http.post<SesionTrabajo>(
      `${this.tareaBase}/${tareaId}/sesiones/${sesionId}/detener/`,
      { notas },
    );
  }

  sesionActiva(): Observable<SesionTrabajo | null> {
    return this.http.get<SesionTrabajo | null>(
      `${this.tareaBase}/sesion-activa/`,
    );
  }

  listarSesiones(tareaId: string): Observable<SesionTrabajo[]> {
    return this.http.get<SesionTrabajo[]>(
      `${this.tareaBase}/${tareaId}/sesiones/`,
    );
  }
}
