import {
  ChangeDetectionStrategy, Component, OnInit,
  inject, signal, computed,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatTableModule } from '@angular/material/table';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatDialogModule, MatDialog } from '@angular/material/dialog';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatDividerModule } from '@angular/material/divider';
import { MatTabsModule } from '@angular/material/tabs';
import { PackageService } from '../services/package.service';
import { ToastService } from '../../../core/services/toast.service';
import { ConfirmDialogComponent } from '../../../shared/components/confirm-dialog/confirm-dialog.component';
import {
  LicensePackage, LicensePackageWriteRequest,
  PackageType, PACKAGE_TYPE_LABELS,
} from '../models/tenant.model';

@Component({
  selector: 'app-package-catalog',
  templateUrl: './package-catalog.component.html',
  styleUrl: './package-catalog.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, ReactiveFormsModule,
    MatButtonModule, MatIconModule, MatInputModule,
    MatFormFieldModule, MatSelectModule, MatCheckboxModule,
    MatTableModule, MatChipsModule, MatTooltipModule,
    MatProgressBarModule, MatDialogModule, MatSlideToggleModule,
    MatDividerModule, MatTabsModule,
  ],
})
export class PackageCatalogComponent implements OnInit {
  private readonly packageService = inject(PackageService);
  private readonly toast          = inject(ToastService);
  private readonly dialog         = inject(MatDialog);
  private readonly fb             = inject(FormBuilder);

  readonly loading  = signal(false);
  readonly saving   = signal(false);
  readonly packages = signal<LicensePackage[]>([]);
  readonly editing  = signal<LicensePackage | null>(null);
  readonly showForm = signal(false);

  readonly TYPE_LABELS = PACKAGE_TYPE_LABELS;
  readonly TYPES: PackageType[] = ['module', 'user_seats', 'ai_tokens'];
  readonly MODULE_CODES = ['proyectos', 'crm', 'soporte', 'dashboard'];

  readonly columnsModules  = ['module_code', 'name', 'code', 'price_monthly', 'price_annual', 'is_active', 'actions'];
  readonly columnsUsers    = ['name', 'code', 'quantity', 'price_monthly', 'price_annual', 'is_active', 'actions'];
  readonly columnsTokens   = ['name', 'code', 'type', 'quantity', 'price_monthly', 'price_annual', 'is_active', 'actions'];

  // Kept for legacy reference — not used in template anymore
  readonly displayedColumns = ['code', 'name', 'type', 'quantity', 'price_monthly', 'price_annual', 'is_active', 'actions'];

  readonly modulePackages = computed(() => this.packages().filter(p => p.package_type === 'module'));
  readonly userPackages   = computed(() => this.packages().filter(p => p.package_type === 'user_seats'));
  readonly tokenPackages  = computed(() => this.packages().filter(p => p.package_type === 'ai_tokens' || p.package_type === 'ai_messages'));

  readonly form = this.fb.group({
    code:          ['', [Validators.required, Validators.maxLength(50)]],
    name:          ['', [Validators.required, Validators.maxLength(100)]],
    description:   [''],
    package_type:  ['module' as PackageType, Validators.required],
    module_code:   [''],
    quantity:      [0, [Validators.min(0)]],
    price_monthly: [0, [Validators.required, Validators.min(0)]],
    price_annual:  [0, [Validators.required, Validators.min(0)]],
    is_active:     [true],
  });

  readonly isModuleType = computed(() => this.form.get('package_type')?.value === 'module');
  readonly isEditing    = computed(() => !!this.editing());
  readonly formTitle    = computed(() => this.isEditing() ? 'Editar paquete' : 'Nuevo paquete');

  ngOnInit(): void {
    this.loadPackages();
  }

  loadPackages(): void {
    this.loading.set(true);
    this.packageService.listPackages().subscribe({
      next:  pkgs => { this.packages.set(pkgs); this.loading.set(false); },
      error: ()   => { this.toast.error('Error al cargar paquetes'); this.loading.set(false); },
    });
  }

  openNew(): void {
    this.openNewWithType('module');
  }

