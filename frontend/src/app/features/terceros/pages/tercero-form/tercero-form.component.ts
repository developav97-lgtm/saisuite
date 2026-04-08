import {
  ChangeDetectionStrategy, Component, OnInit,
  inject, signal, computed,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router, ActivatedRoute, RouterModule } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { TerceroService } from '../../../../core/services/tercero.service';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { ToastService } from '../../../../core/services/toast.service';
import { QuickAccessNavigatorService } from '../../../../shared/services/quick-access-navigator.service';
import {
  TerceroCreate, TerceroDireccion,
  TipoIdentificacion, TipoPersona, TipoTercero, TipoDireccion,
} from '../../../../core/models/tercero.model';
import {
  COLOMBIA_DEPARTAMENTOS, COLOMBIA_CIUDADES,
} from '../../../../shared/data/colombia-geo';

const FORM_EMPTY = {
  tipo_persona:          'natural'   as TipoPersona,
  tipo_identificacion:   'nit'       as TipoIdentificacion,
  numero_identificacion: '',
  primer_nombre:         '',
  segundo_nombre:        '',
  primer_apellido:       '',
  segundo_apellido:      '',
  razon_social:          '',
  tipo_tercero:          ''          as TipoTercero | '',
  email:                 '',
  telefono:              '',
  celular:               '',
};

const DIR_EMPTY = {
  agregar:           false,
  tipo:              'principal' as TipoDireccion,
  nombre_sucursal:   '',
  departamento:      '',
  ciudad:            '',
  direccion_linea1:  '',
  direccion_linea2:  '',
  nombre_contacto:   '',
  telefono_contacto: '',
  email_contacto:    '',
};

@Component({
  selector: 'app-tercero-form',
  templateUrl: './tercero-form.component.html',
  styleUrl: './tercero-form.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, ReactiveFormsModule, RouterModule,
    MatButtonModule, MatIconModule,
    MatFormFieldModule, MatInputModule, MatSelectModule,
    MatAutocompleteModule,
    MatTooltipModule, MatProgressSpinnerModule,
    MatDialogModule,
  ],
})
export class TerceroFormComponent implements OnInit {
  private readonly service    = inject(TerceroService);
  private readonly fb         = inject(FormBuilder);
  private readonly router     = inject(Router);
  private readonly route      = inject(ActivatedRoute);
  private readonly toast      = inject(ToastService);
  private readonly dialog     = inject(MatDialog);
  private readonly navigator  = inject(QuickAccessNavigatorService);

  readonly editId  = signal<string | null>(null);
  readonly loading = signal(false);
  readonly saving  = signal(false);

  // Direcciones existentes (solo en edición)
  readonly direcciones    = signal<TerceroDireccion[]>([]);
  readonly editingDirId   = signal<string | null>(null);
  readonly showNewDirForm = signal(false);
  readonly savingDir      = signal(false);

  // Autocomplete geo
  readonly deptQuery     = signal('');
  readonly cityQuery     = signal('');
  readonly deptoActivo   = signal('');   // depto seleccionado para filtrar ciudades

  readonly deptoOptions = computed(() => {
    const q = this.deptQuery().toLowerCase();
    if (!q) return COLOMBIA_DEPARTAMENTOS;
    return COLOMBIA_DEPARTAMENTOS.filter(d => d.nombre.toLowerCase().includes(q));
  });

  readonly cityOptions = computed(() => {
    const depto = COLOMBIA_DEPARTAMENTOS.find(d => d.nombre === this.deptoActivo());
    if (!depto) return [];
    const q = this.cityQuery().toLowerCase();
    return COLOMBIA_CIUDADES
      .filter(c => c.departamento === depto.codigo)
      .filter(c => !q || c.nombre.toLowerCase().includes(q));
  });

  readonly editMode = computed(() => !!this.editId());

  readonly tipoIdentificacionLabel = computed(() => {
    const val = this.form.get('tipo_identificacion')?.value;
    return this.tipoIdentificacionOptions.find(o => o.value === val)?.label ?? val ?? '';
  });

