export type EntidadConsecutivo = 'proyecto' | 'actividad' | 'factura';

export const ENTIDAD_LABELS: Record<EntidadConsecutivo, string> = {
  proyecto:  'Proyecto',
  actividad: 'Actividad',
  factura:   'Factura',
};

export const SUBTIPOS_POR_ENTIDAD: Record<EntidadConsecutivo, { value: string; label: string }[]> = {
  proyecto: [
    { value: 'obra_civil',         label: 'Obra civil'        },
    { value: 'consultoria',        label: 'Consultoría'       },
    { value: 'manufactura',        label: 'Manufactura'       },
    { value: 'servicios',          label: 'Servicios'         },
    { value: 'licitacion_publica', label: 'Licitación pública' },
    { value: 'otro',               label: 'Otro'              },
  ],
  actividad: [
    { value: 'mano_obra',   label: 'Mano de obra' },
    { value: 'material',    label: 'Material'     },
    { value: 'equipo',      label: 'Equipo'       },
    { value: 'subcontrato', label: 'Subcontrato'  },
  ],
  factura: [],
};

export interface ConsecutivoConfig {
  id:             string;
  nombre:         string;
  tipo:           EntidadConsecutivo;
  subtipo:        string;
  prefijo:        string;
  ultimo_numero:  number;
  formato:        string;
  activo:         boolean;
  proximo_codigo: string;
  created_at:     string;
  updated_at:     string;
}

export interface ConsecutivoCreate {
  nombre:        string;
  tipo:          EntidadConsecutivo;
  subtipo:       string;
  prefijo:       string;
  ultimo_numero: number;
  formato:       string;
  activo:        boolean;
}

export interface FormatoOpcion {
  value:   string;
  label:   string;
  ejemplo: string;
}

export const FORMATO_OPCIONES: FormatoOpcion[] = [
  { value: '{prefijo}-{numero:04d}', label: 'Guión + 4 dígitos',    ejemplo: 'PRY-0001' },
  { value: '{prefijo}-{numero:03d}', label: 'Guión + 3 dígitos',    ejemplo: 'PRY-001'  },
  { value: '{prefijo}-{numero:02d}', label: 'Guión + 2 dígitos',    ejemplo: 'PRY-01'   },
  { value: '{prefijo}-{numero}',     label: 'Guión, sin ceros',      ejemplo: 'PRY-1'    },
  { value: '{prefijo}{numero:04d}',  label: 'Sin guión + 4 dígitos', ejemplo: 'PRY0001'  },
  { value: '{prefijo}{numero:03d}',  label: 'Sin guión + 3 dígitos', ejemplo: 'PRY001'   },
  { value: '{prefijo}{numero}',      label: 'Sin guión, sin ceros',  ejemplo: 'PRY1'     },
];
