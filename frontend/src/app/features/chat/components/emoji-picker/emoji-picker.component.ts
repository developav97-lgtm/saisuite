import {
  ChangeDetectionStrategy, Component, output, signal, computed,
} from '@angular/core';
import { FormsModule } from '@angular/forms';

interface EmojiCategory {
  name: string;
  icon: string;
  emojis: string[];
}

const CATEGORIES: EmojiCategory[] = [
  {
    name: 'Smileys',
    icon: '😀',
    emojis: [
      '😀','😃','😄','😁','😆','😅','😂','🤣','😊','😇','🙂','😉','😌','😍','🥰','😘',
      '😋','😛','😝','😜','🤪','🤨','🧐','🤓','😎','🤩','🥳','😏','😒','😞','😔','😟',
      '😕','🙁','😣','😖','😫','😩','🥺','😢','😭','😤','😠','😡','🤬','🤯','😳','🥵',
      '🥶','😱','😨','😰','😥','😓','🤗','🤔','🤫','🤥','😶','😐','😑','😬','🙄','😯',
      '😦','😧','😮','😲','🥱','😴','🤤','😪','😵','🤐','🥴','🤢','🤮','🤧','😷','🤒',
      '🤕','🤑','🤠','😈','👿','👻','💩','💀','🤖','👽','😺','😸','😹','😻','😼','😽',
      '🙀','😿','😾',
    ],
  },
  {
    name: 'Gestos',
    icon: '👋',
    emojis: [
      '👋','🤚','🖐️','✋','👌','✌️','🤞','🤟','🤘','🤙','👈','👉','👆','👇','☝️',
      '👍','👎','✊','👊','🤛','🤜','👏','🙌','🤲','🤝','🙏','💪','🫶','✍️','💅','🤳',
      '❤️','🧡','💛','💚','💙','💜','🖤','💔','💕','💞','💓','💗','💖','💘','💝','💋','💌',
    ],
  },
  {
    name: 'Animales',
    icon: '🐶',
    emojis: [
      '🐶','🐱','🐭','🐹','🐰','🦊','🐻','🐼','🐨','🐯','🦁','🐮','🐷','🐸','🐵',
      '🙈','🙉','🙊','🐔','🐧','🐦','🐤','🦆','🦅','🦉','🦇','🐺','🐴','🦄','🐝','🦋',
      '🐛','🐌','🐞','🐜','🐢','🐍','🦎','🐙','🦑','🦐','🦞','🦀','🐟','🐬','🐳','🐋',
      '🦈','🐊','🐅','🐆','🦓','🐘','🦛','🦏','🦒','🦘','🐃','🐄','🐎','🐑','🦙','🐐',
      '🦌','🐕','🐩','🐈','🐇','🦝','🦨','🦡','🦦','🦥','🐁','🐀','🐿️','🦔',
    ],
  },
  {
    name: 'Comida',
    icon: '🍎',
    emojis: [
      '🍎','🍊','🍋','🍌','🍉','🍇','🍓','🫐','🍒','🍑','🥭','🍍','🥥','🥝','🍅',
      '🍆','🥑','🥦','🥬','🥕','🌽','🌶️','🥒','🍄','🥜','🌰','🍞','🥐','🥯','🧀','🥚',
      '🍳','🥞','🧇','🥓','🥩','🍗','🍖','🌭','🍔','🍟','🍕','🌮','🌯','🥗','🍝','🍜',
      '🍲','🍛','🍣','🍱','🥟','🍤','🍙','🍚','🍘','🧁','🍰','🎂','🍮','🍭','🍬','🍫',
      '🍿','🍩','🍪','☕','🍵','🥤','🧃','🧋','🍺','🍻','🥂','🍷','🥃','🍸','🍹',
    ],
  },
  {
    name: 'Actividades',
    icon: '⚽',
    emojis: [
      '⚽','🏀','🏈','⚾','🎾','🏐','🏉','🎱','🏓','🏸','🥊','🥋','⛳','🎯','🎮',
      '🎲','♟️','🎭','🎨','🎬','🎤','🎧','🎼','🎹','🥁','🎷','🎺','🎸','🎻','🏆','🥇',
      '🥈','🥉','🎖️','🏅','🎗️','🎫','🎟️','🎪','🤹','🎠','🎡','🎢',
    ],
  },
  {
    name: 'Viaje',
    icon: '🚗',
    emojis: [
      '🚗','🚕','🚙','🚌','🚎','🚓','🚑','🚒','🚐','🚚','🚛','🚜','🏍️','🛵','🚲',
      '🛴','🛹','🚢','✈️','🛩️','🚁','🚀','🛸','🌍','🌎','🌏','🗺️','🧭','⛰️','🏔️',
      '🌋','🏕️','🏖️','🏜️','🏝️','🏟️','🏛️','🏠','🏡','🏢','🏥','🏦','🏨','🏪','🏫',
      '🏬','🏰','🗼','🗽','⛪','🕌',
    ],
  },
  {
    name: 'Objetos',
    icon: '💡',
    emojis: [
      '💡','🔦','🕯️','💻','🖥️','📱','📲','☎️','📺','📷','📸','📹','🔭','🔬','🩺',
      '💊','🩹','🔑','🗝️','🔒','🔓','🧰','🔧','🔨','⚒️','🛠️','📦','📫','📪','📬',
      '📮','📢','📣','🔔','📻','🎵','🎶','📀','💿','📼','📖','📚','📝','✏️','📌','📍',
      '📎','✂️','💰','💳','✉️','📧','📩','📨','🗂️','📋','📊','📈','📉','🗒️','📅','📆',
      '🗑️',
    ],
  },
  {
    name: 'Símbolos',
    icon: '✅',
    emojis: [
      '✅','❌','❓','❗','⚠️','🔴','🟠','🟡','🟢','🔵','🟣','⚫','⚪','🟤','▶️',
      '⏩','⏪','⏫','⏬','⏭️','⏮️','⏸️','⏹️','⏺️','🔁','🔂','🔀','🔃','🔄','🔙',
      '🔚','🔛','🔜','🔝','🔰','♻️','✔️','💯','⛔','🚫','📵','🔇','✨','🎉','🎊',
      '🎈','🎀','🎁','🏮','🌟','⭐','💫','✴️','🌈','🎇','🎆','💬','💭',
    ],
  },
];

