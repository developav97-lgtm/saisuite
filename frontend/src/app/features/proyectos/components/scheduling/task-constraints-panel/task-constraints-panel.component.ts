/**
 * SaiSuite — TaskConstraintsPanelComponent (SK-37)
 * Panel para gestionar restricciones de scheduling de una tarea.
 * Se muestra como sub-panel dentro del detalle de una tarea.
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
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { SchedulingService } from '../../../services/scheduling.service';
import {
  TaskConstraint,
  ConstraintType,
} from '../../../models/scheduling.model';
import { ConfirmDialogComponent } from '../../../../../shared/components/confirm-dialog/confirm-dialog.component';

const CONSTRAINT_OPTIONS: { value: ConstraintType; label: string }[] = [
  { value: 'ASAP',                    label: 'Lo antes posible (ASAP)' },
  { value: 'ALAP',                    label: 'Lo más tarde posible (ALAP)' },
  { value: 'MUST_START_ON',           label: 'Debe empezar en' },
  { value: 'MUST_FINISH_ON',          label: 'Debe terminar en' },
  { value: 'START_NO_EARLIER_THAN',   label: 'Empezar no antes de' },
  { value: 'START_NO_LATER_THAN',     label: 'Empezar no después de' },
  { value: 'FINISH_NO_EARLIER_THAN',  label: 'Terminar no antes de' },
  { value: 'FINISH_NO_LATER_THAN',    label: 'Terminar no después de' },
];

const DATE_TYPES: ConstraintType[] = [
  'MUST_START_ON',
  'MUST_FINISH_ON',
  'START_NO_EARLIER_THAN',
  'START_NO_LATER_THAN',
  'FINISH_NO_EARLIER_THAN',
  'FINISH_NO_LATER_THAN',
];

@Component({
  selector: 'app-task-constraints-panel',
  templateUrl: './task-constraints-panel.component.html',
  styleUrl: './task-constraints-panel.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DatePipe,
    FormsModule,
    MatButtonModule,
    MatIconModule,
    MatListModule,
    MatSelectModule,
    MatFormFieldModule,
    MatInputModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatProgressBarModule,
    MatTooltipModule,
  ],
})
export class TaskConstraintsPanelComponent implements OnInit {
  readonly taskId = input.required<string>();

  private readonly schedulingService = inject(SchedulingService);
  private readonly dialog            = inject(MatDialog);
  private readonly snackBar          = inject(MatSnackBar);

  readonly constraints   = signal<TaskConstraint[]>([]);
  readonly loading       = signal(false);
  readonly saving        = signal(false);
  readonly selectedType  = signal<ConstraintType>('ASAP');
  readonly constraintDate = signal<string | null>(null);

  readonly constraintOptions = CONSTRAINT_OPTIONS;

  /** Computed: el tipo seleccionado requiere fecha */
  readonly requiresDate = computed(() => DATE_TYPES.includes(this.selectedType()));

  ngOnInit(): void {
    this.loadConstraints();
  }

  loadConstraints(): void {
    this.loading.set(true);
    this.schedulingService.getConstraints(this.taskId()).subscribe({
      next: (data) => {
        this.constraints.set(data);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.snackBar.open('Error al cargar restricciones', 'Cerrar', {
          duration: 5000,
          panelClass: ['snack-error'],
        });
      },
    });
  }

  addConstraint(): void {
    if (this.requiresDate() && !this.constraintDate()) {
      this.snackBar.open('Este tipo de restricción requiere una fecha.', 'Cerrar', {
        duration: 4000,
        panelClass: ['snack-warning'],
      });
      return;
    }

    this.saving.set(true);
    this.schedulingService.setConstraint(this.taskId(), {
      constraint_type: this.selectedType(),
      constraint_date: this.requiresDate() ? this.constraintDate() : null,
    }).subscribe({
      next: () => {
        this.saving.set(false);
        this.constraintDate.set(null);
        this.selectedType.set('ASAP');
        this.snackBar.open('Restricción guardada correctamente.', 'Cerrar', {
          duration: 3000,
          panelClass: ['snack-success'],
        });
        this.loadConstraints();
      },
      error: () => {
        this.saving.set(false);
        this.snackBar.open('Error al guardar la restricción.', 'Cerrar', {
          duration: 5000,
          panelClass: ['snack-error'],
        });
      },
    });
  }

  removeConstraint(constraint: TaskConstraint): void {
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        title:   'Eliminar restricción',
        message: `¿Eliminar la restricción "${constraint.constraint_type_display}"?`,
        confirm: 'Eliminar',
        danger:  true,
      },
    });

    ref.afterClosed().subscribe((confirmed: boolean) => {
      if (!confirmed) return;

      this.schedulingService.deleteConstraint(constraint.id).subscribe({
        next: () => {
          this.snackBar.open('Restricción eliminada.', 'Cerrar', {
            duration: 3000,
            panelClass: ['snack-success'],
          });
          this.loadConstraints();
        },
        error: () => {
          this.snackBar.open('Error al eliminar la restricción.', 'Cerrar', {
            duration: 5000,
            panelClass: ['snack-error'],
          });
        },
      });
    });
  }

  onTypeChange(type: ConstraintType): void {
    this.selectedType.set(type);
    if (!DATE_TYPES.includes(type)) {
      this.constraintDate.set(null);
    }
  }

  onDateChange(value: Date | null): void {
    if (!value) {
      this.constraintDate.set(null);
      return;
    }
    // Formato YYYY-MM-DD
    const y = value.getFullYear();
    const m = String(value.getMonth() + 1).padStart(2, '0');
    const d = String(value.getDate()).padStart(2, '0');
    this.constraintDate.set(`${y}-${m}-${d}`);
  }
}
