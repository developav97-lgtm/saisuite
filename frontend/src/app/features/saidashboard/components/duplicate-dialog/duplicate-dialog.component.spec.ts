import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { DuplicateDialogComponent, DuplicateDialogData } from './duplicate-dialog.component';

describe('DuplicateDialogComponent', () => {
  let fixture: ComponentFixture<DuplicateDialogComponent>;
  let component: DuplicateDialogComponent;
  let dialogRefSpy: jasmine.SpyObj<MatDialogRef<DuplicateDialogComponent>>;

  const dialogData: DuplicateDialogData = { reportTitle: 'Ventas por Vendedor' };

  beforeEach(async () => {
    dialogRefSpy = jasmine.createSpyObj('MatDialogRef', ['close']);

    await TestBed.configureTestingModule({
      imports: [DuplicateDialogComponent],
      providers: [
        provideAnimationsAsync(),
        { provide: MAT_DIALOG_DATA, useValue: dialogData },
        { provide: MatDialogRef, useValue: dialogRefSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(DuplicateDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('prellea el título con "(copia)" appended', () => {
    expect(component.titulo).toBe('Ventas por Vendedor (copia)');
  });

  it('confirm closes dialog with titulo result', () => {
    component.titulo = 'Mi copia personalizada';
    component.confirm();
    expect(dialogRefSpy.close).toHaveBeenCalledWith({ titulo: 'Mi copia personalizada' });
  });

  it('confirm trims whitespace from titulo', () => {
    component.titulo = '  Reporte limpio  ';
    component.confirm();
    expect(dialogRefSpy.close).toHaveBeenCalledWith({ titulo: 'Reporte limpio' });
  });

  it('confirm does nothing if titulo is blank', () => {
    component.titulo = '   ';
    component.confirm();
    expect(dialogRefSpy.close).not.toHaveBeenCalled();
  });

  it('cancel closes dialog with undefined', () => {
    component.cancel();
    expect(dialogRefSpy.close).toHaveBeenCalledWith(undefined);
  });
});
