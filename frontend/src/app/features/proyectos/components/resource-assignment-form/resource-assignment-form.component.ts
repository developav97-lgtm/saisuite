/**
 * SaiSuite — ResourceAssignmentFormComponent
 * Dialog para crear una nueva asignación de recurso en una tarea.
 */
import {
  ChangeDetectionStrategy, Component, OnInit, inject, signal,
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
import { ResourceService } from '../../services/resource.service';
import { AdminService } from '../../../admin/services/admin.service';
import { AdminUser } from '../../../admin/models/admin.models';

export interface ResourceAssignmentFormData {
  tareaId: string;
}

@Component({
  selector: 'app-resource-assignment-form',
  templateUrl: './resource-assignment-form.component.html',
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
export class ResourceAssignmentFormComponent implements OnInit {
  private readonly dialogRef      = inject<MatDialogRef<ResourceAssignmentFormComponent, boolean>>(MatDialogRef);
  private readonly data           = inject<ResourceAssignmentFormData>(MAT_DIALOG_DATA);
  private readonly fb             = inject(FormBuilder);
  private readonly resourceService = inject(ResourceService);
  private readonly adminService   = inject(AdminService);
  private readonly snackBar       = inject(MatSnackBar);

  readonly saving   = signal(false);
  readonly usuarios = signal<AdminUser[]>([]);

  readonly form = this.fb.group({
    usuario_id:            ['', Validators.required],
    porcentaje_asignacion: ['50', [Validators.required, Validators.min(0.01), Validators.max(100)]],
    fecha_inicio:          [null as Date | null, Validators.required],
    fecha_fin:             [null as Date | null, Validators.required],
    notas:                 [''],
  });

  ngOnInit(): void {
    this.adminService.listUsers().subscribe(res => {
      this.usuarios.set(res.results.filter(u => u.is_active));
    });
  }

  guardar(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const v = this.form.getRawValue();
    this.saving.set(true);

    this.resourceService.createAssignment(this.data.tareaId, {
      usuario_id:            v.usuario_id!,
      porcentaje_asignacion: v.porcentaje_asignacion!,
      fecha_inicio:          this.formatDate(v.fecha_inicio!),
      fecha_fin:             this.formatDate(v.fecha_fin!),
      notas:                 v.notas ?? '',
    }).subscribe({
      next: () => {
        this.snackBar.open('Recurso asignado', 'Cerrar', { duration: 3000, panelClass: ['snack-success'] });
        this.dialogRef.close(true);
      },
      error: (err) => {
        const msg = err?.error?.usuario_id?.[0]
          ?? err?.error?.porcentaje_asignacion?.[0]
          ?? err?.error?.fecha_fin?.[0]
          ?? err?.error?.detail
          ?? 'Error al asignar recurso';
        this.snackBar.open(msg, 'Cerrar', { duration: 5000, panelClass: ['snack-error'] });
        this.saving.set(false);
      },
    });
  }

  cancelar(): void {
    this.dialogRef.close(false);
  }

  private formatDate(d: Date): string {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }
}
