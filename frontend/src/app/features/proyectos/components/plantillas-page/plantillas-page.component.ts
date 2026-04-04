/**
 * SaiSuite — PlantillasPageComponent
 * Página de gestión de plantillas de proyecto de la empresa.
 */
import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDialog } from '@angular/material/dialog';

import { ProyectoService } from '../../services/proyecto.service';
import { ToastService } from '../../../../core/services/toast.service';
import { NavigationHistoryService } from '../../../../core/services/navigation-history.service';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import {
  PlantillaFormDialogComponent,
  PlantillaFormDialogData,
} from '../plantilla-form-dialog/plantilla-form-dialog.component';
import {
  PlantillaProyecto,
  PLANTILLA_CATEGORIA_LABELS,
} from '../../models/proyecto.model';

@Component({
  selector: 'app-plantillas-page',
  templateUrl: './plantillas-page.component.html',
  styleUrl: './plantillas-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    MatButtonModule,
    MatIconModule,
    MatCardModule,
    MatProgressBarModule,
    MatTooltipModule,
  ],
})
export class PlantillasPageComponent implements OnInit {
  private readonly proyectoSvc = inject(ProyectoService);
  private readonly router      = inject(Router);
  private readonly dialog      = inject(MatDialog);
  private readonly toast       = inject(ToastService);
  private readonly navHistory  = inject(NavigationHistoryService);

  readonly plantillas = signal<PlantillaProyecto[]>([]);
  readonly loading    = signal(false);

  ngOnInit(): void {
    this.loadPlantillas();
  }

  private loadPlantillas(): void {
    this.loading.set(true);
    this.proyectoSvc.getTemplates().subscribe({
      next: (data) => {
        this.plantillas.set(data);
        this.loading.set(false);
      },
      error: () => {
        this.toast.error('No se pudieron cargar las plantillas.');
        this.loading.set(false);
      },
    });
  }

  categoriaLabel(categoria: string): string {
    return PLANTILLA_CATEGORIA_LABELS[categoria as keyof typeof PLANTILLA_CATEGORIA_LABELS] ?? categoria;
  }

  fasesCount(plantilla: PlantillaProyecto): number {
    return plantilla.fases_count ?? plantilla.fases?.length ?? 0;
  }

  tareasCount(plantilla: PlantillaProyecto): number {
    return plantilla.fases?.reduce((acc, f) => acc + (f.tareas?.length ?? 0), 0) ?? 0;
  }

  abrirNueva(): void {
    const data: PlantillaFormDialogData = {};
    this.dialog.open(PlantillaFormDialogComponent, {
      data,
      width: '1100px',
      maxWidth: '95vw',
      maxHeight: '90vh',
      disableClose: false,
    }).afterClosed().subscribe((result: PlantillaProyecto | null) => {
      if (result) {
        this.loadPlantillas();
      }
    });
  }

  abrirEditar(plantilla: PlantillaProyecto): void {
    // Load full detail first to get fases+tareas
    this.loading.set(true);
    this.proyectoSvc.getTemplateDetail(plantilla.id).subscribe({
      next: (detalle) => {
        this.loading.set(false);
        const data: PlantillaFormDialogData = { plantilla: detalle };
        this.dialog.open(PlantillaFormDialogComponent, {
          data,
          width: '1100px',
          maxWidth: '95vw',
          maxHeight: '90vh',
          disableClose: false,
        }).afterClosed().subscribe((result: PlantillaProyecto | null) => {
          if (result) {
            this.loadPlantillas();
          }
        });
      },
      error: () => {
        this.loading.set(false);
        this.toast.error('No se pudo cargar el detalle de la plantilla.');
      },
    });
  }

  confirmarEliminar(plantilla: PlantillaProyecto): void {
    this.dialog.open(ConfirmDialogComponent, {
      data: {
        header:       'Eliminar plantilla',
        message:      `¿Eliminar la plantilla "${plantilla.nombre}"? Esta acción no se puede deshacer.`,
        acceptLabel:  'Eliminar',
        acceptColor:  'warn',
      },
    }).afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) {
        this.eliminar(plantilla.id);
      }
    });
  }

  private eliminar(id: string): void {
    this.proyectoSvc.deleteTemplate(id).subscribe({
      next: () => {
        this.toast.success('Plantilla eliminada correctamente.');
        this.loadPlantillas();
      },
      error: () => {
        this.toast.error('No se pudo eliminar la plantilla.');
      },
    });
  }

  volverAProyectos(): void {
    this.navHistory.goBack(['/proyectos', 'lista']);
  }
}
