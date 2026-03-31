# Informe de Auditoría — Manual de Usuario vs Implementación Real
# Módulo Proyectos — Saicloud

**Fecha de auditoría:** 31 de Marzo de 2026
**Auditado por:** Agente Gestor de Proyectos Saicloud
**Manual auditado:** `docs/manuales/MANUAL-PROYECTOS-SAICLOUD.md` versión 1.0
**Manual actualizado a versión:** 1.1
**Usuario de prueba:** admin@andina.com (company_admin — Constructora Andina S.A.S)
**Proyecto de referencia:** PCON-0001 — Implementacion ERP - Ferreteria Andina S.A.S

---

## Sección 1: Resumen Ejecutivo

| Categoría | Cantidad | Porcentaje |
|---|---|---|
| Total funcionalidades auditadas | 48 | 100% |
| PASS (correctas) | 18 | 37.5% |
| MODIFICADAS (diferente a lo documentado) | 22 | 45.8% |
| FALTANTES (documentadas pero no implementadas) | 5 | 10.4% |
| NO DOCUMENTADAS (implementadas pero sin documentar) | 3 | 6.3% |

**Conclusión general:** El manual requería actualización significativa. Las diferencias más críticas están en: la estructura de tabs del detalle de proyecto (completamente reorganizada), el formulario de terceros (estructura de campos diferente), la sección de Scheduling (ya no es un tab sino un botón), y los KPIs de Analytics (nombres y métricas diferentes). El manual ha sido actualizado a versión 1.1 reflejando la implementación real.

---

## Sección 2: Funcionalidades PASS

Las siguientes funcionalidades coinciden con lo documentado en el manual original:

1. Login con email y contraseña
2. Redirección al dashboard tras login exitoso
3. Botón toggle dark mode / light mode
4. Crear proyecto (formulario con campos esenciales)
5. Estados del proyecto (draft, planned, in_progress, suspended, closed, cancelled)
6. Crear fase en el proyecto (tab Fases, botón + Nueva fase)
7. Editar y eliminar fase
8. Arrastrar para reordenar fases (drag & drop con indicador visual)
9. Crear tarea con campos básicos (nombre, fase, descripción, fechas, responsable, prioridad)
10. Eliminar tarea (con confirmación)
11. Catálogo de actividades (4 tipos: labor, material, equipment, subcontract)
12. Crear actividad en catálogo (formulario con código auto, tipo, nombre, unidad, costo)
13. Tipos de dependencias FS, SS, FF (documentación conceptual correcta)
14. Lag time en dependencias (campo numérico en días)
15. Timer (cronómetro): play, pausa, stop en detalle de tarea
16. Registro manual de timesheet en detalle de tarea
17. Baseline: crear y nombrar baseline en tab Baselines
18. Gantt: visualización con barras por tarea
19. Escenarios What-If: crear escenario con nombre y descripción
20. Crear tercero (flujo general: botón Nuevo tercero, formulario)

---

## Sección 3: Funcionalidades MODIFICADAS

Funcionalidades que existen pero difieren de la documentación original:

