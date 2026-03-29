/**
 * SaiSuite — WhatIfScenarioBuilderComponent (SK-39)
 * Lista escenarios what-if de un proyecto, permite crearlos y simularlos.
 * A-02: Formulario incluye task_changes (fecha_inicio, fecha_fin, horas_estimadas).
 */
import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  input,
  signal,
} from '@angular/core';
import { DatePipe } from '@angular/common';
import {
  ReactiveFormsModule,
  FormControl,
  FormGroup,
  FormArray,
  Validators,
} from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDividerModule } from '@angular/material/divider';
import { MatDialog } from '@angular/material/dialog';
import { WhatIfService } from '../../../services/what-if.service';
import {
  WhatIfScenarioList,
  WhatIfScenarioDetail,
} from '../../../models/what-if.model';
import { TareaService } from '../../../services/tarea.service';
import { Tarea } from '../../../models/tarea.model';
import { ConfirmDialogComponent } from '../../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { ToastService } from '../../../../../core/services/toast.service';

type TaskChangeCampo = 'fecha_inicio' | 'fecha_fin' | 'horas_estimadas';

interface TaskChangeRow {
  task_id: FormControl<string>;
  campo: FormControl<TaskChangeCampo>;
  valor: FormControl<string>;
}

@Component({
  selector: 'app-what-if-scenario-builder',
  templateUrl: './what-if-scenario-builder.component.html',
  styleUrl: './what-if-scenario-builder.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DatePipe,
    ReactiveFormsModule,
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatChipsModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatTooltipModule,
    MatDividerModule,
  ],
})
export class WhatIfScenarioBuilderComponent implements OnInit {
  readonly projectId = input.required<string>();

  private readonly whatIfService = inject(WhatIfService);
  private readonly tareaService  = inject(TareaService);
  private readonly dialog        = inject(MatDialog);
  private readonly toast       = inject(ToastService);

  readonly scenarios        = signal<WhatIfScenarioList[]>([]);
  readonly selectedScenario = signal<WhatIfScenarioDetail | null>(null);
  readonly loading          = signal(false);
  readonly simulating       = signal(false);
  readonly saving           = signal(false);
  readonly showCreateForm   = signal(false);
  readonly loadingTareas    = signal(false);
  readonly tareas           = signal<Tarea[]>([]);

  readonly displayedColumns = ['nombre', 'estado', 'resultado', 'acciones'];

  readonly campoOptions: { value: TaskChangeCampo; label: string }[] = [
    { value: 'fecha_inicio',     label: 'Fecha inicio' },
    { value: 'fecha_fin',        label: 'Fecha fin' },
    { value: 'horas_estimadas',  label: 'Horas estimadas' },
  ];

  readonly createForm = new FormGroup({
    name:              new FormControl<string>('', { nonNullable: true, validators: [Validators.required, Validators.maxLength(120)] }),
    description:       new FormControl<string>('', { nonNullable: true }),
    task_changes_list: new FormArray<FormGroup<TaskChangeRow>>([]),
  });

  get taskChangesList(): FormArray<FormGroup<TaskChangeRow>> {
    return this.createForm.controls['task_changes_list'] as FormArray<FormGroup<TaskChangeRow>>;
  }

  ngOnInit(): void {
    this.loadScenarios();
  }

  loadScenarios(): void {
    this.loading.set(true);
    this.whatIfService.list(this.projectId()).subscribe({
      next: (data) => {
        this.scenarios.set(data);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.toast.error('Error al cargar los escenarios.');
      },
    });
  }

  private loadTareas(): void {
    this.loadingTareas.set(true);
    this.tareaService.listByProyecto(this.projectId()).subscribe({
      next: (data) => {
        this.tareas.set(data);
        this.loadingTareas.set(false);
      },
      error: () => {
        this.loadingTareas.set(false);
        this.toast.error('Error al cargar las tareas del proyecto.');
      },
    });
  }

