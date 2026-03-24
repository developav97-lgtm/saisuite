import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { FaseList, FaseDetail, FaseCreate } from '../models/fase.model';

interface Paginated<T> { count: number; next: string | null; previous: string | null; results: T[]; }

@Injectable({ providedIn: 'root' })
export class FaseService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/proyectos';

  listByProyecto(proyectoId: string): Observable<FaseList[]> {
    return this.http
      .get<Paginated<FaseList> | FaseList[]>(`${this.baseUrl}/${proyectoId}/fases/`)
      .pipe(map(r => (r as Paginated<FaseList>).results ?? (r as FaseList[])));
  }

  getById(faseId: string): Observable<FaseDetail> {
    return this.http.get<FaseDetail>(`${this.baseUrl}/fases/${faseId}/`);
  }

  create(proyectoId: string, data: FaseCreate): Observable<FaseDetail> {
    return this.http.post<FaseDetail>(`${this.baseUrl}/${proyectoId}/fases/`, data);
  }

  update(faseId: string, data: Partial<FaseCreate>): Observable<FaseDetail> {
    return this.http.patch<FaseDetail>(`${this.baseUrl}/fases/${faseId}/`, data);
  }

  delete(faseId: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/fases/${faseId}/`);
  }

  activar(faseId: string): Observable<FaseDetail> {
    return this.http.post<FaseDetail>(`${this.baseUrl}/fases/${faseId}/activar/`, {});
  }

  completar(faseId: string): Observable<FaseDetail> {
    return this.http.post<FaseDetail>(`${this.baseUrl}/fases/${faseId}/completar/`, {});
  }
}
