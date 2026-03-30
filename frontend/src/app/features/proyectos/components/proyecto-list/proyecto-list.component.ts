import { AfterViewInit, ChangeDetectionStrategy, Component, OnInit, ViewChild, effect, inject, signal } from '@angular/core';
import { Router } from '@angular/router';

const PROYECTOS_VIEW_KEY = 'saisuite.proyectosView';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatTableModule, MatTableDataSource } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatSortModule, MatSort } from '@angular/material/sort';
import { MatDialog } from '@angular/material/dialog';
import { ProyectoService, ProyectoListParams } from '../../services/proyecto.service';
import { ProyectoList, EstadoProyecto, TipoProyecto, ESTADO_LABELS, TIPO_LABELS } from '../../models/proyecto.model';
import { AdminService } from '../../../admin/services/admin.service';
import { AdminUser } from '../../../admin/models/admin.models';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { ToastService } from '../../../../core/services/toast.service';
import { HasPermissionDirective } from '../../../../core/directives/has-permission.directive';

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
    MatSortModule, HasPermissionDirective,
  ],
})
export class ProyectoListComponent implements OnInit, AfterViewInit {
  private readonly proyectoService = inject(ProyectoService);
  private readonly adminService    = inject(AdminService);
  private readonly router          = inject(Router);
  private readonly dialog          = inject(MatDialog);
  private readonly toast       = inject(ToastService);

  readonly proyectos     = signal<ProyectoList[]>([]);
  readonly totalCount    = signal(0);
  readonly loading       = signal(false);

  readonly dataSource = new MatTableDataSource<ProyectoList>([]);
  @ViewChild(MatSort) sort!: MatSort;

  constructor() {
    effect(() => {
      this.dataSource.data = this.proyectos();
    });
  }

  ngAfterViewInit(): void {
    this.dataSource.sort = this.sort;
  }
  readonly searchText    = signal('');
  readonly estadoFilter  = signal<EstadoProyecto | null>(null);
  readonly tipoFilter    = signal<TipoProyecto | null>(null);
  readonly gerenteFilter = signal<string | null>(null);
  readonly usuarios      = signal<AdminUser[]>([]);
  readonly pageSize      = 25;

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
    if (localStorage.getItem(PROYECTOS_VIEW_KEY) === 'cards') {
      this.router.navigate(['/proyectos', 'cards']);
      return;
    }
    this.loadUsuarios();
    this.loadProyectos(0, this.pageSize);
  }

  private loadUsuarios(): void {
    this.adminService.listUsers().subscribe({
      next: (res) => this.usuarios.set(res.results),
      error: () => { /* silencioso: el filtro de gerente simplemente no muestra opciones */ },
    });
  }

  loadProyectos(pageIndex: number, pageSize: number): void {
    this.loading.set(true);
    const params: ProyectoListParams = { page: pageIndex + 1, page_size: pageSize };
    if (this.searchText())    params.search     = this.searchText();
    if (this.estadoFilter())  params.estado     = this.estadoFilter()!;
    if (this.tipoFilter())    params.tipo       = this.tipoFilter()!;
    if (this.gerenteFilter()) params.gerente_id = this.gerenteFilter()!;

    this.proyectoService.list(params).subscribe({
      next: (res) => { this.proyectos.set(res.results); this.totalCount.set(res.count); this.loading.set(false); },
      error: () => {
        this.toast.error('No se pudieron cargar los proyectos.');
        this.loading.set(false);
      },
    });
  }

  onSearch(): void { this.loadProyectos(0, this.pageSize); }
  onFilterChange(): void { this.loadProyectos(0, this.pageSize); }
  onPage(event: PageEvent): void { this.loadProyectos(event.pageIndex, event.pageSize); }
  verDetalle(id: string): void { this.router.navigate(['/proyectos', id]); }
  nuevoProyecto():        void { this.router.navigate(['/proyectos', 'nuevo']); }
  irACards(): void {
    localStorage.setItem(PROYECTOS_VIEW_KEY, 'cards');
    this.router.navigate(['/proyectos', 'cards']);
  }

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
        this.toast.success('Proyecto eliminado correctamente.');
        this.loadProyectos(0, this.pageSize);
      },
      error: () => this.toast.error('No se pudo eliminar el proyecto.'),
    });
  }

  formatCurrency(value: string): string {
    const num = parseFloat(value);
    return isNaN(num) ? value : num.toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 });
  }

  estadoLabel(estado: string): string {
    return ESTADO_LABELS[estado as EstadoProyecto] ?? estado;
  }

  tipoLabel(tipo: string): string {
    return TIPO_LABELS[tipo as TipoProyecto] ?? tipo;
  }

  estadoClass(estado: string): string {
    return `pl-estado-badge pl-estado-badge--${estado}`;
  }
}
