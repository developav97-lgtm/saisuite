import {
  ChangeDetectionStrategy, Component, OnInit, inject, signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatButtonModule } from '@angular/material/button';
import { HttpClient } from '@angular/common/http';
import { ToastService } from '../../../core/services/toast.service';

export interface ConfiguracionModulo {
  requiere_sync_saiopen_para_ejecucion: boolean;
  dias_alerta_vencimiento: number;
}

@Component({
  selector: 'app-proyectos-config',
  templateUrl: './proyectos-config.component.html',
  styleUrl: './proyectos-config.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatIconModule,
    MatProgressBarModule,
    MatFormFieldModule,
    MatInputModule,
    MatSlideToggleModule,
    MatButtonModule,
  ],
})
export class ProyectosConfigComponent implements OnInit {
  private readonly http     = inject(HttpClient);
  private readonly fb       = inject(FormBuilder);
  private readonly toast       = inject(ToastService);

  private readonly apiUrl = '/api/v1/proyectos/config/';

  readonly loading = signal(false);
  readonly saving  = signal(false);

  readonly form = this.fb.group({
    requiere_sync_saiopen_para_ejecucion: [false],
    dias_alerta_vencimiento: [15, [Validators.required, Validators.min(1), Validators.max(365)]],
  });

  ngOnInit(): void {
    this.loading.set(true);
    this.http.get<ConfiguracionModulo>(this.apiUrl).subscribe({
      next: (config) => {
        this.form.patchValue(config);
        this.loading.set(false);
      },
      error: () => { this.loading.set(false); },
    });
  }

  guardar(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.saving.set(true);
    this.http.patch<ConfiguracionModulo>(this.apiUrl, this.form.value).subscribe({
      next: (config) => {
        this.form.patchValue(config);
        this.saving.set(false);
        this.toast.success('Configuración guardada.');
      },
      error: () => {
        this.saving.set(false);
        this.toast.error('Error al guardar configuración.');
      },
    });
  }
}