  readonly tipoPersonaOptions = [
    { value: 'natural',  label: 'Persona natural'   },
    { value: 'juridica', label: 'Persona jurídica'  },
  ];
  readonly tipoIdentificacionOptions = [
    { value: 'nit',  label: 'NIT'                   },
    { value: 'cc',   label: 'Cédula de ciudadanía'  },
    { value: 'ce',   label: 'Cédula de extranjería' },
    { value: 'pas',  label: 'Pasaporte'             },
    { value: 'otro', label: 'Otro'                  },
  ];
  readonly tipoTerceroOptions = [
    { value: '',              label: '— Sin clasificar —' },
    { value: 'cliente',       label: 'Cliente'            },
    { value: 'proveedor',     label: 'Proveedor'          },
    { value: 'subcontratista',label: 'Subcontratista'     },
    { value: 'interventor',   label: 'Interventor'        },
    { value: 'consultor',     label: 'Consultor'          },
    { value: 'empleado',      label: 'Empleado'           },
    { value: 'otro',          label: 'Otro'               },
  ];
  readonly tipoDireccionOptions = [
    { value: 'principal',   label: 'Principal'    },
    { value: 'sucursal',    label: 'Sucursal'     },
    { value: 'bodega',      label: 'Bodega'       },
    { value: 'facturacion', label: 'Facturación'  },
    { value: 'otro',        label: 'Otro'         },
  ];

  // ── Form principal ─────────────────────────────────────────────────────────
  readonly form = this.fb.group({
    tipo_persona:          [FORM_EMPTY.tipo_persona,          Validators.required],
    tipo_identificacion:   [FORM_EMPTY.tipo_identificacion,   Validators.required],
    numero_identificacion: [FORM_EMPTY.numero_identificacion, Validators.required],
    primer_nombre:         [FORM_EMPTY.primer_nombre],
    segundo_nombre:        [FORM_EMPTY.segundo_nombre],
    primer_apellido:       [FORM_EMPTY.primer_apellido],
    segundo_apellido:      [FORM_EMPTY.segundo_apellido],
    razon_social:          [FORM_EMPTY.razon_social],
    tipo_tercero:          [FORM_EMPTY.tipo_tercero],
    email:                 [FORM_EMPTY.email, Validators.email],
    telefono:              [FORM_EMPTY.telefono],
    celular:               [FORM_EMPTY.celular],
  });

  // ── Form dirección ─────────────────────────────────────────────────────────
  readonly dirForm = this.fb.group({
    agregar:           [false],
    tipo:              [DIR_EMPTY.tipo as TipoDireccion],
    nombre_sucursal:   [DIR_EMPTY.nombre_sucursal],
    departamento:      [DIR_EMPTY.departamento],
    ciudad:            [DIR_EMPTY.ciudad],
    direccion_linea1:  [DIR_EMPTY.direccion_linea1],
    direccion_linea2:  [DIR_EMPTY.direccion_linea2],
    nombre_contacto:   [DIR_EMPTY.nombre_contacto],
    telefono_contacto: [DIR_EMPTY.telefono_contacto],
    email_contacto:    [DIR_EMPTY.email_contacto],
  });

  get tipoPersonaActual(): TipoPersona {
    return (this.form.get('tipo_persona')?.value ?? 'natural') as TipoPersona;
  }

  get agregarDir(): boolean {
    return !!this.dirForm.get('agregar')?.value;
  }

  ngOnInit(): void {
    const id = this.navigator.isActive
      ? this.navigator.getParam('id')
      : this.route.snapshot.paramMap.get('id');
    if (id) {
      this.editId.set(id);
      this.loading.set(true);
      this.service.get(id).subscribe({
        next: (t) => {
          this.form.reset({ ...FORM_EMPTY, ...t });
          this.direcciones.set(t.direcciones ?? []);
          this.loading.set(false);
        },
        error: () => {
          this.toast.error('No se encontró el tercero.');
          if (this.navigator.isActive) {
            this.navigator.requestGoBack();
          } else {
            this.router.navigate(['/terceros']);
          }
        },
      });
    }
  }

  // ── Autocomplete handlers ──────────────────────────────────────────────────

  onDeptoInput(event: Event): void {
    this.deptQuery.set((event.target as HTMLInputElement).value);
  }

