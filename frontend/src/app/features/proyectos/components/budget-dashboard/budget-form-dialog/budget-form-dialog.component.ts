/**
 * SaiSuite — BudgetFormDialogComponent
 * Dialog para crear o editar el presupuesto de un proyecto.
 */
import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  signal,
} from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';

import { BudgetService } from '../../../services/budget.service';
import { ProjectBudget, ProjectBudgetWrite } from '../../../models/budget.model';
import { ToastService } from '../../../../../core/services/toast.service';

export interface BudgetFormDialogData {
  projectId: string;
  budget: ProjectBudget | null;
}

@Component({
  selector: 'app-budget-form-dialog',
  templateUrl: './budget-form-dialog.component.html',
  styleUrl: './budget-form-dialog.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ReactiveFormsModule,
    MatDialogModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatProgressSpinnerModule,
    MatIconModule,
    MatTooltipModule,
  ],
})
export class BudgetFormDialogComponent {
  private readonly dialogRef  = inject<MatDialogRef<BudgetFormDialogComponent, ProjectBudget | null>>(MatDialogRef);
  readonly dialogData         = inject<BudgetFormDialogData>(MAT_DIALOG_DATA);
  private readonly fb         = inject(FormBuilder);
  private readonly budgetSvc  = inject(BudgetService);
  private readonly toast      = inject(ToastService);

  readonly saving     = signal(false);
  readonly isEditMode = this.dialogData.budget !== null;

  // Signals numéricos — el computed formatea en tiempo real (patrón proyecto-form)
  readonly totalRaw   = signal(this.parseNum(this.dialogData.budget?.planned_total_budget));
  readonly laborRaw   = signal(this.parseNum(this.dialogData.budget?.planned_labor_cost));
  readonly expenseRaw = signal(this.parseNum(this.dialogData.budget?.planned_expense_cost));

  readonly totalDisplay   = computed(() => this.formatCOP(this.totalRaw()));
  readonly laborDisplay   = computed(() => this.formatCOP(this.laborRaw()));
  readonly expenseDisplay = computed(() => this.formatCOP(this.expenseRaw()));

  readonly form = this.fb.group({
    planned_total_budget:       [this.parseNum(this.dialogData.budget?.planned_total_budget),  [Validators.required, Validators.min(0)]],
    planned_labor_cost:         [this.parseNum(this.dialogData.budget?.planned_labor_cost),    Validators.required],
    planned_expense_cost:       [this.parseNum(this.dialogData.budget?.planned_expense_cost),  Validators.required],
    alert_threshold_percentage: [this.dialogData.budget?.alert_threshold_percentage ?? '80',   [Validators.required, Validators.min(1), Validators.max(100)]],
    notes:                      [this.dialogData.budget?.notes ?? ''],
  });

  onMoneyInput(event: Event, controlName: string, rawSignal: ReturnType<typeof signal<number>>): void {
    const raw = (event.target as HTMLInputElement).value.replace(/[^\d]/g, '');
    const num = raw ? parseInt(raw, 10) : 0;
    rawSignal.set(num);
    this.form.get(controlName)!.setValue(num, { emitEvent: false });
  }

  guardar(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const v = this.form.getRawValue();
    const data: ProjectBudgetWrite = {
      planned_total_budget:       String(v['planned_total_budget']),
      planned_labor_cost:         String(v['planned_labor_cost']),
      planned_expense_cost:       String(v['planned_expense_cost']),
      alert_threshold_percentage: String(v['alert_threshold_percentage']),
      currency:                   'COP',
      notes:                      v['notes'] ?? '',
    };

    const request$ = this.isEditMode
      ? this.budgetSvc.updateBudget(this.dialogData.projectId, data)
      : this.budgetSvc.createBudget(this.dialogData.projectId, data);

    this.saving.set(true);
    request$.subscribe({
      next: (b) => {
        this.toast.success('Presupuesto guardado.');
        this.dialogRef.close(b);
      },
      error: (err: { error?: { detail?: string } }) => {
        const msg = err?.error?.detail ?? 'Error al guardar el presupuesto.';
        this.toast.error(msg);
        this.saving.set(false);
      },
    });
  }

  cancelar(): void {
    this.dialogRef.close(null);
  }

  private parseNum(value: string | undefined | null): number {
    if (!value) return 0;
    const n = parseFloat(value);
    return isNaN(n) ? 0 : Math.round(n);
  }

  private formatCOP(value: number): string {
    if (!value) return '';
    return new Intl.NumberFormat('es-CO', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  }
}