  toggleCreateForm(): void {
    this.showCreateForm.update(v => !v);
    if (this.showCreateForm()) {
      this.loadTareas();
    } else {
      this.createForm.reset();
      // Clear the FormArray on close
      while (this.taskChangesList.length > 0) {
        this.taskChangesList.removeAt(0);
      }
    }
  }

  addTaskChange(): void {
    const row = new FormGroup<TaskChangeRow>({
      task_id: new FormControl<string>('', { nonNullable: true, validators: [Validators.required] }),
      campo:   new FormControl<TaskChangeCampo>('fecha_inicio', { nonNullable: true, validators: [Validators.required] }),
      valor:   new FormControl<string>('', { nonNullable: true, validators: [Validators.required] }),
    });
    this.taskChangesList.push(row);
  }

  removeTaskChange(index: number): void {
    this.taskChangesList.removeAt(index);
  }

  getCampoControl(index: number): FormControl<TaskChangeCampo> {
    return this.taskChangesList.at(index).controls['campo'] as FormControl<TaskChangeCampo>;
  }

  createScenario(): void {
    if (this.createForm.invalid) return;

    this.saving.set(true);
    const { name, description } = this.createForm.getRawValue();

    // Build task_changes from FormArray
    const taskChanges: Record<string, Record<string, string | number | boolean>> = {};
    for (const row of this.taskChangesList.controls) {
      const { task_id, campo, valor } = row.getRawValue();
      if (!task_id || !campo || valor === '') continue;

      const parsed: string | number =
        campo === 'horas_estimadas' ? Number(valor) : valor;

      if (!taskChanges[task_id]) {
        taskChanges[task_id] = {};
      }
      taskChanges[task_id][campo] = parsed;
    }

    this.whatIfService.create(this.projectId(), {
      name,
      description: description || undefined,
      task_changes: taskChanges,
    }).subscribe({
      next: () => {
        this.saving.set(false);
        this.showCreateForm.set(false);
        this.createForm.reset();
        while (this.taskChangesList.length > 0) {
          this.taskChangesList.removeAt(0);
        }
        this.toast.success('Escenario creado correctamente.');
        this.loadScenarios();
      },
      error: () => {
        this.saving.set(false);
        this.toast.error('Error al crear el escenario. Verifica los datos.');
      },
    });
  }

  selectScenario(id: string): void {
    this.whatIfService.get(id).subscribe({
      next: (detail) => {
        this.selectedScenario.set(detail);
      },
      error: () => {
        this.toast.error('Error al cargar el detalle del escenario.');
      },
    });
  }

  runSimulation(scenarioId: string): void {
    this.simulating.set(true);

    this.whatIfService.runSimulation(scenarioId).subscribe({
      next: (detail) => {
        this.simulating.set(false);
        this.selectedScenario.set(detail);
        this.toast.success('Simulación completada correctamente.');
        this.loadScenarios();
      },
      error: () => {
        this.simulating.set(false);
        this.toast.error('Error al ejecutar la simulación.');
      },
    });
  }

  deleteScenario(scenario: WhatIfScenarioList): void {
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        title:   'Eliminar escenario',
        message: `¿Eliminar el escenario "${scenario.name}"? Esta acción no se puede deshacer.`,
        confirm: 'Eliminar',
        danger:  true,
      },
    });

    ref.afterClosed().subscribe((confirmed: boolean) => {
      if (!confirmed) return;

      this.whatIfService.delete(scenario.id).subscribe({
        next: () => {
          if (this.selectedScenario()?.id === scenario.id) {
            this.selectedScenario.set(null);
          }
          this.toast.success('Escenario eliminado.');
          this.loadScenarios();
        },
        error: () => {
          this.toast.error('Error al eliminar el escenario.');
        },
      });
    });
  }

  statusLabel(done: boolean): string {
    return done ? 'Simulado' : 'Pendiente';
  }

  deltaDaysDisplay(delta: number | null): string {
    if (delta === null) return '—';
    if (delta === 0) return 'Sin cambio';
    return `${delta > 0 ? '+' : ''}${delta} días`;
  }
}
