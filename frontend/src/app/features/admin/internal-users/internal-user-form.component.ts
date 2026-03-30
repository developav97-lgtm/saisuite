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
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { InternalUsersService } from '../services/internal-users.service';
import { ToastService } from '../../../core/services/toast.service';

@Component({
  selector: 'app-internal-user-form',
  templateUrl: './internal-user-form.component.html',
  styleUrl: './internal-user-form.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, ReactiveFormsModule, RouterModule,
    MatFormFieldModule, MatInputModule, MatButtonModule,
    MatIconModule, MatSelectModule, MatProgressSpinnerModule,
  ],
})
export class InternalUserFormComponent implements OnInit {
  private readonly fb      = inject(FormBuilder);
  private readonly service = inject(InternalUsersService);
  private readonly route   = inject(ActivatedRoute);
  private readonly router  = inject(Router);
  private readonly toast   = inject(ToastService);

  readonly editingId = signal<string | null>(null);
  readonly loading   = signal(false);
  readonly saving    = signal(false);
  readonly hidePass  = signal(true);

  readonly form = this.fb.group({
    first_name:   ['', Validators.required],
    last_name:    ['', Validators.required],
    email:        ['', [Validators.required, Validators.email]],
    tipo:         ['soporte', Validators.required],  // 'superadmin' | 'soporte'
    password:     ['', [Validators.required, Validators.minLength(8)]],
  });

  get pageTitle(): string {
    return this.editingId() ? 'Editar usuario interno' : 'Nuevo usuario interno';
  }

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.editingId.set(id);
      this.form.controls.password.clearValidators();
      this.form.controls.password.updateValueAndValidity();
      this.loadUser(id);
    }
  }

  private loadUser(id: string): void {
    this.loading.set(true);
    this.service.get(id).subscribe({
      next: u => {
        this.form.patchValue({
          first_name: u.first_name,
          last_name:  u.last_name,
          email:      u.email,
          tipo:       u.is_superadmin ? 'superadmin' : 'soporte',
        });
        this.form.controls.email.disable();
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.toast.error('Error al cargar el usuario.');
      },
    });
  }

  guardar(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.saving.set(true);
    const val  = this.form.getRawValue();
    const id   = this.editingId();
    const tipo = val.tipo as 'superadmin' | 'soporte';

    const obs$ = id
      ? this.service.update(id, {
          first_name:   val.first_name!,
          last_name:    val.last_name!,
          is_superadmin: tipo === 'superadmin',
          is_staff:      true,
          ...(val.password ? { password: val.password } : {}),
        })
      : this.service.create({
          first_name:   val.first_name!,
          last_name:    val.last_name!,
          email:        val.email!,
          password:     val.password!,
          is_superadmin: tipo === 'superadmin',
          is_staff:      true,
        });

    obs$.subscribe({
      next: () => {
        this.saving.set(false);
        this.toast.success(id ? 'Usuario actualizado.' : 'Usuario creado.');
        this.router.navigate(['/admin/usuarios-internos']);
      },
      error: (err: { error?: Record<string, string[]> }) => {
        this.saving.set(false);
        const e = err?.error ?? {};
        const msg = Object.values(e).flat()[0] ?? 'Error al guardar.';
        this.toast.error(msg);
      },
    });
  }
}
