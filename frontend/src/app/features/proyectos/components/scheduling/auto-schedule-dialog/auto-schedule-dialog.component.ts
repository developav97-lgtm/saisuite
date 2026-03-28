/**
 * SaiSuite — AutoScheduleDialogComponent (SK-36)
 * Dialog de dos fases: configurar → preview → aplicar.
 * Permite al usuario calcular una reprogramación automática (dry_run)
 * y luego aplicarla si está satisfecho.
 */
import {
  ChangeDetectionStrategy,
  Component,
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
import { SchedulingService } from '../../../services/scheduling.service';
import { AutoScheduleResult, LevelResourcesResult } from '../../../models/scheduling.model';

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
  ],
})
export class AutoScheduleDialogComponent {
  private readonly schedulingService = inject(SchedulingService);
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
        this.dialogRef.close(result);
      },
      error: () => {
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
      },
      error: () => {
        this.levelingLoading.set(false);
      },
    });
  }
}
