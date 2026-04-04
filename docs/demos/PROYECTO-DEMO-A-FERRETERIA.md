# Proyecto Demo A — Remodelación y Ampliación, Ferretería El Constructor

> **Tipo:** Construcción | **Estado:** 🔴 Retrasado (+7 días) | **EVM:** CPI 0.66 · SPI 0.75

---

## Resumen Ejecutivo

| Campo | Valor |
|---|---|
| **Nombre** | Remodelación y Ampliación — Ferretería El Constructor |
| **Cliente** | Ferretería El Constructor S.A.S |
| **NIT cliente** | 900.234.567-1 |
| **Fecha inicio** | 2026-02-02 |
| **Fecha fin planificada** | 2026-04-11 |
| **Fecha fin proyectada** | 2026-04-18 (+7 días de retraso) |
| **Presupuesto total** | $85,000,000 COP |
| **Labor presupuestada** | $62,000,000 COP |
| **Gastos presupuestados** | $23,000,000 COP |
| **Contingencia** | 10% |
| **Estado** | Activo — en ejecución |
| **Fases** | 4 |
| **Tareas** | 14 |
| **Dependencias** | 12 |
| **Timesheets** | 278 entradas |
| **CPI** | 0.66 🔴 (sobre presupuesto) |
| **SPI** | 0.75 🔴 (atrasado) |

---

## Equipo del Proyecto (10 personas)

| # | Nombre | Rol Saicloud | Tarifa | Responsabilidades principales |
|---|---|---|---|---|
| 1 | Carlos Mendoza | company_admin | $120,000/h | Gerente de Proyecto, coordinación general, entrega final |
| 2 | Luisa Fernández | seller | $95,000/h | Arquitecta — diseño, planos, especificaciones técnicas |
| 3 | Andrés Rojas | seller | $55,000/h | Maestro de Obra — obra civil, estructura, cubierta |
| 4 | María Gómez | seller | $65,000/h | Electricista — instalaciones eléctricas, alumbrado |
| 5 | Pedro Salcedo | seller | $60,000/h | Plomero — red hidrosanitaria, plomería |
| 6 | Juliana Torres | seller | $85,000/h | Diseñadora de Interiores — acabados, señalización |
| 7 | Roberto Díaz | seller | $45,000/h | Pintor — pintura y acabados interiores |
| 8 | Ana Herrera | viewer | $35,000/h | Asistente Administrativa — permisos, documentos |
| 9 | Diego Vargas | seller | $75,000/h | Inspector Técnico — supervisión, techo, entrega |
| 10 | Camila Ortiz | seller | $70,000/h | Coordinadora SST — seguridad y salud en el trabajo |

---

## Estructura Detallada — Fases y Tareas

### FASE 1: Planificación y Diseño
**Estado:** Completada | **Fechas:** 2026-02-02 → 2026-02-20 | **Progreso:** 100%

| ID | Tarea | Tipo actividad | Horas/Unidades | Estado | Asignado a |
|---|---|---|---|---|---|
| T1 | Levantamiento arquitectónico y diagnóstico | horas | 40 h | ✅ Completada | Luisa Fernández |
| T2 | Diseño de planos y especificaciones técnicas | horas | 60 h | ✅ Completada | Luisa Fernández |
| T3 | Tramitación de permisos de construcción | hito | — | ✅ Completada | Ana Herrera |
| T4 | Plan de seguridad y salud en el trabajo | horas | 16 h | ✅ Completada | Camila Ortiz |

---

### FASE 2: Estructura y Obra Civil
**Estado:** Activa | **Fechas:** 2026-02-21 → 2026-03-21 | **Progreso:** ~60%

| ID | Tarea | Tipo actividad | Unidad | Estado | Asignado a |
|---|---|---|---|---|---|
| T5 | Demolición y preparación del terreno | unidad | 150 m² | ✅ Completada | Andrés Rojas |
| T6 | Refuerzo estructural y fundaciones | horas | 120 h | 🔄 En progreso | Andrés Rojas |
| T7 | Construcción de nuevas paredes y divisiones | unidad | 85 m² | 🔄 En progreso | Andrés Rojas |
| T8 | Cubierta y techo | horas | 80 h | ⬜ Por hacer | Andrés Rojas, Diego Vargas |

---

### FASE 3: Instalaciones
**Estado:** Planificada | **Fechas:** 2026-03-22 → 2026-04-05 | **Progreso:** 0%

