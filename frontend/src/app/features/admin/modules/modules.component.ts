import {
  ChangeDetectionStrategy, Component, OnInit, inject, signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { AdminService } from '../services/admin.service';
import { CompanyModule, CompanySettings, MODULE_LABELS, ModuleKey } from '../models/admin.models';
import { ToastService } from '../../../core/services/toast.service';

@Component({
  selector: 'app-modules',
  templateUrl: './modules.component.html',
  styleUrl: './modules.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    MatCardModule, MatSlideToggleModule,
    MatIconModule, MatProgressSpinnerModule,
  ],
})
export class ModulesComponent implements OnInit {
  private readonly adminService = inject(AdminService);
  private readonly toast       = inject(ToastService);

  readonly company  = signal<CompanySettings | null>(null);
  readonly loading  = signal(false);
  readonly toggling = signal<string | null>(null);

  readonly moduleLabels = MODULE_LABELS;
  readonly moduleIcons: Record<ModuleKey, string> = {
    crm:       'shopping_cart',
    soporte:   'account_balance_wallet',
    dashboard: 'home',
    proyectos: 'work',
  };

  ngOnInit(): void {
    this.loading.set(true);
    this.adminService.getCompanySettings().subscribe({
      next: (data) => { this.company.set(data); this.loading.set(false); },
      error: ()     => { this.loading.set(false); },
    });
  }

  toggle(mod: CompanyModule): void {
    const company = this.company();
    if (!company || this.toggling()) return;

    this.toggling.set(mod.module);
    const action = mod.is_active
      ? this.adminService.deactivateModule(company.id, mod.module)
      : this.adminService.activateModule(company.id, mod.module);

    action.subscribe({
      next: () => {
        this.company.update(c => c ? {
          ...c,
          modules: c.modules.map(m =>
            m.module === mod.module ? { ...m, is_active: !mod.is_active } : m
          ),
        } : c);
        this.toggling.set(null);
        this.toast.success(`Módulo ${this.moduleLabels[mod.module as ModuleKey]} ${mod.is_active ? 'desactivado' : 'activado'}.`);
      },
      error: () => {
        this.toggling.set(null);
        this.toast.error('No se pudo actualizar el módulo.');
      },
    });
  }
}
