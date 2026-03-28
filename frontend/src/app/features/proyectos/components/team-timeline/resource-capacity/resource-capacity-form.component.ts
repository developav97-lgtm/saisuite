/**
 * SaiSuite — ResourceCapacityFormComponent
 * Dialog para crear o editar una capacidad semanal de un usuario.
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
import { MatSnackBar } from '@angular/material/snack-bar';
import { ResourceService } from '../../../services/resource.service';
import { AdminUser } from '../../../../admin/models/admin.models';
import { ResourceCapacity, ResourceCapacityCreate } from '../../../models/resource.model';

export interface ResourceCapacityFormData {
  capacity?: ResourceCapacity;
  users: AdminUser[];
}

@Component({
  selector: 'app-resource-capacity-form',
  templateUrl: './resource-capacity-form.component.html',
  styleUrl: './resource-capacity-form.component.scss',
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
export class ResourceCapacityFormComponent implements OnInit {
  readonly dialogRef = inject<MatDialogRef<ResourceCapacityFormComponent, boolean>>(MatDialogRef);
  readonly dialogData = inject<ResourceCapacityFormData>(MAT_DIALOG_DATA);

  private readonly fb              = inject(FormBuilder);
  private readonly resourceService = inject(ResourceService);
  private readonly snackBar        = inject(MatSnackBar);

  readonly saving  = signal(false);
  readonly isEdit  = signal(false);

  readonly form = this.fb.group({
    usuario:         ['', Validators.required],
    horas_por_semana: [null as number | null, [Validators.required, Validators.min(1), Validators.max(168)]],
    fecha_inicio:    [null as Date | null, Validators.required],
    fecha_fin:       [null as Date | null],
  });

  ngOnInit(): void {
    const cap = this.dialogData.capacity;
    if (cap) {
      this.isEdit.set(true);
      this.form.patchValue({
        usuario:          cap.usuario,
        horas_por_semana: parseFloat(cap.horas_por_semana),
        fecha_inicio:     cap.fecha_inicio ? new Date(cap.fecha_inicio + 'T00:00:00') : null,
        fecha_fin:        cap.fecha_fin    ? new Date(cap.fecha_fin    + 'T00:00:00') : null,
      });
    }
  }

  get users(): AdminUser[] { return this.dialogData.users; }

  onSubmit(): void {
    if (this.form.invalid || this.saving()) return;
    this.saving.set(true);

    const v = this.form.getRawValue();
    const payload: ResourceCapacityCreate = {
      usuario:          v.usuario!,
      horas_por_semana: String(v.horas_por_semana),
      fecha_inicio:     this.formatDate(v.fecha_inicio!),
      fecha_fin:        v.fecha_fin ? this.formatDate(v.fecha_fin) : null,
    };

    const cap = this.dialogData.capacity;
    const obs = cap
      ? this.resourceService.updateCapacity(cap.id, payload)
      : this.resourceService.createCapacity(payload);

    obs.subscribe({
      next: () => {
        this.snackBar.open(
          cap ? 'Capacidad actualizada.' : 'Capacidad creada.',
          'Cerrar', { duration: 3000, panelClass: ['snack-success'] },
        );
        this.saving.set(false);
        this.dialogRef.close(true);
      },
      error: () => {
        this.snackBar.open('Error al guardar la capacidad.', 'Cerrar', {
          duration: 5000, panelClass: ['snack-error'],
        });
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
