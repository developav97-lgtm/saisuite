/**
 * SaiSuite — AutoScheduleDialogComponent (SK-36)
 * Dialog de dos fases: configurar → preview → aplicar.
 * Permite al usuario calcular una reprogramación automática (dry_run)
 * y luego aplicarla si está satisfecho.
 */
import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  signal,
} from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatRadioModule } from '@angular/material/radio';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatListModule } from '@angular/material/list';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatChipsModule } from '@angular/material/chips';
import { SchedulingService } from '../../../services/scheduling.service';
import { AutoScheduleResult, LevelResourcesResult } from '../../../models/scheduling.model';
import { ToastService } from '../../../../../core/services/toast.service';

export interface AutoScheduleDialogData {
  projectId: string;
  projectName: string;
}

@Component({
  selector: 'app-auto-schedule-dialog',
  templateUrl: './auto-schedule-dialog.component.html',
  styleUrl: './auto-schedule-dialog.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DatePipe,
    FormsModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    MatRadioModule,
    MatCheckboxModule,
    MatProgressBarModule,
    MatListModule,
    MatTooltipModule,
    MatExpansionModule,
    MatChipsModule,
  ],
})
export class AutoScheduleDialogComponent {
  private readonly schedulingService = inject(SchedulingService);
  private readonly toast = inject(ToastService);
  readonly dialogRef = inject(MatDialogRef<AutoScheduleDialogComponent>);
  readonly data = inject<AutoScheduleDialogData>(MAT_DIALOG_DATA);

  readonly mode = signal<'asap' | 'alap'>('asap');
  readonly respectConstraints = signal(true);
  readonly dryRunOnly = signal(false);
  readonly loading = signal(false);
  readonly preview = signal<AutoScheduleResult | null>(null);

  // ── Resource Leveling ──────────────────────────────────────────────────────
  readonly levelingLoading = signal(false);
  readonly levelingPreview = signal<LevelResourcesResult | null>(null);
  readonly levelingDryRun  = signal(true);

  // ── Preview tasks computed ──────────────────────────────────────────────────
  readonly previewTasks = computed(() => {
    const p = this.preview();
    if (!p?.preview) return [];
    return Object.entries(p.preview as Record<string, {
      nombre: string;
      old_start: string | null;
      old_end: string | null;
      new_start: string | null;
      new_end: string | null;
    }>).map(([id, v]) => ({ id, ...v }));
  });

  calculate(): void {
    this.loading.set(true);
    this.preview.set(null);

    this.schedulingService.autoSchedule(this.data.projectId, {
      scheduling_mode: this.mode(),
      respect_constraints: this.respectConstraints(),
      dry_run: true,
    }).subscribe({
      next: (result) => {
        this.preview.set(result);
        this.loading.set(false);
      },
      error: () => {
        this.toast.error('Error al calcular la reprogramación.');
        this.loading.set(false);
      },
    });
  }

  apply(): void {
    if (!this.preview() || this.dryRunOnly()) return;

    this.loading.set(true);

    this.schedulingService.autoSchedule(this.data.projectId, {
      scheduling_mode: this.mode(),
      respect_constraints: this.respectConstraints(),
      dry_run: false,
    }).subscribe({
      next: (result) => {
        this.loading.set(false);
        this.toast.success(
          `Reprogramación aplicada: ${result.tasks_rescheduled} tarea(s) actualizada(s).`
        );
        this.dialogRef.close(result);
      },
      error: () => {
        this.toast.error('Error al aplicar la reprogramación.');
        this.loading.set(false);
      },
    });
  }

  cancel(): void {
    this.dialogRef.close(null);
  }

  // ── Resource Leveling ──────────────────────────────────────────────────────

  levelResources(): void {
    this.levelingLoading.set(true);
    this.levelingPreview.set(null);

    this.schedulingService.levelResources(this.data.projectId, {
      dry_run: this.levelingDryRun(),
    }).subscribe({
      next: (result) => {
        this.levelingPreview.set(result);
        this.levelingLoading.set(false);
        if (!this.levelingDryRun()) {
          this.toast.success(`Nivelación aplicada: ${result.tasks_moved} tarea(s) movida(s).`);
        }
      },
      error: () => {
        this.toast.error('Error al nivelar recursos.');
        this.levelingLoading.set(false);
      },
    });
  }
}