| ID | Tarea | Tipo actividad | Unidad | Estado | Asignado a |
|---|---|---|---|---|---|
| T9 | Instalaciones eléctricas y alumbrado | horas | 96 h | ⬜ Por hacer | María Gómez |
| T10 | Red hidrosanitaria y plomería | horas | 64 h | ⬜ Por hacer | Pedro Salcedo |
| T11 | Red contra incendios | horas | 32 h | ⬜ Por hacer | Diego Vargas |

---

### FASE 4: Acabados y Entrega
**Estado:** Planificada | **Fechas:** 2026-04-06 → 2026-04-11 | **Progreso:** 0%

| ID | Tarea | Tipo actividad | Unidad | Estado | Asignado a |
|---|---|---|---|---|---|
| T12 | Pintura y acabados interiores | unidad | 320 m² | ⬜ Por hacer | Roberto Díaz, Juliana Torres |
| T13 | Señalización y demarcación | unidad | 45 señales | ⬜ Por hacer | Camila Ortiz |
| T14 | Inspección final y entrega al cliente | hito | — | ⬜ Por hacer | Carlos Mendoza, Diego Vargas |

---

## Mapa de Dependencias (12 dependencias)

| # | Predecesora | Sucesora | Tipo | Lag | Razón de negocio |
|---|---|---|---|---|---|
| D1 | T1 | T2 | FS | 0 | No se puede diseñar sin el levantamiento previo |
| D2 | T2 | T3 | FS | 0 | Los permisos requieren los planos aprobados |
| D3 | T2 | T4 | FS | 0 | El plan SST se basa en las especificaciones técnicas |
| D4 | T3 | T5 | FS | 0 | La demolición no puede iniciar sin permiso de construcción |
| D5 | T4 | T5 | FS | 0 | La demolición requiere plan SST aprobado |
| D6 | T5 | T6 | FS | 0 | Las fundaciones inician después de demolición completa |
| D7 | T6 | T7 | SS | +2d | Las paredes inician 2 días después de fundaciones (cimentado) |
| D8 | T7 | T8 | FS | 0 | La cubierta requiere paredes terminadas |
| D9 | T6 | T9 | FS | +5d | Electricidad inicia 5 días después de terminadas fundaciones |
| D10 | T9 | T10 | SS | 0 | Plomería puede ir en paralelo con electricidad |
| D11 | T10 | T11 | FS | 0 | Red contra incendios requiere plomería base terminada |
| D12 | T11 | T12 | FS | 0 | Acabados inician cuando todas las instalaciones terminan |

> **Tareas sin dependencias de salida → T12, T13, T14** (cola final).
> **Ruta crítica:** T1→T2→T3→T5→T6→T7→T8→T9→T10→T11→T12→T13→T14

---

## Plan de Timesheets (278 entradas totales)

| Tarea | Responsable(s) | Horas plan | Horas registradas | Entradas | Observación |
|---|---|---|---|---|---|
| T1 | Luisa Fernández | 40 h | 38 h | 43 | Casi completado al plan |
| T2 | Luisa Fernández | 60 h | 58 h | 67 | Dentro del estimado |
| T3 | Ana Herrera | — | 15 h | 12 | Hito — gestión documental tomó más de lo esperado |
| T4 | Camila Ortiz | 16 h | 17 h | 18 | Leve sobrecosto (+1h) |
| T5 | Andrés Rojas | ~80 h | 162 h | 45 | **+82h sobre lo planeado** — demolición más compleja |
| T6 | Andrés Rojas | 120 h | 98 h | 62 | En progreso — 82% completado |
| T7 | Andrés Rojas | ~50 h | 52 h | 31 | En progreso — obstáculos estructurales |
| T8 | Andrés Rojas, Diego | 80 h | 0 h | 0 | No iniciada |
| T9–T14 | Varios | — | 0 h | 0 | Fases no iniciadas |
| **TOTAL** | | | | **278** | |

> **Nota:** El exceso en T5 (demolición) es la causa principal del desvío de presupuesto. Se encontraron refuerzos adicionales no previstos en el diagnóstico inicial.

---

## Presupuesto y Gastos

### Presupuesto Aprobado

| Componente | Valor |
|---|---|
| Labor presupuestada | $62,000,000 |
| Gastos presupuestados | $23,000,000 |
| Contingencia (10%) | $8,500,000 |
| **Total presupuestado (BAC)** | **$85,000,000** |

### Gastos Registrados (9 gastos)

