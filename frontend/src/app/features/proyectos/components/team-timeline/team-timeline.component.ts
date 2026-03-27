/**
 * SaiSuite — TeamTimelineComponent (Feature #4)
 * Muestra la disponibilidad y asignaciones del equipo en un proyecto.
 * Tab "Equipo" dentro de ProyectoDetail.
 */
import {
  ChangeDetectionStrategy, Component, OnInit, input, inject, signal, computed,
} from '@angular/core';
import { DatePipe } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { FormsModule } from '@angular/forms';
import { ResourceService } from '../../services/resource.service';
import { TeamAvailabilityUser } from '../../models/resource.model';

@Component({
  selector: 'app-team-timeline',
  templateUrl: './team-timeline.component.html',
  styleUrl: './team-timeline.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DatePipe,
    FormsModule,
    MatButtonModule,
    MatIconModule,
    MatTooltipModule,
    MatProgressBarModule,
    MatFormFieldModule,
    MatInputModule,
    MatDatepickerModule,
    MatNativeDateModule,
  ],
})
export class TeamTimelineComponent implements OnInit {
  readonly proyectoId = input.required<string>();

  private readonly resourceService = inject(ResourceService);
  private readonly snackBar        = inject(MatSnackBar);

  readonly loading = signal(false);
  readonly team    = signal<TeamAvailabilityUser[]>([]);

  // Rango de fechas por defecto: hoy → +30 días
  fechaInicio: Date = new Date();
  fechaFin: Date    = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000);

  readonly totalMiembros = computed(() => this.team().length);

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.loading.set(true);
    this.resourceService.getTeamTimeline(
      this.proyectoId(),
      this.formatDate(this.fechaInicio),
      this.formatDate(this.fechaFin),
    ).subscribe({
      next: (data) => {
        this.team.set(data);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.snackBar.open('Error al cargar disponibilidad del equipo', 'Cerrar', {
          duration: 3000, panelClass: ['snack-error'],
        });
      },
    });
  }

  tareasDe(usuario: TeamAvailabilityUser): string {
    if (!usuario.asignaciones.length) return 'Sin tareas en el período';
    return usuario.asignaciones
      .map(a => `${a.tarea_nombre} (${a.porcentaje_asignacion}%)`)
      .join(', ');
  }

  ausenciasDe(usuario: TeamAvailabilityUser): string {
    if (!usuario.ausencias.length) return '';
    return usuario.ausencias
      .map(a => `${a.tipo_display}: ${a.fecha_inicio} → ${a.fecha_fin}`)
      .join('; ');
  }

  totalPorcentaje(usuario: TeamAvailabilityUser): number {
    return usuario.asignaciones.reduce(
      (sum, a) => sum + Number(a.porcentaje_asignacion), 0,
    );
  }

  private formatDate(d: Date): string {
    const y   = d.getFullYear();
    const m   = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }
}
