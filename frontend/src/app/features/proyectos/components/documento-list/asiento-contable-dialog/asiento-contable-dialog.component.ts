import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material/table';
import { MatTooltipModule } from '@angular/material/tooltip';
import { DocumentoContableList, LineaContable } from '../../../models/documento-contable.model';

export interface AsientoDialogData {
  doc: DocumentoContableList;
  lineas: LineaContable[];
}

@Component({
  selector: 'app-asiento-contable-dialog',
  templateUrl: './asiento-contable-dialog.component.html',
  styleUrl: './asiento-contable-dialog.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, MatDialogModule, MatButtonModule,
    MatIconModule, MatTableModule, MatTooltipModule,
  ],
})
export class AsientoContableDialogComponent {
  private readonly data = inject<AsientoDialogData>(MAT_DIALOG_DATA);

  readonly doc   = this.data.doc;
  readonly lineas = this.data.lineas;

  readonly displayedColumns = [
    'auxiliar', 'auxiliar_nombre', 'titulo_nombre', 'tercero_nombre',
    'descripcion', 'debito', 'credito',
  ];

  readonly totalDebito = computed(() =>
    this.lineas.reduce((acc, l) => acc + parseFloat(l.debito || '0'), 0),
  );

  readonly totalCredito = computed(() =>
    this.lineas.reduce((acc, l) => acc + parseFloat(l.credito || '0'), 0),
  );

  formatCurrency(value: string | number): string {
    const num = typeof value === 'number' ? value : parseFloat(value);
    if (isNaN(num) || num === 0) return '—';
    return num.toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 });
  }

  formatDate(date: string): string {
    if (!date) return '—';
    return new Date(date.includes('T') ? date : date + 'T00:00:00').toLocaleDateString('es-CO');
  }
}
