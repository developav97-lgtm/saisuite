import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ProyectoService, ProyectoListParams } from '../../services/proyecto.service';
import { ProyectoList, EstadoProyecto, TipoProyecto, ESTADO_LABELS, TIPO_LABELS } from '../../models/proyecto.model';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';

interface SelectOption { label: string; value: string | null; }

@Component({
  selector: 'app-proyecto-list',
  templateUrl: './proyecto-list.component.html',
  styleUrl: './proyecto-list.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, FormsModule,
    MatTableModule, MatButtonModule, MatIconModule,
    MatInputModule, MatFormFieldModule, MatSelectModule,
    MatPaginatorModule, MatProgressBarModule, MatTooltipModule,
  ],
})
export class ProyectoListComponent implements OnInit {
  private readonly proyectoService = inject(ProyectoService);
  private readonly router          = inject(Router);
  private readonly dialog          = inject(MatDialog);
  private readonly snackBar        = inject(MatSnackBar);

  readonly proyectos    = signal<ProyectoList[]>([]);
  readonly totalCount   = signal(0);
  readonly loading      = signal(false);
  readonly searchText   = signal('');
  readonly estadoFilter = signal<EstadoProyecto | null>(null);
  readonly tipoFilter   = signal<TipoProyecto | null>(null);
  readonly pageSize     = 25;

  readonly displayedColumns = ['codigo', 'nombre', 'tipo', 'estado', 'cliente', 'gerente', 'fecha_fin', 'presupuesto', 'acciones'];

  readonly estadoOptions: SelectOption[] = [
    { label: 'Todos los estados', value: null },
    ...Object.entries(ESTADO_LABELS).map(([value, label]) => ({ label, value })),
  ];
  readonly tipoOptions: SelectOption[] = [
    { label: 'Todos los tipos', value: null },
    ...Object.entries(TIPO_LABELS).map(([value, label]) => ({ label, value })),
  ];

  readonly ESTADO_LABELS = ESTADO_LABELS;

  ngOnInit(): void {
    this.loadProyectos(0, this.pageSize);
  }

  loadProyectos(pageIndex: number, pageSize: number): void {
    this.loading.set(true);
    const params: ProyectoListParams = { page: pageIndex + 1, page_size: pageSize };
    if (this.searchText())   params.search = this.searchText();
    if (this.estadoFilter()) params.estado  = this.estadoFilter()!;
    if (this.tipoFilter())   params.tipo    = this.tipoFilter()!;

    this.proyectoService.list(params).subscribe({
      next: (res) => { this.proyectos.set(res.results); this.totalCount.set(res.count); this.loading.set(false); },
      error: () => {
        this.snackBar.open('No se pudieron cargar los proyectos.', 'Cerrar', { duration: 4000, panelClass: ['snack-error'] });
        this.loading.set(false);
      },
    });
  }

  onSearch(): void { this.loadProyectos(0, this.pageSize); }
  onFilterChange(): void { this.loadProyectos(0, this.pageSize); }
  onPage(event: PageEvent): void { this.loadProyectos(event.pageIndex, event.pageSize); }
  verDetalle(id: string): void { this.router.navigate(['/proyectos', id]); }
  nuevoProyecto(): void { this.router.navigate(['/proyectos', 'nuevo']); }

  confirmarEliminar(proyecto: ProyectoList): void {
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: { header: 'Confirmar eliminación', message: `¿Eliminar el proyecto "${proyecto.nombre}"? Esta acción no se puede deshacer.`, acceptLabel: 'Eliminar', acceptColor: 'warn' },
      width: '400px',
    });
    ref.afterClosed().subscribe(confirmed => { if (confirmed) this.eliminar(proyecto.id); });
  }

  private eliminar(id: string): void {
    this.proyectoService.delete(id).subscribe({
      next: () => {
        this.snackBar.open('Proyecto eliminado correctamente.', 'Cerrar', { duration: 3000, panelClass: ['snack-success'] });
        this.loadProyectos(0, this.pageSize);
      },
      error: () => this.snackBar.open('No se pudo eliminar el proyecto.', 'Cerrar', { duration: 4000, panelClass: ['snack-error'] }),
    });
  }

  formatCurrency(value: string): string {
    const num = parseFloat(value);
    return isNaN(num) ? value : num.toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 });
  }

  estadoLabel(estado: string): string {
    return ESTADO_LABELS[estado as EstadoProyecto] ?? estado;
  }

  estadoClass(estado: string): string {
    return `pl-estado-badge pl-estado-badge--${estado}`;
  }
}
