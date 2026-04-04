/**
 * SaiSuite — FloatIndicatorComponent (SK-40)
 * Badge/chip reutilizable que muestra la holgura (float) de una tarea.
 * Selector: sc-float-indicator
 */
import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';

@Component({
  selector: 'sc-float-indicator',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatChipsModule, MatTooltipModule],
  template: `
    @if (isCritical()) {
      <mat-chip-set>
        <mat-chip
          class="fi-chip fi-chip--critical"
          [disableRipple]="true"
          matTooltip="Tarea en el camino crítico — sin holgura disponible"
          matTooltipPosition="above"
        >CRÍTICA</mat-chip>
      </mat-chip-set>
    } @else if (floatDays() !== null && floatDays()! > 0) {
      <mat-chip-set>
        <mat-chip
          class="fi-chip fi-chip--float"
          [disableRipple]="true"
          matTooltip="Holgura disponible (días)"
          matTooltipPosition="above"
        >
          Holgura: {{ floatDays() }} {{ floatDays() === 1 ? 'día' : 'días' }}
        </mat-chip>
      </mat-chip-set>
    }
  `,
  styles: [`
    :host { display: block; max-width: 100%; overflow: hidden; }

    .fi-chip {
      font-size: 0.6875rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      min-height: 22px;
      height: 22px;
      padding: 0 8px;
      cursor: default;
    }

    .fi-chip--critical {
      background-color: var(--sc-danger-light, #fdecea) !important;
      color: var(--sc-danger, #c62828) !important;
      border: 1px solid var(--sc-danger, #c62828) !important;
    }

    .fi-chip--float {
      background-color: var(--sc-primary-light) !important;
      color: var(--sc-primary) !important;
      border: 1px solid var(--sc-primary) !important;
    }
  `],
})
export class FloatIndicatorComponent {
  readonly floatDays = input<number | null>(null);
  readonly isCritical = input<boolean>(false);
}
