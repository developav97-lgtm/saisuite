import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { TerceroProyecto, TerceroProyectoCreate } from '../models/tercero-proyecto.model';

@Injectable({ providedIn: 'root' })
export class TerceroProyectoService {
  private readonly http = inject(HttpClient);

  private url(proyectoId: string): string {
    return `/api/v1/proyectos/${proyectoId}/terceros`;
  }

  list(proyectoId: string): Observable<TerceroProyecto[]> {
    return this.http.get<TerceroProyecto[]>(`${this.url(proyectoId)}/`);
  }

  vincular(proyectoId: string, data: TerceroProyectoCreate): Observable<TerceroProyecto> {
    return this.http.post<TerceroProyecto>(`${this.url(proyectoId)}/`, data);
  }

  desvincular(proyectoId: string, terceroId: string): Observable<void> {
    return this.http.delete<void>(`${this.url(proyectoId)}/${terceroId}/`);
  }
}
