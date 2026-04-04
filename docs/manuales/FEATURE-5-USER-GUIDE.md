# Guía de Analytics — SaiSuite

**Versión:** 1.0
**Fecha:** 27 Marzo 2026
**Dirigido a:** Gerentes de proyecto, coordinadores y supervisores

---

## ¿Qué son los Analytics?

Los Analytics de SaiSuite te muestran la salud de tus proyectos en tiempo real, sin necesidad de exportar datos ni armar hojas de cálculo manualmente. Con un solo clic puedes ver cuánto ha avanzado el equipo, si están cumpliendo los plazos, si el proyecto está dentro del presupuesto de horas y quién tiene más carga de trabajo.

Todo está calculado automáticamente a partir de las tareas, el tiempo registrado y las asignaciones de recursos que ya existen en el proyecto. No necesitas ingresar datos adicionales: los números se actualizan cada vez que consultas el panel.

Los Analytics están diseñados para responder tres preguntas clave en menos de un minuto:
1. ¿Vamos bien o mal en términos de avance?
2. ¿Estamos cumpliendo los plazos comprometidos?
3. ¿El equipo tiene la carga de trabajo distribuida de forma razonable?

---

## Cómo acceder

1. En el menú lateral, haz clic en **Proyectos**.
2. Abre el proyecto que quieres analizar haciendo clic en su nombre.
3. En la vista de detalle del proyecto, haz clic en la pestaña **Analytics**.
4. El panel cargará automáticamente todos los indicadores y gráficos.

Si el panel tarda más de unos segundos, es porque el proyecto tiene un gran volumen de tareas o registros de tiempo. La carga es normal y no requiere ninguna acción de tu parte.

---

## KPIs — Qué significa cada número

Los KPIs (indicadores clave de rendimiento) aparecen en la parte superior del panel. Son los números más importantes de un vistazo.

### Completud (%)

**Qué mide:** El porcentaje de tareas que ya están marcadas como "Completadas" sobre el total de tareas del proyecto.

**Ejemplo:** Si el proyecto tiene 40 tareas completadas de un total de 47, la completud es 85%.

**Cómo leerlo:**
- Verde (75% o más): El proyecto avanza bien.
- Amarillo (50%–74%): El avance es moderado; revisa si hay bloqueos.
- Rojo (menos de 50%): El proyecto tiene una brecha importante en avance.

**Cómo mejorar este número:** Marca las tareas como completadas en SaiSuite tan pronto terminen. Un número bajo puede simplemente significar que el equipo completó trabajo pero no lo registró.

---

### On-Time (%)

**Qué mide:** De todas las tareas ya completadas que tenían fecha límite, el porcentaje que se entregó antes de o en la fecha acordada.

**Ejemplo:** Si 10 de 14 tareas completadas con fecha límite se entregaron a tiempo, el On-Time es 71%.

**Advertencia importante:** Este indicador solo incluye tareas que tienen una fecha límite asignada y que ya están completadas. Si la mayoría de tus tareas no tienen fecha límite configurada, el indicador mostrará 0% o un porcentaje basado en una muestra pequeña. Asegúrate de que las tareas importantes tengan fecha límite definida.

**Cómo leerlo:**
- Verde (75% o más): El equipo cumple los compromisos con consistencia.
- Amarillo (50%–74%): Hay retrasos recurrentes; vale la pena revisar causas.
- Rojo (menos de 50%): Los plazos no se están cumpliendo. Se recomienda analizar bloqueos o ajustar la planificación.

---

### Velocidad (/sem)

**Qué mide:** El promedio de tareas que el equipo completa por semana, calculado sobre las últimas 4 semanas.

**Ejemplo:** Si en las últimas 4 semanas el equipo completó 12, 10, 14 y 11 tareas respectivamente, la velocidad es 11.75 tareas/semana.

**Por qué importa:** La velocidad te dice a qué ritmo trabaja el equipo en promedio. Si sabes que quedan 50 tareas y la velocidad es 10/semana, puedes estimar que faltan aproximadamente 5 semanas para terminar.

**Cómo usarlo:** Compara la velocidad actual con la velocidad necesaria para terminar a tiempo. Si el proyecto vence en 3 semanas y quedan 45 tareas, necesitas una velocidad de 15/semana — más alta que el promedio actual.

---

### Burn Rate (h/sem)

**Qué mide:** El promedio de horas registradas por semana en el proyecto durante las últimas 4 semanas. Se calcula a partir del tiempo que los miembros del equipo registran en SaiSuite.

**Ejemplo:** Si el equipo registró 38, 42, 35 y 41 horas en las últimas 4 semanas, el burn rate es 39 h/semana.

**Varianza de presupuesto:** Junto al burn rate verás también la varianza de presupuesto expresada como porcentaje. Este número compara las horas estimadas vs. las horas realmente registradas:
- Un número negativo (por ejemplo, -5%) significa que están usando menos horas de las estimadas — buena señal.
- Un número positivo (por ejemplo, +12%) significa que están usando más horas de las previstas — hay sobrecosto.

**Nota:** El burn rate solo refleja las horas que el equipo registra activamente. Si el equipo no está usando el módulo de registro de tiempo, este indicador aparecerá en 0.

---

## Cómo interpretar cada gráfico

### Burn Down

El Burn Down muestra cómo se está "quemando" el presupuesto de horas del proyecto semana a semana. Es el gráfico más importante para saber si el proyecto va bien en términos de esfuerzo.

El gráfico tiene tres líneas:

**Línea gris punteada — Ideal:** Cómo debería disminuir el trabajo si el avance fuera perfectamente uniforme. Es la referencia teórica.

