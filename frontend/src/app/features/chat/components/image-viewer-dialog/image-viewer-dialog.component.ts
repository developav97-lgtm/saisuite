import { ChangeDetectionStrategy, Component, inject, signal, computed } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';

export interface ImageViewerData {
  /** All image URLs (original full-res) in the conversation, in display order. */
  images: string[];
  /** Index of the image the user clicked. */
  initialIndex: number;
}

@Component({
  selector: 'app-image-viewer-dialog',
  imports: [MatDialogModule, MatButtonModule, MatIconModule, MatTooltipModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="viewer">
      <div class="viewer__toolbar">
        <span class="viewer__counter">{{ currentIndex() + 1 }} / {{ data.images.length }}</span>
        <span class="viewer__spacer"></span>
        <a [href]="currentImage()"
           download
           mat-icon-button
           matTooltip="Descargar imagen original">
          <mat-icon>download</mat-icon>
        </a>
        <button mat-icon-button matTooltip="Cerrar" (click)="close()">
          <mat-icon>close</mat-icon>
        </button>
      </div>

      <div class="viewer__stage">
        @if (hasPrev()) {
          <button class="viewer__nav viewer__nav--prev"
                  mat-icon-button
                  matTooltip="Anterior"
                  (click)="prev()">
            <mat-icon>chevron_left</mat-icon>
          </button>
        }

        <div class="viewer__image-wrap">
          <img class="viewer__image"
               [src]="currentImage()"
               [alt]="'Imagen ' + (currentIndex() + 1)"
               (load)="onImageLoad()" />
          @if (loading()) {
            <div class="viewer__loading">
              <mat-icon class="viewer__spinner">hourglass_empty</mat-icon>
            </div>
          }
        </div>

        @if (hasNext()) {
          <button class="viewer__nav viewer__nav--next"
                  mat-icon-button
                  matTooltip="Siguiente"
                  (click)="next()">
            <mat-icon>chevron_right</mat-icon>
          </button>
        }
      </div>
    </div>
  `,
  styles: [`
    .viewer {
      display: flex;
      flex-direction: column;
      height: 90vh;
      width: 90vw;
      max-width: 1200px;
      background: #000;
      color: #fff;
    }

    .viewer__toolbar {
      display: flex;
      align-items: center;
      padding: 8px 16px;
      gap: 8px;
      background: rgba(0, 0, 0, 0.8);
      flex-shrink: 0;
    }

    .viewer__counter {
      font-size: 0.9rem;
      opacity: 0.8;
    }

    .viewer__spacer { flex: 1; }

    .viewer__stage {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      overflow: hidden;
    }

    .viewer__image-wrap {
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
      width: 100%;
      height: 100%;
    }

    .viewer__image {
      max-width: 100%;
      max-height: 100%;
      object-fit: contain;
    }

    .viewer__loading {
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(0, 0, 0, 0.5);
    }

    @keyframes spin { to { transform: rotate(360deg); } }
    .viewer__spinner { animation: spin 1s linear infinite; }

    .viewer__nav {
      position: absolute;
      z-index: 10;
      background: rgba(255, 255, 255, 0.15) !important;
      color: #fff !important;

      &--prev { left: 16px; }
      &--next { right: 16px; }

      &:hover { background: rgba(255, 255, 255, 0.3) !important; }
    }
  `],
})
export class ImageViewerDialogComponent {
  readonly data: ImageViewerData = inject(MAT_DIALOG_DATA);
  private readonly dialogRef = inject(MatDialogRef<ImageViewerDialogComponent>);

  readonly currentIndex = signal(this.data.initialIndex);
  readonly loading = signal(true);

  readonly currentImage = computed(() => this.data.images[this.currentIndex()]);
  readonly hasPrev = computed(() => this.currentIndex() > 0);
  readonly hasNext = computed(() => this.currentIndex() < this.data.images.length - 1);

  prev(): void {
    if (this.hasPrev()) {
      this.loading.set(true);
      this.currentIndex.update(i => i - 1);
    }
  }

  next(): void {
    if (this.hasNext()) {
      this.loading.set(true);
      this.currentIndex.update(i => i + 1);
    }
  }

  onImageLoad(): void {
    this.loading.set(false);
  }

  close(): void {
    this.dialogRef.close();
  }
}
