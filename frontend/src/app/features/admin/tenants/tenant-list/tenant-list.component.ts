import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule, DatePipe } from '@angular/common';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { FormsModule } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { TenantService } from '../../services/tenant.service';
import { ToastService } from '../../../../core/services/toast.service';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { Tenant, LICENSE_STATUS_LABELS, PLAN_LABELS } from '../../models/tenant.model';

@Component({
  selector: 'app-tenant-list',
  templateUrl: './tenant-list.component.html',
  styleUrl: './tenant-list.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, FormsModule, DatePipe,
    MatTableModule, MatButtonModule, MatIconModule,
    MatProgressBarModule, MatChipsModule, MatTooltipModule,
    MatInputModule, MatFormFieldModule,
  ],
})
export class TenantListComponent implements OnInit {
  private readonly tenantService = inject(TenantService);
  private readonly router        = inject(Router);
  private readonly dialog        = inject(MatDialog);
  private readonly toast         = inject(ToastService);

  readonly loading  = signal(false);
  readonly tenants  = signal<Tenant[]>([]);
  readonly search   = signal('');

  readonly columns = ['name', 'nit', 'plan', 'license', 'vencimiento', 'usuarios', 'acciones'];

  readonly STATUS_LABELS = LICENSE_STATUS_LABELS;
  readonly PLAN_LABELS   = PLAN_LABELS;

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.tenantService.listTenants().subscribe({
      next: list => {
        this.tenants.set(list);
        this.loading.set(false);
      },
      error: () => {
        this.toast.error('Error al cargar empresas');
        this.loading.set(false);
      },
    });
  }

  get filtered(): Tenant[] {
    const q = this.search().toLowerCase();
    if (!q) return this.tenants();
    return this.tenants().filter(t =>
      t.name.toLowerCase().includes(q) || t.nit.includes(q)
    );
  }

  getLicenseColor(t: Tenant): string {
    const status = t.license?.status;
    if (!status || status === 'expired' || status === 'suspended') return 'warn';
    if (status === 'trial') return 'accent';
    return 'primary';
  }

  getLicenseLabel(t: Tenant): string {
    if (!t.license) return 'Sin licencia';
    return this.STATUS_LABELS[t.license.status] ?? t.license.status;
  }

  getLicenseDaysClass(t: Tenant): string {
    const days = t.license?.days_until_expiry ?? 0;
    if (days <= 7)  return 'days-critical';
    if (days <= 30) return 'days-warning';
    return '';
  }

  crear(): void {
    this.router.navigate(['/admin/tenants/nuevo']);
  }

  editar(t: Tenant): void {
    this.router.navigate(['/admin/tenants', t.id]);
  }

  toggleActive(t: Tenant): void {
    const action = t.is_active ? 'desactivar' : 'activar';
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        title: `${action.charAt(0).toUpperCase() + action.slice(1)} empresa`,
        message: `¿Deseas ${action} la empresa "${t.name}"?`,
        confirmText: action.charAt(0).toUpperCase() + action.slice(1),
        confirmColor: t.is_active ? 'warn' : 'primary',
      },
    });
    ref.afterClosed().subscribe(confirmed => {
      if (!confirmed) return;
      this.tenantService.setTenantActive(t.id, !t.is_active).subscribe({
        next: () => {
          this.toast.success(`Empresa ${action}da correctamente`);
          this.load();
        },
        error: () => this.toast.error(`Error al ${action} empresa`),
      });
    });
  }
}
