import {
  ChangeDetectionStrategy, Component, OnInit, inject, signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { AdminService } from '../services/admin.service';
import { MODULE_LABELS, ROLE_OPTIONS } from '../models/admin.models';
import { ToastService } from '../../../core/services/toast.service';
import { AuthService } from '../../../core/auth/auth.service';
import { RoleSummary, RolesService } from '../services/roles.service';
import { QuickAccessNavigatorService } from '../../../shared/services/quick-access-navigator.service';
import { NavigationHistoryService } from '../../../core/services/navigation-history.service';

@Component({
  selector: 'app-user-form',
  templateUrl: './user-form.component.html',
  styleUrl: './user-form.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, ReactiveFormsModule, RouterModule,
    MatFormFieldModule, MatInputModule, MatButtonModule,
    MatIconModule, MatSelectModule, MatCheckboxModule,
    MatProgressSpinnerModule,
  ],
})
export class UserFormComponent implements OnInit {
  private readonly fb           = inject(FormBuilder);
  private readonly adminService = inject(AdminService);
  private readonly rolesService = inject(RolesService);
  private readonly route        = inject(ActivatedRoute);
  private readonly router       = inject(Router);
  private readonly toast        = inject(ToastService);
  private readonly authService  = inject(AuthService);
  private readonly navigator    = inject(QuickAccessNavigatorService);
  private readonly navHistory   = inject(NavigationHistoryService);

  readonly editingId   = signal<string | null>(null);
  readonly loading     = signal(false);
  readonly saving      = signal(false);
  readonly hidePass    = signal(true);
  readonly rolesDisp   = signal<RoleSummary[]>([]);

  readonly roleOptions = ROLE_OPTIONS;

  /** Módulos contratados en la licencia de la empresa activa. */
  get licenseModules(): string[] {
    const user = this.authService.currentUser();
    const ec = user?.effective_company ?? user?.company;
    return ec?.license?.modules_included ?? [];
  }

  get moduleEntries(): [string, string][] {
    return this.licenseModules
      .filter(m => MODULE_LABELS[m] !== undefined)
      .map(m => [m, MODULE_LABELS[m] as string]);
  }

  get isAdmin(): boolean {
    return this.form.controls.role.value === 'company_admin';
  }

  /** El rol del sistema fuerza un rol granular fijo (admin/viewer), no se debe mostrar selector. */
  get rolGranularFijo(): boolean {
    const r = this.form.controls.role.value;
    return r === 'company_admin' || r === 'viewer';
  }

  /** Roles disponibles para selección manual: solo los de tipo 'custom'. */
  get rolesCustom(): import('../services/roles.service').RoleSummary[] {
    return this.rolesDisp().filter(r => r.tipo === 'custom');
  }

  readonly form = this.fb.group({
    first_name:      ['', Validators.required],
    last_name:       ['', Validators.required],
    email:           ['', [Validators.required, Validators.email]],
    role:            ['company_admin', Validators.required],
    password:        ['', [Validators.required, Validators.minLength(8)]],
    modules_access:  [[] as string[]],
    rol_granular_id: [null as number | null],
  });

  ngOnInit(): void {
    // Validación inicial según rol por defecto
    this.actualizarValidacionRolGranular(this.form.controls.role.value);

    // Cargar roles disponibles y luego aplicar defaults iniciales
    this.rolesService.listar().subscribe({
      next: roles => {
        this.rolesDisp.set(roles);
        // Al cargar, si no hay id (nuevo usuario), pre-asignar rol granular según role
        if (!this.editingId()) {
          this.autoAsignarRolGranular(this.form.controls.role.value);
        }
      },
      error: () => {},
    });

    // When role changes: auto-select modules + auto-asignar rol granular + validación dinámica
    this.form.controls.role.valueChanges.subscribe(role => {
      if (role === 'company_admin') {
        this.form.controls.modules_access.setValue(this.licenseModules);
      }
      this.autoAsignarRolGranular(role);
      this.actualizarValidacionRolGranular(role);
    });

    const id = this.navigator.isActive
      ? this.navigator.getParam('id')
      : this.route.snapshot.paramMap.get('id');
    if (id) {
      this.editingId.set(id);
      this.form.controls.password.clearValidators();
      this.form.controls.password.updateValueAndValidity();
      this.loadUser(id);
    } else {
      // New user: if default role is admin, pre-select all modules
      if (this.form.controls.role.value === 'company_admin') {
        this.form.controls.modules_access.setValue(this.licenseModules);
      }
    }
  }

