import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  input,
  signal,
  computed,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTableModule } from '@angular/material/table';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialog } from '@angular/material/dialog';
import { MatDividerModule } from '@angular/material/divider';
import { forkJoin } from 'rxjs';

import { BudgetService } from '../../services/budget.service';
import { ExpenseService } from '../../services/expense.service';
import { CostRateService } from '../../services/cost-rate.service';
import {
  ProjectBudget,
  BudgetAlert,
  BudgetSnapshot,
  EvmMetrics,
  CostBreakdownByResource,
  CostBreakdownByTask,
  ProjectExpense,
  ResourceCostRate,
} from '../../models/budget.model';
import { ConfirmDialogComponent, ConfirmDialogData } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { CostRateFormComponent, CostRateFormData } from './cost-rate-form/cost-rate-form.component';
import { ExpenseFormDialogComponent, ExpenseFormDialogData } from './expense-form-dialog/expense-form-dialog.component';
import { BudgetFormDialogComponent, BudgetFormDialogData } from './budget-form-dialog/budget-form-dialog.component';
import { ToastService } from '../../../../core/services/toast.service';

@Component({
  selector: 'app-budget-dashboard',
  templateUrl: './budget-dashboard.component.html',
  styleUrl: './budget-dashboard.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatTableModule,
    MatTooltipModule,
    MatChipsModule,
    MatDividerModule,
  ],
})
export class BudgetDashboardComponent implements OnInit {
  readonly projectId = input.required<string>();

  private readonly budgetService   = inject(BudgetService);
  private readonly expenseService  = inject(ExpenseService);
  private readonly costRateService = inject(CostRateService);
  private readonly toast           = inject(ToastService);
  private readonly dialog          = inject(MatDialog);

  // ── State signals ──────────────────────────────────────────────────────────
  readonly loading         = signal(true);
  readonly budget          = signal<ProjectBudget | null>(null);
  readonly alerts          = signal<BudgetAlert[]>([]);
  readonly evm             = signal<EvmMetrics | null>(null);
  readonly costByResource  = signal<CostBreakdownByResource[]>([]);
  readonly costByTask      = signal<CostBreakdownByTask[]>([]);
  readonly expenses        = signal<ProjectExpense[]>([]);
  readonly costRates       = signal<ResourceCostRate[]>([]);
  readonly loadingRates    = signal(false);
  readonly snapshots       = signal<BudgetSnapshot[]>([]);

  // ── Computed ───────────────────────────────────────────────────────────────
  readonly hasBudget = computed(() => this.budget() !== null);

  readonly executionPct = computed(() => {
    const b = this.budget();
    if (!b?.actual_total_cost || !b.planned_total_budget) return 0;
    const actual  = parseFloat(b.actual_total_cost);
    const planned = parseFloat(b.planned_total_budget);
    return planned > 0 ? Math.min(100, Math.round((actual / planned) * 100)) : 0;
  });

  readonly alertLevel = computed(() => {
    const al = this.alerts();
    if (al.some(a => a.type === 'danger'))   return 'danger';
    if (al.some(a => a.type === 'warning'))  return 'warning';
    if (al.some(a => a.type === 'info'))     return 'info';
    return 'none';
  });

  readonly RESOURCE_COLUMNS   = ['user', 'hours', 'rate', 'cost', 'pct'];
  readonly TASK_COLUMNS       = ['task', 'hours', 'labor_cost', 'total_cost'];
  readonly EXPENSE_COLUMNS    = ['date', 'category', 'description', 'amount', 'billable', 'approved', 'actions'];
  readonly COST_RATE_COLUMNS  = ['user', 'hourly_rate', 'start_date', 'end_date', 'status', 'actions'];
  readonly SNAPSHOT_COLUMNS   = ['snapshot_date', 'total_cost', 'planned_budget', 'variance', 'variance_percentage'];

  // ── Lifecycle ──────────────────────────────────────────────────────────────

  ngOnInit(): void {
    this.loadAll();
    this.loadCostRates();
    this.loadSnapshots();
  }

