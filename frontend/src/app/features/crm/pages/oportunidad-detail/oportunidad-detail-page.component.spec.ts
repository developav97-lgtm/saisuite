/**
 * SaiSuite — OportunidadDetailPageComponent Spec
 * Cobertura ≥70% de lógica de componente.
 */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ActivatedRoute, provideRouter } from '@angular/router';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of, throwError } from 'rxjs';
import { MatDialog } from '@angular/material/dialog';

import { OportunidadDetailPageComponent } from './oportunidad-detail-page.component';
import { CrmService } from '../../services/crm.service';
import { ToastService } from '../../../../core/services/toast.service';
import { CrmOportunidad, CrmActividad, CrmTimelineEvent, CrmCotizacion } from '../../models/crm.model';

const mockOp: CrmOportunidad = {
  id: 'o1', titulo: 'Deal Test', pipeline: 'p1', pipeline_nombre: 'Ventas',
  etapa: 'e1', etapa_nombre: 'Prospecto', etapa_color: '#000',
  valor_esperado: '5000', probabilidad: '20', valor_ponderado: '1000',
  fecha_cierre_estimada: null, contacto: null, contacto_nombre: null,
  asignado_a: null, asignado_a_nombre: null,
  ganada_en: null, perdida_en: null, motivo_perdida: '',
  proxima_actividad_fecha: null, proxima_actividad_tipo: null,
  created_at: '2026-01-01', updated_at: '2026-01-01',
};

const mockActividad: CrmActividad = {
  id: 'a1', oportunidad: 'o1', tipo: 'llamada', titulo: 'Llamada inicial',
  descripcion: '', fecha_programada: '2026-04-20T10:00:00Z',
  completada: false, resultado: '', asignado_a: null, asignado_a_nombre: null,
  created_at: '2026-01-01',
};

const mockTimeline: CrmTimelineEvent = {
  id: 't1', tipo: 'nota', descripcion: 'Primera nota',
  usuario_nombre: 'Admin', metadata: {}, created_at: '2026-01-01',
};

const mockCotizacion: CrmCotizacion = {
  id: 'c1', numero_interno: 'COT-001', titulo: 'Cot 1', oportunidad: 'o1',
  estado: 'borrador', contacto: null, contacto_nombre: null,
  validez_dias: 30, fecha_vencimiento: null,
  subtotal: '0', descuento_adicional_p: '0', descuento_adicional_val: '0',
  total_iva: '0', total: '0', notas: '', terminos: '',
  sai_key: null, saiopen_synced: false, lineas: [],
  created_at: '2026-01-01', updated_at: '2026-01-01',
};