| # | Funcionalidad | Descripción en el Manual v1.0 | Implementación Real | Acción Tomada |
|---|---|---|---|---|
| 1 | Tab "Resumen" del proyecto | Primer tab llamado "Resumen" con información general | El tab se llama **"General"**, no "Resumen" | Manual actualizado |
| 2 | Estructura de tabs del detalle de proyecto | 13 tabs: Resumen, Fases, Tareas, Kanban, Gantt, Actividades, Recursos, Timesheets, Analytics, Scheduling, Presupuesto, Documentos, Hitos | 14 tabs en este orden: General, Fases, Terceros, Documentos, Hitos, Tareas, Actividades, Gantt, Equipo, Timesheets, Analytics, Baselines, Escenarios, Presupuesto | Manual actualizado — tabla completa de tabs corregida |
| 3 | Tab "Recursos" del proyecto | Tab llamado "Recursos" con workload y calendario | El tab se llama **"Equipo"** y tiene: equipo con tareas asignadas, capacidades y ausencias. No tiene vista workload semanal ni calendario detallado | Manual actualizado — sección renombrada |
| 4 | Tab "Kanban" del proyecto | Tab separado "Kanban" en el detalle del proyecto | No hay tab "Kanban" independiente. El Kanban está dentro del tab "Tareas" como un botón toggle ("Kanban" / "Lista") | Manual actualizado |
| 5 | Tab "Scheduling" del proyecto | Tab "Scheduling" con Auto-Schedule, nivelación, restricciones, baselines y escenarios | No existe el tab "Scheduling". Las funcionalidades están distribuidas: Auto-Schedule es el botón "Scheduling" en el encabezado (dropdown), Baselines es un tab, Escenarios es un tab, Restricciones está en el detalle de cada tarea | Manual actualizado — sección completamente reestructurada |
| 6 | Timesheets dentro del proyecto | No documentado como tab dentro del proyecto; se mencionaba solo por tarea o semanal | Tab "Timesheets" dentro del proyecto muestra TODOS los timesheets del proyecto con: fecha, usuario, tarea, horas, descripción | Manual actualizado |
| 7 | Terceros dentro del proyecto | Se mencionaba brevemente; no como tab propio | Tab "Terceros" dentro del proyecto permite vincular/desvincular terceros con rol y fase. Muestra: nombre, NIT, rol, fase asignada | Manual actualizado |
| 8 | Vista predeterminada de lista de proyectos | "Vista Cards (predeterminada)" | La vista predeterminada es **Vista Lista** (tabla). El botón visible dice "Cards" para cambiar a tarjetas | Manual actualizado |
| 9 | Vista semanal de timesheets | Documentada como "no accesible" o difícil de encontrar | Ruta `/proyectos/timesheets` accesible desde el sidebar bajo "Registro de Horas". Muestra semana actual con navegación | Manual actualizado |
| 10 | "Mis Tareas" | Mencionada en tabla de sidebar pero documentada como funcionalidad faltante | Existe en `/proyectos/mis-tareas`. Muestra tareas asignadas al usuario actual. Tiene vista lista y kanban | Manual actualizado |
| 11 | Formulario de terceros | 8 campos: Nombre/Razón social, Tipo (Cliente/Proveedor/Ambos), NIT/Cédula, Email, Teléfono, Ciudad, Dirección, Notas | Formulario estructurado por secciones: Identificación (tipo persona, tipo tercero, tipo documento, número), Nombre (4 campos separados para nombre y apellido), Contacto (email, teléfono fijo, celular), Dirección (opcional) | Manual actualizado — formulario completamente redocumentado |
| 12 | Formulario de nueva tarea (campos) | 16 campos incluyendo Seguidores, Etiquetas, Horas estimadas, Cantidad objetivo | El formulario de creación tiene 13 campos. Seguidores y etiquetas no están en el form de creación. Horas estimadas y cantidad objetivo se gestionan en el detalle de la tarea según el tipo de actividad | Manual actualizado |
| 13 | KPIs de Analytics | 6 KPIs: % completud, Tasa a tiempo, Horas registradas, Eficiencia, Tareas vencidas, Tareas activas | 4 KPIs: Completud (X/Y tareas), On-Time (vencidas), Velocidad (tareas/semana), Horas Burn Rate (h/semana + varianza) | Manual actualizado |
| 14 | Zoom del Gantt | Botones `+` y `-` para zoom, niveles Días/Semanas/Meses/Trimestres | Botones **Día**, **Semana**, **Mes** (no `+/-`). No hay nivel "Trimestres" visible | Manual actualizado |
| 15 | Exportar Gantt | No documentado | Botón **Exportar SVG** disponible en la barra del Gantt | Manual actualizado |
| 16 | Nivelación de recursos | Descrita como funcionalidad del tab Scheduling con wizard | No disponible en la interfaz actual | Manual actualizado — marcada como no disponible |
| 17 | Restricciones de tareas | Documentadas en tab "Scheduling" | Disponibles en el detalle de cada tarea, sección "Restricciones". El tab Scheduling no existe | Manual actualizado — ubicación corregida |
| 18 | EVM con valores calculados | Documentado como sistema completo con CPI, SPI, EAC, etc. | El EVM muestra "—" para todos los indicadores calculados si no hay presupuesto aprobado. Las tarifas SÍ existen en la UI (sección Tarifas por Recurso en tab Presupuesto) | Manual actualizado — se documenta la condición para que funcione |
| 19 | Tarifas de costo por recurso | Descritas como sin UI disponible | La UI existe en el tab **Presupuesto**, sección "Tarifas por Recurso" con CRUD completo | Manual actualizado |
| 20 | Presupuesto — sección Mano de obra | No separada explícitamente | Tab Presupuesto muestra secciones separadas: "Mano de obra" y "Gastos directos" con montos planificados y reales | Manual actualizado |
| 21 | Eliminación de proyecto | Desde menú tres puntos (⋮) dentro del detalle, con confirmación escribiendo el nombre | El botón eliminar (papelera) está en la **lista de proyectos** (vista tabla), no dentro del detalle. No requiere escribir el nombre, solo confirmar en diálogo | Manual actualizado |
| 22 | Sidebar con labels de texto | Documentado con nombres de módulo visibles: "Dashboard, Proyectos, Mis tareas..." | El sidebar muestra solo iconos. Los nombres aparecen en el panel expandible o al hacer hover | Manual actualizado — descripción corregida |

