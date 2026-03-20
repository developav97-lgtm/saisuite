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
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { TerceroService } from '../../../../core/services/tercero.service';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import {
  TerceroCreate, TerceroDireccion,
  TipoIdentificacion, TipoPersona, TipoTercero, TipoDireccion,
} from '../../../../core/models/tercero.model';

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
  agregar: false,
  tipo:              'principal' as TipoDireccion,
  nombre_sucursal:   '',
  pais:              'Colombia',
  departamento:      '',
  ciudad:            '',
  direccion_linea1:  '',
  direccion_linea2:  '',
  codigo_postal:     '',
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
    MatTooltipModule, MatProgressSpinnerModule,
    MatDialogModule,
  ],
})
export class TerceroFormComponent implements OnInit {
  private readonly service = inject(TerceroService);
  private readonly fb      = inject(FormBuilder);
  private readonly router  = inject(Router);
  private readonly route   = inject(ActivatedRoute);
  private readonly snack   = inject(MatSnackBar);
  private readonly dialog  = inject(MatDialog);

  readonly editId  = signal<string | null>(null);
  readonly loading = signal(false);
  readonly saving  = signal(false);

  // Direcciones existentes (solo en edición)
  readonly direcciones       = signal<TerceroDireccion[]>([]);
  readonly editingDirId      = signal<string | null>(null);   // id de la dirección en edición inline
  readonly showNewDirForm    = signal(false);                  // mostrar form de nueva dirección
  readonly savingDir         = signal(false);

  readonly editMode = computed(() => !!this.editId());

  readonly tipoPersonaOptions     = [
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

  // ── Form dirección (al crear o al agregar/editar en edición) ───────────────
  readonly dirForm = this.fb.group({
    agregar: [false],
    tipo:              [DIR_EMPTY.tipo as TipoDireccion],
    nombre_sucursal:   [DIR_EMPTY.nombre_sucursal],
    pais:              [DIR_EMPTY.pais],
    departamento:      [DIR_EMPTY.departamento],
    ciudad:            [DIR_EMPTY.ciudad],
    direccion_linea1:  [DIR_EMPTY.direccion_linea1],
    direccion_linea2:  [DIR_EMPTY.direccion_linea2],
    codigo_postal:     [DIR_EMPTY.codigo_postal],
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
    const id = this.route.snapshot.paramMap.get('id');
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
          this.snack.open('No se encontró el tercero.', 'Cerrar', { duration: 4000 });
          this.router.navigate(['/terceros']);
        },
      });
    }
  }

  // ── Guardar datos del tercero ──────────────────────────────────────────────
  guardar(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }

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
            pais:              d.pais              ?? 'Colombia',
            departamento:      d.departamento      ?? '',
            ciudad:            d.ciudad            ?? '',
            direccion_linea1:  d.direccion_linea1  ?? '',
            direccion_linea2:  d.direccion_linea2  ?? '',
            codigo_postal:     d.codigo_postal     ?? '',
            nombre_contacto:   d.nombre_contacto   ?? '',
            telefono_contacto: d.telefono_contacto ?? '',
            email_contacto:    d.email_contacto    ?? '',
            es_principal:      d.tipo === 'principal',
            activa:            true,
          }).subscribe();
        }
        this.saving.set(false);
        this.snack.open(
          `Tercero ${id ? 'actualizado' : 'creado'} correctamente.`,
          'Cerrar',
          { duration: 3000, panelClass: ['snack-success'] },
        );
        this.router.navigate(['/terceros']);
      },
      error: (err: { error?: Record<string, string[]> }) => {
        this.saving.set(false);
        const msg = err.error ? Object.values(err.error).flat()[0] : 'Error al guardar.';
        this.snack.open(msg ?? 'Error al guardar.', 'Cerrar', { duration: 5000, panelClass: ['snack-error'] });
      },
    });
  }

  // ── Gestión de direcciones en edición ─────────────────────────────────────

  abrirEditarDir(dir: TerceroDireccion): void {
    this.showNewDirForm.set(false);
    this.editingDirId.set(dir.id);
    this.dirForm.reset({
      agregar:           true,
      tipo:              dir.tipo,
      nombre_sucursal:   dir.nombre_sucursal,
      pais:              dir.pais,
      departamento:      dir.departamento,
      ciudad:            dir.ciudad,
      direccion_linea1:  dir.direccion_linea1,
      direccion_linea2:  dir.direccion_linea2,
      codigo_postal:     dir.codigo_postal,
      nombre_contacto:   dir.nombre_contacto,
      telefono_contacto: dir.telefono_contacto,
      email_contacto:    dir.email_contacto,
    });
  }

  abrirNuevaDir(): void {
    this.editingDirId.set(null);
    this.showNewDirForm.set(true);
    this.dirForm.reset({ ...DIR_EMPTY, agregar: true });
  }

  cancelarDir(): void {
    this.editingDirId.set(null);
    this.showNewDirForm.set(false);
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
    const dirData: Partial<TerceroDireccion> = {
      tipo:              raw.tipo as TipoDireccion,
      nombre_sucursal:   raw.nombre_sucursal   ?? '',
      pais:              raw.pais              ?? 'Colombia',
      departamento:      raw.departamento      ?? '',
      ciudad:            raw.ciudad            ?? '',
      direccion_linea1:  raw.direccion_linea1  ?? '',
      direccion_linea2:  raw.direccion_linea2  ?? '',
      codigo_postal:     raw.codigo_postal     ?? '',
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
        this.snack.open('Dirección guardada.', 'Cerrar', { duration: 2500, panelClass: ['snack-success'] });
      },
      error: () => {
        this.savingDir.set(false);
        this.snack.open('Error al guardar la dirección.', 'Cerrar', { duration: 4000, panelClass: ['snack-error'] });
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
          this.snack.open('Dirección eliminada.', 'Cerrar', { duration: 2500, panelClass: ['snack-success'] });
        },
        error: () => {
          this.snack.open('No se pudo eliminar la dirección.', 'Cerrar', { duration: 4000, panelClass: ['snack-error'] });
        },
      });
    });
  }

  cancelar(): void {
    this.router.navigate(['/terceros']);
  }
}