describe('OportunidadDetailPageComponent', () => {
  let fixture: ComponentFixture<OportunidadDetailPageComponent>;
  let component: OportunidadDetailPageComponent;
  let crmSpy: jasmine.SpyObj<CrmService>;
  let toastSpy: jasmine.SpyObj<ToastService>;
  let dialogSpy: jasmine.SpyObj<MatDialog>;

  beforeEach(async () => {
    crmSpy   = jasmine.createSpyObj('CrmService', [
      'getOportunidad', 'getTimeline', 'listActividades', 'listCotizaciones',
      'agregarNota', 'ganarOportunidad', 'perderOportunidad',
      'createCotizacion', 'completarActividad',
    ]);
    toastSpy = jasmine.createSpyObj('ToastService', ['error', 'success', 'info']);
    dialogSpy = jasmine.createSpyObj('MatDialog', ['open']);

    crmSpy.getOportunidad.and.returnValue(of(mockOp));
    crmSpy.getTimeline.and.returnValue(of([mockTimeline]));
    crmSpy.listActividades.and.returnValue(of([mockActividad]));
    crmSpy.listCotizaciones.and.returnValue(of([mockCotizacion]));
    crmSpy.agregarNota.and.returnValue(of(mockTimeline));
    crmSpy.ganarOportunidad.and.returnValue(of({ ...mockOp, ganada_en: '2026-01-02' }));
    crmSpy.perderOportunidad.and.returnValue(of({ ...mockOp, perdida_en: '2026-01-02' }));
    crmSpy.createCotizacion.and.returnValue(of(mockCotizacion));
    crmSpy.completarActividad.and.returnValue(of({ ...mockActividad, completada: true }));

    await TestBed.configureTestingModule({
      imports: [OportunidadDetailPageComponent, NoopAnimationsModule],
      providers: [
        provideHttpClient(), provideHttpClientTesting(),
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: { params: of({ id: 'o1' }) },
        },
        { provide: CrmService, useValue: crmSpy },
        { provide: ToastService, useValue: toastSpy },
        { provide: MatDialog, useValue: dialogSpy },
      ],
    }).compileComponents();

    fixture   = TestBed.createComponent(OportunidadDetailPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('crea el componente', () => {
    expect(component).toBeTruthy();
  });

  it('carga oportunidad, timeline, actividades y cotizaciones', () => {
    expect(crmSpy.getOportunidad).toHaveBeenCalledWith('o1');
    expect(component.oportunidad()?.id).toBe('o1');
    expect(component.timeline().length).toBe(1);
    expect(component.actividades().length).toBe(1);
    expect(component.cotizaciones().length).toBe(1);
    expect(component.loading()).toBeFalse();
  });

  it('tipoIconMap tiene entradas para todos los tipos', () => {
    expect(component.tipoIconMap['nota']).toBeTruthy();
    expect(component.tipoIconMap['cambio_etapa']).toBeTruthy();
  });

  it('agregarNota — sin llamar API si formulario inválido', () => {
    component.notaForm.reset();
    component.agregarNota();
    expect(crmSpy.agregarNota).not.toHaveBeenCalled();
  });

  it('agregarNota — llama API y prepend al timeline', () => {
    component.notaForm.setValue({ descripcion: 'Nota de prueba' });
    component.agregarNota();
    expect(crmSpy.agregarNota).toHaveBeenCalledWith('o1', 'Nota de prueba');
    expect(component.timeline()[0].id).toBe('t1');
    expect(component.addingNota()).toBeFalse();
  });

  it('agregarNota — maneja error', () => {
    crmSpy.agregarNota.and.returnValue(throwError(() => new Error('fail')));
    component.notaForm.setValue({ descripcion: 'Nota de prueba' });
    component.agregarNota();
    expect(toastSpy.error).toHaveBeenCalledWith('Error agregando nota');
    expect(component.addingNota()).toBeFalse();
  });

  it('ganar — actualiza oportunidad y muestra toast', () => {
    component.ganar();
    expect(crmSpy.ganarOportunidad).toHaveBeenCalledWith('o1');
    expect(toastSpy.success).toHaveBeenCalled();
  });

  it('ganar — maneja error', () => {
    crmSpy.ganarOportunidad.and.returnValue(throwError(() => ({ error: { detail: 'Sin etapa ganado' } })));
    component.ganar();
    expect(toastSpy.error).toHaveBeenCalledWith('Sin etapa ganado');
  });

  it('perder — abre dialog y llama API si hay motivo', () => {
    dialogSpy.open.and.returnValue({ afterClosed: () => of('Precio alto') } as never);
    component.perder();
    expect(dialogSpy.open).toHaveBeenCalled();
    expect(crmSpy.perderOportunidad).toHaveBeenCalledWith('o1', 'Precio alto');
  });

  it('perder — no llama API si dialog se cancela', () => {
    dialogSpy.open.and.returnValue({ afterClosed: () => of(undefined) } as never);
    component.perder();
    expect(crmSpy.perderOportunidad).not.toHaveBeenCalled();
  });

  it('openActividadDialog — abre dialog y agrega actividad al crear', () => {
    const newActividad = { ...mockActividad, id: 'a2' };
    dialogSpy.open.and.returnValue({ afterClosed: () => of(newActividad) } as never);
    component.openActividadDialog();
    expect(dialogSpy.open).toHaveBeenCalled();
    expect(component.actividades().some(a => a.id === 'a2')).toBeTrue();
    expect(toastSpy.success).toHaveBeenCalledWith('Actividad creada');
  });

  it('openActividadDialog — no modifica lista si dialog cancela', () => {
    dialogSpy.open.and.returnValue({ afterClosed: () => of(null) } as never);
    const prevLen = component.actividades().length;
    component.openActividadDialog();
    expect(component.actividades().length).toBe(prevLen);
  });

  it('completarActividad — abre dialog y actualiza actividad', () => {
    dialogSpy.open.and.returnValue({ afterClosed: () => of('Resultado OK') } as never);
    component.completarActividad(mockActividad);
    expect(crmSpy.completarActividad).toHaveBeenCalledWith('a1', 'Resultado OK');
    expect(toastSpy.success).toHaveBeenCalledWith('Actividad completada');
  });

  it('completarActividad — no llama API si resultado es undefined (cancel)', () => {
    dialogSpy.open.and.returnValue({ afterClosed: () => of(undefined) } as never);
    component.completarActividad(mockActividad);
    expect(crmSpy.completarActividad).not.toHaveBeenCalled();
  });

  it('createCotizacion — navega a /crm/cotizaciones/:id', () => {
    const routerSpy = spyOn(component['router'], 'navigate');
    component.createCotizacion();
    expect(crmSpy.createCotizacion).toHaveBeenCalled();
    expect(routerSpy).toHaveBeenCalledWith(['/crm/cotizaciones', 'c1']);
  });

  it('formatMoney formatea en COP', () => {
    expect(component.formatMoney('5000')).toContain('5.000');
  });

  it('goBack navega a /crm', () => {
    const routerSpy = spyOn(component['router'], 'navigate');
    component.goBack();
    expect(routerSpy).toHaveBeenCalledWith(['/crm']);
  });

  it('maneja error al cargar oportunidad', () => {
    crmSpy.getOportunidad.and.returnValue(throwError(() => new Error('fail')));
    component.ngOnInit();
    expect(toastSpy.error).toHaveBeenCalledWith('Error cargando oportunidad');
    expect(component.loading()).toBeFalse();
  });

  it('ngOnDestroy completa destroy$', () => {
    spyOn(component['destroy$'], 'next');
    spyOn(component['destroy$'], 'complete');
    component.ngOnDestroy();
    expect(component['destroy$'].next).toHaveBeenCalled();
    expect(component['destroy$'].complete).toHaveBeenCalled();
  });
});
