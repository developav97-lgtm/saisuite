import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Chart, registerables } from 'chart.js';
import { provideHttpClient } from '@angular/common/http';

Chart.register(...registerables);
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { ActivatedRoute } from '@angular/router';
import { ReportViewerComponent } from './report-viewer.component';
import { ToastService } from '../../../../core/services/toast.service';
import { ReportBIDetail } from '../../models/report-bi.model';

describe('ReportViewerComponent', () => {
  let component: ReportViewerComponent;
  let fixture: ComponentFixture<ReportViewerComponent>;
  let httpMock: HttpTestingController;

  const mockReport: ReportBIDetail = {
    id: '00000000-0000-0000-0000-000000000001',
    titulo: 'Test Report',
    descripcion: 'A test',
    es_privado: false,
    es_favorito: false,
    es_template: false,
    fuentes: ['gl'],
    campos_config: [
      { source: 'gl', field: 'periodo', role: 'dimension', label: 'Período' },
      { source: 'gl', field: 'debito', role: 'metric', aggregation: 'SUM', label: 'Débito' },
    ],
    tipo_visualizacion: 'table',
    viz_config: {},
    filtros: {},
    orden_config: [],
    limite_registros: null,
    template_origen: null,
    categoria_galeria: null,
    user: { id: 'u1', email: 'test@test.com', full_name: 'Test User' },
    shares: [],
    created_at: '2026-04-10T00:00:00Z',
    updated_at: '2026-04-10T00:00:00Z',
  };

  const mockResult = {
    columns: ['periodo', 'debito_sum'],
    rows: [{ periodo: '2026-01', debito_sum: 5000 }],
    total_count: 1,
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ReportViewerComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: { paramMap: { get: (key: string) => '00000000-0000-0000-0000-000000000001' } },
          },
        },
        { provide: ToastService, useValue: jasmine.createSpyObj('ToastService', ['success', 'error']) },
      ],
    }).compileComponents();

    httpMock = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(ReportViewerComponent);
    component = fixture.componentInstance;
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should create and start loading', () => {
    expect(component).toBeTruthy();
    fixture.detectChanges();

    // Answer the getById request
    const getReq = httpMock.expectOne(r => r.url.includes('/reportes/00000000'));
    getReq.flush(mockReport);

    // Answer the execute request
    const execReq = httpMock.expectOne(r => r.url.includes('/execute/'));
    execReq.flush(mockResult);

    expect(component.report()).toBeTruthy();
    expect(component.result()).toBeTruthy();
  });

  it('should show table visualization', () => {
    fixture.detectChanges();
    const getReq = httpMock.expectOne(r => r.url.includes('/reportes/00000000'));
    getReq.flush(mockReport);
    const execReq = httpMock.expectOne(r => r.url.includes('/execute/'));
    execReq.flush(mockResult);

    fixture.detectChanges();
    expect(component.isTable()).toBeTrue();
    expect(component.isPivot()).toBeFalse();
    expect(component.isChart()).toBeFalse();
  });

  it('should detect chart visualization', () => {
    fixture.detectChanges();
    const chartReport = { ...mockReport, tipo_visualizacion: 'bar' as const };
    const getReq = httpMock.expectOne(r => r.url.includes('/reportes/00000000'));
    getReq.flush(chartReport);
    const execReq = httpMock.expectOne(r => r.url.includes('/execute/'));
    execReq.flush(mockResult);

    fixture.detectChanges();
    expect(component.isChart()).toBeTrue();
  });

  it('should toggle favorite', () => {
    fixture.detectChanges();
    const getReq = httpMock.expectOne(r => r.url.includes('/reportes/00000000'));
    getReq.flush(mockReport);
    const execReq = httpMock.expectOne(r => r.url.includes('/execute/'));
    execReq.flush(mockResult);

    component.toggleFavorite();
    const favReq = httpMock.expectOne(r => r.url.includes('/toggle-favorite/'));
    favReq.flush({ es_favorito: true });

    expect(component.report()!.es_favorito).toBeTrue();
  });

  it('should close drill-down panel', () => {
    component.drillDown.set({
      title: 'Test',
      filters: {},
      columns: [],
      rows: [],
      loading: false,
    });
    component.closeDrillDown();
    expect(component.drillDown()).toBeNull();
  });
});
