/**
 * SaiSuite — ProyectoCardsComponent
 * Vista de tarjetas de proyectos con métricas resumidas.
 */
import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ProyectoService, ProyectoListParams } from '../../services/proyecto.service';
import {
  ProyectoList,
  EstadoProyecto,
  TipoProyecto,
  ESTADO_LABELS,
  TIPO_LABELS,
} from '../../models/proyecto.model';
import { AdminService } from '../../../admin/services/admin.service';
import { AdminUser } from '../../../admin/models/admin.models';

@Component({
  selector: 'app-proyecto-cards',
  standalone: true,
  imports: [
    CommonModule, FormsModule,
    MatButtonModule, MatIconModule,
    MatInputModule, MatFormFieldModule, MatSelectModule,
    MatPaginatorModule, MatProgressBarModule, MatTooltipModule,
  ],
  templateUrl: './proyecto-cards.component.html',
  styleUrl: './proyecto-cards.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ProyectoCardsComponent implements OnInit {
  private readonly proyectoService = inject(ProyectoService);
  private readonly adminService    = inject(AdminService);
  private readonly router          = inject(Router);
  private readonly snackBar        = inject(MatSnackBar);

  readonly proyectos     = signal<ProyectoList[]>([]);
  readonly totalCount    = signal(0);
  readonly loading       = signal(false);
  readonly searchText    = signal('');
  readonly estadoFilter  = signal<EstadoProyecto | null>(null);
  readonly tipoFilter    = signal<TipoProyecto | null>(null);
  readonly gerenteFilter = signal<string | null>(null);
  readonly usuarios      = signal<AdminUser[]>([]);
  readonly pageSize      = 25;

  readonly estadoOptions: { label: string; value: EstadoProyecto | null }[] = [
    { label: 'Todos los estados', value: null },
    ...Object.entries(ESTADO_LABELS).map(([v, l]) => ({ label: l, value: v as EstadoProyecto })),
  ];

  readonly tipoOptions: { label: string; value: TipoProyecto | null }[] = [
    { label: 'Todos los tipos', value: null },
    ...Object.entries(TIPO_LABELS).map(([v, l]) => ({ label: l, value: v as TipoProyecto })),
  ];

  ngOnInit(): void {
    this.loadUsuarios();
    this.load(0);
  }

  private loadUsuarios(): void {
    this.adminService.listUsers().subscribe({
      next: (res) => this.usuarios.set(res.results),
      error: () => { /* silencioso: el filtro de gerente simplemente no muestra opciones */ },
    });
  }

  load(pageIndex: number): void {
    this.loading.set(true);
    const params: ProyectoListParams = { page: pageIndex + 1, page_size: this.pageSize };
    if (this.searchText())    params.search     = this.searchText();
    if (this.estadoFilter())  params.estado     = this.estadoFilter()!;
    if (this.tipoFilter())    params.tipo       = this.tipoFilter()!;
    if (this.gerenteFilter()) params.gerente_id = this.gerenteFilter()!;

    this.proyectoService.list(params).subscribe({
      next: (res) => {
        this.proyectos.set(res.results);
        this.totalCount.set(res.count);
        this.loading.set(false);
      },
      error: () => {
        this.snackBar.open('No se pudieron cargar los proyectos.', 'Cerrar', { duration: 4000, panelClass: ['snack-error'] });
        this.loading.set(false);
      },
    });
  }

  onFilterChange(): void { this.load(0); }
  onSearch():       void { this.load(0); }
  onPage(e: PageEvent): void { this.load(e.pageIndex); }

  irALista(): void {
    localStorage.setItem('saisuite.proyectosView', 'list');
    this.router.navigate(['/proyectos', 'lista']);
  }
  verDetalle(id: string): void { this.router.navigate(['/proyectos', id]); }
  nuevoProyecto():       void { this.router.navigate(['/proyectos', 'nuevo']); }

  estadoLabel(estado: string): string {
    return ESTADO_LABELS[estado as EstadoProyecto] ?? estado;
  }

  tipoLabel(tipo: string): string {
    return TIPO_LABELS[tipo as TipoProyecto] ?? tipo;
  }

  estadoClass(estado: string): string {
    return `pc-estado pc-estado--${estado}`;
  }

  formatCurrency(value: string): string {
    const num = parseFloat(value);
    return isNaN(num)
      ? value
      : num.toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 });
  }

  formatDate(date: string | null): string {
    if (!date) return '—';
    return new Date(date + 'T00:00:00').toLocaleDateString('es-CO', {
      day: '2-digit', month: 'short', year: 'numeric',
    });
  }

  progressValue(p: ProyectoList): number {
    return parseFloat(p.porcentaje_avance) || 0;
  }

  progressColor(p: ProyectoList): string {
    const v = this.progressValue(p);
    if (v >= 80) return 'primary';
    if (v >= 40) return 'accent';
    return 'warn';
  }
}
