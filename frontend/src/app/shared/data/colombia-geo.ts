export interface Departamento { codigo: string; nombre: string; }
export interface Ciudad { codigo: string; nombre: string; departamento: string; }

export const COLOMBIA_DEPARTAMENTOS: Departamento[] = [
  { codigo: '05', nombre: 'Antioquia' },
  { codigo: '08', nombre: 'Atlántico' },
  { codigo: '11', nombre: 'Bogotá D.C.' },
  { codigo: '13', nombre: 'Bolívar' },
  { codigo: '15', nombre: 'Boyacá' },
  { codigo: '17', nombre: 'Caldas' },
  { codigo: '18', nombre: 'Caquetá' },
  { codigo: '19', nombre: 'Cauca' },
  { codigo: '20', nombre: 'Cesar' },
  { codigo: '23', nombre: 'Córdoba' },
  { codigo: '25', nombre: 'Cundinamarca' },
  { codigo: '27', nombre: 'Chocó' },
  { codigo: '41', nombre: 'Huila' },
  { codigo: '44', nombre: 'La Guajira' },
  { codigo: '47', nombre: 'Magdalena' },
  { codigo: '50', nombre: 'Meta' },
  { codigo: '52', nombre: 'Nariño' },
  { codigo: '54', nombre: 'Norte de Santander' },
  { codigo: '63', nombre: 'Quindío' },
  { codigo: '66', nombre: 'Risaralda' },
  { codigo: '68', nombre: 'Santander' },
  { codigo: '70', nombre: 'Sucre' },
  { codigo: '73', nombre: 'Tolima' },
  { codigo: '76', nombre: 'Valle del Cauca' },
  { codigo: '81', nombre: 'Arauca' },
  { codigo: '85', nombre: 'Casanare' },
  { codigo: '86', nombre: 'Putumayo' },
  { codigo: '88', nombre: 'Archipiélago de San Andrés' },
  { codigo: '91', nombre: 'Amazonas' },
  { codigo: '94', nombre: 'Guainía' },
  { codigo: '95', nombre: 'Guaviare' },
  { codigo: '97', nombre: 'Vaupés' },
  { codigo: '99', nombre: 'Vichada' },
];

