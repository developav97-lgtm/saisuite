import {
  ChangeDetectionStrategy, Component, OnInit, inject, signal, computed,
} from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { CommonModule, DatePipe } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators, FormGroup } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTableModule } from '@angular/material/table';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDividerModule } from '@angular/material/divider';
import { MatDialog } from '@angular/material/dialog';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { TenantService } from '../../services/tenant.service';
import { PackageService } from '../../services/package.service';
import { ToastService } from '../../../../core/services/toast.service';
import { NavigationHistoryService } from '../../../../core/services/navigation-history.service';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import {
  Tenant, TenantLicense, LicenseHistory, LicenseRenewal,
  LICENSE_STATUS_LABELS, PLAN_LABELS, MODULE_LABELS,
  LICENSE_PERIOD_LABELS, LICENSE_PERIOD_DAYS, LicensePeriod,
  LicensePackage, LicensePackageItem, MonthlyLicenseSnapshot,
  AIUsageSummary, AIUsagePerUser, PACKAGE_TYPE_LABELS, AgentTokenInfo,
} from '../../models/tenant.model';

const AVAILABLE_MODULES = ['proyectos', 'crm', 'soporte', 'dashboard'];

/** Convierte 'YYYY-MM-DD' a Date local (sin desfase de zona horaria). */
function strToDate(s: string): Date | null {
  if (!s) return null;
  const [y, m, d] = s.split('-').map(Number);
  return new Date(y, m - 1, d);
}

/** Convierte Date a 'YYYY-MM-DD'. */
function dateToStr(d: Date | null): string {
  if (!d) return '';
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

@Component({
  selector: 'app-tenant-form',
  templateUrl: './tenant-form.component.html',
  styleUrl: './tenant-form.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, ReactiveFormsModule, DatePipe,
    MatButtonModule, MatIconModule, MatInputModule,
    MatFormFieldModule, MatSelectModule, MatCheckboxModule,
    MatProgressBarModule, MatTabsModule, MatTableModule,
    MatChipsModule, MatTooltipModule, MatDividerModule,
    MatDatepickerModule, MatNativeDateModule, MatSlideToggleModule,
  ],
})
export class TenantFormComponent implements OnInit {
  private readonly route          = inject(ActivatedRoute);
  private readonly router         = inject(Router);
  private readonly fb             = inject(FormBuilder);
  private readonly tenantService  = inject(TenantService);
  private readonly packageService = inject(PackageService);
  private readonly toast          = inject(ToastService);
  private readonly navHistory     = inject(NavigationHistoryService);
  private readonly dialog         = inject(MatDialog);

  readonly loading  = signal(false);
  readonly saving   = signal(false);
  readonly tenantId = signal<string | null>(null);
  readonly tenant   = signal<Tenant | null>(null);
  readonly license  = signal<TenantLicense | null>(null);
  readonly history  = signal<LicenseHistory[]>([]);

  readonly pendingRenewal      = signal<LicenseRenewal | null>(null);
  readonly licenseEditExpanded = signal(false);
  readonly confirmingPayment   = signal(false);
  readonly creatingRenewal     = signal(false);
  readonly cancellingRenewal   = signal(false);

  // ── Paquetes ──────────────────────────────────────────────────────────────
  readonly licensePackages      = signal<LicensePackageItem[]>([]);
  readonly allPackages          = signal<LicensePackage[]>([]);
  readonly loadingPackages      = signal(false);
  readonly addingPackage        = signal(false);
  readonly selectedPackageId    = signal<string>('');
  readonly snapshots            = signal<MonthlyLicenseSnapshot[]>([]);

  // ── Uso IA ────────────────────────────────────────────────────────────────
  readonly aiUsage              = signal<AIUsageSummary | null>(null);
  readonly aiUsageByUser        = signal<AIUsagePerUser[]>([]);
  readonly loadingAI            = signal(false);

  // ── Tokens del agente ─────────────────────────────────────────────────────
  readonly agentTokens          = signal<AgentTokenInfo[]>([]);
  readonly loadingTokens        = signal(false);
  readonly creatingToken        = signal(false);

