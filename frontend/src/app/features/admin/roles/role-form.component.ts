import {
  ChangeDetectionStrategy,
  Component,
  Inject,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import {
  MAT_DIALOG_DATA,
  MatDialogModule,
  MatDialogRef,
} from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatDividerModule } from '@angular/material/divider';
import {
  MODULO_NOMBRES,
  Permission,
  Role,
  RoleCreateDto,
  RolesService,
} from '../services/roles.service';

export interface RoleFormData {
  mode: 'create' | 'edit';
  rol?: Role;
  licenseModules: string[];
}

/** Un sub-módulo dentro de un grupo padre */
export interface SubModulo {
  clave: string;
  nombre: string;
  permisos: Permission[];
}

/** Un grupo padre de permisos (ej: Proyectos, Terceros, Administración) */
export interface GrupoPermisos {
  clave: string;
  nombre: string;
  submodulos: SubModulo[];
}

/** Permisos de admin relevantes para roles de empresa */
const ADMIN_PERMISOS_PERMITIDOS = ['usuarios', 'consecutivos', 'ver_empresa'];

/** Sub-módulos que se agrupan dentro de "Proyectos" */
const SUBMODULOS_PROYECTOS = ['actividades', 'tareas', 'timesheets'];

@Component({
  selector: 'app-role-form',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatDialogModule,
    MatButtonModule,
    MatCheckboxModule,
    MatExpansionModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressBarModule,
    MatDividerModule,
  ],
  template: `
    <h2 mat-dialog-title>
      {{ data.mode === 'create' ? 'Nuevo Rol' : 'Editar Rol' }}
    </h2>

    @if (loading()) {
      <mat-progress-bar mode="indeterminate" />
    }

    <form [formGroup]="form" (ngSubmit)="guardar()">
      <mat-dialog-content class="role-form-content">

        <mat-form-field appearance="outline" class="full-width">
          <mat-label>Nombre del Rol</mat-label>
          <input matInput formControlName="nombre" placeholder="Ej: Supervisor de Proyectos" />
          @if (form.get('nombre')?.hasError('required') && form.get('nombre')?.touched) {
            <mat-error>El nombre es requerido</mat-error>
          }
        </mat-form-field>

        <mat-form-field appearance="outline" class="full-width">
          <mat-label>Descripción</mat-label>
          <textarea
            matInput
            formControlName="descripcion"
            rows="2"
            placeholder="Descripción del rol y sus responsabilidades"
          ></textarea>
        </mat-form-field>

        <h3 class="permisos-titulo">
          <mat-icon>security</mat-icon>
          Permisos
          <span class="permisos-resumen">({{ totalSeleccionados() }} seleccionados)</span>
        </h3>

        @if (grupos().length === 0 && !loading()) {
          <p class="sin-permisos">No hay permisos disponibles.</p>
        }

        <mat-accordion multi>
          @for (grupo of grupos(); track grupo.clave) {
            <mat-expansion-panel>
              <mat-expansion-panel-header>
                <mat-panel-title class="panel-titulo">
                  <span class="grupo-nombre">{{ grupo.nombre }}</span>
                  <span class="contador"
                    [class.contador--parcial]="getSeleccionadosGrupo(grupo) > 0 && getSeleccionadosGrupo(grupo) < getTotalGrupo(grupo)"
                    [class.contador--completo]="getSeleccionadosGrupo(grupo) > 0 && getSeleccionadosGrupo(grupo) === getTotalGrupo(grupo)">
                    {{ getSeleccionadosGrupo(grupo) }}/{{ getTotalGrupo(grupo) }}
                  </span>
                </mat-panel-title>
              </mat-expansion-panel-header>

              <!-- Sub-módulos dentro del grupo -->
              @for (sub of grupo.submodulos; track sub.clave) {
                <div class="submodulo">
                  <div class="submodulo-header">
                    <span class="submodulo-nombre">{{ sub.nombre }}</span>
                    <div class="submodulo-acciones">
                      <span class="sub-contador"
                        [class.sub-contador--parcial]="getSeleccionadosEnModulo(sub.clave) > 0 && getSeleccionadosEnModulo(sub.clave) < sub.permisos.length"
                        [class.sub-contador--completo]="getSeleccionadosEnModulo(sub.clave) === sub.permisos.length">
                        {{ getSeleccionadosEnModulo(sub.clave) }}/{{ sub.permisos.length }}
                      </span>
                      <button mat-button type="button" class="btn-sel-todos"
                        (click)="toggleTodosSubmodulo(sub.clave, $event)">
                        {{ getSeleccionadosEnModulo(sub.clave) === sub.permisos.length ? 'Quitar todos' : 'Seleccionar todos' }}
                      </button>
                    </div>
                  </div>
                  <div class="permisos-grid">
                    @for (permiso of sub.permisos; track permiso.id) {
                      <mat-checkbox
                        [checked]="isSeleccionado(permiso.id)"
                        (change)="togglePermiso(permiso.id)"
                      >
                        <span class="permiso-nombre">{{ permiso.nombre }}</span>
                        @if (permiso.descripcion) {
                          <span class="permiso-desc">{{ permiso.descripcion }}</span>
                        }
                      </mat-checkbox>
                    }
                  </div>
                </div>
                @if (!$last) { <mat-divider /> }
              }
            </mat-expansion-panel>
          }
        </mat-accordion>

      </mat-dialog-content>

      <mat-dialog-actions align="end">
        <button mat-button type="button" (click)="cancelar()">Cancelar</button>
        <button
          mat-raised-button
          color="primary"
          type="submit"
          [disabled]="form.invalid || saving()"
        >
          {{ saving() ? 'Guardando...' : 'Guardar' }}
        </button>
      </mat-dialog-actions>
    </form>
  `,
  styles: [`
    :host {
      display: flex;
      flex-direction: column;
      height: 100%;
    }
    .role-form-content {
      width: 100%;
      flex: 1 1 auto;
      max-height: 75vh;
      padding-top: 8px;
      overflow-y: auto;
    }
    .full-width { width: 100%; margin-bottom: 8px; }
    .permisos-titulo {
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 16px 0 8px;
      font-size: 15px;
      font-weight: 500;
      color: var(--sc-text-primary, #212121);
    }
    .permisos-resumen { font-weight: 400; font-size: 13px; color: var(--sc-text-secondary, #757575); }
    .sin-permisos { color: var(--sc-text-secondary, #757575); font-size: 14px; }
    .panel-titulo {
      display: flex;
      align-items: center;
      justify-content: space-between;
      width: 100%;
    }
    .grupo-nombre { font-weight: 600; font-size: 15px; }
    .contador {
      font-size: 12px;
      color: var(--sc-text-secondary, #757575);
      margin-left: 8px;
    }
    .contador--parcial { color: #f57c00; }
    .contador--completo { color: #2e7d32; font-weight: 600; }

    /* Sub-módulo dentro del grupo */
    .submodulo { padding: 12px 0 8px; }
    .submodulo-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 8px;
    }
    .submodulo-nombre {
      font-size: 13px;
      font-weight: 600;
      color: var(--sc-text-secondary, #616161);
      text-transform: uppercase;
      letter-spacing: 0.4px;
    }
    .submodulo-acciones {
      display: flex;
      align-items: center;
      gap: 4px;
    }
    .sub-contador {
      font-size: 11px;
      color: var(--sc-text-secondary, #757575);
    }
    .sub-contador--parcial { color: #f57c00; }
    .sub-contador--completo { color: #2e7d32; font-weight: 600; }
    .btn-sel-todos { font-size: 12px; min-width: 0; padding: 0 8px; }
    .permisos-grid {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 4px 16px;
      padding: 4px 0;
    }
    .permiso-nombre { font-size: 14px; }
    .permiso-desc {
      display: block;
      font-size: 11px;
      color: var(--sc-text-secondary, #757575);
      margin-top: 1px;
    }
  `],
})
export class RoleFormComponent implements OnInit {
  private readonly fb           = inject(FormBuilder);
  private readonly rolesService = inject(RolesService);
  private readonly dialogRef    = inject(MatDialogRef<RoleFormComponent>);

