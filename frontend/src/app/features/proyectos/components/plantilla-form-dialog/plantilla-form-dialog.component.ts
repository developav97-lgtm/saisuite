/**
 * SaiSuite — PlantillaFormDialogComponent
 * Dialog para crear y editar plantillas de proyecto.
 * Formulario reactivo con fases y tareas anidadas.
 */
import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  OnInit,
  signal,
} from '@angular/core';
import {
  FormArray,
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatAutocompleteModule, MatAutocompleteSelectedEvent } from '@angular/material/autocomplete';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatDialogModule, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatTooltipModule } from '@angular/material/tooltip';

import { ProyectoService } from '../../services/proyecto.service';
import { ActividadService } from '../../services/actividad.service';
import { ToastService } from '../../../../core/services/toast.service';
import { ActividadList } from '../../models/actividad.model';
import {
  PlantillaProyecto,
  PlantillaProyectoCreate,
  PlantillaFaseCreate,
  PlantillaTareaCreate,
  TipoProyecto,
  TIPO_LABELS,
} from '../../models/proyecto.model';

export interface PlantillaFormDialogData {
  plantilla?: PlantillaProyecto;
}

interface TareaFormGroup {
  nombre:               FormControl<string>;
  descripcion:          FormControl<string>;
  orden:                FormControl<number>;
  duracion_dias:        FormControl<number>;
  /** ID de la actividad — enviado al backend */
  actividad_saiopen_id: FormControl<string | null>;
  /** Objeto actividad o texto de búsqueda — solo para el autocomplete */
  actividad_display:    FormControl<ActividadList | string | null>;
}

interface FaseFormGroup {
  nombre:              FormControl<string>;
  descripcion:         FormControl<string>;
  orden:               FormControl<number>;
  porcentaje_duracion: FormControl<number>;
  tareas:              FormArray<FormGroup<TareaFormGroup>>;
}

@Component({
  selector: 'app-plantilla-form-dialog',
  templateUrl: './plantilla-form-dialog.component.html',
  styleUrl: './plantilla-form-dialog.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatIconModule,
    MatInputModule,
    MatFormFieldModule,
    MatSelectModule,
    MatAutocompleteModule,
    MatProgressBarModule,
    MatDialogModule,
    MatTooltipModule,
  ],
})
export class PlantillaFormDialogComponent implements OnInit {
  private readonly dialogRef    = inject(MatDialogRef<PlantillaFormDialogComponent>);
  private readonly data         = inject<PlantillaFormDialogData>(MAT_DIALOG_DATA);
  private readonly proyectoSvc  = inject(ProyectoService);
  private readonly actividadSvc = inject(ActividadService);
  private readonly toast        = inject(ToastService);

  readonly saving      = signal(false);
  readonly actividades = signal<ActividadList[]>([]);
  readonly isEdit      = !!this.data?.plantilla;
  readonly title       = this.isEdit ? 'Editar plantilla' : 'Nueva plantilla';

  /** Texto de búsqueda compartido — solo un autocomplete abierto a la vez */
  readonly actividadSearch = signal('');

  readonly filteredActividades = computed(() => {
    const q = this.actividadSearch().toLowerCase().trim();
    if (!q) return this.actividades();
    return this.actividades().filter(a =>
      a.nombre.toLowerCase().includes(q) || a.codigo.toLowerCase().includes(q),
    );
  });

  /** Función displayWith para mat-autocomplete */
  readonly displayActividad = (v: ActividadList | string | null): string => {
    if (!v) return '';
    if (typeof v === 'string') return v;
    return `${v.codigo} — ${v.nombre} (${v.unidad_medida})`;
  };

  /** IDs a resolver en ngOnInit (edición) */
  private readonly editActividadIds: { fi: number; ti: number; id: string }[] = [];

  readonly tipoOptions: { label: string; value: TipoProyecto }[] =
    (Object.entries(TIPO_LABELS) as [TipoProyecto, string][]).map(
      ([value, label]) => ({ value, label }),
    );

