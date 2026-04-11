import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { RouterTestingModule } from '@angular/router/testing';
import { MatDialogModule } from '@angular/material/dialog';
import { of } from 'rxjs';
import { ReportListComponent } from './report-list.component';
import { ReportBIService } from '../../services/report-bi.service';
import { ToastService } from '../../../../core/services/toast.service';
import { ReportBIListItem } from '../../models/report-bi.model';

describe('ReportListComponent', () => {
  let fixture: ComponentFixture<ReportListComponent>;
  let component: ReportListComponent;
  let serviceSpy: jasmine.SpyObj<ReportBIService>;

  const mockReports: ReportBIListItem[] = [
    {
      id: 'r1', titulo: 'Balance Q1', descripcion: 'Balance trimestral',
      es_privado: false, es_favorito: true, es_template: false,
      fuentes: ['gl'], tipo_visualizacion: 'table',
      user_email: 'test@test.com', created_at: '2026-04-10', updated_at: '2026-04-10',
    },
    {
      id: 'r2', titulo: 'Ventas por Vendedor', descripcion: '',
      es_privado: true, es_favorito: false, es_template: false,
      fuentes: ['facturacion'], tipo_visualizacion: 'pivot',
      user_email: 'test@test.com', created_at: '2026-04-09', updated_at: '2026-04-09',
    },
  ];

  beforeEach(() => {
    serviceSpy = jasmine.createSpyObj('ReportBIService', [
      'list', 'getTemplates', 'toggleFavorite', 'delete',
    ]);
    serviceSpy.list.and.returnValue(of(mockReports));
    serviceSpy.getTemplates.and.returnValue(of([]));

    TestBed.configureTestingModule({
      imports: [
        ReportListComponent,
        HttpClientTestingModule,
        NoopAnimationsModule,
        RouterTestingModule,
        MatDialogModule,
      ],
      providers: [
        { provide: ReportBIService, useValue: serviceSpy },
        { provide: ToastService, useValue: jasmine.createSpyObj('ToastService', ['success', 'error', 'info']) },
      ],
    });

    fixture = TestBed.createComponent(ReportListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('loads reports on init', () => {
    expect(serviceSpy.list).toHaveBeenCalled();
    expect(component.reports().length).toBe(2);
  });

  it('loads templates on init', () => {
    expect(serviceSpy.getTemplates).toHaveBeenCalled();
  });

  it('filtered reports matches search', () => {
    component.searchText.set('Balance');
    expect(component.filteredReports().length).toBe(1);
    expect(component.filteredReports()[0].id).toBe('r1');
  });

  it('filtered reports returns empty on no match', () => {
    component.searchText.set('xyz_no_match');
    expect(component.filteredReports().length).toBe(0);
  });

  it('favoritos computed returns only favorites', () => {
    expect(component.favoritos().length).toBe(1);
    expect(component.favoritos()[0].id).toBe('r1');
  });

  it('toggleFavorite calls service', () => {
    serviceSpy.toggleFavorite.and.returnValue(of({ es_favorito: false }));
    const fakeEvent = new MouseEvent('click');
    spyOn(fakeEvent, 'stopPropagation');
    component.toggleFavorite(mockReports[0], fakeEvent);
    expect(serviceSpy.toggleFavorite).toHaveBeenCalledWith('r1');
  });

  it('getVizLabel returns correct label', () => {
    expect(component.getVizLabel('table')).toBe('Tabla');
    expect(component.getVizLabel('pivot')).toBe('Tabla Dinámica');
  });

  it('getSourceLabels returns correct labels', () => {
    const labels = component.getSourceLabels(['gl', 'cartera']);
    expect(labels).toContain('Contabilidad (GL)');
    expect(labels).toContain('Cartera (CxC/CxP)');
  });
});
