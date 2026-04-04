// SaiSuite — Feature #6: Advanced Scheduling
// SK-30 — Interfaces TypeScript: Scheduling, CPM, Float, Constraints
// Espeja exactamente los serializers de scheduling_serializers.py y scheduling_views.py

// ── Constraint types ─────────────────────────────────────────────────────────

export type ConstraintType =
  | 'asap'
  | 'alap'
  | 'must_start_on'
  | 'must_finish_on'
  | 'start_no_earlier_than'
  | 'start_no_later_than'
  | 'finish_no_earlier_than'
  | 'finish_no_later_than';

export type DependencyType = 'FS' | 'SS' | 'FF';

// ── TaskConstraint ────────────────────────────────────────────────────────────

/** Restricción de scheduling de una tarea (read). Espeja TaskConstraintSerializer. */
export interface TaskConstraint {
  id: string;
  task: string;
  tarea_codigo: string;
  tarea_nombre: string;
  constraint_type: ConstraintType;
  constraint_type_display: string;
  constraint_date: string | null;  // YYYY-MM-DD
  created_at: string;
  updated_at: string;
}

/** Payload para crear una restricción. Espeja TaskConstraintCreateSerializer. */
export interface CreateTaskConstraintRequest {
  constraint_type: ConstraintType;
  constraint_date?: string | null;  // requerido para tipos con fecha
}

// ── Auto-Schedule ─────────────────────────────────────────────────────────────

export type SchedulingMode = 'asap' | 'alap';

/** Payload para POST .../scheduling/auto-schedule/ */
export interface AutoScheduleRequest {
  scheduling_mode?: SchedulingMode;
  respect_constraints?: boolean;
  dry_run?: boolean;
}

/** Respuesta de AutoScheduleView. */
export interface AutoScheduleResult {
  tasks_rescheduled: number;
  tasks_excluded: string[];   // IDs de tareas excluidas
  new_project_end_date: string | null;  // YYYY-MM-DD
  critical_path: string[];    // task IDs en la ruta crítica
  warnings: string[];
  dry_run: boolean;
  preview?: Record<string, unknown>;  // solo cuando dry_run=true
}

// ── Resource Leveling ─────────────────────────────────────────────────────────

/** Payload para POST .../scheduling/level-resources/ */
export interface LevelResourcesRequest {
  dry_run?: boolean;
  max_iterations?: number;
}

/** Cambio individual de una tarea en la nivelación. */
export interface LevelResourcesTaskChange {
  task_id: string;
  task_name: string;
  current_start: string;
  new_start: string;
  current_end: string;
  new_end: string;
}

export interface OverloadTask {
  task_name: string;
  porcentaje: number;
}

export interface UnresolvableOverload {
  user_name: string;
  overload_days: number;
  date_from: string;
  date_to: string;
  tasks: OverloadTask[];
  max_pct: number;
}

/** Respuesta de ResourceLevelingView. */
export interface LevelResourcesResult {
  tasks_moved: number;
  iterations_used: number;
  max_overload_before: number;
  max_overload_after: number;
  leveling_effective: boolean;
  warnings: string[];
  dry_run: boolean;
  task_changes?: LevelResourcesTaskChange[];
  unresolvable_overloads?: UnresolvableOverload[];
}

// ── Critical Path ─────────────────────────────────────────────────────────────

/** Tarea en la ruta crítica con datos de fechas CPM. */
export interface CriticalPathTask {
  task_id: string;
  codigo: string;
  nombre: string;
  early_start: string | null;   // YYYY-MM-DD
  early_finish: string | null;  // YYYY-MM-DD
}

/** Respuesta de CriticalPathView. */
export interface CriticalPathResponse {
  critical_path: string[];        // task IDs
  tasks: CriticalPathTask[];
  project_end_date: string | null;  // YYYY-MM-DD
  tasks_excluded: string[];         // task IDs sin fechas
}

// ── Float ─────────────────────────────────────────────────────────────────────

/** Datos de holgura de una tarea. Espeja TaskFloatView response. */
export interface FloatData {
  task_id: string;
  task_codigo: string;
  task_nombre: string;
  total_float: number | null;
  free_float: number | null;
  is_critical: boolean;
  has_dates: boolean;
  early_start: string | null;   // YYYY-MM-DD
  early_finish: string | null;  // YYYY-MM-DD
  late_start: string | null;    // YYYY-MM-DD
  late_finish: string | null;   // YYYY-MM-DD
}
