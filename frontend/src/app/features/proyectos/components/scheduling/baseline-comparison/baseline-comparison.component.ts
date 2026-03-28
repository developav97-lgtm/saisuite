/**
 * SaiSuite — BaselineComparisonComponent (SK-38)
 * Gestiona y compara baselines de un proyecto.
 * Muestra tabla de variación plan actual vs baseline seleccionado.
 */
import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  computed,
  inject,
  input,
  signal,
} from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormControl, FormGroup, Validators } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { BaselineService } from '../../../services/baseline.service';
import {
  ProjectBaselineList,
  BaselineComparison,
  BaselineComparisonTask,
} from '../../../models/baseline.model';
import { ConfirmDialogComponent } from '../../../../../shared/components/confirm-dialog/confirm-dialog.component';

@Component({
  selector: 'app-baseline-comparison',
  templateUrl: './baseline-comparison.component.html',
  styleUrl: './baseline-comparison.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DatePipe,
    FormsModule,
    ReactiveFormsModule,
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatSelectModule,
    MatFormFieldModule,
    MatInputModule,
    MatProgressBarModule,
    MatChipsModule,
    MatTooltipModule,
    MatPaginatorModule,
  ],
})
export class BaselineComparisonComponent implements OnInit {
  readonly projectId = input.required<string>();

  private readonly baselineService = inject(BaselineService);
  private readonly dialog          = inject(MatDialog);
  private readonly snackBar        = inject(MatSnackBar);

  readonly baselines          = signal<ProjectBaselineList[]>([]);
  readonly selectedBaselineId = signal<string | null>(null);
  readonly comparison         = signal<BaselineComparison | null>(null);
  readonly loading            = signal(false);
  readonly comparing          = signal(false);
  readonly saving             = signal(false);
  readonly showCreateForm     = signal(false);

  // Paginación client-side
  readonly pageIndex = signal(0);
  readonly pageSize  = 10;

  readonly paginatedTasks = computed<BaselineComparisonTask[]>(() => {
    const tasks = this.comparison()?.tasks ?? [];
    const start = this.pageIndex() * this.pageSize;
    return tasks.slice(start, start + this.pageSize);
  });

  readonly displayedColumns = ['tarea', 'baseline_ini', 'actual_ini', 'variacion', 'estado'];

  /** Formulario de creación de baseline */
  readonly createForm = new FormGroup({
    name:        new FormControl<string>('',  { nonNullable: true, validators: [Validators.required] }),
    description: new FormControl<string>('',  { nonNullable: true }),
    set_as_active: new FormControl<boolean>(false, { nonNullable: true }),
  });

  ngOnInit(): void {
    this.loadBaselines();
  }

  loadBaselines(): void {
    this.loading.set(true);
    this.baselineService.list(this.projectId()).subscribe({
      next: (data) => {
        this.baselines.set(data);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.snackBar.open('Error al cargar baselines.', 'Cerrar', {
          duration: 5000,
          panelClass: ['snack-error'],
        });
      },
    });
  }

  toggleCreateForm(): void {
    this.showCreateForm.update(v => !v);
    if (!this.showCreateForm()) {
      this.createForm.reset();
    }
  }

  createBaseline(): void {
    if (this.createForm.invalid) return;

    this.saving.set(true);
    const { name, description, set_as_active } = this.createForm.getRawValue();

    this.baselineService.create(this.projectId(), {
      name,
      description: description || undefined,
      set_as_active,
    }).subscribe({
      next: () => {
        this.saving.set(false);
        this.showCreateForm.set(false);
        this.createForm.reset();
        this.snackBar.open('Baseline creado correctamente.', 'Cerrar', {
          duration: 3000,
          panelClass: ['snack-success'],
        });
        this.loadBaselines();
      },
      error: () => {
        this.saving.set(false);
        this.snackBar.open('Error al crear el baseline.', 'Cerrar', {
          duration: 5000,
          panelClass: ['snack-error'],
        });
      },
    });
  }

  loadComparison(): void {
    const id = this.selectedBaselineId();
    if (!id) return;

    this.comparing.set(true);
    this.comparison.set(null);
    this.pageIndex.set(0);

    this.baselineService.compare(id).subscribe({
      next: (data) => {
        this.comparison.set(data);
        this.comparing.set(false);
      },
      error: () => {
        this.comparing.set(false);
        this.snackBar.open('Error al calcular la comparación.', 'Cerrar', {
          duration: 5000,
          panelClass: ['snack-error'],
        });
      },
    });
  }

  deleteBaseline(baseline: ProjectBaselineList): void {
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        title:   'Eliminar baseline',
        message: `¿Eliminar el baseline "${baseline.name}"? Esta acción no se puede deshacer.`,
        confirm: 'Eliminar',
        danger:  true,
      },
    });

    ref.afterClosed().subscribe((confirmed: boolean) => {
      if (!confirmed) return;

      this.baselineService.delete(baseline.id).subscribe({
        next: () => {
          if (this.selectedBaselineId() === baseline.id) {
            this.selectedBaselineId.set(null);
            this.comparison.set(null);
          }
          this.snackBar.open('Baseline eliminado.', 'Cerrar', {
            duration: 3000,
            panelClass: ['snack-success'],
          });
          this.loadBaselines();
        },
        error: () => {
          this.snackBar.open('Error al eliminar el baseline. El baseline activo no puede eliminarse.', 'Cerrar', {
            duration: 5000,
            panelClass: ['snack-error'],
          });
        },
      });
    });
  }

  onPage(event: PageEvent): void {
    this.pageIndex.set(event.pageIndex);
  }

  onBaselineSelect(id: string): void {
    this.selectedBaselineId.set(id);
    this.comparison.set(null);
  }

  statusLabel(status: 'ahead' | 'on_schedule' | 'behind'): string {
    const map: Record<string, string> = {
      ahead:       'Adelantada',
      on_schedule: 'En plazo',
      behind:      'Retrasada',
    };
    return map[status] ?? status;
  }
}
