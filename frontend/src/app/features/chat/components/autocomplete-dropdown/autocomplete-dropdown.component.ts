import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { AutocompleteEntidad, AutocompleteUsuario } from '../../models/chat.models';

export type AutocompleteItem =
  | { kind: 'entidad'; value: AutocompleteEntidad }
  | { kind: 'usuario'; value: AutocompleteUsuario };

@Component({
  selector: 'app-autocomplete-dropdown',
  imports: [MatIconModule, MatProgressBarModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="ac-dropdown">
      @if (loading()) {
        <mat-progress-bar mode="indeterminate" class="ac-dropdown__loader" />
      }
      @if (items().length > 0) {
        <ul class="ac-dropdown__list" role="listbox">
          @for (item of items(); track $index; let i = $index) {
            <li class="ac-dropdown__item"
                [class.ac-dropdown__item--active]="i === activeIndex()"
                role="option"
                (click)="select.emit(item)">
              @if (item.kind === 'entidad') {
                <mat-icon class="ac-dropdown__icon">description</mat-icon>
                <span class="ac-dropdown__text">
                  <span class="ac-dropdown__title">
                    <strong>{{ item.value.codigo }}</strong> — {{ item.value.nombre }}
                  </span>
                  <span class="ac-dropdown__sub">{{ item.value.tipo }}</span>
                </span>
              } @else {
                <mat-icon class="ac-dropdown__icon">person</mat-icon>
                <span class="ac-dropdown__text">
                  <span class="ac-dropdown__title">{{ item.value.nombre }}</span>
                  <span class="ac-dropdown__sub">{{ item.value.email }}</span>
                </span>
              }
            </li>
          }
        </ul>
      } @else if (!loading()) {
        <div class="ac-dropdown__empty">
          <mat-icon>search_off</mat-icon>
          <span>Sin resultados</span>
        </div>
      }
    </div>
  `,
  styles: [`
    .ac-dropdown {
      position: absolute;
      bottom: 100%;
      left: 0;
      right: 0;
      max-height: 240px;
      overflow-y: auto;
      background: var(--sc-surface-card, #fff);
      border: 1px solid var(--sc-surface-border, #e2e8f0);
      border-radius: var(--sc-radius, 10px);
      box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.15);
      z-index: 1001;
      margin-bottom: 4px;
    }

    .ac-dropdown__loader {
      border-radius: var(--sc-radius, 10px) var(--sc-radius, 10px) 0 0;
    }

    .ac-dropdown__list {
      list-style: none;
      margin: 0;
      padding: 4px 0;
    }

    .ac-dropdown__item {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 8px 14px;
      cursor: pointer;
      transition: background 0.1s;

      &:hover {
        background: var(--sc-surface-hover, rgba(0, 0, 0, 0.06));
      }

      &--active {
        background: var(--sc-primary-50, rgba(21, 101, 192, 0.1));
      }
    }

    .ac-dropdown__icon {
      font-size: 18px;
      width: 18px;
      height: 18px;
      flex-shrink: 0;
      color: var(--sc-text-muted, #718096);
    }

    .ac-dropdown__text {
      display: flex;
      flex-direction: column;
      min-width: 0;
      flex: 1;
    }

    .ac-dropdown__title {
      font-size: 0.875rem;
      color: var(--sc-text-color, #1a202c);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      line-height: 1.3;
    }

    .ac-dropdown__sub {
      font-size: 0.75rem;
      color: var(--sc-text-muted, #718096);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      line-height: 1.3;
    }

    .ac-dropdown__empty {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px 16px;
      color: var(--sc-text-muted, #718096);
      font-size: 0.85rem;

      mat-icon {
        font-size: 18px;
        width: 18px;
        height: 18px;
      }
    }
  `],
})
export class AutocompleteDropdownComponent {
  readonly items = input<AutocompleteItem[]>([]);
  readonly activeIndex = input(0);
  readonly loading = input(false);
  readonly select = output<AutocompleteItem>();
}
