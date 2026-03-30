/**
 * SaiSuite — ExpenseFormDialogComponent
 * Dialog para registrar un gasto del proyecto.
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

import { ExpenseService } from '../../../services/expense.service';
import { ProjectExpense, ProjectExpenseWrite, ExpenseCategory } from '../../../models/budget.model';
import { ToastService } from '../../../../../core/services/toast.service';

export interface ExpenseFormDialogData {
  projectId: string;
}

@Component({
  selector: 'app-expense-form-dialog',
  templateUrl: './expense-form-dialog.component.html',
  styleUrl: './expense-form-dialog.component.scss',
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
export class ExpenseFormDialogComponent {
  private readonly dialogRef   = inject<MatDialogRef<ExpenseFormDialogComponent, ProjectExpense | null>>(MatDialogRef);
  readonly dialogData          = inject<ExpenseFormDialogData>(MAT_DIALOG_DATA);
  private readonly fb          = inject(FormBuilder);
  private readonly expenseSvc  = inject(ExpenseService);
  private readonly toast       = inject(ToastService);

  readonly saving     = signal(false);
  readonly amountRaw  = signal(0);
  readonly amountDisplay = computed(() => this.formatCOP(this.amountRaw()));

  readonly form = this.fb.group({
    category:     ['materials' as ExpenseCategory, Validators.required],
    description:  ['', Validators.required],
    amount:       [0, [Validators.required, Validators.min(0.01)]],
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

  onAmountInput(event: Event): void {
    const raw = (event.target as HTMLInputElement).value.replace(/[^\d]/g, '');
    const num = raw ? parseInt(raw, 10) : 0;
    this.amountRaw.set(num);
    this.form.controls['amount'].setValue(num, { emitEvent: false });
  }

  guardar(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const raw = this.form.getRawValue();
    const data: ProjectExpenseWrite = {
      category:     raw['category'] as ExpenseCategory,
      description:  raw['description'] as string,
      amount:       String(raw['amount']),
      currency:     'COP',
      expense_date: raw['expense_date'] as string,
      billable:     raw['billable'] as boolean,
      notes:        raw['notes'] as string,
    };

    this.saving.set(true);
    this.expenseSvc.createExpense(this.dialogData.projectId, data).subscribe({
      next: (exp) => {
        this.toast.success('Gasto registrado.');
        this.dialogRef.close(exp);
      },
      error: (err: { error?: { detail?: string } }) => {
        const msg = err?.error?.detail ?? 'Error al registrar el gasto.';
        this.toast.error(msg);
        this.saving.set(false);
      },
    });
  }

  cancelar(): void {
    this.dialogRef.close(null);
  }

  private formatCOP(value: number): string {
    if (!value) return '';
    return new Intl.NumberFormat('es-CO', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  }
}
