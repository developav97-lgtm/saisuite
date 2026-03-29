/**
 * SaiSuite — ResourceAvailabilityFormComponent
 * Dialog para registrar una ausencia/disponibilidad de un usuario.
 */
import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { provideNativeDateAdapter } from '@angular/material/core';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatIconModule } from '@angular/material/icon';
import { ResourceService } from '../../../services/resource.service';
import { AdminUser } from '../../../../admin/models/admin.models';
import { AvailabilityType, AVAILABILITY_TYPE_LABELS, ResourceAvailabilityCreate } from '../../../models/resource.model';
import { ToastService } from '../../../../../core/services/toast.service';

export interface ResourceAvailabilityFormData {
  users: AdminUser[];
}

@Component({
  selector: 'app-resource-availability-form',
  templateUrl: './resource-availability-form.component.html',
  styleUrl: './resource-availability-form.component.scss',
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
export class ResourceAvailabilityFormComponent {
  readonly dialogRef  = inject<MatDialogRef<ResourceAvailabilityFormComponent, boolean>>(MatDialogRef);
  readonly dialogData = inject<ResourceAvailabilityFormData>(MAT_DIALOG_DATA);

  private readonly fb              = inject(FormBuilder);
  private readonly resourceService = inject(ResourceService);
  private readonly toast       = inject(ToastService);

  readonly saving = signal(false);

  readonly availabilityTypes: { value: AvailabilityType; label: string }[] = (
    Object.entries(AVAILABILITY_TYPE_LABELS) as [AvailabilityType, string][]
  ).map(([value, label]) => ({ value, label }));

  readonly form = this.fb.group({
    usuario_id:   ['', Validators.required],
    tipo:         ['' as AvailabilityType | '', Validators.required],
    fecha_inicio: [null as Date | null, Validators.required],
    fecha_fin:    [null as Date | null, Validators.required],
    descripcion:  [''],
  });

  get users(): AdminUser[] { return this.dialogData.users; }

  onSubmit(): void {
    if (this.form.invalid || this.saving()) return;
    this.saving.set(true);

    const v = this.form.getRawValue();
    const payload: ResourceAvailabilityCreate = {
      usuario_id:  v.usuario_id!,
      tipo:        v.tipo as AvailabilityType,
      fecha_inicio: this.formatDate(v.fecha_inicio!),
      fecha_fin:    this.formatDate(v.fecha_fin!),
      descripcion:  v.descripcion ?? '',
    };

    this.resourceService.createAvailability(payload).subscribe({
      next: () => {
        this.toast.success('Ausencia registrada correctamente.');
        this.saving.set(false);
        this.dialogRef.close(true);
      },
      error: () => {
        this.toast.error('Error al registrar la ausencia.');
        this.saving.set(false);
      },
    });
  }

  onCancel(): void {
    this.dialogRef.close(false);
  }

  private formatDate(d: Date): string {
    const y   = d.getFullYear();
    const m   = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }
}
