import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';
import { MatStepperModule } from '@angular/material/stepper';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { AuthService } from '../../../core/auth/auth.service';
import { ToastService } from '../../../core/services/toast.service';

@Component({
  selector: 'app-register',
  templateUrl: './register.component.html',
  styleUrl: './register.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, ReactiveFormsModule, RouterModule,
    MatFormFieldModule, MatInputModule, MatButtonModule,
    MatIconModule, MatStepperModule,
    MatProgressSpinnerModule,
  ],
})
export class RegisterComponent {
  private readonly fb          = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly router      = inject(Router);
  private readonly toast       = inject(ToastService);

  readonly loading      = signal(false);
  readonly hidePassword = signal(true);

  /** Paso 1: datos de la empresa */
  readonly empresaForm = this.fb.group({
    company_name: ['', [Validators.required, Validators.minLength(3)]],
    company_nit:  ['', [Validators.required, Validators.pattern(/^\d{6,15}$/)]],
  });

  /** Paso 2: datos del usuario administrador */
  readonly usuarioForm = this.fb.group({
    first_name: ['', Validators.required],
    last_name:  ['', Validators.required],
    email:      ['', [Validators.required, Validators.email]],
    password:   ['', [Validators.required, Validators.minLength(8)]],
  });

  registrar(): void {
    if (this.empresaForm.invalid || this.usuarioForm.invalid) {
      this.empresaForm.markAllAsTouched();
      this.usuarioForm.markAllAsTouched();
      return;
    }
    this.loading.set(true);
    const e = this.empresaForm.getRawValue();
    const u = this.usuarioForm.getRawValue();

    this.authService.register({
      company_name: e.company_name!,
      company_nit:  e.company_nit!,
      first_name:   u.first_name!,
      last_name:    u.last_name!,
      email:        u.email!,
      password:     u.password!,
    }).subscribe({
      next: () => {
        this.loading.set(false);
        this.toast.success('¡Empresa creada! Bienvenido a Saicloud.');
        this.router.navigate(['/dashboard']);
      },
      error: (err: { error?: Record<string, string[]> }) => {
        this.loading.set(false);
        const e = err?.error ?? {};
        const firstMsg = Object.values(e).flat()[0] ?? 'Error al crear la empresa.';
        this.toast.error(String(firstMsg));
      },
    });
  }
}
