/**
 * SaiSuite — Completar Actividad Dialog
 * Solicita el resultado al marcar una actividad como completada.
 */
import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogModule, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { CrmActividad } from '../../models/crm.model';

@Component({
  selector: 'app-completar-actividad-dialog',
  template: `
    <h2 mat-dialog-title>Completar Actividad</h2>
    <mat-dialog-content>
      <p style="margin:0 0 12px;color:var(--sc-text-secondary)">{{ data.titulo }}</p>
      <mat-form-field appearance="outline" style="width:100%">
        <mat-label>Resultado</mat-label>
        <textarea matInput [(ngModel)]="resultado" rows="3"
          placeholder="Describe el resultado de la actividad..."></textarea>
      </mat-form-field>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button mat-dialog-close>Cancelar</button>
      <button mat-flat-button color="primary" [mat-dialog-close]="resultado">
        Completar
      </button>
    </mat-dialog-actions>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule, MatDialogModule,
    MatButtonModule, MatFormFieldModule, MatInputModule,
  ],
})
export class CompletarActividadDialogComponent {
  readonly data = inject<CrmActividad>(MAT_DIALOG_DATA);
  resultado = '';
}
