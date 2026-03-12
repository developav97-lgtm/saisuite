// frontend/src/app/features/configuracion/configuracion-placeholder.component.ts
import { Component, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
    selector: 'app-configuracion-placeholder',
    standalone: true,
    imports: [CommonModule],
    template: `
    <div class="sc-page-header"><h2>Configuración</h2></div>
    <div class="sc-page-card">
      <p>Módulo de Configuración — por implementar.</p>
    </div>
  `,
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ConfiguracionPlaceholderComponent { }