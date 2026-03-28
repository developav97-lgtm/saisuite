/**
 * SaiSuite — CostRateFormComponent
 * Dialog para crear o editar una tarifa de costo por recurso (ResourceCostRate).
 */
import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { provideNativeDateAdapter } from '@angular/material/core';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar } from '@angular/material/snack-bar';

import { CostRateService } from '../../../services/cost-rate.service';
import { AdminService } from '../../../../admin/services/admin.service';
import { AdminUser } from '../../../../admin/models/admin.models';
import { ResourceCostRate } from '../../../models/budget.model';

export interface CostRateFormData {
  /** Si se pasa una tarifa existente se entra en modo edición; si no, modo creación. */
  rate?: ResourceCostRate;
}

@Component({
  selector: 'app-cost-rate-form',
  templateUrl: './cost-rate-form.component.html',
  styleUrl: './cost-rate-form.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [provideNativeDateAdapter()],
  imports: [
    ReactiveFormsModule,
    MatDialogModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatDatepickerModule,
    MatProgressSpinnerModule,
    MatIconModule,
  ],
})
export class CostRateFormComponent implements OnInit {
  private readonly dialogRef    = inject<MatDialogRef<CostRateFormComponent, ResourceCostRate | null>>(MatDialogRef);
  readonly dialogData           = inject<CostRateFormData>(MAT_DIALOG_DATA);
  private readonly fb           = inject(FormBuilder);
  private readonly costRateSvc  = inject(CostRateService);
  private readonly adminService = inject(AdminService);
  private readonly snackBar     = inject(MatSnackBar);

  readonly saving   = signal(false);
  readonly usuarios = signal<AdminUser[]>([]);

  readonly isEditMode = !!this.dialogData.rate;

  readonly form = this.fb.group({
    user:         [this.dialogData.rate?.user ?? '', Validators.required],
    hourly_rate:  [this.dialogData.rate?.hourly_rate ?? '', [Validators.required, Validators.min(0)]],
    start_date:   [
      this.dialogData.rate ? this.parseDate(this.dialogData.rate.start_date) : null as Date | null,
      Validators.required,
    ],
    end_date:     [
      this.dialogData.rate?.end_date ? this.parseDate(this.dialogData.rate.end_date) : null as Date | null,
    ],
    notes:        [this.dialogData.rate?.notes ?? ''],
  });

  ngOnInit(): void {
    this.adminService.listUsers().subscribe(users => {
      this.usuarios.set(users.filter(u => u.is_active));
    });
  }

  guardar(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const v = this.form.getRawValue();
    const payload = {
      user:        v.user!,
      hourly_rate: v.hourly_rate!,
      start_date:  this.formatDate(v.start_date!),
      end_date:    v.end_date ? this.formatDate(v.end_date) : null,
      notes:       v.notes ?? '',
    };

    this.saving.set(true);

    const request$ = this.isEditMode
      ? this.costRateSvc.updateRate(this.dialogData.rate!.id, payload)
      : this.costRateSvc.createRate(payload);

    request$.subscribe({
      next: (saved) => {
        this.snackBar.open(
          this.isEditMode ? 'Tarifa actualizada.' : 'Tarifa creada.',
          'Cerrar',
          { duration: 3000, panelClass: ['snack-success'] },
        );
        this.dialogRef.close(saved);
      },
      error: (err: { error?: { detail?: string; hourly_rate?: string[]; start_date?: string[] } }) => {
        const msg =
          err?.error?.hourly_rate?.[0] ??
          err?.error?.start_date?.[0] ??
          err?.error?.detail ??
          'Error al guardar la tarifa.';
        this.snackBar.open(msg, 'Cerrar', { duration: 5000, panelClass: ['snack-error'] });
        this.saving.set(false);
      },
    });
  }

  cancelar(): void {
    this.dialogRef.close(null);
  }

  private formatDate(d: Date): string {
    const y   = d.getFullYear();
    const m   = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }

  private parseDate(dateStr: string): Date {
    const [y, m, d] = dateStr.split('-').map(Number);
    return new Date(y, m - 1, d);
  }
}
