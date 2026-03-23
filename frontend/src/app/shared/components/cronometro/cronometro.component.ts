/**
 * SaiSuite — CronometroComponent
 * Cronómetro reutilizable para registrar tiempo en tareas.
 * Soporta inicio, pausa, reanudación y detención con notas opcionales.
 * Se restaura automáticamente si hay una sesión activa al cargar.
 */
import {
  ChangeDetectionStrategy, ChangeDetectorRef,
  Component, OnInit, OnDestroy, inject, input, output, signal, computed,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar } from '@angular/material/snack-bar';
import { SesionTrabajoService } from '../../../features/proyectos/services/sesion-trabajo.service';
import { SesionTrabajo, Pausa } from '../../../features/proyectos/models/sesion-trabajo.model';

@Component({
  selector: 'app-cronometro',
  templateUrl: './cronometro.component.html',
  styleUrl: './cronometro.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    MatButtonModule, MatIconModule,
    MatFormFieldModule, MatInputModule,
    MatProgressSpinnerModule,
  ],
})
export class CronometroComponent implements OnInit, OnDestroy {
  // ── Inputs / Outputs ────────────────────────────────────────
  readonly tareaId         = input.required<string>();
  readonly sesionFinalizada = output<SesionTrabajo>();

  // ── Servicios ───────────────────────────────────────────────
  private readonly sesionService = inject(SesionTrabajoService);
  private readonly snackBar      = inject(MatSnackBar);
  private readonly cdr           = inject(ChangeDetectorRef);

  // ── Estado ──────────────────────────────────────────────────
  readonly sesion            = signal<SesionTrabajo | null>(null);
  readonly tiempoTranscurrido = signal(0); // segundos
  readonly loading           = signal(false);

  /** Campo de notas como propiedad plana para [(ngModel)] */
  notas = '';

  // ── Computed ────────────────────────────────────────────────
  readonly estado     = computed(() => this.sesion()?.estado ?? 'inactiva');
  readonly estaActiva  = computed(() => this.estado() === 'activa');
  readonly estaPausada = computed(() => this.estado() === 'pausada');
  readonly estaInactiva = computed(() => this.estado() === 'inactiva');

  private intervalId: ReturnType<typeof setInterval> | null = null;

  // ── Ciclo de vida ───────────────────────────────────────────

  ngOnInit(): void {
    this.verificarSesionActiva();
  }

  ngOnDestroy(): void {
    this.pararInterval();
  }

  // ── Acciones públicas ───────────────────────────────────────

  iniciar(): void {
    this.loading.set(true);
    this.sesionService.iniciar(this.tareaId()).subscribe({
      next: (sesion) => {
        this.sesion.set(sesion);
        this.tiempoTranscurrido.set(0);
        this.iniciarInterval();
        this.loading.set(false);
        this.snackBar.open('Cronómetro iniciado.', 'Cerrar', { duration: 2000 });
        this.cdr.markForCheck();
      },
      error: (err: { error?: { detail?: string; sesion_activa?: SesionTrabajo } }) => {
        this.loading.set(false);
        const detail = err.error?.detail ?? 'Error al iniciar el cronómetro.';
        // Si ya hay sesión activa en ESTA tarea, restaurarla
        const sesionActiva = err.error?.sesion_activa;
        if (sesionActiva && sesionActiva.tarea === this.tareaId()) {
          this.restaurarSesion(sesionActiva);
        } else {
          this.snackBar.open(detail, 'Cerrar', { duration: 4000, panelClass: ['snack-error'] });
        }
        this.cdr.markForCheck();
      },
    });
  }

