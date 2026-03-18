import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Hito, HitoCreate } from '../models/hito.model';

@Injectable({ providedIn: 'root' })
export class HitoService {
  private readonly http = inject(HttpClient);

  private url(proyectoId: string): string {
    return `/api/v1/proyectos/${proyectoId}/hitos`;
  }

  list(proyectoId: string): Observable<Hito[]> {
    return this.http.get<Hito[]>(`${this.url(proyectoId)}/`);
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
