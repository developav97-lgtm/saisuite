import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface ProyectoSaiopenDisponible {
  codigo: string;
  nombre: string;
  descripcion?: string;
}

export interface VincularSaiopenResult {
  saiopen_proyecto_id: string;
}

export interface SyncActividadesResult {
  created: number;
  updated: number;
}

@Injectable({ providedIn: 'root' })
export class ProyectoSaiopenService {
  private readonly http = inject(HttpClient);

  getDisponibles(): Observable<ProyectoSaiopenDisponible[]> {
    return this.http.get<ProyectoSaiopenDisponible[]>('/api/v1/projects/saiopen/disponibles/');
  }

  vincular(proyectoId: string, saiopenCodigo: string): Observable<VincularSaiopenResult> {
    return this.http.post<VincularSaiopenResult>(
      `/api/v1/projects/${proyectoId}/vincular-saiopen/`,
      { saiopen_codigo: saiopenCodigo },
    );
  }

  desvincular(proyectoId: string): Observable<void> {
    return this.http.delete<void>(`/api/v1/projects/${proyectoId}/vincular-saiopen/`);
  }

  syncActividades(proyectoId: string): Observable<SyncActividadesResult> {
    return this.http.post<SyncActividadesResult>(
      `/api/v1/projects/${proyectoId}/sync-actividades/`,
      {},
    );
  }
}