**Línea azul — Estimadas restantes:** Las horas que aún no se han consumido del presupuesto total. Esta línea debería bajar progresivamente. Si sube, significa que hubo semanas sin trabajo registrado.

**Línea verde — Acumuladas reales:** Las horas que el equipo ha registrado en total hasta la fecha, acumuladas semana a semana.

**Cómo leerlo:** Si la línea azul está por encima de la gris, el proyecto va más lento de lo ideal. Si está por debajo, el ritmo es más rápido de lo planeado. Lo ideal es que ambas líneas se acerquen progresivamente al cero al final del proyecto.

---

### Velocidad del equipo

Este gráfico de barras muestra cuántas tareas completó el equipo en cada semana durante el período analizado.

**Barras verdes:** Semanas donde la producción estuvo por encima del promedio.

**Barras rojas:** Semanas donde la producción estuvo por debajo del promedio.

**Línea amarilla punteada:** El promedio de velocidad del período.

Semanas con barras rojas repetidas pueden indicar bloqueos, ausencias del equipo o acumulación de tareas en revisión. Si ves un patrón de 2 o 3 semanas rojas seguidas, vale la pena investigar qué pasó.

---

### Distribución de tareas

Este gráfico de dona muestra en qué estado se encuentran todas las tareas del proyecto en este momento.

**Colores:**
- Gris: Por hacer (todo)
- Azul: En progreso (in progress)
- Amarillo: En revisión (in review)
- Verde: Completadas (completed)
- Rojo: Bloqueadas (blocked)

Un proyecto saludable tiene la mayor parte del área en verde. Si hay mucha área roja (bloqueadas), el equipo necesita atención inmediata para desbloquear esas tareas.

---

### Utilización de recursos

Este gráfico de barras horizontales muestra el porcentaje de utilización de cada persona del equipo. La utilización compara las horas registradas con la capacidad disponible de cada persona.

**Colores:**
- Verde: Utilización saludable (70% o menos)
- Amarillo: Utilización alta pero manejable (71%–90%)
- Rojo: Persona sobrecargada (más del 90%)

Una persona al 120% no tiene tiempo libre para imprevistos y puede generar un cuello de botella. Una persona al 20% tiene capacidad disponible que podría redirigirse a tareas prioritarias.

**Nota:** Si alguna persona no aparece en el gráfico, significa que no tiene asignaciones activas en este proyecto.

---

## Exportar datos a Excel

El panel de analytics puede exportarse a un archivo Excel con tres hojas: un resumen general, el detalle de KPIs y la distribución de tareas.

**Pasos:**

1. Abre el proyecto y navega a la pestaña **Analytics**.
2. Haz clic en el botón **Exportar Excel** (ícono de descarga en la parte superior del panel).
3. El archivo se descargará automáticamente con el nombre `analytics-[id-proyecto].xlsx`.
4. Abre el archivo en Excel, Numbers o Google Sheets.

El archivo incluye tres hojas:
- **Summary:** Vista general con los KPIs principales de cada proyecto.
- **KPIs:** Detalle completo de indicadores, incluyendo burn rate.
- **Task Distribution:** Conteo de tareas por estado para cada proyecto.

**Comparación de proyectos:** Si quieres comparar varios proyectos en un solo Excel, usa la función de comparación antes de exportar. Selecciona hasta 20 proyectos y el archivo incluirá una fila por proyecto en cada hoja.

---

## Preguntas frecuentes

**¿Por qué mi On-Time sale 0%?**

Hay dos causas posibles:
1. Ninguna de las tareas completadas tiene una fecha límite asignada. El indicador solo puede calcularse cuando las tareas tienen fecha límite. Revisa si las tareas cuentan con el campo "Fecha límite" configurado.
2. El proyecto no tiene tareas completadas aún. El indicador requiere al menos una tarea completada con fecha límite para mostrar un valor distinto de cero.

---

**¿Cada cuánto se actualizan los datos?**

Los datos se calculan en tiempo real cada vez que abres o recargas el panel de Analytics. No hay caché ni datos del día anterior: lo que ves refleja el estado actual del proyecto en ese momento. Si alguien acaba de completar una tarea, el indicador de completud ya incluirá ese cambio cuando actualices la página.

---

**¿Puedo comparar proyectos?**

Sí. Desde la sección de Proyectos, usa la opción **Comparar proyectos** para seleccionar hasta 20 proyectos activos de tu empresa. El sistema muestra una tabla con los KPIs principales de cada uno lado a lado, lo que facilita identificar qué proyectos están en riesgo.

---

**¿Por qué el Burn Down no muestra datos históricos del inicio del proyecto?**

El Burn Down se calcula a partir de las fechas de inicio y fin del proyecto y de los registros de tiempo ingresados en SaiSuite. Si el proyecto inició antes de que el equipo comenzara a registrar tiempo en el sistema, las semanas anteriores aparecerán con 0 horas y la línea ideal no coincidirá con la realidad. Esto es esperado para proyectos que migraron a SaiSuite en medio de su ejecución.

---

**¿La velocidad del equipo incluye todas las tareas o solo las de una fase?**

Incluye todas las tareas del proyecto, sin importar en qué fase estén. Si quieres ver la velocidad por fase, puedes filtrar el tablero Kanban por fase y observar el avance de forma manual.

---

**¿Qué significa una varianza de presupuesto positiva?**

Una varianza positiva (por ejemplo, +15%) indica que el equipo ha registrado más horas de las estimadas originalmente. Puede significar que las estimaciones fueron optimistas, que surgieron imprevistos, o que hay trabajo no contemplado en el alcance original. Conviene revisar las tareas con mayor diferencia entre horas estimadas y registradas.

---

*Para soporte técnico o preguntas sobre el módulo, contacta al equipo de ValMen Tech en juan@valmentech.com*
