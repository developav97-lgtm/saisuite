import {
  ChangeDetectionStrategy,
  Component,
  inject,
  signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogModule, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';

export interface DuplicateDialogData {
  reportTitle: string;
}

export interface DuplicateDialogResult {
  titulo: string;
}

@Component({
  selector: 'app-duplicate-dialog',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    MatDialogModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatIconModule,
  ],
  template: `
    <h2 mat-dialog-title>
      <mat-icon>content_copy</mat-icon>
      Duplicar reporte
    </h2>

    <mat-dialog-content>
      <mat-form-field appearance="outline" class="dup-dialog__field">
        <mat-label>Nombre del nuevo reporte</mat-label>
        <input
          matInput
          [(ngModel)]="titulo"
          (ngModelChange)="titulo = $event"
          [value]="titulo"
          maxlength="200"
          placeholder="Nombre del reporte duplicado"
          #tituloInput>
        <mat-hint align="end">{{ titulo.length }}/200</mat-hint>
      </mat-form-field>
    </mat-dialog-content>

    <mat-dialog-actions align="end">
      <button mat-button (click)="cancel()">Cancelar</button>
      <button
        mat-flat-button
        color="primary"
        [disabled]="!titulo.trim()"
        (click)="confirm()">
        Duplicar
      </button>
    </mat-dialog-actions>
  `,
  styles: [`
    h2[mat-dialog-title] {
      display: flex;
      align-items: center;
      gap: 8px;

      mat-icon {
        color: var(--sc-primary);
        font-size: 22px;
        width: 22px;
        height: 22px;
      }
    }

    .dup-dialog__field {
      width: 100%;
      min-width: 360px;
    }

    @media (max-width: 480px) {
      .dup-dialog__field { min-width: 240px; }
    }
  `],
})
export class DuplicateDialogComponent {
  private readonly dialogRef = inject(MatDialogRef<DuplicateDialogComponent>);
  private readonly data = inject<DuplicateDialogData>(MAT_DIALOG_DATA);

  titulo = `${this.data.reportTitle} (copia)`;

  confirm(): void {
    const t = this.titulo.trim();
    if (!t) return;
    this.dialogRef.close({ titulo: t } satisfies DuplicateDialogResult);
  }

  cancel(): void {
    this.dialogRef.close(undefined);
  }
}
