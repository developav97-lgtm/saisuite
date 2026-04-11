import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatMenuModule } from '@angular/material/menu';
import { MatTabsModule } from '@angular/material/tabs';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialog } from '@angular/material/dialog';
import { ReportBIService } from '../../services/report-bi.service';
import { ReportBIListItem, VISUALIZATION_LABELS, VISUALIZATION_ICONS, BISuggestResult } from '../../models/report-bi.model';
import { BI_SOURCES } from '../../models/bi-source.model';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { ReportShareDialogComponent, ReportShareDialogData } from '../report-share-dialog/report-share-dialog.component';
import { AuthService } from '../../../../core/auth/auth.service';
import { ToastService } from '../../../../core/services/toast.service';

@Component({
  selector: 'app-report-list',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    FormsModule,
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatInputModule,
    MatFormFieldModule,
    MatProgressBarModule,
    MatTooltipModule,
    MatMenuModule,
    MatTabsModule,
    MatChipsModule,
  ],
  templateUrl: './report-list.component.html',
  styleUrl: './report-list.component.scss',
})
export class ReportListComponent implements OnInit {
  private readonly reportBIService = inject(ReportBIService);
  private readonly router = inject(Router);
  private readonly dialog = inject(MatDialog);
  private readonly auth = inject(AuthService);
  private readonly toast = inject(ToastService);
  private readonly destroyRef = inject(DestroyRef);

  // ── State ──────────────────────────────────────────────────
  readonly loading = signal(false);
  readonly reports = signal<ReportBIListItem[]>([]);
  readonly templates = signal<ReportBIListItem[]>([]);
  readonly searchText = signal('');
  readonly activeTab = signal(0);
  readonly suggesting = signal(false);
  readonly suggestion = signal<BISuggestResult | null>(null);

  readonly displayedColumns = ['es_favorito', 'titulo', 'fuentes', 'tipo_visualizacion', 'updated_at', 'acciones'];

  // ── Computed ───────────────────────────────────────────────
  readonly filteredReports = computed(() => {
    const query = this.searchText().toLowerCase().trim();
    const all = this.reports();
    if (!query) return all;
    return all.filter(
      r => r.titulo.toLowerCase().includes(query) || r.descripcion.toLowerCase().includes(query),
    );
  });

  readonly favoritos = computed(() =>
    this.reports().filter(r => r.es_favorito),
  );

  ngOnInit(): void {
    this.loadAll();
  }

  private loadAll(): void {
    this.loading.set(true);

    this.reportBIService.list()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: items => {
          this.reports.set(items.filter(i => !i.es_template));
          this.loading.set(false);
        },
        error: () => {
          this.toast.error('No se pudieron cargar los reportes.');
          this.loading.set(false);
        },
      });

    this.reportBIService.getTemplates()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: items => this.templates.set(items),
      });
  }

  // ── Helpers ────────────────────────────────────────────────

  getVizLabel(viz: string): string {
    return VISUALIZATION_LABELS[viz as keyof typeof VISUALIZATION_LABELS] ?? viz;
  }

  getVizIcon(viz: string): string {
    return VISUALIZATION_ICONS[viz as keyof typeof VISUALIZATION_ICONS] ?? 'table_chart';
  }

  getSourceLabels(fuentes: string[]): string {
    return fuentes
      .map(f => BI_SOURCES.find(s => s.code === f)?.label ?? f)
      .join(', ');
  }

  // ── Actions ────────────────────────────────────────────────

  nuevo(): void {
    this.router.navigate(['/saidashboard', 'reportes', 'nuevo']);
  }

  ver(id: string): void {
    this.router.navigate(['/saidashboard', 'reportes', id]);
  }

  editar(id: string): void {
    this.router.navigate(['/saidashboard', 'reportes', id, 'edit']);
  }

  usarTemplate(template: ReportBIListItem): void {
    this.router.navigate(['/saidashboard', 'reportes', 'nuevo'], {
      queryParams: { template: template.id },
    });
  }

  toggleFavorite(report: ReportBIListItem, event: Event): void {
    event.stopPropagation();
    this.reportBIService.toggleFavorite(report.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => {
          this.reports.update(list =>
            list.map(r =>
              r.id === report.id ? { ...r, es_favorito: res.es_favorito } : r,
            ),
          );
          this.toast.success(
            res.es_favorito ? 'Agregado a favoritos.' : 'Removido de favoritos.',
          );
        },
        error: () => this.toast.error('Error al cambiar favorito.'),
      });
  }

  compartir(report: ReportBIListItem): void {
    this.dialog.open(ReportShareDialogComponent, {
      width: '520px',
      data: {
        reportId: report.id,
        reportTitle: report.titulo,
        existingShares: [],
        currentUserId: this.auth.currentUser()?.id ?? '',
      } satisfies ReportShareDialogData,
    });
  }

  confirmarEliminar(report: ReportBIListItem): void {
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        header: 'Confirmar eliminación',
        message: `¿Eliminar el reporte "${report.titulo}"? Esta acción no se puede deshacer.`,
        acceptLabel: 'Eliminar',
        acceptColor: 'warn',
      },
      width: '400px',
    });
    ref.afterClosed().subscribe(confirmed => {
      if (confirmed) this.eliminar(report.id);
    });
  }

  sugerirConIA(question: string): void {
    if (!question.trim()) return;
    this.suggesting.set(true);
    this.suggestion.set(null);

    this.reportBIService.suggestReport(question)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: result => {
          this.suggestion.set(result);
          this.suggesting.set(false);
          if (result.template_titulo && result.config) {
            this.toast.success(`Sugerencia: ${result.template_titulo}`);
          } else {
            this.toast.info(result.explanation || 'No se encontró un template adecuado.');
          }
        },
        error: () => {
          this.suggesting.set(false);
          this.toast.error('Error al obtener sugerencia IA.');
        },
      });
  }

  usarSugerencia(): void {
    const s = this.suggestion();
    if (!s?.config) return;
    this.router.navigate(['/saidashboard', 'reportes', 'nuevo'], {
      queryParams: { preset: JSON.stringify(s.config) },
    });
  }

  private eliminar(id: string): void {
    this.reportBIService.delete(id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.reports.update(list => list.filter(r => r.id !== id));
          this.toast.success('Reporte eliminado correctamente.');
        },
        error: () => this.toast.error('No se pudo eliminar el reporte.'),
      });
  }
}
