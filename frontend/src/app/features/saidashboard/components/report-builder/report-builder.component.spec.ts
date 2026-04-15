import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { RouterTestingModule } from '@angular/router/testing';
import { of } from 'rxjs';
import { ReportBuilderComponent } from './report-builder.component';
import { ReportBIService } from '../../services/report-bi.service';
import { ToastService } from '../../../../core/services/toast.service';

describe('ReportBuilderComponent', () => {
  let fixture: ComponentFixture<ReportBuilderComponent>;
  let component: ReportBuilderComponent;
  let serviceSpy: jasmine.SpyObj<ReportBIService>;

  beforeEach(() => {
    serviceSpy = jasmine.createSpyObj('ReportBIService', [
      'list', 'getById', 'create', 'update', 'preview',
      'getFields', 'getFilters', 'getSources', 'getJoins',
    ]);
    serviceSpy.getFields.and.returnValue(of({}));
    serviceSpy.getFilters.and.returnValue(of([]));
    serviceSpy.getJoins.and.returnValue(of([]));

    TestBed.configureTestingModule({
      imports: [
        ReportBuilderComponent,
        HttpClientTestingModule,
        NoopAnimationsModule,
        RouterTestingModule,
      ],
      providers: [
        { provide: ReportBIService, useValue: serviceSpy },
        { provide: ToastService, useValue: jasmine.createSpyObj('ToastService', ['success', 'error', 'info']) },
      ],
    });

    fixture = TestBed.createComponent(ReportBuilderComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('canPreview is false when no sources/fields', () => {
    expect(component.canPreview()).toBeFalse();
  });

  it('canPreview is true when sources and fields selected', () => {
    component.selectedSources.set(['gl']);
    component.selectedFields.set([
      { source: 'gl', field: 'debito', role: 'metric', aggregation: 'SUM', label: 'Débito' },
    ]);
    expect(component.canPreview()).toBeTrue();
  });

  it('canSave is false without titulo', () => {
    component.selectedSources.set(['gl']);
    component.selectedFields.set([
      { source: 'gl', field: 'debito', role: 'metric', aggregation: 'SUM', label: 'Débito' },
    ]);
    expect(component.canSave()).toBeFalse();
  });

  it('canSave is true with titulo + sources + fields', () => {
    component.titulo.set('Test Report');
    component.selectedSources.set(['gl']);
    component.selectedFields.set([
      { source: 'gl', field: 'debito', role: 'metric', aggregation: 'SUM', label: 'Débito' },
    ]);
    expect(component.canSave()).toBeTrue();
  });

  it('onSourcesChange clears fields from deselected sources', () => {
    component.selectedFields.set([
      { source: 'gl', field: 'debito', role: 'metric', aggregation: 'SUM', label: 'Débito' },
      { source: 'cartera', field: 'saldo', role: 'metric', aggregation: 'SUM', label: 'Saldo' },
    ]);
    component.onSourcesChange(['gl']);
    expect(component.selectedFields().length).toBe(1);
    expect(component.selectedFields()[0].source).toBe('gl');
  });

  it('preview calls service with current config', () => {
    serviceSpy.preview.and.returnValue(of({ columns: [{ field: 'debito', label: 'Débito', type: 'metric' }], rows: [], total_count: 0 } as any));
    component.selectedSources.set(['gl']);
    component.selectedFields.set([
      { source: 'gl', field: 'debito', role: 'metric', aggregation: 'SUM', label: 'Débito' },
    ]);
    component.preview();
    expect(serviceSpy.preview).toHaveBeenCalled();
  });
});