@Component({
  selector: 'app-emoji-picker',
  imports: [FormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="ep">
      <div class="ep__tabs">
        @for (cat of CATEGORIES; track cat.name; let i = $index) {
          <button
            class="ep__tab"
            [class.ep__tab--active]="activeTab() === i"
            [title]="cat.name"
            (click)="activeTab.set(i)">
            {{ cat.icon }}
          </button>
        }
      </div>
      <div class="ep__search">
        <input
          class="ep__search-input"
          placeholder="Buscar emoji..."
          [ngModel]="searchQuery()"
          (ngModelChange)="searchQuery.set($event)"
        />
      </div>
      <div class="ep__grid">
        @for (emoji of visibleEmojis(); track emoji) {
          <button class="ep__emoji" (click)="pick(emoji)" [title]="emoji">
            {{ emoji }}
          </button>
        }
        @if (visibleEmojis().length === 0) {
          <span class="ep__empty">Sin resultados</span>
        }
      </div>
    </div>
  `,
  styles: [`
    :host {
      display: block;
    }

    .ep {
      width: 320px;
      background: var(--sc-surface-card, #fff);
      border: 1px solid var(--sc-surface-border, #e2e8f0);
      border-radius: var(--sc-radius, 10px);
      box-shadow: 0 -4px 24px rgba(0, 0, 0, 0.15);
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .ep__tabs {
      display: flex;
      gap: 2px;
      padding: 6px 8px 4px;
      border-bottom: 1px solid var(--sc-surface-border, #e2e8f0);
      overflow-x: auto;
      scrollbar-width: none;

      &::-webkit-scrollbar { display: none; }
    }

    .ep__tab {
      flex-shrink: 0;
      width: 32px;
      height: 32px;
      border: none;
      background: none;
      cursor: pointer;
      border-radius: 6px;
      font-size: 1.1rem;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background 0.1s;

      &:hover {
        background: var(--sc-surface-hover, rgba(0, 0, 0, 0.06));
      }

      &--active {
        background: var(--sc-primary-50, rgba(21, 101, 192, 0.1));
      }
    }

    .ep__search {
      padding: 6px 8px;
      border-bottom: 1px solid var(--sc-surface-border, #e2e8f0);
    }

    .ep__search-input {
      width: 100%;
      box-sizing: border-box;
      border: 1px solid var(--sc-surface-border, #e2e8f0);
      border-radius: 6px;
      padding: 5px 10px;
      font-size: 0.85rem;
      background: var(--sc-surface-ground, #f0f2f5);
      color: var(--sc-text-color, #1a202c);
      outline: none;

      &::placeholder { color: var(--sc-text-muted, #718096); }
      &:focus { border-color: var(--sc-primary, #1565c0); }
    }

    .ep__grid {
      display: grid;
      grid-template-columns: repeat(8, 1fr);
      gap: 2px;
      padding: 6px 8px 8px;
      max-height: 240px;
      overflow-y: auto;
      scrollbar-width: thin;
    }

    .ep__emoji {
      width: 34px;
      height: 34px;
      border: none;
      background: none;
      cursor: pointer;
      border-radius: 6px;
      font-size: 1.1rem;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background 0.1s;

      &:hover {
        background: var(--sc-surface-hover, rgba(0, 0, 0, 0.06));
        transform: scale(1.15);
      }
    }

    .ep__empty {
      grid-column: 1 / -1;
      text-align: center;
      padding: 16px;
      color: var(--sc-text-muted, #718096);
      font-size: 0.85rem;
    }
  `],
})
export class EmojiPickerComponent {
  protected readonly CATEGORIES = CATEGORIES;

  readonly emojiSelect = output<string>();

  readonly activeTab = signal(0);
  readonly searchQuery = signal('');

  readonly visibleEmojis = computed(() => {
    const q = this.searchQuery().trim().toLowerCase();
    if (q) {
      return CATEGORIES.flatMap(c => c.emojis).filter(e =>
        e.includes(q)
      );
    }
    return CATEGORIES[this.activeTab()]?.emojis ?? [];
  });

  pick(emoji: string): void {
    this.emojiSelect.emit(emoji);
  }
}
