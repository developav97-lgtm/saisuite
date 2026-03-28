/**
 * SaiSuite — WorkloadSummaryComponent (Feature #4 / Epic 8)
 * Muestra el resumen de carga de trabajo de un usuario con código de colores semáforo:
 *   - Verde  (<80% utilización)
 *   - Amarillo (80–100%)
 *   - Rojo   (>100% — sobrecargado)
 */
import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  input,
  signal,
  computed,
} from '@angular/core';
import { DatePipe, DecimalPipe } from '@angular/common';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { ResourceService } from '../../services/resource.service';
import { UserWorkload } from '../../models/resource.model';

@Component({
  selector: 'app-workload-summary',
  templateUrl: './workload-summary.component.html',
  styleUrl: './workload-summary.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DatePipe,
    DecimalPipe,
    MatProgressBarModule,
    MatIconModule,
    MatTooltipModule,
  ],
})
export class WorkloadSummaryComponent implements OnInit {
  /** ID del usuario cuya carga se mostrará. */
  readonly usuarioId  = input.required<string>();
  /** Período de análisis — defecto: hoy → +30 días */
  readonly startDate  = input<string>(WorkloadSummaryComponent.todayStr());
  readonly endDate    = input<string>(WorkloadSummaryComponent.plusDaysStr(30));

  private readonly resourceService = inject(ResourceService);

  readonly loading  = signal(false);
  readonly workload = signal<UserWorkload | null>(null);
  readonly error    = signal(false);

  /**
   * Porcentaje de utilización como número (0–N).
   * Si supera 100 devuelve 100 para la barra visual, pero el valor real
   * se muestra en la etiqueta.
   */
  readonly utilizacionNum = computed(() => {
    const w = this.workload();
    return w ? parseFloat(w.porcentaje_utilizacion) : 0;
  });

  /** Clase semáforo basada en % utilización */
  readonly semaforo = computed((): 'verde' | 'amarillo' | 'rojo' => {
    const pct = this.utilizacionNum();
    if (pct > 100) return 'rojo';
    if (pct >= 80)  return 'amarillo';
    return 'verde';
  });

  /** Ancho de la barra visual (máx. 100) */
  readonly barraWidth = computed(() => Math.min(100, this.utilizacionNum()));

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.loading.set(true);
    this.error.set(false);
    this.resourceService.getWorkload(
      this.usuarioId(),
      this.startDate(),
      this.endDate(),
    ).subscribe({
      next: (data) => {
        this.workload.set(data);
        this.loading.set(false);
      },
      error: () => {
        this.error.set(true);
        this.loading.set(false);
      },
    });
  }

  // ── Helpers estáticos ──────────────────────────────────────────────────────

  private static todayStr(): string {
    return WorkloadSummaryComponent.formatDate(new Date());
  }

  private static plusDaysStr(days: number): string {
    return WorkloadSummaryComponent.formatDate(new Date(Date.now() + days * 24 * 60 * 60 * 1000));
  }

  private static formatDate(d: Date): string {
    const y   = d.getFullYear();
    const m   = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }
}
