/**
 * SaiSuite — CRM Dashboard Page
 * KPIs, embudo de ventas y forecast.
 */
import {
  ChangeDetectionStrategy, Component, OnInit, OnDestroy,
  inject, signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatButtonModule } from '@angular/material/button';
import { MatTableModule } from '@angular/material/table';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Subject, takeUntil } from 'rxjs';

import { CrmService } from '../../services/crm.service';
import { CrmDashboard, CrmForecast } from '../../models/crm.model';
import { ToastService } from '../../../../core/services/toast.service';

@Component({
  selector: 'app-crm-dashboard-page',
  templateUrl: './crm-dashboard-page.component.html',
  styleUrl: './crm-dashboard-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, MatCardModule, MatIconModule,
    MatProgressBarModule, MatButtonModule, MatTableModule, MatTooltipModule,
  ],
})
export class CrmDashboardPageComponent implements OnInit, OnDestroy {
  private readonly crm     = inject(CrmService);
  private readonly toast   = inject(ToastService);
  private readonly destroy$ = new Subject<void>();

  readonly dashboard = signal<CrmDashboard | null>(null);
  readonly forecast  = signal<CrmForecast | null>(null);
  readonly loading   = signal(false);

  readonly vendedoresColumns = ['nombre', 'activas', 'ganadas_mes', 'valor_ganado_mes'];

  ngOnInit(): void {
    this.loading.set(true);
    this.crm.getDashboard().pipe(takeUntil(this.destroy$)).subscribe({
      next: dash => {
        this.dashboard.set(dash);
        this.loading.set(false);
      },
      error: () => {
        this.toast.error('Error cargando dashboard');
        this.loading.set(false);
      },
    });

    this.crm.getForecast().pipe(takeUntil(this.destroy$)).subscribe({
      next: f => this.forecast.set(f),
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  formatMoney(val: string | number): string {
    const n = typeof val === 'string' ? parseFloat(val) : val;
    return new Intl.NumberFormat('es-CO', {
      style: 'currency', currency: 'COP', maximumFractionDigits: 0,
    }).format(n || 0);
  }

  formatPercent(val: string): string {
    return `${parseFloat(val || '0').toFixed(1)}%`;
  }
}
