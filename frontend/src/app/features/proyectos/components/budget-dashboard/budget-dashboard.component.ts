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
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTableModule } from '@angular/material/table';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatChipsModule } from '@angular/material/chips';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatDialog } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatDividerModule } from '@angular/material/divider';
import { forkJoin } from 'rxjs';

import { BudgetService } from '../../services/budget.service';
import { ExpenseService } from '../../services/expense.service';
import {
  ProjectBudget,
  ProjectBudgetWrite,
  BudgetAlert,
  EvmMetrics,
  CostBreakdownByResource,
  CostBreakdownByTask,
  ProjectExpense,
  ProjectExpenseWrite,
  ExpenseCategory,
} from '../../models/budget.model';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';

@Component({
  selector: 'app-budget-dashboard',
  templateUrl: './budget-dashboard.component.html',
  styleUrl: './budget-dashboard.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatTableModule,
    MatTooltipModule,
    MatChipsModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatDatepickerModule,
    MatDividerModule,
  ],
})
export class BudgetDashboardComponent implements OnInit {
  readonly projectId = input.required<string>();

  private readonly budgetService  = inject(BudgetService);
  private readonly expenseService = inject(ExpenseService);
  private readonly snackBar       = inject(MatSnackBar);
  private readonly dialog         = inject(MatDialog);
  private readonly fb             = inject(FormBuilder);

  // ── State signals ──────────────────────────────────────────────────────────
  readonly loading        = signal(true);
  readonly budget         = signal<ProjectBudget | null>(null);
  readonly alerts         = signal<BudgetAlert[]>([]);
  readonly evm            = signal<EvmMetrics | null>(null);
  readonly costByResource = signal<CostBreakdownByResource[]>([]);
  readonly costByTask     = signal<CostBreakdownByTask[]>([]);
  readonly expenses       = signal<ProjectExpense[]>([]);
  readonly showBudgetForm = signal(false);
  readonly showExpenseForm = signal(false);

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

  // ── Forms ──────────────────────────────────────────────────────────────────
  readonly budgetForm = this.fb.group({
    planned_labor_cost:       ['', Validators.required],
    planned_expense_cost:     ['', Validators.required],
    planned_total_budget:     ['', [Validators.required, Validators.min(0)]],
    alert_threshold_percentage: ['80', [Validators.required, Validators.min(1), Validators.max(100)]],
    currency:                 ['COP', Validators.required],
    notes:                    [''],
  });

  readonly expenseForm = this.fb.group({
    category:     ['materials' as ExpenseCategory, Validators.required],
    description:  ['', Validators.required],
    amount:       ['', [Validators.required, Validators.min(0.01)]],
    currency:     ['COP', Validators.required],
    expense_date: ['', Validators.required],
    billable:     [true],
    notes:        [''],
  });

  readonly EXPENSE_CATEGORIES: { value: ExpenseCategory; label: string }[] = [
    { value: 'materials',     label: 'Materiales' },
    { value: 'equipment',     label: 'Equipos' },
    { value: 'travel',        label: 'Viajes' },
    { value: 'subcontractor', label: 'Subcontratistas' },
    { value: 'software',      label: 'Software' },
    { value: 'training',      label: 'Capacitación' },
    { value: 'other',         label: 'Otro' },
  ];

  readonly RESOURCE_COLUMNS  = ['user', 'hours', 'rate', 'cost', 'pct'];
  readonly TASK_COLUMNS      = ['task', 'hours', 'labor_cost', 'total_cost'];
  readonly EXPENSE_COLUMNS   = ['date', 'category', 'description', 'amount', 'billable', 'approved', 'actions'];

  // ── Lifecycle ──────────────────────────────────────────────────────────────

  ngOnInit(): void {
    this.loadAll();
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
      next: b => {
        this.budget.set(b);
        if (b) {
          this.budgetForm.patchValue({
            planned_labor_cost:         b.planned_labor_cost,
            planned_expense_cost:       b.planned_expense_cost,
            planned_total_budget:       b.planned_total_budget,
            alert_threshold_percentage: b.alert_threshold_percentage,
            currency:                   b.currency,
            notes:                      b.notes,
          });
        }
      },
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

  saveBudget(): void {
    if (this.budgetForm.invalid) return;

    const data = this.budgetForm.value as ProjectBudgetWrite;
    const request$ = this.hasBudget()
      ? this.budgetService.updateBudget(this.projectId(), data)
      : this.budgetService.createBudget(this.projectId(), data);

    request$.subscribe({
      next: b => {
        this.budget.set(b);
        this.showBudgetForm.set(false);
        this.snackBar.open('Presupuesto guardado.', 'OK', {
          duration: 3000, panelClass: ['snack-success'],
        });
      },
      error: () => this.snackBar.open('Error al guardar el presupuesto.', 'OK', {
        duration: 4000, panelClass: ['snack-error'],
      }),
    });
  }

  createSnapshot(): void {
    this.budgetService.createSnapshot(this.projectId()).subscribe({
      next: () => this.snackBar.open('Snapshot creado.', 'OK', {
        duration: 3000, panelClass: ['snack-success'],
      }),
      error: () => this.snackBar.open('Error al crear snapshot.', 'OK', {
        duration: 4000, panelClass: ['snack-error'],
      }),
    });
  }

  // ── Expense actions ────────────────────────────────────────────────────────

  saveExpense(): void {
    if (this.expenseForm.invalid) return;

    const raw  = this.expenseForm.value;
    const data: ProjectExpenseWrite = {
      category:     raw['category'] as ExpenseCategory,
      description:  raw['description'] as string,
      amount:       raw['amount'] as string,
      currency:     raw['currency'] as string,
      expense_date: raw['expense_date'] as string,
      billable:     raw['billable'] as boolean,
      notes:        raw['notes'] as string,
    };

    this.expenseService.createExpense(this.projectId(), data).subscribe({
      next: exp => {
        this.expenses.update(list => [exp, ...list]);
        this.expenseForm.reset({ category: 'materials', currency: 'COP', billable: true });
        this.showExpenseForm.set(false);
        this.snackBar.open('Gasto registrado.', 'OK', {
          duration: 3000, panelClass: ['snack-success'],
        });
      },
      error: () => this.snackBar.open('Error al registrar el gasto.', 'OK', {
        duration: 4000, panelClass: ['snack-error'],
      }),
    });
  }

  approveExpense(expense: ProjectExpense): void {
    this.expenseService.approveExpense(expense.id).subscribe({
      next: updated => {
        this.expenses.update(list =>
          list.map(e => e.id === updated.id ? updated : e)
        );
        this.snackBar.open('Gasto aprobado.', 'OK', {
          duration: 3000, panelClass: ['snack-success'],
        });
      },
      error: (err) => {
        const msg = err?.error?.detail ?? 'Error al aprobar el gasto.';
        this.snackBar.open(msg, 'OK', { duration: 4000, panelClass: ['snack-error'] });
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
          this.snackBar.open('Gasto eliminado.', 'OK', {
            duration: 3000, panelClass: ['snack-success'],
          });
        },
        error: (err) => {
          const msg = err?.error?.detail ?? 'Error al eliminar el gasto.';
          this.snackBar.open(msg, 'OK', { duration: 4000, panelClass: ['snack-error'] });
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

  cpiColor(cpi: string | null): string {
    if (!cpi) return '';
    const v = parseFloat(cpi);
    if (v >= 0.9) return 'var(--sc-success, #388e3c)';
    if (v >= 0.7) return 'var(--sc-warning, #f57c00)';
    return 'var(--sc-danger, #d32f2f)';
  }
}
