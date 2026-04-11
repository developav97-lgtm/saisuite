import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  inject,
  input,
  output,
  signal,
  effect,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatSelectModule } from '@angular/material/select';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { BIFilterDef } from '../../models/bi-field.model';
import { ReportBIService } from '../../services/report-bi.service';

@Component({
  selector: 'app-filter-builder',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatDatepickerModule,
    MatSelectModule,
    MatIconModule,
    MatButtonModule,
    MatChipsModule,
  ],
  templateUrl: './filter-builder.component.html',
  styleUrl: './filter-builder.component.scss',
})
export class FilterBuilderComponent {
  private readonly reportBIService = inject(ReportBIService);
  private readonly destroyRef = inject(DestroyRef);

  readonly sources = input<string[]>([]);
  readonly filters = input<Record<string, unknown>>({});
  readonly filtersChange = output<Record<string, unknown>>();

  readonly availableFilters = signal<BIFilterDef[]>([]);

  constructor() {
    effect(() => {
      const srcs = this.sources();
      if (srcs.length > 0) {
        this.loadFilters(srcs);
      } else {
        this.availableFilters.set([]);
      }
    });
  }

  private loadFilters(srcs: string[]): void {
    const allFilters: BIFilterDef[] = [];
    let pending = srcs.length;

    for (const src of srcs) {
      this.reportBIService.getFilters(src)
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe({
          next: filters => {
            // Deduplicate by field name
            for (const f of filters) {
              if (!allFilters.some(existing => existing.field === f.field)) {
                allFilters.push(f);
              }
            }
            pending--;
            if (pending === 0) {
              this.availableFilters.set(allFilters);
            }
          },
          error: () => {
            pending--;
          },
        });
    }
  }

  getFilterValue(field: string): unknown {
    return this.filters()[field] ?? null;
  }

  updateFilter(field: string, value: unknown): void {
    const updated = { ...this.filters(), [field]: value };
    // Remove empty values
    if (value === null || value === undefined || value === '') {
      delete updated[field];
    }
    this.filtersChange.emit(updated);
  }

  clearFilter(field: string): void {
    const updated = { ...this.filters() };
    delete updated[field];
    this.filtersChange.emit(updated);
  }

  clearAll(): void {
    this.filtersChange.emit({});
  }

  get activeFilterCount(): number {
    return Object.keys(this.filters()).length;
  }
}
