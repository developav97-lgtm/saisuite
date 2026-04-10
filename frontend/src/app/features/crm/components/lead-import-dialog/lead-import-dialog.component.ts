/**
 * SaiSuite — Lead Import Dialog
 * Permite subir un CSV/Excel y previsualizar antes de importar.
 */
import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTableModule } from '@angular/material/table';

import { CrmService } from '../../services/crm.service';
import { ToastService } from '../../../../core/services/toast.service';

@Component({
  selector: 'app-lead-import-dialog',
  templateUrl: './lead-import-dialog.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, MatDialogModule, MatButtonModule,
    MatIconModule, MatProgressBarModule, MatTableModule,
  ],
})
export class LeadImportDialogComponent {
  private readonly crm    = inject(CrmService);
  private readonly toast  = inject(ToastService);
  private readonly dialogRef = inject(MatDialogRef<LeadImportDialogComponent>);

  readonly rows     = signal<Record<string, string>[]>([]);
  readonly columns  = signal<string[]>([]);
  readonly loading  = signal(false);
  readonly fileName = signal('');

  onFileSelected(event: Event): void {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (!file) return;
    this.fileName.set(file.name);
    this.parseFile(file);
  }

  private parseFile(file: File): void {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      const lines = text.split('\n').filter(l => l.trim());
      if (lines.length < 2) return;

      const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
      const rows = lines.slice(1).map(line => {
        const values = line.split(',').map(v => v.trim().replace(/"/g, ''));
        const row: Record<string, string> = {};
        headers.forEach((h, i) => row[h] = values[i] ?? '');
        return row;
      });

      this.columns.set(headers);
      this.rows.set(rows.slice(0, 5)); // preview first 5
    };
    reader.readAsText(file);
  }

  import(): void {
    if (this.rows().length === 0) return;
    this.loading.set(true);
    this.crm.importarLeads(this.rows()).subscribe({
      next: result => {
        this.loading.set(false);
        this.dialogRef.close(result.creados);
      },
      error: () => {
        this.toast.error('Error importando leads');
        this.loading.set(false);
      },
    });
  }

  cancel(): void {
    this.dialogRef.close(null);
  }
}
