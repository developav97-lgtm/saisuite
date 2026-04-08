import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { KnowledgeIngestResult, KnowledgeSource } from '../models/admin.models';

@Injectable({ providedIn: 'root' })
export class KnowledgeBaseService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/ai/knowledge';

  listSources(): Observable<KnowledgeSource[]> {
    return this.http.get<KnowledgeSource[]>(`${this.baseUrl}/sources/`);
  }

  deleteSource(id: string): Observable<{ file_name: string; chunks_deleted: number }> {
    return this.http.delete<{ file_name: string; chunks_deleted: number }>(
      `${this.baseUrl}/sources/${id}/`,
    );
  }

  uploadFile(file: File, module: string, category: string): Observable<KnowledgeIngestResult> {
    const formData = new FormData();
    formData.append('file', file, file.name);
    if (module)   formData.append('module',   module);
    if (category) formData.append('category', category);
    return this.http.post<KnowledgeIngestResult>(`${this.baseUrl}/upload/`, formData);
  }

  reindex(): Observable<{ status: string; output: string }> {
    return this.http.post<{ status: string; output: string }>(
      `${this.baseUrl}/reindex/`,
      {},
    );
  }
}
