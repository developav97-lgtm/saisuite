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
import { MatDialog } from '@angular/material/dialog';
import { MatDividerModule } from '@angular/material/divider';
import { DashboardService } from '../../services/dashboard.service';
import { TrialService } from '../../services/trial.service';
import { DashboardListItem } from '../../models/dashboard.model';
import { TrialStatus } from '../../models/trial.model';
import { TrialBannerComponent } from '../trial-banner/trial-banner.component';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { ToastService } from '../../../../core/services/toast.service';

const VIEW_KEY = 'saisuite.saidashboardView';

@Component({
  selector: 'app-dashboard-list',
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
    MatDividerModule,
    TrialBannerComponent,
  ],
  templateUrl: './dashboard-list.component.html',
  styleUrl: './dashboard-list.component.scss',
})
export class DashboardListComponent implements OnInit {
  private readonly dashboardService = inject(DashboardService);
  private readonly trialService = inject(TrialService);
  private readonly router = inject(Router);
  private readonly dialog = inject(MatDialog);
  private readonly toast = inject(ToastService);
  private readonly destroyRef = inject(DestroyRef);

  // ── State ──────────────────────────────────────────────────
  readonly loading = signal(false);
  readonly dashboards = signal<DashboardListItem[]>([]);
  readonly sharedDashboards = signal<DashboardListItem[]>([]);
  readonly trialStatus = signal<TrialStatus | null>(null);
  readonly searchText = signal('');

  readonly viewMode = signal<'list' | 'cards'>(
    (localStorage.getItem(VIEW_KEY) as 'list' | 'cards') ?? 'list',
  );

  // ── Computed ───────────────────────────────────────────────
  readonly favoritos = computed(() =>
    this.dashboards().filter(d => d.es_favorito),
  );

  readonly filteredDashboards = computed(() => {
    const query = this.searchText().toLowerCase().trim();
    const all = this.dashboards();
    if (!query) return all;
    return all.filter(
      d =>
        d.titulo.toLowerCase().includes(query) ||
        d.descripcion.toLowerCase().includes(query),
    );
  });

  readonly filteredShared = computed(() => {
    const query = this.searchText().toLowerCase().trim();
    const all = this.sharedDashboards();
    if (!query) return all;
    return all.filter(
      d =>
        d.titulo.toLowerCase().includes(query) ||
        d.descripcion.toLowerCase().includes(query),
    );
  });

  readonly displayedColumns = ['titulo', 'card_count', 'created_at', 'acciones'];

  ngOnInit(): void {
    this.loadAll();
    this.loadTrialStatus();
  }

  private loadAll(): void {
    this.loading.set(true);

    this.dashboardService.list()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: items => {
          this.dashboards.set(items);
          this.loading.set(false);
        },
        error: () => {
          this.toast.error('No se pudieron cargar los dashboards.');
          this.loading.set(false);
        },
      });

    this.dashboardService.getSharedWithMe()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: items => this.sharedDashboards.set(items),
      });
  }

  private loadTrialStatus(): void {
    this.trialService.getStatus()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: status => this.trialStatus.set(status),
      });
  }

  // ── View mode ──────────────────────────────────────────────
  setViewMode(mode: 'list' | 'cards'): void {
    this.viewMode.set(mode);
    localStorage.setItem(VIEW_KEY, mode);
  }

  // ── Actions ────────────────────────────────────────────────
  nuevo(): void {
    this.router.navigate(['/saidashboard', 'nuevo']);
  }

  verDashboard(id: string): void {
    this.router.navigate(['/saidashboard', id]);
  }

  editDashboard(id: string): void {
    this.router.navigate(['/saidashboard', 'builder', id]);
  }

  toggleFavorite(dashboard: DashboardListItem, event: Event): void {
    event.stopPropagation();
    this.dashboardService.toggleFavorite(dashboard.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => {
          this.dashboards.update(list =>
            list.map(d =>
              d.id === dashboard.id ? { ...d, es_favorito: res.es_favorito } : d,
            ),
          );
          this.toast.success(
            res.es_favorito ? 'Agregado a favoritos.' : 'Removido de favoritos.',
          );
        },
        error: () => this.toast.error('Error al cambiar favorito.'),
      });
  }

  setDefault(dashboard: DashboardListItem): void {
    this.dashboardService.setDefault(dashboard.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.dashboards.update(list =>
            list.map(d => ({
              ...d,
              es_default: d.id === dashboard.id,
            })),
          );
          this.toast.success('Dashboard predeterminado actualizado.');
        },
        error: () => this.toast.error('Error al establecer dashboard predeterminado.'),
      });
  }

  confirmarEliminar(dashboard: DashboardListItem): void {
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        header: 'Confirmar eliminacion',
        message: `Eliminar el dashboard "${dashboard.titulo}"? Esta accion no se puede deshacer.`,
        acceptLabel: 'Eliminar',
        acceptColor: 'warn',
      },
      width: '400px',
    });
    ref.afterClosed().subscribe(confirmed => {
      if (confirmed) this.eliminar(dashboard.id);
    });
  }

  private eliminar(id: string): void {
    this.dashboardService.delete(id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.dashboards.update(list => list.filter(d => d.id !== id));
          this.toast.success('Dashboard eliminado correctamente.');
        },
        error: () => this.toast.error('No se pudo eliminar el dashboard.'),
      });
  }

  activateTrial(): void {
    this.trialService.activate()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.toast.success('Prueba activada correctamente.');
          this.loadTrialStatus();
        },
        error: () => this.toast.error('Error al activar la prueba.'),
      });
  }

  onSearch(): void {
    // Search is computed — no action needed, just triggers reactivity via searchText signal
  }
}
