// Interfaces that mirror exactly the backend serializers

export interface ProjectKPIs {
  completion_rate: number;      // 0-100
  on_time_rate: number;         // 0-100
  budget_variance: number;      // negative = under budget
  velocity: number;             // tasks/week average
  burn_rate: number;            // hours/week average
  total_tasks: number;
  completed_tasks: number;
  overdue_tasks: number;
}

export interface TaskDistribution {
  todo: number;
  in_progress: number;
  in_review: number;
  completed: number;
  blocked: number;
  cancelled: number;
  total: number;
  percentages: {
    todo: number;
    in_progress: number;
    in_review: number;
    completed: number;
    blocked: number;
    cancelled: number;
  };
}

export interface VelocityDataPoint {
  week_label: string;
  week_start: string;
  tasks_completed: number;
}

// Backend wraps velocity data: { periods: N, data: VelocityDataPoint[] }
export interface VelocityResponse {
  periods: number;
  data: VelocityDataPoint[];
}

export interface BurnRateDataPoint {
  week_label: string;
  week_start: string;
  hours_registered: number;
}

// Backend wraps burn rate data: { periods: N, data: BurnRateDataPoint[] }
export interface BurnRateResponse {
  periods: number;
  data: BurnRateDataPoint[];
}

export interface BurnDownPoint {
  week_label: string;
  week_start: string;
  hours_remaining: number;
  hours_ideal: number;
  hours_actual_cumulative: number;
}

export interface BurnDownData {
  total_hours_estimated: number;
  data_points: BurnDownPoint[];
}

export interface ResourceUtilization {
  user_id: string;
  user_name: string;
  user_email: string;
  assigned_hours: number;
  registered_hours: number;
  capacity_hours: number;
  utilization_percentage: number;
}

export interface ProjectComparison {
  project_id: string;
  project_name: string;
  project_code: string;
  completion_rate: number;
  on_time_rate: number;
  budget_variance: number;
  velocity: number;
  total_tasks: number;
  completed_tasks: number;
  overdue_tasks: number;
}

export interface TimelineTask {
  task_id: string;
  task_name: string;
  estado: string;
  prioridad: number;
  deadline: string | null;
  horas_estimadas: number;
  horas_registradas: number;
}

export interface TimelinePhase {
  phase_id: string;
  phase_name: string;
  phase_order: number;
  estado: string;
  progress: number;
  total_tasks: number;
  completed_tasks: number;
  tasks: TimelineTask[];
}

export interface ProjectTimeline {
  project_id: string;
  project_name: string;
  project_code: string;
  start_planned: string | null;
  end_planned: string | null;
  start_actual: string | null;
  end_actual: string | null;
  overall_progress: number;
  phases: TimelinePhase[];
}

export interface CompareProjectsRequest {
  project_ids: string[];
}

export interface ExportExcelRequest {
  project_ids: string[];
  metrics?: string[];
}