  /** Aplica o quita la validación `required` en rol_granular_id según el tipo de rol. */
  private actualizarValidacionRolGranular(role: string | null): void {
    const ctrl = this.form.controls.rol_granular_id;
    const esFijo = role === 'company_admin' || role === 'viewer';
    if (esFijo) {
      ctrl.clearValidators();
    } else {
      ctrl.setValidators(Validators.required);
    }
    ctrl.updateValueAndValidity();
  }

  /** Asigna automáticamente el rol granular según el rol del sistema seleccionado.
   *  Para roles fijos (company_admin/viewer) siempre sobreescribe.
   *  Para otros roles solo actúa si el campo está vacío. */
  private autoAsignarRolGranular(role: string | null): void {
    const roles = this.rolesDisp();
    if (roles.length === 0) return;

    let tipoObjetivo: 'admin' | 'readonly' | null = null;
    if (role === 'company_admin') tipoObjetivo = 'admin';
    else if (role === 'viewer')   tipoObjetivo = 'readonly';

    if (tipoObjetivo) {
      // Rol fijo: siempre asignar (y el selector estará oculto)
      const match = roles.find(r => r.tipo === tipoObjetivo);
      if (match) this.form.controls.rol_granular_id.setValue(match.id);
    } else {
      // Rol de usuario (seller/collector/etc.): limpiar si venía de un rol fijo
      const current = this.form.controls.rol_granular_id.value;
      const currentRole = roles.find(r => r.id === current);
      if (currentRole && currentRole.tipo !== 'custom') {
        this.form.controls.rol_granular_id.setValue(null);
      }
    }
  }

  private loadUser(id: string): void {
    this.loading.set(true);
    this.adminService.getUser(id).subscribe({
      next: (u) => {
        this.form.patchValue({
          first_name:      u.first_name,
          last_name:       u.last_name,
          email:           u.email,
          role:            u.role,
          modules_access:  u.modules_access,
          rol_granular_id: u.rol_granular?.id ?? null,
        });
        // Si no tiene rol granular, auto-asignar según su role
        if (!u.rol_granular) {
          this.autoAsignarRolGranular(u.role);
        }
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.toast.error('Error al cargar el usuario.');
      },
    });
  }

  isModuleSelected(key: string): boolean {
    if (this.isAdmin) return true;
    return (this.form.controls.modules_access.value ?? []).includes(key);
  }

  toggleModule(key: string): void {
    if (this.isAdmin) return; // Admin always has all modules
    const current = this.form.controls.modules_access.value ?? [];
    const updated = current.includes(key)
      ? current.filter(k => k !== key)
      : [...current, key];
    this.form.controls.modules_access.setValue(updated);
  }

  volver(): void {
    if (this.navigator.isActive) {
      this.navigator.requestGoBack();
    } else {
      this.navHistory.goBack('/admin/usuarios');
    }
  }

  guardar(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.saving.set(true);
    const val = this.form.getRawValue();
    const id  = this.editingId();

    const action = id
      ? this.adminService.updateUser(id, {
          first_name:      val.first_name!,
          last_name:       val.last_name!,
          role:            val.role as never,
          modules_access:  val.modules_access ?? [],
          rol_granular_id: val.rol_granular_id ?? null,
          ...(val.password ? { password: val.password } : {}),
        })
      : this.adminService.createUser({
          first_name:     val.first_name!,
          last_name:      val.last_name!,
          email:          val.email!,
          role:           val.role as never,
          password:       val.password!,
          modules_access: val.modules_access ?? [],
        });

    action.subscribe({
      next: () => {
        this.saving.set(false);
        this.toast.success(id ? 'Actualizado.' : 'Creado.');
        if (this.navigator.isActive) {
          this.navigator.requestGoBack();
        } else {
          this.router.navigate(['/admin/usuarios']);
        }
      },
      error: (err: { error?: Record<string, string[]> }) => {
        this.saving.set(false);
        const e = err?.error ?? {};
        const msg = Object.values(e).flat()[0] ?? 'Error al guardar.';
        this.toast.info(msg);
      },
    });
  }
}
