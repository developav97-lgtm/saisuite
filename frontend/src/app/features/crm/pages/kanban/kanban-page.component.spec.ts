/**
 * SaiSuite — KanbanPageComponent Spec
 * Cobertura ≥70% de lógica de componente.
 */
import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of, throwError } from 'rxjs';

import { KanbanPageComponent } from './kanban-page.component';
import { CrmService } from '../../services/crm.service';
import { ToastService } from '../../../../core/services/toast.service';
import { CrmOportunidad, CrmPipeline, KanbanColumna, KanbanOportunidad } from '../../models/crm.model';

const mockOp: KanbanOportunidad = {
  id: 'op1', titulo: 'Deal 1', contacto_nombre: null, valor_esperado: '1000',
  probabilidad: '20', asignado_a_nombre: null,
  proxima_actividad_tipo: null, proxima_actividad_fecha: null, created_at: '2026-01-01',
};

const mockEtapa = { id: 'e1', nombre: 'Prospecto', orden: 1, color: '#000', probabilidad: '10', es_ganado: false, es_perdido: false };
const mockPipeline: CrmPipeline = { id: 'p1', nombre: 'Ventas', es_default: true, etapas: [mockEtapa], created_at: '2026-01-01' };

const mockOportunidad: CrmOportunidad = {
  id: 'op1', titulo: 'Deal 1', pipeline: 'p1', pipeline_nombre: 'Ventas',
  etapa: 'e1', etapa_nombre: 'Prospecto', etapa_color: '#000',
  valor_esperado: '1000', probabilidad: '20', valor_ponderado: '200',
  fecha_cierre_estimada: null, contacto: null, contacto_nombre: null,
  asignado_a: null, asignado_a_nombre: null,
  ganada_en: null, perdida_en: null, motivo_perdida: '',
  proxima_actividad_fecha: null, proxima_actividad_tipo: null,
  created_at: '2026-01-01', updated_at: '2026-01-01',
};

const mockColumna: KanbanColumna = {
  etapa_id: 'e1', etapa_nombre: 'Prospecto', color: '#000', probabilidad: '10',
  es_ganado: false, es_perdido: false,
  oportunidades: [mockOp], total_count: 1, total_valor: '1000',
};

describe('KanbanPageComponent', () => {
  let fixture: ComponentFixture<KanbanPageComponent>;
  let component: KanbanPageComponent;
  let crmSpy: jasmine.SpyObj<CrmService>;
  let toastSpy: jasmine.SpyObj<ToastService>;

  beforeEach(async () => {
    crmSpy   = jasmine.createSpyObj('CrmService', ['listPipelines', 'getKanban', 'moverEtapa']);
    toastSpy = jasmine.createSpyObj('ToastService', ['error', 'success', 'info']);

    crmSpy.listPipelines.and.returnValue(of([mockPipeline]));
    crmSpy.getKanban.and.returnValue(of([mockColumna]));
    crmSpy.moverEtapa.and.returnValue(of(mockOportunidad));

    await TestBed.configureTestingModule({
      imports: [KanbanPageComponent, NoopAnimationsModule],
      providers: [
        provideHttpClient(), provideHttpClientTesting(),
        provideRouter([]),
        { provide: CrmService, useValue: crmSpy },
        { provide: ToastService, useValue: toastSpy },
      ],
    }).compileComponents();

    fixture   = TestBed.createComponent(KanbanPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('crea el componente', () => {
    expect(component).toBeTruthy();
  });

  it('carga pipelines en ngOnInit', () => {
    expect(crmSpy.listPipelines).toHaveBeenCalled();
    expect(component.pipelines().length).toBe(1);
  });

  it('carga kanban del pipeline default', () => {
    expect(crmSpy.getKanban).toHaveBeenCalledWith('p1');
    expect(component.columnas().length).toBe(1);
  });

  it('selectedPipelineId se inicializa con el pipeline default', () => {
    expect(component.selectedPipelineId()).toBe('p1');
  });

  it('connectedLists computed genera lista de IDs de etapa', () => {
    expect(component.connectedLists()).toEqual(['etapa-e1']);
  });

  it('onPipelineChange carga nuevo kanban', () => {
    crmSpy.getKanban.and.returnValue(of([]));
    component.onPipelineChange('p2');
    expect(component.selectedPipelineId()).toBe('p2');
    expect(crmSpy.getKanban).toHaveBeenCalledWith('p2');
  });

  it('formatMoney formatea correctamente en COP', () => {
    const result = component.formatMoney('1000000');
    expect(result).toContain('1.000.000');
  });

  it('formatMoney maneja valor vacío', () => {
    const result = component.formatMoney('');
    expect(result).toContain('0');
  });

  it('maneja error al cargar pipelines', () => {
    crmSpy.listPipelines.and.returnValue(throwError(() => new Error('fail')));
    component.ngOnInit();
    expect(toastSpy.error).toHaveBeenCalledWith('Error cargando pipelines');
  });

  it('maneja error al cargar kanban', () => {
    crmSpy.getKanban.and.returnValue(throwError(() => new Error('fail')));
    component['loadKanban']('p1');
    expect(toastSpy.error).toHaveBeenCalledWith('Error cargando kanban');
    expect(component.loading()).toBeFalse();
  });

  it('onCardDrop — mismo contenedor reordena sin llamar API', () => {
    const container = { element: { nativeElement: document.createElement('div') } } as never;
    const event = {
      previousContainer: container,
      container: container,
      previousIndex: 0,
      currentIndex: 0,
    } as never;
    component.onCardDrop(event, mockColumna);
    expect(crmSpy.moverEtapa).not.toHaveBeenCalled();
  });

  it('ngOnDestroy completa destroy$', () => {
    spyOn(component['destroy$'], 'next');
    spyOn(component['destroy$'], 'complete');
    component.ngOnDestroy();
    expect(component['destroy$'].next).toHaveBeenCalled();
    expect(component['destroy$'].complete).toHaveBeenCalled();
  });
});
