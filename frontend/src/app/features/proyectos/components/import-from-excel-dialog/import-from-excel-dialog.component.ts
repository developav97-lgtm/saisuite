/**
 * SaiSuite — ImportFromExcelDialogComponent
 * Dialog para importar un proyecto desde archivo Excel (.xlsx).
 */
import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  signal,
} from '@angular/core';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { ProyectoService } from '../../services/proyecto.service';
import { ToastService } from '../../../../core/services/toast.service';

@Component({
  selector: 'app-import-from-excel-dialog',
  templateUrl: './import-from-excel-dialog.component.html',
  styleUrl: './import-from-excel-dialog.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
  ],
})
export class ImportFromExcelDialogComponent {
  private readonly proyectoService = inject(ProyectoService);
  private readonly toast           = inject(ToastService);
  readonly dialogRef               = inject(MatDialogRef<ImportFromExcelDialogComponent>);

  readonly selectedFile   = signal<File | null>(null);
  readonly loading        = signal(false);
  readonly importErrors   = signal<string[]>([]);

  readonly hasFile   = computed(() => this.selectedFile() !== null);
  readonly showErrors = computed(() => this.importErrors().length > 0);

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file  = input.files?.[0] ?? null;
    this.importErrors.set([]);
    this.selectedFile.set(file);
    // Reset input so the same file can be re-selected if removed first
    input.value = '';
  }

  removeFile(): void {
    this.selectedFile.set(null);
    this.importErrors.set([]);
  }

  downloadTemplate(): void {
    this.proyectoService.downloadExcelTemplate().subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        const a   = document.createElement('a');
        a.href    = url;
        a.download = 'plantilla-proyecto.xlsx';
        a.click();
        URL.revokeObjectURL(url);
      },
      error: () => this.toast.error('No se pudo descargar la plantilla.'),
    });
  }

  importProject(): void {
    const file = this.selectedFile();
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    this.loading.set(true);
    this.importErrors.set([]);

    this.proyectoService.importFromExcel(formData).subscribe({
      next: (result) => {
        this.loading.set(false);
        const { fases, tareas, dependencias } = result.stats;
        this.toast.success(
          `Proyecto importado correctamente.`,
          `${fases} fases, ${tareas} tareas, ${dependencias} dependencias.`,
        );
        if (result.warnings.length > 0) {
          this.importErrors.set(result.warnings);
          // Still close with result — warnings are non-blocking
        }
        this.dialogRef.close(result.proyecto);
      },
      error: (err: unknown) => {
        this.loading.set(false);
        const errObj = err as { error?: { detail?: string; non_field_errors?: string[] } };
        const msgs: string[] = [];
        if (errObj?.error?.detail) {
          msgs.push(errObj.error.detail);
        } else if (Array.isArray(errObj?.error?.non_field_errors)) {
          msgs.push(...(errObj.error!.non_field_errors as string[]));
        } else {
          msgs.push('Ocurrió un error al procesar el archivo.');
        }
        this.importErrors.set(msgs);
        this.toast.error('No se pudo importar el archivo Excel.');
      },
    });
  }

  cancel(): void {
    this.dialogRef.close(null);
  }
}
