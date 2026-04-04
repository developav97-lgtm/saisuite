import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';

export type KpiFormat = 'currency' | 'percent' | 'number';

@Component({
  selector: 'app-kpi-card',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatIconModule],
  template: `
    <div class="kpi-card">
      <p class="kpi-label">{{ title() }}</p>
      <p class="kpi-value">{{ formattedValue() }}</p>
      @if (previousValue() !== undefined && previousValue() !== null) {
        <div class="kpi-trend" [class.kpi-trend--up]="trendUp()" [class.kpi-trend--down]="!trendUp()">
          <mat-icon>{{ trendUp() ? 'trending_up' : 'trending_down' }}</mat-icon>
          <span>{{ trendPercent() }}</span>
        </div>
      }
    </div>
  `,
  styles: [`
    .kpi-card {
      background: var(--sc-surface-card);
      border: 1px solid var(--sc-surface-border);
      border-radius: var(--sc-radius);
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
      box-shadow: var(--sc-shadow-sm);
      transition: box-shadow 0.15s ease, transform 0.1s ease;

      &:hover {
        box-shadow: var(--sc-shadow-md);
        transform: translateY(-1px);
      }
    }

    .kpi-label {
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--sc-text-muted);
      text-transform: uppercase;
      letter-spacing: 0.06em;
      margin: 0;
    }

    .kpi-value {
      font-size: 1.75rem;
      font-weight: 700;
      color: var(--sc-text-color);
      margin: 0.25rem 0 0;
      font-variant-numeric: tabular-nums;
      line-height: 1.2;
    }

    .kpi-trend {
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
      font-size: 0.75rem;
      font-weight: 600;
      margin-top: 0.5rem;

      mat-icon {
        font-size: 1rem;
        width: 1rem;
        height: 1rem;
      }
    }

    .kpi-trend--up {
      color: #2e7d32;
    }

    .kpi-trend--down {
      color: #c62828;
    }

    @media (max-width: 768px) {
      .kpi-value {
        font-size: 1.375rem;
      }
    }
  `],
})
export class KpiCardComponent {
  readonly title = input.required<string>();
  readonly value = input.required<number>();
  readonly previousValue = input<number | null>(null);
  readonly format = input<KpiFormat>('number');

  readonly formattedValue = computed(() => {
    const v = this.value();
    switch (this.format()) {
      case 'currency':
        return new Intl.NumberFormat('es-CO', {
          style: 'currency',
          currency: 'COP',
          maximumFractionDigits: 0,
        }).format(v);
      case 'percent':
        return `${v.toFixed(1)}%`;
      case 'number':
      default:
        return new Intl.NumberFormat('es-CO').format(v);
    }
  });

  readonly trendUp = computed(() => {
    const prev = this.previousValue();
    if (prev === null || prev === undefined || prev === 0) return true;
    return this.value() >= prev;
  });

  readonly trendPercent = computed(() => {
    const prev = this.previousValue();
    if (prev === null || prev === undefined || prev === 0) return '';
    const change = ((this.value() - prev) / Math.abs(prev)) * 100;
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(1)}%`;
  });
}