  readonly PACKAGE_TYPE_LABELS = PACKAGE_TYPE_LABELS;
  readonly packageColumns      = ['name', 'type', 'quantity', 'added_at', 'actions'];
  readonly aiUserColumns       = ['email', 'requests', 'tokens'];
  readonly snapshotColumns     = ['month', 'plan', 'status', 'users'];
  readonly tokenColumns        = ['label', 'token', 'last_used', 'actions'];

  readonly isEdit    = computed(() => !!this.tenantId());
  readonly pageTitle = computed(() => this.isEdit() ? 'Editar empresa' : 'Nueva empresa');

  readonly STATUS_LABELS = LICENSE_STATUS_LABELS;
  readonly PLAN_LABELS   = PLAN_LABELS;
  readonly MODULE_LABELS = MODULE_LABELS;
  readonly modules       = AVAILABLE_MODULES;

  readonly PERIOD_LABELS = LICENSE_PERIOD_LABELS;
  readonly PERIOD_DAYS   = LICENSE_PERIOD_DAYS;
  readonly PERIODS       = Object.keys(LICENSE_PERIOD_LABELS) as LicensePeriod[];

  readonly historyColumns = ['date', 'change_type', 'by', 'notes'];

  // ── Formulario empresa ────────────────────────────────────────────────────
  readonly empresaForm: FormGroup = this.fb.group({
    name:            ['', [Validators.required, Validators.maxLength(255)]],
    nit:             ['', [Validators.required, Validators.maxLength(20)]],
    plan:            ['starter', Validators.required],
    saiopen_enabled: [false],
  });

  // ── Formulario licencia ───────────────────────────────────────────────────
  readonly licenciaForm: FormGroup = this.fb.group({
    status:            ['trial', Validators.required],
    starts_at:         [null, Validators.required],
    period:            ['trial' as LicensePeriod, Validators.required],
    concurrent_users:  [1, [Validators.required, Validators.min(1)]],
    max_users:         [5, [Validators.required, Validators.min(1)]],
    modules_proyectos: [false],
    modules_crm:       [false],
    modules_soporte:   [false],
    modules_dashboard: [false],
    messages_quota:    [0, [Validators.min(0)]],
    ai_tokens_quota:   [0, [Validators.min(0)]],
    notes:             [''],
  });