export const COLOMBIA_CIUDADES: Ciudad[] = [
  // Valle del Cauca
  { codigo: '76001', nombre: 'Cali',                    departamento: '76' },
  { codigo: '76036', nombre: 'Alcalá',                  departamento: '76' },
  { codigo: '76111', nombre: 'Guadalajara de Buga',     departamento: '76' },
  { codigo: '76122', nombre: 'Buenaventura',            departamento: '76' },
  { codigo: '76130', nombre: 'Cartago',                 departamento: '76' },
  { codigo: '76147', nombre: 'Jamundí',                 departamento: '76' },
  { codigo: '76306', nombre: 'Ginebra',                 departamento: '76' },
  { codigo: '76318', nombre: 'Guacarí',                 departamento: '76' },
  { codigo: '76520', nombre: 'Palmira',                 departamento: '76' },
  { codigo: '76834', nombre: 'Tuluá',                   departamento: '76' },
  { codigo: '76892', nombre: 'Yumbo',                   departamento: '76' },
  // Antioquia
  { codigo: '05001', nombre: 'Medellín',                departamento: '05' },
  { codigo: '05088', nombre: 'Bello',                   departamento: '05' },
  { codigo: '05360', nombre: 'Itagüí',                  departamento: '05' },
  { codigo: '05631', nombre: 'Rionegro',                departamento: '05' },
  { codigo: '05266', nombre: 'Envigado',                departamento: '05' },
  { codigo: '05045', nombre: 'Apartadó',                departamento: '05' },
  { codigo: '05615', nombre: 'Sabaneta',                departamento: '05' },
  // Bogotá
  { codigo: '11001', nombre: 'Bogotá D.C.',             departamento: '11' },
  // Cundinamarca
  { codigo: '25126', nombre: 'Cajicá',                  departamento: '25' },
  { codigo: '25148', nombre: 'Chía',                    departamento: '25' },
  { codigo: '25175', nombre: 'Cota',                    departamento: '25' },
  { codigo: '25214', nombre: 'Facatativá',              departamento: '25' },
  { codigo: '25260', nombre: 'Funza',                   departamento: '25' },
  { codigo: '25269', nombre: 'Girardot',                departamento: '25' },
  { codigo: '25473', nombre: 'Mosquera',                departamento: '25' },
  { codigo: '25754', nombre: 'Soacha',                  departamento: '25' },
  { codigo: '25899', nombre: 'Zipaquirá',               departamento: '25' },
  // Atlántico
  { codigo: '08001', nombre: 'Barranquilla',            departamento: '08' },
  { codigo: '08078', nombre: 'Baranoa',                 departamento: '08' },
  { codigo: '08606', nombre: 'Puerto Colombia',         departamento: '08' },
  { codigo: '08758', nombre: 'Soledad',                 departamento: '08' },
  // Santander
  { codigo: '68001', nombre: 'Bucaramanga',             departamento: '68' },
  { codigo: '68276', nombre: 'Floridablanca',           departamento: '68' },
  { codigo: '68307', nombre: 'Girón',                   departamento: '68' },
  { codigo: '68547', nombre: 'Piedecuesta',             departamento: '68' },
  // Bolívar
  { codigo: '13001', nombre: 'Cartagena',               departamento: '13' },
  { codigo: '13430', nombre: 'Magangué',                departamento: '13' },
  // Boyacá
  { codigo: '15001', nombre: 'Tunja',                   departamento: '15' },
  { codigo: '15176', nombre: 'Chiquinquirá',            departamento: '15' },
  { codigo: '15238', nombre: 'Duitama',                 departamento: '15' },
  { codigo: '15693', nombre: 'Sogamoso',                departamento: '15' },
  // Caldas
  { codigo: '17001', nombre: 'Manizales',               departamento: '17' },
  { codigo: '17380', nombre: 'La Dorada',               departamento: '17' },
  // Cauca
  { codigo: '19001', nombre: 'Popayán',                 departamento: '19' },
  // Cesar
  { codigo: '20001', nombre: 'Valledupar',              departamento: '20' },
  // Córdoba
  { codigo: '23001', nombre: 'Montería',                departamento: '23' },
  // Huila
  { codigo: '41001', nombre: 'Neiva',                   departamento: '41' },
  { codigo: '41551', nombre: 'Pitalito',                departamento: '41' },
  // Meta
  { codigo: '50001', nombre: 'Villavicencio',           departamento: '50' },
  // Nariño
  { codigo: '52001', nombre: 'Pasto',                   departamento: '52' },
  { codigo: '52356', nombre: 'Ipiales',                 departamento: '52' },
  // Norte de Santander
  { codigo: '54001', nombre: 'Cúcuta',                  departamento: '54' },
  { codigo: '54405', nombre: 'Los Patios',              departamento: '54' },
  // Quindío
  { codigo: '63001', nombre: 'Armenia',                 departamento: '63' },
  // Risaralda
  { codigo: '66001', nombre: 'Pereira',                 departamento: '66' },
  { codigo: '66170', nombre: 'Dosquebradas',            departamento: '66' },
  // Sucre
  { codigo: '70001', nombre: 'Sincelejo',               departamento: '70' },
  // Tolima
  { codigo: '73001', nombre: 'Ibagué',                  departamento: '73' },
  { codigo: '73268', nombre: 'Espinal',                 departamento: '73' },
  // La Guajira
  { codigo: '44001', nombre: 'Riohacha',                departamento: '44' },
  // Magdalena
  { codigo: '47001', nombre: 'Santa Marta',             departamento: '47' },
  // Casanare
  { codigo: '85001', nombre: 'Yopal',                   departamento: '85' },
  // Arauca
  { codigo: '81001', nombre: 'Arauca',                  departamento: '81' },
];
