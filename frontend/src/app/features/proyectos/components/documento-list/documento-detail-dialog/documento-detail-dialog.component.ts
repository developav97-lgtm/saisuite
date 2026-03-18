import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { DocumentoContableDetail, TIPO_DOCUMENTO_LABELS } from '../../../models/documento-contable.model';

@Component({
  selector: 'app-documento-detail-dialog',
  template: `
    <h2 mat-dialog-title>
      <mat-icon>description</mat-icon>
      {{ TIPO_DOCUMENTO_LABELS[doc.tipo_documento] }} — {{ doc.numero_documento }}
    </h2>
    <mat-dialog-content>
      <div class="ddd-grid">
        <div class="ddd-field"><label>Tipo</label><span>{{ doc.tipo_documento_display }}</span></div>
        <div class="ddd-field"><label>Número</label><span>{{ doc.numero_documento }}</span></div>
        <div class="ddd-field"><label>Fecha</label><span>{{ formatDate(doc.fecha_documento) }}</span></div>
        <div class="ddd-field"><label>ID Saiopen</label><span>{{ doc.saiopen_doc_id }}</span></div>
        <div class="ddd-field ddd-field--full"><label>Tercero</label><span>{{ doc.tercero_nombre }} ({{ doc.tercero_id }})</span></div>
        <div class="ddd-field"><label>Valor bruto</label><span>{{ formatCurrency(doc.valor_bruto) }}</span></div>
        <div class="ddd-field"><label>Descuento</label><span>{{ formatCurrency(doc.valor_descuento) }}</span></div>
        <div class="ddd-field"><label>Valor neto</label><span class="ddd-neto">{{ formatCurrency(doc.valor_neto) }}</span></div>
        @if (doc.observaciones) {
          <div class="ddd-field ddd-field--full"><label>Observaciones</label><span>{{ doc.observaciones }}</span></div>
        }
        <div class="ddd-field ddd-field--full ddd-sync">
          <mat-icon>sync</mat-icon>
          <small>Sincronizado desde Saiopen: {{ formatDate(doc.sincronizado_desde_saiopen) }}</small>
        </div>
      </div>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button [mat-dialog-close]="null">Cerrar</button>
    </mat-dialog-actions>
  `,
  styles: [`
    .ddd-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; padding-top: 0.5rem; }
    .ddd-field { display: flex; flex-direction: column; gap: 0.25rem; }
    .ddd-field--full { grid-column: 1 / -1; }
    label { font-size: 0.75rem; font-weight: 600; color: var(--sc-text-muted); text-transform: uppercase; }
    .ddd-neto { font-weight: 700; font-size: 1.05rem; color: var(--sc-primary); }
    .ddd-sync { flex-direction: row; align-items: center; gap: 0.25rem; color: var(--sc-text-muted); font-size: 0.8rem; }
    h2 mat-icon { vertical-align: middle; margin-right: 0.25rem; }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, MatDialogModule, MatButtonModule, MatIconModule],
})
export class DocumentoDetailDialogComponent {
  readonly doc = inject<DocumentoContableDetail>(MAT_DIALOG_DATA);
  readonly TIPO_DOCUMENTO_LABELS = TIPO_DOCUMENTO_LABELS;

  formatCurrency(value: string): string {
    const num = parseFloat(value);
    return isNaN(num)
      ? value
      : num.toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 });
  }

  formatDate(date: string): string {
    if (!date) return '—';
    return new Date(date.includes('T') ? date : date + 'T00:00:00').toLocaleDateString('es-CO');
  }
}
