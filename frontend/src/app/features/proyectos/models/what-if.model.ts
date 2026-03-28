// SaiSuite — Feature #6: Advanced Scheduling
// SK-32 — Interfaces TypeScript: WhatIfScenario y SimulationResult
// Espeja exactamente WhatIfScenarioListSerializer, WhatIfScenarioDetailSerializer,
// WhatIfScenarioCreateSerializer.

// ── WhatIfScenario — List ─────────────────────────────────────────────────────

/** Fila de escenario en listados. Espeja WhatIfScenarioListSerializer. */
export interface WhatIfScenarioList {
  id: string;
  project: string;
  project_nombre: string;
  name: string;
  description: string;
  created_by: string | null;
  created_by_nombre: string | null;
  simulated_end_date: string | null;  // YYYY-MM-DD
  days_delta: number | null;
  tasks_affected_count: number;
  simulation_done: boolean;
  simulation_ran_at: string | null;
  created_at: string;
}

// ── WhatIfScenario — Detail ───────────────────────────────────────────────────

/**
 * Cambios propuestos en una tarea.
 * Clave = task UUID (string), valor = objeto con campos a cambiar.
 * Ejemplo: { "uuid-task-1": { "fecha_inicio": "2026-04-01", "fecha_fin": "2026-04-10" } }
 */
export type TaskChangesMap = Record<string, Record<string, string | number | boolean>>;

/**
 * Cambios en asignaciones de recursos.
 * Clave = assignment UUID, valor = campos a modificar.
 */
export type ResourceChangesMap = Record<string, Record<string, string | number>>;

/**
 * Cambios en dependencias.
 * Clave = dependency UUID, valor = { retraso_dias: N }.
 */
export type DependencyChangesMap = Record<string, { retraso_dias: number }>;

/** Detalle completo de un escenario. Espeja WhatIfScenarioDetailSerializer. */
export interface WhatIfScenarioDetail {
  id: string;
  project: string;
  project_nombre: string;
  name: string;
  description: string;
  created_by: string | null;
  created_by_nombre: string | null;
  task_changes: TaskChangesMap;
  resource_changes: ResourceChangesMap;
  dependency_changes: DependencyChangesMap;
  simulated_end_date: string | null;   // YYYY-MM-DD
  simulated_critical_path: string[];   // task IDs
  days_delta: number | null;
  tasks_affected_count: number;
  simulation_done: boolean;
  simulation_ran_at: string | null;
  created_at: string;
  updated_at: string;
}

// ── Create Scenario ───────────────────────────────────────────────────────────

/** Payload para POST .../scenarios/. Espeja WhatIfScenarioCreateSerializer. */
export interface CreateWhatIfScenarioRequest {
  name: string;
  description?: string;
  task_changes?: TaskChangesMap;
  resource_changes?: ResourceChangesMap;
  dependency_changes?: DependencyChangesMap;
}

// ── Compare Scenarios ─────────────────────────────────────────────────────────

/** Fila de comparación de un escenario. Retornado por CompareScenariosView. */
export interface ScenarioComparisonRow {
  scenario_id: string;
  scenario_name: string;
  simulated_end_date: string | null;
  days_delta: number | null;
  tasks_affected_count: number;
  simulation_done: boolean;
}

/** Payload para POST .../scenarios/compare/ */
export interface CompareScenarioRequest {
  scenario_ids: string[];
}
