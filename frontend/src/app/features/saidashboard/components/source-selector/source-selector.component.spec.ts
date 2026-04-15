import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SourceSelectorComponent } from './source-selector.component';
import { BI_SOURCES, BI_SOURCE_GROUPS } from '../../models/bi-source.model';

describe('SourceSelectorComponent', () => {
  let fixture: ComponentFixture<SourceSelectorComponent>;
  let component: SourceSelectorComponent;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [SourceSelectorComponent],
    });
    fixture = TestBed.createComponent(SourceSelectorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('exposes all BI_SOURCE_GROUPS', () => {
    expect(component.groups).toEqual(BI_SOURCE_GROUPS);
    expect(component.groups.length).toBe(2);
  });

  it('sourcesForGroup returns only transaccional sources', () => {
    const transaccionales = component.sourcesForGroup('transaccional');
    expect(transaccionales.every(s => s.group === 'transaccional')).toBeTrue();
    expect(transaccionales.length).toBeGreaterThan(0);
  });

  it('sourcesForGroup returns only maestro sources', () => {
    const maestros = component.sourcesForGroup('maestro');
    expect(maestros.every(s => s.group === 'maestro')).toBeTrue();
    expect(maestros.length).toBeGreaterThan(0);
  });

  it('total sources across groups equals BI_SOURCES length', () => {
    const total = component.sourcesForGroup('transaccional').length
      + component.sourcesForGroup('maestro').length;
    expect(total).toBe(BI_SOURCES.length);
  });

  it('isSelected returns false when nothing selected', () => {
    expect(component.isSelected('gl')).toBeFalse();
  });

  it('toggle emits new selection', () => {
    spyOn(component.selectionChange, 'emit');
    component.toggle('gl');
    expect(component.selectionChange.emit).toHaveBeenCalledWith(['gl']);
  });

  it('toggle removes already selected source', () => {
    fixture.componentRef.setInput('selected', ['gl', 'cartera']);
    fixture.detectChanges();

    spyOn(component.selectionChange, 'emit');
    component.toggle('gl');
    expect(component.selectionChange.emit).toHaveBeenCalledWith(['cartera']);
  });

  it('isSelected returns true for selected sources', () => {
    fixture.componentRef.setInput('selected', ['gl']);
    fixture.detectChanges();
    expect(component.isSelected('gl')).toBeTrue();
    expect(component.isSelected('cartera')).toBeFalse();
  });

  it('new sources terceros_saiopen and productos are available', () => {
    const codes = BI_SOURCES.map(s => s.code);
    expect(codes).toContain('terceros_saiopen');
    expect(codes).toContain('productos');
    expect(codes).toContain('cuentas_contables');
  });
});