| # | Descripción | Categoría | Monto | Estado | Facturable |
|---|---|---|---|---|---|
| G1 | Materiales de demolición | equipment | $3,200,000 | ✅ Aprobado | No |
| G2 | Cemento y agregados | equipment | $8,500,000 | ✅ Aprobado | Sí |
| G3 | Acero de refuerzo | equipment | $12,000,000 | ✅ Aprobado | Sí |
| G4 | Herramientas especializadas (alquiler) | equipment | $2,800,000 | ✅ Aprobado | Sí |
| G5 | EPP equipo completo | equipment | $1,500,000 | ✅ Aprobado | No |
| G6 | Permisos de construcción | other | $850,000 | ✅ Aprobado | No |
| G7 | Transporte de materiales | travel | $1,200,000 | ✅ Aprobado | Sí |
| G8 | Materiales eléctricos | equipment | $4,500,000 | ⏳ Pendiente | Sí |
| G9 | Materiales plomería | equipment | $3,800,000 | ⏳ Pendiente | Sí |
| **TOTAL** | | | **$38,350,000** | | |

**Gastos aprobados:** $30,050,000
**Gastos pendientes:** $8,300,000
**Gastos facturables aprobados:** $24,500,000

---

## Análisis EVM Completo

> Fecha de análisis: 28 Marzo 2026 (semana 7 de 10)

| Métrica | Sigla | Valor | Interpretación |
|---|---|---|---|
| Presupuesto total | BAC | $85,000,000 | Costo total planificado del proyecto |
| Valor planificado | PV | $63,750,000 | 75% del cronograma debería estar completo |
| Valor ganado | EV | $47,812,500 | Solo el 56.25% está realmente completado |
| Costo real | AC | $72,442,000 | Lo que se ha gastado hasta la fecha |
| Variación de costo | CV | -$24,629,500 | **Sobre presupuesto en $24.6M** |
| Variación de schedule | SV | -$15,937,500 | **Atrasado en valor equivalente a $15.9M** |
| Índice rendimiento costo | CPI | **0.66** 🔴 | Por cada $1 gastado se generan $0.66 de valor |
| Índice rendimiento schedule | SPI | **0.75** 🔴 | Avanzando al 75% del ritmo esperado |
| Costo final estimado | EAC | $128,787,878 | Si CPI no mejora, el proyecto costará $128.8M |
| Costo restante estimado | ETC | $56,345,878 | Lo que falta gastar para terminar |
| Variación al completar | VAC | -$43,787,878 | **Sobrecosto proyectado: $43.8M** |
| Índice de eficiencia necesario | TCPI | 1.72 | Debe mejorar mucho la eficiencia para llegar al BAC |

### Diagnóstico
- **Causa principal:** Demolición (T5) tomó 162h vs 80h planeadas (+82h) por estructuras no previstas.
- **Efecto cascada:** Retraso de 7 días en el cronograma general.
- **Acción recomendada:** Revisar plan de Fases 3 y 4; considerar agregar recursos en T9 (electricidad).

---

## Baselines

### Baseline 1: "Plan Original"
- **Creada:** 2026-02-01 (antes del inicio)
- **Creada por:** Carlos Mendoza
- **Descripción:** Fotografía del plan inicial antes de cualquier ejecución
- **Estado al comparar (28-Mar):** 6 de 14 tareas con fecha fin posterior a baseline

| Tarea | Fecha fin baseline | Fecha fin actual | Desviación |
|---|---|---|---|
| T5 | 2026-02-27 | 2026-03-05 | +6 días |
| T6 | 2026-03-14 | 2026-03-21 | +7 días |
| T7 | 2026-03-18 | 2026-03-25 | +7 días |
| T8 | 2026-03-21 | 2026-03-28 | +7 días |
| T9 | 2026-03-28 | 2026-04-05 | +8 días |
| T14 | 2026-04-11 | 2026-04-18 | +7 días |

---

## Escenarios What-If

### Escenario 1: "Refuerzo de Equipo Fase 3"
- **Hipótesis:** Agregar 2 electricistas adicionales en T9 reduce la duración en un 30%
- **T9 original:** 96 horas / 12 días calendario
- **T9 simulado:** 67 horas / 8.4 días (con 3 electricistas en paralelo)
- **Resultado:** Entrega proyectada el 2026-04-13 en lugar de 2026-04-18
- **Ahorro en tiempo:** 5 días calendario
- **Costo adicional labor:** ~$6,240,000 (2 electricistas × 32h × $65,000)
- **Decisión:** Pendiente de aprobación por Carlos Mendoza

---

## Instrucciones de Inserción en Saicloud

Seguir este orden exacto para ingresar el proyecto en la aplicación:

### Paso 1: Crear el Tercero
1. Ir a **Terceros** en el sidebar
2. Clic en **Nuevo Tercero**
3. Ingresar: Nombre = "Ferretería El Constructor S.A.S", NIT = 900234567-1, Tipo = Cliente
4. Guardar

