import {
  ChangeDetectionStrategy,
  Component,
  input,
  output,
} from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatRippleModule } from '@angular/material/core';
import { BISource, BI_SOURCES } from '../../models/bi-source.model';

@Component({
  selector: 'app-source-selector',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatIconModule, MatRippleModule],
  templateUrl: './source-selector.component.html',
  styleUrl: './source-selector.component.scss',
})
export class SourceSelectorComponent {
  readonly selected = input<string[]>([]);
  readonly selectionChange = output<string[]>();

  readonly sources: BISource[] = BI_SOURCES;

  isSelected(code: string): boolean {
    return this.selected().includes(code);
  }

  toggle(code: string): void {
    const current = this.selected();
    const next = this.isSelected(code)
      ? current.filter(c => c !== code)
      : [...current, code];
    this.selectionChange.emit(next);
  }
}
