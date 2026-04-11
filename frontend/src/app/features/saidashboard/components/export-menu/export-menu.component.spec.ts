import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ExportMenuComponent } from './export-menu.component';
import { ReportBITableResult } from '../../models/report-bi.model';
import { ToastService } from '../../../../core/services/toast.service';

describe('ExportMenuComponent', () => {
  let component: ExportMenuComponent;
  let fixture: ComponentFixture<ExportMenuComponent>;
  let toastSpy: jasmine.SpyObj<ToastService>;

  const mockData: ReportBITableResult = {
    columns: ['cuenta', 'debito', 'credito'],
    rows: [
      { cuenta: '4101', debito: 1000, credito: 0 },
      { cuenta: '4102', debito: 0, credito: 500 },
    ],
    total_count: 2,
  };

  beforeEach(async () => {
    toastSpy = jasmine.createSpyObj('ToastService', ['success', 'error']);

    await TestBed.configureTestingModule({
      imports: [ExportMenuComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: ToastService, useValue: toastSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ExportMenuComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should disable button when no data', () => {
    fixture.detectChanges();
    const btn = fixture.nativeElement.querySelector('button') as HTMLButtonElement;
    expect(btn.disabled).toBeTrue();
  });

  it('should enable button when data is provided', () => {
    fixture.componentRef.setInput('data', mockData);
    fixture.detectChanges();
    const btn = fixture.nativeElement.querySelector('button') as HTMLButtonElement;
    expect(btn.disabled).toBeFalse();
  });

  it('should export CSV and show toast', () => {
    fixture.componentRef.setInput('data', mockData);
    fixture.componentRef.setInput('title', 'Test Report');
    fixture.detectChanges();

    component.exportCsv();
    expect(toastSpy.success).toHaveBeenCalledWith('Archivo CSV descargado.');
  });

  it('should show error for CSV on non-table data', () => {
    const pivotData = {
      row_headers: [],
      col_headers: [],
      data: {},
      row_totals: {},
      col_totals: {},
      grand_total: {},
      value_aliases: [],
    };
    fixture.componentRef.setInput('data', pivotData);
    fixture.detectChanges();
    component.exportCsv();
    expect(toastSpy.error).toHaveBeenCalledWith('Solo se puede exportar CSV en vista de tabla.');
  });

  it('should show error when exporting PDF without reportId', () => {
    fixture.componentRef.setInput('data', mockData);
    fixture.detectChanges();
    component.exportPdf();
    expect(toastSpy.error).toHaveBeenCalledWith('Guarda el reporte antes de exportar a PDF.');
  });
});
