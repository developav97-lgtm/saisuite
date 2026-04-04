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
import { ActivatedRoute, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormControl, FormGroup, Validators } from '@angular/forms';
import { CdkDragDrop, CdkDrag, CdkDropList, CdkDragPlaceholder, moveItemInArray } from '@angular/cdk/drag-drop';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatDialog } from '@angular/material/dialog';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { NavigationHistoryService } from '../../../../core/services/navigation-history.service';
import { DashboardService } from '../../services/dashboard.service';
import { CardCatalogService } from '../../services/card-catalog.service';
import {
  DashboardDetail,
  DashboardCard,
  DashboardCardCreate,
  CardLayoutItem,
  DashboardCreate,
  ChartType,
} from '../../models/dashboard.model';
import { CategoryWithCards, CardCatalogItem } from '../../models/card-catalog.model';
import {
  CardSelectorComponent,
  CardSelectorResult,
} from '../card-selector/card-selector.component';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { ToastService } from '../../../../core/services/toast.service';

interface BuilderCard {
  id: string | null; // null for new unsaved cards
  card_type_code: string;
  chart_type: ChartType;
  titulo_personalizado: string;
  icono: string;
  color: string;
  pos_x: number;
  pos_y: number;
  width: number;
  height: number;
  orden: number;
}