  onDeptoSelected(nombre: string): void {
    this.deptoActivo.set(nombre);
    this.deptQuery.set('');
    this.cityQuery.set('');
    this.dirForm.patchValue({ ciudad: '' });
  }

  onCityInput(event: Event): void {
    this.cityQuery.set((event.target as HTMLInputElement).value);
  }

  private resetGeoSignals(): void {
    this.deptQuery.set('');
    this.cityQuery.set('');
    this.deptoActivo.set('');
  }

  // ── Guardar datos del tercero ──────────────────────────────────────────────
  guardar(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }

    // Validación: debe haber al menos una dirección
    if (this.editMode()) {
      if (this.direcciones().length === 0) {
        this.toast.error('Debe agregar al menos una dirección antes de guardar.');
        return;
      }
    } else {
      if (!this.agregarDir) {
        this.toast.error('Debe agregar al menos una dirección antes de guardar.');
        return;
      }
    }

    if (this.agregarDir) {
      const d = this.dirForm;
      d.get('departamento')?.setValidators(Validators.required);
      d.get('ciudad')?.setValidators(Validators.required);
      d.get('direccion_linea1')?.setValidators(Validators.required);
      d.updateValueAndValidity();
      if (d.invalid) { d.markAllAsTouched(); return; }
    }

    this.saving.set(true);
    const raw = this.form.getRawValue();
    const payload: TerceroCreate = {
      tipo_persona:          raw.tipo_persona          as TipoPersona,
      tipo_identificacion:   raw.tipo_identificacion   as TipoIdentificacion,
      numero_identificacion: raw.numero_identificacion ?? '',
      primer_nombre:         raw.primer_nombre         ?? '',
      segundo_nombre:        raw.segundo_nombre        ?? '',
      primer_apellido:       raw.primer_apellido       ?? '',
      segundo_apellido:      raw.segundo_apellido      ?? '',
      razon_social:          raw.razon_social          ?? '',
      tipo_tercero:          (raw.tipo_tercero         ?? '') as TipoTercero | '',
      email:                 raw.email                 ?? '',
      telefono:              raw.telefono              ?? '',
      celular:               raw.celular               ?? '',
    };

    const id = this.editId();
    const tercero$ = id
      ? this.service.update(id, payload)
      : this.service.create(payload);

