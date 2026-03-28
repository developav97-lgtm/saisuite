// SaiSuite — Feature #6: Advanced Scheduling
// SK-34 — baseline.service.ts
// Cubre: create, list, get, delete, compare baselines

import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  ProjectBaselineList,
  ProjectBaselineDetail,
  CreateBaselineRequest,
  BaselineComparison,
} from '../models/baseline.model';

@Injectable({ providedIn: 'root' })
export class BaselineService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/projects';

  // ── Listar ─────────────────────────────────────────────────────────────────

  /**
   * SK-21-08 — Listar todos los baselines de un proyecto.
   * GET /api/v1/projects/{projectId}/baselines/
   */
  list(projectId: string): Observable<ProjectBaselineList[]> {
    return this.http.get<ProjectBaselineList[]>(
      `${this.baseUrl}/${projectId}/baselines/`
    );
  }

  // ── Crear ──────────────────────────────────────────────────────────────────

  /**
   * SK-21-09 — Crear un snapshot de baseline del estado actual.
   * POST /api/v1/projects/{projectId}/baselines/
   */
  create(
    projectId: string,
    request: CreateBaselineRequest
  ): Observable<ProjectBaselineDetail> {
    return this.http.post<ProjectBaselineDetail>(
      `${this.baseUrl}/${projectId}/baselines/`,
      request
    );
  }

  // ── Detalle ────────────────────────────────────────────────────────────────

  /**
   * SK-21-10 — Obtener el detalle completo de un baseline (incluye snapshots JSON).
   * GET /api/v1/projects/baselines/{baselineId}/
   */
  get(baselineId: string): Observable<ProjectBaselineDetail> {
    return this.http.get<ProjectBaselineDetail>(
      `${this.baseUrl}/baselines/${baselineId}/`
    );
  }

  // ── Eliminar ───────────────────────────────────────────────────────────────

  /**
   * SK-21-12 — Eliminar un baseline (no se puede eliminar el activo).
   * DELETE /api/v1/projects/baselines/{baselineId}/
   */
  delete(baselineId: string): Observable<void> {
    return this.http.delete<void>(
      `${this.baseUrl}/baselines/${baselineId}/`
    );
  }

  // ── Comparar ───────────────────────────────────────────────────────────────

  /**
   * SK-21-11 — Comparar el plan actual vs un baseline guardado.
   * GET /api/v1/projects/baselines/{baselineId}/compare/
   */
  compare(baselineId: string): Observable<BaselineComparison> {
    return this.http.get<BaselineComparison>(
      `${this.baseUrl}/baselines/${baselineId}/compare/`
    );
  }
}
