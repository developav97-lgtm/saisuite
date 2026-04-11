import {
  ChangeDetectionStrategy,
  Component,
  computed,
  input,
  output,
} from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule, MatTableDataSource } from '@angular/material/table';
import { MatProgressBarModule } from '@angular/material/progress-bar';

export interface DrillDownData {
  title: string;
  filters: Record<string, unknown>;
  columns: string[];
  rows: Record<string, unknown>[];
  loading: boolean;
}

@Component({
  selector: 'app-drill-down-panel',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DecimalPipe,
    MatButtonModule,
    MatIconModule,
    MatTableModule,
    MatProgressBarModule,
  ],
  templateUrl: './drill-down-panel.component.html',
  styleUrl: './drill-down-panel.component.scss',
})
export class DrillDownPanelComponent {
  readonly data = input<DrillDownData | null>(null);
  readonly close = output<void>();

  readonly isOpen = computed(() => this.data() !== null);
  readonly columns = computed(() => this.data()?.columns ?? []);
  readonly title = computed(() => this.data()?.title ?? '');
  readonly loading = computed(() => this.data()?.loading ?? false);

  readonly dataSource = computed(() => {
    const d = this.data();
    const ds = new MatTableDataSource<Record<string, unknown>>(d?.rows ?? []);
    return ds;
  });

  readonly filterChips = computed(() => {
    const d = this.data();
    if (!d) return [];
    return Object.entries(d.filters).map(([key, value]) => ({
      key,
      value: String(value),
    }));
  });

  isNumeric(value: unknown): boolean {
    return typeof value === 'number';
  }

  onClose(): void {
    this.close.emit();
  }
}
