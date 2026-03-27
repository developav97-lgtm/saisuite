/**
 * SaiSuite — ConfiguracionComponent (Proyectos)
 * Página de configuración del módulo de proyectos.
 * Consume GET/PATCH /api/v1/projects/config/
 */
import {
  ChangeDetectionStrategy, ChangeDetectorRef,
  Component, OnInit, inject, signal,
} from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatDividerModule } from '@angular/material/divider';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ConfiguracionProyectoService } from '../../services/configuracion-proyecto.service';
import { ConfiguracionProyecto, ModoTimesheet } from '../../models/configuracion-proyecto.model';

interface ModoOpcion {
  value: ModoTimesheet;
  label: string;
  icon: string;
  description: string;
}

@Component({
  selector: 'app-configuracion-proyecto',
  templateUrl: './configuracion.component.html',
  styleUrl: './configuracion.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ReactiveFormsModule,
    MatButtonModule, MatCardModule, MatCheckboxModule,
    MatDividerModule, MatFormFieldModule, MatIconModule,
    MatInputModule, MatProgressSpinnerModule, MatSelectModule,
  ],
})
export class ConfiguracionComponent implements OnInit {
  private readonly fb            = inject(FormBuilder);
  private readonly configService = inject(ConfiguracionProyectoService);
  private readonly snackBar      = inject(MatSnackBar);
  private readonly cdr           = inject(ChangeDetectorRef);

  readonly loading = signal(true);
  readonly saving  = signal(false);

  readonly form = this.fb.group({
    modo_timesheet:                      ['ambos' as ModoTimesheet],
    requiere_sync_saiopen_para_ejecucion: [false],
    dias_alerta_vencimiento:              [15, [Validators.min(1), Validators.max(365)]],
  });

  readonly modosTimesheet: ModoOpcion[] = [
    {
      value: 'manual',
      label: 'Manual',
      icon: 'edit_note',
      description: 'Los usuarios agregan horas haciendo click en "Horas registradas" en el detalle de la tarea. Ideal para registros al final del día.',
    },
    {
      value: 'cronometro',
      label: 'Cronómetro',
      icon: 'timer',
      description: 'Los usuarios inician un cronómetro en el detalle de la tarea. Las horas se suman automáticamente al detenerlo. Ideal para máxima precisión.',
    },
    {
      value: 'ambos',
      label: 'Ambos modos (recomendado)',
      icon: 'tune',
      description: 'Los usuarios ven tanto el input manual como el cronómetro y pueden elegir el que prefieran. Máxima flexibilidad.',
    },
    {
      value: 'desactivado',
      label: 'Desactivado',
      icon: 'block',
      description: 'El registro de tiempo no está disponible para los usuarios. Las horas estimadas siguen siendo visibles.',
    },
  ];

  private savedConfig: ConfiguracionProyecto | null = null;

  ngOnInit(): void {
    this.configService.obtener().subscribe({
      next: (config) => {
        this.savedConfig = config;
        this.form.patchValue({
          modo_timesheet:                      config.modo_timesheet,
          requiere_sync_saiopen_para_ejecucion: config.requiere_sync_saiopen_para_ejecucion,
          dias_alerta_vencimiento:              config.dias_alerta_vencimiento,
        });
        this.loading.set(false);
        this.cdr.markForCheck();
      },
      error: () => {
        this.snackBar.open('Error al cargar la configuración.', 'Cerrar', {
          duration: 4000, panelClass: ['snack-error'],
        });
        this.loading.set(false);
        this.cdr.markForCheck();
      },
    });
  }

  guardar(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.saving.set(true);

    this.configService.actualizar(this.form.getRawValue() as Partial<ConfiguracionProyecto>).subscribe({
      next: (config) => {
        this.savedConfig = config;
        this.saving.set(false);
        this.snackBar.open('Configuración guardada correctamente.', 'Cerrar', {
          duration: 2500, panelClass: ['snack-success'],
        });
        this.cdr.markForCheck();
      },
      error: () => {
        this.saving.set(false);
        this.snackBar.open('Error al guardar la configuración.', 'Cerrar', {
          duration: 4000, panelClass: ['snack-error'],
        });
        this.cdr.markForCheck();
      },
    });
  }

  cancelar(): void {
    if (!this.savedConfig) return;
    this.form.patchValue({
      modo_timesheet:                      this.savedConfig.modo_timesheet,
      requiere_sync_saiopen_para_ejecucion: this.savedConfig.requiere_sync_saiopen_para_ejecucion,
      dias_alerta_vencimiento:              this.savedConfig.dias_alerta_vencimiento,
    });
    this.form.markAsPristine();
  }

  modoSeleccionado(): ModoOpcion | undefined {
    return this.modosTimesheet.find(m => m.value === this.form.value.modo_timesheet);
  }
}
