import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { AuthService } from '../../../core/auth/auth.service';
import { ToastService } from '../../../core/services/toast.service';

@Component({
  selector: 'app-reset-password',
  imports: [
    ReactiveFormsModule, RouterModule,
    MatFormFieldModule, MatInputModule,
    MatButtonModule, MatIconModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './reset-password.component.html',
  styleUrl: './reset-password.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ResetPasswordComponent implements OnInit {
  private readonly fb          = inject(FormBuilder);
  private readonly route       = inject(ActivatedRoute);
  private readonly router      = inject(Router);
  private readonly authService = inject(AuthService);
  private readonly toast       = inject(ToastService);

  readonly loading      = signal(false);
  readonly done         = signal(false);
  readonly hidePassword = signal(true);
  private uid   = '';
  private token = '';

  readonly form = this.fb.group({
    password:  ['', [Validators.required, Validators.minLength(8)]],
    password2: ['', Validators.required],
  });

  ngOnInit(): void {
    this.uid   = this.route.snapshot.queryParamMap.get('uid')   ?? '';
    this.token = this.route.snapshot.queryParamMap.get('token') ?? '';
    if (!this.uid || !this.token) {
      this.toast.error('Enlace de recuperación inválido.');
      this.router.navigate(['/auth/login']);
    }
  }

  onSubmit(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    const { password, password2 } = this.form.getRawValue();
    if (password !== password2) {
      this.toast.error('Las contraseñas no coinciden.');
      return;
    }
    this.loading.set(true);
    this.authService.confirmPasswordReset(this.uid, this.token, password!).subscribe({
      next: () => { this.loading.set(false); this.done.set(true); },
      error: (err) => {
        this.loading.set(false);
        const msg = (err as { error?: { detail?: string } })?.error?.detail ?? 'El enlace ha expirado o es inválido.';
        this.toast.error(msg);
      },
    });
  }
}