  openNewWithType(type: PackageType): void {
    this.editing.set(null);
    this.form.reset({
      code: '', name: '', description: '',
      package_type: type, module_code: '',
      quantity: 0, price_monthly: 0, price_annual: 0, is_active: true,
    });
    this.form.get('code')?.enable();
    this.showForm.set(true);
    // Scroll al formulario
    setTimeout(() => document.querySelector('.pc-form-card')?.scrollIntoView({ behavior: 'smooth' }), 50);
  }

  openEdit(pkg: LicensePackage): void {
    this.editing.set(pkg);
    this.form.patchValue({
      code:          pkg.code,
      name:          pkg.name,
      description:   pkg.description,
      package_type:  pkg.package_type,
      module_code:   pkg.module_code,
      quantity:      pkg.quantity,
      price_monthly: parseFloat(pkg.price_monthly),
      price_annual:  parseFloat(pkg.price_annual),
      is_active:     pkg.is_active,
    });
    this.form.get('code')?.disable();
    this.showForm.set(true);
  }

  cancelForm(): void {
    this.showForm.set(false);
    this.editing.set(null);
  }

  guardar(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }

    this.saving.set(true);
    const v = this.form.getRawValue();
    const data: LicensePackageWriteRequest = {
      code:          v.code ?? '',
      name:          v.name ?? '',
      description:   v.description ?? '',
      package_type:  (v.package_type ?? 'module') as PackageType,
      module_code:   v.module_code ?? '',
      quantity:      v.quantity ?? 0,
      price_monthly: v.price_monthly ?? 0,
      price_annual:  v.price_annual ?? 0,
      is_active:     v.is_active ?? true,
    };

    const pkg = this.editing();
    const obs$ = pkg
      ? this.packageService.updatePackage(pkg.id, data)
      : this.packageService.createPackage(data);

    obs$.subscribe({
      next: () => {
        this.toast.success(pkg ? 'Paquete actualizado' : 'Paquete creado');
        this.saving.set(false);
        this.showForm.set(false);
        this.editing.set(null);
        this.loadPackages();
      },
      error: () => {
        this.toast.error('Error al guardar paquete');
        this.saving.set(false);
      },
    });
  }

  toggleActive(pkg: LicensePackage): void {
    this.packageService.updatePackage(pkg.id, { is_active: !pkg.is_active }).subscribe({
      next: () => { this.toast.success('Estado actualizado'); this.loadPackages(); },
      error: ()  => this.toast.error('Error al actualizar estado'),
    });
  }

  eliminar(pkg: LicensePackage): void {
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        title: 'Eliminar paquete',
        message: `¿Eliminar el paquete "${pkg.name}"? Esta acción es irreversible y fallará si está asignado a alguna licencia.`,
        confirmText: 'Eliminar',
        confirmColor: 'warn',
      },
    });
    ref.afterClosed().subscribe(ok => {
      if (!ok) return;
      this.packageService.deletePackage(pkg.id).subscribe({
        next: () => { this.toast.success('Paquete eliminado'); this.loadPackages(); },
        error: ()  => this.toast.error('No se puede eliminar: está asignado a una licencia'),
      });
    });
  }

  typeLabel(type: PackageType): string {
    return PACKAGE_TYPE_LABELS[type] ?? type;
  }

  formatCOP(value: string | number): string {
    const n = typeof value === 'string' ? parseFloat(value) : value;
    if (!n) return '$0';
    return '$' + n.toLocaleString('es-CO', { minimumFractionDigits: 0 });
  }

  formatMiles(value: number | null | undefined): string {
    if (value == null || value === 0) return '0';
    return value.toLocaleString('es-CO');
  }

  onMilesInput(event: Event, controlName: string): void {
    const input = event.target as HTMLInputElement;
    const raw = input.value.replace(/\D/g, '');
    const num = raw ? parseInt(raw, 10) : 0;
    this.form.get(controlName)?.setValue(num, { emitEvent: false });
    input.value = num ? num.toLocaleString('es-CO') : '0';
  }
}
