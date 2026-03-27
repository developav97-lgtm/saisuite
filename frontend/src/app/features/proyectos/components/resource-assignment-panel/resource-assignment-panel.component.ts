/**
 * SaiSuite — ResourceAssignmentPanelComponent
 * Tab "Recursos" dentro de TareaDetail.
 * Lista asignaciones de recurso de una tarea y permite agregar / quitar.
 */
import {
  ChangeDetectionStrategy, Component, OnInit, input, inject, signal,
} from '@angular/core';
import { DatePipe, DecimalPipe } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ResourceService } from '../../services/resource.service';
import { ResourceAssignmentList } from '../../models/resource.model';
import { ResourceAssignmentFormComponent } from '../resource-assignment-form/resource-assignment-form.component';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';

@Component({
  selector: 'app-resource-assignment-panel',
  templateUrl: './resource-assignment-panel.component.html',
  styleUrl: './resource-assignment-panel.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DatePipe,
    DecimalPipe,
    MatButtonModule,
    MatIconModule,
    MatTooltipModule,
    MatProgressBarModule,
  ],
})
export class ResourceAssignmentPanelComponent implements OnInit {
  readonly tareaId     = input.required<string>();
  readonly tareaEstado = input<string>('todo');

  private readonly resourceService = inject(ResourceService);
  private readonly dialog          = inject(MatDialog);
  private readonly snackBar        = inject(MatSnackBar);

  readonly loading     = signal(false);
  readonly assignments = signal<ResourceAssignmentList[]>([]);

  ngOnInit(): void {
    this.loadAssignments();
  }

  loadAssignments(): void {
    this.loading.set(true);
    this.resourceService.listAssignments(this.tareaId()).subscribe({
      next: data => {
        this.assignments.set(data);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.snackBar.open('Error al cargar asignaciones', 'Cerrar', { duration: 3000, panelClass: ['snack-error'] });
      },
    });
  }

  agregarAsignacion(): void {
    const ref = this.dialog.open(ResourceAssignmentFormComponent, {
      width: '480px',
      data: { tareaId: this.tareaId() },
    });
    ref.afterClosed().subscribe(result => {
      if (result) this.loadAssignments();
    });
  }

  eliminarAsignacion(asignacion: ResourceAssignmentList): void {
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        title:   'Desasignar recurso',
        message: `¿Desasignar a ${asignacion.usuario_nombre} de esta tarea?`,
        confirm: 'Desasignar',
        danger:  true,
      },
    });
    ref.afterClosed().subscribe(confirmed => {
      if (!confirmed) return;
      this.resourceService.deleteAssignment(this.tareaId(), asignacion.id).subscribe({
        next: () => {
          this.snackBar.open('Recurso desasignado', 'Cerrar', { duration: 3000, panelClass: ['snack-success'] });
          this.loadAssignments();
        },
        error: () => {
          this.snackBar.open('Error al desasignar', 'Cerrar', { duration: 3000, panelClass: ['snack-error'] });
        },
      });
    });
  }

  readonly tareaActiva = (): boolean =>
    ['todo', 'in_progress', 'in_review', 'blocked'].includes(this.tareaEstado());
}
