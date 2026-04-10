import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import {
  DocumentoContableList,
  DocumentoContableDetail,
  SyncDocumentosResult,
  LineaContable,
} from '../models/documento-contable.model';

interface Paginated<T> { count: number; next: string | null; previous: string | null; results: T[]; }

@Injectable({ providedIn: 'root' })
export class DocumentoContableService {
  private readonly http = inject(HttpClient);

  private url(proyectoId: string): string {
    return `/api/v1/projects/${proyectoId}/documents`;
  }

  list(proyectoId: string, faseId?: string | null): Observable<DocumentoContableList[]> {
    let params = new HttpParams();
    if (faseId) params = params.set('fase', faseId);
    return this.http
      .get<Paginated<DocumentoContableList> | DocumentoContableList[]>(`${this.url(proyectoId)}/`, { params })
      .pipe(map(r => (r as Paginated<DocumentoContableList>).results ?? (r as DocumentoContableList[])));
  }

  getById(proyectoId: string, documentoId: string): Observable<DocumentoContableDetail> {
    return this.http.get<DocumentoContableDetail>(`${this.url(proyectoId)}/${documentoId}/`);
  }

  /**
   * Sincroniza documentos del GL (MovimientoContable) para el proyecto.
   * Requiere que el proyecto esté vinculado a un ProyectoSaiopen.
   */
  sync(proyectoId: string): Observable<SyncDocumentosResult> {
    return this.http.post<SyncDocumentosResult>(`${this.url(proyectoId)}/sync/`, {});
  }

  /**
   * Retorna las líneas de asiento contable (MovimientoContable) para un documento.
   * Usa tipo_gl + batch_gl para identificar el documento en el GL.
   */
  getLineas(proyectoId: string, documentoId: string): Observable<LineaContable[]> {
    return this.http.get<LineaContable[]>(`${this.url(proyectoId)}/${documentoId}/lineas/`);
  }
}
