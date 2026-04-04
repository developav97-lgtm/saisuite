/**
 * SaiSuite — ResponsiveTableDirective
 * Envuelve automáticamente una tabla mat-table en un div.table-responsive
 * para habilitar scroll horizontal en pantallas pequeñas.
 *
 * Uso: <mat-table appResponsiveTable ...>
 */
import { AfterViewInit, Directive, ElementRef, Renderer2, inject } from '@angular/core';

@Directive({
  selector: '[appResponsiveTable]',
  standalone: true,
})
export class ResponsiveTableDirective implements AfterViewInit {
  private readonly el       = inject(ElementRef);
  private readonly renderer = inject(Renderer2);

  ngAfterViewInit(): void {
    const table: HTMLElement = this.el.nativeElement;
    const parent = table.parentNode;

    if (!parent) return;

    const wrapper = this.renderer.createElement('div') as HTMLElement;
    this.renderer.addClass(wrapper, 'table-responsive');

    // Insertar el wrapper antes de la tabla en el DOM
    this.renderer.insertBefore(parent, wrapper, table);
    // Mover la tabla dentro del wrapper
    this.renderer.appendChild(wrapper, table);
  }
}