  readonly iconOptions: { label: string; value: string }[] = [
    { label: 'Carpeta',       value: 'folder'      },
    { label: 'Construcción',  value: 'construction' },
    { label: 'Computadora',   value: 'computer'     },
    { label: 'Herramienta',   value: 'build'        },
    { label: 'Equipo',        value: 'groups'       },
    { label: 'Asignación',    value: 'assignment'   },
    { label: 'Configuración', value: 'settings'     },
  ];

  readonly form = new FormGroup({
    nombre:            new FormControl('', { nonNullable: true, validators: [Validators.required, Validators.maxLength(200)] }),
    descripcion:       new FormControl('', { nonNullable: true }),
    tipo:              new FormControl<TipoProyecto>('' as TipoProyecto, { nonNullable: true, validators: [Validators.required] }),
    icono:             new FormControl('folder', { nonNullable: true }),
    duracion_estimada: new FormControl(30, { nonNullable: true, validators: [Validators.required, Validators.min(1)] }),
    fases:             new FormArray<FormGroup<FaseFormGroup>>([]),
  });

  get fasesArray(): FormArray<FormGroup<FaseFormGroup>> {
    return this.form.controls.fases;
  }

  getTareasArray(faseIndex: number): FormArray<FormGroup<TareaFormGroup>> {
    return this.fasesArray.at(faseIndex).controls.tareas;
  }

  constructor() {
    if (this.isEdit && this.data.plantilla) {
      const p = this.data.plantilla;
      this.form.patchValue({
        nombre:            p.nombre,
        descripcion:       p.descripcion,
        tipo:              p.tipo,
        icono:             p.icono,
        duracion_estimada: p.duracion_estimada,
      });

      (p.fases ?? []).forEach((fase, fi) => {
        const faseGroup = this.buildFaseGroup(
          fase.nombre,
          fase.descripcion,
          fase.orden,
          parseFloat(fase.porcentaje_duracion),
        );
        (fase.tareas ?? []).forEach((tarea, ti) => {
          faseGroup.controls.tareas.push(
            this.buildTareaGroup(tarea.nombre, tarea.descripcion, tarea.orden, tarea.duracion_dias),
          );
          if (tarea.actividad_saiopen_id) {
            this.editActividadIds.push({ fi, ti, id: tarea.actividad_saiopen_id });
          }
        });
        this.fasesArray.push(faseGroup);
      });
    }
  }

  ngOnInit(): void {
    this.actividadSvc.list(undefined, undefined, 1, 200).subscribe({
      next: (res) => {
        this.actividades.set(res.results);
        // Restaurar objetos actividad en modo edición
        for (const { fi, ti, id } of this.editActividadIds) {
          const act = res.results.find(a => a.id === id);
          if (act) {
            const ctrl = this.getTareasArray(fi).at(ti).controls;
            ctrl.actividad_saiopen_id.setValue(act.id);
            ctrl.actividad_display.setValue(act);
          }
        }
      },
      error: () => { /* lista vacía — no bloquear formulario */ },
    });
  }

  /** Devuelve true cuando la tarea tiene una actividad real seleccionada */
  hasActividad(fi: number, ti: number): boolean {
    const v = this.getTareasArray(fi).at(ti).controls.actividad_display.value;
    return !!(v && typeof v === 'object');
  }

  /** Label dinámico de la unidad de medida según la actividad seleccionada */
  getUnidadLabel(fi: number, ti: number): string {
    const v = this.getTareasArray(fi).at(ti).controls.actividad_display.value;
    if (!v || typeof v === 'string') return 'Días';
    return v.unidad_medida || 'Días';
  }

  /** Llamado cuando el usuario selecciona una opción del autocomplete */
  onActividadSelected(fi: number, ti: number, event: MatAutocompleteSelectedEvent): void {
    const act = event.option.value as ActividadList | null;
    const ctrl = this.getTareasArray(fi).at(ti).controls;
    ctrl.actividad_saiopen_id.setValue(act?.id ?? null);
    ctrl.actividad_display.setValue(act ?? null);
    this.actividadSearch.set('');
  }

