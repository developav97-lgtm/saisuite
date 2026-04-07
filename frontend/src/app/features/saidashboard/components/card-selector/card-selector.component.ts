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
import { FormsModule } from '@angular/forms';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTabsModule } from '@angular/material/tabs';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { CardCatalogService } from '../../services/card-catalog.service';
import { CardCatalogItem, CategoryWithCards } from '../../models/card-catalog.model';
import { ChartType } from '../../models/dashboard.model';
import { CustomRangoCuentasConfig } from '../../models/report-filter.model';
import {
  CustomCardConfigComponent,
  CustomCardConfigDialogData,
  CustomCardConfigDialogResult,
} from '../custom-card-config/custom-card-config.component';
import { MatDialog } from '@angular/material/dialog';

export interface CardSelectorResult {
  card: CardCatalogItem;
  chartType: ChartType;
  filtrosConfig?: Record<string, unknown>;
}

@Component({
  selector: 'app-card-selector',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    MatTabsModule,
    MatFormFieldModule,
    MatInputModule,
    MatChipsModule,
    MatTooltipModule,
    MatProgressBarModule,
  ],
  templateUrl: './card-selector.component.html',
  styleUrl: './card-selector.component.scss',
})
export class CardSelectorComponent implements OnInit {
  private readonly catalogService = inject(CardCatalogService);
  private readonly dialogRef = inject(MatDialogRef<CardSelectorComponent>);
  private readonly dialog = inject(MatDialog);
  private readonly destroyRef = inject(DestroyRef);

  readonly categories = signal<CategoryWithCards[]>([]);
  readonly loading = signal(true);
  readonly searchText = signal('');
  readonly selectedCard = signal<CardCatalogItem | null>(null);
  readonly selectedChartType = signal<ChartType | null>(null);

  readonly filteredCategories = computed(() => {
    const cats = this.categories();
    const query = this.searchText().toLowerCase().trim();
    if (!query) return cats;

    return cats
      .map(cat => ({
        ...cat,
        cards: cat.cards.filter(
          c =>
            c.nombre.toLowerCase().includes(query) ||
            c.descripcion.toLowerCase().includes(query),
        ),
      }))
      .filter(cat => cat.cards.length > 0);
  });

  readonly canConfirm = computed(() =>
    this.selectedCard() !== null && this.selectedChartType() !== null,
  );

  ngOnInit(): void {
    this.catalogService.getCategories()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: cats => {
          this.categories.set(cats);
          this.loading.set(false);
        },
        error: () => this.loading.set(false),
      });
  }

  selectCard(card: CardCatalogItem): void {
    this.selectedCard.set(card);
    this.selectedChartType.set(card.chart_default);
  }

  selectChartType(type: ChartType): void {
    this.selectedChartType.set(type);
  }

  isCardSelected(card: CardCatalogItem): boolean {
    return this.selectedCard()?.code === card.code;
  }

  confirm(): void {
    const card = this.selectedCard();
    const chartType = this.selectedChartType();
    if (!card || !chartType) return;

    // Si la tarjeta requiere configuracion adicional, abrir el diálogo de config
    if (card.requiere_config) {
      const configRef = this.dialog.open(CustomCardConfigComponent, {
        width: '520px',
        maxWidth: '95vw',
        data: {
          cardTypeCode: card.code,
          cardNombre: card.nombre,
          initialConfig: null,
        } as CustomCardConfigDialogData,
      });

      configRef.afterClosed().subscribe((result: CustomCardConfigDialogResult | null) => {
        if (result) {
          this.dialogRef.close({
            card,
            chartType,
            filtrosConfig: result.config as unknown as Record<string, unknown>,
          } as CardSelectorResult);
        }
      });
      return;
    }

    this.dialogRef.close({ card, chartType } as CardSelectorResult);
  }

  cancel(): void {
    this.dialogRef.close(null);
  }
}