  readonly loading  = signal(false);
  readonly saving   = signal(false);
  readonly permisosAgrupadosRaw = signal<Record<string, Permission[]>>({});
  readonly seleccionados        = signal<Set<number>>(new Set());

  /**
   * Construye los grupos padre con sub-módulos adentro:
   * - "Proyectos": proyectos + actividades + tareas + timesheets (si están en licencia)
   * - "Terceros": terceros (siempre)
   * - "Administración": admin filtrado a usuarios/consecutivos/ver_empresa (siempre)
   */
  readonly grupos = computed<GrupoPermisos[]>(() => {
    const raw     = this.permisosAgrupadosRaw();
    const license = this.data.licenseModules;
    const result: GrupoPermisos[] = [];

    // ── Grupo Proyectos ──────────────────────────────────────────────
    if (license.includes('proyectos')) {
      const submodulos: SubModulo[] = [];

      if (raw['proyectos']?.length) {
        submodulos.push({ clave: 'proyectos', nombre: 'Proyectos', permisos: raw['proyectos'] });
      }
      for (const sub of SUBMODULOS_PROYECTOS) {
        if (raw[sub]?.length) {
          submodulos.push({ clave: sub, nombre: MODULO_NOMBRES[sub] ?? sub, permisos: raw[sub] });
        }
      }

      if (submodulos.length) {
        result.push({ clave: 'grupo_proyectos', nombre: 'Proyectos', submodulos });
      }
    }

    // ── Otros módulos de licencia (no proyectos ni sus sub-módulos) ──
    for (const mod of license) {
      if (mod === 'proyectos') continue;
      if (!raw[mod]?.length) continue;
      result.push({
        clave: `grupo_${mod}`,
        nombre: MODULO_NOMBRES[mod] ?? mod,
        submodulos: [{ clave: mod, nombre: MODULO_NOMBRES[mod] ?? mod, permisos: raw[mod] }],
      });
    }

    // ── Terceros (siempre) ───────────────────────────────────────────
    if (raw['terceros']?.length) {
      result.push({
        clave: 'grupo_terceros',
        nombre: 'Terceros',
        submodulos: [{ clave: 'terceros', nombre: 'Terceros', permisos: raw['terceros'] }],
      });
    }

    // ── Administración (siempre, filtrado) ───────────────────────────
    const adminPermisos = (raw['admin'] ?? []).filter(p =>
      ADMIN_PERMISOS_PERMITIDOS.some(k => p.codigo.includes(k))
    );
    if (adminPermisos.length) {
      result.push({
        clave: 'grupo_admin',
        nombre: 'Administración',
        submodulos: [{ clave: 'admin', nombre: 'Administración', permisos: adminPermisos }],
      });
    }

    return result;
  });

