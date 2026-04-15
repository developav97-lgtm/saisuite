import {
  ChangeDetectionStrategy,
  Component,
  inject,
  signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import {
  MAT_DIALOG_DATA,
  MatDialogModule,
  MatDialogRef,
} from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDividerModule } from '@angular/material/divider';
import { BIFieldConfig, BIFieldFormat } from '../../models/bi-field.model';
import { CalcFieldStoreService, CalcFieldTemplate } from '../../services/calc-field-store.service';

export interface CalcFieldDialogData {
  sources: string[];
  metrics: { field: string; label: string }[];
  templates: CalcFieldTemplate[];
}

@Component({
  selector: 'app-calc-field-dialog',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    MatDialogModule,
    MatButtonModule,
    MatChipsModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatSelectModule,
    MatTooltipModule,
    MatDividerModule,
  ],
  template: `
    <h2 mat-dialog-title class="dialog-title">
      <mat-icon>calculate</mat-icon>
      Campo calculado
    </h2>

    <mat-dialog-content class="cfd-content">

      <!-- Plantillas guardadas -->
      @if (templates().length > 0) {
        <div class="cfd-section-label">Mis plantillas</div>
        <div class="cfd-templates">
          @for (tpl of templates(); track tpl.id) {
            <div class="cfd-tpl-item">
              <div class="cfd-tpl-info">
                <span class="cfd-tpl-name">{{ tpl.label }}</span>
                <span class="cfd-tpl-formula">{{ tpl.formula }}</span>
              </div>
              <button mat-icon-button (click)="addFromTemplate(tpl)"
                matTooltip="Agregar al reporte" class="cfd-tpl-add">
                <mat-icon>add_circle_outline</mat-icon>
              </button>
              <button mat-icon-button (click)="deleteTemplate(tpl)"
                matTooltip="Eliminar plantilla" class="cfd-tpl-delete">
                <mat-icon>delete_outline</mat-icon>
              </button>
            </div>
          }
        </div>
        <mat-divider class="cfd-divider"></mat-divider>
        <div class="cfd-section-label cfd-section-label--new">Nuevo campo</div>
      }

      <!-- Nombre -->
      <mat-form-field appearance="outline" subscriptSizing="dynamic" class="cfd-field">
        <mat-label>Nombre del campo</mat-label>
        <input matInput [(ngModel)]="calcLabel" placeholder="ej: Saldo neto">
      </mat-form-field>

      <!-- Chips de campos disponibles -->
      @if (data.metrics.length > 0) {
        <div class="cfd-section-label">Insertar campo en fórmula:</div>
        <mat-chip-set class="cfd-chips">
          @for (m of data.metrics; track m.field) {
            <mat-chip (click)="insertField(m.field)"
              class="cfd-chip"
              [matTooltip]="m.label">
              {{ m.field }}
            </mat-chip>
          }
        </mat-chip-set>
      }

      <!-- Fórmula -->
      <mat-form-field appearance="outline" class="cfd-field">
        <mat-label>Fórmula</mat-label>
        <input matInput [(ngModel)]="calcFormula" placeholder="ej: debito - credito">
        <mat-hint>Operadores: + − × ÷ con paréntesis si es necesario</mat-hint>
      </mat-form-field>

      <!-- Formato -->
      <mat-form-field appearance="outline" subscriptSizing="dynamic" class="cfd-field">
        <mat-label>Formato</mat-label>
        <mat-select [(ngModel)]="calcFormat">
          @for (f of formatOptions; track f.value) {
            <mat-option [value]="f.value">{{ f.label }}</mat-option>
          }
        </mat-select>
      </mat-form-field>

    </mat-dialog-content>

    <mat-dialog-actions align="end">
      <button mat-button (click)="cancel()">Cancelar</button>
      <button mat-flat-button color="primary"
        [disabled]="!calcLabel.trim() || !calcFormula.trim()"
        (click)="create()">
        <mat-icon>add</mat-icon>
        Agregar al reporte
      </button>
    </mat-dialog-actions>
  `,
  styles: [`
    .cfd-content {
      min-width: 420px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      padding-top: 8px !important;
    }

    .cfd-section-label {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--sc-text-muted);
      margin-bottom: -4px;
    }

    .cfd-section-label--new {
      margin-top: 4px;
    }

    .cfd-templates {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .cfd-tpl-item {
      display: flex;
      align-items: center;
      gap: 4px;
      padding: 6px 8px;
      border-radius: 8px;
      background: var(--sc-surface-header);
      border: 1px solid var(--sc-surface-border);
    }

    .cfd-tpl-info {
      flex: 1;
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .cfd-tpl-name {
      font-size: 13px;
      font-weight: 600;
      color: var(--sc-text-color);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .cfd-tpl-formula {
      font-size: 11px;
      font-family: monospace;
      color: var(--sc-text-muted);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .cfd-tpl-add mat-icon { color: var(--sc-primary); }
    .cfd-tpl-delete mat-icon { color: var(--sc-error); }

    .cfd-divider { margin: 4px 0 !important; }

    .cfd-field { width: 100%; }

    .cfd-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
    }

    .cfd-chip {
      cursor: pointer;
      font-size: 11px !important;
      font-family: monospace !important;
      height: 24px !important;
    }
  `],
})
export class CalcFieldDialogComponent {
  private readonly dialogRef = inject(MatDialogRef<CalcFieldDialogComponent>);
  private readonly calcStore = inject(CalcFieldStoreService);
  readonly data = inject<CalcFieldDialogData>(MAT_DIALOG_DATA);

  readonly templates = signal<CalcFieldTemplate[]>([...this.data.templates]);

  calcLabel = '';
  calcFormula = '';
  calcFormat: BIFieldFormat = 'number';

  readonly formatOptions: { value: BIFieldFormat; label: string }[] = [
    { value: 'string',   label: 'Texto' },
    { value: 'number',   label: 'Número' },
    { value: 'currency', label: 'Moneda ($)' },
    { value: 'date',     label: 'Fecha' },
  ];

  insertField(fieldName: string): void {
    const sep = this.calcFormula.trim().length > 0 ? ' ' : '';
    this.calcFormula = this.calcFormula + sep + fieldName;
  }

  create(): void {
    if (!this.calcLabel.trim() || !this.calcFormula.trim()) return;
    const source = this.data.sources[0] ?? '';
    const templateId = `tpl_${Date.now()}`;

    const template: CalcFieldTemplate = {
      id: templateId,
      label: this.calcLabel.trim(),
      formula: this.calcFormula.trim(),
      format: this.calcFormat,
    };
    this.calcStore.saveTemplate(source, template);

    const config: BIFieldConfig = {
      source,
      field: `__calc_${templateId}`,
      role: 'metric',
      label: template.label,
      format: template.format,
      is_calculated: true,
      formula: template.formula,
    };
    this.dialogRef.close(config);
  }

  addFromTemplate(template: CalcFieldTemplate): void {
    const source = this.data.sources[0] ?? '';
    const config: BIFieldConfig = {
      source,
      field: `__calc_${Date.now()}`,
      role: 'metric',
      label: template.label,
      format: template.format,
      is_calculated: true,
      formula: template.formula,
    };
    this.dialogRef.close(config);
  }

  deleteTemplate(template: CalcFieldTemplate): void {
    const source = this.data.sources[0] ?? '';
    this.calcStore.removeTemplate(source, template.id);
    this.templates.update(ts => ts.filter(t => t.id !== template.id));
  }

  cancel(): void {
    this.dialogRef.close(null);
  }
}
