/**
 * SaiSuite — CRM Leads Page
 * Lista de leads con búsqueda, filtros y acciones de conversión/importación.
 */
import {
  ChangeDetectionStrategy, Component, OnInit, OnDestroy,
  inject, signal, ViewChild,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { MatTableModule, MatTableDataSource } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatPaginatorModule, MatPaginator, PageEvent } from '@angular/material/paginator';
import { MatMenuModule } from '@angular/material/menu';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatBadgeModule } from '@angular/material/badge';
import { Subject, takeUntil, debounceTime, distinctUntilChanged } from 'rxjs';

import { CrmService } from '../../services/crm.service';
import { CrmLead, FuenteLead } from '../../models/crm.model';
import { ToastService } from '../../../../core/services/toast.service';
import { LeadImportDialogComponent } from '../../components/lead-import-dialog/lead-import-dialog.component';
import { LeadConvertirDialogComponent } from '../../components/lead-convertir-dialog/lead-convertir-dialog.component';

@Component({
  selector: 'app-leads-page',
  templateUrl: './leads-page.component.html',
  styleUrl: './leads-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, FormsModule, RouterModule,
    MatTableModule, MatButtonModule, MatIconModule,
    MatFormFieldModule, MatInputModule, MatSelectModule,
    MatChipsModule, MatProgressBarModule, MatPaginatorModule,
    MatMenuModule, MatTooltipModule, MatDialogModule, MatBadgeModule,
  ],
})
export class LeadsPageComponent implements OnInit, OnDestroy {
  private readonly crm    = inject(CrmService);
  private readonly router = inject(Router);
  private readonly toast  = inject(ToastService);
  private readonly dialog = inject(MatDialog);
  private readonly destroy$ = new Subject<void>();
  private readonly searchChange$ = new Subject<string>();

  @ViewChild(MatPaginator) paginator!: MatPaginator;

  readonly leads    = signal<CrmLead[]>([]);
  readonly loading  = signal(false);
  readonly total    = signal(0);

  readonly searchTerm  = signal('');
  readonly filtroFuente = signal('');

  readonly pageSize  = signal(20);
  readonly pageIndex = signal(0);

  readonly displayedColumns = [
    'nombre', 'empresa', 'email', 'fuente', 'score', 'asignado_a', 'acciones',
  ];

  readonly dataSource = new MatTableDataSource<CrmLead>();

  readonly fuenteOpciones: { value: FuenteLead | ''; label: string }[] = [
    { value: '', label: 'Todas las fuentes' },
    { value: 'manual', label: 'Manual' },
    { value: 'webhook', label: 'Webhook' },
    { value: 'csv', label: 'CSV/Excel' },
    { value: 'referido', label: 'Referido' },
    { value: 'otro', label: 'Otro' },
  ];

  ngOnInit(): void {
    this.searchChange$.pipe(
      debounceTime(400),
      distinctUntilChanged(),
      takeUntil(this.destroy$),
    ).subscribe(() => {
      this.pageIndex.set(0);
      this.loadLeads();
    });

    this.loadLeads();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  onSearchChange(value: string): void {
    this.searchTerm.set(value);
    this.searchChange$.next(value);
  }

  onFuenteChange(value: string): void {
    this.filtroFuente.set(value);
    this.pageIndex.set(0);
    this.loadLeads();
  }

  onPageChange(event: PageEvent): void {
    this.pageIndex.set(event.pageIndex);
    this.pageSize.set(event.pageSize);
    this.loadLeads();
  }

  private loadLeads(): void {
    this.loading.set(true);
    this.crm.listLeads({
      search: this.searchTerm() || undefined,
      fuente: this.filtroFuente() || undefined,
      page: this.pageIndex() + 1,
      page_size: this.pageSize(),
    }).pipe(takeUntil(this.destroy$)).subscribe({
      next: resp => {
        this.leads.set(resp.results);
        this.dataSource.data = resp.results;
        this.total.set(resp.count);
        this.loading.set(false);
      },
      error: () => {
        this.toast.error('Error cargando leads');
        this.loading.set(false);
      },
    });
  }

  openImportDialog(): void {
    const ref = this.dialog.open(LeadImportDialogComponent, { width: '600px' });
    ref.afterClosed().pipe(takeUntil(this.destroy$)).subscribe(imported => {
      if (imported) {
        this.loadLeads();
        this.toast.success(`${imported} leads importados correctamente`);
      }
    });
  }

  openConvertirDialog(lead: CrmLead): void {
    const ref = this.dialog.open(LeadConvertirDialogComponent, {
      width: '480px',
      data: lead,
    });
    ref.afterClosed().pipe(takeUntil(this.destroy$)).subscribe(result => {
      if (result) {
        this.loadLeads();
        this.toast.success('Lead convertido a oportunidad');
        this.router.navigate(['/crm/oportunidades', result.id]);
      }
    });
  }

  deleteLead(lead: CrmLead): void {
    this.crm.deleteLead(lead.id).pipe(takeUntil(this.destroy$)).subscribe({
      next: () => {
        this.toast.success('Lead eliminado');
        this.loadLeads();
      },
      error: () => this.toast.error('Error eliminando lead'),
    });
  }

  asignarRoundRobin(lead: CrmLead, event: Event): void {
    event.stopPropagation();
    this.crm.asignarRoundRobin(lead.id).pipe(takeUntil(this.destroy$)).subscribe({
      next: updated => {
        this.leads.update(list => list.map(l => l.id === updated.id ? updated : l));
        this.dataSource.data = this.leads();
        this.toast.success(`Asignado a ${updated.asignado_a_nombre ?? 'vendedor'}`);
      },
      error: () => this.toast.error('No hay vendedores disponibles para asignar'),
    });
  }

  asignarTodosRoundRobin(): void {
    this.crm.asignarMasivoRoundRobin().pipe(takeUntil(this.destroy$)).subscribe({
      next: ({ asignados }) => {
        this.toast.success(`${asignados} lead${asignados !== 1 ? 's' : ''} asignado${asignados !== 1 ? 's' : ''}`);
        this.loadLeads();
      },
      error: () => this.toast.error('Error al asignar leads'),
    });
  }

  getScoreColor(score: number): string {
    if (score >= 70) return 'var(--sc-success)';
    if (score >= 40) return 'var(--sc-warning)';
    return 'var(--sc-text-secondary)';
  }

  getFuenteLabel(fuente: FuenteLead): string {
    const map: Record<string, string> = {
      manual: 'Manual', webhook: 'Webhook', csv: 'CSV',
      referido: 'Referido', otro: 'Otro',
    };
    return map[fuente] ?? fuente;
  }
}
