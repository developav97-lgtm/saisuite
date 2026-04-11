import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SourceSelectorComponent } from './source-selector.component';
import { BI_SOURCES } from '../../models/bi-source.model';

describe('SourceSelectorComponent', () => {
  let fixture: ComponentFixture<SourceSelectorComponent>;
  let component: SourceSelectorComponent;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [SourceSelectorComponent],
    });
    fixture = TestBed.createComponent(SourceSelectorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('renders all BI sources', () => {
    expect(component.sources.length).toBe(BI_SOURCES.length);
  });

  it('isSelected returns false when nothing selected', () => {
    expect(component.isSelected('gl')).toBeFalse();
  });

  it('toggle emits new selection', () => {
    spyOn(component.selectionChange, 'emit');
    component.toggle('gl');
    expect(component.selectionChange.emit).toHaveBeenCalledWith(['gl']);
  });

  it('toggle removes already selected source', () => {
    fixture.componentRef.setInput('selected', ['gl', 'cartera']);
    fixture.detectChanges();

    spyOn(component.selectionChange, 'emit');
    component.toggle('gl');
    expect(component.selectionChange.emit).toHaveBeenCalledWith(['cartera']);
  });

  it('isSelected returns true for selected sources', () => {
    fixture.componentRef.setInput('selected', ['gl']);
    fixture.detectChanges();
    expect(component.isSelected('gl')).toBeTrue();
    expect(component.isSelected('cartera')).toBeFalse();
  });
});
