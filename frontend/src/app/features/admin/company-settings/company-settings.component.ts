import {
  ChangeDetectionStrategy, Component, OnInit, inject, signal, ElementRef, ViewChild,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatButtonModule } from '@angular/material/button';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatTabsModule } from '@angular/material/tabs';
import { MatDialog } from '@angular/material/dialog';
import { MatChipsModule } from '@angular/material/chips';
import { AdminService } from '../services/admin.service';
import { AgentTokenInfo, CompanyLicense, CompanySettings, LICENSE_STATUS_LABELS, MODULE_ICONS, MODULE_LABELS } from '../models/admin.models';
import { LicensePackage, LicenseRequest, LICENSE_REQUEST_TYPE_LABELS, LICENSE_REQUEST_STATUS_LABELS } from '../models/tenant.model';
import { ToastService } from '../../../core/services/toast.service';
import { LicenseRequestDialogComponent } from './license-request-dialog/license-request-dialog.component';

const ALLOWED_TYPES = ['image/png', 'image/jpeg', 'image/webp', 'image/gif'];
const MAX_SIZE_MB = 2;

@Component({
  selector: 'app-company-settings',
  templateUrl: './company-settings.component.html',
  styleUrl: './company-settings.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    MatIconModule,
    MatProgressBarModule,
    MatButtonModule,
    MatTooltipModule,
    MatTabsModule,
    MatChipsModule,
  ],
})
export class CompanySettingsComponent implements OnInit {
  private readonly adminService = inject(AdminService);
  private readonly toast        = inject(ToastService);
  private readonly dialog       = inject(MatDialog);

  @ViewChild('fileInput') fileInput!: ElementRef<HTMLInputElement>;

  readonly company            = signal<CompanySettings | null>(null);
  readonly license            = signal<CompanyLicense | null>(null);
  readonly aiUsage            = signal<{ messages_used: number; tokens_used: number; tokens_quota: number; tokens_pct: number; total_requests: number } | null>(null);
  readonly loading            = signal(false);
  readonly uploading          = signal(false);
  readonly logoPreview        = signal<string | null>(null);
  readonly agentTokens        = signal<AgentTokenInfo[]>([]);
  readonly loadingTokens      = signal(false);
  readonly myRequests         = signal<LicenseRequest[]>([]);
  readonly loadingRequests    = signal(false);
  readonly availablePackages  = signal<LicensePackage[]>([]);
  readonly submittingRequest  = signal(false);

  readonly moduleLabels            = MODULE_LABELS;
  readonly moduleIcons             = MODULE_ICONS;
  readonly licenseStatusLabels     = LICENSE_STATUS_LABELS;
  readonly requestTypeLabels       = LICENSE_REQUEST_TYPE_LABELS;
  readonly requestStatusLabels     = LICENSE_REQUEST_STATUS_LABELS;

  ngOnInit(): void {
    this.loading.set(true);
    this.adminService.getCompanySettings().subscribe({
      next: (data) => { this.company.set(data); this.loading.set(false); },
      error: ()     => { this.loading.set(false); },
    });
    this.adminService.getMyLicense().subscribe({
      next: (lic) => this.license.set(lic),
      error: () => {},
    });
    this.adminService.getMyAIUsage().subscribe({
      next: (usage) => this.aiUsage.set(usage),
      error: () => {},
    });
    this.loadIntegrationTokens();
    this.loadMyRequests();
    this.loadAvailablePackages();
  }

  loadIntegrationTokens(): void {
    this.loadingTokens.set(true);
    this.adminService.getMyAgentTokens().subscribe({
      next: (tokens) => { this.agentTokens.set(tokens); this.loadingTokens.set(false); },
      error: ()       => { this.loadingTokens.set(false); },
    });
  }

  loadMyRequests(): void {
    this.loadingRequests.set(true);
    this.adminService.getMyLicenseRequests().subscribe({
      next: (reqs) => { this.myRequests.set(reqs); this.loadingRequests.set(false); },
      error: ()     => { this.loadingRequests.set(false); },
    });
  }

  loadAvailablePackages(): void {
    this.adminService.getAvailablePackages().subscribe({
      next: (pkgs) => this.availablePackages.set(pkgs),
      error: () => {},
    });
  }

  openRequestDialog(requestType: 'user_seats' | 'module' | 'ai_tokens'): void {
    const packages = this.availablePackages().filter(p => p.package_type === requestType);
    if (packages.length === 0) {
      this.toast.error('No hay paquetes disponibles para este tipo de solicitud.');
      return;
    }

    const ref = this.dialog.open(LicenseRequestDialogComponent, {
      width: '480px',
      data: { requestType, packages },
    });

    ref.afterClosed().subscribe((result: { packageId: string; notes: string } | undefined) => {
      if (!result) return;
      this.submittingRequest.set(true);
      this.adminService.createLicenseRequest({
        package_id:   result.packageId,
        request_type: requestType,
        notes:        result.notes,
      }).subscribe({
        next: (req) => {
          this.myRequests.update(reqs => [req, ...reqs]);
          this.submittingRequest.set(false);
          this.toast.success('Solicitud enviada. El equipo de ValMen Tech la revisará pronto.');
        },
        error: (err) => {
          const msg = err?.error?.detail ?? err?.error?.[0] ?? 'No se pudo enviar la solicitud.';
          this.toast.error(msg);
          this.submittingRequest.set(false);
        },
      });
    });
  }

  copyToClipboard(value: string, label: string): void {
    navigator.clipboard.writeText(value).then(() => {
      this.toast.success(`${label} copiado al portapapeles.`);
    });
  }

  triggerFilePicker(): void {
    this.fileInput.nativeElement.click();
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file  = input.files?.[0];
    if (!file) return;

    if (!ALLOWED_TYPES.includes(file.type)) {
      this.toast.error('Formato no soportado. Use PNG, JPG, WebP o GIF.');
      return;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      this.toast.error(`El archivo supera el límite de ${MAX_SIZE_MB} MB.`);
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => this.logoPreview.set(e.target?.result as string);
    reader.readAsDataURL(file);

    this.uploading.set(true);
    this.adminService.uploadLogo(file).subscribe({
      next: (updated) => {
        this.company.set(updated);
        this.uploading.set(false);
        this.toast.success('Logo actualizado correctamente.');
        input.value = '';
      },
      error: () => {
        this.logoPreview.set(null);
        this.uploading.set(false);
        this.toast.error('No se pudo subir el logo. Intente nuevamente.');
        input.value = '';
      },
    });
  }

  deleteLogo(): void {
    this.uploading.set(true);
    this.adminService.deleteLogo().subscribe({
      next: () => {
        const current = this.company();
        if (current) this.company.set({ ...current, logo: null });
        this.logoPreview.set(null);
        this.uploading.set(false);
        this.toast.success('Logo eliminado.');
      },
      error: () => {
        this.uploading.set(false);
        this.toast.error('No se pudo eliminar el logo.');
      },
    });
  }

  get currentLogoUrl(): string | null {
    return this.logoPreview() ?? this.company()?.logo ?? null;
  }
}
