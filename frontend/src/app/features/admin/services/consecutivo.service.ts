import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ConsecutivoConfig, ConsecutivoCreate } from '../models/consecutivo.model';

@Injectable({ providedIn: 'root' })
export class ConsecutivoService {
  private readonly http    = inject(HttpClient);
  private readonly baseUrl = '/api/v1/core/consecutivos';

  list(): Observable<ConsecutivoConfig[]> {
    return this.http.get<ConsecutivoConfig[]>(`${this.baseUrl}/`);
  }

  create(data: ConsecutivoCreate): Observable<ConsecutivoConfig> {
    return this.http.post<ConsecutivoConfig>(`${this.baseUrl}/`, data);
  }

  update(id: string, data: Partial<ConsecutivoCreate>): Observable<ConsecutivoConfig> {
    return this.http.patch<ConsecutivoConfig>(`${this.baseUrl}/${id}/`, data);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${id}/`);
  }
}
