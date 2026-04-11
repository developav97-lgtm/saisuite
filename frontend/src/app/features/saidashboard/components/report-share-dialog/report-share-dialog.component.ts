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
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatListModule } from '@angular/material/list';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { ReportBIService } from '../../services/report-bi.service';
import { ReportBIShare } from '../../models/report-bi.model';
import { ToastService } from '../../../../core/services/toast.service';

export interface ReportShareDialogData {
  reportId: string;
  reportTitle: string;
  existingShares: ReportBIShare[];
  currentUserId: string;
}

@Component({
  selector: 'app-report-share-dialog',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    FormsModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    MatFormFieldModule,
    MatSelectModule,
    MatSlideToggleModule,
    MatListModule,
    MatProgressBarModule,
    MatTooltipModule,
  ],
  template: `
    <h2 mat-dialog-title>Compartir "{{ data.reportTitle }}"</h2>

    @if (loading()) {
      <mat-progress-bar mode="indeterminate"></mat-progress-bar>
    }

    <mat-dialog-content>
      <!-- Add new share -->
      <div class="share-form">
        <mat-form-field appearance="outline" class="share-form__select">
          <mat-label>Seleccionar usuario</mat-label>
          <mat-select [(ngModel)]="selectedUserId">
            @for (user of availableUsers(); track user.id) {
              <mat-option [value]="user.id">
                {{ user.full_name || user.email }}
              </mat-option>
            }
          </mat-select>
        </mat-form-field>

        <mat-slide-toggle [(ngModel)]="puedeEditar" class="share-form__toggle">
          Puede editar
        </mat-slide-toggle>

        <button mat-flat-button color="primary"
                [disabled]="!selectedUserId"
                (click)="addShare()">
          <mat-icon>person_add</mat-icon>
          Compartir
        </button>
      </div>

      <!-- Existing shares -->
      @if (shares().length > 0) {
        <h3 class="share-list__title">Compartido con</h3>
        <mat-list class="share-list">
          @for (share of shares(); track share.user_id) {
            <mat-list-item>
              <mat-icon matListItemIcon>person</mat-icon>
              <div matListItemTitle>{{ share.full_name || share.email }}</div>
              <div matListItemLine>
                {{ share.puede_editar ? 'Lectura y edición' : 'Solo lectura' }}
              </div>
              <button mat-icon-button matListItemMeta
                      matTooltip="Revocar acceso"
                      (click)="revokeShare(share.user_id)">
                <mat-icon color="warn">close</mat-icon>
              </button>
            </mat-list-item>
          }
        </mat-list>
      } @else {
        <p class="share-list__empty">Este reporte no se ha compartido con nadie.</p>
      }
    </mat-dialog-content>

    <mat-dialog-actions align="end">
      <button mat-button mat-dialog-close>Cerrar</button>
    </mat-dialog-actions>
  `,
  styles: [`
    .share-form {
      display: flex;
      align-items: center;
      gap: 16px;
      margin-bottom: 16px;
      flex-wrap: wrap;
    }
    .share-form__select {
      flex: 1;
      min-width: 200px;
    }
    .share-form__toggle {
      font-size: 14px;
    }
    .share-list__title {
      font-size: 14px;
      font-weight: 500;
      margin: 16px 0 8px;
      color: var(--sc-text-secondary, rgba(0, 0, 0, 0.6));
    }
    .share-list__empty {
      text-align: center;
      color: var(--sc-text-secondary, rgba(0, 0, 0, 0.6));
      padding: 24px 0;
    }
  `],
})
export class ReportShareDialogComponent implements OnInit {
  readonly data = inject<ReportShareDialogData>(MAT_DIALOG_DATA);
  private readonly dialogRef = inject(MatDialogRef<ReportShareDialogComponent>);
  private readonly reportBIService = inject(ReportBIService);
  private readonly toast = inject(ToastService);
  private readonly destroyRef = inject(DestroyRef);

  readonly loading = signal(false);
  readonly allUsers = signal<{ id: string; email: string; full_name: string }[]>([]);
  readonly shares = signal<ReportBIShare[]>([]);

  selectedUserId = '';
  puedeEditar = false;

  readonly availableUsers = computed(() => {
    const sharedIds = new Set(this.shares().map(s => s.user_id));
    sharedIds.add(this.data.currentUserId);
    return this.allUsers().filter(u => !sharedIds.has(u.id));
  });

  ngOnInit(): void {
    this.shares.set([...this.data.existingShares]);
    this.loading.set(true);

    this.reportBIService.getCompanyUsers()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: users => {
          this.allUsers.set(users);
          this.loading.set(false);
        },
        error: () => {
          this.toast.error('No se pudieron cargar los usuarios.');
          this.loading.set(false);
        },
      });
  }

  addShare(): void {
    if (!this.selectedUserId) return;
    this.loading.set(true);

    this.reportBIService.share(this.data.reportId, {
      user_id: this.selectedUserId,
      puede_editar: this.puedeEditar,
    })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: newShare => {
          this.shares.update(list => [...list, newShare]);
          this.selectedUserId = '';
          this.puedeEditar = false;
          this.loading.set(false);
          this.toast.success('Reporte compartido correctamente.');
        },
        error: () => {
          this.loading.set(false);
          this.toast.error('No se pudo compartir el reporte.');
        },
      });
  }

  revokeShare(userId: string): void {
    this.loading.set(true);

    this.reportBIService.revokeShare(this.data.reportId, userId)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.shares.update(list => list.filter(s => s.user_id !== userId));
          this.loading.set(false);
          this.toast.success('Acceso revocado.');
        },
        error: () => {
          this.loading.set(false);
          this.toast.error('No se pudo revocar el acceso.');
        },
      });
  }
}