  pausar(): void {
    const sesion = this.sesion();
    if (!sesion) return;
    this.loading.set(true);
    this.sesionService.pausar(this.tareaId(), sesion.id).subscribe({
      next: (updated) => {
        this.sesion.set(updated);
        this.pararInterval();
        this.loading.set(false);
        this.snackBar.open('Cronómetro pausado.', 'Cerrar', { duration: 2000 });
        this.cdr.markForCheck();
      },
      error: () => {
        this.loading.set(false);
        this.snackBar.open('Error al pausar el cronómetro.', 'Cerrar', {
          duration: 3000, panelClass: ['snack-error'],
        });
        this.cdr.markForCheck();
      },
    });
  }

  reanudar(): void {
    const sesion = this.sesion();
    if (!sesion) return;
    this.loading.set(true);
    this.sesionService.reanudar(this.tareaId(), sesion.id).subscribe({
      next: (updated) => {
        this.sesion.set(updated);
        this.iniciarInterval();
        this.loading.set(false);
        this.snackBar.open('Cronómetro reanudado.', 'Cerrar', { duration: 2000 });
        this.cdr.markForCheck();
      },
      error: () => {
        this.loading.set(false);
        this.snackBar.open('Error al reanudar el cronómetro.', 'Cerrar', {
          duration: 3000, panelClass: ['snack-error'],
        });
        this.cdr.markForCheck();
      },
    });
  }

  detener(): void {
    const sesion = this.sesion();
    if (!sesion) return;
    this.loading.set(true);
    this.sesionService.detener(this.tareaId(), sesion.id, this.notas).subscribe({
      next: (finalizada) => {
        this.pararInterval();
        this.sesion.set(null);
        this.tiempoTranscurrido.set(0);
        this.notas = '';
        this.loading.set(false);
        this.snackBar.open(
          `Sesión finalizada: ${parseFloat(finalizada.duracion_horas).toFixed(2)}h registradas.`,
          'Cerrar',
          { duration: 3000, panelClass: ['snack-success'] },
        );
        this.sesionFinalizada.emit(finalizada);
        this.cdr.markForCheck();
      },
      error: () => {
        this.loading.set(false);
        this.snackBar.open('Error al detener el cronómetro.', 'Cerrar', {
          duration: 3000, panelClass: ['snack-error'],
        });
        this.cdr.markForCheck();
      },
    });
  }

  formatearTiempo(): string {
    const seg = this.tiempoTranscurrido();
    const h   = Math.floor(seg / 3600);
    const m   = Math.floor((seg % 3600) / 60);
    const s   = seg % 60;
    return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }

  // ── Privados ────────────────────────────────────────────────

  private verificarSesionActiva(): void {
    this.sesionService.obtenerSesionActiva().subscribe({
      next: (sesion) => {
        if (sesion.tarea === this.tareaId()) {
          this.restaurarSesion(sesion);
        }
      },
      error: () => { /* sin sesión activa, estado normal */ },
    });
  }

  private restaurarSesion(sesion: SesionTrabajo): void {
    this.sesion.set(sesion);
    this.tiempoTranscurrido.set(this.calcularSegundosTranscurridos(sesion));
    if (sesion.estado === 'activa') {
      this.iniciarInterval();
    }
    this.cdr.markForCheck();
  }

  private iniciarInterval(): void {
    this.pararInterval();
    this.intervalId = setInterval(() => {
      this.tiempoTranscurrido.update(t => t + 1);
      this.cdr.markForCheck();
    }, 1000);
  }

  private pararInterval(): void {
    if (this.intervalId !== null) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  private calcularSegundosTranscurridos(sesion: SesionTrabajo): number {
    const ahora   = Date.now();
    const inicio  = new Date(sesion.inicio).getTime();
    let total     = (ahora - inicio) / 1000;

    for (const pausa of (sesion.pausas as Pausa[])) {
      const inicioPausa = new Date(pausa.inicio).getTime();
      if (pausa.fin) {
        total -= (new Date(pausa.fin).getTime() - inicioPausa) / 1000;
      } else {
        // Pausa aún activa: restar desde su inicio hasta ahora
        total -= (ahora - inicioPausa) / 1000;
      }
    }

    return Math.max(0, Math.floor(total));
  }
}
