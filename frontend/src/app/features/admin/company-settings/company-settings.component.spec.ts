/**
 * SaiSuite — Tests CompanySettingsComponent
 */
import { registerLocaleData } from '@angular/common';
import localeEsCo from '@angular/common/locales/es-CO';
import { LOCALE_ID } from '@angular/core';
import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { of, throwError } from 'rxjs';
import { CompanySettingsComponent } from './company-settings.component';
import { AdminService } from '../services/admin.service';
import { CompanySettings, CompanyLicense } from '../models/admin.models';

registerLocaleData(localeEsCo);

// ── Mock data ─────────────────────────────────────────────────────────────────

const mockSettings: CompanySettings = {
  id: 'co-1', name: 'Mi Empresa', nit: '900001001',
  plan: 'professional', saiopen_enabled: false, is_active: true,
  modules: [
    { id: 'm-1', module: 'proyectos', is_active: true },
    { id: 'm-2', module: 'ventas',    is_active: false },
  ],
  created_at: '2026-01-01T00:00:00Z',
};

function makeLicense(overrides: Partial<CompanyLicense> = {}): CompanyLicense {
  return {
    id: 'lic-1', plan: 'professional', status: 'active',
    starts_at: '2026-01-01', expires_at: '2026-12-31',
    max_users: 20, days_until_expiry: 100, is_expired: false,
    ...overrides,
  };
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('CompanySettingsComponent', () => {
  let fixture: ComponentFixture<CompanySettingsComponent>;
  let component: CompanySettingsComponent;
  let adminService: jasmine.SpyObj<AdminService>;

  async function setup(
    settingsResult: CompanySettings | null = mockSettings,
    licenseResult: CompanyLicense | null = makeLicense(),
  ) {
    const spy = jasmine.createSpyObj('AdminService', ['getCompanySettings', 'getMyLicense']);
    spy.getCompanySettings.and.returnValue(
      settingsResult ? of(settingsResult) : throwError(() => ({ status: 500 }))
    );
    spy.getMyLicense.and.returnValue(
      licenseResult ? of(licenseResult) : throwError(() => ({ status: 404 }))
    );

    await TestBed.configureTestingModule({
      imports: [CompanySettingsComponent],
      providers: [
        provideAnimationsAsync(),
        { provide: AdminService, useValue: spy },
        { provide: LOCALE_ID, useValue: 'es-CO' },
      ],
    }).compileComponents();

    adminService = TestBed.inject(AdminService) as jasmine.SpyObj<AdminService>;
    fixture      = TestBed.createComponent(CompanySettingsComponent);
    component    = fixture.componentInstance;
    fixture.detectChanges();
  }

  afterEach(() => TestBed.resetTestingModule());

  // ── Creación e inicialización ─────────────────────────────────────────────

  it('se crea correctamente', async () => {
    await setup();
    expect(component).toBeTruthy();
  });

  it('ngOnInit carga datos de company y licencia', fakeAsync(async () => {
    await setup();
    tick();
    expect(adminService.getCompanySettings).toHaveBeenCalled();
    expect(adminService.getMyLicense).toHaveBeenCalled();
    expect(component.company()).toEqual(mockSettings);
    expect(component.license()).toBeTruthy();
  }));

  it('loading pasa a false tras carga exitosa', fakeAsync(async () => {
    await setup();
    tick();
    expect(component.loading()).toBeFalse();
  }));

  it('loading pasa a false tras error en getCompanySettings', fakeAsync(async () => {
    await setup(null, makeLicense());
    tick();
    expect(component.loading()).toBeFalse();
  }));

  // ── Señales de datos ──────────────────────────────────────────────────────

  it('company signal contiene datos tras carga', fakeAsync(async () => {
    await setup();
    tick();
    expect(component.company()?.name).toBe('Mi Empresa');
    expect(component.company()?.nit).toBe('900001001');
    expect(component.company()?.plan).toBe('professional');
  }));

  it('license signal contiene datos tras carga', fakeAsync(async () => {
    await setup();
    tick();
    expect(component.license()?.status).toBe('active');
    expect(component.license()?.max_users).toBe(20);
    expect(component.license()?.days_until_expiry).toBe(100);
  }));

  it('license es null si el servicio falla', fakeAsync(async () => {
    await setup(mockSettings, null);
    tick();
    expect(component.license()).toBeNull();
  }));

  it('company es null si el servicio falla', fakeAsync(async () => {
    await setup(null, makeLicense());
    tick();
    expect(component.company()).toBeNull();
  }));

  // ── Labels y estados ──────────────────────────────────────────────────────

  it('planLabels contiene las traducciones correctas', async () => {
    await setup();
    expect(component.planLabels['starter']).toBe('Starter');
    expect(component.planLabels['professional']).toBe('Professional');
    expect(component.planLabels['enterprise']).toBe('Enterprise');
  });

  it('licenseStatusLabels contiene todos los estados', async () => {
    await setup();
    expect(component.licenseStatusLabels['active']).toBe('Activa');
    expect(component.licenseStatusLabels['expired']).toBe('Expirada');
    expect(component.licenseStatusLabels['suspended']).toBe('Suspendida');
    expect(component.licenseStatusLabels['trial']).toBe('Prueba');
  });

  it('moduleLabels contiene los módulos', async () => {
    await setup();
    expect(component.moduleLabels['proyectos']).toBe('SaiProyectos');
    expect(component.moduleLabels['ventas']).toBe('SaiVentas');
    expect(component.moduleLabels['cobros']).toBe('SaiCobros');
    expect(component.moduleLabels['dashboard']).toBe('SaiDashboard');
  });

  // ── Escenarios de licencia ────────────────────────────────────────────────

  it('is_expired false cuando licencia vigente', fakeAsync(async () => {
    await setup(mockSettings, makeLicense({ is_expired: false }));
    tick();
    expect(component.license()?.is_expired).toBeFalse();
  }));

  it('is_expired true cuando licencia expirada', fakeAsync(async () => {
    await setup(mockSettings, makeLicense({ status: 'expired', is_expired: true, days_until_expiry: -5 }));
    tick();
    expect(component.license()?.is_expired).toBeTrue();
  }));

  it('days_until_expiry positivo cuando vigente', fakeAsync(async () => {
    await setup(mockSettings, makeLicense({ days_until_expiry: 30 }));
    tick();
    expect(component.license()!.days_until_expiry).toBe(30);
  }));

  it('days_until_expiry negativo cuando expirada', fakeAsync(async () => {
    await setup(mockSettings, makeLicense({ is_expired: true, days_until_expiry: -3 }));
    tick();
    expect(component.license()!.days_until_expiry).toBe(-3);
  }));

  it('estado suspended en licencia suspendida', fakeAsync(async () => {
    await setup(mockSettings, makeLicense({ status: 'suspended' }));
    tick();
    expect(component.license()?.status).toBe('suspended');
  }));

  it('módulos activos en company.modules', fakeAsync(async () => {
    await setup();
    tick();
    const activeModules = component.company()?.modules.filter(m => m.is_active) ?? [];
    expect(activeModules.length).toBe(1);
    expect(activeModules[0].module).toBe('proyectos');
  }));
});
