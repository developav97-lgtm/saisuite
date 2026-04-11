import { ComponentFixture, TestBed } from '@angular/core/testing';
import { DrillDownPanelComponent, DrillDownData } from './drill-down-panel.component';

describe('DrillDownPanelComponent', () => {
  let component: DrillDownPanelComponent;
  let fixture: ComponentFixture<DrillDownPanelComponent>;

  const mockDrillDown: DrillDownData = {
    title: 'Detalle: Cuenta 4101',
    filters: { cuenta: '4101', periodo: '2026-01' },
    columns: ['fecha', 'tercero', 'debito', 'credito'],
    rows: [
      { fecha: '2026-01-15', tercero: 'Cliente A', debito: 500, credito: 0 },
      { fecha: '2026-01-20', tercero: 'Cliente B', debito: 0, credito: 300 },
    ],
    loading: false,
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DrillDownPanelComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(DrillDownPanelComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should be closed when no data', () => {
    fixture.detectChanges();
    expect(component.isOpen()).toBeFalse();
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('.drill-down-panel')).toBeNull();
  });

  it('should open when data is provided', () => {
    fixture.componentRef.setInput('data', mockDrillDown);
    fixture.detectChanges();
    expect(component.isOpen()).toBeTrue();
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('.drill-down-panel')).toBeTruthy();
  });

  it('should display title', () => {
    fixture.componentRef.setInput('data', mockDrillDown);
    fixture.detectChanges();
    expect(component.title()).toBe('Detalle: Cuenta 4101');
  });

  it('should display filter chips', () => {
    fixture.componentRef.setInput('data', mockDrillDown);
    fixture.detectChanges();
    const chips = component.filterChips();
    expect(chips.length).toBe(2);
    expect(chips[0]).toEqual({ key: 'cuenta', value: '4101' });
  });

  it('should emit close', () => {
    fixture.componentRef.setInput('data', mockDrillDown);
    fixture.detectChanges();
    const spy = spyOn(component.close, 'emit');
    component.onClose();
    expect(spy).toHaveBeenCalled();
  });

  it('should identify numeric values', () => {
    expect(component.isNumeric(42)).toBeTrue();
    expect(component.isNumeric('text')).toBeFalse();
    expect(component.isNumeric(null)).toBeFalse();
  });
});
