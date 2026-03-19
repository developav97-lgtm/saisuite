import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { TerceroProyecto, TerceroProyectoCreate } from '../models/tercero-proyecto.model';

interface Paginated<T> { count: number; next: string | null; previous: string | null; results: T[]; }

@Injectable({ providedIn: 'root' })
export class TerceroProyectoService {
  private readonly http = inject(HttpClient);

  private url(proyectoId: string): string {
    return `/api/v1/proyectos/${proyectoId}/terceros`;
  }

  list(proyectoId: string): Observable<TerceroProyecto[]> {
    return this.http
      .get<Paginated<TerceroProyecto> | TerceroProyecto[]>(`${this.url(proyectoId)}/`)
      .pipe(map(r => (r as Paginated<TerceroProyecto>).results ?? (r as TerceroProyecto[])));
  }

  vincular(proyectoId: string, data: TerceroProyectoCreate): Observable<TerceroProyecto> {
    return this.http.post<TerceroProyecto>(`${this.url(proyectoId)}/`, data);
  }

  desvincular(proyectoId: string, terceroId: string): Observable<void> {
    return this.http.delete<void>(`${this.url(proyectoId)}/${terceroId}/`);
  }
}
