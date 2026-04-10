/**
 * SaiSuite — Actividad Lead Dialog
 * Crear una nueva actividad para un lead.
 */
import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatDialogModule, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { provideNativeDateAdapter } from '@angular/material/core';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatIconModule } from '@angular/material/icon';

import { CrmService } from '../../services/crm.service';
import { TipoActividad } from '../../models/crm.model';
import { ToastService } from '../../../../core/services/toast.service';

export interface ActividadLeadDialogData {
  leadId: string;
}

@Component({
  selector: 'app-actividad-lead-dialog',
  templateUrl: './actividad-lead-dialog.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [provideNativeDateAdapter()],
  styles: [`
    .fecha-hora-row { display: flex; gap: 12px; }
    .fecha-field    { flex: 2; }
    .hora-field     { flex: 1; min-width: 120px; }
    .form-grid mat-form-field { width: 100%; }
  `],
  imports: [
    CommonModule, ReactiveFormsModule, MatDialogModule,
    MatButtonModule, MatFormFieldModule, MatInputModule,
    MatSelectModule, MatDatepickerModule, MatProgressBarModule, MatIconModule,
  ],
})
export class ActividadLeadDialogComponent {
  private readonly crm       = inject(CrmService);
  private readonly toast     = inject(ToastService);
  private readonly dialogRef = inject(MatDialogRef<ActividadLeadDialogComponent>);
  private readonly fb        = inject(FormBuilder);
  readonly data              = inject<ActividadLeadDialogData>(MAT_DIALOG_DATA);

  readonly saving  = signal(false);
  readonly minDate = new Date();

  readonly form = this.fb.group({
    tipo:             ['llamada' as TipoActividad, Validators.required],
    titulo:           ['', [Validators.required, Validators.minLength(3)]],
    descripcion:      [''],
    fecha_programada: [null as Date | null, Validators.required],
    hora_programada:  ['09:00', Validators.required],
  });

  readonly tipoOpciones: { value: TipoActividad; label: string }[] = [
    { value: 'llamada',  label: 'Llamada' },
    { value: 'reunion',  label: 'Reunión' },
    { value: 'email',    label: 'Email' },
    { value: 'tarea',    label: 'Tarea' },
    { value: 'whatsapp', label: 'WhatsApp' },
    { value: 'otro',     label: 'Otro' },
  ];

  save(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.saving.set(true);
    const val = this.form.value;
    const fechaBase = new Date(val.fecha_programada as Date);
    const [hh, mm] = (val.hora_programada ?? '00:00').split(':').map(Number);
    fechaBase.setHours(hh, mm, 0, 0);
    const fecha = fechaBase.toISOString();

    this.crm.createActividadLead(this.data.leadId, {
      tipo:             val.tipo as TipoActividad,
      titulo:           val.titulo!,
      descripcion:      val.descripcion ?? '',
      fecha_programada: fecha,
    }).subscribe({
      next: actividad => {
        this.saving.set(false);
        this.dialogRef.close(actividad);
      },
      error: () => {
        this.toast.error('Error creando actividad');
        this.saving.set(false);
      },
    });
  }
}
