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
  private readonly route        = inject(ActivatedRoute);
  private readonly router       = inject(Router);
  private readonly toast       = inject(ToastService);

  readonly editingId  = signal<string | null>(null);
  readonly loading    = signal(false);
  readonly saving     = signal(false);
  readonly hidePass   = signal(true);

  readonly roleOptions   = ROLE_OPTIONS;
  readonly moduleEntries = Object.entries(MODULE_LABELS) as [string, string][];

  readonly form = this.fb.group({
    first_name:     ['', Validators.required],
    last_name:      ['', Validators.required],
    email:          ['', [Validators.required, Validators.email]],
    role:           ['company_admin', Validators.required],
    password:       ['', [Validators.required, Validators.minLength(8)]],
    modules_access: [[] as string[]],
  });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.editingId.set(id);
      // Password not required on edit
      this.form.controls.password.clearValidators();
      this.form.controls.password.updateValueAndValidity();
      this.loadUser(id);
    }
  }

  private loadUser(id: string): void {
    this.loading.set(true);
    this.adminService.getUser(id).subscribe({
      next: (u) => {
        this.form.patchValue({
          first_name:     u.first_name,
          last_name:      u.last_name,
          email:          u.email,
          role:           u.role,
          modules_access: u.modules_access,
        });
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.toast.error('Error al cargar el usuario.');
      },
    });
  }

  isModuleSelected(key: string): boolean {
    return (this.form.controls.modules_access.value ?? []).includes(key);
  }

  toggleModule(key: string): void {
    const current = this.form.controls.modules_access.value ?? [];
    const updated = current.includes(key)
      ? current.filter(k => k !== key)
      : [...current, key];
    this.form.controls.modules_access.setValue(updated);
  }

  guardar(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.saving.set(true);
    const val = this.form.getRawValue();
    const id  = this.editingId();

    const action = id
      ? this.adminService.updateUser(id, {
          first_name:     val.first_name!,
          last_name:      val.last_name!,
          role:           val.role as never,
          modules_access: val.modules_access ?? [],
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
        this.toast.success(id? 'Actualizado.' : 'Creado.');
        this.router.navigate(['/admin/usuarios']);
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
