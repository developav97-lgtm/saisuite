/**
 * SaiSuite — ScMoneyInputDirective
 * Directiva para inputs de dinero (COP).
 * - Al hacer focus: muestra el número sin formato (ej: 1000000)
 * - Al hacer blur: muestra con separadores de miles (ej: 1.000.000)
 * - El valor del FormControl siempre es el número crudo como string.
 *
 * Uso: <input matInput scMoneyInput formControlName="valor_esperado" />
 */
import {
  Directive, ElementRef, OnInit, inject,
} from '@angular/core';
import { NgControl } from '@angular/forms';

@Directive({
  selector: 'input[scMoneyInput]',
  standalone: true,
  host: {
    inputmode: 'numeric',
    autocomplete: 'off',
    '(focus)': 'onFocus()',
    '(blur)': 'onBlur()',
    '(input)': 'onInput($event)',
  },
})
export class ScMoneyInputDirective implements OnInit {
  private readonly el    = inject(ElementRef<HTMLInputElement>);
  private readonly ctrl  = inject(NgControl, { optional: true });

  private format(value: string | number | null | undefined): string {
    const num = parseFloat(String(value ?? '0').replace(/\./g, '').replace(',', '.'));
    if (isNaN(num)) return '';
    return new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 }).format(num);
  }

  private strip(display: string): string {
    return display.replace(/\./g, '').replace(',', '.').trim();
  }

  ngOnInit(): void {
    const raw = this.ctrl?.value ?? this.el.nativeElement.value;
    this.el.nativeElement.value = this.format(raw);
  }

  onFocus(): void {
    const raw = this.strip(this.el.nativeElement.value);
    this.el.nativeElement.value = raw === '0' ? '' : raw;
  }

  onBlur(): void {
    const raw = this.strip(this.el.nativeElement.value);
    const num = parseFloat(raw || '0');
    const formatted = this.format(isNaN(num) ? 0 : num);
    this.el.nativeElement.value = formatted;
    if (this.ctrl?.control) {
      this.ctrl.control.setValue(isNaN(num) ? '0' : String(Math.round(num)), { emitEvent: true });
    }
  }

  onInput(event: Event): void {
    const displayValue = (event.target as HTMLInputElement).value;
    const raw = displayValue.replace(/[^\d]/g, '');
    if (this.ctrl?.control) {
      this.ctrl.control.setValue(raw || '0', { emitEvent: true, emitModelToViewChange: false });
    }
  }
}
