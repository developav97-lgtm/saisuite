import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';
import { DatePipe } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { TrialStatus } from '../../models/trial.model';

@Component({
  selector: 'app-trial-banner',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [DatePipe, MatButtonModule, MatIconModule],
  template: `
    @if (trialStatus(); as status) {
      @if (status.tipo_acceso === 'trial') {
        <div class="tb-banner" [class.tb-banner--warning]="status.dias_restantes <= 5">
          <mat-icon>hourglass_top</mat-icon>
          <span class="tb-text">
            Prueba activa: <strong>{{ status.dias_restantes }} días restantes</strong>
            @if (status.expira_en) {
              <span class="tb-expires">(expira {{ status.expira_en | date:'dd/MM/yyyy' }})</span>
            }
          </span>
          <button mat-stroked-button class="tb-action" (click)="contactSales.emit()">
            <mat-icon>shopping_cart</mat-icon>
            Adquirir licencia
          </button>
        </div>
      } @else if (status.tipo_acceso === 'none') {
        <div class="tb-banner tb-banner--inactive">
          <mat-icon>lock</mat-icon>
          <span class="tb-text">
            Módulo no disponible — activa una prueba gratuita de 14 días
          </span>
          <button mat-raised-button color="primary" (click)="activateTrial.emit()">
            <mat-icon>play_arrow</mat-icon>
            Activar prueba
          </button>
        </div>
      }
    }
  `,
  styles: [`
    .tb-banner {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.75rem 1rem;
      border-radius: var(--sc-radius);
      background: var(--sc-primary-light);
      border: 1px solid var(--sc-primary);
      margin-bottom: 1rem;
      flex-wrap: wrap;

      > mat-icon {
        color: var(--sc-primary);
        flex-shrink: 0;
      }
    }

    .tb-banner--warning {
      background: rgba(255, 152, 0, 0.1);
      border-color: #ff9800;

      > mat-icon { color: #ff9800; }
    }

    .tb-banner--inactive {
      background: var(--sc-surface-ground);
      border-color: var(--sc-surface-border);

      > mat-icon { color: var(--sc-text-muted); }
    }

    .tb-text {
      flex: 1;
      font-size: 0.875rem;
      color: var(--sc-text-color);
      min-width: 200px;
    }

    .tb-expires {
      color: var(--sc-text-muted);
      font-size: 0.8125rem;
    }

    .tb-action {
      flex-shrink: 0;
    }

    @media (max-width: 768px) {
      .tb-banner {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.5rem;
      }
      .tb-action { align-self: flex-end; }
    }
  `],
})
export class TrialBannerComponent {
  readonly trialStatus = input.required<TrialStatus | null>();
  readonly activateTrial = output<void>();
  readonly contactSales = output<void>();
}
