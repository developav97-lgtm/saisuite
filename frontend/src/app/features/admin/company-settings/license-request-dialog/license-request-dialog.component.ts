import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { DecimalPipe } from '@angular/common';
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

const NOTES_MAX_LENGTH = 500;

@Component({
  selector: 'app-license-request-dialog',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DecimalPipe,
    ReactiveFormsModule,
    MatButtonModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatIconModule,
  ],
  template: `
    <h2 mat-dialog-title class="dialog-title">
      <mat-icon aria-hidden="true">send</mat-icon>
      Solicitar {{ typeLabel() }}
    </h2>

    <mat-dialog-content>
      <p class="lrd-hint">
        Selecciona el paquete que necesitas. El equipo de ValMen Tech revisará tu solicitud y te notificará por correo.
      </p>

      <form [formGroup]="form">
        <mat-form-field appearance="outline" class="lrd-full" subscriptSizing="dynamic">
          <mat-label>Paquete</mat-label>
          <mat-select formControlName="packageId" required>
            @for (pkg of data.packages; track pkg.id) {
              <mat-option [value]="pkg.id" [attr.aria-label]="optionAriaLabel(pkg)">
                {{ pkg.name }}
                @if (pkg.quantity) { — {{ pkg.quantity | number }} {{ unitLabel() }} }
                @if (+pkg.price_monthly > 0) { · {{ +pkg.price_monthly | number:'1.0-0' }} COP/mes }
              </mat-option>
            }
          </mat-select>
          @if (form.controls.packageId.invalid && form.controls.packageId.touched) {
            <mat-error>Selecciona un paquete</mat-error>
          }
        </mat-form-field>

        <mat-form-field appearance="outline" class="lrd-full" subscriptSizing="dynamic">
          <mat-label>Nota (opcional)</mat-label>
          <textarea matInput formControlName="notes" rows="3"
                    [maxlength]="notesMaxLength"
                    placeholder="Ej: Necesitamos 5 usuarios adicionales para el área de ventas"></textarea>
          <mat-hint align="end">{{ notesLength() }} / {{ notesMaxLength }}</mat-hint>
          @if (form.controls.notes.hasError('maxlength')) {
            <mat-error>Máximo {{ notesMaxLength }} caracteres</mat-error>
          }
        </mat-form-field>
      </form>
    </mat-dialog-content>

    <mat-dialog-actions align="end">
      <button mat-button (click)="cancel()" [disabled]="submitting()">Cancelar</button>
      <button mat-raised-button color="primary"
              [disabled]="form.invalid || submitting()"
              (click)="submit()">
        Enviar solicitud
      </button>
    </mat-dialog-actions>
  `,
  styles: [`
    .lrd-hint {
      font-size: 0.875rem;
      color: var(--sc-text-muted);
      margin: 0 0 1rem;
    }
    .lrd-full { width: 100%; }
    form {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
  `],
})
export class LicenseRequestDialogComponent {
  readonly data = inject<LicenseRequestDialogData>(MAT_DIALOG_DATA);
  private readonly dialogRef = inject(MatDialogRef<LicenseRequestDialogComponent>);
  private readonly fb = inject(FormBuilder);

  readonly notesMaxLength = NOTES_MAX_LENGTH;
  readonly submitting = signal(false);

  readonly form = this.fb.group({
    packageId: ['', Validators.required],
    notes: ['', Validators.maxLength(NOTES_MAX_LENGTH)],
  });

  readonly typeLabel = computed(() => LICENSE_REQUEST_TYPE_LABELS[this.data.requestType]);

  readonly unitLabel = computed(() => {
    if (this.data.requestType === 'user_seats') return 'usuarios';
    if (this.data.requestType === 'ai_tokens') return 'tokens';
    return '';
  });

  readonly notesLength = signal(0);

  constructor() {
    this.form.controls.notes.valueChanges.subscribe(v => {
      this.notesLength.set((v ?? '').length);
    });
  }

  optionAriaLabel(pkg: LicensePackage): string {
    const parts: string[] = [pkg.name];
    if (pkg.quantity) parts.push(`${pkg.quantity} ${this.unitLabel()}`);
    if (+pkg.price_monthly > 0) parts.push(`${pkg.price_monthly} COP mensuales`);
    return parts.join(', ');
  }

  cancel(): void {
    this.dialogRef.close();
  }

  submit(): void {
    if (this.form.invalid || this.submitting()) return;
    this.submitting.set(true);
    this.dialogRef.close({
      packageId: this.form.value.packageId,
      notes:     this.form.value.notes ?? '',
    });
  }
}
