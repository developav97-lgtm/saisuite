import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { ReactiveFormsModule, FormBuilder } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogModule, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';

export interface ReviewDialogData {
  action: 'approve' | 'reject';
  companyName: string;
  packageName: string;
}

@Component({
  selector: 'app-review-dialog',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatIconModule,
  ],
  template: `
    <h2 mat-dialog-title [style.color]="data.action === 'approve' ? '#2e7d32' : '#c62828'">
      <mat-icon>{{ data.action === 'approve' ? 'check_circle' : 'cancel' }}</mat-icon>
      {{ data.action === 'approve' ? 'Aprobar solicitud' : 'Rechazar solicitud' }}
    </h2>

    <mat-dialog-content>
      <p style="font-size:0.9rem; color:#555; margin:0 0 16px;">
        {{ data.action === 'approve' ? 'Aprobarás' : 'Rechazarás' }}
        la solicitud de <strong>{{ data.companyName }}</strong>
        para el paquete <strong>{{ data.packageName }}</strong>.
        @if (data.action === 'approve') {
          El paquete se aplicará automáticamente a su licencia.
        }
      </p>

      <form [formGroup]="form">
        <mat-form-field appearance="outline" style="width:100%">
          <mat-label>Nota para el cliente (opcional)</mat-label>
          <textarea matInput formControlName="reviewNotes" rows="3"
                    placeholder="Ej: Paquete activado para el período vigente."></textarea>
        </mat-form-field>
      </form>
    </mat-dialog-content>

    <mat-dialog-actions align="end">
      <button mat-button (click)="cancel()">Cancelar</button>
      <button mat-raised-button
              [color]="data.action === 'approve' ? 'primary' : 'warn'"
              (click)="submit()">
        {{ data.action === 'approve' ? 'Aprobar' : 'Rechazar' }}
      </button>
    </mat-dialog-actions>
  `,
  styles: [`
    h2[mat-dialog-title] {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  `],
})
export class ReviewDialogComponent {
  readonly data = inject<ReviewDialogData>(MAT_DIALOG_DATA);
  private readonly dialogRef = inject(MatDialogRef<ReviewDialogComponent>);
  private readonly fb = inject(FormBuilder);

  readonly form = this.fb.group({ reviewNotes: [''] });

  cancel(): void { this.dialogRef.close(undefined); }

  submit(): void {
    this.dialogRef.close(this.form.value.reviewNotes ?? '');
  }
}
