import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { RouterTestingModule } from '@angular/router/testing';
import { MatDialogModule } from '@angular/material/dialog';
import { of } from 'rxjs';
import { DashboardListComponent } from './dashboard-list.component';
import { DashboardService } from '../../services/dashboard.service';
import { TrialService } from '../../services/trial.service';
import { ToastService } from '../../../../core/services/toast.service';

describe('DashboardListComponent', () => {
  let fixture: ComponentFixture<DashboardListComponent>;
  let component: DashboardListComponent;
  let dashboardServiceSpy: jasmine.SpyObj<DashboardService>;
  let trialServiceSpy: jasmine.SpyObj<TrialService>;

  const mockTrial = { tiene_acceso: true, tipo_acceso: 'licensed' as const, dias_restantes: 0, expira_en: null };
  const mockDashboards = [
    { id: 'd1', titulo: 'Dashboard 1', descripcion: '', es_privado: false, es_favorito: false, es_default: false, orientacion: 'horizontal', user_email: 'test@test.com', card_count: 0, created_at: '' },
  ];

  beforeEach(() => {
    dashboardServiceSpy = jasmine.createSpyObj('DashboardService', ['list', 'getSharedWithMe', 'delete', 'setDefault', 'toggleFavorite']);
    trialServiceSpy     = jasmine.createSpyObj('TrialService', ['getStatus', 'activate']);

    dashboardServiceSpy.list.and.returnValue(of(mockDashboards as any));
    dashboardServiceSpy.getSharedWithMe.and.returnValue(of([]));
    trialServiceSpy.getStatus.and.returnValue(of(mockTrial as any));

    TestBed.configureTestingModule({
      imports: [
        DashboardListComponent,
        HttpClientTestingModule,
        NoopAnimationsModule,
        RouterTestingModule,
        MatDialogModule,
      ],
      providers: [
        { provide: DashboardService, useValue: dashboardServiceSpy },
        { provide: TrialService, useValue: trialServiceSpy },
        { provide: ToastService, useValue: jasmine.createSpyObj('ToastService', ['success', 'error', 'info']) },
      ],
    });

    fixture   = TestBed.createComponent(DashboardListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('loads dashboards on init', () => {
    expect(dashboardServiceSpy.list).toHaveBeenCalled();
    expect(component.dashboards().length).toBe(1);
  });

  it('loads trial status on init', () => {
    expect(trialServiceSpy.getStatus).toHaveBeenCalled();
  });

  it('filtered dashboards matches search', () => {
    component.searchText.set('Dashboard 1');
    expect(component.filteredDashboards().length).toBe(1);
  });

  it('filtered dashboards returns empty on no match', () => {
    component.searchText.set('xyz_no_match');
    expect(component.filteredDashboards().length).toBe(0);
  });

  it('toggleFavorite calls service', () => {
    dashboardServiceSpy.toggleFavorite.and.returnValue(of({ es_favorito: true }));
    const fakeEvent = new MouseEvent('click');
    spyOn(fakeEvent, 'stopPropagation');
    component.toggleFavorite(mockDashboards[0] as any, fakeEvent);
    expect(dashboardServiceSpy.toggleFavorite).toHaveBeenCalledWith('d1');
  });
});
