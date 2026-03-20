import {
  ChangeDetectionStrategy, Component, OnInit, inject, signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { AdminService } from '../services/admin.service';
import { CompanyLicense, CompanySettings, LICENSE_STATUS_LABELS, MODULE_LABELS } from '../models/admin.models';

const PLAN_LABELS: Record<string, string> = {
  starter:      'Starter',
  professional: 'Professional',
  enterprise:   'Enterprise',
};

@Component({
  selector: 'app-company-settings',
  templateUrl: './company-settings.component.html',
  styleUrl: './company-settings.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    MatIconModule,
    MatProgressBarModule,
  ],
})
export class CompanySettingsComponent implements OnInit {
  private readonly adminService = inject(AdminService);

  readonly company      = signal<CompanySettings | null>(null);
  readonly license      = signal<CompanyLicense | null>(null);
  readonly loading      = signal(false);

  readonly planLabels          = PLAN_LABELS;
  readonly moduleLabels        = MODULE_LABELS;
  readonly licenseStatusLabels = LICENSE_STATUS_LABELS;

  ngOnInit(): void {
    this.loading.set(true);
    this.adminService.getCompanySettings().subscribe({
      next: (data) => { this.company.set(data); this.loading.set(false); },
      error: ()     => { this.loading.set(false); },
    });
    this.adminService.getMyLicense().subscribe({
      next: (lic) => this.license.set(lic),
      error: () => { /* silencioso si no tiene licencia configurada */ },
    });
  }
}
