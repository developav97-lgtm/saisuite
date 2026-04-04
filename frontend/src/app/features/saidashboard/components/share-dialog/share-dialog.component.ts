import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDividerModule } from '@angular/material/divider';
import { DashboardService } from '../../services/dashboard.service';
import { DashboardShare } from '../../models/dashboard.model';
import { AdminService } from '../../../admin/services/admin.service';
import { AdminUser } from '../../../admin/models/admin.models';
import { ToastService } from '../../../../core/services/toast.service';

export interface ShareDialogData {
  dashboardId: string;
  dashboardTitle: string;
  currentShares: DashboardShare[];
}

@Component({
  selector: 'app-share-dialog',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    MatFormFieldModule,
    MatSelectModule,
    MatSlideToggleModule,
    MatTooltipModule,
    MatProgressSpinnerModule,
    MatDividerModule,
  ],
  templateUrl: './share-dialog.component.html',
  styleUrl: './share-dialog.component.scss',
})
export class ShareDialogComponent implements OnInit {
  private readonly dashboardService = inject(DashboardService);
  private readonly adminService = inject(AdminService);
  private readonly dialogRef = inject(MatDialogRef<ShareDialogComponent>);
  private readonly data = inject<ShareDialogData>(MAT_DIALOG_DATA);
  private readonly toast = inject(ToastService);
  private readonly destroyRef = inject(DestroyRef);

  readonly dashboardTitle = this.data.dashboardTitle;
  readonly shares = signal<DashboardShare[]>([...this.data.currentShares]);
  readonly users = signal<AdminUser[]>([]);
  readonly selectedUserId = signal<string | null>(null);
  readonly canEdit = signal(false);
  readonly saving = signal(false);

  ngOnInit(): void {
    this.adminService.listUsers()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => this.users.set(res.results),
      });
  }

  shareWith(): void {
    const userId = this.selectedUserId();
    if (!userId) return;

    this.saving.set(true);
    this.dashboardService.share(this.data.dashboardId, {
      user_id: userId,
      puede_editar: this.canEdit(),
    })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: share => {
          this.shares.update(s => [...s, share]);
          this.selectedUserId.set(null);
          this.canEdit.set(false);
          this.saving.set(false);
          this.toast.success('Dashboard compartido correctamente.');
        },
        error: () => {
          this.saving.set(false);
          this.toast.error('Error al compartir el dashboard.');
        },
      });
  }

  revokeShare(userId: string): void {
    this.dashboardService.revokeShare(this.data.dashboardId, userId)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.shares.update(s => s.filter(sh => sh.user_id !== userId));
          this.toast.success('Acceso revocado.');
        },
        error: () => this.toast.error('Error al revocar acceso.'),
      });
  }

  isAlreadyShared(userId: string): boolean {
    return this.shares().some(s => s.user_id === userId);
  }

  close(): void {
    this.dialogRef.close(this.shares());
  }
}
