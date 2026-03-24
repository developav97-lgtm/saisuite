import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import {
  Notificacion,
  NotificacionItem,
  NotificacionListResponse,
  PreferenciaNotificacion,
} from '../../shared/models/notificacion.model';

export interface NotificacionFilters {
  leida?: boolean;
  tipo?: string;
  page?: number;
  page_size?: number;
}

@Injectable({ providedIn: 'root' })
export class NotificacionesService {
  private readonly http   = inject(HttpClient);
  private readonly apiUrl = `${environment.apiUrl}/notificaciones`;

  listar(filters?: NotificacionFilters): Observable<NotificacionListResponse> {
    let params = new HttpParams();
    if (filters?.leida !== undefined) params = params.set('leida', String(filters.leida));
    if (filters?.tipo)                params = params.set('tipo', filters.tipo);
    if (filters?.page)                params = params.set('page', String(filters.page));
    if (filters?.page_size)           params = params.set('page_size', String(filters.page_size));
    return this.http.get<NotificacionListResponse>(`${this.apiUrl}/`, { params });
  }

  contarSinLeer(): Observable<{ count: number }> {
    return this.http.get<{ count: number }>(`${this.apiUrl}/no-leidas/`);
  }

  marcarLeida(id: string): Observable<Notificacion> {
    return this.http.post<Notificacion>(`${this.apiUrl}/${id}/leer/`, {});
  }

  marcarTodasLeidas(): Observable<{ count: number }> {
    return this.http.post<{ count: number }>(`${this.apiUrl}/leer-todas/`, {});
  }

  marcarNoLeida(id: string): Observable<Notificacion> {
    return this.http.post<Notificacion>(`${this.apiUrl}/${id}/marcar-no-leida/`, {});
  }

  // ── C.1: Agrupadas ──────────────────────────────────────────────────────────
  listarAgrupadas(): Observable<NotificacionItem[]> {
    return this.http.get<NotificacionItem[]>(`${this.apiUrl}/agrupadas/`);
  }

  marcarGrupoLeidas(notificacionesIds: string[]): Observable<{ count: number }> {
    return this.http.post<{ count: number }>(
      `${this.apiUrl}/marcar-grupo-leidas/`,
      { notificaciones_ids: notificacionesIds },
    );
  }

  // ── C.2: Preferencias ───────────────────────────────────────────────────────
  obtenerPreferencias(): Observable<PreferenciaNotificacion[]> {
    return this.http.get<{ results: PreferenciaNotificacion[] } | PreferenciaNotificacion[]>(
      `${this.apiUrl}/preferencias/`,
    ).pipe(
      map(r => Array.isArray(r) ? r : r.results),
    );
  }

  actualizarPreferencia(
    tipo: string,
    datos: Partial<PreferenciaNotificacion>,
  ): Observable<PreferenciaNotificacion> {
    return this.http.patch<PreferenciaNotificacion>(
      `${this.apiUrl}/preferencias/${tipo}/`,
      datos,
    );
  }

  // ── C.3: Snooze ─────────────────────────────────────────────────────────────
  snooze(id: string, minutos: number): Observable<Notificacion> {
    return this.http.post<Notificacion>(`${this.apiUrl}/${id}/snooze/`, { minutos });
  }

  // ── C.4: Remind Me ──────────────────────────────────────────────────────────
  remindMe(id: string, minutos: number): Observable<Notificacion> {
    return this.http.post<Notificacion>(`${this.apiUrl}/${id}/remind-me/`, { minutos });
  }
}
