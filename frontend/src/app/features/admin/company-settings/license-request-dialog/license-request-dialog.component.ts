import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogModule, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatIconModule } from '@angular/material/icon';
import { LicensePackage, LICENSE_REQUEST_TYPE_LABELS, LicenseRequestType } from '../../models/tenant.model';

export interface LicenseRequestDialogData {
  requestType: LicenseRequestType;
  packages: LicensePackage[];
}

@Component({
  selector: 'app-license-request-dialog',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatButtonModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatIconModule,
  ],
  template: `
    <h2 mat-dialog-title>
      <mat-icon>send</mat-icon>
      Solicitar {{ typeLabel }}
    </h2>

    <mat-dialog-content>
      <p class="lrd-hint">
        Selecciona el paquete que necesitas. El equipo de ValMen Tech revisará tu solicitud y te notificará por correo.
      </p>

      <form [formGroup]="form">
        <mat-form-field appearance="outline" class="lrd-full">
          <mat-label>Paquete</mat-label>
          <mat-select formControlName="packageId" required>
            @for (pkg of data.packages; track pkg.id) {
              <mat-option [value]="pkg.id">
                {{ pkg.name }}
                @if (pkg.quantity) { — {{ pkg.quantity | number }} {{ unitLabel }} }
                @if (+pkg.price_monthly > 0) { · {{ +pkg.price_monthly | number:'1.0-0' }} COP/mes }
              </mat-option>
            }
          </mat-select>
          @if (form.get('packageId')?.invalid && form.get('packageId')?.touched) {
            <mat-error>Selecciona un paquete</mat-error>
          }
        </mat-form-field>

        <mat-form-field appearance="outline" class="lrd-full">
          <mat-label>Nota (opcional)</mat-label>
          <textarea matInput formControlName="notes" rows="3"
                    placeholder="Ej: Necesitamos 5 usuarios adicionales para el área de ventas"></textarea>
        </mat-form-field>
      </form>
    </mat-dialog-content>

    <mat-dialog-actions align="end">
      <button mat-button (click)="cancel()">Cancelar</button>
      <button mat-raised-button color="primary"
              [disabled]="form.invalid"
              (click)="submit()">
        Enviar solicitud
      </button>
    </mat-dialog-actions>
  `,
  styles: [`
    h2[mat-dialog-title] {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .lrd-hint {
      font-size: 0.875rem;
      color: var(--sc-text-secondary, #666);
      margin: 0 0 16px;
    }
    .lrd-full { width: 100%; }
  `],
})
export class LicenseRequestDialogComponent {
  readonly data = inject<LicenseRequestDialogData>(MAT_DIALOG_DATA);
  private readonly dialogRef = inject(MatDialogRef<LicenseRequestDialogComponent>);
  private readonly fb = inject(FormBuilder);

  readonly form = this.fb.group({
    packageId: ['', Validators.required],
    notes: [''],
  });

  get typeLabel(): string {
    return LICENSE_REQUEST_TYPE_LABELS[this.data.requestType];
  }

  get unitLabel(): string {
    if (this.data.requestType === 'user_seats') return 'usuarios';
    if (this.data.requestType === 'ai_tokens') return 'tokens';
    return '';
  }

  cancel(): void {
    this.dialogRef.close();
  }

  submit(): void {
    if (this.form.invalid) return;
    this.dialogRef.close({
      packageId: this.form.value.packageId,
      notes:     this.form.value.notes ?? '',
    });
  }
}
