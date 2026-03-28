# Feature 6 — Advanced Scheduling: Guía de Usuario

> Para gerentes de proyecto y coordinadores en SaiSuite.

---

## ¿Qué ofrece Feature 6?

Feature 6 agrega herramientas de programación avanzada al módulo de Proyectos:

| Herramienta | ¿Para qué sirve? |
|---|---|
| **Auto-Schedule** | Calcula automáticamente las fechas de inicio y fin de todas las tareas según dependencias |
| **Ruta crítica** | Resalta las tareas cuyo retraso impacta directamente la fecha de entrega del proyecto |
| **Holgura (Float)** | Muestra cuántos días puede retrasarse una tarea sin afectar el proyecto |
| **Baselines** | Guarda una foto del plan original para compararlo con el avance real |
| **Escenarios What-If** | Simula cambios hipotéticos ("¿qué pasa si esta tarea tarda 3 días más?") |
| **Restricciones de tarea** | Bloquea o fuerza fechas específicas en tareas individuales |

---

## Auto-Schedule

### ¿Cuándo usarlo?

- Al inicio del proyecto, después de crear todas las tareas y dependencias.
- Cuando el plan cambia y quieres recalcular fechas en bloque.

### Pasos

1. Abre el proyecto y haz clic en **Scheduling → Auto-Schedule** (botón en la cabecera del proyecto).
2. Elige el **modo**:
   - **ASAP** (As Soon As Possible): programa tareas lo antes posible. Recomendado para la mayoría de proyectos.
   - **ALAP** (As Late As Possible): programa tareas lo más tarde posible sin afectar la entrega.
3. Activa **Respetar restricciones** si tienes fechas fijadas en tareas (ej. "debe iniciar el 1 de abril").
4. Haz clic en **Calcular (previsualizar)** para ver los cambios propuestos sin guardarlos.
5. Revisa la tabla de previsualización. Cada fila muestra fecha anterior vs. fecha propuesta.
6. Si estás de acuerdo, haz clic en **Aplicar cambios**. Si no, cierra el diálogo sin cambios.

> **Nota:** Auto-Schedule no puede circular — si dos tareas se dependen mutuamente, mostrará un error de dependencia circular.

---

## Gantt — Overlays de Scheduling

En la pestaña **Gantt** del proyecto encontrarás tres botones de overlay:

### Ruta crítica

Haz clic en **Ruta crítica** para resaltar en rojo las tareas que forman la ruta crítica del proyecto. Estas tareas no tienen holgura — cualquier retraso en ellas retrasa el proyecto completo.

### Holgura (Float)

Haz clic en **Holgura** para ver cuántos días de margen tiene cada tarea. Las tareas críticas mostrarán `[CRÍTICA]` en su nombre. Las tareas con holgura mostrarán `[Float: Xd]`.

### Baseline

Haz clic en **Baseline** para ver qué baseline activo está siendo comparado. La información del baseline aparece como un chip debajo de la barra de controles. (Para ver la comparación detallada, usa la pestaña **Baselines**.)

---

## Baselines

### ¿Qué es un baseline?

Un baseline es una "fotografía" del plan del proyecto en un momento dado: fechas de inicio y fin de cada tarea. Te permite comparar el plan original con cómo va el proyecto en realidad.

### Crear un baseline

1. Ve a la pestaña **Baselines** del proyecto.
2. Haz clic en **+ Nuevo baseline**.
3. Dale un nombre descriptivo (ej. "Línea base contrato" o "Baseline semana 1").
4. Opcional: escribe una descripción.
5. Activa **Establecer como activo** si quieres que este sea el baseline de referencia en el Gantt.
6. Haz clic en **Guardar**.

### Comparar con el plan actual

1. Selecciona un baseline en el selector "Seleccionar baseline".
2. Haz clic en **Calcular comparación**.
3. Verás una tabla con:
   - **Fecha baseline**: fecha planeada original.
   - **Fecha actual**: fecha actual de la tarea.
   - **Variación**: diferencia en días (positivo = retraso, negativo = adelanto).
   - **Estado**: Adelantada / En plazo / Retrasada.
4. Los contadores de resumen arriba muestran cuántas tareas están en cada estado.

### Eliminar un baseline

Haz clic en el botón eliminar (icono de papelera) junto al baseline. El baseline activo no puede eliminarse — primero debes activar otro.

---

## Escenarios What-If

### ¿Para qué sirven?

Permiten simular "¿qué pasaría si...?" sin alterar el plan real del proyecto. Por ejemplo:
- ¿Qué pasa si la tarea de diseño tarda 5 días más?
- ¿Qué pasa si agrego un recurso extra a las instalaciones?

### Crear un escenario

1. Ve a la pestaña **Escenarios** del proyecto.
2. Haz clic en **+ Nuevo escenario**.
3. Escribe un nombre y descripción.
4. Haz clic en **Guardar**.
5. El escenario aparece en la tabla con estado "Sin simulación".

### Correr la simulación

1. Haz clic en el nombre del escenario para expandir sus detalles.
2. Haz clic en **Correr simulación**.
3. El sistema calculará las fechas proyectadas con los cambios del escenario.
4. Verás la fecha proyectada de fin y cuántos días de delta respecto al plan actual.

---

## Restricciones de tarea

Las restricciones fijan condiciones de fecha sobre una tarea individual, independientemente del Auto-Schedule.

### Tipos de restricción

| Código | Nombre | Descripción |
|---|---|---|
| ASAP | Lo antes posible | La tarea inicia lo antes que las dependencias lo permitan (por defecto) |
| ALAP | Lo más tarde posible | La tarea se programa al final del proyecto |
| SNET | Iniciar no antes de | La tarea no puede empezar antes de la fecha indicada |
| SNLT | Iniciar no después de | La tarea debe empezar antes de la fecha indicada |
| FNET | Terminar no antes de | La tarea no puede terminar antes de la fecha indicada |
| FNLT | Terminar no después de | La tarea debe terminar antes de la fecha indicada |
| MSO | Debe iniciar el | La tarea debe iniciar exactamente en la fecha indicada |
| MFO | Debe terminar el | La tarea debe terminar exactamente en la fecha indicada |

### Agregar una restricción

1. Abre el detalle de una tarea.
2. En el panel **Restricciones**, selecciona el tipo de restricción.
3. Si el tipo requiere fecha, selecciónala en el campo de fecha.
4. Haz clic en **Agregar**.

### Eliminar una restricción

Haz clic en el icono de papelera junto a la restricción. Esta acción no requiere confirmación.

---

## Preguntas frecuentes

**¿Auto-Schedule cambia todas las tareas?**
Solo cambia las tareas que tienen fechas inconsistentes con sus dependencias. Las tareas sin dependencias o que ya están en el orden correcto no se modifican.

**¿Puedo deshacer un Auto-Schedule?**
Sí. Antes de aplicar, usa la previsualización para revisar cambios. Si ya aplicaste y quieres revertir, crea un baseline antes de correr el Auto-Schedule — así puedes ver exactamente qué cambió.

**¿Qué pasa si hay una dependencia circular?**
El sistema la detecta y muestra un error. Debes revisar las dependencias de las tareas involucradas y eliminar el ciclo antes de correr el Auto-Schedule.

**¿Los escenarios what-if modifican el proyecto real?**
No. Los escenarios son simulaciones virtuales. El plan real del proyecto no cambia hasta que apliques manualmente los cambios que desees.

**¿Cuántos baselines puedo tener?**
No hay límite. Sin embargo, solo uno puede ser el "activo" (el que se muestra en el Gantt).