---

## Sección 4: Funcionalidades FALTANTES

Funcionalidades documentadas en el manual que no están disponibles en la implementación actual:

| # | Funcionalidad | Descripción en el Manual | Prioridad | Nota |
|---|---|---|---|---|
| 1 | Nivelación automática de recursos | Reprogramación automática de tareas para eliminar sobreasignación | Alta | Algoritmo backend existe pero no hay UI |
| 2 | Exportación a Excel del Analytics | Exportar reporte con 4 hojas: KPIs, tareas, horas, burn down | Media | Solo hay botón de descarga genérico |
| 3 | Facturación (módulo de datos de factura) | Generar líneas de factura con labor + gastos facturables agrupados por recurso | Alta | No existe sección de Facturación en el tab Presupuesto |
| 4 | Workload (carga por semana con colores) | Vista semanal de utilización por recurso con semáforo verde/amarillo/rojo | Media | Solo se muestra la lista de tareas asignadas por persona en el tab Equipo |
| 5 | Calendario detallado por usuario | Vista calendario mensual con bloques de tareas por usuario | Baja | No disponible actualmente |

---

## Sección 5: Funcionalidades NO DOCUMENTADAS

Funcionalidades implementadas en la plataforma que el manual no documenta:

| # | Funcionalidad | Descripción | Impacto |
|---|---|---|---|
| 1 | Tab **Hitos facturables** del proyecto | El tab "Hitos" permite crear hitos facturables con: nombre, descripción, porcentaje de pago, valor a facturar, estado de factura. Es diferente a las tareas marcadas como hito del Gantt. Permite gestionar los pagos parciales por hito contractual | Alto — funcionalidad clave para cobros |
| 2 | Módulo de Configuración del proyecto | Ruta `/proyectos/configuracion` permite configurar: modo de registro de tiempo (Manual/Cronómetro/Ambos/Desactivado), integración con Saiopen, días de alerta antes del vencimiento de tareas | Medio — afecta comportamiento del timer |
| 3 | Dashboard de proyectos (`/proyectos/dashboard`) | Al ingresar al módulo, hay un dashboard resumen con: KPIs globales (total proyectos, activos, presupuesto, tareas vencidas), distribución por estado, y tarjetas de seguimiento por proyecto activo con avance, tareas y % puntual | Alto — primera pantalla del módulo |

---

## Sección 6: Cambios Aplicados al Manual

Todos los cambios se aplicaron al archivo `docs/manuales/MANUAL-PROYECTOS-SAICLOUD.md`.

### Cambio 1 — Versión del manual
- **Sección:** Encabezado
- **Antes:** Versión 1.0 — Marzo 2026
- **Después:** Versión 1.1 — Marzo 2026 (Actualizado tras auditoría de implementación real)

### Cambio 2 — Sidebar de navegación
- **Sección:** 2.5 Navegación general
- **Antes:** Tabla simple con 6 módulos del sidebar principal (Dashboard, Proyectos, Mis tareas, Terceros, Catálogo, Configuración)
- **Después:** Descripción del sidebar de módulo Proyectos con 7 opciones (Dashboard, Proyectos, Tareas, Mis Tareas, Registro de Horas, Actividades, Configuración) + sección Acceso Rápido (Terceros, Usuarios, Consecutivos)
- **Razón:** El sidebar real del módulo Proyectos tiene estructura diferente a la descrita

### Cambio 3 — Vista predeterminada de proyectos
- **Sección:** 4.2 Lista de proyectos
- **Antes:** "Vista Cards (predeterminada)" con descripción primero de cards
- **Después:** "Vista Lista (predeterminada)" con descripción de tabla como vista inicial; cards como alternativa
- **Razón:** La URL `/proyectos/lista` es la predeterminada

