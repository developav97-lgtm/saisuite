import {
  ChangeDetectionStrategy, Component, OnInit, computed, inject, signal,
} from '@angular/core';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { AuthService } from '../../../core/auth/auth.service';
import { ModuleTrialService } from '../../../core/services/module-trial.service';
import { ToastService } from '../../../core/services/toast.service';
import { ModuleTrialStatus } from '../../../features/admin/models/tenant.model';

const MODULE_NAMES: Record<string, string> = {
  proyectos: 'SaiProyectos',
  dashboard: 'SaiDashboard',
  crm:       'CRM',
  soporte:   'Soporte',
};

@Component({
  selector: 'app-module-locked',
  templateUrl: './module-locked.component.html',
  styleUrl: './module-locked.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatButtonModule, MatIconModule, MatProgressBarModule, RouterModule],
})
export class ModuleLockedComponent implements OnInit {
  private readonly route        = inject(ActivatedRoute);
  private readonly router       = inject(Router);
  private readonly authService  = inject(AuthService);
  private readonly trialService = inject(ModuleTrialService);
  private readonly toast        = inject(ToastService);

  readonly moduleCode     = signal('');
  readonly moduleName     = signal('');
  readonly trialStatus    = signal<ModuleTrialStatus | null>(null);
  readonly loading        = signal(true);
  readonly activating     = signal(false);
  readonly trialActivated = signal(false);

  readonly isAdmin = computed(() => {
    const user = this.authService.currentUser();
    return user?.tipo_usuario === 'admin_tenant' || user?.role === 'company_admin';
  });

  ngOnInit(): void {
    const code = this.route.snapshot.queryParamMap.get('module') ?? '';
    this.moduleCode.set(code);
    this.moduleName.set(MODULE_NAMES[code] ?? code);

    if (code) {
      this.trialService.getStatus(code).subscribe({
        next: s  => { this.trialStatus.set(s); this.loading.set(false); },
        error: () => { this.loading.set(false); },
      });
    } else {
      this.loading.set(false);
    }
  }

  activarTrial(): void {
    const code = this.moduleCode();
    this.activating.set(true);
    this.trialService.activateTrial(code).subscribe({
      next: () => {
        this.activating.set(false);
        this.trialActivated.set(true);
        this.toast.success(`Prueba gratuita de 14 días activada para ${this.moduleName()}`);
        // Refrescar estado
        this.trialService.getStatus(code).subscribe({
          next: s  => this.trialStatus.set(s),
          error: () => {},
        });
      },
      error: (err: { error?: { detail?: string } }) => {
        this.activating.set(false);
        this.toast.error(err?.error?.detail ?? 'Error al activar la prueba');
      },
    });
  }

  irAlModulo(): void {
    const code = this.moduleCode();
    this.router.navigate([`/${code}`]);
  }

  volver(): void {
    this.router.navigate(['/dashboard']);
  }
}
