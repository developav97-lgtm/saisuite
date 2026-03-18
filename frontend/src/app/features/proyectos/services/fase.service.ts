import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { FaseList, FaseDetail, FaseCreate } from '../models/fase.model';

@Injectable({ providedIn: 'root' })
export class FaseService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/proyectos';

  listByProyecto(proyectoId: string): Observable<FaseList[]> {
    return this.http.get<FaseList[]>(`${this.baseUrl}/${proyectoId}/fases/`);
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
}
