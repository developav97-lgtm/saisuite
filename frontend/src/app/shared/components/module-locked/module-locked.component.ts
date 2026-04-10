import {
  ChangeDetectionStrategy, Component, OnInit, computed, inject, signal,
} from '@angular/core';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatDialog } from '@angular/material/dialog';
import { AuthService } from '../../../core/auth/auth.service';
import { ModuleTrialService } from '../../../core/services/module-trial.service';
import { ToastService } from '../../../core/services/toast.service';
import { AdminService } from '../../../features/admin/services/admin.service';
import { ModuleTrialStatus } from '../../../features/admin/models/tenant.model';
import { LicenseRequestDialogComponent } from '../../../features/admin/company-settings/license-request-dialog/license-request-dialog.component';

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
  private readonly adminService = inject(AdminService);
  private readonly dialog       = inject(MatDialog);

  readonly moduleCode      = signal('');
  readonly moduleName      = signal('');
  readonly trialStatus     = signal<ModuleTrialStatus | null>(null);
  readonly loading         = signal(true);
  readonly activating      = signal(false);
  readonly trialActivated  = signal(false);
  readonly requestSent     = signal(false);

  readonly isAdmin = computed(() => {
    const user = this.authService.currentUser();
    return user?.role === 'company_admin';
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

  solicitarLicencia(): void {
    this.adminService.getAvailablePackages('module').subscribe({
      next: (pkgs) => {
        const moduleCode = this.moduleCode();
        const filtered = pkgs.filter(p => p.module_code === moduleCode);
        if (filtered.length === 0) {
          this.toast.error('No hay paquetes disponibles para este módulo. Contacta a ventas@valmentech.com.');
          return;
        }
        const ref = this.dialog.open(LicenseRequestDialogComponent, {
          width: '480px',
          data: { requestType: 'module', packages: filtered },
        });
        ref.afterClosed().subscribe((result: { packageId: string; notes: string } | undefined) => {
          if (!result) return;
          this.adminService.createLicenseRequest({
            package_id:   result.packageId,
            request_type: 'module',
            notes:        result.notes,
          }).subscribe({
            next: () => {
              this.requestSent.set(true);
              this.toast.success('Solicitud enviada. El equipo de ValMen Tech la revisará pronto.');
            },
            error: (err) => {
              const msg = err?.error?.detail ?? err?.error?.[0] ?? 'No se pudo enviar la solicitud.';
              this.toast.error(msg);
            },
          });
        });
      },
      error: () => this.toast.error('Error al cargar paquetes disponibles.'),
    });
  }

  irAlModulo(): void {
    this.router.navigate([`/${this.moduleCode()}`]);
  }

  volver(): void {
    this.router.navigate(['/dashboard']);
  }
}
