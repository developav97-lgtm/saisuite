import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { BiReportCardComponent } from './bi-report-card.component';
import { DashboardService } from '../../services/dashboard.service';
import { DashboardCard } from '../../models/dashboard.model';

const MOCK_CARD: DashboardCard = {
  id: 42,
  card_type_code: 'bi_report',
  chart_type: 'bar',
  pos_x: 0,
  pos_y: 0,
  width: 3,
  height: 2,
  filtros_config: {},
  titulo_personalizado: '',
  orden: 0,
  bi_report_id: 'aaaabbbb-0000-0000-0000-000000000001',
  bi_report_titulo: 'Ventas por vendedor',
  bi_report_tipo_visualizacion: 'bar',
  bi_report_campos_config: [
    { source: 'facturacion', field: 'vendedor_nombre', role: 'dimension', label: 'Vendedor' },
    { source: 'facturacion', field: 'total', role: 'metric', label: 'Total', aggregation: 'SUM' },
  ],
};

const MOCK_RESULT = {
  columns: [{ field: 'vendedor_nombre', label: 'Vendedor', role: 'dimension' }],
  rows: [{ vendedor_nombre: 'Juan', total: 1000 }],
  total_count: 1,
};

describe('BiReportCardComponent', () => {
  let fixture: ComponentFixture<BiReportCardComponent>;
  let component: BiReportCardComponent;
  let service: jasmine.SpyObj<DashboardService>;

  beforeEach(async () => {
    const spy = jasmine.createSpyObj('DashboardService', ['executeBiCard']);

    await TestBed.configureTestingModule({
      imports: [BiReportCardComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        { provide: DashboardService, useValue: spy },
      ],
    }).compileComponents();

    service = TestBed.inject(DashboardService) as jasmine.SpyObj<DashboardService>;
    fixture = TestBed.createComponent(BiReportCardComponent);
    component = fixture.componentInstance;
  });

  it('muestra el título del reporte cuando no hay titulo_personalizado', () => {
    service.executeBiCard.and.returnValue(of(MOCK_RESULT));
    fixture.componentRef.setInput('card', MOCK_CARD);
    fixture.componentRef.setInput('dashboardId', 'dash-uuid-001');
    fixture.detectChanges();
    expect(component.cardTitle()).toBe('Ventas por vendedor');
  });

  it('usa titulo_personalizado si está definido', () => {
    service.executeBiCard.and.returnValue(of(MOCK_RESULT));
    const cardWithTitle = { ...MOCK_CARD, titulo_personalizado: 'Mi gráfico' };
    fixture.componentRef.setInput('card', cardWithTitle);
    fixture.componentRef.setInput('dashboardId', 'dash-uuid-001');
    fixture.detectChanges();
    expect(component.cardTitle()).toBe('Mi gráfico');
  });

  it('llama executeBiCard con los parámetros correctos', () => {
    service.executeBiCard.and.returnValue(of(MOCK_RESULT));
    fixture.componentRef.setInput('card', MOCK_CARD);
    fixture.componentRef.setInput('dashboardId', 'dash-uuid-001');
    fixture.componentRef.setInput('dashboardFilters', { fecha_desde: '2026-01-01' });
    fixture.detectChanges();
    expect(service.executeBiCard).toHaveBeenCalledWith(
      'dash-uuid-001',
      42,
      { fecha_desde: '2026-01-01' },
    );
  });

  it('muestra "no disponible" cuando no hay bi_report_id', () => {
    const cardWithoutReport = { ...MOCK_CARD, bi_report_id: null, bi_report_titulo: null };
    fixture.componentRef.setInput('card', cardWithoutReport);
    fixture.componentRef.setInput('dashboardId', 'dash-uuid-001');
    fixture.detectChanges();
    expect(component.reportNotAvailable()).toBeTrue();
    expect(service.executeBiCard).not.toHaveBeenCalled();
  });

  it('marca reportNotAvailable si la ejecución falla', () => {
    service.executeBiCard.and.returnValue(throwError(() => new Error('error')));
    fixture.componentRef.setInput('card', MOCK_CARD);
    fixture.componentRef.setInput('dashboardId', 'dash-uuid-001');
    fixture.detectChanges();
    expect(component.reportNotAvailable()).toBeTrue();
    expect(component.loading()).toBeFalse();
  });

  it('mapea campos_config a BIFieldConfig para el chart-renderer', () => {
    service.executeBiCard.and.returnValue(of(MOCK_RESULT));
    fixture.componentRef.setInput('card', MOCK_CARD);
    fixture.componentRef.setInput('dashboardId', 'dash-uuid-001');
    fixture.detectChanges();
    expect(component.campos().length).toBe(2);
    expect(component.campos()[0].field).toBe('vendedor_nombre');
  });

  it('refresh() recarga los datos', () => {
    service.executeBiCard.and.returnValue(of(MOCK_RESULT));
    fixture.componentRef.setInput('card', MOCK_CARD);
    fixture.componentRef.setInput('dashboardId', 'dash-uuid-001');
    fixture.detectChanges();
    expect(service.executeBiCard).toHaveBeenCalledTimes(1);
    component.refresh();
    expect(service.executeBiCard).toHaveBeenCalledTimes(2);
  });
});
