import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material/table';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSnackBar } from '@angular/material/snack-bar';
import { DecimalPipe, DatePipe } from '@angular/common';
import { TimesheetService } from '../../services/timesheet.service';
import { TimesheetEntry, TimesheetSemanalRow } from '../../models/timesheet.model';

@Component({
  selector:    'app-timesheet-semanal',
  templateUrl: './timesheet-semanal.component.html',
  styleUrl:    './timesheet-semanal.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    MatButtonModule,
    MatIconModule,
    MatTableModule,
    MatChipsModule,
    MatTooltipModule,
    MatProgressBarModule,
    DecimalPipe,
    DatePipe,
  ],
})
export class TimesheetSemanalComponent implements OnInit {
  private readonly timesheetService = inject(TimesheetService);
  private readonly snackBar         = inject(MatSnackBar);

  readonly loading = signal(false);
  readonly entries = signal<TimesheetEntry[]>([]);

  // ── Semana actual ──────────────────────────────────────────────────────────
  private inicioSemana = signal<Date>(this.getLunes(new Date()));

  readonly diasSemana = computed(() => {
    const lunes = this.inicioSemana();
    return Array.from({ length: 7 }, (_, i) => {
      const d = new Date(lunes);
      d.setDate(d.getDate() + i);
      return {
        fecha:       this.toIso(d),
        labelCorto:  this.DIAS_CORTOS[i],
        labelLargo:  this.DIAS_LARGOS[i],
        esHoy:       this.toIso(d) === this.toIso(new Date()),
        esFinDeSemana: i >= 5,
      };
    });
  });

  readonly rangoSemana = computed(() => {
    const dias = this.diasSemana();
    return `${this.formatLabel(dias[0].fecha)} — ${this.formatLabel(dias[6].fecha)}`;
  });

  /** Entradas agrupadas por tarea para la tabla */
  readonly filas = computed<TimesheetSemanalRow[]>(() => {
    const map = new Map<string, TimesheetSemanalRow>();

    for (const e of this.entries()) {
      const tareaId = e.tarea_detail.id;
      if (!map.has(tareaId)) {
        map.set(tareaId, {
          tarea:        e.tarea_detail,
          horasPorDia:  {},
          totalSemana:  0,
        });
      }
      const fila = map.get(tareaId)!;
      const prev = fila.horasPorDia[e.fecha] ?? 0;
      fila.horasPorDia[e.fecha] = prev + Number(e.horas);
      fila.totalSemana           = (fila.totalSemana ?? 0) + Number(e.horas);
    }

    return Array.from(map.values());
  });

  readonly totalPorDia = computed<Record<string, number | undefined>>(() => {
    const totales: Record<string, number> = {};
    for (const e of this.entries()) {
      totales[e.fecha] = (totales[e.fecha] ?? 0) + Number(e.horas);
    }
    return totales;
  });

  readonly totalSemana = computed(() =>
    this.entries().reduce((sum, e) => sum + Number(e.horas), 0),
  );

  readonly columnas = computed(() => [
    'tarea',
    ...this.diasSemana().map(d => d.fecha),
    'total',
  ]);

  private readonly DIAS_CORTOS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];
  private readonly DIAS_LARGOS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];

  // ── Lifecycle ─────────────────────────────────────────────────────────────

  ngOnInit(): void {
    this.cargar();
  }

  // ── Navegación ─────────────────────────────────────────────────────────────

  semanaAnterior(): void {
    const d = new Date(this.inicioSemana());
    d.setDate(d.getDate() - 7);
    this.inicioSemana.set(d);
    this.cargar();
  }

  semanaSiguiente(): void {
    const d = new Date(this.inicioSemana());
    d.setDate(d.getDate() + 7);
    this.inicioSemana.set(d);
    this.cargar();
  }

  semanaActual(): void {
    this.inicioSemana.set(this.getLunes(new Date()));
    this.cargar();
  }

  // ── Carga ─────────────────────────────────────────────────────────────────

  cargar(): void {
    const dias = this.diasSemana();
    this.loading.set(true);
    this.timesheetService
      .misHoras(dias[0].fecha, dias[6].fecha)
      .subscribe({
        next: (data) => {
          this.entries.set(data);
          this.loading.set(false);
        },
        error: () => {
          this.snackBar.open('No se pudo cargar el timesheet.', 'Cerrar', {
            duration: 4000, panelClass: ['snack-error'],
          });
          this.loading.set(false);
        },
      });
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  getHorasDia(fila: TimesheetSemanalRow, fecha: string): number {
    return fila.horasPorDia[fecha] ?? 0;
  }

  getDiaLabel(fecha: string): { corto: string; esHoy: boolean; esFinDeSemana: boolean } {
    const dia = this.diasSemana().find(d => d.fecha === fecha);
    return {
      corto:        dia?.labelCorto ?? fecha,
      esHoy:        dia?.esHoy ?? false,
      esFinDeSemana: dia?.esFinDeSemana ?? false,
    };
  }

  private getLunes(d: Date): Date {
    const dia = d.getDay();  // 0=Dom, 1=Lun, ...
    const diff = (dia === 0) ? -6 : 1 - dia;
    const lunes = new Date(d);
    lunes.setDate(d.getDate() + diff);
    lunes.setHours(0, 0, 0, 0);
    return lunes;
  }

  private toIso(d: Date): string {
    return d.toISOString().slice(0, 10);
  }

  private formatLabel(isoDate: string): string {
    const [y, m, day] = isoDate.split('-').map(Number);
    return `${day}/${m}/${y}`;
  }
}
