import { ComponentFixture, TestBed } from '@angular/core/testing';
import { PivotTableComponent } from './pivot-table.component';
import { ReportBIPivotResult } from '../../models/report-bi.model';

describe('PivotTableComponent', () => {
  let component: PivotTableComponent;
  let fixture: ComponentFixture<PivotTableComponent>;

  const mockPivotData: ReportBIPivotResult = {
    row_headers: [
      { cuenta: '4101' },
      { cuenta: '4102' },
    ],
    col_headers: [
      { periodo: '2026-01' },
      { periodo: '2026-02' },
    ],
    data: {
      '4101___2026-01': { total_sum: 1000 },
      '4101___2026-02': { total_sum: 1500 },
      '4102___2026-01': { total_sum: 800 },
      '4102___2026-02': { total_sum: 1200 },
    },
    row_totals: {
      '4101': { total_sum: 2500 },
      '4102': { total_sum: 2000 },
    },
    col_totals: {
      '2026-01': { total_sum: 1800 },
      '2026-02': { total_sum: 2700 },
    },
    grand_total: { total_sum: 4500 },
    value_aliases: ['total_sum'],
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PivotTableComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(PivotTableComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should show empty state when no data', () => {
    fixture.detectChanges();
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('.sc-empty-state')).toBeTruthy();
  });

  it('should compute row dimension fields', () => {
    fixture.componentRef.setInput('data', mockPivotData);
    fixture.detectChanges();
    expect(component.rowDimFields()).toEqual(['cuenta']);
  });

  it('should compute column keys', () => {
    fixture.componentRef.setInput('data', mockPivotData);
    fixture.detectChanges();
    expect(component.colKeys()).toEqual(['2026-01', '2026-02']);
  });

  it('should return cell value', () => {
    fixture.componentRef.setInput('data', mockPivotData);
    fixture.detectChanges();
    expect(component.getCellValue('4101', '2026-01')).toBe(1000);
    expect(component.getCellValue('4101', '2026-02')).toBe(1500);
    expect(component.getCellValue('9999', '2026-01')).toBeNull();
  });

  it('should return row totals', () => {
    fixture.componentRef.setInput('data', mockPivotData);
    fixture.detectChanges();
    expect(component.getRowTotal('4101')).toBe(2500);
    expect(component.getRowTotal('4102')).toBe(2000);
  });

  it('should return column totals', () => {
    fixture.componentRef.setInput('data', mockPivotData);
    fixture.detectChanges();
    expect(component.getColTotal('2026-01')).toBe(1800);
    expect(component.getColTotal('2026-02')).toBe(2700);
  });

  it('should return grand total', () => {
    fixture.componentRef.setInput('data', mockPivotData);
    fixture.detectChanges();
    expect(component.getGrandTotal()).toBe(4500);
  });

  it('should emit cellClick on cell click', () => {
    fixture.componentRef.setInput('data', mockPivotData);
    fixture.detectChanges();
    const spy = spyOn(component.cellClick, 'emit');
    component.onCellClick('4101', '2026-01', 1000);
    expect(spy).toHaveBeenCalledWith(jasmine.objectContaining({
      rowKey: '4101',
      colKey: '2026-01',
      value: 1000,
    }));
  });

  it('should not emit cellClick for null values', () => {
    fixture.componentRef.setInput('data', mockPivotData);
    fixture.detectChanges();
    const spy = spyOn(component.cellClick, 'emit');
    component.onCellClick('9999', '2026-01', null);
    expect(spy).not.toHaveBeenCalled();
  });

  it('should render table with pivot data', () => {
    fixture.componentRef.setInput('data', mockPivotData);
    fixture.detectChanges();
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('.pivot-table')).toBeTruthy();
    const headers = el.querySelectorAll('.pivot-table__col-header');
    // 2 col headers + 1 Total
    expect(headers.length).toBe(3);
  });
});