  private loadAll(): void {
    const pid = this.projectId();
    this.loading.set(true);

    forkJoin({
      alerts:   this.budgetService.getAlerts(pid),
      expenses: this.expenseService.getExpenses(pid),
    }).subscribe({
      next: ({ alerts, expenses }) => {
        this.alerts.set(alerts);
        this.expenses.set(expenses);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });

    // Budget, EVM and cost breakdown load independently
    this.budgetService.getBudget(pid).subscribe({
      next: b => this.budget.set(b),
      error: () => {},
    });

    this.budgetService.getEvmMetrics(pid).subscribe({
      next: evm => this.evm.set(evm),
      error: () => {},
    });

    this.budgetService.getCostByResource(pid).subscribe({
      next: data => this.costByResource.set(data),
      error: () => {},
    });

    this.budgetService.getCostByTask(pid).subscribe({
      next: data => this.costByTask.set(data),
      error: () => {},
    });
  }

  // ── Budget actions ─────────────────────────────────────────────────────────

  openBudgetForm(): void {
    const data: BudgetFormDialogData = {
      projectId: this.projectId(),
      budget:    this.budget(),
    };
    const ref = this.dialog.open(BudgetFormDialogComponent, {
      data,
      width: '560px',
      disableClose: true,
    });
    ref.afterClosed().subscribe((saved: ProjectBudget | null | undefined) => {
      if (!saved) return;
      this.budget.set(saved);
    });
  }

  createSnapshot(): void {
    this.budgetService.createSnapshot(this.projectId()).subscribe({
      next: () => {
        this.toast.success('Snapshot creado.');
        this.loadSnapshots();
      },
      error: () => this.toast.error('Error al crear snapshot.'),
    });
  }

  loadSnapshots(): void {
    this.budgetService.getSnapshots(this.projectId()).subscribe({
      next: data => this.snapshots.set(data),
      error: () => {},
    });
  }

  // ── Expense actions ────────────────────────────────────────────────────────

  openExpenseForm(): void {
    const data: ExpenseFormDialogData = { projectId: this.projectId() };
    const ref = this.dialog.open(ExpenseFormDialogComponent, {
      data,
      width: '520px',
      disableClose: true,
    });
    ref.afterClosed().subscribe((saved: ProjectExpense | null | undefined) => {
      if (!saved) return;
      this.expenses.update(list => [saved, ...list]);
    });
  }

  approveExpense(expense: ProjectExpense): void {
    this.expenseService.approveExpense(expense.id).subscribe({
      next: updated => {
        this.expenses.update(list =>
          list.map(e => e.id === updated.id ? updated : e)
        );
        this.toast.success('Gasto aprobado.');
      },
      error: (err) => {
        const msg = err?.error?.detail ?? 'Error al aprobar el gasto.';
        this.toast.error(msg);
      },
    });
  }

  deleteExpense(expense: ProjectExpense): void {
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        title:   'Eliminar gasto',
        message: `¿Eliminar el gasto "${expense.description}"? Esta acción no se puede deshacer.`,
      },
    });
    ref.afterClosed().subscribe((confirmed: boolean) => {
      if (!confirmed) return;
      this.expenseService.deleteExpense(expense.id).subscribe({
        next: () => {
          this.expenses.update(list => list.filter(e => e.id !== expense.id));
          this.toast.success('Gasto eliminado.');
        },
        error: (err) => {
          const msg = err?.error?.detail ?? 'Error al eliminar el gasto.';
          this.toast.error(msg);
        },
      });
    });
  }

  // ── Cost Rate actions ──────────────────────────────────────────────────────

  private loadCostRates(): void {
    this.loadingRates.set(true);
    this.costRateService.getRates().subscribe({
      next: rates => {
        this.costRates.set(rates);
        this.loadingRates.set(false);
      },
      error: () => this.loadingRates.set(false),
    });
  }

  openCostRateForm(rate?: ResourceCostRate): void {
    const data: CostRateFormData = { rate };
    const ref = this.dialog.open(CostRateFormComponent, {
      data,
      width: '520px',
      disableClose: true,
    });
    ref.afterClosed().subscribe((saved: ResourceCostRate | null | undefined) => {
      if (!saved) return;
      if (rate) {
        this.costRates.update(list => list.map(r => r.id === saved.id ? saved : r));
      } else {
        this.costRates.update(list => [saved, ...list]);
      }
    });
  }

  deleteCostRate(rate: ResourceCostRate): void {
    const data: ConfirmDialogData = {
      header:      'Eliminar tarifa',
      message:     `¿Eliminar la tarifa de ${rate.user_full_name}? Esta acción no se puede deshacer.`,
      acceptLabel: 'Eliminar',
      acceptColor: 'warn',
    };
    const ref = this.dialog.open(ConfirmDialogComponent, { data });
    ref.afterClosed().subscribe((confirmed: boolean) => {
      if (!confirmed) return;
      this.costRateService.deleteRate(rate.id).subscribe({
        next: () => {
          this.costRates.update(list => list.filter(r => r.id !== rate.id));
          this.toast.success('Tarifa eliminada.');
        },
        error: (err: { error?: { detail?: string } }) => {
          const msg = err?.error?.detail ?? 'Error al eliminar la tarifa.';
          this.toast.error(msg);
        },
      });
    });
  }

  // ── Helpers ────────────────────────────────────────────────────────────────

  formatCurrency(value: string | null | undefined): string {
    if (!value) return '—';
    return parseFloat(value).toLocaleString('es-CO', {
      style:                 'currency',
      currency:              this.budget()?.currency ?? 'COP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    });
  }

  isNegativeVariance(variance: string | null): boolean {
    if (!variance) return false;
    return parseFloat(variance) < 0;
  }

  cpiColor(cpi: string | null): string {
    if (!cpi) return '';
    const v = parseFloat(cpi);
    if (v >= 0.9) return 'var(--sc-success, #388e3c)';
    if (v >= 0.7) return 'var(--sc-warning, #f57c00)';
    return 'var(--sc-danger, #d32f2f)';
  }
}
