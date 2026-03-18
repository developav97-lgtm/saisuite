import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { DocumentoContableList, DocumentoContableDetail } from '../models/documento-contable.model';

@Injectable({ providedIn: 'root' })
export class DocumentoContableService {
  private readonly http = inject(HttpClient);

  private url(proyectoId: string): string {
    return `/api/v1/proyectos/${proyectoId}/documentos`;
  }

  list(proyectoId: string, faseId?: string | null): Observable<DocumentoContableList[]> {
    let params = new HttpParams();
    if (faseId) params = params.set('fase', faseId);
    return this.http.get<DocumentoContableList[]>(`${this.url(proyectoId)}/`, { params });
  }

  getById(proyectoId: string, documentoId: string): Observable<DocumentoContableDetail> {
    return this.http.get<DocumentoContableDetail>(`${this.url(proyectoId)}/${documentoId}/`);
  }
}
