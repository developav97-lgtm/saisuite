/**
 * SaiSuite — ResourceLevelingWizardComponent
 * Wizard de 3 pasos para nivelación automática de recursos del proyecto.
 * Paso 1: Configuración de parámetros
 * Paso 2: Preview de cambios (dry_run)
 * Paso 3: Confirmación y aplicación
 */
import {
  ChangeDetectionStrategy,
  Component,
  inject,
  signal,
} from '@angular/core';
import { DatePipe, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatInputModule } from '@angular/material/input';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTableModule } from '@angular/material/table';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatSnackBar } from '@angular/material/snack-bar';
import { SchedulingService } from '../../../services/scheduling.service';

// ── Tipos locales ─────────────────────────────────────────────────────────────

export type PriorityMode = 'critical_path' | 'priority' | 'deadline';

export interface LevelingConfig {
  priorityMode: PriorityMode;
  allowDelay: boolean;
  maxDelayDays: number;
}

export interface TareaChange {
  tareaId: string;
  tareaNombre: string;
  currentStart: string;
  newStart: string;
  currentEnd: string;
  newEnd: string;
  reason: string;
}

export interface LevelingSummary {
  totalTasksModified: number;
  averageDelayDays: number;
  conflictsResolved: number;
}

export interface LevelingPreview {
  changes: TareaChange[];
  summary: LevelingSummary;
}

export interface ResourceLevelingWizardData {
  proyectoId: string;
}

export interface ResourceLevelingResult {
  success: boolean;
  modifiedTasksCount: number;
}

// ── Columnas para la tabla de cambios ─────────────────────────────────────────
const CHANGE_COLUMNS: string[] = [
  'tarea',
  'fechasActuales',
  'fechasNuevas',
  'razon',
];

@Component({
  selector: 'app-resource-leveling-wizard',
  templateUrl: './resource-leveling-wizard.component.html',
  styleUrl: './resource-leveling-wizard.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DatePipe,
    DecimalPipe,
    FormsModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    MatSelectModule,
    MatFormFieldModule,
    MatCheckboxModule,
    MatInputModule,
    MatProgressBarModule,
    MatTableModule,
    MatTooltipModule,
  ],
})
export class ResourceLevelingWizardComponent {
  private readonly schedulingService = inject(SchedulingService);
  private readonly snackBar          = inject(MatSnackBar);
  readonly dialogRef = inject(MatDialogRef<ResourceLevelingWizardComponent>);
  readonly data      = inject<ResourceLevelingWizardData>(MAT_DIALOG_DATA);

  // ── Estado del wizard ─────────────────────────────────────────────────────
  readonly currentStep = signal<1 | 2 | 3>(1);
  readonly loading     = signal(false);
  readonly error       = signal<string | null>(null);
  readonly preview     = signal<LevelingPreview | null>(null);

  readonly config = signal<LevelingConfig>({
    priorityMode: 'critical_path',
    allowDelay: true,
    maxDelayDays: 5,
  });

  readonly displayedColumns = CHANGE_COLUMNS;

  // ── Paso 1: helpers de config ─────────────────────────────────────────────

  setPriorityMode(value: PriorityMode): void {
    this.config.update(c => ({ ...c, priorityMode: value }));
  }

  setAllowDelay(value: boolean): void {
    this.config.update(c => ({ ...c, allowDelay: value }));
  }

  setMaxDelayDays(value: number): void {
    const days = Math.max(0, value);
    this.config.update(c => ({ ...c, maxDelayDays: days }));
  }

  // ── Paso 1 → 2: calcular preview ─────────────────────────────────────────

  goToPreview(): void {
    this.error.set(null);
    this.loading.set(true);
    this.preview.set(null);

    this.schedulingService
      .resourceLevelingPreview(this.data.proyectoId, this.config())
      .subscribe({
        next: (result) => {
          this.preview.set(result);
          this.loading.set(false);
          this.currentStep.set(2);
        },
        error: (err: unknown) => {
          const message = this.extractErrorMessage(err);
          this.error.set(message);
          this.loading.set(false);
        },
      });
  }

  // ── Paso 2 → 3 ────────────────────────────────────────────────────────────

  goToConfirm(): void {
    this.currentStep.set(3);
  }

  // ── Paso 3: aplicar nivelación ────────────────────────────────────────────

  applyLeveling(): void {
    this.error.set(null);
    this.loading.set(true);

    this.schedulingService
      .resourceLevelingApply(this.data.proyectoId, this.config())
      .subscribe({
        next: (result) => {
          this.loading.set(false);
          this.snackBar.open(
            `Nivelación aplicada: ${result.modifiedTasksCount} tarea(s) modificada(s).`,
            'Cerrar',
            { duration: 5000, panelClass: ['snack-success'] }
          );
          this.dialogRef.close(result);
        },
        error: (err: unknown) => {
          const message = this.extractErrorMessage(err);
          this.error.set(message);
          this.loading.set(false);
        },
      });
  }

  // ── Navegación ────────────────────────────────────────────────────────────

  goBack(): void {
    const step = this.currentStep();
    if (step === 2) { this.currentStep.set(1); }
    else if (step === 3) { this.currentStep.set(2); }
  }

  cancel(): void {
    this.dialogRef.close(null);
  }

  // ── Helpers privados ──────────────────────────────────────────────────────

  private extractErrorMessage(err: unknown): string {
    if (err !== null && typeof err === 'object') {
      const errObj = err as Record<string, unknown>;
      const detail = errObj['error'];
      if (typeof detail === 'string') return detail;
      if (detail !== null && typeof detail === 'object') {
        const detailObj = detail as Record<string, unknown>;
        if (typeof detailObj['detail'] === 'string') return detailObj['detail'];
      }
    }
    return 'No se pudo procesar la solicitud. Intenta de nuevo.';
  }
}