  readonly totalSeleccionados = computed(() => this.seleccionados().size);

  readonly form = this.fb.group({
    nombre:      ['', Validators.required],
    descripcion: [''],
  });

  constructor(@Inject(MAT_DIALOG_DATA) readonly data: RoleFormData) {}

  ngOnInit(): void {
    this.loading.set(true);
    this.rolesService.obtenerPermisosAgrupados().subscribe({
      next: agrupados => {
        this.permisosAgrupadosRaw.set(agrupados);

        if (this.data.mode === 'edit' && this.data.rol) {
          this.form.patchValue({
            nombre:      this.data.rol.nombre,
            descripcion: this.data.rol.descripcion,
          });
          this.seleccionados.set(new Set(this.data.rol.permisos.map(p => p.id)));
        }

        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  isSeleccionado(id: number): boolean {
    return this.seleccionados().has(id);
  }

  togglePermiso(id: number): void {
    const next = new Set(this.seleccionados());
    if (next.has(id)) next.delete(id); else next.add(id);
    this.seleccionados.set(next);
  }

  getSeleccionadosEnModulo(clave: string): number {
    // Busca el sub-módulo por clave en todos los grupos
    for (const grupo of this.grupos()) {
      const sub = grupo.submodulos.find(s => s.clave === clave);
      if (sub) return sub.permisos.filter(p => this.isSeleccionado(p.id)).length;
    }
    return 0;
  }

  getSeleccionadosGrupo(grupo: GrupoPermisos): number {
    return grupo.submodulos.reduce((acc, sub) =>
      acc + sub.permisos.filter(p => this.isSeleccionado(p.id)).length, 0);
  }

  getTotalGrupo(grupo: GrupoPermisos): number {
    return grupo.submodulos.reduce((acc, sub) => acc + sub.permisos.length, 0);
  }

  toggleTodosSubmodulo(clave: string, event: Event): void {
    event.stopPropagation();
    const sub = this.grupos().flatMap(g => g.submodulos).find(s => s.clave === clave);
    if (!sub) return;
    const todosOn = sub.permisos.every(p => this.isSeleccionado(p.id));
    const next = new Set(this.seleccionados());
    if (todosOn) {
      sub.permisos.forEach(p => next.delete(p.id));
    } else {
      sub.permisos.forEach(p => next.add(p.id));
    }
    this.seleccionados.set(next);
  }

  guardar(): void {
    if (this.form.invalid) return;

    const payload: RoleCreateDto = {
      nombre:       this.form.value.nombre!,
      descripcion:  this.form.value.descripcion ?? '',
      permisos_ids: Array.from(this.seleccionados()),
    };

    this.saving.set(true);

    const req$ = this.data.mode === 'create'
      ? this.rolesService.crear(payload)
      : this.rolesService.actualizar(this.data.rol!.id, payload);

    req$.subscribe({
      next: rol  => { this.saving.set(false); this.dialogRef.close(rol); },
      error: ()  => this.saving.set(false),
    });
  }

  cancelar(): void {
    this.dialogRef.close(null);
  }
}