### Cambio 4 — Tabs del detalle de proyecto
- **Sección:** 4.3 Detalle del proyecto (tabs disponibles)
- **Antes:** Tabla con 13 tabs incluyendo "Resumen", "Kanban", "Recursos", "Scheduling"
- **Después:** Tabla con 14 tabs en el orden real: General, Fases, Terceros, Documentos, Hitos, Tareas, Actividades, Gantt, Equipo, Timesheets, Analytics, Baselines, Escenarios, Presupuesto. Adicionado bloque de "Botones de acción en el encabezado"
- **Razón:** Los tabs fueron reorganizados y renombrados en la implementación

### Cambio 5 — Eliminación de proyectos
- **Sección:** 4.4 Editar y eliminar proyectos
- **Antes:** Eliminación desde menú ⋮ dentro del detalle, escribiendo el nombre del proyecto
- **Después:** Eliminación desde botón papelera en la lista de proyectos (vista tabla), con diálogo de confirmación simple
- **Razón:** El botón de eliminación no está en el detalle sino en la lista

### Cambio 6 — Formulario de nueva tarea
- **Sección:** 6.1 Crear una tarea
- **Antes:** 16 campos incluyendo Seguidores, Etiquetas, Horas estimadas, Cantidad objetivo
- **Después:** 13 campos del formulario real; nota sobre horas estimadas y cantidad objetivo en el detalle de tarea
- **Razón:** El formulario de creación no tiene todos los campos documentados

### Cambio 7 — Vista Kanban dentro del proyecto
- **Sección:** 6.3 Vista lista y Kanban
- **Antes:** Dos vistas separadas (lista y kanban) como opciones independientes
- **Después:** Kanban como botón toggle dentro del tab Tareas; descripción de columnas y filtros reales
- **Razón:** No existe tab Kanban separado; el Kanban es un botón dentro del tab Tareas

### Cambio 8 — Detalle de tarea
- **Sección:** 6.5 Editar y eliminar tareas
- **Antes:** Descripción genérica del panel de detalle
- **Después:** Descripción completa de todas las secciones del detalle real: Progreso, Estado, Descripción, Subtareas, Seguidores, Tiempo, Dependencias, Restricciones, Recursos, Comentarios. Metadata en panel lateral: Float, proyecto, fase, actividad, responsable, prioridad, fechas
- **Razón:** El detalle tiene más funcionalidades que las documentadas

### Cambio 9 — Zoom del Gantt
- **Sección:** 9.2 Navegación del Gantt
- **Antes:** Botones `+` y `-`, con nivel "Trimestres"
- **Después:** Botones Día, Semana, Mes. Sin nivel Trimestres
- **Razón:** La interfaz usa botones de texto, no iconos de zoom

### Cambio 10 — Exportar Gantt
- **Sección:** 9.2 Navegación del Gantt
- **Antes:** No documentado
- **Después:** Botón "Exportar SVG" documentado
- **Razón:** Funcionalidad existente no documentada

### Cambio 11 — Overlays del Gantt
- **Sección:** 9.3 Overlays disponibles
- **Antes:** "Menú de overlays" con selección múltiple
- **Después:** Botones individuales en la barra: Ruta crítica, Holgura, Baseline
- **Razón:** No hay menú desplegable de overlays, son botones independientes

### Cambio 12 — Registro semanal de horas
- **Sección:** 10.2 Registrar tiempo manual
- **Antes:** Vista semanal con grilla (filas=tareas, columnas=días) y botón "Guardar semana"
- **Después:** Vista semanal de solo consulta en `/proyectos/timesheets` (Registro de Horas). El registro se hace en cada tarea individual
- **Razón:** La vista semanal no permite edición inline; es una vista de resumen

### Cambio 13 — Nombre del módulo de gestión de equipo
- **Sección:** 11. Resource Management (encabezado y contenido)
- **Antes:** "Resource Management" con tabs "Recursos", "Capacidades", "Carga de trabajo", "Calendario del equipo"
- **Después:** "Gestión del Equipo (Tab Equipo)" con secciones: equipo con tareas, capacidades, ausencias. Workload y calendario documentados como pendientes
- **Razón:** El tab se llama "Equipo", no "Recursos". Las vistas de workload y calendario no están implementadas

### Cambio 14 — KPIs de Analytics
- **Sección:** 12.2 KPIs principales
- **Antes:** 6 KPIs: % completud, Tasa a tiempo, Horas registradas, Eficiencia, Tareas vencidas, Tareas activas
- **Después:** 4 KPIs: Completud, On-Time, Velocidad, Horas Burn Rate. Con descripción de botones refresh y download
- **Razón:** Los KPIs implementados tienen nombres y métricas diferentes

