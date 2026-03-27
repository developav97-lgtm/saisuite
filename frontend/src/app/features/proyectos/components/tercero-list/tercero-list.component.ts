import {
  ChangeDetectionStrategy, Component, OnInit, TemplateRef, ViewChild,
  inject, input, signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDialog, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatChipsModule } from '@angular/material/chips';
import { MatSnackBar } from '@angular/material/snack-bar';
import { TerceroProyectoService } from '../../services/tercero-proyecto.service';
import { FaseService } from '../../services/fase.service';
import {
  TerceroProyecto,
  RolTercero,
  ROL_LABELS,
  ROL_OPTIONS,
} from '../../models/tercero-proyecto.model';
import { FaseList } from '../../models/fase.model';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { TerceroSelectorComponent, TerceroSeleccionado } from '../../../../shared/components/tercero-selector/tercero-selector.component';

@Component({
  selector: 'app-tercero-list',
  templateUrl: './tercero-list.component.html',
  styleUrl: './tercero-list.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, ReactiveFormsModule,
    MatTableModule, MatButtonModule, MatIconModule,
    MatFormFieldModule, MatInputModule, MatSelectModule,
    MatTooltipModule, MatDialogModule, MatProgressBarModule,
    MatChipsModule, TerceroSelectorComponent,
  ],
})
export class TerceroListComponent implements OnInit {
  private readonly service     = inject(TerceroProyectoService);
  private readonly faseService = inject(FaseService);
  private readonly fb          = inject(FormBuilder);
  private readonly dialog      = inject(MatDialog);
  private readonly snackBar    = inject(MatSnackBar);

  readonly proyectoId = input.required<string>();

  readonly terceros  = signal<TerceroProyecto[]>([]);
  readonly fases     = signal<FaseList[]>([]);
  readonly loading   = signal(false);

  // Tercero seleccionado en el autocomplete
  private terceroSeleccionado: TerceroSeleccionado | null = null;

  readonly displayedColumns = ['tercero_nombre', 'rol', 'fase', 'acciones'];

  readonly ROL_LABELS  = ROL_LABELS;
  readonly ROL_OPTIONS = ROL_OPTIONS;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  @ViewChild('terceroFormTpl') terceroFormTemplate!: TemplateRef<any>;
  private dialogRef: MatDialogRef<unknown> | null = null;

  readonly form = this.fb.group({
    rol:  [null as RolTercero | null, Validators.required],
    fase: [null as string | null],
  });

  ngOnInit(): void {
    this.loadTerceros();
    this.loadFases();
  }

  loadTerceros(): void {
    this.loading.set(true);
    this.service.list(this.proyectoId()).subscribe({
      next: (data) => { this.terceros.set(data); this.loading.set(false); },
      error: () => { this.loading.set(false); },
    });
  }

  private loadFases(): void {
    this.faseService.listByProyecto(this.proyectoId()).subscribe({
      next: (fases) => this.fases.set(fases),
    });
  }

  abrirDialogVincular(): void {
    this.terceroSeleccionado = null;
    this.form.reset({ fase: null });
    this.dialogRef = this.dialog.open(this.terceroFormTemplate, {
      width: '540px',
      disableClose: false,
    });
  }

  onTerceroSeleccionado(tercero: TerceroSeleccionado | null): void {
    this.terceroSeleccionado = tercero;
  }

  vincular(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    if (!this.terceroSeleccionado) {
      this.snackBar.open('Selecciona un tercero del catálogo.', 'Cerrar', { duration: 3000 });
      return;
    }
    const val = this.form.getRawValue();
    this.service.vincular(this.proyectoId(), {
      tercero_id:     this.terceroSeleccionado.numero_identificacion,
      tercero_nombre: this.terceroSeleccionado.nombre_completo,
      rol:            val.rol!,
      fase:           val.fase ?? null,
      tercero_fk:     this.terceroSeleccionado.id,
    }).subscribe({
      next: () => {
        this.dialogRef?.close();
        this.loadTerceros();
        this.snackBar.open('Tercero vinculado correctamente.', 'Cerrar', {
          duration: 3000, panelClass: ['snack-success'],
        });
      },
      error: (err: { error?: unknown[] | { detail?: string } }) => {
        const e = err?.error;
        const msg = Array.isArray(e)
          ? String(e[0])
          : (e as { detail?: string })?.detail ?? 'No se pudo vincular el tercero.';
        this.snackBar.open(msg, 'Cerrar', { duration: 5000, panelClass: ['snack-error'] });
      },
    });
  }

  confirmarDesvincular(tercero: TerceroProyecto): void {
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        header: 'Confirmar desvinculación',
        message: `¿Desvincular a "${tercero.tercero_nombre}" del proyecto?`,
        acceptLabel: 'Desvincular',
        acceptColor: 'warn',
      },
      width: '400px',
    });
    ref.afterClosed().subscribe((confirmed: boolean) => {
      if (!confirmed) return;
      this.service.desvincular(this.proyectoId(), tercero.id).subscribe({
        next: () => {
          this.loadTerceros();
          this.snackBar.open('Tercero desvinculado.', 'Cerrar', {
            duration: 3000, panelClass: ['snack-success'],
          });
        },
        error: () => {
          this.snackBar.open('No se pudo desvincular.', 'Cerrar', {
            duration: 4000, panelClass: ['snack-error'],
          });
        },
      });
    });
  }

  faseNombre(faseId: string | null): string {
    if (!faseId) return '—';
    return this.fases().find(f => f.id === faseId)?.nombre ?? faseId;
  }
}