  /** Limpia la actividad seleccionada en una tarea */
  clearActividad(fi: number, ti: number): void {
    const ctrl = this.getTareasArray(fi).at(ti).controls;
    ctrl.actividad_saiopen_id.setValue(null);
    ctrl.actividad_display.setValue(null);
    this.actividadSearch.set('');
  }

  private buildFaseGroup(
    nombre = '',
    descripcion = '',
    orden = 0,
    porcentaje_duracion = 100,
  ): FormGroup<FaseFormGroup> {
    return new FormGroup<FaseFormGroup>({
      nombre:              new FormControl(nombre, { nonNullable: true, validators: [Validators.required, Validators.maxLength(255)] }),
      descripcion:         new FormControl(descripcion, { nonNullable: true }),
      orden:               new FormControl(orden, { nonNullable: true }),
      porcentaje_duracion: new FormControl(porcentaje_duracion, { nonNullable: true, validators: [Validators.required, Validators.min(1), Validators.max(100)] }),
      tareas:              new FormArray<FormGroup<TareaFormGroup>>([]),
    });
  }

  private buildTareaGroup(
    nombre = '',
    descripcion = '',
    orden = 0,
    duracion_dias = 1,
  ): FormGroup<TareaFormGroup> {
    return new FormGroup<TareaFormGroup>({
      nombre:               new FormControl(nombre, { nonNullable: true, validators: [Validators.required, Validators.maxLength(200)] }),
      descripcion:          new FormControl(descripcion, { nonNullable: true }),
      orden:                new FormControl(orden, { nonNullable: true }),
      duracion_dias:        new FormControl(duracion_dias, { nonNullable: true, validators: [Validators.required, Validators.min(1)] }),
      actividad_saiopen_id: new FormControl<string | null>(null),
      actividad_display:    new FormControl<ActividadList | string | null>(null),
    });
  }

  addFase(): void {
    const nextOrden = this.fasesArray.length;
    this.fasesArray.push(this.buildFaseGroup('', '', nextOrden, 100));
  }

  removeFase(index: number): void {
    this.fasesArray.removeAt(index);
  }

  addTarea(faseIndex: number): void {
    const tareasArr = this.getTareasArray(faseIndex);
    const nextOrden = tareasArr.length;
    tareasArr.push(this.buildTareaGroup('', '', nextOrden, 1));
  }

  removeTarea(faseIndex: number, tareaIndex: number): void {
    this.getTareasArray(faseIndex).removeAt(tareaIndex);
  }

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const raw = this.form.getRawValue();

    const payload: PlantillaProyectoCreate = {
      nombre:            raw.nombre,
      descripcion:       raw.descripcion,
      tipo:              raw.tipo,
      icono:             raw.icono,
      duracion_estimada: raw.duracion_estimada,
      fases: raw.fases.map((f, fi): PlantillaFaseCreate => ({
        nombre:              f.nombre,
        descripcion:         f.descripcion,
        orden:               f.orden !== 0 ? f.orden : fi,
        porcentaje_duracion: f.porcentaje_duracion,
        tareas: f.tareas.map((t, ti): PlantillaTareaCreate => ({
          nombre:               t.nombre,
          descripcion:          t.descripcion,
          orden:                t.orden !== 0 ? t.orden : ti,
          duracion_dias:        t.duracion_dias,
          actividad_saiopen_id: t.actividad_saiopen_id ?? null,
        })),
      })),
    };

    this.saving.set(true);

    const obs$ = this.isEdit && this.data.plantilla
      ? this.proyectoSvc.updateTemplate(this.data.plantilla.id, payload)
      : this.proyectoSvc.createTemplate(payload);

    obs$.subscribe({
      next: (plantilla) => {
        this.saving.set(false);
        const msg = this.isEdit ? 'Plantilla actualizada correctamente.' : 'Plantilla creada correctamente.';
        this.toast.success(msg);
        this.dialogRef.close(plantilla);
      },
      error: (err: unknown) => {
        this.saving.set(false);
        const errObj = err as { error?: { detail?: string } };
        const message = errObj?.error?.detail ?? 'Error al guardar la plantilla.';
        this.toast.error(message);
      },
    });
  }

  cancel(): void {
    this.dialogRef.close(null);
  }
}
