import { Injectable } from '@angular/core';
import { BIFieldFormat } from '../models/bi-field.model';

/** Definición guardada de un campo calculado (plantilla reutilizable por fuente). */
export interface CalcFieldTemplate {
  id: string;
  label: string;
  formula: string;
  format: BIFieldFormat;
}

/**
 * Persiste definiciones de campos calculados en localStorage,
 * organizadas por clave de fuente (ej: 'gl', 'facturacion').
 * No usa backend — es configuración personal del usuario en el navegador.
 */
@Injectable({ providedIn: 'root' })
export class CalcFieldStoreService {
  private key(source: string): string {
    return `saidash_calc_${source}`;
  }

  getTemplates(source: string): CalcFieldTemplate[] {
    try {
      const raw = localStorage.getItem(this.key(source));
      return raw ? (JSON.parse(raw) as CalcFieldTemplate[]) : [];
    } catch {
      return [];
    }
  }

  saveTemplate(source: string, template: CalcFieldTemplate): void {
    const all = this.getTemplates(source);
    const idx = all.findIndex(t => t.id === template.id);
    if (idx >= 0) {
      all[idx] = template;
    } else {
      all.push(template);
    }
    localStorage.setItem(this.key(source), JSON.stringify(all));
  }

  removeTemplate(source: string, id: string): void {
    const remaining = this.getTemplates(source).filter(t => t.id !== id);
    localStorage.setItem(this.key(source), JSON.stringify(remaining));
  }
}
