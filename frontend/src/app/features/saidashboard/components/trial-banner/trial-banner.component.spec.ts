import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TrialBannerComponent } from './trial-banner.component';
import { TrialStatus } from '../../models/trial.model';

describe('TrialBannerComponent', () => {
  let fixture: ComponentFixture<TrialBannerComponent>;
  let component: TrialBannerComponent;

  const trialStatus: TrialStatus = {
    tiene_acceso: true,
    tipo_acceso: 'trial',
    dias_restantes: 10,
    expira_en: '2026-04-17',
  };

  const noneStatus: TrialStatus = {
    tiene_acceso: false,
    tipo_acceso: 'none',
    dias_restantes: 0,
    expira_en: null,
  };

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [TrialBannerComponent] });
    fixture   = TestBed.createComponent(TrialBannerComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    fixture.componentRef.setInput('trialStatus', null);
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  it('renders nothing when trialStatus is null', () => {
    fixture.componentRef.setInput('trialStatus', null);
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('.tb-banner')).toBeNull();
  });

  it('renders trial banner when tipo_acceso is trial', () => {
    fixture.componentRef.setInput('trialStatus', trialStatus);
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('.tb-banner')).toBeTruthy();
    expect(el.textContent).toContain('10 días restantes');
  });

  it('adds warning class when dias_restantes <= 5', () => {
    fixture.componentRef.setInput('trialStatus', { ...trialStatus, dias_restantes: 3 });
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('.tb-banner--warning')).toBeTruthy();
  });

  it('does not add warning class when dias_restantes > 5', () => {
    fixture.componentRef.setInput('trialStatus', trialStatus);
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('.tb-banner--warning')).toBeNull();
  });

  it('renders inactive banner when tipo_acceso is none', () => {
    fixture.componentRef.setInput('trialStatus', noneStatus);
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('.tb-banner--inactive')).toBeTruthy();
    expect(el.textContent).toContain('prueba gratuita');
  });

  it('emits activateTrial when button clicked (none state)', () => {
    fixture.componentRef.setInput('trialStatus', noneStatus);
    fixture.detectChanges();
    let emitted = false;
    component.activateTrial.subscribe(() => emitted = true);
    const btn = fixture.nativeElement.querySelector('button[color="primary"]');
    btn?.click();
    expect(emitted).toBeTrue();
  });

  it('emits contactSales when Adquirir licencia clicked', () => {
    fixture.componentRef.setInput('trialStatus', trialStatus);
    fixture.detectChanges();
    let emitted = false;
    component.contactSales.subscribe(() => emitted = true);
    const btn: HTMLButtonElement = fixture.nativeElement.querySelector('.tb-action');
    btn?.click();
    expect(emitted).toBeTrue();
  });
});
