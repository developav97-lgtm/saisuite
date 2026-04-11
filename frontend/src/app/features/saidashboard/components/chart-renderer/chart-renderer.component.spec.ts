import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Chart, registerables } from 'chart.js';
import { ChartRendererComponent } from './chart-renderer.component';
import { ReportBITableResult } from '../../models/report-bi.model';
import { BIFieldConfig } from '../../models/bi-field.model';

Chart.register(...registerables);

describe('ChartRendererComponent', () => {
  let component: ChartRendererComponent;
  let fixture: ComponentFixture<ChartRendererComponent>;

  const mockTableData: ReportBITableResult = {
    columns: ['periodo', 'total_sum'],
    rows: [
      { periodo: '2026-01', total_sum: 5000 },
      { periodo: '2026-02', total_sum: 7500 },
      { periodo: '2026-03', total_sum: 6200 },
    ],
    total_count: 3,
  };

  const mockFields: BIFieldConfig[] = [
    { source: 'gl', field: 'periodo', role: 'dimension', label: 'Período' },
    { source: 'gl', field: 'total', role: 'metric', aggregation: 'SUM', label: 'Total' },
  ];

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ChartRendererComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ChartRendererComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should detect KPI visualization', () => {
    fixture.componentRef.setInput('visualization', 'kpi');
    fixture.detectChanges();
    expect(component.isKpi()).toBeTrue();
    expect(component.isChart()).toBeFalse();
  });

  it('should detect chart visualizations', () => {
    for (const viz of ['bar', 'line', 'pie', 'area', 'waterfall'] as const) {
      fixture.componentRef.setInput('visualization', viz);
      fixture.detectChanges();
      expect(component.isChart()).toBeTrue();
      expect(component.isKpi()).toBeFalse();
    }
  });

  it('should generate KPI data from metrics', () => {
    fixture.componentRef.setInput('data', mockTableData);
    fixture.componentRef.setInput('visualization', 'kpi');
    fixture.componentRef.setInput('fields', mockFields);
    fixture.detectChanges();
    const kpis = component.kpiData();
    expect(kpis.length).toBe(1);
    expect(kpis[0].label).toBe('Total');
  });

  it('should generate chart config for bar', () => {
    fixture.componentRef.setInput('data', mockTableData);
    fixture.componentRef.setInput('visualization', 'bar');
    fixture.componentRef.setInput('fields', mockFields);
    fixture.detectChanges();
    const config = component.chartConfig();
    expect(config).toBeTruthy();
    expect(config!.type).toBe('bar');
    expect(config!.data.labels!.length).toBe(3);
  });

  it('should generate pie config for pie', () => {
    fixture.componentRef.setInput('data', mockTableData);
    fixture.componentRef.setInput('visualization', 'pie');
    fixture.componentRef.setInput('fields', mockFields);
    fixture.detectChanges();
    const config = component.chartConfig();
    expect(config).toBeTruthy();
    expect(config!.type).toBe('pie');
  });

  it('should generate waterfall config with total bar', () => {
    fixture.componentRef.setInput('data', mockTableData);
    fixture.componentRef.setInput('visualization', 'waterfall');
    fixture.componentRef.setInput('fields', mockFields);
    fixture.detectChanges();
    const config = component.chartConfig();
    expect(config).toBeTruthy();
    expect(config!.type).toBe('bar');
    // Waterfall adds a "Total" label
    expect(config!.data.labels!.length).toBe(4);
  });

  it('should return null config when no data', () => {
    fixture.componentRef.setInput('visualization', 'bar');
    fixture.componentRef.setInput('fields', mockFields);
    fixture.detectChanges();
    expect(component.chartConfig()).toBeNull();
  });

  it('should return correct chartType for area', () => {
    fixture.componentRef.setInput('visualization', 'area');
    fixture.detectChanges();
    expect(component.chartType()).toBe('line');
  });
});
