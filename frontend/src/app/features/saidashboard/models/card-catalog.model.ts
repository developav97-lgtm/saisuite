/** Card catalog models — mirrors backend DRF catalog endpoints. */

import { ChartType } from './dashboard.model';

export interface CardCatalogItem {
  code: string;
  nombre: string;
  categoria: string;
  descripcion: string;
  chart_types: ChartType[];
  chart_default: ChartType;
  color: string;
  icono: string;
  requiere: string[];
  /** Si true, la tarjeta requiere configuracion adicional (filtros_config) antes de agregar */
  requiere_config?: boolean;
}

export interface CardCategory {
  code: string;
  nombre: string;
  icono: string;
}

export interface CategoryWithCards extends CardCategory {
  cards: CardCatalogItem[];
}
