// SaiSuite — Feature #6: Advanced Scheduling
// SK-33 — scheduling.service.ts
// Cubre: auto-schedule, level-resources, critical-path, float, constraints

import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  AutoScheduleRequest,
  AutoScheduleResult,
  LevelResourcesRequest,
  LevelResourcesResult,
  CriticalPathResponse,
  FloatData,
  TaskConstraint,
  CreateTaskConstraintRequest,
} from '../models/scheduling.model';

@Injectable({ providedIn: 'root' })
export class SchedulingService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/projects';

  // ── Auto-Schedule ──────────────────────────────────────────────────────────

  /**
   * SK-21-01 — Reprogramar automáticamente todas las tareas del proyecto.
   * POST /api/v1/projects/{projectId}/scheduling/auto-schedule/
   */
  autoSchedule(
    projectId: string,
    request: AutoScheduleRequest = {}
  ): Observable<AutoScheduleResult> {
    return this.http.post<AutoScheduleResult>(
      `${this.baseUrl}/${projectId}/scheduling/auto-schedule/`,
      request
    );
  }

  // ── Resource Leveling ──────────────────────────────────────────────────────

  /**
   * SK-21-02 — Nivelar recursos del proyecto moviendo tareas con float > 0.
   * POST /api/v1/projects/{projectId}/scheduling/level-resources/
   */
  levelResources(
    projectId: string,
    request: LevelResourcesRequest = {}
  ): Observable<LevelResourcesResult> {
    return this.http.post<LevelResourcesResult>(
      `${this.baseUrl}/${projectId}/scheduling/level-resources/`,
      request
    );
  }

  // ── Critical Path ──────────────────────────────────────────────────────────

  /**
   * SK-21-03 — Obtener la ruta crítica del proyecto (cacheada 5 min en backend).
   * GET /api/v1/projects/{projectId}/scheduling/critical-path/
   */
  getCriticalPath(projectId: string): Observable<CriticalPathResponse> {
    return this.http.get<CriticalPathResponse>(
      `${this.baseUrl}/${projectId}/scheduling/critical-path/`
    );
  }

  // ── Task Float ─────────────────────────────────────────────────────────────

  /**
   * SK-21-04 — Holgura (float) de una tarea específica.
   * GET /api/v1/projects/tasks/{taskId}/scheduling/float/
   */
  getTaskFloat(taskId: string): Observable<FloatData> {
    return this.http.get<FloatData>(
      `${this.baseUrl}/tasks/${taskId}/scheduling/float/`
    );
  }

  // ── Task Constraints ───────────────────────────────────────────────────────

  /**
   * SK-21-05 — Listar restricciones de scheduling de una tarea.
   * GET /api/v1/projects/tasks/{taskId}/constraints/
   */
  getConstraints(taskId: string): Observable<TaskConstraint[]> {
    return this.http.get<TaskConstraint[]>(
      `${this.baseUrl}/tasks/${taskId}/constraints/`
    );
  }

  /**
   * SK-21-06 — Crear o actualizar una restricción de scheduling.
   * POST /api/v1/projects/tasks/{taskId}/constraints/
   * El backend hace upsert por (task, constraint_type).
   */
  setConstraint(
    taskId: string,
    request: CreateTaskConstraintRequest
  ): Observable<TaskConstraint> {
    return this.http.post<TaskConstraint>(
      `${this.baseUrl}/tasks/${taskId}/constraints/`,
      request
    );
  }

  /**
   * SK-21-07 — Eliminar una restricción de scheduling.
   * DELETE /api/v1/projects/constraints/{constraintId}/
   */
  deleteConstraint(constraintId: string): Observable<void> {
    return this.http.delete<void>(
      `${this.baseUrl}/constraints/${constraintId}/`
    );
  }
}
