import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { FilterBuilderComponent } from './filter-builder.component';
import { BIFilterV2 } from '../../models/bi-field.model';

describe('FilterBuilderComponent (V2)', () => {
  let fixture: ComponentFixture<FilterBuilderComponent>;
  let component: FilterBuilderComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FilterBuilderComponent],
      providers: [
        provideAnimationsAsync(),
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(FilterBuilderComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('starts with no filters and panel closed', () => {
    expect(component.activeFilterCount).toBe(0);
    expect(component.addPanelOpen()).toBeFalse();
  });

  it('toggleAddPanel opens the panel', () => {
    component.toggleAddPanel();
    expect(component.addPanelOpen()).toBeTrue();
  });

  it('toggleAddPanel closes and resets pending', () => {
    component.toggleAddPanel();
    component.pending.update(p => ({ ...p, field: 'debito', source: 'gl' }));
    component.toggleAddPanel();
    expect(component.addPanelOpen()).toBeFalse();
    expect(component.pending().field).toBe('');
  });

  it('canAddFilter is false with no field selected', () => {
    expect(component.canAddFilter()).toBeFalse();
  });

  it('selectField updates pending with field info', () => {
    component.selectField({
      source: 'gl',
      sourceLabel: 'Contabilidad (GL)',
      field: 'debito',
      label: 'Débito',
      type: 'decimal',
      role: 'metric',
    });
    const p = component.pending();
    expect(p.source).toBe('gl');
    expect(p.field).toBe('debito');
    expect(p.fieldType).toBe('decimal');
  });

  it('availableOperators changes based on field type', () => {
    component.selectField({
      source: 'gl', sourceLabel: 'GL', field: 'fecha', label: 'Fecha',
      type: 'date', role: 'dimension',
    });
    const ops = component.availableOperators().map(o => o.value);
    expect(ops).toContain('between');
    expect(ops).not.toContain('contains');
  });

  it('isBoolOp is true for boolean field with is_true', () => {
    component.selectField({
      source: 'facturacion', sourceLabel: 'Facturación', field: 'posted',
      label: 'Contabilizado', type: 'boolean', role: 'dimension',
    });
    // Default for boolean is is_true
    expect(component.isBoolOp()).toBeTrue();
  });

  it('addFilter emits new filter and closes panel', () => {
    fixture.componentRef.setInput('filters', []);
    const emitted: BIFilterV2[][] = [];
    component.filtersChange.subscribe((f: BIFilterV2[]) => emitted.push(f));

    component.selectField({
      source: 'gl', sourceLabel: 'GL', field: 'periodo', label: 'Período',
      type: 'text', role: 'dimension',
    });
    component.selectOperator('eq');
    component.pending.update(p => ({ ...p, valueScalar: '202601' }));
    component.toggleAddPanel(); // open
    component.addFilter();

    expect(emitted.length).toBe(1);
    expect(emitted[0][0].operator).toBe('eq');
    expect(emitted[0][0].value).toBe('202601');
    expect(component.addPanelOpen()).toBeFalse();
  });

  it('addFilter with "in" operator parses comma-separated list', () => {
    fixture.componentRef.setInput('filters', []);
    const emitted: BIFilterV2[][] = [];
    component.filtersChange.subscribe((f: BIFilterV2[]) => emitted.push(f));

    component.selectField({
      source: 'gl', sourceLabel: 'GL', field: 'tercero_id', label: 'ID Tercero',
      type: 'text', role: 'dimension',
    });
    component.selectOperator('in');
    component.pending.update(p => ({ ...p, valueList: '1001, 1002, 1003' }));
    component.addFilter();

    expect(emitted[0][0].value).toEqual(['1001', '1002', '1003']);
  });

  it('removeFilter emits updated array', () => {
    const existing: BIFilterV2[] = [
      { source: 'gl', field: 'periodo', operator: 'eq', value: '202601' },
      { source: 'gl', field: 'debito', operator: 'gt', value: '0' },
    ];
    fixture.componentRef.setInput('filters', existing);
    const emitted: BIFilterV2[][] = [];
    component.filtersChange.subscribe((f: BIFilterV2[]) => emitted.push(f));

    component.removeFilter(0);
    expect(emitted[0].length).toBe(1);
    expect(emitted[0][0].field).toBe('debito');
  });

  it('clearAll emits empty array', () => {
    fixture.componentRef.setInput('filters', [
      { source: 'gl', field: 'periodo', operator: 'eq', value: '202601' },
    ]);
    const emitted: BIFilterV2[][] = [];
    component.filtersChange.subscribe((f: BIFilterV2[]) => emitted.push(f));

    component.clearAll();
    expect(emitted[0]).toEqual([]);
  });

  it('getFilterSummary returns readable string', () => {
    component.fieldOptions.set([{
      source: 'gl', sourceLabel: 'GL', field: 'periodo', label: 'Período',
      type: 'text', role: 'dimension',
    }]);
    const f: BIFilterV2 = { source: 'gl', field: 'periodo', operator: 'eq', value: '202601' };
    const summary = component.getFilterSummary(f);
    expect(summary).toContain('Período');
    expect(summary).toContain('202601');
  });
});
