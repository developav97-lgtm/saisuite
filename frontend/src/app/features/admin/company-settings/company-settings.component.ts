import {
  ChangeDetectionStrategy, Component, OnInit, inject, signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatChipsModule } from '@angular/material/chips';
import { AdminService } from '../services/admin.service';
import { CompanySettings, MODULE_LABELS } from '../models/admin.models';

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
    MatCardModule, MatIconModule,
    MatProgressSpinnerModule, MatChipsModule,
  ],
})
export class CompanySettingsComponent implements OnInit {
  private readonly adminService = inject(AdminService);

  readonly company = signal<CompanySettings | null>(null);
  readonly loading = signal(false);

  readonly planLabels   = PLAN_LABELS;
  readonly moduleLabels = MODULE_LABELS;

  ngOnInit(): void {
    this.loading.set(true);
    this.adminService.getCompanySettings().subscribe({
      next: (data) => { this.company.set(data); this.loading.set(false); },
      error: ()     => { this.loading.set(false); },
    });
  }
}