### Paso 2: Crear los 10 Usuarios
1. Ir a **Admin > Usuarios**
2. Crear cada usuario de la tabla del equipo
3. Asignar roles según la columna "Rol Saicloud"

### Paso 3: Crear Actividades del Catálogo
Crear al menos estas actividades antes del proyecto:
- "Levantamiento arquitectónico" (horas)
- "Diseño de planos" (horas)
- "Tramitación de permisos" (hito)
- "Plan SST" (horas)
- "Demolición" (unidad — m²)
- "Refuerzo estructural" (horas)
- "Construcción de paredes" (unidad — m²)
- "Cubierta y techo" (horas)
- "Instalaciones eléctricas" (horas)
- "Red hidrosanitaria" (horas)
- "Red contra incendios" (horas)
- "Pintura y acabados" (unidad — m²)
- "Señalización" (unidad — señales)
- "Inspección y entrega" (hito)

### Paso 4: Crear el Proyecto
1. Ir a **Proyectos** → **Nuevo Proyecto**
2. Nombre: "Remodelación y Ampliación — Ferretería El Constructor"
3. Fecha inicio: 2026-02-02, Fecha fin: 2026-04-11
4. Cliente: Ferretería El Constructor S.A.S
5. Estado: Activo
6. Guardar

### Paso 5: Crear las 4 Fases (en orden)
1. Planificación y Diseño (2026-02-02 → 2026-02-20)
2. Estructura y Obra Civil (2026-02-21 → 2026-03-21)
3. Instalaciones (2026-03-22 → 2026-04-05)
4. Acabados y Entrega (2026-04-06 → 2026-04-11)

### Paso 6: Crear las 14 Tareas (en orden por fase)
Crear T1→T14 según la tabla de estructura detallada.
Asignar actividad del catálogo a cada tarea.

### Paso 7: Crear las 12 Dependencias
Seguir la tabla de dependencias. Usar tipo FS excepto donde se indica SS.

### Paso 8: Ejecutar Auto-Schedule
1. Clic en **Scheduling → Auto-Schedule**
2. Modo: **ASAP**
3. Previsualizar → verificar fechas → Aplicar

### Paso 9: Crear Baseline "Plan Original"
1. Ir a tab **Baselines**
2. Clic en **Nueva Baseline**
3. Nombre: "Plan Original"
4. Guardar

### Paso 10: Asignar Recursos a Tareas
Asignar cada miembro del equipo a sus tareas correspondientes.
Verificar sobreasignación en `/check-overallocation/`.

### Paso 11: Registrar Timesheets
Registrar ~278 entradas distribuyendo según la tabla de timesheets.
Para tareas de T1-T7: registrar históricamente con fechas pasadas.

### Paso 12: Marcar Tareas Completadas
- T1, T2, T3, T4: marcar como **completadas**
- T5: marcar como **completada**
- T6, T7: dejar en **en_progreso**

### Paso 13: Crear Presupuesto
1. Ir a tab **Presupuesto**
2. Labor: $62,000,000 | Gastos: $23,000,000 | Contingencia: 10%
3. Guardar → **Aprobar**

### Paso 14: Configurar Tarifas por Recurso
Crear tarifa activa para cada miembro del equipo según la tabla.

### Paso 15: Registrar Gastos
Ingresar los 9 gastos de la tabla. Aprobar los 7 que corresponde.

### Paso 16: Crear Escenario What-If
1. Tab **Escenarios** → **Nuevo Escenario**
2. Nombre: "Refuerzo de Equipo Fase 3"
3. Configurar y ejecutar simulación

---

## Checklist de Verificación Post-Inserción

- [ ] Proyecto aparece en lista con estado "Activo"
- [ ] 4 fases creadas con fechas correctas
- [ ] 14 tareas con actividades asignadas
- [ ] 12 dependencias visibles en tabla
- [ ] Gantt muestra barras para todas las tareas
- [ ] Auto-Schedule aplicado (fechas calculadas)
- [ ] Baseline "Plan Original" creada
- [ ] T1-T5 marcadas como completadas
- [ ] T6, T7 en estado "en_progreso"
- [ ] 278 timesheets aproximadamente registrados
- [ ] Analytics muestra KPIs con datos
- [ ] Presupuesto aprobado (no editable)
- [ ] 9 gastos registrados (7 aprobados, 2 pendientes)
- [ ] EVM: CPI ≈ 0.66, SPI ≈ 0.75 (valores rojos)
- [ ] Dashboard presupuesto muestra alertas de sobrecosto
- [ ] Escenario "Refuerzo de Equipo" creado y simulado
