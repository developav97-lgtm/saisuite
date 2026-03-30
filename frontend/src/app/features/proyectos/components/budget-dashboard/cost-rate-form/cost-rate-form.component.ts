/**
 * SaiSuite — CostRateFormComponent
 * Dialog para crear o editar una tarifa de costo por recurso (ResourceCostRate).
 */
import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
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
import { MatDatepickerModule } from '@angular/material/datepicker';
import { provideNativeDateAdapter } from '@angular/material/core';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatIconModule } from '@angular/material/icon';

import { CostRateService } from '../../../services/cost-rate.service';
import { AdminService } from '../../../../admin/services/admin.service';
import { AdminUser } from '../../../../admin/models/admin.models';
import { ResourceCostRate } from '../../../models/budget.model';
import { ToastService } from '../../../../../core/services/toast.service';

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
  private readonly toast       = inject(ToastService);

  readonly saving   = signal(false);
  readonly usuarios = signal<AdminUser[]>([]);

  readonly isEditMode = !!this.dialogData.rate;

  // Patrón estándar campos monetarios: signal numérico + computed formateado
  readonly rateRaw     = signal(this.parseRate(this.dialogData.rate?.hourly_rate));
  readonly rateDisplay = computed(() => this.formatCOP(this.rateRaw()));

  readonly form = this.fb.group({
    user:         [this.dialogData.rate?.user ?? '', Validators.required],
    hourly_rate:  [this.parseRate(this.dialogData.rate?.hourly_rate), [Validators.required, Validators.min(0)]],
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
    this.adminService.listUsers().subscribe(res => {
      this.usuarios.set(res.results.filter(u => u.is_active));
    });
  }

  onRateInput(event: Event): void {
    const raw = (event.target as HTMLInputElement).value.replace(/[^\d]/g, '');
    const num = raw ? parseInt(raw, 10) : 0;
    this.rateRaw.set(num);
    this.form.get('hourly_rate')!.setValue(num, { emitEvent: false });
  }

  guardar(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const v = this.form.getRawValue();
    const payload = {
      user:        v.user!,
      hourly_rate: String(v.hourly_rate!),
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
        this.toast.success(this.isEditMode ? 'Tarifa actualizada.' : 'Tarifa creada.');
        this.dialogRef.close(saved);
      },
      error: (err: { error?: { detail?: string; hourly_rate?: string[]; start_date?: string[] } }) => {
        const msg =
          err?.error?.hourly_rate?.[0] ??
          err?.error?.start_date?.[0] ??
          err?.error?.detail ??
          'Error al guardar la tarifa.';
        this.toast.error(msg);
        this.saving.set(false);
      },
    });
  }

  cancelar(): void {
    this.dialogRef.close(null);
  }

  private parseRate(value: string | undefined | null): number {
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
