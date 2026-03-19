import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { Hito, HitoCreate } from '../models/hito.model';

interface Paginated<T> { count: number; next: string | null; previous: string | null; results: T[]; }

@Injectable({ providedIn: 'root' })
export class HitoService {
  private readonly http = inject(HttpClient);

  private url(proyectoId: string): string {
    return `/api/v1/proyectos/${proyectoId}/hitos`;
  }

  list(proyectoId: string): Observable<Hito[]> {
    return this.http
      .get<Paginated<Hito> | Hito[]>(`${this.url(proyectoId)}/`)
      .pipe(map(r => (r as Paginated<Hito>).results ?? (r as Hito[])));
  }

  create(proyectoId: string, data: HitoCreate): Observable<Hito> {
    return this.http.post<Hito>(`${this.url(proyectoId)}/`, data);
  }

  generarFactura(proyectoId: string, hitoId: string): Observable<Hito> {
    return this.http.post<Hito>(
      `${this.url(proyectoId)}/${hitoId}/generar-factura/`,
      { confirmar: true }
    );
  }
}
