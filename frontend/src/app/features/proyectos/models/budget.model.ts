// Interfaces that mirror exactly the backend budget_serializers.py
// Feature #7 — Budget & Cost Tracking

// ─── Resource Cost Rate ───────────────────────────────────────────────────────

export interface ResourceCostRate {
  id: string;
  user: string;
  user_email: string;
  user_full_name: string;
  start_date: string;           // YYYY-MM-DD
  end_date: string | null;      // null = open-ended (currently active)
  hourly_rate: string;          // Decimal as string
  currency: string;
  is_active: boolean;
  notes?: string;
  created_at: string;
  updated_at?: string;
}

export interface ResourceCostRateWrite {
  user: string;
  start_date: string;
  end_date?: string | null;
  hourly_rate: string;
  currency?: string;
  notes?: string;
}

// ─── Project Budget ───────────────────────────────────────────────────────────

export type BudgetAlertLevel = 'none' | 'warning' | 'critical';

export interface ProjectBudget {
  id: string;
  project: string;
  planned_labor_cost: string;
  planned_expense_cost: string;
  planned_total_budget: string;
  approved_budget: string | null;
  approved_by: string | null;
  approved_date: string | null;
  is_approved: boolean;
  alert_threshold_percentage: string;
  currency: string;
  notes: string;
  // Computed fields — injected by view
  actual_labor_cost: string | null;
  actual_expense_cost: string | null;
  actual_total_cost: string | null;
  variance: string | null;
  variance_percentage: string | null;
  alert: BudgetAlertLevel | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectBudgetWrite {
  planned_labor_cost?: string;
  planned_expense_cost?: string;
  planned_total_budget?: string;
  alert_threshold_percentage?: string;
  currency?: string;
  notes?: string;
}

// ─── Expense ─────────────────────────────────────────────────────────────────

export type ExpenseCategory =
  | 'materials'
  | 'equipment'
  | 'travel'
  | 'subcontractor'
  | 'software'
  | 'training'
  | 'other';

export interface ProjectExpense {
  id: string;
  project: string;
  category: ExpenseCategory;
  category_display: string;
  description: string;
  amount: string;
  currency: string;
  expense_date: string;
  paid_by: string | null;
  paid_by_name: string;
  billable: boolean;
  is_approved: boolean;
  receipt_url?: string;
  notes?: string;
  approved_by?: string | null;
  approved_by_name?: string;
  approved_date?: string | null;
  created_at: string;
  updated_at?: string;
}

export interface ProjectExpenseWrite {
  category: ExpenseCategory;
  description: string;
  amount: string;
  currency?: string;
  expense_date: string;
  paid_by?: string | null;
  receipt_url?: string;
  billable?: boolean;
  notes?: string;
}

// ─── Budget Snapshot ──────────────────────────────────────────────────────────

export interface BudgetSnapshot {
  id: string;
  project: string;
  snapshot_date: string;
  labor_cost: string;
  expense_cost: string;
  total_cost: string;
  planned_budget: string;
  variance: string;
  variance_percentage: string;
  created_at: string;
}

// ─── Cost Summary (computed) ──────────────────────────────────────────────────

export interface CostSummary {
  labor_cost: string;
  expense_cost: string;
  total_cost: string;
  currency: string;
}

export interface CostBreakdownByResource {
  user_id: string;
  user_full_name: string;
  hours_worked: string;
  cost: string;
  percentage_of_total: string;
}

export interface CostBreakdownByTask {
  task_id: string;
  task_name: string;
  estimated_hours: string;
  actual_hours: string;
  actual_cost: string;
  hours_variance: string;
}

// ─── Budget Variance ──────────────────────────────────────────────────────────

export type BudgetStatus = 'under' | 'warning' | 'on' | 'over' | 'no_budget';

export interface BudgetVariance {
  planned_budget: string;
  actual_cost: string;
  variance: string;
  variance_percentage: string;
  is_over_budget: boolean;
  alert_triggered: boolean;
  currency: string;
}

// ─── Budget Alert ─────────────────────────────────────────────────────────────

export interface BudgetAlert {
  type: 'info' | 'warning' | 'danger';
  message: string;
  current_pct: string;
  threshold: string;
  labor_cost: string;
  expense_cost: string;
  total_cost: string;
  reference_budget: string;
}

// ─── EVM Metrics ─────────────────────────────────────────────────────────────

export type ScheduleHealth = 'on_track' | 'at_risk' | 'behind';
export type CostHealth = 'on_track' | 'at_risk' | 'over_budget';

export interface EvmMetrics {
  BAC: string;
  PV: string;
  EV: string;
  AC: string;
  CV: string;
  SV: string;
  CPI: string | null;
  SPI: string | null;
  EAC: string | null;
  ETC: string | null;
  TCPI: string | null;
  VAC: string | null;
  completion_percentage: string;
  schedule_health: ScheduleHealth;
  cost_health: CostHealth;
  currency: string;
  as_of_date: string;
  warning: string | null;
}

// ─── Invoice ─────────────────────────────────────────────────────────────────

export interface InvoiceLineItem {
  type: 'labor' | 'expense';
  description: string;
  quantity: string;
  unit_rate: string;
  subtotal: string;
}

export interface InvoiceData {
  project_id: string;
  project_name: string;
  client_name: string;
  line_items: InvoiceLineItem[];
  subtotal_labor: string;
  subtotal_expenses: string;
  grand_total: string;
  currency: string;
  generated_at: string;
}

// ─── Query params ─────────────────────────────────────────────────────────────

export interface ExpenseFilters {
  category?: ExpenseCategory;
  billable?: boolean;
  start_date?: string;
  end_date?: string;
}

export interface CostFilters {
  start_date?: string;
  end_date?: string;
}
