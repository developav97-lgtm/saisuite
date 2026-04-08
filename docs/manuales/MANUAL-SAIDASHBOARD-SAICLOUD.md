---
title: Manual de Usuario — SaiDashboard
module: dashboard
category: manual
source: ValMen Tech — SaiCloud
---

# Manual de Usuario — SaiDashboard

**Version:** 1.0 — Abril 2026
**Elaborado por:** ValMen Tech
**Plataforma:** SaiSuite / Saicloud
**Stack:** Django 5 + Angular 18 + Angular Material + ECharts

---

## Tabla de Contenidos

1. [Introduccion](#1-introduccion)
2. [Acceso al Modulo](#2-acceso-al-modulo)
3. [Periodo de Prueba](#3-periodo-de-prueba)
4. [Lista de Dashboards](#4-lista-de-dashboards)
5. [Crear un Dashboard](#5-crear-un-dashboard)
6. [Constructor de Dashboard (Builder)](#6-constructor-de-dashboard-builder)
7. [Tipos de Tarjetas](#7-tipos-de-tarjetas)
8. [Tipos de Graficos](#8-tipos-de-graficos)
9. [Visualizar un Dashboard](#9-visualizar-un-dashboard)
10. [Filtros](#10-filtros)
11. [Exportar a PDF](#11-exportar-a-pdf)
12. [Compartir Dashboards](#12-compartir-dashboards)
13. [Favoritos y Dashboard Predeterminado](#13-favoritos-y-dashboard-predeterminado)
14. [CFO Virtual (Asistente IA)](#14-cfo-virtual-asistente-ia)
15. [Preguntas Frecuentes](#15-preguntas-frecuentes)

---

## 1. Introduccion

### 1.1 Que es SaiDashboard

SaiDashboard es el modulo de inteligencia de negocios (BI) de Saicloud. Permite a los usuarios construir dashboards financieros personalizados a partir de los datos contables de su empresa, con graficos interactivos, indicadores clave de rendimiento (KPI) y un asistente financiero impulsado por inteligencia artificial.

El modulo transforma la informacion contable de Saiopen en visualizaciones claras y accionables, sin necesidad de exportar datos a hojas de calculo ni herramientas externas.

### 1.2 Para quien esta disenado

SaiDashboard esta dirigido a:

- **Gerentes generales y directivos** que necesitan una vista consolidada de la salud financiera de la empresa.
- **Contadores y directores financieros** que analizan estados financieros, margenes, liquidez y endeudamiento.
- **Administradores de proyectos** que monitorean costos por proyecto y actividad contable.
- **Jefes de area** que requieren control de gastos por departamento o centro de costo.

### 1.3 Beneficios principales

| Beneficio | Descripcion |
|---|---|
| Dashboards personalizables | Cada usuario crea y organiza sus propios dashboards con las tarjetas que necesita |
| Catalogo de 22 tarjetas | Indicadores financieros predefinidos organizados en 6 categorias |
| Graficos interactivos | 8 tipos de grafico (barras, torta, lineas, KPI, tabla, area, cascada, indicador) |
| Filtros dinamicos | Filtre por periodo, tercero, proyecto, departamento o rango de fechas |
| Exportacion a PDF | Exporte cualquier dashboard como documento PDF para compartir o archivar |
| Dashboards compartidos | Comparta dashboards con otros usuarios de su empresa con control de permisos |
| CFO Virtual | Asistente financiero con IA que responde preguntas sobre la situacion financiera |
| Soporte dark mode | Todos los graficos y componentes se adaptan automaticamente al tema claro y oscuro |

---

## 2. Acceso al Modulo

### 2.1 Navegacion

1. Inicie sesion en Saicloud con sus credenciales.
2. En el menu lateral (sidebar), haga clic en **SaiDashboard**.
3. La plataforma lo llevara a la lista de dashboards en la ruta `/saidashboard`.

### 2.2 Requisitos de acceso

Para acceder al modulo SaiDashboard, su empresa debe tener una de las siguientes condiciones:

- **Licencia activa** que incluya el modulo `dashboard`.
- **Periodo de prueba activo** (14 dias, una sola vez por empresa).

Si ninguna de las dos condiciones se cumple, vera un banner informativo con la opcion de activar la prueba gratuita. Mientras no tenga acceso, el boton **Nuevo dashboard** permanecera deshabilitado.

---

## 3. Periodo de Prueba

### 3.1 Que incluye la prueba

El periodo de prueba otorga acceso completo a todas las funcionalidades de SaiDashboard durante **14 dias corridos**. Incluye:

- Crear y editar dashboards sin limite.
- Acceso a las 22 tarjetas del catalogo.
- Todos los tipos de grafico.
- Filtros, exportacion a PDF, compartir y CFO Virtual.

### 3.2 Como activar la prueba

1. Navegue a **SaiDashboard** desde el menu lateral.
2. Vera un banner con el mensaje: *"Modulo no disponible -- activa una prueba gratuita de 14 dias"*.
3. Haga clic en el boton **Activar prueba**.
4. El sistema confirmara la activacion con un mensaje: *"Prueba activada correctamente."*

### 3.3 Reglas importantes

- La prueba solo se puede activar **una vez por empresa**. No es posible renovarla ni reactivarla.
- Cualquier usuario de la empresa puede activar la prueba. Una vez activada, aplica para todos los usuarios de esa empresa.
- El banner superior muestra los dias restantes de la prueba y la fecha de expiracion.
- Cuando quedan **5 dias o menos**, el banner cambia a color naranja de advertencia.
- Al expirar la prueba, los dashboards creados se conservan pero no podra acceder a ellos hasta adquirir una licencia.

### 3.4 Adquirir licencia

Cuando el periodo de prueba este activo, el banner muestra un boton **Adquirir licencia** que lo dirige al proceso de contratacion.

---

## 4. Lista de Dashboards

La pagina principal de SaiDashboard muestra todos sus dashboards organizados en tres secciones.

### 4.1 Secciones de la lista

| Seccion | Descripcion |
|---|---|
| **Mis Favoritos** | Tarjetas destacadas de acceso rapido. Solo aparece si tiene al menos un favorito. |
| **Mis Dashboards** | Todos los dashboards que usted creo, con tabla o vista de tarjetas. |
| **Compartidos conmigo** | Dashboards que otros usuarios de su empresa han compartido con usted. |

### 4.2 Modos de visualizacion

La lista de dashboards ofrece dos modos de visualizacion. Su preferencia se guarda automaticamente en el navegador.

- **Vista de lista (tabla):** Muestra los dashboards en una tabla con columnas de titulo, cantidad de tarjetas, fecha de creacion y acciones. Haga clic en el boton **Cards** para cambiar a la vista de tarjetas.
- **Vista de tarjetas (cards):** Muestra cada dashboard como una tarjeta visual con titulo, descripcion, cantidad de tarjetas y fecha de creacion. Haga clic en el boton **Lista** para volver a la tabla.

### 4.3 Busqueda

Utilice el campo **Buscar dashboards...** ubicado debajo del banner de prueba. La busqueda filtra en tiempo real por titulo y descripcion, tanto en sus dashboards como en los compartidos.

### 4.4 Acciones disponibles en la lista

En la **vista de tabla**, cada fila tiene un boton de **Favorito** (estrella) y un menu de opciones (tres puntos) con las siguientes acciones:

| Accion | Descripcion |
|---|---|
| **Ver** | Abre el dashboard en modo visualizacion con todos los graficos cargados |
| **Editar** | Abre el constructor (builder) para modificar tarjetas y configuracion |
| **Predeterminado** | Marca este dashboard como su dashboard predeterminado |
| **Eliminar** | Elimina el dashboard tras confirmacion. Esta accion no se puede deshacer. |

En la **vista de tarjetas**, puede hacer clic en **Editar** o **Eliminar** directamente desde cada tarjeta.

Para abrir cualquier dashboard, haga clic sobre su fila (en tabla) o su tarjeta (en cards).

### 4.5 Dashboards compartidos conmigo

Los dashboards compartidos aparecen en una seccion separada con una etiqueta **Compartido** y el nombre del propietario. No puede eliminar ni editar dashboards compartidos a menos que el propietario le haya otorgado permiso de edicion.

---

## 5. Crear un Dashboard

1. En la lista de dashboards, haga clic en el boton **Nuevo dashboard**.
2. El sistema abrira el constructor (builder) en modo creacion.
3. Complete los campos del formulario:

| Campo | Obligatorio | Descripcion |
|---|---|---|
| **Titulo** | Si | Nombre del dashboard (maximo 255 caracteres) |
| **Descripcion** | No | Descripcion breve del proposito del dashboard (maximo 500 caracteres) |
| **Privado** | No | Si esta activado, solo usted y los usuarios con acceso compartido pueden verlo |

4. Agregue tarjetas desde el catalogo (ver seccion 6).
5. Haga clic en **Guardar** para crear el dashboard.

---

## 6. Constructor de Dashboard (Builder)

El constructor es la herramienta principal para disenar el contenido de un dashboard. Se accede desde la creacion de un nuevo dashboard o haciendo clic en **Editar** sobre un dashboard existente.

### 6.1 Interfaz del constructor

El constructor muestra:

- **Formulario superior:** Campos de titulo, descripcion y privacidad del dashboard.
- **Catalogo de tarjetas:** Listado de categorias con las tarjetas disponibles para agregar.
- **Area de tarjetas:** Las tarjetas agregadas al dashboard, que se pueden reordenar arrastrando.

### 6.2 Agregar tarjetas

Hay dos formas de agregar tarjetas:

**Desde el catalogo lateral:**
1. Navegue por las categorias del catalogo en el panel de expansion.
2. Haga clic sobre la tarjeta que desea agregar.
3. La tarjeta se anadira al final de la lista con su tipo de grafico predeterminado.

**Desde el selector de tarjetas (dialog):**
1. Haga clic en el boton de agregar tarjeta.
2. Se abrira un dialogo con todas las categorias y tarjetas disponibles, organizadas en pestanas.
3. Use el campo de busqueda para filtrar por nombre o descripcion.
4. Seleccione una tarjeta. Al seleccionarla, vera los tipos de grafico soportados.
5. Elija el tipo de grafico deseado.
6. Haga clic en **Agregar** para confirmar.

### 6.3 Reordenar tarjetas (Drag & Drop)

Arrastre las tarjetas para cambiar su orden dentro del dashboard. Tome la tarjeta desde cualquier punto y sueltela en la posicion deseada. El orden se recalcula automaticamente.

### 6.4 Redimensionar tarjetas

Cada tarjeta tiene controles para ajustar su ancho (`width`) y alto (`height`) en unidades de grilla. Los valores disponibles van desde 1 hasta el maximo de columnas del grid.

### 6.5 Personalizar titulo de tarjeta

Haga clic sobre el titulo de una tarjeta para editarlo. El titulo personalizado se mostrara en lugar del nombre predeterminado del catalogo.

### 6.6 Eliminar tarjetas

Haga clic en el boton de eliminar (icono de papelera) en la tarjeta. El sistema le pedira confirmacion antes de eliminarla.

### 6.7 Guardar y cambios sin guardar

- El constructor detecta automaticamente cuando tiene cambios sin guardar.
- Haga clic en **Guardar** para persistir todos los cambios (titulo, descripcion, privacidad, tarjetas y layout).
- Si intenta salir con cambios sin guardar, el sistema le advertira con un dialogo de confirmacion: *"Tienes cambios sin guardar. Si sales se perderan."*

### 6.8 Vista previa

Si esta editando un dashboard existente, puede hacer clic en **Vista previa** para verlo en modo visualizacion sin salir del editor.

---

## 7. Tipos de Tarjetas

El catalogo de SaiDashboard ofrece **22 tipos de tarjetas** organizadas en **6 categorias**. Las tarjetas disponibles dependen de la configuracion contable de su empresa: algunas requieren que la empresa tenga habilitadas funcionalidades especificas (departamentos, centros de costo, proyectos).

### 7.1 Estados Financieros

| Tarjeta | Descripcion | Graficos soportados |
|---|---|---|
| **Balance General** | Activos, pasivos y patrimonio de la empresa | Barras, Tabla, Cascada |
| **Estado de Resultados** | Ingresos menos costos y gastos igual utilidad | Cascada, Barras, Tabla |
| **Indicadores de Liquidez** | Razon corriente, prueba acida y capital de trabajo | KPI, Indicador, Tabla |
| **EBITDA** | Utilidad antes de intereses, impuestos, depreciacion y amortizacion | KPI, Lineas, Barras |
| **Ingresos vs Egresos** | Comparacion visual de ingresos contra egresos | Barras, Lineas, Area |
| **ROE / ROA** | Retorno sobre patrimonio y sobre activos | KPI, Indicador, Barras |
| **Endeudamiento** | Nivel de endeudamiento y concentracion de deuda | KPI, Indicador, Torta |

### 7.2 Costos y Gastos

| Tarjeta | Descripcion | Graficos soportados |
|---|---|---|
| **Costo de Ventas** | Total de costos de ventas del periodo | KPI, Lineas, Barras |
| **Margen Bruto y Neto** | Margenes de rentabilidad bruta y neta | KPI, Barras, Lineas |
| **Gastos Operacionales** | Desglose de gastos operacionales por grupo contable | Torta, Barras, Tabla |
| **Gastos por Departamento** | Distribucion de gastos por departamento | Barras, Torta, Tabla |
| **Gastos por Centro de Costo** | Distribucion de gastos por centro de costo | Barras, Torta, Tabla |

> **Nota:** Las tarjetas *Gastos por Departamento* y *Gastos por Centro de Costo* solo estan disponibles si su empresa tiene habilitada la funcionalidad de departamentos y centros de costo en la configuracion contable.

### 7.3 Cartera

| Tarjeta | Descripcion | Graficos soportados |
|---|---|---|
| **Cartera Total** | Total de cuentas por cobrar pendientes | KPI, Indicador, Barras |
| **Aging de Cartera** | Antiguedad de cartera por rangos de dias vencidos | Barras, Tabla, Torta |
| **Top Clientes por Saldo** | Clientes con mayor saldo pendiente | Barras, Tabla, Torta |
| **Movimiento por Tercero** | Debitos y creditos agrupados por tercero | Tabla, Barras |

### 7.4 Proveedores

| Tarjeta | Descripcion | Graficos soportados |
|---|---|---|
| **Cuentas por Pagar** | Total de obligaciones con proveedores | KPI, Indicador, Barras |
| **Aging de Proveedores** | Antiguedad de cuentas por pagar por rangos de dias | Barras, Tabla, Torta |
| **Top Proveedores por Saldo** | Proveedores con mayor saldo por pagar | Barras, Tabla, Torta |

### 7.5 Proyectos

| Tarjeta | Descripcion | Graficos soportados |
|---|---|---|
| **Costo por Proyecto** | Costos y gastos agrupados por proyecto contable | Barras, Torta, Tabla |
| **Costo por Actividad** | Costos y gastos agrupados por actividad contable | Barras, Torta, Tabla |

> **Nota:** Las tarjetas de Proyectos solo estan disponibles si su empresa tiene habilitada la funcionalidad de proyectos y actividades contables.

### 7.6 Comparativos

| Tarjeta | Descripcion | Graficos soportados |
|---|---|---|
| **Comparativo de Periodos** | Comparacion de ingresos, costos y gastos entre dos periodos | Barras, Tabla, Lineas |
| **Tendencia Mensual** | Evolucion mensual de ingresos, costos y utilidad | Lineas, Area, Barras |

---

## 8. Tipos de Graficos

SaiDashboard ofrece 8 tipos de grafico. No todos los tipos estan disponibles para todas las tarjetas; cada tarjeta define los graficos que soporta.

| Tipo | Nombre | Uso recomendado |
|---|---|---|
| `bar` | **Barras** | Comparar valores entre categorias. Ideal para ingresos, gastos, saldos. |
| `pie` | **Torta** | Mostrar proporciones y distribuciones. Ideal para composicion de gastos. |
| `line` | **Lineas** | Visualizar tendencias y evolucion en el tiempo. |
| `kpi` | **KPI** | Mostrar un valor numerico destacado con indicador de tendencia respecto al periodo anterior. |
| `table` | **Tabla** | Mostrar datos tabulares con detalle numerico completo. |
| `area` | **Area** | Similar a lineas pero con relleno. Ideal para visualizar volumenes acumulados. |
| `waterfall` | **Cascada** | Mostrar como un valor total se descompone en contribuciones positivas y negativas. Ideal para estado de resultados. |
| `gauge` | **Indicador** | Mostrar un valor porcentual sobre una escala visual de 0 a 100%. Ideal para indicadores de liquidez y endeudamiento. |

### 8.1 Tarjetas KPI

Las tarjetas de tipo KPI muestran:

- **Etiqueta:** El nombre del indicador en texto pequeno.
- **Valor principal:** El numero formateado en grande (moneda COP, porcentaje o numero).
- **Tendencia:** Si existe un valor anterior para comparar, se muestra una flecha hacia arriba (verde) o hacia abajo (roja) con el porcentaje de cambio.

### 8.2 Graficos interactivos

Los graficos de barras, lineas, area, torta, cascada e indicador son interactivos:

- **Tooltip:** Al pasar el mouse sobre un punto de datos, se muestra el valor exacto.
- **Leyenda:** Cuando hay multiples series de datos, aparece una leyenda que permite activar o desactivar series.
- **Pantalla completa:** Cada tarjeta de grafico tiene un menu con la opcion **Pantalla completa** que expande el grafico al tamano completo del monitor.
- **Responsive:** Los graficos se redimensionan automaticamente al cambiar el tamano de la ventana.
- **Dark mode:** Los graficos detectan automaticamente si el tema oscuro esta activo y ajustan colores de texto y fondo.

---

## 9. Visualizar un Dashboard

Al hacer clic sobre un dashboard en la lista, se abre la vista de visualizacion.

### 9.1 Estructura de la vista

La vista de un dashboard se organiza en dos zonas:

- **Fila de KPIs:** Las tarjetas configuradas con tipo de grafico KPI se agrupan en una fila horizontal en la parte superior.
- **Grilla de graficos:** Las tarjetas con otros tipos de grafico se distribuyen en una grilla responsive, respetando el ancho y alto configurado por cada tarjeta.

Si el dashboard no tiene tarjetas, se muestra un estado vacio con el boton **Configurar dashboard** que lleva al builder.

### 9.2 Barra de herramientas

La barra superior de la vista de dashboard contiene:

| Elemento | Descripcion |
|---|---|
| **Flecha atras** | Regresa a la lista de dashboards |
| **Titulo** | Nombre del dashboard |
| **Estrella (Favorito)** | Alterna el estado de favorito |
| **Filtros** | Abre o cierra el panel de filtros |
| **Menu de opciones** | Contiene: Editar, Compartir, Exportar PDF |

### 9.3 Carga de datos

Al abrir un dashboard, el sistema carga los datos de todas las tarjetas en paralelo. Cada tarjeta muestra una barra de progreso mientras sus datos se estan cargando. Si ocurre un error, la tarjeta muestra el mensaje *"Sin datos para mostrar"*.

---

## 10. Filtros

El panel de filtros permite refinar los datos mostrados en todas las tarjetas del dashboard.

### 10.1 Abrir el panel de filtros

Haga clic en el icono de **Filtros** (embudo) en la barra de herramientas del dashboard. El panel aparecera debajo de la barra, encima de las tarjetas.

### 10.2 Filtros disponibles

| Filtro | Descripcion |
|---|---|
| **Fecha desde / Fecha hasta** | Rango de fechas para filtrar los movimientos contables. Use los selectores de fecha (datepicker). |
| **Tercero** | Busqueda por autocompletado. Escriba el nombre o identificacion del tercero y seleccione de la lista de sugerencias. |
| **Proyecto** | Seleccione un proyecto contable del listado desplegable. Solo aparece si su empresa tiene proyectos contables. |
| **Departamento** | Seleccione un departamento del listado desplegable. Solo aparece si su empresa usa departamentos. |
| **Periodo contable** | Seleccione un periodo contable especifico del listado desplegable. |
| **Comparar con periodo anterior** | Interruptor que activa la comparacion con el periodo equivalente anterior. |

### 10.3 Accesos rapidos de periodo

El panel de filtros ofrece botones de acceso rapido para rangos de fecha comunes:

| Boton | Rango que aplica |
|---|---|
| **Mes actual** | Desde el primer dia hasta el ultimo dia del mes en curso |
| **Trimestre actual** | Desde el primer dia hasta el ultimo dia del trimestre en curso |
| **Ano actual** | Desde el 1 de enero hasta el 31 de diciembre del ano en curso |
| **Ano anterior** | Desde el 1 de enero hasta el 31 de diciembre del ano anterior |

### 10.4 Aplicar y limpiar filtros

- Haga clic en **Aplicar** para ejecutar los filtros seleccionados. Todas las tarjetas del dashboard se recargaran con los datos filtrados.
- Haga clic en **Limpiar todo** para remover todos los filtros activos y volver a los datos sin filtrar.
- Un indicador numerico muestra cuantos filtros tiene activos cuando el panel esta contraido.

---

## 11. Exportar a PDF

SaiDashboard permite exportar el contenido visual de un dashboard como un archivo PDF.

### 11.1 Como exportar

1. Abra el dashboard que desea exportar.
2. Haga clic en el icono de **menu de opciones** (tres puntos) en la barra de herramientas.
3. Seleccione **Exportar PDF**.
4. Espere mientras el sistema genera el archivo. Vera un indicador de progreso.
5. El archivo PDF se descargara automaticamente con el nombre del dashboard.

### 11.2 Consideraciones

- El PDF captura el estado actual del dashboard, incluyendo los filtros aplicados.
- Asegurese de que todas las tarjetas hayan terminado de cargar antes de exportar.
- El tiempo de generacion depende de la cantidad de tarjetas y la complejidad de los graficos.

---

## 12. Compartir Dashboards

Puede compartir sus dashboards con otros usuarios de la misma empresa.

### 12.1 Como compartir un dashboard

1. Abra el dashboard que desea compartir.
2. Haga clic en el **menu de opciones** (tres puntos) en la barra de herramientas.
3. Seleccione **Compartir**.
4. Se abrira el dialogo de compartir que muestra:
   - La lista de usuarios con los que ya esta compartido el dashboard.
   - Un selector para agregar nuevos usuarios.
5. Seleccione el usuario del listado desplegable.
6. Active o desactive el interruptor **Puede editar** segun el nivel de acceso que desea otorgar.
7. Haga clic en **Compartir**.
8. El sistema confirmara: *"Dashboard compartido correctamente."*

### 12.2 Niveles de permiso

| Permiso | Descripcion |
|---|---|
| **Solo lectura** (predeterminado) | El usuario puede ver el dashboard y sus datos, pero no puede modificar tarjetas ni configuracion |
| **Puede editar** | El usuario puede modificar el dashboard, agregar o quitar tarjetas, y cambiar la configuracion |

### 12.3 Revocar acceso

1. Abra el dialogo de **Compartir** del dashboard.
2. En la lista de usuarios compartidos, haga clic en el boton de eliminar junto al usuario al que desea revocar el acceso.
3. El sistema confirmara: *"Acceso revocado."*

### 12.4 Restricciones

- Solo el creador del dashboard puede compartirlo.
- Solo puede compartir con usuarios de la misma empresa.
- No puede compartir un dashboard consigo mismo.

---

## 13. Favoritos y Dashboard Predeterminado

### 13.1 Marcar como favorito

Puede marcar cualquier dashboard como favorito para acceder a el rapidamente.

**Desde la lista de dashboards:**
- Haga clic en el icono de **estrella** en la fila o tarjeta del dashboard.

**Desde la vista del dashboard:**
- Haga clic en el icono de **estrella** en la barra de herramientas.

Los dashboards favoritos aparecen en la seccion **Mis Favoritos** en la parte superior de la lista, presentados como tarjetas de acceso rapido.

Para quitar un dashboard de favoritos, haga clic nuevamente en la estrella.

### 13.2 Dashboard predeterminado

Puede designar un unico dashboard como predeterminado. El dashboard predeterminado aparece primero en la lista y se identifica con un icono de **pin** (chincheta).

**Para establecer un dashboard predeterminado:**

1. En la lista de dashboards (vista de tabla), haga clic en el **menu de opciones** del dashboard deseado.
2. Seleccione **Predeterminado**.
3. El sistema confirmara: *"Dashboard predeterminado actualizado."*

Solo puede haber un dashboard predeterminado por usuario. Al marcar uno nuevo como predeterminado, el anterior deja de serlo automaticamente.

> **Nota:** Solo el creador del dashboard puede marcarlo como predeterminado.

---

## 14. CFO Virtual (Asistente IA)

El CFO Virtual es un asistente financiero impulsado por inteligencia artificial que responde preguntas sobre la situacion financiera de su empresa utilizando los datos contables de los ultimos 12 meses.

### 14.1 Como acceder

El CFO Virtual esta disponible como un boton flotante (FAB) en la esquina inferior de la pantalla con un icono de robot. Haga clic en el para abrir el panel de conversacion.

### 14.2 Pantalla de bienvenida

Al abrir el CFO Virtual por primera vez en una sesion, vera:

- Un mensaje de bienvenida: *"Tu asistente financiero inteligente. Preguntame sobre la salud financiera de tu empresa."*
- Cuatro **acciones rapidas** predefinidas que puede usar como punto de partida:

| Accion rapida | Descripcion |
|---|---|
| **Como esta mi liquidez?** | Analisis de indicadores de liquidez |
| **Riesgo de endeudamiento?** | Evaluacion del nivel de deuda |
| **Resumen financiero del mes** | Resumen general del periodo actual |
| **Proyeccion de ingresos** | Estimacion basada en tendencias |

### 14.3 Como hacer preguntas

1. Escriba su pregunta en el campo de texto en la parte inferior del panel.
2. Presione **Enter** o haga clic en el boton **Enviar** (icono de flecha).
3. Tambien puede hacer clic en cualquiera de las acciones rapidas para enviar esa pregunta directamente.
4. El asistente mostrara una animacion de escritura mientras procesa su consulta.
5. La respuesta aparecera como un mensaje del asistente con la hora de generacion.

### 14.4 Contexto financiero

El CFO Virtual trabaja con un resumen financiero automatico que incluye los movimientos contables de su empresa agrupados por titulo contable (Activo, Pasivo, Patrimonio, Ingresos, Gastos, Costos, Costos de Produccion) de los ultimos 12 meses. No tiene acceso a datos individuales de transacciones ni a informacion de otros modulos.

### 14.5 Consideraciones

- El CFO Virtual es un asistente informativo. Sus respuestas no constituyen asesoria financiera profesional.
- Si el asistente no puede procesar una consulta (por timeout o error de conexion), mostrara el mensaje: *"Lo siento, no pude procesar tu consulta en este momento. Intenta de nuevo mas tarde."*
- Para cerrar el panel, haga clic en el boton de **cerrar** (X) en la esquina superior del panel o en el boton flotante.

---

## 15. Preguntas Frecuentes

### No puedo crear dashboards. El boton esta deshabilitado.

Su empresa no tiene acceso al modulo. Active la prueba gratuita de 14 dias haciendo clic en **Activar prueba** en el banner informativo, o contacte a su administrador para adquirir la licencia.

### No veo las tarjetas de Gastos por Departamento o Costo por Proyecto.

Estas tarjetas requieren que su empresa tenga habilitada la configuracion contable correspondiente (departamentos/centros de costo o proyectos/actividades). Contacte a su administrador de Saiopen para verificar la configuracion.

### Mi periodo de prueba expiro. Puedo reactivarlo?

No. El periodo de prueba solo se puede activar una vez por empresa. Para continuar utilizando SaiDashboard, debe adquirir una licencia.

### Como cambio el tipo de grafico de una tarjeta ya creada?

Abra el dashboard en modo edicion (builder) y puede modificar el tipo de grafico de cada tarjeta utilizando el selector de tipo de grafico.

### Los graficos no se ven correctamente en modo oscuro.

Los graficos detectan automaticamente el tema activo. Si acaba de cambiar de tema, recargue la pagina para que los graficos se reinicialicen con los colores correctos.

### Puedo compartir un dashboard con alguien de otra empresa?

No. Solo puede compartir dashboards con usuarios que pertenezcan a la misma empresa.

### Al exportar el PDF, algunos graficos aparecen en blanco.

Asegurese de que todas las tarjetas hayan terminado de cargar antes de exportar. Si un grafico muestra *"Sin datos para mostrar"*, no tendra contenido visual en el PDF.

### Como elimino un dashboard compartido conmigo?

No puede eliminar dashboards compartidos. Solo el creador del dashboard puede eliminarlo. Si ya no desea verlo en su lista, solicite al propietario que revoque el acceso.

---

**Ultima actualizacion:** Abril 2026
**Mantenido por:** Equipo Saicloud -- ValMen Tech
