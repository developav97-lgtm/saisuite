/**
 * SaiSuite — Perder Dialog
 * Solicita el motivo de pérdida antes de marcar una oportunidad como perdida.
 */
import { ChangeDetectionStrategy, Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';

@Component({
  selector: 'app-perder-dialog',
  template: `
    <h2 mat-dialog-title>Marcar como Perdida</h2>
    <mat-dialog-content>
      <mat-form-field appearance="outline" style="width:100%;margin-top:8px">
        <mat-label>Motivo de pérdida *</mat-label>
        <textarea matInput [(ngModel)]="motivo" rows="3"
          placeholder="Ej: Precio muy alto, eligió competidor..."></textarea>
      </mat-form-field>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button mat-dialog-close>Cancelar</button>
      <button mat-flat-button color="warn" [disabled]="!motivo.trim()"
        [mat-dialog-close]="motivo.trim()">
        Confirmar pérdida
      </button>
    </mat-dialog-actions>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule, MatDialogModule,
    MatButtonModule, MatFormFieldModule, MatInputModule,
  ],
})
export class PerderDialogComponent {
  motivo = '';
}
