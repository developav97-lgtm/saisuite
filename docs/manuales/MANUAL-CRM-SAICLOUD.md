---
title: Manual de Usuario — SaiCRM
module: crm
category: manual
source: ValMen Tech — SaiCloud
---

# Manual de Usuario — SaiCRM

**Versión:** 1.1 — Abril 2026 (v2: actividades en lead, agenda, round-robin)
**Elaborado por:** ValMen Tech
**Plataforma:** SaiSuite / Saicloud
**Stack:** Django 5 + Angular 18 + Angular Material

---

## Tabla de Contenidos

1. [Introducción](#1-introducción)
2. [Acceso al Módulo](#2-acceso-al-módulo)
3. [Conceptos Fundamentales](#3-conceptos-fundamentales)
4. [Pipeline Kanban](#4-pipeline-kanban)
5. [Gestión de Leads](#5-gestión-de-leads)
6. [Gestión de Oportunidades](#6-gestión-de-oportunidades)
7. [Actividades](#7-actividades)
8. [Timeline y Notas](#8-timeline-y-notas)
9. [Cotizaciones](#9-cotizaciones)
10. [Dashboard CRM](#10-dashboard-crm)
11. [Agenda](#11-agenda)
12. [Flujos de Trabajo Recomendados](#12-flujos-de-trabajo-recomendados)
13. [Glosario](#13-glosario)

---

## 1. Introducción

SaiCRM es el módulo de gestión de ventas de SaiSuite. Permite gestionar el ciclo completo de una venta: desde la captación de un prospecto (lead) hasta el cierre y emisión de la cotización formal.

### ¿Qué puedes hacer con SaiCRM?

- Visualizar tu pipeline de ventas en un tablero Kanban con arrastrar y soltar
- Registrar y calificar leads (prospectos) de distintas fuentes
- Asignar leads a vendedores automáticamente con **Round-Robin**
- Programar actividades directamente sobre leads (antes de convertirlos)
- Convertir leads en oportunidades de venta
- Programar y completar actividades sobre cada oportunidad (llamadas, reuniones, emails, tareas)
- Ver tu **Agenda** unificada: todas las actividades (de leads y oportunidades) en un rango de fechas
- Registrar notas y ver el historial completo de cada oportunidad en el Timeline
- Crear, enviar y gestionar cotizaciones formales ligadas a cada oportunidad
- Ver métricas globales del equipo de ventas en el Dashboard

### Lo que NO está en esta versión

- Gestión de pipelines y etapas desde la UI (se administra internamente — ya viene preconfigurado)
- Reglas de scoring automático (configuración interna)
- Sincronización automática con Saiopen (se activa por empresa, es transparente al usuario)

---

## 2. Acceso al Módulo

### Requisito previo

El módulo CRM debe estar habilitado en la licencia de tu empresa. Si el card de CRM aparece con la etiqueta **"Próximamente"** en el selector de módulos, contacta a tu administrador.

### Ingresar al CRM

1. Inicia sesión en SaiCloud
2. En el selector de módulos (`/dashboard`) haz clic en el card **CRM**
3. Serás redirigido al Pipeline Kanban (`/crm`)

### Navegación

El menú lateral contextual del CRM tiene tres secciones:

| Opción | Ruta | Descripción |
|--------|------|-------------|
| Pipeline | `/crm` | Tablero Kanban principal |
| Leads | `/crm/leads` | Lista de prospectos |
| Dashboard | `/crm/dashboard` | Métricas y forecast |

---

## 3. Conceptos Fundamentales

### Pipeline

Un pipeline es el proceso de ventas de tu empresa, representado como una secuencia de etapas. Cada oportunidad avanza por las etapas a medida que la negociación progresa.

Ejemplo de pipeline típico:
```
Prospecto → Contactado → Propuesta enviada → Negociación → Ganado / Perdido
```

### Etapa

Cada fase del pipeline. Las etapas tienen:
- **Probabilidad (%):** qué tan probable es cerrar desde esa etapa (usado en el forecast)
- **Color:** identificador visual en el Kanban
- **Etapa ganado:** mover una oportunidad aquí la cierra como **ganada**
- **Etapa perdido:** mover una oportunidad aquí la cierra como **perdida**

### Lead

Un prospecto en etapa de calificación. Un lead puede:
- Crearse manualmente
- Importarse masivamente desde un CSV
- Tener actividades programadas (llamadas, emails, etc.) directamente sobre él
- Asignarse automáticamente a un vendedor vía **Round-Robin**
- Convertirse en una **Oportunidad** cuando hay interés real

### Oportunidad

Una negociación activa con un cliente. Es el núcleo del CRM. Tiene valor económico estimado, etapa actual, responsable y todas las interacciones (actividades, notas, cotizaciones).

### Actividad

Una tarea programada sobre una **oportunidad o un lead**: llamada, reunión, email, tarea o WhatsApp. Tienen fecha de vencimiento y se marcan como completadas registrando el resultado.

### Agenda

Vista unificada de todas las actividades del equipo (de leads y de oportunidades) en un rango de fechas. Permite ver el día de trabajo completo sin importar en qué etapa del proceso está cada prospecto.

### Round-Robin

Mecanismo de asignación equitativa de leads a vendedores. El sistema asigna automáticamente al vendedor con menos leads activos en ese momento, distribuyendo la carga de trabajo de forma balanceada.

### Cotización

Documento comercial formal asociado a una oportunidad. Tiene líneas de detalle con productos/servicios, valores, impuestos y un ciclo de vida: Borrador → Enviada → Aceptada o Rechazada.

---

## 4. Pipeline Kanban

### Acceso

Menú lateral → **Pipeline** o URL `/crm`

### Vista general

El Kanban muestra columnas por etapa. Cada columna tiene:
- Nombre de la etapa y color identificador
- Número de oportunidades y valor total en la parte superior
- Cards de oportunidades con: nombre, valor, probabilidad y próxima actividad

### Cambiar de Pipeline

Si tu empresa tiene más de un pipeline, usa el selector **"Pipeline"** en la barra superior para cambiar de vista.

### Mover una Oportunidad (Drag & Drop)

1. Haz clic y mantén presionado sobre un card de oportunidad
2. Arrástralo a la columna de la etapa destino
3. Suéltalo — el sistema actualizará la etapa automáticamente
4. Si la etapa destino es la **etapa de ganado**, la oportunidad se marca como **Ganada**
5. Si es la **etapa de perdido**, la oportunidad se marca como **Perdida**

> **Nota:** El cambio de etapa queda registrado automáticamente en el Timeline de la oportunidad.

### Abrir una Oportunidad

Haz clic sobre el título del card para ir al detalle completo de la oportunidad.

### Crear una Oportunidad desde el Kanban

Botón **"Nueva Oportunidad"** (ícono `+`) en la barra superior → formulario de creación.

---

## 5. Gestión de Leads

### Acceso

Menú lateral → **Leads** o URL `/crm/leads`

### Lista de Leads

La vista muestra una tabla con:
- Nombre, empresa, email, teléfono
- Fuente (Manual, CSV, Webhook, Referido, Otro)
- Score de calificación (0–100)
- Vendedor asignado
- Estado: activo o convertido

### Filtros disponibles

| Filtro | Ubicación | Descripción |
|--------|-----------|-------------|
| Búsqueda | Campo de texto | Filtra por nombre, empresa o email |
| Fuente | Selector | Filtra por origen del lead |
| Paginación | Parte inferior | 20 registros por página (ajustable) |

### Crear un Lead manualmente

1. Botón **"Nuevo Lead"** (parte superior derecha)
2. Rellena el formulario:
   - **Nombre** *(obligatorio)*
   - **Empresa**
   - **Email**
   - **Teléfono**
   - **Cargo**
   - **Fuente** *(obligatorio)*: origen del lead
   - **Pipeline objetivo:** pipeline al que se convertirá si avanza
   - **Notas**
3. Clic en **"Guardar"**

### Editar un Lead

1. En la tabla, menú de acciones (ícono `⋮`) → **Editar**
2. Se abre el mismo formulario pre-rellenado
3. Modifica los campos necesarios → **"Guardar"**

### Importar Leads desde CSV

1. Botón **"Importar CSV"** (ícono de nube con flecha)
2. Selecciona o arrastra tu archivo `.csv`
3. El sistema muestra una **vista previa** de los registros detectados
4. Revisa los datos y haz clic en **"Importar"**
5. Recibirás un resumen: cuántos se crearon y si hubo errores

**Formato esperado del CSV:** columnas `nombre`, `email`, `telefono`, `empresa`, `cargo`, `fuente`, `notas`. El separador puede ser coma o punto y coma.

### Asignación Automática de Leads (Round-Robin)

Puedes asignar vendedores a los leads automáticamente, sin hacerlo uno a uno.

**Asignar un lead individual:**
1. En la tabla de leads, busca el ícono `person_add` en la fila del lead (aparece solo si el lead no tiene vendedor asignado)
2. Clic en el ícono — el sistema asigna automáticamente al vendedor con menos leads
3. Se muestra un mensaje con el nombre del vendedor asignado

**Asignación masiva:**
1. Botón **"Auto-asignar"** en la parte superior de la lista de leads
2. El sistema asigna todos los leads sin vendedor usando round-robin
3. Recibirás un mensaje con el número de leads asignados (ej: "5 leads asignados")

> Si no hay vendedores activos en la empresa, el sistema no asigna ningún lead y muestra un aviso.

### Actividades en un Lead

Puedes programar actividades directamente sobre un lead, antes de convertirlo en oportunidad.

**Ver actividades del lead:**
1. En la tabla, menú `⋮` → **Ver actividades** (o desde la vista de detalle del lead)
2. Se muestra la lista de actividades programadas

**Crear una actividad en un lead:**
1. En la lista de actividades del lead, clic en **"Nueva Actividad"**
2. Selecciona tipo, título y fecha programada
3. Clic en **"Crear"**

**Filtrar por pendientes:**
- Activa el filtro **"Solo pendientes"** para ver solo las actividades no completadas

> Las actividades de un lead **no** aparecen en el Timeline de oportunidad (el Timeline es exclusivo de oportunidades). Sí aparecen en la [Agenda](#11-agenda).

### Convertir un Lead en Oportunidad

Cuando un lead muestra interés real:

1. En la tabla, menú `⋮` → **Convertir a Oportunidad**
2. En el diálogo selecciona:
   - **Etapa inicial** del pipeline
   - **Valor estimado** de la oportunidad (opcional)
3. Clic en **"Convertir"**
4. El lead se marca como **Convertido** y se crea la oportunidad automáticamente
5. El sistema navega al detalle de la nueva oportunidad

> Una vez convertido, el lead no puede volver al estado activo.

---

## 6. Gestión de Oportunidades

### Crear una Oportunidad

Desde el Kanban (botón `+`) o desde `/crm/oportunidades/nueva`:

| Campo | Obligatorio | Descripción |
|-------|-------------|-------------|
| Título | Sí | Nombre descriptivo de la negociación |
| Pipeline | Sí | Pipeline al que pertenece |
| Etapa | Sí | Etapa inicial (se carga al seleccionar pipeline) |
| Contacto | No | Cliente del módulo Terceros |
| Valor esperado | Sí | Valor económico estimado en pesos |
| Probabilidad | Sí | % de cierre (se hereda de la etapa, ajustable) |
| Fecha estimada de cierre | No | Fecha objetivo |
| Responsable | No | Vendedor asignado |
| Descripción | No | Notas internas |

### Detalle de una Oportunidad

Al abrir una oportunidad verás:

**Encabezado:**
- Título y etapa actual (con color)
- Contacto y responsable
- Valor esperado
- Botones de acción: **Ganar** / **Perder** (o badge si ya está cerrada)

**Tabs:**
1. [Timeline](#8-timeline-y-notas) — historial de eventos y notas
2. [Actividades](#7-actividades) — tareas programadas
3. [Cotizaciones](#9-cotizaciones) — propuestas comerciales

### Ganar una Oportunidad

1. En el encabezado, clic en **"Ganar"**
2. La oportunidad se mueve a la etapa de ganado y se registra la fecha de cierre
3. Se muestra badge **"Ganada"** y los botones desaparecen

### Perder una Oportunidad

1. Clic en **"Perder"**
2. En el diálogo ingresa el **motivo de pérdida** (obligatorio)
3. Clic en **"Confirmar pérdida"**
4. La oportunidad se mueve a la etapa de perdido y se registra el motivo

> Tanto ganar como perder quedan registrados en el Timeline automáticamente.

### Editar una Oportunidad

Desde el listado de oportunidades o URL `/crm/oportunidades/:id/editar`. Mismos campos que el formulario de creación.

---

## 7. Actividades

Las actividades son tareas programadas sobre una oportunidad: llamadas a realizar, reuniones agendadas, emails a enviar, etc.

### Ver actividades de una oportunidad

En el detalle de la oportunidad → tab **"Actividades"**

La lista muestra:
- Tipo de actividad (ícono)
- Título
- Fecha programada
- Responsable (si tiene)
- Resultado (si está completada)

### Crear una Actividad

1. Tab **"Actividades"** → botón **"Nueva Actividad"**
2. En el diálogo completa:

| Campo | Obligatorio | Descripción |
|-------|-------------|-------------|
| Tipo | Sí | Llamada, Reunión, Email, Tarea, WhatsApp, Otro |
| Título | Sí | Descripción breve (mínimo 3 caracteres) |
| Fecha programada | Sí | No puede ser una fecha pasada |
| Descripción | No | Detalles adicionales |

3. Clic en **"Crear Actividad"**

> Al crear una actividad se registra automáticamente un evento en el Timeline de la oportunidad.

### Completar una Actividad

1. En la lista de actividades, clic en el ícono `✓` (círculo) de la actividad pendiente
2. En el diálogo escribe el **resultado** de la actividad (qué ocurrió)
3. Clic en **"Completar"**
4. La actividad aparece marcada como completada con su resultado
5. Se registra un evento `actividad_completada` en el Timeline

### Tipos de actividad disponibles

| Tipo | Ícono | Uso recomendado |
|------|-------|-----------------|
| Llamada | Teléfono | Llamadas telefónicas |
| Reunión | Grupo | Reuniones presenciales o virtuales |
| Email | Sobre | Correos importantes a registrar |
| Tarea | Check | Tareas administrativas o de seguimiento |
| WhatsApp | Chat | Mensajes de WhatsApp |
| Otro | `···` | Cualquier actividad no categorizada |

---

## 8. Timeline y Notas

El Timeline es el historial completo e inmutable de todo lo que ha ocurrido en una oportunidad. No se puede eliminar ningún evento.

### Ver el Timeline

Detalle de la oportunidad → tab **"Timeline"** (primera pestaña)

Los eventos aparecen en orden cronológico descendente (el más reciente arriba). Cada evento muestra:
- Ícono del tipo de evento
- Descripción del evento
- Usuario que lo generó (o "Sistema" si fue automático)
- Fecha y hora

### Tipos de eventos que aparecen en el Timeline

| Tipo | ¿Cuándo aparece? | ¿Automático? |
|------|------------------|--------------|
| **Nota** | Al agregar una nota manualmente | No |
| **Cambio de etapa** | Al mover la oportunidad entre etapas | Sí |
| **Ganada / Perdida** | Al ganar o perder la oportunidad | Sí |
| **Actividad programada** | Al crear una nueva actividad | Sí |
| **Actividad completada** | Al marcar una actividad como completada | Sí |
| **Cotización creada** | Al crear una cotización | Sí |
| **Cotización aceptada** | Al aceptar una cotización | Sí |
| **Lead convertido** | Cuando la oportunidad viene de un lead | Sí |
| **Sistema** | Al crear la oportunidad, otros eventos automáticos | Sí |

### Agregar una Nota

1. En el tab Timeline, escribe en el campo de texto **"Agregar nota..."**
2. La nota debe tener mínimo 3 caracteres
3. Clic en el botón **Enviar** (ícono ➤)
4. La nota aparece inmediatamente al tope del Timeline

> Las notas son visibles para todos los usuarios con acceso al CRM de la empresa.

---

## 9. Cotizaciones

Las cotizaciones son documentos comerciales formales ligados a una oportunidad.

### Ver cotizaciones de una oportunidad

Detalle de la oportunidad → tab **"Cotizaciones"**

La lista muestra número, título, estado y valor total de cada cotización.

### Crear una Cotización

1. Tab **"Cotizaciones"** → botón **"Nueva Cotización"**
2. El sistema crea automáticamente una cotización en estado **Borrador** y te lleva al editor

### Editor de Cotización

El editor tiene dos secciones principales:

**Panel izquierdo — Líneas de detalle:**
- Botón **"Agregar línea"** para añadir productos o servicios
- Por cada línea puedes ingresar:
  - Descripción del producto/servicio
  - Cantidad
  - Precio unitario
  - Descuento por línea (%)
  - Impuesto (IVA u otro, según catálogo de tu empresa)
- Botón `×` para eliminar una línea
- Los totales se actualizan automáticamente

**Panel derecho — Resumen y acciones:**
- Subtotal, descuento adicional global, IVA total y **Total**
- Campo de notas y términos/condiciones
- Validez en días (por defecto 30)

### Ciclo de vida de la Cotización

```
BORRADOR → [Enviar] → ENVIADA → [Aceptar] → ACEPTADA
                              → [Rechazar] → RECHAZADA
```

**Enviar cotización:**
1. Clic en **"Enviar"**
2. Opcionalmente ingresa un email destino (si no, usa el email del contacto)
3. El estado cambia a **Enviada**

**Aceptar cotización:**
1. Clic en **"Aceptar"**
2. El estado cambia a **Aceptada**
3. Se registra en el Timeline automáticamente
4. Si la empresa tiene integración Saiopen activa, la cotización se sincroniza al ERP

**Rechazar cotización:**
1. Clic en **"Rechazar"**
2. El estado cambia a **Rechazada**

**Descargar PDF:**
- Botón **"PDF"** en el editor — genera y descarga el documento en formato PDF

### Estados de la Cotización

| Estado | Color | Descripción |
|--------|-------|-------------|
| Borrador | Gris | En edición, no enviada aún |
| Enviada | Azul | Enviada al cliente, pendiente de respuesta |
| Aceptada | Verde | Cliente aprobó la propuesta |
| Rechazada | Rojo | Cliente rechazó la propuesta |
| Vencida | Naranja | Expiró el plazo de validez |
| Anulada | Gris oscuro | Anulada manualmente |

> Solo las cotizaciones en estado **Borrador** permiten editar las líneas.

---

## 10. Dashboard CRM

### Acceso

Menú lateral → **Dashboard** o URL `/crm/dashboard`

### Métricas disponibles

**KPIs principales (tarjetas superiores):**

| Métrica | Descripción |
|---------|-------------|
| Total de leads | Leads registrados en la empresa |
| Leads nuevos (mes) | Leads creados en el mes actual |
| Oportunidades activas | Oportunidades abiertas (no ganadas ni perdidas) |
| Valor total activo | Suma del valor esperado de todas las oportunidades abiertas |
| Tasa de conversión | % de leads que se convirtieron en oportunidad |
| Forecast | Suma ponderada: valor × probabilidad de cada oportunidad activa |

**Embudo de ventas (Funnel):**
- Vista visual de cuántas oportunidades hay en cada etapa
- Muestra cantidad y valor total por etapa

**Rendimiento de vendedores:**
- Por cada vendedor: oportunidades activas, ganadas este mes, perdidas este mes, valor ganado

**Forecast detallado:**
- Total forecast (ponderado) vs total valor esperado (sin ponderar)
- Desglose por etapa: cuántas oportunidades, valor esperado, valor ponderado

---

## 11. Agenda

La Agenda es tu vista unificada de actividades del día o de cualquier rango de fechas. Reúne actividades tanto de leads como de oportunidades en un solo lugar.

### Acceso

Menú lateral → **Agenda** o URL `/crm/agenda`

### Usar la Agenda

1. Selecciona un rango de fechas con **"Desde"** y **"Hasta"**
2. La lista muestra todas las actividades del equipo en ese período
3. Cada actividad indica si pertenece a un **lead** o a una **oportunidad** (`contexto_tipo`)
4. Puedes ver el nombre del lead u oportunidad asociada (`contexto_nombre`)

### Filtrar solo pendientes

Activa el toggle **"Solo pendientes"** para ver únicamente las actividades que aún no se han completado.

### ¿Qué aparece en la Agenda?

| Tipo de actividad | ¿Aparece? |
|-------------------|-----------|
| Actividades de oportunidad | ✅ Sí |
| Actividades de lead | ✅ Sí |
| Actividades completadas | Solo si "Solo pendientes" está desactivado |
| Actividades de otras empresas | ❌ No (aislamiento automático) |

---

## 12. Flujos de Trabajo Recomendados

### Flujo 1: Lead → Oportunidad → Cierre

```
1. Registrar lead (manual o CSV)
2. Calificar: ¿tiene interés real? → Convertir a Oportunidad
3. En la oportunidad:
   a. Programar primera actividad (llamada o reunión)
   b. Agregar notas de cada interacción
   c. Avanzar etapas en el Kanban
4. Cuando hay acuerdo de precio:
   a. Crear cotización con las líneas acordadas
   b. Enviar cotización al cliente
5. Cliente responde:
   a. Acepta → Aceptar cotización → Ganar oportunidad
   b. Negocia → Crear nueva cotización con ajustes
   c. Rechaza → Registrar motivo → Perder oportunidad
```

### Flujo 2: Seguimiento de oportunidades activas

```
1. Abrir Pipeline Kanban → vista general del estado
2. Identificar oportunidades sin actividades pendientes
3. Para cada una: crear actividad de seguimiento
4. Al completar cada actividad: registrar resultado
5. Revisar Dashboard semanalmente para ajustar forecast
```

### Flujo 3: Importación masiva de leads

```
1. Preparar CSV con columnas: nombre, email, telefono, empresa, cargo, fuente
2. Leads → "Importar CSV" → Seleccionar archivo
3. Revisar vista previa → confirmar
4. Calificar los leads importados (score manual o por reglas)
5. Botón "Auto-asignar" → asignar leads a vendedores automáticamente
6. Convertir los leads calificados a oportunidades
```

### Flujo 4: Seguimiento de leads con agenda

```
1. Abrir Agenda → seleccionar rango de fechas (ej: esta semana)
2. Activar "Solo pendientes"
3. Identificar actividades de leads y oportunidades sin resolver
4. Completar actividades registrando el resultado
5. Para leads sin actividad próxima → crear nueva actividad de seguimiento
```

---

## 13. Glosario

| Término | Definición |
|---------|-----------|
| **Pipeline** | Proceso de ventas representado como secuencia de etapas |
| **Etapa** | Fase dentro del pipeline (ej: Prospecto, Propuesta, Cierre) |
| **Lead** | Prospecto en etapa de calificación, aún no es oportunidad |
| **Oportunidad** | Negociación activa con un cliente, con valor económico estimado |
| **Score** | Puntaje de calificación del lead (0–100) |
| **Conversión** | Transformar un lead en una oportunidad de venta |
| **Actividad** | Tarea programada sobre una oportunidad (llamada, reunión, etc.) |
| **Timeline** | Historial inmutable de todos los eventos de una oportunidad |
| **Cotización** | Documento comercial formal con productos, precios e impuestos |
| **Forecast** | Proyección de ingresos = suma de (valor × probabilidad) de oportunidades activas |
| **Valor ponderado** | Valor esperado × probabilidad de cierre de la etapa |
| **Etapa ganado** | Etapa especial que cierra la oportunidad como ganada |
| **Etapa perdido** | Etapa especial que cierra la oportunidad como perdida |
| **Saiopen** | ERP Windows/Firebird con el que SaiCloud se integra vía SQS |
| **Round-Robin** | Asignación equitativa de leads: el sistema elige al vendedor con menos leads activos |
| **Agenda** | Vista unificada de todas las actividades (leads + oportunidades) en un rango de fechas |
| **Asignación masiva** | Asignar todos los leads sin vendedor de una vez usando round-robin |

---

*Manual generado: 10 Abril 2026 — ValMen Tech*
*Actualizado: 10 Abril 2026 (v1.1) — v2 Sprint: actividades en lead, agenda, round-robin, asignación masiva*
*Módulo: SaiCRM v1.1 — Solo incluye funcionalidades implementadas y verificadas*
