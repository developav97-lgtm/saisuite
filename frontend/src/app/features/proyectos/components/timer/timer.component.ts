import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnDestroy,
  inject,
  input,
  output,
  signal,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { TimesheetService } from '../../services/timesheet.service';
import { SesionTrabajo } from '../../models/timesheet.model';
import type { Tarea } from '../../models/tarea.model';
import { ToastService } from '../../../../core/services/toast.service';

@Component({
  selector:    'app-timer',
  templateUrl: './timer.component.html',
  styleUrl:    './timer.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatButtonModule, MatIconModule, MatTooltipModule],
})
export class TimerComponent implements OnDestroy {
  readonly tarea      = input.required<Tarea>();
  /** Emits la SesionTrabajo finalizada para que el padre recargue horas */
  readonly sesionFin  = output<SesionTrabajo>();

  private readonly timesheetService = inject(TimesheetService);
  private readonly toast       = inject(ToastService);
  private readonly cdr              = inject(ChangeDetectorRef);

  readonly loading          = signal(false);
  readonly sesionActiva     = signal<SesionTrabajo | null>(null);
  readonly tiempoTranscurrido = signal(0);   // segundos acumulados

  private intervalId: ReturnType<typeof setInterval> | null = null;

  // ── Controles del timer ───────────────────────────────────────────────────

  start(): void {
    this.loading.set(true);
    this.timesheetService.iniciarSesion(this.tarea().id).subscribe({
      next: (sesion) => {
        this.sesionActiva.set(sesion);
        this.tiempoTranscurrido.set(0);
        this.iniciarIntervalo();
        this.loading.set(false);
        this.cdr.markForCheck();
      },
      error: (err: { error?: { detail?: string; sesion_activa?: SesionTrabajo } }) => {
        const detail = err?.error?.detail ?? 'No se pudo iniciar el timer.';
        // Si hay sesión activa en otra tarea, ofrecer restaurarla
        const activa = err?.error?.sesion_activa;
        if (activa) {
          this.sesionActiva.set(activa);
          this.tiempoTranscurrido.set(activa.duracion_segundos);
          this.iniciarIntervalo();
        }
        this.toast.error(detail);
        this.loading.set(false);
        this.cdr.markForCheck();
      },
    });
  }

  pause(): void {
    const sesion = this.sesionActiva();
    if (!sesion) return;
    this.loading.set(true);
    this.timesheetService.pausarSesion(this.tarea().id, sesion.id).subscribe({
      next: (updated) => {
        this.sesionActiva.set(updated);
        this.detenerIntervalo();
        this.loading.set(false);
        this.cdr.markForCheck();
      },
      error: () => {
        this.toast.error('No se pudo pausar el timer.');
        this.loading.set(false);
      },
    });
  }

  resume(): void {
    const sesion = this.sesionActiva();
    if (!sesion) return;
    this.loading.set(true);
    this.timesheetService.reanudarSesion(this.tarea().id, sesion.id).subscribe({
      next: (updated) => {
        this.sesionActiva.set(updated);
        this.iniciarIntervalo();
        this.loading.set(false);
        this.cdr.markForCheck();
      },
      error: () => {
        this.toast.error('No se pudo reanudar el timer.');
        this.loading.set(false);
      },
    });
  }

  stop(): void {
    const sesion = this.sesionActiva();
    if (!sesion) return;
    this.loading.set(true);
    this.timesheetService.detenerSesion(this.tarea().id, sesion.id).subscribe({
      next: (finalizada) => {
        this.sesionActiva.set(null);
        this.tiempoTranscurrido.set(0);
        this.detenerIntervalo();
        this.sesionFin.emit(finalizada);
        const horas = (finalizada.duracion_segundos / 3600).toFixed(2);
        this.toast.success(`${horas}h registradas en "${this.tarea().nombre}"`);
        this.loading.set(false);
        this.cdr.markForCheck();
      },
      error: () => {
        this.toast.error('No se pudo detener el timer.');
        this.loading.set(false);
      },
    });
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  get tiempoFormateado(): string {
    const total = this.tiempoTranscurrido();
    const hh    = Math.floor(total / 3600);
    const mm    = Math.floor((total % 3600) / 60);
    const ss    = total % 60;
    return [hh, mm, ss].map(n => String(n).padStart(2, '0')).join(':');
  }

  get corriendo(): boolean {
    return this.sesionActiva()?.estado === 'active';
  }

  get pausado(): boolean {
    return this.sesionActiva()?.estado === 'paused';
  }

  private iniciarIntervalo(): void {
    this.detenerIntervalo();
    this.intervalId = setInterval(() => {
      this.tiempoTranscurrido.update(s => s + 1);
      this.cdr.markForCheck();
    }, 1000);
  }

  private detenerIntervalo(): void {
    if (this.intervalId !== null) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  ngOnDestroy(): void {
    this.detenerIntervalo();
  }
}