### Cambio 15 — Exportación de Analytics
- **Sección:** 12.5 Exportación a Excel
- **Antes:** Exportación a Excel con 4 hojas detalladas
- **Después:** Botón de descarga genérico disponible; exportación Excel completa como funcionalidad en desarrollo
- **Razón:** La exportación Excel con 4 hojas no está implementada

### Cambio 16 — Estructura de Advanced Scheduling
- **Sección:** 13. Advanced Scheduling
- **Antes:** Todo centralizado en el tab "Scheduling" con 5 subsecciones
- **Después:** Funcionalidades distribuidas: Auto-Schedule en botón del encabezado, Baselines en tab propio, Escenarios en tab propio, Restricciones en detalle de tarea
- **Razón:** El tab "Scheduling" fue eliminado y sus funciones redistribuidas

### Cambio 17 — Auto-Schedule: cómo acceder
- **Sección:** 13.1 Auto-Schedule
- **Antes:** "En el tab Scheduling, haga clic en Auto-Schedule"
- **Después:** "En el encabezado del proyecto, haga clic en el botón Scheduling → Auto-Schedule"
- **Razón:** No existe el tab Scheduling

### Cambio 18 — Nivelación de recursos
- **Sección:** 13.2 Nivelación de recursos
- **Antes:** Wizard de 5 pasos con dry run y aplicación
- **Después:** Documentada como no disponible en la interfaz actual; indicación de alternativa manual
- **Razón:** No hay UI para nivelación de recursos

### Cambio 19 — Restricciones de tareas: ubicación
- **Sección:** 13.3 Restricciones de tareas
- **Antes:** "En el detalle de la tarea, busque la sección Restricciones de programación"
- **Después:** "Abra el detalle de la tarea (botón de flecha), busque la sección Restricciones"
- **Razón:** Corrección de ruta de acceso

### Cambio 20 — Baselines: cómo acceder
- **Sección:** 13.4 Baselines
- **Antes:** "En el tab Scheduling → Baselines"
- **Después:** "En el detalle del proyecto, haga clic en el tab Baselines"
- **Razón:** No existe el tab Scheduling

### Cambio 21 — Comparar baseline
- **Sección:** 13.4 Comparar baseline
- **Antes:** "Clic en el nombre → Comparar con avance actual"
- **Después:** "Sección Comparar con baseline, selector desplegable + botón Calcular comparación"
- **Razón:** La interfaz de comparación usa un selector + botón, no un clic en el nombre

### Cambio 22 — Escenarios: cómo acceder
- **Sección:** 13.5 Escenarios What-If
- **Antes:** "En el tab Scheduling → Escenarios"
- **Después:** "En el tab Escenarios del proyecto"
- **Razón:** No existe el tab Scheduling

### Cambio 23 — EVM: condiciones para funcionar
- **Sección:** 14.5 EVM
- **Antes:** Solo requisitos básicos; sin mención de que puede mostrar "—"
- **Después:** Nota explícita de que EVM muestra "—" si faltan presupuesto, timesheets, fechas o tarifas. Se documenta que las tarifas SÍ tienen UI (contra lo indicado en documentación del agente)
- **Razón:** El EVM muestra "—" frecuentemente y los usuarios necesitan saber por qué

### Cambio 24 — Tarifas de recurso: ubicación en UI
- **Sección:** 14.2 Tarifas de costo por recurso
- **Antes:** Documentadas como sin UI disponible; acceso desde "Tarifas de recurso"
- **Después:** Acceso desde tab Presupuesto → sección "Tarifas por Recurso" con CRUD completo
- **Razón:** La UI de tarifas existe y es accesible directamente desde el tab Presupuesto

### Cambio 25 — Gastos: ubicación en UI
- **Sección:** 14.3 Gastos del proyecto
- **Antes:** "Tab Presupuesto → sección Gastos"
- **Después:** "Tab Presupuesto → sección Gastos directos"
- **Razón:** La sección se llama "Gastos directos" en la interfaz

### Cambio 26 — Facturación
- **Sección:** 14.6 Facturación
- **Antes:** Flujo completo de generación de datos de factura con líneas de labor y gastos
- **Después:** Nota indicando que esta funcionalidad no está disponible en la versión actual
- **Razón:** No existe sección de Facturación en el tab Presupuesto

