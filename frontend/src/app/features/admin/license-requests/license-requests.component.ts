import {
  AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  OnInit,
  ViewChild,
  effect,
  inject,
  signal,
  computed,
} from '@angular/core';
import { DatePipe, DecimalPipe } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTableModule, MatTableDataSource } from '@angular/material/table';
import { MatPaginator, MatPaginatorModule } from '@angular/material/paginator';
import { MatDialog } from '@angular/material/dialog';
import { AdminService } from '../services/admin.service';
import { ToastService } from '../../../core/services/toast.service';
import {
  LicenseRequest,
  LICENSE_REQUEST_TYPE_LABELS,
  LICENSE_REQUEST_STATUS_LABELS,
} from '../models/tenant.model';
import { ReviewDialogComponent } from './review-dialog/review-dialog.component';

@Component({
  selector: 'app-license-requests',
  templateUrl: './license-requests.component.html',
  styleUrl: './license-requests.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DatePipe,
    DecimalPipe,
    MatIconModule,
    MatButtonModule,
    MatProgressBarModule,
    MatTooltipModule,
    MatTabsModule,
    MatTableModule,
    MatPaginatorModule,
  ],
})
export class LicenseRequestsComponent implements OnInit, AfterViewInit {
  private readonly adminService = inject(AdminService);
  private readonly toast        = inject(ToastService);
  private readonly dialog       = inject(MatDialog);

  readonly allRequests   = signal<LicenseRequest[]>([]);
  readonly loading       = signal(false);
  readonly processingId  = signal<string | null>(null);

  typeLabel(req: LicenseRequest): string {
    return LICENSE_REQUEST_TYPE_LABELS[req.request_type];
  }

  statusLabel(req: LicenseRequest): string {
    return LICENSE_REQUEST_STATUS_LABELS[req.status];
  }

  readonly pending  = computed(() => this.allRequests().filter(r => r.status === 'pending'));
  readonly resolved = computed(() => this.allRequests().filter(r => r.status !== 'pending'));

  readonly pendingEmpty  = computed(() => !this.loading() && this.pending().length === 0);
  readonly resolvedEmpty = computed(() => !this.loading() && this.resolved().length === 0);

  readonly pendingColumns  = ['company', 'type', 'package', 'price', 'requester', 'date', 'actions'];
  readonly resolvedColumns = ['company', 'type', 'package', 'status', 'reviewer', 'date'];

  readonly pendingSource  = new MatTableDataSource<LicenseRequest>([]);
  readonly resolvedSource = new MatTableDataSource<LicenseRequest>([]);

  readonly pageSizeOptions = [10, 25, 50];

  @ViewChild('pendingPaginator') pendingPaginator?: MatPaginator;
  @ViewChild('resolvedPaginator') resolvedPaginator?: MatPaginator;

  constructor() {
    effect(() => { this.pendingSource.data  = this.pending();  });
    effect(() => { this.resolvedSource.data = this.resolved(); });
  }

  ngOnInit(): void {
    this.load();
  }

  ngAfterViewInit(): void {
    if (this.pendingPaginator)  this.pendingSource.paginator  = this.pendingPaginator;
    if (this.resolvedPaginator) this.resolvedSource.paginator = this.resolvedPaginator;
  }

  load(): void {
    this.loading.set(true);
    this.adminService.getAdminLicenseRequests().subscribe({
      next: (reqs) => {
        this.allRequests.set(reqs);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.toast.error('No se pudieron cargar las solicitudes. Intenta nuevamente.');
      },
    });
  }

  approve(req: LicenseRequest): void {
    const ref = this.dialog.open(ReviewDialogComponent, {
      width: '420px',
      data: { action: 'approve', companyName: req.company_name, packageName: req.package.name },
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
      data: { action: 'reject', companyName: req.company_name, packageName: req.package.name },
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
