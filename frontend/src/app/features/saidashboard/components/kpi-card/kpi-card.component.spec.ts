import { ComponentFixture, TestBed } from '@angular/core/testing';
import { KpiCardComponent } from './kpi-card.component';

describe('KpiCardComponent', () => {
  let fixture: ComponentFixture<KpiCardComponent>;

  function createComponent(inputs: { value: number; title: string; previousValue?: number | null; format?: 'currency' | 'percent' | 'number' }) {
    fixture = TestBed.createComponent(KpiCardComponent);
    fixture.componentRef.setInput('title', inputs.title);
    fixture.componentRef.setInput('value', inputs.value);
    if (inputs.previousValue !== undefined) fixture.componentRef.setInput('previousValue', inputs.previousValue);
    if (inputs.format) fixture.componentRef.setInput('format', inputs.format);
    fixture.detectChanges();
    return fixture.componentInstance;
  }

  beforeEach(() => TestBed.configureTestingModule({ imports: [KpiCardComponent] }));

  it('should create', () => {
    const comp = createComponent({ title: 'Ingresos', value: 1000 });
    expect(comp).toBeTruthy();
  });

  it('formattedValue — format number (default)', () => {
    const comp = createComponent({ title: 'Ventas', value: 1500000 });
    expect(comp.formattedValue()).toContain('1');
  });

  it('formattedValue — format currency', () => {
    const comp = createComponent({ title: 'Ingresos', value: 5000000, format: 'currency' });
    expect(comp.formattedValue()).toContain('$');
  });

  it('formattedValue — format percent', () => {
    const comp = createComponent({ title: 'Margen', value: 23.456, format: 'percent' });
    expect(comp.formattedValue()).toBe('23.5%');
  });

  it('trendUp — true when value >= previousValue', () => {
    const comp = createComponent({ title: 'T', value: 100, previousValue: 80 });
    expect(comp.trendUp()).toBeTrue();
  });

  it('trendUp — false when value < previousValue', () => {
    const comp = createComponent({ title: 'T', value: 60, previousValue: 80 });
    expect(comp.trendUp()).toBeFalse();
  });

  it('trendUp — true when previousValue is 0', () => {
    const comp = createComponent({ title: 'T', value: 100, previousValue: 0 });
    expect(comp.trendUp()).toBeTrue();
  });

  it('trendPercent — shows correct change %', () => {
    const comp = createComponent({ title: 'T', value: 120, previousValue: 100 });
    expect(comp.trendPercent()).toBe('+20.0%');
  });

  it('trendPercent — shows negative change %', () => {
    const comp = createComponent({ title: 'T', value: 80, previousValue: 100 });
    expect(comp.trendPercent()).toBe('-20.0%');
  });

  it('trendPercent — empty when previousValue is null', () => {
    const comp = createComponent({ title: 'T', value: 100, previousValue: null });
    expect(comp.trendPercent()).toBe('');
  });

  it('renders title in template', () => {
    createComponent({ title: 'Flujo de Caja', value: 500 });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Flujo de Caja');
  });

  it('does not render trend when previousValue is null', () => {
    createComponent({ title: 'T', value: 100, previousValue: null });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('.kpi-trend')).toBeNull();
  });

  it('renders trend when previousValue is set', () => {
    createComponent({ title: 'T', value: 100, previousValue: 80 });
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('.kpi-trend')).toBeTruthy();
  });
});
