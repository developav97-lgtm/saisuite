/**
 * SaiSuite — TareaCardComponent
 * Tarjeta reutilizable para mostrar una tarea en el Kanban y otros contextos.
 */
import { ChangeDetectionStrategy, Component, input, output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { Tarea } from '../../models/tarea.model';

const PRIORIDAD_ICONS: Record<string, string> = {
  4: 'priority_high',
  3: 'arrow_upward',
  2: 'remove',
  1: 'arrow_downward',
};

const PRIORIDAD_LABELS: Record<string, string> = {
  4: 'Urgente',
  3: 'Alta',
  2: 'Normal',
  1: 'Baja',
};

@Component({
  selector: 'app-tarea-card',
  templateUrl: './tarea-card.component.html',
  styleUrl: './tarea-card.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatTooltipModule,
    MatProgressBarModule,
  ],
})
export class TareaCardComponent {
  readonly tarea             = input.required<Tarea>();
  readonly showActions       = input(true);
  readonly compact           = input(false);
  /** Habilitar edición inline de progreso (solo en Kanban). */
  readonly enableProgressEdit = input(false);

  readonly edit           = output<Tarea>();
  readonly eliminar       = output<Tarea>();
  readonly viewDetail     = output<Tarea>();
  readonly progressUpdate = output<{ tarea: Tarea; progreso: number }>();
  readonly timeRegister   = output<Tarea>();

  readonly PRIORIDAD_ICONS  = PRIORIDAD_ICONS;
  readonly PRIORIDAD_LABELS = PRIORIDAD_LABELS;

  readonly editandoProgreso = signal(false);
  readonly progresoTemporal = signal(0);

  get progreso(): number {
    return this.tarea().progreso_porcentaje ?? 0;
  }

  get unidadMedida(): string {
    const um = this.tarea().actividad_proyecto_detail?.actividad_unidad_medida?.toLowerCase().trim();
    if (!um || um === 'hora' || um === 'horas') return 'h';
    return um;
  }

  get esModoHoras(): boolean {
    const um = this.tarea().actividad_proyecto_detail?.actividad_unidad_medida?.toLowerCase().trim();
    return !um || um === 'hora' || um === 'horas';
  }

  get progresoColor(): 'primary' | 'accent' | 'warn' {
    if (this.progreso >= 100) return 'accent';
    if (this.progreso >= 50)  return 'primary';
    return 'warn';
  }

  prioridadIconClass(): string {
    return `tc-prio-icon tc-prio--${this.tarea().prioridad}`;
  }

  onEdit(event: Event): void {
    event.stopPropagation();
    this.edit.emit(this.tarea());
  }

  onTimeRegister(event: Event): void {
    event.stopPropagation();
    this.timeRegister.emit(this.tarea());
  }

  onEliminar(event: Event): void {
    event.stopPropagation();
    this.eliminar.emit(this.tarea());
  }

  onViewDetail(): void {
    this.viewDetail.emit(this.tarea());
  }

  onProgresoClick(event: Event): void {
    if (!this.enableProgressEdit()) return;
    event.stopPropagation();
    this.progresoTemporal.set(this.tarea().porcentaje_completado);
    this.editandoProgreso.set(true);
  }

  onProgresoChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.progresoTemporal.set(Number(input.value));
  }

  onProgresoBlur(): void {
    if (this.progresoTemporal() !== this.tarea().porcentaje_completado) {
      this.progressUpdate.emit({ tarea: this.tarea(), progreso: this.progresoTemporal() });
    }
    this.editandoProgreso.set(false);
  }

  onProgresoKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter') {
      (event.target as HTMLElement).blur();
    } else if (event.key === 'Escape') {
      this.progresoTemporal.set(this.tarea().porcentaje_completado);
      this.editandoProgreso.set(false);
    }
  }
}