@Component({
  selector: 'app-dashboard-builder',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    CdkDrag,
    CdkDropList,
    CdkDragPlaceholder,
    MatButtonModule,
    MatIconModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatTooltipModule,
    MatProgressBarModule,
    MatProgressSpinnerModule,
    MatExpansionModule,
    MatSlideToggleModule,
  ],
  templateUrl: './dashboard-builder.component.html',
  styleUrl: './dashboard-builder.component.scss',
})
export class DashboardBuilderComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly dashboardService = inject(DashboardService);
  private readonly catalogService = inject(CardCatalogService);
  private readonly dialog = inject(MatDialog);
  private readonly toast = inject(ToastService);
  private readonly navHistory = inject(NavigationHistoryService);
  private readonly destroyRef = inject(DestroyRef);

  // ── State ──────────────────────────────────────────────────
  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly dashboardId = signal<string | null>(null);
  readonly isNew = computed(() => this.dashboardId() === null);
  readonly categories = signal<CategoryWithCards[]>([]);
  readonly builderCards = signal<BuilderCard[]>([]);
  readonly isMobile = signal(window.innerWidth < 768);
  readonly hasUnsavedChanges = signal(false);

  readonly form = new FormGroup({
    titulo: new FormControl('', { nonNullable: true, validators: [Validators.required, Validators.maxLength(255)] }),
    descripcion: new FormControl('', { nonNullable: true, validators: [Validators.maxLength(500)] }),
    es_privado: new FormControl(false, { nonNullable: true }),
  });

  constructor() {
    // Listen for window resize
    if (typeof window !== 'undefined') {
      window.addEventListener('resize', () => {
        this.isMobile.set(window.innerWidth < 768);
      });
    }
  }

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.dashboardId.set(id);
      this.loadDashboard(id);
    } else {
      this.loading.set(false);
    }
    this.loadCatalog();
  }

  private loadDashboard(id: string): void {
    this.dashboardService.getById(id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: detail => {
          this.form.patchValue({
            titulo: detail.titulo,
            descripcion: detail.descripcion,
            es_privado: detail.es_privado,
          });
          this.builderCards.set(
            detail.cards.map(c => this.cardToBuilderCard(c)),
          );
          this.loading.set(false);
        },
        error: () => {
          this.toast.error('Error al cargar el dashboard.');
          this.loading.set(false);
          this.router.navigate(['/saidashboard']);
        },
      });
  }

  private loadCatalog(): void {
    this.catalogService.getCategories()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: cats => this.categories.set(cats),
      });
  }

  private cardToBuilderCard(c: DashboardCard): BuilderCard {
    return {
      id: c.id,
      card_type_code: c.card_type_code,
      chart_type: c.chart_type,
      titulo_personalizado: c.titulo_personalizado,
      icono: 'bar_chart',
      color: '#1565c0',
      pos_x: c.pos_x,
      pos_y: c.pos_y,
      width: c.width,
      height: c.height,
      orden: c.orden,
    };
  }

  // ── Drag & Drop ────────────────────────────────────────────
  onCardDrop(event: CdkDragDrop<BuilderCard[]>): void {
    this.builderCards.update(cards => {
      const updated = [...cards];
      moveItemInArray(updated, event.previousIndex, event.currentIndex);
      // Recalculate orden
      return updated.map((c, i) => ({ ...c, orden: i }));
    });
    this.hasUnsavedChanges.set(true);
  }

  // ── Card management ────────────────────────────────────────
  openCardSelector(): void {
    const ref = this.dialog.open(CardSelectorComponent, {
      width: '800px',
      maxWidth: '95vw',
      maxHeight: '85vh',
    });

    ref.afterClosed().subscribe((result: CardSelectorResult | null) => {
      if (result) {
        this.addCard(result);
      }
    });
  }

  addCardFromCatalog(catalogCard: CardCatalogItem): void {
    const result: CardSelectorResult = {
      card: catalogCard,
      chartType: catalogCard.chart_default,
    };
    this.addCard(result);
  }

  private addCard(result: CardSelectorResult): void {
    const cards = this.builderCards();
    const newCard: BuilderCard = {
      id: null,
      card_type_code: result.card.code,
      chart_type: result.chartType,
      titulo_personalizado: result.card.nombre,
      icono: result.card.icono,
      color: result.card.color,
      pos_x: 0,
      pos_y: cards.length,
      width: 2,
      height: 1,
      orden: cards.length,
    };
    this.builderCards.update(list => [...list, newCard]);
    this.hasUnsavedChanges.set(true);
    this.toast.success(`Tarjeta "${result.card.nombre}" agregada.`);
  }

  removeCard(index: number): void {
    const card = this.builderCards()[index];
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        header: 'Eliminar tarjeta',
        message: `Eliminar la tarjeta "${card.titulo_personalizado}"?`,
        acceptLabel: 'Eliminar',
        acceptColor: 'warn',
      },
      width: '400px',
    });

    ref.afterClosed().subscribe(confirmed => {
      if (confirmed) {
        this.builderCards.update(list => list.filter((_, i) => i !== index));
        this.hasUnsavedChanges.set(true);
      }
    });
  }

  updateCardSize(index: number, width: number, height: number): void {
    this.builderCards.update(list =>
      list.map((c, i) =>
        i === index ? { ...c, width, height } : c,
      ),
    );
    this.hasUnsavedChanges.set(true);
  }

  onTitleChange(index: number, event: Event): void {
    const value = (event.target as HTMLInputElement).value;
    this.updateCardTitle(index, value);
  }

  updateCardTitle(index: number, title: string): void {
    this.builderCards.update(list =>
      list.map((c, i) =>
        i === index ? { ...c, titulo_personalizado: title } : c,
      ),
    );
    this.hasUnsavedChanges.set(true);
  }

  // ── Save ───────────────────────────────────────────────────
  save(): void {
    if (this.form.invalid) {
      this.toast.warning('Completa los campos requeridos.');
      return;
    }

    this.saving.set(true);
    const formValue = this.form.getRawValue();

    if (this.isNew()) {
      this.createDashboard(formValue);
    } else {
      this.updateDashboard(formValue);
    }
  }

  private createDashboard(formValue: DashboardCreate): void {
    this.dashboardService.create(formValue)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: created => {
          this.dashboardId.set(created.id);
          this.saveCards(created.id);
        },
        error: () => {
          this.saving.set(false);
          this.toast.error('Error al crear el dashboard.');
        },
      });
  }

  private updateDashboard(formValue: DashboardCreate): void {
    const id = this.dashboardId()!;
    this.dashboardService.update(id, formValue)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => this.saveCards(id),
        error: () => {
          this.saving.set(false);
          this.toast.error('Error al actualizar el dashboard.');
        },
      });
  }

  private saveCards(dashboardId: string): void {
    const cards = this.builderCards();

    // For new cards, add them first
    const newCards = cards.filter(c => c.id === null);
    const existingCards = cards.filter(c => c.id !== null);

    if (newCards.length > 0) {
      const addPromises = newCards.map(c => {
        const create: DashboardCardCreate = {
          card_type_code: c.card_type_code,
          chart_type: c.chart_type,
          pos_x: c.pos_x,
          pos_y: c.pos_y,
          width: c.width,
          height: c.height,
          titulo_personalizado: c.titulo_personalizado,
          orden: c.orden,
        };
        return this.dashboardService.addCard(dashboardId, create).toPromise();
      });

      Promise.all(addPromises)
        .then(results => {
          // Update builder cards with IDs from server
          const newIds = results.map(r => r?.id ?? null);
          let newIndex = 0;
          this.builderCards.update(list =>
            list.map(c => {
              if (c.id === null && newIndex < newIds.length) {
                return { ...c, id: newIds[newIndex++] };
              }
              return c;
            }),
          );
          this.saveLayout(dashboardId);
        })
        .catch(() => {
          this.saving.set(false);
          this.toast.error('Error al agregar tarjetas.');
        });
    } else if (existingCards.length > 0) {
      this.saveLayout(dashboardId);
    } else {
      this.saving.set(false);
      this.hasUnsavedChanges.set(false);
      this.toast.success('Dashboard guardado correctamente.');
    }
  }

  private saveLayout(dashboardId: string): void {
    const cards = this.builderCards();
    const layout: CardLayoutItem[] = cards
      .filter(c => c.id !== null)
      .map(c => ({
        id: c.id!,
        pos_x: c.pos_x,
        pos_y: c.pos_y,
        width: c.width,
        height: c.height,
        orden: c.orden,
      }));

    if (layout.length === 0) {
      this.saving.set(false);
      this.hasUnsavedChanges.set(false);
      this.toast.success('Dashboard guardado correctamente.');
      return;
    }

    this.dashboardService.saveLayout(dashboardId, { layout })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.saving.set(false);
          this.hasUnsavedChanges.set(false);
          this.toast.success('Dashboard guardado correctamente.');
        },
        error: () => {
          this.saving.set(false);
          this.toast.error('Error al guardar el layout.');
        },
      });
  }

  // ── Navigation ─────────────────────────────────────────────
  goBack(): void {
    if (this.hasUnsavedChanges()) {
      const ref = this.dialog.open(ConfirmDialogComponent, {
        data: {
          header: 'Cambios sin guardar',
          message: 'Tienes cambios sin guardar. Si sales se perderan.',
          acceptLabel: 'Salir sin guardar',
          acceptColor: 'warn',
        },
        width: '400px',
      });
      ref.afterClosed().subscribe(confirmed => {
        if (confirmed) this.navHistory.goBack('/saidashboard');
      });
    } else {
      this.navHistory.goBack('/saidashboard');
    }
  }

  preview(): void {
    const id = this.dashboardId();
    if (id) {
      this.router.navigate(['/saidashboard', id]);
    }
  }
}
