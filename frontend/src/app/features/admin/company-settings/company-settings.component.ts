import {
  ChangeDetectionStrategy, Component, OnInit, inject, signal, ElementRef, ViewChild,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatButtonModule } from '@angular/material/button';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatTabsModule } from '@angular/material/tabs';
import { AdminService } from '../services/admin.service';
import { AgentTokenInfo, CompanyLicense, CompanySettings, LICENSE_STATUS_LABELS, MODULE_LABELS } from '../models/admin.models';
import { ToastService } from '../../../core/services/toast.service';

const PLAN_LABELS: Record<string, string | undefined> = {
  starter:      'Starter',
  professional: 'Professional',
  enterprise:   'Enterprise',
};

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
  ],
})
export class CompanySettingsComponent implements OnInit {
  private readonly adminService = inject(AdminService);
  private readonly toast        = inject(ToastService);

  @ViewChild('fileInput') fileInput!: ElementRef<HTMLInputElement>;

  readonly company      = signal<CompanySettings | null>(null);
  readonly license      = signal<CompanyLicense | null>(null);
  readonly loading      = signal(false);
  readonly uploading    = signal(false);
  readonly logoPreview  = signal<string | null>(null);
  readonly agentTokens  = signal<AgentTokenInfo[]>([]);
  readonly loadingTokens = signal(false);

  readonly planLabels          = PLAN_LABELS;
  readonly moduleLabels        = MODULE_LABELS;
  readonly licenseStatusLabels = LICENSE_STATUS_LABELS;

  ngOnInit(): void {
    this.loading.set(true);
    this.adminService.getCompanySettings().subscribe({
      next: (data) => { this.company.set(data); this.loading.set(false); },
      error: ()     => { this.loading.set(false); },
    });
    this.adminService.getMyLicense().subscribe({
      next: (lic) => this.license.set(lic),
      error: () => { /* silencioso si no tiene licencia configurada */ },
    });
    this.loadIntegrationTokens();
  }

  loadIntegrationTokens(): void {
    this.loadingTokens.set(true);
    this.adminService.getMyAgentTokens().subscribe({
      next: (tokens) => { this.agentTokens.set(tokens); this.loadingTokens.set(false); },
      error: ()       => { this.loadingTokens.set(false); },
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

    // Mostrar preview local inmediato
    const reader = new FileReader();
    reader.onload = (e) => this.logoPreview.set(e.target?.result as string);
    reader.readAsDataURL(file);

    this.uploading.set(true);
    this.adminService.uploadLogo(file).subscribe({
      next: (updated) => {
        this.company.set(updated);
        this.uploading.set(false);
        this.toast.success('Logo actualizado correctamente.');
        // Limpiar input para permitir re-subir mismo archivo
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
