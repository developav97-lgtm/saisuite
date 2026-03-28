/**
 * SaiSuite — WhatIfScenarioBuilderComponent (SK-39)
 * Lista escenarios what-if de un proyecto, permite crearlos y simularlos.
 * La configuración de cambios detallados (task_changes, resource_changes) es trabajo futuro (Chunk 8).
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
import { ReactiveFormsModule, FormControl, FormGroup, Validators } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDividerModule } from '@angular/material/divider';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { WhatIfService } from '../../../services/what-if.service';
import {
  WhatIfScenarioList,
  WhatIfScenarioDetail,
} from '../../../models/what-if.model';
import { ConfirmDialogComponent } from '../../../../../shared/components/confirm-dialog/confirm-dialog.component';

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
    MatTooltipModule,
    MatDividerModule,
  ],
})
export class WhatIfScenarioBuilderComponent implements OnInit {
  readonly projectId = input.required<string>();

  private readonly whatIfService = inject(WhatIfService);
  private readonly dialog        = inject(MatDialog);
  private readonly snackBar      = inject(MatSnackBar);

  readonly scenarios        = signal<WhatIfScenarioList[]>([]);
  readonly selectedScenario = signal<WhatIfScenarioDetail | null>(null);
  readonly loading          = signal(false);
  readonly simulating       = signal(false);
  readonly saving           = signal(false);
  readonly showCreateForm   = signal(false);

  readonly displayedColumns = ['nombre', 'estado', 'resultado', 'acciones'];

  readonly createForm = new FormGroup({
    name:        new FormControl<string>('', { nonNullable: true, validators: [Validators.required, Validators.maxLength(120)] }),
    description: new FormControl<string>('', { nonNullable: true }),
  });

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
        this.snackBar.open('Error al cargar los escenarios.', 'Cerrar', {
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

  createScenario(): void {
    if (this.createForm.invalid) return;

    this.saving.set(true);
    const { name, description } = this.createForm.getRawValue();

    this.whatIfService.create(this.projectId(), {
      name,
      description: description || undefined,
      // Backend requiere al menos un cambio; se crea con un placeholder mínimo.
      dependency_changes: { new: { retraso_dias: 0 } },
    }).subscribe({
      next: () => {
        this.saving.set(false);
        this.showCreateForm.set(false);
        this.createForm.reset();
        this.snackBar.open('Escenario creado correctamente.', 'Cerrar', {
          duration: 3000,
          panelClass: ['snack-success'],
        });
        this.loadScenarios();
      },
      error: () => {
        this.saving.set(false);
        this.snackBar.open('Error al crear el escenario. Verifica los datos.', 'Cerrar', {
          duration: 5000,
          panelClass: ['snack-error'],
        });
      },
    });
  }

  selectScenario(id: string): void {
    this.whatIfService.get(id).subscribe({
      next: (detail) => {
        this.selectedScenario.set(detail);
      },
      error: () => {
        this.snackBar.open('Error al cargar el detalle del escenario.', 'Cerrar', {
          duration: 5000,
          panelClass: ['snack-error'],
        });
      },
    });
  }

  runSimulation(scenarioId: string): void {
    this.simulating.set(true);

    this.whatIfService.runSimulation(scenarioId).subscribe({
      next: (detail) => {
        this.simulating.set(false);
        this.selectedScenario.set(detail);
        this.snackBar.open('Simulación completada correctamente.', 'Cerrar', {
          duration: 3000,
          panelClass: ['snack-success'],
        });
        this.loadScenarios();
      },
      error: () => {
        this.simulating.set(false);
        this.snackBar.open('Error al ejecutar la simulación.', 'Cerrar', {
          duration: 5000,
          panelClass: ['snack-error'],
        });
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
          this.snackBar.open('Escenario eliminado.', 'Cerrar', {
            duration: 3000,
            panelClass: ['snack-success'],
          });
          this.loadScenarios();
        },
        error: () => {
          this.snackBar.open('Error al eliminar el escenario.', 'Cerrar', {
            duration: 5000,
            panelClass: ['snack-error'],
          });
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
