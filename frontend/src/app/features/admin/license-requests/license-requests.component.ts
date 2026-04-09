import { ChangeDetectionStrategy, Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatChipsModule } from '@angular/material/chips';
import { MatTabsModule } from '@angular/material/tabs';
import { MatDialog } from '@angular/material/dialog';
import { AdminService } from '../services/admin.service';
import { ToastService } from '../../../core/services/toast.service';
import { ConfirmDialogComponent } from '../../../shared/components/confirm-dialog/confirm-dialog.component';
import {
  LicenseRequest, LicenseRequestStatus,
  LICENSE_REQUEST_TYPE_LABELS, LICENSE_REQUEST_STATUS_LABELS,
} from '../models/tenant.model';
import { ReviewDialogComponent } from './review-dialog/review-dialog.component';

@Component({
  selector: 'app-license-requests',
  templateUrl: './license-requests.component.html',
  styleUrl: './license-requests.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    MatIconModule,
    MatButtonModule,
    MatProgressBarModule,
    MatTooltipModule,
    MatChipsModule,
    MatTabsModule,
  ],
})
export class LicenseRequestsComponent implements OnInit {
  private readonly adminService = inject(AdminService);
  private readonly toast        = inject(ToastService);
  private readonly dialog       = inject(MatDialog);

  readonly allRequests   = signal<LicenseRequest[]>([]);
  readonly loading       = signal(false);
  readonly processingId  = signal<string | null>(null);

  readonly typeLabels   = LICENSE_REQUEST_TYPE_LABELS;
  readonly statusLabels = LICENSE_REQUEST_STATUS_LABELS;

  readonly pending  = computed(() => this.allRequests().filter(r => r.status === 'pending'));
  readonly resolved = computed(() => this.allRequests().filter(r => r.status !== 'pending'));

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.adminService.getAdminLicenseRequests().subscribe({
      next: (reqs) => { this.allRequests.set(reqs); this.loading.set(false); },
      error: ()     => { this.loading.set(false); },
    });
  }

  approve(req: LicenseRequest): void {
    const ref = this.dialog.open(ReviewDialogComponent, {
      width: '420px',
      data: { action: 'approve', companyName: req.company_name, packageName: req.package?.name },
    });

    ref.afterClosed().subscribe((reviewNotes: string | undefined) => {
      if (reviewNotes === undefined) return;
      this.processingId.set(req.id);
      this.adminService.approveLicenseRequest(req.id, reviewNotes).subscribe({
        next: (updated) => {
          this.allRequests.update(reqs => reqs.map(r => r.id === updated.id ? updated : r));
          this.processingId.set(null);
          this.toast.success(`Solicitud de ${req.company_name} aprobada.`);
        },
        error: (err) => {
          const msg = err?.error?.detail ?? 'No se pudo aprobar la solicitud.';
          this.toast.error(msg);
          this.processingId.set(null);
        },
      });
    });
  }

  reject(req: LicenseRequest): void {
    const ref = this.dialog.open(ReviewDialogComponent, {
      width: '420px',
      data: { action: 'reject', companyName: req.company_name, packageName: req.package?.name },
    });

    ref.afterClosed().subscribe((reviewNotes: string | undefined) => {
      if (reviewNotes === undefined) return;
      this.processingId.set(req.id);
      this.adminService.rejectLicenseRequest(req.id, reviewNotes).subscribe({
        next: (updated) => {
          this.allRequests.update(reqs => reqs.map(r => r.id === updated.id ? updated : r));
          this.processingId.set(null);
          this.toast.success(`Solicitud de ${req.company_name} rechazada.`);
        },
        error: (err) => {
          const msg = err?.error?.detail ?? 'No se pudo rechazar la solicitud.';
          this.toast.error(msg);
          this.processingId.set(null);
        },
      });
    });
  }
}
