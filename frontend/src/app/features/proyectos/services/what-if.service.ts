// SaiSuite — Feature #6: Advanced Scheduling
// SK-35 — what-if.service.ts
// Cubre: create, list, get, delete, run-simulation, compare scenarios

import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  WhatIfScenarioList,
  WhatIfScenarioDetail,
  CreateWhatIfScenarioRequest,
  ScenarioComparisonRow,
  CompareScenarioRequest,
} from '../models/what-if.model';

@Injectable({ providedIn: 'root' })
export class WhatIfService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/projects';

  // ── Listar ─────────────────────────────────────────────────────────────────

  /**
   * SK-21-13 — Listar todos los escenarios what-if de un proyecto.
   * GET /api/v1/projects/{projectId}/scenarios/
   */
  list(projectId: string): Observable<WhatIfScenarioList[]> {
    return this.http.get<WhatIfScenarioList[]>(
      `${this.baseUrl}/${projectId}/scenarios/`
    );
  }

  // ── Crear ──────────────────────────────────────────────────────────────────

  /**
   * SK-21-14 — Crear un nuevo escenario what-if con cambios propuestos.
   * POST /api/v1/projects/{projectId}/scenarios/
   * Debe incluir al menos un cambio (task_changes, resource_changes o dependency_changes).
   */
  create(
    projectId: string,
    request: CreateWhatIfScenarioRequest
  ): Observable<WhatIfScenarioDetail> {
    return this.http.post<WhatIfScenarioDetail>(
      `${this.baseUrl}/${projectId}/scenarios/`,
      request
    );
  }

  // ── Detalle ────────────────────────────────────────────────────────────────

  /**
   * SK-21-15 — Obtener el detalle completo de un escenario (con resultados de simulación).
   * GET /api/v1/projects/scenarios/{scenarioId}/
   */
  get(scenarioId: string): Observable<WhatIfScenarioDetail> {
    return this.http.get<WhatIfScenarioDetail>(
      `${this.baseUrl}/scenarios/${scenarioId}/`
    );
  }

  // ── Eliminar ───────────────────────────────────────────────────────────────

  /**
   * SK-21-17 — Eliminar un escenario what-if.
   * DELETE /api/v1/projects/scenarios/{scenarioId}/
   */
  delete(scenarioId: string): Observable<void> {
    return this.http.delete<void>(
      `${this.baseUrl}/scenarios/${scenarioId}/`
    );
  }

  // ── Ejecutar simulación ───────────────────────────────────────────────────

  /**
   * SK-21-16 — Ejecutar la simulación CPM del escenario. NO modifica datos reales.
   * Los resultados (simulated_end_date, critical_path, days_delta) se guardan en el escenario.
   * POST /api/v1/projects/scenarios/{scenarioId}/run-simulation/
   */
  runSimulation(scenarioId: string): Observable<WhatIfScenarioDetail> {
    return this.http.post<WhatIfScenarioDetail>(
      `${this.baseUrl}/scenarios/${scenarioId}/run-simulation/`,
      {}
    );
  }

  // ── Comparar escenarios ────────────────────────────────────────────────────

  /**
   * SK-21-18 — Tabla comparativa de múltiples escenarios (máx. 10).
   * POST /api/v1/projects/scenarios/compare/
   */
  compare(request: CompareScenarioRequest): Observable<ScenarioComparisonRow[]> {
    return this.http.post<ScenarioComparisonRow[]>(
      `${this.baseUrl}/scenarios/compare/`,
      request
    );
  }
}
