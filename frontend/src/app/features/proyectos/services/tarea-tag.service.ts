/**
 * SaiSuite — TareaTagService
 * Consume la API REST de tags en /api/v1/proyectos/tags/
 */
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { PaginatedResponse } from '../models/paginated-response.model';
import { TareaTag, TareaTagColor } from '../models/tarea.model';

export interface TareaTagCreateDTO {
  nombre: string;
  color: TareaTagColor;
}

@Injectable({ providedIn: 'root' })
export class TareaTagService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/proyectos/tags';

  /**
   * GET /api/v1/proyectos/tags/
   */
  list(): Observable<TareaTag[]> {
    return this.http.get<PaginatedResponse<TareaTag>>(`${this.baseUrl}/`).pipe(
      map(r => r.results),
    );
  }

  /**
   * POST /api/v1/proyectos/tags/
   */
  create(data: TareaTagCreateDTO): Observable<TareaTag> {
    return this.http.post<TareaTag>(`${this.baseUrl}/`, data);
  }

  /**
   * PATCH /api/v1/proyectos/tags/{id}/
   */
  update(id: string, data: Partial<TareaTagCreateDTO>): Observable<TareaTag> {
    return this.http.patch<TareaTag>(`${this.baseUrl}/${id}/`, data);
  }

  /**
   * DELETE /api/v1/proyectos/tags/{id}/
   */
  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${id}/`);
  }
}
