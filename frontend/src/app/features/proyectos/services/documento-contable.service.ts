import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { DocumentoContableList, DocumentoContableDetail } from '../models/documento-contable.model';

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
}