  readonly expiryPreview = computed(() => {
    const period = this.licenciaForm.get('period')?.value as LicensePeriod;
    const startsRaw = this.licenciaForm.get('starts_at')?.value;
    if (!period || !startsRaw) return null;
    const starts = startsRaw instanceof Date ? startsRaw : strToDate(String(startsRaw));
    if (!starts) return null;
    const days = LICENSE_PERIOD_DAYS[period] ?? 30;
    const end = new Date(starts);
    end.setDate(end.getDate() + days);
    return end;
  });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.tenantId.set(id);
      this.loadTenant(id);
    } else {
      const today = new Date();
      this.licenciaForm.patchValue({
        starts_at: today,
        period:    'trial',
      });
    }
  }

  private loadTenant(id: string): void {
    this.loading.set(true);
    this.tenantService.getTenant(id).subscribe({
      next: t => {
        this.tenant.set(t);
        this.empresaForm.patchValue({
          name:            t.name,
          nit:             t.nit,
          plan:            t.plan,
          saiopen_enabled: false,
        });
        this.empresaForm.get('nit')?.disable();
        this.loadLicense(id);
      },
      error: () => {
        this.toast.error('Error al cargar empresa');
        this.loading.set(false);
      },
    });
  }

  private loadLicense(id: string): void {
    this.tenantService.getLicense(id).subscribe({
      next: lic => {
        this.license.set(lic);
        this.pendingRenewal.set(lic.pending_renewal ?? null);
        const modules = lic.modules_included ?? [];
        this.licenciaForm.patchValue({
          status:            lic.status,
          starts_at:         strToDate(lic.starts_at),
          period:            lic.period ?? 'monthly',
          concurrent_users:  lic.concurrent_users,
          max_users:         lic.max_users,
          modules_proyectos: modules.includes('proyectos'),
          modules_crm:       modules.includes('crm'),
          modules_soporte:   modules.includes('soporte'),
          modules_dashboard: modules.includes('dashboard'),
          messages_quota:    lic.messages_quota,
          ai_tokens_quota:   lic.ai_tokens_quota,
          notes:             lic.notes,
        });
        this.loadHistory(id);
        this.loading.set(false);
      },
      error: () => {
        const today = new Date();
        this.licenciaForm.patchValue({ starts_at: today, period: 'trial' });
        this.loading.set(false);
      },
    });
  }

  private loadHistory(id: string): void {
    this.tenantService.getLicenseHistory(id).subscribe({
      next: h => this.history.set(h),
      error: () => {},
    });
  }

  private getModulesSelected(): string[] {
    const v = this.licenciaForm.value;
    const mods: string[] = [];
    if (v.modules_proyectos) mods.push('proyectos');
    if (v.modules_crm)       mods.push('crm');
    if (v.modules_soporte)   mods.push('soporte');
    if (v.modules_dashboard) mods.push('dashboard');
    return mods;
  }

  guardar(): void {
    if (this.empresaForm.invalid || this.licenciaForm.invalid) {
      this.empresaForm.markAllAsTouched();
      this.licenciaForm.markAllAsTouched();
      return;
    }

    this.saving.set(true);
    const ev = this.empresaForm.getRawValue();
    const lv = this.licenciaForm.value;

    // Calcular expires_at a partir del período seleccionado
    const startsDate = lv.starts_at instanceof Date ? lv.starts_at : strToDate(lv.starts_at);
    lv.starts_at = dateToStr(startsDate);
    const days = LICENSE_PERIOD_DAYS[lv.period as LicensePeriod] ?? 30;
    const expiresDate = new Date(startsDate!);
    expiresDate.setDate(expiresDate.getDate() + days);
    lv.expires_at = dateToStr(expiresDate);

    if (!this.isEdit()) {
      // Crear empresa + licencia
      this.tenantService.createTenant({
        name:            ev.name,
        nit:             ev.nit,
        plan:            ev.plan,
        saiopen_enabled: ev.saiopen_enabled,
        license_status:      lv.status,
        license_starts_at:   lv.starts_at,
        license_expires_at:  lv.expires_at,
        concurrent_users:    lv.concurrent_users,
        max_users:           lv.max_users,
        modules_included:    this.getModulesSelected(),
        messages_quota:      lv.messages_quota,
        ai_tokens_quota:     lv.ai_tokens_quota,
        license_notes:       lv.notes,
      }).subscribe({
        next: () => {
          this.toast.success('Empresa creada correctamente');
          this.router.navigate(['/admin/tenants']);
        },
        error: (err: { error?: { nit?: string[] } }) => {
          this.toast.error(err?.error?.nit?.[0] ?? 'Error al crear empresa');
          this.saving.set(false);
        },
      });
    } else {
      const id = this.tenantId()!;
      // Actualizar empresa
      this.tenantService.updateTenant(id, { name: ev.name, plan: ev.plan }).subscribe({
        next: () => {
          // Actualizar licencia
          const licenseData = {
            plan:             ev.plan,
            status:           lv.status,
            starts_at:        lv.starts_at,
            expires_at:       lv.expires_at,
            period:           lv.period,
            concurrent_users: lv.concurrent_users,
            max_users:        lv.max_users,
            modules_included: this.getModulesSelected(),
            messages_quota:   lv.messages_quota,
            ai_tokens_quota:  lv.ai_tokens_quota,
            notes:            lv.notes,
          };
          const obs$ = this.license()
            ? this.tenantService.updateLicense(id, licenseData)
            : this.tenantService.createLicense(id, licenseData);

          obs$.subscribe({
            next: () => {
              this.toast.success('Cambios guardados correctamente');
              this.saving.set(false);
              this.loadLicense(id);
            },
            error: () => {
              this.toast.error('Empresa actualizada pero error en licencia');
              this.saving.set(false);
            },
          });
        },
        error: () => {
          this.toast.error('Error al actualizar empresa');
          this.saving.set(false);
        },
      });
    }
  }

  renovar(): void {
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        title: 'Renovar licencia',
        message: 'Esto creará un nuevo período activo. ¿Deseas continuar?',
        confirmText: 'Renovar',
        confirmColor: 'primary',
      },
    });
    ref.afterClosed().subscribe(confirmed => {
      if (!confirmed) return;
      this.guardar();
    });
  }

  volver(): void {
    this.navHistory.goBack('/admin/tenants');
  }

  formatMiles(value: number | null | undefined): string {
    if (value == null || value === 0) return '0';
    return value.toLocaleString('es-CO');
  }

  onMilesInput(event: Event, controlName: string): void {
    const input = event.target as HTMLInputElement;
    const raw = input.value.replace(/\D/g, '');
    const num = raw ? parseInt(raw, 10) : 0;
    this.licenciaForm.get(controlName)?.setValue(num, { emitEvent: false });
    // Reformatear el display
    input.value = num ? num.toLocaleString('es-CO') : '0';
  }

  getChangeTypeLabel(type: string): string {
    const labels: Record<string, string> = {
      created: 'Creada', renewed: 'Renovada', extended: 'Extendida',
      suspended: 'Suspendida', activated: 'Activada', modified: 'Modificada',
    };
    return labels[type] ?? type;
  }

  generarRenovacion(): void {
    const period = this.licenciaForm.get('period')?.value;
    if (!period) return;
    this.creatingRenewal.set(true);
    this.tenantService.createRenewal(this.tenantId()!, period).subscribe({
      next: renewal => {
        this.pendingRenewal.set(renewal);
        this.toast.success('Renovación pendiente creada');
        this.creatingRenewal.set(false);
      },
      error: () => {
        this.toast.error('Error al crear renovación');
        this.creatingRenewal.set(false);
      },
    });
  }

  confirmarPago(): void {
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        title: 'Confirmar pago de renovación',
        message: `La renovación quedará lista para activarse automáticamente cuando venza la licencia actual (${this.pendingRenewal()?.new_starts_at}).`,
        confirmText: 'Confirmar pago',
        confirmColor: 'primary',
      },
    });
    ref.afterClosed().subscribe(confirmed => {
      if (!confirmed) return;
      this.confirmingPayment.set(true);
      this.tenantService.confirmRenewal(this.tenantId()!).subscribe({
        next: renewal => {
          this.pendingRenewal.set(renewal);
          this.toast.success('Pago confirmado. La renovación se activará automáticamente al vencer la licencia actual.');
          this.confirmingPayment.set(false);
        },
        error: () => {
          this.toast.error('Error al confirmar pago');
          this.confirmingPayment.set(false);
        },
      });
    });
  }

  cancelarRenovacion(): void {
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        title: 'Cancelar renovación',
        message: '¿Estás seguro de cancelar esta renovación pendiente?',
        confirmText: 'Cancelar renovación',
        confirmColor: 'warn',
      },
    });
    ref.afterClosed().subscribe(confirmed => {
      if (!confirmed) return;
      this.cancellingRenewal.set(true);
      this.tenantService.cancelRenewal(this.tenantId()!).subscribe({
        next: () => {
          this.pendingRenewal.set(null);
          this.toast.success('Renovación cancelada');
          this.cancellingRenewal.set(false);
        },
        error: () => {
          this.toast.error('Error al cancelar renovación');
          this.cancellingRenewal.set(false);
        },
      });
    });
  }

  // Tab index: 0=Empresa, 1=Licencia, 2=Paquetes, 3=Uso IA, 4=Tokens, 5=Historial
  onTabChange(index: number): void {
    if (index === 2) this.loadPackagesTab();
    if (index === 3) this.loadAITab();
    if (index === 4) this.loadAgentTokensTab();
  }

  licenseStatusColor(): 'primary' | 'accent' | 'warn' {
    const s = this.license()?.status;
    if (s === 'active') return 'primary';
    if (s === 'trial') return 'accent';
    return 'warn';
  }

  // ── Paquetes ──────────────────────────────────────────────────────────────

  loadPackagesTab(): void {
    const id = this.tenantId();
    if (!id) return;
    this.loadingPackages.set(true);
    this.tenantService.getLicensePackages(id).subscribe({
      next: items => {
        this.licensePackages.set(items);
        this.loadingPackages.set(false);
      },
      error: () => { this.toast.error('Error al cargar paquetes'); this.loadingPackages.set(false); },
    });
    this.packageService.listPackages().subscribe({
      next: pkgs => this.allPackages.set(pkgs.filter(p => p.is_active)),
      error: ()   => {},
    });
    this.tenantService.getLicenseSnapshots(id).subscribe({
      next: snaps => this.snapshots.set(snaps),
      error: ()    => {},
    });
  }

  availablePackagesToAdd(): LicensePackage[] {
    const assigned = new Set(this.licensePackages().map(i => i.package.id));
    return this.allPackages().filter(p => !assigned.has(p.id));
  }

  agregarPaquete(): void {
    const pkgId = this.selectedPackageId();
    const id    = this.tenantId();
    if (!pkgId || !id) return;
    this.addingPackage.set(true);
    this.tenantService.addLicensePackage(id, pkgId).subscribe({
      next: () => {
        this.toast.success('Paquete agregado a la licencia');
        this.selectedPackageId.set('');
        this.addingPackage.set(false);
        this.loadPackagesTab();
        this.loadLicense(id);
      },
      error: () => { this.toast.error('Error al agregar paquete'); this.addingPackage.set(false); },
    });
  }

  quitarPaquete(item: LicensePackageItem): void {
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        title: 'Quitar paquete',
        message: `¿Quitar el paquete "${item.package.name}" de esta licencia? Esto ajustará los límites de la empresa.`,
        confirmText: 'Quitar',
        confirmColor: 'warn',
      },
    });
    ref.afterClosed().subscribe(ok => {
      if (!ok) return;
      const id = this.tenantId()!;
      this.tenantService.removeLicensePackage(id, item.id).subscribe({
        next: () => {
          this.toast.success('Paquete removido');
          this.loadPackagesTab();
          this.loadLicense(id);
        },
        error: () => this.toast.error('Error al quitar paquete'),
      });
    });
  }

  packageTypeLabel(type: string): string {
    return PACKAGE_TYPE_LABELS[type as keyof typeof PACKAGE_TYPE_LABELS] ?? type;
  }

  snapshotMonth(snap: MonthlyLicenseSnapshot): string {
    const d = new Date(snap.month + 'T00:00:00');
    return d.toLocaleDateString('es-CO', { month: 'long', year: 'numeric' });
  }

  // ── Uso IA ────────────────────────────────────────────────────────────────

  loadAITab(): void {
    const id = this.tenantId();
    if (!id) return;
    this.loadingAI.set(true);
    this.tenantService.getAIUsage(id).subscribe({
      next: data => { this.aiUsage.set(data); this.loadingAI.set(false); },
      error: ()   => { this.loadingAI.set(false); },
    });
    this.tenantService.getAIUsageByUser(id).subscribe({
      next: data => this.aiUsageByUser.set(data),
      error: ()   => {},
    });
  }

  pctColor(pct: number): string {
    if (pct >= 90) return 'warn';
    if (pct >= 60) return 'accent';
    return 'primary';
  }

  // ── Tokens del agente ─────────────────────────────────────────────────────

  loadAgentTokensTab(): void {
    const id = this.tenantId();
    if (!id) return;
    this.loadingTokens.set(true);
    this.tenantService.getAgentTokens(id).subscribe({
      next: data => { this.agentTokens.set(data); this.loadingTokens.set(false); },
      error: ()   => { this.loadingTokens.set(false); },
    });
  }

  crearAgentToken(): void {
    const id = this.tenantId();
    if (!id) return;
    this.creatingToken.set(true);
    this.tenantService.createAgentToken(id, '').subscribe({
      next: (token) => {
        this.agentTokens.update(list => [token, ...list]);
        this.creatingToken.set(false);
        this.toast.success('Token creado correctamente.');
      },
      error: () => {
        this.creatingToken.set(false);
        this.toast.error('No se pudo crear el token.');
      },
    });
  }

  revocarToken(token: AgentTokenInfo): void {
    const id = this.tenantId();
    if (!id) return;
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      data: {
        title: 'Revocar token',
        message: `¿Estás seguro de revocar el token "${token.label || token.token.slice(0, 12) + '...'}"? El agente dejará de funcionar con este token.`,
        confirmText: 'Revocar',
        confirmColor: 'warn',
      },
    });
    dialogRef.afterClosed().subscribe(confirmed => {
      if (!confirmed) return;
      this.tenantService.revokeAgentToken(id, token.id).subscribe({
        next: () => {
          this.agentTokens.update(list => list.filter(t => t.id !== token.id));
          this.toast.success('Token revocado.');
        },
        error: () => this.toast.error('No se pudo revocar el token.'),
      });
    });
  }

  copyToken(value: string): void {
    navigator.clipboard.writeText(value).then(() => {
      this.toast.success('Token copiado al portapapeles.');
    });
  }
}