    tercero$.subscribe({
      next: (t) => {
        if (!id && this.agregarDir) {
          const d = this.dirForm.getRawValue();
          this.service.addDireccion(t.id, {
            tipo:              d.tipo as TipoDireccion,
            nombre_sucursal:   d.nombre_sucursal   ?? '',
            pais:              'Colombia',
            departamento:      d.departamento      ?? '',
            ciudad:            d.ciudad            ?? '',
            direccion_linea1:  d.direccion_linea1  ?? '',
            direccion_linea2:  d.direccion_linea2  ?? '',
            nombre_contacto:   d.nombre_contacto   ?? '',
            telefono_contacto: d.telefono_contacto ?? '',
            email_contacto:    d.email_contacto    ?? '',
            es_principal:      d.tipo === 'principal',
            activa:            true,
          }).subscribe();
        }
        this.saving.set(false);
        this.toast.success(`Tercero ${id ? 'actualizado' : 'creado'} correctamente.`);
        if (this.navigator.isActive) {
          this.navigator.requestGoBack();
        } else {
          this.router.navigate(['/terceros']);
        }
      },
      error: (err: { error?: Record<string, string[]> }) => {
        this.saving.set(false);
        const msg = err.error ? Object.values(err.error).flat()[0] : 'Error al guardar.';
        this.toast.error(msg ?? 'Error al guardar.');
      },
    });
  }

  // ── Gestión de direcciones en edición ─────────────────────────────────────

  abrirEditarDir(dir: TerceroDireccion): void {
    this.showNewDirForm.set(false);
    this.editingDirId.set(dir.id);
    this.deptoActivo.set(dir.departamento ?? '');
    this.deptQuery.set('');
    this.cityQuery.set('');
    this.dirForm.reset({
      agregar:           true,
      tipo:              dir.tipo,
      nombre_sucursal:   dir.nombre_sucursal   ?? '',
      departamento:      dir.departamento      ?? '',
      ciudad:            dir.ciudad            ?? '',
      direccion_linea1:  dir.direccion_linea1  ?? '',
      direccion_linea2:  dir.direccion_linea2  ?? '',
      nombre_contacto:   dir.nombre_contacto   ?? '',
      telefono_contacto: dir.telefono_contacto ?? '',
      email_contacto:    dir.email_contacto    ?? '',
    });
  }

  abrirNuevaDir(): void {
    this.editingDirId.set(null);
    this.showNewDirForm.set(true);
    this.resetGeoSignals();
    this.dirForm.reset({ ...DIR_EMPTY, agregar: true });
  }

  cancelarDir(): void {
    this.editingDirId.set(null);
    this.showNewDirForm.set(false);
    this.resetGeoSignals();
    this.dirForm.reset(DIR_EMPTY);
  }

  guardarDir(): void {
    const d = this.dirForm;
    d.get('departamento')?.setValidators(Validators.required);
    d.get('ciudad')?.setValidators(Validators.required);
    d.get('direccion_linea1')?.setValidators(Validators.required);
    d.updateValueAndValidity();
    if (d.invalid) { d.markAllAsTouched(); return; }

    const raw = d.getRawValue();

    // Validación: no permitir múltiples direcciones principales
    if (raw.tipo === 'principal') {
      const dirId = this.editingDirId();
      const yaHayPrincipal = this.direcciones().some(
        dir => dir.es_principal && dir.id !== dirId,
      );
      if (yaHayPrincipal) {
        this.toast.info('Ya existe una dirección principal. Edítala y cambia su tipo antes de asignar otra.');
        return;
      }
    }
    const dirData: Partial<TerceroDireccion> = {
      tipo:              raw.tipo as TipoDireccion,
      nombre_sucursal:   raw.nombre_sucursal   ?? '',
      pais:              'Colombia',
      departamento:      raw.departamento      ?? '',
      ciudad:            raw.ciudad            ?? '',
      direccion_linea1:  raw.direccion_linea1  ?? '',
      direccion_linea2:  raw.direccion_linea2  ?? '',
      nombre_contacto:   raw.nombre_contacto   ?? '',
      telefono_contacto: raw.telefono_contacto ?? '',
      email_contacto:    raw.email_contacto    ?? '',
      es_principal:      raw.tipo === 'principal',
      activa:            true,
    };

    const terceroId = this.editId()!;
    const dirId = this.editingDirId();
    this.savingDir.set(true);

    const op$ = dirId
      ? this.service.updateDireccion(terceroId, dirId, dirData)
      : this.service.addDireccion(terceroId, dirData);

    op$.subscribe({
      next: (updated) => {
        this.savingDir.set(false);
        if (dirId) {
          this.direcciones.update(dirs => dirs.map(d => d.id === dirId ? updated : d));
        } else {
          this.direcciones.update(dirs => [...dirs, updated]);
        }
        this.cancelarDir();
        this.toast.success('Dirección guardada.');
      },
      error: () => {
        this.savingDir.set(false);
        this.toast.error('Error al guardar la dirección.');
      },
    });
  }

  confirmarEliminarDir(dir: TerceroDireccion): void {
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        header:      'Eliminar dirección',
        message:     `¿Eliminar la dirección en ${dir.ciudad}?`,
        acceptLabel: 'Eliminar',
        acceptColor: 'warn',
      },
      width: '380px',
    });
    ref.afterClosed().subscribe((confirmed: boolean) => {
      if (!confirmed) return;
      this.service.deleteDireccion(this.editId()!, dir.id).subscribe({
        next: () => {
          this.direcciones.update(dirs => dirs.filter(d => d.id !== dir.id));
          if (this.editingDirId() === dir.id) this.cancelarDir();
          this.toast.success('Dirección eliminada.');
        },
        error: () => {
          this.toast.error('No se pudo eliminar la dirección.');
        },
      });
    });
  }

  cancelar(): void {
    if (this.navigator.isActive) {
      this.navigator.requestGoBack();
    } else {
      this.router.navigate(['/terceros']);
    }
  }
}
