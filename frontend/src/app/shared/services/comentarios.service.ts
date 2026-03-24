import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Comentario, ComentarioListResponse } from '../models/comentario.model';

export interface ComentarioFilters {
  content_type_model: string;
  object_id: string;
}

export interface CrearComentarioPayload {
  content_type_model: string;
  object_id: string;
  texto: string;
  padre?: string;
}

@Injectable({ providedIn: 'root' })
export class ComentariosService {
  private readonly http   = inject(HttpClient);
  private readonly apiUrl = `${environment.apiUrl}/notificaciones/comentarios`;

  listar(filters: ComentarioFilters): Observable<ComentarioListResponse> {
    const params = new HttpParams()
      .set('content_type_model', filters.content_type_model)
      .set('object_id', filters.object_id);
    return this.http.get<ComentarioListResponse>(`${this.apiUrl}/`, { params });
  }

  crear(data: CrearComentarioPayload): Observable<Comentario> {
    return this.http.post<Comentario>(`${this.apiUrl}/`, data);
  }

  editar(id: string, texto: string): Observable<Comentario> {
    return this.http.patch<Comentario>(`${this.apiUrl}/${id}/`, { texto });
  }

  eliminar(id: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${id}/`);
  }
}
