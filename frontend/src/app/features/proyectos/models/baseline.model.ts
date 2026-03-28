// SaiSuite — Feature #6: Advanced Scheduling
// SK-31 — Interfaces TypeScript: ProjectBaseline y BaselineComparison
// Espeja exactamente ProjectBaselineListSerializer, ProjectBaselineDetailSerializer,
// ProjectBaselineCreateSerializer, BaselineComparisonSerializer.

// ── ProjectBaseline — List ────────────────────────────────────────────────────

/** Fila de baseline en listados. Espeja ProjectBaselineListSerializer. */
export interface ProjectBaselineList {
  id: string;
  project: string;
  project_nombre: string;
  name: string;
  description: string;
  is_active_baseline: boolean;
  project_end_date_snapshot: string | null;  // YYYY-MM-DD
  total_tasks_snapshot: number;
  created_at: string;
}

// ── ProjectBaseline — Detail ──────────────────────────────────────────────────

/** Snapshot de tarea dentro del JSON de un baseline. */
export interface BaselineTaskSnapshot {
  task_id: string;
  nombre: string;
  codigo: string;
  fecha_inicio: string | null;
  fecha_fin: string | null;
  horas_estimadas: number;
  estado: string;
}

/** Detalle completo de un baseline. Espeja ProjectBaselineDetailSerializer. */
export interface ProjectBaselineDetail {
  id: string;
  project: string;
  project_nombre: string;
  name: string;
  description: string;
  is_active_baseline: boolean;
  tasks_snapshot: BaselineTaskSnapshot[];
  resources_snapshot: Record<string, unknown>;
  critical_path_snapshot: string[];
  project_end_date_snapshot: string | null;
  total_tasks_snapshot: number;
  created_at: string;
  updated_at: string;
}

// ── Create Baseline ───────────────────────────────────────────────────────────

/** Payload para POST .../baselines/. Espeja ProjectBaselineCreateSerializer. */
export interface CreateBaselineRequest {
  name: string;
  description?: string;
  set_as_active?: boolean;
}

// ── Baseline Comparison ───────────────────────────────────────────────────────

export type BaselineTaskStatus = 'ahead' | 'on_schedule' | 'behind';

/** Fila de tarea en la tabla de comparación. Espeja BaselineComparisonTaskSerializer. */
export interface BaselineComparisonTask {
  task_id: string;
  nombre: string;
  codigo: string;
  baseline_start: string | null;   // YYYY-MM-DD
  baseline_finish: string | null;  // YYYY-MM-DD
  current_start: string | null;    // YYYY-MM-DD
  current_finish: string | null;   // YYYY-MM-DD
  variance_days: number;
  status: BaselineTaskStatus;
}

/** Resumen agregado de la comparación. */
export interface BaselineComparisonSummary {
  total_tasks: number;
  ahead: number;
  on_schedule: number;
  behind: number;
  removed: number;
}

/** Respuesta completa de BaselineCompareView. Espeja BaselineComparisonSerializer. */
export interface BaselineComparison {
  baseline_name: string;
  baseline_end_date: string | null;
  current_end_date: string | null;
  schedule_variance_days: number;
  tasks: BaselineComparisonTask[];
  summary: BaselineComparisonSummary;
}
