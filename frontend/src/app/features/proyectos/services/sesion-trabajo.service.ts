/**
 * SaiSuite — SesionTrabajoService
 * Consume los endpoints de cronómetro en /api/v1/projects/tasks/
 */
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { SesionTrabajo } from '../models/sesion-trabajo.model';

@Injectable({ providedIn: 'root' })
export class SesionTrabajoService {
  private readonly http   = inject(HttpClient);
  private readonly apiUrl = '/api/v1/projects/tasks';

  /** POST /tareas/{tareaId}/sesiones/iniciar/ */
  iniciar(tareaId: string): Observable<SesionTrabajo> {
    return this.http.post<SesionTrabajo>(
      `${this.apiUrl}/${tareaId}/sesiones/iniciar/`,
      {},
    );
  }

  /** POST /tareas/{tareaId}/sesiones/{sesionId}/pausar/ */
  pausar(tareaId: string, sesionId: string): Observable<SesionTrabajo> {
    return this.http.post<SesionTrabajo>(
      `${this.apiUrl}/${tareaId}/sesiones/${sesionId}/pausar/`,
      {},
    );
  }

  /** POST /tareas/{tareaId}/sesiones/{sesionId}/reanudar/ */
  reanudar(tareaId: string, sesionId: string): Observable<SesionTrabajo> {
    return this.http.post<SesionTrabajo>(
      `${this.apiUrl}/${tareaId}/sesiones/${sesionId}/reanudar/`,
      {},
    );
  }

  /** POST /tareas/{tareaId}/sesiones/{sesionId}/detener/ */
  detener(tareaId: string, sesionId: string, notas = ''): Observable<SesionTrabajo> {
    return this.http.post<SesionTrabajo>(
      `${this.apiUrl}/${tareaId}/sesiones/${sesionId}/detener/`,
      { notas },
    );
  }

  /** GET /tareas/{tareaId}/sesiones/ */
  listar(
    tareaId: string,
    filters?: { estado?: string; usuario?: string },
  ): Observable<SesionTrabajo[]> {
    let params = new HttpParams();
    if (filters?.estado)   params = params.set('estado',   filters.estado);
    if (filters?.usuario)  params = params.set('usuario',  filters.usuario);

    return this.http.get<SesionTrabajo[]>(
      `${this.apiUrl}/${tareaId}/sesiones/`,
      { params },
    );
  }

  /** GET /tareas/sesion-activa/ — para restaurar cronómetro al recargar */
  obtenerSesionActiva(): Observable<SesionTrabajo> {
    return this.http.get<SesionTrabajo>(
      `${this.apiUrl}/sesion-activa/`,
    );
  }
}