### Cambio 27 — Formulario de terceros
- **Sección:** 15.2 Crear un tercero
- **Antes:** 8 campos simples: Nombre/Razón social, Tipo, NIT/Cédula, Email, Teléfono, Ciudad, Dirección, Notas
- **Después:** Formulario estructurado en 4 secciones con 15 campos totales incluyendo tipo de persona, tipo de documento, campos separados para nombre y apellidos, teléfono fijo y celular por separado, dirección como sección opcional
- **Razón:** El formulario real tiene estructura muy diferente a la documentada

### Cambio 28 — Flujos de trabajo: referencias a Scheduling y Recursos
- **Secciones:** 16.1 y 16.2 Flujos recomendados
- **Antes:** Referencias a "tab Scheduling", "tab Recursos"
- **Después:** Referencias corregidas a ubicaciones reales
- **Razón:** Los tabs mencionados no existen con esos nombres

---

## Sección 7: Recomendaciones

### Funcionalidades faltantes de alta prioridad (a implementar próximamente)

1. **Módulo de Facturación** (Prioridad: Alta)
   - Generar datos para cobro al cliente agrupando horas × tarifa + gastos facturables
   - Actualmente el tab Hitos tiene hitos facturables pero no se vincula con el módulo de presupuesto

2. **Nivelación automática de recursos** (Prioridad: Alta)
   - El algoritmo existe en backend pero no tiene UI
   - Es necesaria para proyectos con equipos pequeños y muchas tareas paralelas

3. **Exportación a Excel del Analytics** (Prioridad: Media)
   - El botón de descarga existe pero la funcionalidad completa (4 hojas) no está implementada

### Mejoras al manual sugeridas

1. **Documentar el módulo de Configuración** (`/proyectos/configuracion`)
   - Los modos de timesheet (Manual/Cronómetro/Ambos/Desactivado) son críticos para el comportamiento del sistema
   - La configuración de integración con Saiopen afecta el cambio de estado de las tareas

2. **Documentar el tab Hitos facturables**
   - Los hitos con valor a facturar son una funcionalidad diferente a los hitos del Gantt
   - Necesitan documentación propia con flujo de creación, porcentajes y estados de factura

3. **Documentar el Dashboard de Proyectos** (`/proyectos/dashboard`)
   - Primera pantalla del módulo con KPIs globales y seguimiento por proyecto
   - No está documentado en el manual

4. **Agregar capturas de pantalla reales**
   - El manual describe funcionalidades sin imágenes de referencia
   - Los usuarios se confunden cuando los nombres de elementos difieren ligeramente

5. **Clarificar la diferencia entre "Hitos del Gantt" y "Hitos facturables"**
   - Existen dos tipos de hito en la plataforma: tareas marcadas como hito (se muestran como diamante en Gantt) y hitos del tab Hitos (con valor a facturar)
   - Esta diferencia es confusa para usuarios nuevos

### Próximos pasos

1. Actualizar la sección 3 del manual con descripción del Dashboard de proyectos
2. Crear sección nueva "20. Configuración del Módulo" basada en `/proyectos/configuracion`
3. Expandir la documentación del tab Hitos facturables como sección propia
4. Coordinarse con el equipo de desarrollo para fecha de implementación de nivelación y facturación
5. Programar revisión del manual cada 2 meses o tras cambios significativos de UI

---

## Apéndice: Rutas validadas en la auditoría

| Ruta | Estado | Observación |
|---|---|---|
| `/proyectos/dashboard` | Funciona | Dashboard global del módulo (no documentado en manual) |
| `/proyectos/lista` | Funciona | Lista de proyectos en vista tabla |
| `/proyectos/cards` | Funciona | Lista de proyectos en vista cards |
| `/proyectos/nuevo` | Funciona | Formulario de creación de proyecto |
| `/proyectos/:id` | Funciona | Detalle del proyecto con 14 tabs |
| `/proyectos/tareas` | Funciona | Lista global de tareas |
| `/proyectos/tareas/:id` | Funciona | Detalle de tarea individual |
| `/proyectos/tareas/nueva` | Funciona | Formulario de nueva tarea |
| `/proyectos/mis-tareas` | Funciona | Tareas asignadas al usuario actual |
| `/proyectos/timesheets` | Funciona | Vista semanal de registro de horas |
| `/proyectos/actividades` | Funciona | Catálogo de actividades |
| `/proyectos/configuracion` | Funciona | Configuración del módulo |
| `/terceros` | Funciona | Lista de terceros |
| `/terceros/nuevo` | Funciona | Formulario de nuevo tercero (estructura diferente al manual) |

---

*Informe generado por: Agente Gestor de Proyectos Saicloud*
*Fecha: 31 de Marzo de 2026*
