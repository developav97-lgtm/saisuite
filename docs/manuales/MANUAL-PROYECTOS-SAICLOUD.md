# Manual de Usuario — Saicloud

**Versión:** 1.1 — Marzo 2026 (Actualizado tras auditoría de implementación real)
**Elaborado por:** ValMen Tech
**Plataforma:** SaiSuite / Saicloud
**Stack:** Django 5 + Angular 18 + Angular Material

---

## Tabla de Contenidos

1. [Introducción](#1-introducción)
2. [Primeros Pasos](#2-primeros-pasos)
3. [Módulo Proyectos — Conceptos Fundamentales](#3-módulo-proyectos--conceptos-fundamentales)
4. [Gestión de Proyectos](#4-gestión-de-proyectos)
5. [Gestión de Fases](#5-gestión-de-fases)
6. [Gestión de Tareas](#6-gestión-de-tareas)
7. [Catálogo de Actividades](#7-catálogo-de-actividades)
8. [Dependencias entre Tareas](#8-dependencias-entre-tareas)
9. [Gantt](#9-gantt)
10. [Timesheets y Timer](#10-timesheets-y-timer)
11. [Resource Management](#11-resource-management)
12. [Reporting & Analytics](#12-reporting--analytics)
13. [Advanced Scheduling](#13-advanced-scheduling)
14. [Budget & Cost Tracking](#14-budget--cost-tracking)
15. [Terceros (Clientes y Proveedores)](#15-terceros-clientes-y-proveedores)
16. [Flujos de Trabajo Recomendados](#16-flujos-de-trabajo-recomendados)
17. [Mejores Prácticas](#17-mejores-prácticas)
18. [Troubleshooting](#18-troubleshooting)
19. [Glosario](#19-glosario)

---

## 1. Introducción

### 1.1 Qué es Saicloud

Saicloud es la plataforma web de gestión de proyectos empresariales desarrollada por **ValMen Tech** para el ecosistema **Saiopen** de Grupo SAI S.A.S. Es una solución SaaS (Software como Servicio) multi-tenant: cada empresa cliente tiene su propio espacio de datos completamente aislado, sin posibilidad de cruce de información entre organizaciones.

La plataforma permite a equipos de trabajo crear y gestionar proyectos desde cualquier lugar con acceso a internet, con control de avance en tiempo real, seguimiento de costos, análisis de cronogramas y generación de reportes ejecutivos.

### 1.2 Para quién está diseñado

Saicloud está dirigido a:

- **Directores y gerentes de proyectos** que necesitan visibilidad completa del estado de sus proyectos y equipo.
- **Coordinadores y líderes de área** que asignan tareas y hacen seguimiento diario del avance.
- **Profesionales técnicos** (ingenieros, consultores, desarrolladores) que registran su tiempo de trabajo y actualizan el progreso de las actividades.
- **Administradores financieros** que necesitan controlar presupuesto, costos ejecutados y valor ganado.
- **Directivos y clientes** que requieren reportes de avance y dashboards ejecutivos de solo lectura.

### 1.3 Beneficios principales

| Beneficio | Descripción |
|---|---|
| Visibilidad en tiempo real | El avance de tareas, horas registradas y costos se actualizan al instante |
| Jerarquía estructurada | Proyectos → Fases → Tareas permite organizar cualquier tipo de proyecto |
| Cronograma inteligente | Auto-Schedule calcula fechas óptimas respetando dependencias y restricciones |
| Control de costos | EVM (Earned Value Management) detecta desviaciones antes de que se vuelvan críticas |
| Registro de tiempo | Timer integrado y timesheets semanales para captura precisa de horas |
| Análisis visual | Gantt, Burn Down, Velocity, Resource Utilization y más gráficos en tiempo real |
| Multi-tenant seguro | Los datos de su empresa nunca se mezclan con los de otras organizaciones |
| Integración con Saiopen | Sincronización bidireccional con el ERP Saiopen para eliminar doble digitación |

### 1.4 Navegadores recomendados

Saicloud está optimizado para los siguientes navegadores en sus versiones más recientes:

| Navegador | Soporte |
|---|---|
| Google Chrome 120+ | Recomendado (soporte completo) |
| Microsoft Edge 120+ | Compatible (soporte completo) |
| Mozilla Firefox 121+ | Compatible |
| Safari 17+ (macOS/iOS) | Compatible |

> **Nota:** Internet Explorer no es compatible. Si usa una versión antigua de cualquier navegador, actualícelo antes de ingresar a la plataforma.

> **Tip:** Para la mejor experiencia, use Chrome o Edge en una resolución mínima de 1280 × 720 píxeles. El Gantt y los dashboards de analytics requieren al menos 1440 × 900 para visualizarse correctamente.

---

## 2. Primeros Pasos

### 2.1 Registro y activación de cuenta

El acceso a Saicloud es por invitación. El administrador de su empresa debe crear su cuenta desde el panel de administración. Una vez creada, usted recibirá un correo electrónico con:

1. El enlace de acceso a la plataforma: `http://[su-empresa].saicloud.com` (o la URL interna configurada).
2. Sus credenciales iniciales (correo y contraseña temporal).
3. Instrucciones para activar su cuenta.

**Pasos para activar la cuenta:**

1. Abra el correo de bienvenida y haga clic en el enlace **Activar cuenta**.
2. Será redirigido a la pantalla de cambio de contraseña.
3. Ingrese una contraseña nueva que cumpla los requisitos:
   - Mínimo 8 caracteres.
   - Al menos una letra mayúscula.
   - Al menos un número.
   - Al menos un carácter especial (!, @, #, $, etc.).
4. Confirme la contraseña y haga clic en **Guardar**.
5. La plataforma lo redirigirá automáticamente al dashboard principal.

> **Nota:** El enlace de activación tiene una vigencia de 72 horas. Si no lo usa en ese tiempo, contacte al administrador de su empresa para que le envíe un nuevo enlace.

### 2.2 Primer login

1. Ingrese a la URL de Saicloud de su organización.
2. En la pantalla de login, escriba su correo electrónico y contraseña.
3. Haga clic en **Ingresar**.
4. Si tiene habilitada la autenticación de dos factores (2FA), ingrese el código de su aplicación autenticadora.
5. Al ingresar por primera vez, el sistema le pedirá completar su perfil.

> **Tip:** Active la opción "Recordarme" solo en dispositivos personales y de confianza. En equipos compartidos, nunca marque esta opción.

### 2.3 Configuración inicial del perfil

Para configurar su perfil:

1. Haga clic en su nombre o avatar en la esquina superior derecha de la pantalla.
2. Seleccione **Mi perfil** en el menú desplegable.
3. Complete o actualice los siguientes campos:

| Campo | Descripción |
|---|---|
| Nombre completo | Su nombre y apellido como aparecerá en asignaciones y reportes |
| Correo electrónico | Solo lectura — modificable por el administrador |
| Teléfono | Opcional, para contacto interno |
| Cargo | Su rol en la organización |
| Zona horaria | Importante para el correcto funcionamiento del Timer y timesheets |
| Foto de perfil | Avatar visible en tareas y comentarios |

4. Haga clic en **Guardar cambios**.

### 2.4 Dark mode / Light mode

Saicloud ofrece un modo oscuro (dark mode) y un modo claro (light mode) para adaptarse a sus preferencias visuales o condiciones de iluminación.

**Para cambiar el tema:**

1. Haga clic en el ícono de sol/luna ubicado en la barra de navegación superior (extremo derecho, junto a las notificaciones).
2. El cambio se aplica de inmediato y se guarda en su perfil.
3. La preferencia se mantiene entre sesiones.

> **Tip:** El modo oscuro es recomendado para sesiones largas de trabajo nocturno y reduce la fatiga visual. El modo claro es mejor para presentaciones y reuniones con proyectores.

### 2.5 Navegación general

**Estructura de la interfaz:**

```
┌─────────────────────────────────────────────────────┐
│  [Logo Saicloud]  [Barra superior: notif, perfil]   │
├──────────┬──────────────────────────────────────────┤
│          │                                          │
│ SIDEBAR  │         ÁREA DE CONTENIDO                │
│          │                                          │
│ Dashboard│                                          │
│ Proyectos│                                          │
│ Tareas   │                                          │
│ Terceros │                                          │
│ Config   │                                          │
│          │                                          │
└──────────┴──────────────────────────────────────────┘
```

**Módulos disponibles en el sidebar (según su rol):**

El sidebar principal de Saicloud muestra iconos de módulo. Al ingresar al módulo de Proyectos, el sidebar lateral muestra las siguientes opciones:

| Módulo / Opción | Descripción |
|---|---|
| Dashboard | Resumen ejecutivo de todos sus proyectos activos y métricas globales |
| Proyectos | Lista de proyectos (vista lista o cards) |
| Tareas | Lista global de todas las tareas de todos los proyectos |
| Mis Tareas | Vista personal: solo las tareas asignadas al usuario actual |
| Registro de Horas | Vista semanal para registrar timesheets de la semana |
| Actividades | Catálogo compartido de actividades de la empresa |
| Configuración | Parámetros del módulo (solo administradores) |

**Sección Acceso Rápido (parte inferior del sidebar):**

| Opción | Descripción |
|---|---|
| Terceros | Gestión de clientes y proveedores |
| Usuarios | Gestión de usuarios de la empresa |
| Consecutivos | Configuración de numeración automática |

> **Nota:** Los módulos visibles dependen de su rol. Un usuario con rol `viewer` verá menos opciones que un `company_admin`.

**Atajos de teclado útiles:**

| Atajo | Acción |
|---|---|
| `Ctrl + /` | Abrir búsqueda global |
| `Esc` | Cerrar diálogos y paneles laterales |
| `Ctrl + S` | Guardar formulario activo |

---

## 3. Módulo Proyectos — Conceptos Fundamentales

### 3.1 Jerarquía: Empresa → Proyectos → Fases → Tareas

Saicloud organiza el trabajo en cuatro niveles jerárquicos:

```
EMPRESA (su organización en Saicloud)
  └── PROYECTO (ej: "Construcción Bodega Norte")
        ├── FASE 1: Planificación
        │     ├── TAREA 1.1: Levantamiento de requisitos
        │     ├── TAREA 1.2: Diseño arquitectónico
        │     └── TAREA 1.3: Aprobación de planos
        ├── FASE 2: Ejecución
        │     ├── TAREA 2.1: Cimentación
        │     │     ├── SUBTAREA 2.1.1: Excavación
        │     │     └── SUBTAREA 2.1.2: Fundición
        │     └── TAREA 2.2: Estructura metálica
        └── FASE 3: Cierre
              ├── TAREA 3.1: Entrega formal
              └── TAREA 3.2: Acta de liquidación
```

- **Proyecto:** la unidad principal de trabajo. Tiene presupuesto, fechas, cliente y responsables.
- **Fase:** agrupa tareas por etapa lógica del proyecto (ej: Diseño, Construcción, Entrega). Solo una fase puede estar activa a la vez.
- **Tarea:** la unidad mínima de trabajo asignable a una persona. Puede tener subtareas, dependencias, timesheets y actividades del catálogo.

### 3.2 Qué es una Actividad del catálogo

Una **Actividad** es una plantilla de trabajo reutilizable definida a nivel de empresa. Tiene un tipo, una unidad de medida y un costo unitario base.

**Ejemplos de actividades:**
- "Excavación manual" — tipo: Mano de obra — unidad: m³ — costo: $45.000/m³
- "Concreto 3000 PSI" — tipo: Material — unidad: m³ — costo: $320.000/m³
- "Reunión de seguimiento" — tipo: Mano de obra — unidad: horas — costo: $80.000/h
- "Entrega de informe" — tipo: Hito — sin costo unitario

Cuando una tarea se asocia a una actividad del catálogo, el sistema determina automáticamente cómo se mide el progreso de esa tarea (en horas, en cantidades, por porcentaje, o como hito).

### 3.3 Qué es una Dependencia

Una **Dependencia** define la relación de orden entre dos tareas: la **predecesora** y la **sucesora**. Hay cuatro tipos, cada uno con una lógica diferente de encadenamiento. Las dependencias son la base para el cálculo de la ruta crítica y el Auto-Schedule.

### 3.4 Roles y permisos en proyectos

| Rol | Puede hacer |
|---|---|
| `valmen_admin` | Todo en la plataforma (administrador del sistema) |
| `company_admin` | Todo dentro de su empresa: crear/editar proyectos, fases, tareas, usuarios, presupuestos |
| `seller` | Ver y gestionar proyectos de ventas; crear tareas; registrar tiempo |
| `collector` | Módulo de cobros; acceso limitado a proyectos |
| `viewer` | Solo lectura: ver proyectos, dashboards, reportes. No puede crear ni modificar nada |
| `valmen_support` | Solo lectura de datos del cliente (soporte técnico de ValMen Tech) |

> **Nota:** Los permisos específicos dentro de un proyecto pueden ser configurados adicionalmente por el `company_admin` de su organización.

### 3.5 Flujo general de trabajo recomendado

El flujo típico para un proyecto nuevo en Saicloud es:

1. Crear el tercero (cliente) si no existe.
2. Crear el proyecto con sus datos básicos y vincularlo al cliente.
3. Definir las fases del proyecto.
4. Crear las tareas dentro de cada fase.
5. Asignar actividades del catálogo a las tareas.
6. Establecer dependencias entre tareas relacionadas.
7. Asignar recursos (usuarios) a las tareas.
8. Ejecutar Auto-Schedule para calcular fechas óptimas.
9. Crear una baseline del plan inicial.
10. Iniciar ejecución: registrar tiempo, actualizar avance.
11. Monitorear con Analytics, Gantt y dashboard de presupuesto.
12. Ajustar el plan cuando sea necesario con escenarios What-If.

---

## 4. Gestión de Proyectos

### 4.1 Crear un proyecto

**Pasos para crear un proyecto:**

1. En el sidebar, haga clic en **Proyectos**.
2. En la lista de proyectos, haga clic en el botón **+ Nuevo proyecto** (esquina superior derecha).
3. Se abrirá el formulario de creación. Complete los campos:

**Campos del formulario:**

| Campo | Obligatorio | Descripción |
|---|---|---|
| Código | No (autogenerado) | Identificador único del proyecto (ej: PRY-001). Si se deja vacío, el sistema lo genera |
| Nombre | Sí | Nombre descriptivo del proyecto |
| Tipo de proyecto | Sí | Obra civil, Consultoría, Manufactura, Servicios, Licitación pública, Otro |
| Cliente (Tercero) | Sí | Empresa o persona para quien se ejecuta el proyecto |
| Gerente del proyecto | Sí | Usuario responsable principal del proyecto |
| Coordinador | No | Usuario de apoyo en la gestión |
| Fecha de inicio planificada | Sí | Fecha en que se planifica comenzar |
| Fecha de fin planificada | Sí | Fecha en que se planifica terminar |
| Fecha de inicio real | No | Se llena cuando el proyecto realmente comienza |
| Fecha de fin real | No | Se llena cuando el proyecto realmente termina |
| Presupuesto total | Sí | Monto total del contrato o presupuesto (en pesos colombianos) |
| % Administración (AIU) | No | Porcentaje de administración (default: 0) |
| % Imprevistos (AIU) | No | Porcentaje de imprevistos (default: 0) |
| % Utilidad (AIU) | No | Porcentaje de utilidad (default: 0) |

4. Haga clic en **Guardar**.
5. El sistema creará el proyecto y lo redirigirá al detalle del proyecto.

> **Tip:** El AIU (Administración, Imprevistos y Utilidad) es especialmente útil en proyectos de obra civil y licitaciones públicas en Colombia. Si no aplica para su proyecto, déjelo en 0%.

> **Nota:** Una vez creado el proyecto, su estado inicial es **Borrador**. Debe cambiarlo a **Planificado** o **En ejecución** cuando corresponda.

**Estados del proyecto:**

| Estado | Código | Descripción |
|---|---|---|
| Borrador | `draft` | Proyecto en construcción, no ha iniciado |
| Planificado | `planned` | Proyecto aprobado, listo para iniciar |
| En ejecución | `in_progress` | Proyecto activo, se está ejecutando |
| Suspendido | `suspended` | Proyecto pausado temporalmente |
| Cerrado | `closed` | Proyecto finalizado exitosamente |
| Cancelado | `cancelled` | Proyecto cancelado, no se completará |

### 4.2 Lista de proyectos (vista lista y cards)

Al ingresar al módulo Proyectos, verá la lista de todos los proyectos de su empresa en **Vista Lista** (predeterminada). Puede alternar entre vistas usando el botón de cambio en la esquina superior derecha.

**Vista Lista (predeterminada):**
- Tabla con columnas: Código, Nombre, Tipo, Estado, Cliente, Gerente, Fecha fin, Presupuesto.
- Útil para comparar múltiples proyectos al mismo tiempo.
- Soporta ordenamiento por columna (haga clic en el encabezado de la columna).
- Cada fila tiene botones de acción: Ver detalle (flecha) y Eliminar (papelera).

**Vista Cards:**
- Haga clic en el botón **Cards** (esquina superior derecha) para cambiar a esta vista.
- Cada proyecto se muestra como una tarjeta con: código, estado, nombre, tipo, avance, gerente, cliente, fecha fin y presupuesto.
- Haga clic en **Lista** para volver a la vista tabla.

**Filtros disponibles:**
- Búsqueda por código, nombre o cliente.
- Por estado del proyecto.
- Por tipo de proyecto.
- Por gerente.

### 4.3 Detalle del proyecto (tabs disponibles)

Al hacer clic en un proyecto (botón de flecha en vista lista, o botón "Ver detalle" en vista cards), accede a su vista de detalle. Esta vista tiene las siguientes pestañas (tabs) en orden:

| Tab | Contenido |
|---|---|
| General | Información general: código, tipo, cliente (con NIT), fechas planificadas y reales, equipo (gerente y coordinador), presupuesto y AIU |
| Fases | Lista de fases del proyecto con presupuesto, estado y avance |
| Terceros | Terceros (clientes/proveedores) vinculados a este proyecto |
| Documentos | Archivos adjuntos del proyecto |
| Hitos | Listado de tareas marcadas como hitos |
| Tareas | Lista completa de tareas. Incluye botón **Kanban** para alternar a vista tablero |
| Actividades | Actividades del catálogo asignadas a este proyecto con cantidades planificadas |
| Gantt | Diagrama de Gantt con overlays de ruta crítica, holgura y baseline |
| Equipo | Miembros del equipo con sus tareas asignadas, capacidades y ausencias |
| Timesheets | Registro de horas del equipo en este proyecto |
| Analytics | Dashboard de métricas y gráficos |
| Baselines | Gestión de líneas base del plan |
| Escenarios | Escenarios What-If para simulación de cambios |
| Presupuesto | Seguimiento de costos, EVM, tarifas por recurso y gastos |

> **Nota:** Los tabs disponibles dependen de su rol y de los módulos activos en su empresa.

**Botones de acción en el encabezado del proyecto:**

Dependiendo del estado del proyecto, verá diferentes botones de acción:
- **Iniciar ejecución:** cambia el proyecto de Planificado a En ejecución.
- **Volver a borrador:** regresa el proyecto al estado Borrador.
- **Scheduling:** abre un menú con la opción Auto-Schedule para calcular fechas automáticamente.
- **Editar:** abre el formulario de edición del proyecto.

### 4.4 Editar y eliminar proyectos

**Editar un proyecto:**

1. Ingrese al detalle del proyecto.
2. Haga clic en el botón **Editar** (ícono de lápiz) en el encabezado del proyecto.
3. Se abrirá el formulario con los datos actuales.
4. Modifique los campos necesarios y haga clic en **Guardar**.

**Eliminar un proyecto:**

> **Advertencia:** Eliminar un proyecto es una acción irreversible. Se eliminan también todas sus fases, tareas, timesheets, asignaciones, gastos y baselines. No se puede deshacer.

1. Desde la lista de proyectos (vista lista), haga clic en el ícono de eliminar (papelera) al final de la fila del proyecto.
2. Confirme en el diálogo de confirmación que aparece.

> **Tip:** Si no quiere eliminar un proyecto sino solo ocultarlo, cambie su estado a **Cancelado** o **Cerrado**. Así queda el historial y se puede consultar en el futuro.

---

## 5. Gestión de Fases

### 5.1 Qué es una fase y para qué sirve

Una **Fase** es una división lógica del proyecto que agrupa tareas relacionadas por etapa temporal o temática. Las fases permiten:

- Organizar el trabajo en bloques manejables.
- Controlar qué etapa está activa en un momento dado.
- Calcular el progreso parcial del proyecto por etapa.
- Aplicar el Auto-Schedule a nivel de fase.

**Ejemplos de estructuras de fases:**

| Tipo de proyecto | Fases típicas |
|---|---|
| Construcción | Diseño → Adquisiciones → Cimentación → Estructura → Acabados → Entrega |
| Consultoría | Diagnóstico → Análisis → Propuesta → Implementación → Cierre |
| Software | Sprint 1 → Sprint 2 → Sprint 3 → UAT → Go Live |
| Licitación pública | Planeación → Precalificación → Propuesta → Ejecución → Liquidación |

### 5.2 Crear, editar y reordenar fases

**Crear una fase:**

1. Ingrese al detalle del proyecto.
2. Haga clic en el tab **Fases**.
3. Haga clic en **+ Nueva fase**.
4. Complete los campos:
   - **Nombre:** nombre de la fase (obligatorio).
   - **Descripción:** descripción opcional.
   - **Orden:** número de posición de la fase en la secuencia.
   - **Fecha de inicio planificada** y **Fecha de fin planificada** (opcionales, pueden derivarse del Auto-Schedule).
5. Haga clic en **Guardar**.

**Editar una fase:**

1. En la lista de fases, haga clic en el ícono de lápiz (editar) a la derecha de la fase.
2. Modifique los campos y guarde.

**Reordenar fases:**

1. En la lista de fases, use los íconos de flecha arriba/abajo para cambiar el orden.
2. El orden determina la secuencia lógica del proyecto en el Gantt.

> **Tip:** Defina todas las fases al inicio del proyecto, aunque las tareas se agreguen gradualmente. Esto facilita la planificación y el Auto-Schedule.

### 5.3 Activar una fase

Solo una fase puede estar **activa** a la vez. La fase activa indica la etapa en la que se encuentra el proyecto actualmente.

**Para activar una fase:**

1. En la lista de fases, haga clic en el ícono de activación (bandera o check) de la fase que desea activar.
2. El sistema desactivará automáticamente la fase anterior y activará la nueva.
3. La fase activa se muestra con un indicador visual diferenciado (generalmente un chip de color verde).

> **Nota:** Activar una fase no cambia el estado de las tareas. Solo indica que esa es la etapa en curso del proyecto.

### 5.4 Estados de fase

| Estado | Descripción |
|---|---|
| Pendiente | La fase aún no ha comenzado |
| Activa | La fase está en ejecución actualmente |
| Completada | Todas las tareas de la fase están terminadas |
| Cancelada | La fase fue cancelada |

### 5.5 Progreso automático

El porcentaje de avance de una fase se calcula automáticamente como el promedio ponderado del avance de todas sus tareas. No es necesario actualizar manualmente el progreso de la fase; se recalcula cada vez que se modifica el estado o progreso de alguna tarea.

El porcentaje de avance del **proyecto** se calcula como el promedio del avance de todas sus fases.

---

## 6. Gestión de Tareas

### 6.1 Crear una tarea

**Pasos para crear una tarea:**

1. Ingrese al detalle del proyecto.
2. Haga clic en el tab **Tareas**.
3. Haga clic en **+ Nueva tarea**.
4. Complete el formulario:

**Campos del formulario de tarea:**

| Campo | Obligatorio | Descripción |
|---|---|---|
| Nombre | Sí | Descripción corta de la tarea |
| Descripción | No | Detalle adicional de la tarea |
| Fecha de inicio | No | Fecha en que debe comenzar la tarea |
| Fecha de fin | No | Fecha en que debe terminar la tarea |
| Fecha límite | No | Fecha tope para entrega (puede diferir de fecha de fin) |
| Tarea recurrente | No | Marcar si la tarea se repite periódicamente |
| Proyecto | Sí | Proyecto al que pertenece la tarea |
| Fase | Sí | Fase dentro del proyecto a la que pertenece |
| Actividad del catálogo | No | Actividad que determina el modo de medición |
| Tarea padre | No | Si es subtarea, seleccione la tarea padre |
| Cliente (opcional) | No | Tercero relacionado con la tarea |
| Responsable | No | Usuario asignado a la tarea |
| Prioridad | No | Baja, Normal, Alta, Urgente |

> **Nota:** Las horas estimadas y la cantidad objetivo se configuran en el detalle de la tarea una vez creada, dependiendo del tipo de actividad asociada.

5. Haga clic en **Crear tarea**.

### 6.2 Modos de UI según tipo de actividad

El comportamiento visual y funcional de una tarea cambia dependiendo del tipo de actividad asignada:

#### Modo: Sin actividad (solo_estados)

Cuando la tarea no tiene actividad del catálogo asignada:
- Se muestra un selector de estado: Todo → En progreso → En revisión → Bloqueada → Completada → Cancelada.
- No hay cronómetro ni campos de horas.
- El progreso se actualiza manualmente cambiando el estado.

#### Modo: Actividad en horas (timesheet)

Cuando la actividad tiene unidad de medida en horas (ej: "Reunión de coordinación"):
- Se muestra el **cronómetro (Timer)** para iniciar/pausar/detener el conteo de tiempo.
- Se muestra el panel de **Timesheets** para registrar horas manualmente.
- Se muestran las horas estimadas vs horas registradas.
- El progreso se calcula como: `(horas registradas / horas estimadas) × 100`.

#### Modo: Actividad en unidades (cantidad)

Cuando la actividad tiene unidad de medida física (m³, ton, kg, días, unidades, etc.):
- Se muestra un campo de **edición inline de cantidad**.
- Se pueden ingresar directamente los metros cúbicos instalados, toneladas colocadas, etc.
- El progreso se calcula como: `(cantidad registrada / cantidad objetivo) × 100`.

#### Modo: Hito (hito)

Cuando la actividad es de tipo hito (milestone):
- Se muestra un **checkbox de completado**.
- El progreso es binario: 0% o 100%.
- En el Gantt, los hitos se muestran como un diamante (♦).

> **Tip:** Elija bien la actividad del catálogo desde el inicio, porque cambiar el modo de medición después de que la tarea tiene timesheets registrados puede generar inconsistencias.

### 6.3 Vista lista y Kanban

En el tab **Tareas** del proyecto, hay dos formas de visualizar las tareas:

**Vista Lista (predeterminada):**
- Tabla con columnas: Código, Nombre, Responsable, Estado, Prioridad, Avance, Fecha límite.
- Se puede filtrar por: Estado, Prioridad, Fase.
- Se puede buscar por código o nombre.
- Cada fila tiene botones: Ver detalle (flecha), Editar (lápiz), Eliminar (papelera).

**Vista Kanban:**
- Haga clic en el botón **Kanban** (ícono de tablero) para alternar a esta vista.
- Columnas por estado: **Por hacer | En progreso | En revisión | Bloqueada | Completada**.
- Cada tarjeta muestra: código, nombre, responsable, tipo de progreso, porcentaje de avance.
- Filtros disponibles: Proyecto, Fase, Responsable, Prioridad.
- Haga clic en **Lista** para volver a la vista tabla.

> **Tip:** El Kanban es ideal para proyectos de software con flujo ágil. La vista lista es mejor para proyectos de construcción donde el control de fechas es crítico.

La misma vista Kanban está disponible desde **Mis Tareas** en el sidebar, mostrando solo las tareas asignadas al usuario actual.

### 6.4 Subtareas

Una subtarea es una tarea que pertenece a otra tarea padre. Las subtareas:
- Heredan la fase de la tarea padre.
- Se pueden asignar a usuarios diferentes a la tarea padre.
- Contribuyen al cálculo de avance de la tarea padre.
- Aparecen indentadas en la vista lista.

**Para crear una subtarea:**

1. En la vista lista de tareas, haga clic en la tarea que será el padre.
2. En el panel de detalle de la tarea, busque la sección **Subtareas**.
3. Haga clic en **+ Agregar subtarea**.
4. Complete el formulario igual que una tarea normal.
5. Guarde.

**Alternativamente:**
1. Al crear una nueva tarea, seleccione la **tarea padre** en el campo correspondiente del formulario.

### 6.5 Editar y eliminar tareas

**Editar una tarea:**

1. En la vista lista, haga clic en el ícono de lápiz (editar) de la fila de la tarea.
2. Se abrirá el formulario de edición con los datos actuales.
3. Modifique los campos y guarde.

**Cambio rápido de estado (en el detalle de la tarea):**
- Abra el detalle de la tarea haciendo clic en el botón de flecha (chevron_right).
- En la sección "Estado actual", haga clic en el estado deseado para cambiarlo directamente.

**Eliminar una tarea:**

> **Advertencia:** Eliminar una tarea elimina también todos sus timesheets, asignaciones de recursos y dependencias. Esta acción no se puede deshacer.

1. En la vista lista, haga clic en el ícono de eliminar (papelera) de la fila de la tarea.
2. Confirme en el diálogo.

**Detalle de tarea:**

Al hacer clic en el ícono de flecha (ver detalle), se abre la vista completa de la tarea con las siguientes secciones:
- **Progreso:** porcentaje de avance y tipo de medición.
- **Estado actual:** selector de estado inline.
- **Descripción:** texto descriptivo de la tarea.
- **Subtareas:** lista de subtareas hijas.
- **Seguidores:** usuarios que reciben notificaciones.
- **Tiempo:** cronómetro (Timer) para registrar horas en tiempo real.
- **Dependencias:** dependencias con otras tareas.
- **Restricciones:** restricciones de programación (SNET, MSO, etc.).
- **Recursos:** asignaciones de recursos a esta tarea.
- **Comentarios:** hilo de comentarios del equipo.

La barra lateral derecha muestra metadata: proyecto, fase, actividad, responsable, prioridad, fechas y holgura (Float) en días.

---

## 7. Catálogo de Actividades

### 7.1 Qué es el catálogo compartido

El **Catálogo de Actividades** es una biblioteca centralizada de tipos de trabajo estándar de su empresa. En lugar de definir cada tipo de trabajo cada vez que crea una tarea, lo define una vez en el catálogo y lo reutiliza en todos los proyectos.

El catálogo es **compartido a nivel de empresa**: todas las actividades creadas por cualquier usuario están disponibles para todos los proyectos de la organización.

### 7.2 Tipos de actividades

| Tipo | Código | Descripción | Ejemplo |
|---|---|---|---|
| Mano de obra | `labor` | Trabajo humano medido en horas | Instalación eléctrica, programación, consultoría |
| Material | `material` | Insumos físicos medidos en unidades | Concreto (m³), cable (ml), tuberías (un) |
| Equipo | `equipment` | Uso de maquinaria o herramientas | Alquiler de retroexcavadora (días), uso de servidor (horas) |
| Subcontrato | `subcontract` | Trabajo ejecutado por terceros | Pintura por empresa externa, transporte |

Cada tipo tiene su propia lógica de unidad de medida:
- `labor` → horas (activa cronómetro y timesheets)
- `material` y `equipment` → unidades físicas (m³, ml, un, kg, ton, días)
- `subcontract` → puede ser horas o unidades según el acuerdo

### 7.3 Crear y gestionar actividades

**Para acceder al catálogo:**

1. En el sidebar, haga clic en **Catálogo** (o desde el tab **Actividades** dentro de un proyecto).
2. Se muestra la lista de todas las actividades con columnas: código, nombre, tipo, unidad de medida, costo unitario base, estado.

**Para crear una actividad:**

1. Haga clic en **+ Nueva actividad**.
2. Complete el formulario:

| Campo | Obligatorio | Descripción |
|---|---|---|
| Código | No (autogenerado) | Identificador único de la actividad (ej: ACT-001) |
| Nombre | Sí | Nombre descriptivo (ej: "Excavación manual") |
| Descripción | No | Detalle adicional |
| Tipo | Sí | Mano de obra, Material, Equipo, Subcontrato |
| Unidad de medida | Sí | m³, ml, un, kg, ton, horas, días, etc. |
| Costo unitario base | Sí | Precio por unidad de medida en la moneda de la empresa |

3. Haga clic en **Guardar**.

**Para desactivar una actividad:**
1. En la lista, haga clic en el toggle de estado de la actividad.
2. Las actividades inactivas no aparecen en los selectores al crear tareas, pero mantienen su historial en las tareas existentes.

### 7.4 Reutilización entre proyectos

Una vez que una actividad está en el catálogo, está disponible para **todos los proyectos** de la empresa. Al crear una tarea en cualquier proyecto, puede buscar y seleccionar cualquier actividad activa del catálogo.

Las actividades también se pueden **asignar al nivel de proyecto** (tab Actividades) para definir cantidades planificadas y costos específicos por proyecto, lo que alimenta el estado financiero y los reportes de avance.

> **Tip:** Estandarice los nombres del catálogo siguiendo una convención clara. Por ejemplo: "[Tipo] [Recurso] [Acción]" → "Mano de obra Maestro Excavación". Esto facilita los reportes comparativos entre proyectos.

---

## 8. Dependencias entre Tareas

### 8.1 Tipos de dependencias

Saicloud soporta tres tipos de dependencias (en la interfaz; el modelo técnico incluye también SF):

#### FS — Fin a Inicio (Finish to Start)

La tarea sucesora **no puede empezar** hasta que la predecesora haya **terminado**.

```
Tarea A: [====Diseño====]
                        Tarea B:    [====Construcción====]
```

**Ejemplo práctico:** Los planos de construcción deben estar aprobados (Fin de Tarea A) antes de que comience la excavación (Inicio de Tarea B).

Este es el tipo más común. Representa el ~80% de las dependencias en proyectos típicos.

#### SS — Inicio a Inicio (Start to Start)

La tarea sucesora **no puede empezar** hasta que la predecesora haya **empezado**.

```
Tarea A: [====Instalación tubería====]
Tarea B:    [====Pruebas de presión====]
```

**Ejemplo práctico:** Las pruebas de presión solo pueden comenzar una vez que la instalación de tubería ha empezado (no es necesario que termine, pero sí que comience).

#### FF — Fin a Fin (Finish to Finish)

La tarea sucesora **no puede terminar** hasta que la predecesora haya **terminado**.

```
Tarea A: [====Redacción informe====]
Tarea B:         [====Revisión y corrección====]
```

**Ejemplo práctico:** La revisión y corrección del informe (B) no puede terminar hasta que la redacción completa (A) también haya terminado, porque no se puede corregir lo que aún no está escrito.

#### SF — Inicio a Fin (Start to Finish)

La tarea sucesora **no puede terminar** hasta que la predecesora haya **empezado**. Es el tipo menos común.

**Ejemplo práctico (industria):** El turno nocturno (B) no puede terminar hasta que el turno diurno (A) haya comenzado.

### 8.2 Cómo crear una dependencia

**Método 1: Desde el detalle de la tarea**

1. Abra la tarea que será la **sucesora** (la que depende de otra).
2. En el panel de detalle, busque la sección **Dependencias**.
3. Haga clic en **+ Agregar predecesora**.
4. En el diálogo, busque y seleccione la **tarea predecesora**.
5. Seleccione el **tipo de dependencia**: FS, SS o FF.
6. (Opcional) Ingrese el **Lag time** en días (retraso adicional entre las tareas).
7. Haga clic en **Guardar**.

**Método 2: Desde el componente selector de dependencias**

1. En el tab **Tareas** del proyecto, haga clic en el ícono de dependencias (cadena) de la tarea.
2. Use el selector visual para agregar dependencias.

> **Nota:** Saicloud detecta automáticamente dependencias circulares (ciclos). Si intenta crear una dependencia que generaría un ciclo (ej: A depende de B, B depende de C, C depende de A), el sistema mostrará un error y no permitirá guardar la dependencia.

### 8.3 Ver dependencias en tabla y en Gantt

**En la vista lista de tareas:**
- La columna "Predecesoras" muestra los códigos de las tareas predecesoras con su tipo de dependencia. Ejemplo: `T-003(FS)`, `T-005(SS+2d)`.

**En el Gantt:**
- Las dependencias se muestran como flechas entre las barras de las tareas.
- FS: flecha del extremo derecho de la predecesora al extremo izquierdo de la sucesora.
- SS: flecha del extremo izquierdo de la predecesora al extremo izquierdo de la sucesora.
- FF: flecha del extremo derecho de la predecesora al extremo derecho de la sucesora.

### 8.4 Lag time (retraso entre dependencias)

El **Lag time** es un número de días de espera adicional entre el evento de la predecesora y el evento de la sucesora.

**Ejemplos:**
- `FS + 2 días`: la tarea sucesora comienza 2 días **después** de que termina la predecesora. Útil para tiempos de curado de concreto, tiempos de secado, etc.
- `FS - 1 día` (lag negativo): la tarea sucesora puede comenzar 1 día **antes** de que termine la predecesora (solapamiento parcial).

> **Tip:** Use el lag positivo para representar tiempos de espera naturales del proceso (curado, secado, aprobaciones formales). Use el lag negativo con precaución: significa que las dos tareas se solapan y eso puede complicar la ruta crítica.

---

## 9. Gantt

### 9.1 Cómo acceder al Gantt

1. Ingrese al detalle del proyecto.
2. Haga clic en el tab **Gantt**.
3. El diagrama cargará automáticamente con las tareas del proyecto que tienen fechas definidas.

> **Nota:** Solo las tareas con **fecha de inicio** y **fecha de fin** aparecen en el Gantt. Las tareas sin fechas se excluyen del diagrama y se muestran en una lista separada como "Tareas sin fechas".

### 9.2 Navegación

**Zoom (niveles de escala de tiempo):**
- Use los botones **Día**, **Semana**, **Mes** en la barra de herramientas del Gantt para cambiar el nivel de detalle.
- **Día:** máximo detalle, ideal para proyectos cortos.
- **Semana:** nivel recomendado para proyectos de 1-6 meses.
- **Mes:** vista panorámica, ideal para proyectos largos (más de 6 meses).

**Scroll:**
- Desplazamiento horizontal: arrastrar la barra de scroll inferior.
- Desplazamiento vertical: rueda del mouse en la lista de tareas de la izquierda.

**Exportar:**
- Haga clic en el botón **Exportar SVG** para descargar el Gantt como imagen vectorial.

**Navegar al proyecto actual:**
- Haga clic en el botón **Hoy** en la barra de herramientas para centrar la vista en la fecha actual.

**Barra de tareas:**
- La barra de cada tarea representa la duración planificada.
- El porcentaje de completado se muestra como relleno oscuro dentro de la barra.
- Al pasar el cursor sobre una barra, aparece un tooltip con: nombre, fechas, responsable y avance.

### 9.3 Overlays disponibles

Los overlays son capas de información adicional que se activan mediante botones en la barra de herramientas del Gantt.

**Para activar un overlay:**
1. En la barra de herramientas del Gantt, haga clic en el botón del overlay deseado.
2. Puede activar varios overlays simultáneamente.
3. Los botones disponibles son: **Ruta crítica**, **Holgura**, **Baseline**.

#### Overlay: Ruta Crítica

Cuando está activo:
- Las tareas que pertenecen a la **ruta crítica** se muestran con la barra en **color rojo**.
- Las tareas que no son críticas mantienen su color original (verde, azul o gris).
- Un retraso en cualquier tarea roja retrasa directamente la fecha de fin del proyecto.

**Cómo interpretar:**
- Identifique las tareas en rojo y asegúrese de que tengan recursos asignados y sin impedimentos.
- Si hay muchas tareas en rojo, el cronograma tiene poco margen de error (Float bajo).

#### Overlay: Holgura / Float

Cuando está activo:
- Se muestra un número (en días) junto a cada tarea indicando cuántos días puede retrasarse sin afectar la fecha de fin del proyecto.
- Tareas con Float = 0 son críticas.
- Tareas con Float alto tienen más margen de maniobra.

**Cómo interpretar:**

| Float | Interpretación | Acción recomendada |
|---|---|---|
| 0 días | Tarea crítica — sin margen | Priorizar y monitorear de cerca |
| 1-3 días | Margen muy pequeño | Vigilar; cualquier retraso puede volverse crítico |
| 4-10 días | Margen moderado | Monitoreo normal |
| > 10 días | Margen amplio | Puede reprogramar si es necesario |

#### Overlay: Baseline

Cuando está activo:
- Se muestra una barra delgada de color gris/azul oscuro debajo de la barra actual de cada tarea.
- La barra delgada representa las fechas planificadas en la **baseline** (plan de referencia).
- Si la barra actual está a la derecha de la baseline, la tarea va retrasada.
- Si están alineadas, la tarea está en tiempo.

**Cómo interpretar:**
- Comparar la barra actual (colorida) con la barra de baseline (gris) le permite ver de un vistazo qué tareas están adelantadas, a tiempo o retrasadas respecto al plan original.

### 9.4 Limitaciones conocidas

- El Gantt no es interactivo (no se puede arrastrar barras directamente). Para cambiar fechas, edite la tarea.
- Si el proyecto tiene más de 500 tareas, el Gantt puede tardar más en cargar.
- Las tareas sin fechas no aparecen. Asegúrese de ejecutar el Auto-Schedule para poblar fechas.
- En pantallas menores a 1280px de ancho, el Gantt muestra una versión simplificada.

---

## 10. Timesheets y Timer

### 10.1 Qué es un timesheet

Un **Timesheet** es un registro de tiempo trabajado en una tarea específica. Contiene:
- La tarea a la que se imputa el tiempo.
- El número de horas trabajadas.
- La fecha en que se realizó el trabajo.
- Una descripción de lo que se hizo (opcional pero recomendado).
- El usuario que realizó el trabajo.

Los timesheets son la base para:
- Calcular el avance real de tareas tipo "horas".
- Calcular los costos de labor en el módulo de Budget & Cost.
- Alimentar las métricas de Earned Value (EV, AC).
- Generar reportes de horas por proyecto, fase, tarea y recurso.

### 10.2 Registrar tiempo manual

**Para registrar tiempo manualmente en una tarea:**

1. Abra el detalle de la tarea.
2. Haga clic en el tab **Timesheets** dentro del detalle de la tarea.
3. Haga clic en **+ Registrar horas**.
4. Complete el formulario:
   - **Fecha:** fecha en que se realizó el trabajo.
   - **Horas:** número de horas trabajadas (acepta decimales: 1.5 = 1 hora y 30 minutos).
   - **Descripción:** qué se hizo en esas horas (opcional pero recomendado).
5. Haga clic en **Guardar**.

**Vista de registro semanal de horas:**

También puede consultar y visualizar sus horas registradas desde la vista semanal:

1. En el sidebar del módulo Proyectos, haga clic en **Registro de Horas**.
2. La vista muestra las entradas de timesheet de la semana actual con navegación de fechas (flechas para semana anterior/siguiente).
3. Use el botón **Hoy** para volver a la semana actual.
4. Los registros de horas se ingresan directamente en el detalle de cada tarea (sección Tiempo / Timer).

> **Tip:** Registre las horas diariamente usando el Timer directamente desde el detalle de la tarea para mayor precisión. La vista de Registro de Horas sirve como resumen de lo ya registrado.

### 10.3 Usar el cronómetro en tiempo real

El **Timer** (cronómetro) permite registrar tiempo mientras trabaja, en tiempo real.

**Para iniciar el Timer:**

1. Abra el detalle de una tarea con modo de medición "horas".
2. Haga clic en el botón de **Play** (▶) en el panel del Timer.
3. El cronómetro comenzará a contar: `0:00:01... 0:00:02...`
4. El ícono del Timer en la barra superior también se activará, indicando que hay un cronómetro corriendo.

**Para pausar el Timer:**

1. Haga clic en el botón de **Pausa** (⏸) en el panel del Timer.
2. El contador se detiene. Puede reanudarlo más tarde.

**Para detener el Timer:**

1. Haga clic en el botón de **Stop** (⏹).
2. El sistema calculará el total de horas transcurridas.
3. Se abrirá un diálogo de confirmación para guardar el timesheet:
   - Confirme la fecha (predeterminado: hoy).
   - Confirme las horas calculadas (puede ajustarlas).
   - Agregue una descripción.
4. Haga clic en **Guardar**. El tiempo queda registrado como un timesheet.

> **Advertencia:** Si cierra la ventana del navegador sin detener el Timer, el tiempo contado hasta ese momento puede perderse. Siempre detenga el Timer antes de cerrar la sesión.

> **Tip:** Solo puede tener un Timer activo a la vez por sesión. Si intenta iniciar otro Timer en una tarea diferente, el sistema le preguntará si desea detener el actual.

### 10.4 Editar y eliminar registros

**Editar un timesheet:**

1. En la lista de timesheets de la tarea, haga clic en el ícono de lápiz del registro.
2. Modifique las horas, fecha o descripción.
3. Guarde.

> **Nota:** Solo puede editar sus propios timesheets. Los administradores pueden editar los de cualquier usuario.

**Eliminar un timesheet:**

> **Advertencia:** Eliminar un timesheet reduce las horas registradas en la tarea y puede cambiar el porcentaje de avance calculado.

1. En la lista de timesheets, haga clic en el ícono de eliminar (basura) del registro.
2. Confirme en el diálogo.

### 10.5 Ver historial de timesheets por tarea

1. Abra el detalle de la tarea.
2. Haga clic en el tab **Timesheets**.
3. Se muestra la tabla completa de todos los registros: fecha, horas, descripción, usuario.
4. Al pie de la tabla, verá el **total de horas registradas** vs las horas estimadas.

---

## 11. Gestión del Equipo (Tab Equipo)

El tab **Equipo** del proyecto agrupa toda la gestión de recursos: asignación a tareas, capacidades y ausencias. Este tab se llama "Equipo" en la interfaz (no "Recursos").

### 11.1 Asignación de recursos a tareas

Una **Asignación de recurso** vincula un usuario (persona) a una tarea, con un porcentaje de dedicación y un rango de fechas.

**Para asignar un recurso a una tarea:**

1. Abra el detalle de la tarea (botón de flecha en la lista de tareas).
2. En la sección **Recursos**, haga clic en **+ Asignar recurso**.
3. Complete el formulario de asignación:

| Campo | Descripción |
|---|---|
| Usuario | El miembro del equipo a asignar |
| Porcentaje de asignación | Qué fracción de su tiempo dedica a esta tarea (ej: 50% = medio tiempo) |
| Fecha de inicio | Desde cuándo trabaja en esta tarea |
| Fecha de fin | Hasta cuándo trabaja en esta tarea |
| Notas | Instrucciones o aclaraciones opcionales |

4. Haga clic en **Guardar**.

> **Nota:** El porcentaje de asignación es diferente al porcentaje de avance. El 50% de asignación significa que la persona dedica la mitad de su jornada laboral a esa tarea, no que la tarea está al 50% de completada.

**Detección de sobreasignación:**

Si el porcentaje total de asignaciones de un usuario en un período supera el 100%, el sistema muestra una **alerta de sobreasignación**:
- En la vista de workload, el período aparece resaltado en rojo o amarillo.
- En el panel de asignación, aparece un aviso preventivo.

### 11.2 Capacidad de recursos

La **capacidad** define cuántas horas semanales tiene disponibles un usuario para trabajar en proyectos.

**Para definir la capacidad de un recurso:**

1. Ingrese al tab **Equipo** del proyecto.
2. En la sección **Capacidades del equipo**, haga clic en **+ Agregar capacidad**.
3. Complete el formulario:
5. Complete:
   - **Horas por semana:** número de horas laborables (ej: 40 para tiempo completo, 20 para medio tiempo).
   - **Fecha de inicio:** desde cuándo aplica esta capacidad.
   - **Fecha de fin:** hasta cuándo aplica (deje vacío si es indefinido).
6. Guarde.

> **Tip:** Si un usuario tiene vacaciones, no reduzca su capacidad. En su lugar, registre la ausencia en el módulo de Disponibilidad. Así el sistema puede calcular correctamente la disponibilidad real en cada período.

### 11.3 Disponibilidad y calendarios

Las **ausencias** registran períodos en que un usuario no está disponible para trabajar.

**Para registrar una ausencia:**

1. Ingrese al tab **Equipo** del proyecto.
2. En la sección **Ausencias y disponibilidad**, haga clic en **+ Registrar ausencia**.
3. Complete el formulario:

| Campo | Descripción |
|---|---|
| Usuario | El recurso que estará ausente |
| Tipo | Vacaciones, Incapacidad, Festivo, Capacitación, Otro |
| Fecha de inicio | Primer día de la ausencia |
| Fecha de fin | Último día de la ausencia |
| Descripción | Motivo o detalle adicional |

4. Guarde.

**Flujo de aprobación:**
- Las ausencias inician en estado **pendiente de aprobación**.
- El `company_admin` recibe una notificación para aprobar o rechazar.
- Solo las ausencias **aprobadas** se descuentan del calendario de disponibilidad.

> **Nota:** Los festivos nacionales de Colombia (Ley de Festivos) no se carguen automáticamente. Deben registrarse manualmente o por lote por el administrador.

### 11.4 Workload y calendario de equipo

#### Vista de equipo y sus tareas

En el tab **Equipo**, la sección superior muestra:
- Listado de miembros del equipo con su porcentaje de utilización.
- Para cada miembro, la lista de tareas asignadas en el proyecto con su avance.

Esta vista permite identificar rápidamente qué tareas tiene cada persona y si hay desequilibrio en la carga.

> **Nota:** La vista detallada de Workload (carga por semana con colores) y el calendario por usuario son funcionalidades planificadas para versiones futuras.

---

## 12. Reporting & Analytics

### 12.1 Cómo acceder al dashboard de analytics

1. Ingrese al detalle del proyecto.
2. Haga clic en el tab **Analytics**.
3. El dashboard carga automáticamente las métricas del proyecto.

También puede acceder a analytics multiproyecto desde el **Dashboard principal** en el sidebar.

### 12.2 KPIs principales

Los KPIs (indicadores clave de desempeño) se muestran en cuatro tarjetas en la parte superior del dashboard de Analytics:

| KPI | Descripción |
|---|---|
| Completud | Porcentaje de avance del proyecto (tareas completadas sobre total). Muestra el conteo "X / Y tareas". |
| On-Time | Porcentaje de tareas completadas a tiempo. Muestra el número de tareas vencidas. |
| Velocidad | Tareas completadas por semana (ritmo del equipo). |
| Horas Burn Rate | Horas registradas por semana y varianza respecto al ritmo planificado. |

El dashboard también incluye dos botones de acción:
- **Actualizar (refresh):** recalcula los KPIs con los datos más recientes.
- **Descargar (download):** descarga los datos del analytics.

### 12.3 Gráficos disponibles

#### Burn Down Chart

**Qué muestra:** La reducción del trabajo pendiente a lo largo del tiempo.

- **Eje X (horizontal):** Línea de tiempo del proyecto (fechas).
- **Eje Y (vertical):** Trabajo pendiente (en tareas o horas).
- **Línea ideal (gris punteada):** Cómo debería disminuir el trabajo si se avanza uniformemente.
- **Línea real (azul):** Cómo está disminuyendo realmente el trabajo.

**Cómo leer:**
- Si la línea real está **por debajo** de la ideal: el equipo está avanzando más rápido de lo planificado (buena señal).
- Si la línea real está **por encima** de la ideal: hay retraso acumulado.
- Si la línea real es **plana** durante varios días: el equipo no está avanzando (tareas bloqueadas o no actualizadas).

#### Velocity Chart

**Qué muestra:** La cantidad de trabajo completado por período (semana o sprint).

- **Eje X:** Semanas o períodos del proyecto.
- **Eje Y:** Número de tareas completadas (o puntos de historia, si aplica).
- **Barras:** Una por período, altura = trabajo completado.
- **Línea promedio (roja):** Velocidad promedio del equipo.

**Cómo leer:**
- Velocidad alta y constante = equipo productivo y predecible.
- Velocidad que disminuye hacia el final = posible agotamiento o complejidad creciente.
- Períodos con velocidad = 0: el equipo no completó nada esa semana (investigar causa).

#### Task Distribution (gráfico de dona)

**Qué muestra:** La distribución porcentual de tareas por estado.

- **Sectores coloreados:** Cada sector = un estado (Por hacer, En progreso, En revisión, Bloqueada, Completada, Cancelada).
- **Porcentajes:** Qué fracción del total de tareas está en cada estado.

**Cómo leer:**
- Un proyecto saludable en fase de ejecución tiene la mayoría en "En progreso" y "Completada".
- Un alto porcentaje en "Bloqueada" indica impedimentos sistémicos.
- Un alto porcentaje en "Por hacer" en un proyecto avanzado puede indicar retraso.

#### Resource Utilization (barras horizontales)

**Qué muestra:** El porcentaje de utilización de cada miembro del equipo en el período seleccionado.

- **Filas:** Un miembro del equipo por fila.
- **Barras:** Longitud proporcional al porcentaje de utilización (0% a 100%+).
- **Colores:** Verde = normal, Amarillo = alto, Rojo = sobreasignado.

**Cómo leer:**
- Barras muy cortas (< 30%): el recurso está subutilizado, podría asumir más trabajo.
- Barras por encima del 100%: el recurso está sobreasignado; puede haber riesgo de burnout o retrasos.

### 12.4 Cómo leer cada gráfico paso a paso

**Proceso de análisis recomendado para una revisión semanal:**

1. Revisar los **KPI cards** primero (2 minutos): ¿hay alertas rojas?
2. Ver el **Burn Down** (3 minutos): ¿estamos en ritmo o hay retraso acumulado?
3. Ver la **distribución de tareas (dona)** (1 minuto): ¿hay muchas tareas bloqueadas?
4. Ver **Resource Utilization** (2 minutos): ¿alguien está sobreasignado o subutilizado?
5. Si hay problemas, profundizar en los datos de tareas específicas.

### 12.5 Exportación de datos

Para exportar datos del analytics:

1. En el dashboard de analytics, haga clic en el botón de descarga (ícono en la barra de herramientas del Analytics).
2. Los datos se descargarán en el formato disponible.

> **Nota:** La exportación a Excel con múltiples hojas (KPIs, tareas, horas, burn down) es una funcionalidad en desarrollo. La exportación actual puede generar un archivo con los datos básicos disponibles.

### 12.6 Comparación entre proyectos

Desde el **Dashboard principal** (no desde el detalle de un proyecto):

1. En el sidebar, haga clic en **Dashboard**.
2. La vista multiproyecto muestra tarjetas comparativas de todos los proyectos activos.
3. Use los filtros de fecha y tipo de proyecto para comparar proyectos similares.
4. El gráfico de comparación de velocidad muestra qué proyectos están avanzando más rápido.

---

## 13. Scheduling Avanzado

Las herramientas de programación avanzada del proyecto están distribuidas en múltiples ubicaciones de la interfaz:

- **Auto-Schedule:** accesible desde el botón **Scheduling** (con ícono de calendario y flecha desplegable) en el encabezado del proyecto.
- **Baselines:** tab **Baselines** del proyecto.
- **Escenarios What-If:** tab **Escenarios** del proyecto.
- **Restricciones de tarea:** sección **Restricciones** dentro del detalle de cada tarea.

### 13.1 Auto-Schedule

#### Cuándo usarlo

Use Auto-Schedule cuando:
- Haya definido todas las tareas con sus duraciones estimadas.
- Haya establecido las dependencias entre tareas.
- Necesite calcular automáticamente las fechas óptimas sin hacerlo manualmente.
- Cambie duraciones o dependencias y necesite recalcular todo el cronograma.

#### Modos ASAP vs ALAP

| Modo | Nombre | Descripción |
|---|---|---|
| ASAP | As Soon As Possible | Cada tarea se programa para comenzar lo más pronto posible dentro de sus restricciones |
| ALAP | As Late As Possible | Cada tarea se programa para comenzar lo más tarde posible sin retrasar el proyecto |

**¿Cuándo usar cada modo?**

- **ASAP** (más común): para proyectos donde quiere terminar lo antes posible y maximizar el margen de maniobra.
- **ALAP**: para proyectos donde los recursos son limitados y se prefiere no comprometerse antes de lo necesario.

#### Previsualización antes de aplicar

Antes de aplicar el Auto-Schedule, puede previsualizarlo:

1. En el encabezado del proyecto, haga clic en el botón **Scheduling**.
2. Seleccione **Auto-Schedule** en el menú desplegable.
3. En el diálogo, seleccione el modo (ASAP o ALAP).
4. Active la opción **Previsualizar cambios (dry run)**.
5. Haga clic en **Calcular**.
5. El sistema muestra:
   - Número de tareas que serían reprogramadas.
   - Nueva fecha de fin del proyecto proyectada.
   - Ruta crítica calculada.
   - Advertencias (si hay tareas sin fechas de inicio del proyecto, sin dependencias, etc.).
6. Revise la previsualización.
7. Si está conforme, haga clic en **Aplicar cambios**.
8. Si no, haga clic en **Cancelar** (no se modificó nada en los datos reales).

> **Advertencia:** Una vez aplicado el Auto-Schedule (sin dry run), las fechas de todas las tareas calculadas serán sobrescritas. Las tareas con restricciones de fechas (`MUST_START_ON`, `MUST_FINISH_ON`) no serán modificadas.

#### Restricciones respetadas

El Auto-Schedule respeta automáticamente:
- Todas las dependencias (FS, SS, FF, SF) con sus lag times.
- Las restricciones de fechas configuradas en cada tarea (ver sección 13.3).
- La fecha de inicio del proyecto como punto de partida.

### 13.2 Nivelación de recursos

> **Nota:** La nivelación automática de recursos no está disponible en la interfaz actual. Para gestionar la carga del equipo, use el tab **Equipo** del proyecto para revisar las asignaciones y ajústalas manualmente desde el detalle de cada tarea (sección Recursos).

### 13.3 Restricciones de tareas

Las restricciones limitan cuándo puede empezar o terminar una tarea, más allá de lo que dicten las dependencias.

#### Tipos de restricciones

| Código | Nombre | Descripción | Requiere fecha |
|---|---|---|---|
| `ASAP` | Tan pronto como sea posible | Sin restricción de fecha, la tarea empieza lo antes posible | No |
| `ALAP` | Tan tarde como sea posible | Sin restricción de fecha, la tarea empieza lo más tarde posible | No |
| `SNET` | No empezar antes de | La tarea no puede iniciar antes de la fecha indicada | Sí |
| `SNLT` | No empezar después de | La tarea debe iniciar a más tardar en la fecha indicada | Sí |
| `FNET` | No terminar antes de | La tarea no puede terminar antes de la fecha indicada | Sí |
| `FNLT` | No terminar después de | La tarea debe terminar a más tardar en la fecha indicada | Sí |
| `MSO` | Debe iniciar en | La tarea DEBE comenzar exactamente en la fecha indicada | Sí |
| `MFO` | Debe terminar en | La tarea DEBE terminar exactamente en la fecha indicada | Sí |

#### Crear una restricción

1. Abra el detalle de la tarea (botón de flecha en la lista de tareas).
2. Busque la sección **Restricciones** en el panel de la tarea.
3. Haga clic en **+ Agregar restricción**.
4. Seleccione el tipo de restricción.
5. Si el tipo requiere fecha, seleccione la fecha correspondiente.
6. Guarde.

> **Nota:** Una tarea solo puede tener una restricción activa a la vez. Si agrega una nueva, reemplaza la anterior.

#### Eliminar una restricción

1. En la sección de restricciones de la tarea, haga clic en el ícono de eliminar (basura) junto a la restricción.
2. Confirme. La tarea vuelve al modo ASAP por defecto.

### 13.4 Baselines

#### Qué es una baseline

Una **Baseline** (línea base) es una fotografía del plan del proyecto en un momento específico. Captura el estado de todas las tareas en esa fecha: fechas de inicio y fin planificadas, horas estimadas, estado, etc.

Las baselines permiten comparar el plan original con el avance real y detectar desviaciones.

#### Crear una baseline

> **Tip:** Cree la primera baseline justo antes de iniciar la ejecución del proyecto. Este será su "plan de referencia" contra el cual comparar el avance real.

1. En el detalle del proyecto, haga clic en el tab **Baselines**.
2. Haga clic en **+ Crear Baseline**.
3. Complete:
   - **Nombre:** identificador descriptivo (ej: "Baseline inicial - Enero 2026", "Baseline post-cambio de alcance").
   - **Descripción:** contexto de por qué se creó esta baseline.
   - **Establecer como activa:** marque esta opción para que sea la baseline de referencia en el Gantt.
4. Haga clic en **Guardar**.

La baseline guarda para cada tarea: nombre, código, fecha inicio, fecha fin, horas estimadas y estado.

#### Comparar baseline vs avance real

1. En el tab **Baselines** del proyecto, en la sección **Comparar con baseline**, seleccione la baseline a comparar en el selector desplegable.
2. Haga clic en **Calcular comparación**.
3. Se muestra una tabla con:

| Columna | Descripción |
|---|---|
| Código / Nombre | Identificador de la tarea |
| Inicio baseline | Fecha de inicio en la baseline |
| Fin baseline | Fecha de fin en la baseline |
| Inicio actual | Fecha de inicio actual de la tarea |
| Fin actual | Fecha de fin actual de la tarea |
| Variación (días) | Diferencia en días (positivo = retraso) |
| Estado | Adelantada, En tiempo, Retrasada |

4. El resumen al inicio muestra: total de tareas, cuántas están adelantadas, en tiempo y retrasadas.

#### Múltiples baselines

Puede crear múltiples baselines a lo largo del proyecto (ej: una al inicio, otra tras un cambio de alcance, otra a la mitad del proyecto). Solo una puede ser la **baseline activa** que aparece en el overlay del Gantt.

Para cambiar la baseline activa:
1. En el tab **Baselines**, en la lista de baselines creadas, use los controles disponibles para gestionar la baseline activa.

### 13.5 Escenarios What-If

#### Qué es un escenario

Un **escenario What-If** (¿Qué pasa si?) le permite simular cambios en el plan del proyecto sin afectar los datos reales. Puede preguntar, por ejemplo:
- "¿Qué pasa si la tarea X se retrasa 2 semanas?"
- "¿Qué pasa si reduzco la asignación del recurso Y al 50%?"
- "¿Qué pasa si elimino la dependencia entre A y B?"

#### Crear y configurar un escenario

1. En el tab **Escenarios** del proyecto, haga clic en **+ Nuevo Escenario**.
2. Complete:
   - **Nombre:** descripción del escenario (ej: "Impacto de retraso en cimentación").
   - **Descripción:** detalle del supuesto que está analizando.
3. En la sección **Cambios propuestos**, configure los cambios:

**Cambios en tareas:**
- Para cada tarea que desee modificar en el escenario, ingrese los campos a cambiar (fecha inicio, fecha fin, duración).
- Ejemplo: `{ "uuid-tarea-001": { "fecha_inicio": "2026-05-01", "fecha_fin": "2026-05-20" } }`

**Cambios en recursos:**
- Modifique el porcentaje de asignación de recursos en el escenario.

**Cambios en dependencias:**
- Modifique el lag time de dependencias existentes.

4. Guarde el escenario.

#### Ejecutar simulación

1. En la lista de escenarios, haga clic en el escenario que creó.
2. Haga clic en **Ejecutar simulación**.
3. El sistema calcula el impacto de los cambios propuestos y muestra:
   - Nueva fecha de fin proyectada del proyecto.
   - Diferencia en días respecto al plan actual (delta de días).
   - Nueva ruta crítica.
   - Número de tareas afectadas.

#### Comparar escenarios

1. En la lista de escenarios, seleccione 2 o más escenarios con las casillas de selección.
2. Haga clic en **Comparar seleccionados**.
3. Se muestra una tabla comparativa:

| Escenario | Fecha fin simulada | Delta días | Tareas afectadas |
|---|---|---|---|
| Plan actual | 2026-06-30 | 0 | — |
| Retraso cimentación | 2026-07-15 | +15 | 12 |
| Recurso reducido | 2026-07-08 | +8 | 5 |

#### Aplicar o descartar cambios

- Si después del análisis decide implementar un escenario en el plan real: haga clic en **Aplicar escenario** y confirme en el diálogo. Los cambios del escenario se copiarán al plan real del proyecto.
- Si decide no implementarlo: simplemente cierre el escenario. Los datos reales no se modifican.

> **Advertencia:** Aplicar un escenario sobrescribe las fechas del plan real. Antes de aplicar, asegúrese de haber creado una baseline para poder comparar antes y después.

---

## 14. Budget & Cost Tracking

### 14.1 Presupuesto del proyecto

#### Crear y aprobar presupuesto

**Para crear el presupuesto:**

1. Ingrese al detalle del proyecto.
2. Haga clic en el tab **Presupuesto**.
3. Si no existe presupuesto, haga clic en **+ Crear presupuesto**.
4. Complete el formulario:

| Campo | Descripción |
|---|---|
| Costo de labor planificado | Presupuesto total asignado a horas de trabajo humano |
| Costo de gastos planificado | Presupuesto para materiales, equipos, viajes, etc. |
| Presupuesto total planificado | Suma total (puede ser diferente a labor + gastos si hay margen adicional) |
| Umbral de alerta (%) | Porcentaje de ejecución a partir del cual se activan alertas (ej: 80%) |
| Moneda | COP (Peso colombiano) por defecto |
| Notas | Observaciones sobre el presupuesto |

5. Guarde el presupuesto.

**Para aprobar el presupuesto:**

> **Advertencia:** Una vez aprobado el presupuesto, no se pueden modificar los campos de costo planificado. Si necesita ajustarlo, deberá crear un nuevo presupuesto (el anterior queda como histórico).

1. En el panel de presupuesto, haga clic en **Aprobar presupuesto**.
2. Solo usuarios con rol `company_admin` pueden aprobar presupuestos.
3. El sistema registra quién aprobó y cuándo.
4. El presupuesto aprobado es el que se usa para las métricas EVM.

### 14.2 Tarifas de costo por recurso

Las **tarifas de costo** definen cuánto cuesta por hora de trabajo cada miembro del equipo. Se usan para calcular el costo real de labor a partir de los timesheets. En el tab **Presupuesto**, hay una sección dedicada **Tarifas por Recurso** que muestra todas las tarifas activas.

**Para crear una tarifa:**

1. En el tab **Presupuesto**, desplácese hasta la sección **Tarifas por Recurso**.
2. Haga clic en **+ Agregar tarifa**.
3. Complete:

| Campo | Descripción |
|---|---|
| Usuario | El miembro del equipo |
| Tarifa por hora | Costo por hora de trabajo (ej: 75.000 COP/hora) |
| Fecha de inicio | Desde cuándo aplica esta tarifa |
| Fecha de fin | Hasta cuándo aplica (vacío = vigente indefinidamente) |
| Moneda | COP por defecto |
| Notas | Contexto adicional |

4. Guarde.

> **Nota:** No puede haber dos tarifas activas para el mismo usuario que se solaapen en fechas. El sistema valida esto al guardar. Si el costo del recurso cambió (aumento salarial, cambio de categoría), cree una nueva tarifa con la nueva fecha de inicio y cierre la anterior con la fecha de fin correspondiente.

### 14.3 Gastos del proyecto

Los **gastos** registran todos los costos que no son horas de trabajo: materiales comprados, alquiler de equipos, viáticos, licencias de software, subcontratos, capacitaciones, etc. En el tab **Presupuesto**, la sección **Gastos directos** muestra el listado de gastos registrados.

#### Registrar un gasto

1. En el tab **Presupuesto**, en la sección **Gastos directos**, haga clic en **+ Registrar gasto**.
2. Complete el formulario:

| Campo | Descripción |
|---|---|
| Categoría | Equipment, Software, Travel, Training, Subcontractor, Materials, Other |
| Descripción | Qué se compró o pagó |
| Monto | Valor del gasto |
| Moneda | COP por defecto |
| Fecha | Fecha en que se incurrió el gasto |
| Pagado por | Usuario que realizó el pago (opcional) |
| Facturable | Si este gasto se facturará al cliente |
| URL de factura/recibo | Enlace al documento soporte (opcional) |
| Notas | Información adicional |

3. Guarde.

#### Aprobar gastos

Los gastos inician en estado **pendiente**. Deben ser aprobados antes de incluirse en los reportes de costo real.

> **Nota (segregación de funciones):** El mismo usuario que registró el gasto NO puede aprobarlo. Esto garantiza control interno.

**Para aprobar un gasto:**

1. En la lista de gastos, los gastos pendientes aparecen con el estado "Pendiente".
2. Un usuario diferente al que registró el gasto (con permiso de aprobación) hace clic en el ícono de aprobar (✓).
3. Confirme en el diálogo.
4. El gasto pasa a estado **Aprobado** y se suma al costo real del proyecto.

**Filtros disponibles en la lista de gastos:**
- Por categoría.
- Por estado (pendiente, aprobado).
- Por facturable (sí/no).
- Por rango de fechas.

### 14.4 Dashboard de presupuesto

El dashboard de presupuesto muestra en tiempo real el estado financiero del proyecto.

**Summary cards (tarjetas resumen):**

| Card | Descripción |
|---|---|
| Presupuesto total | Monto aprobado del presupuesto |
| Costo de labor | Horas registradas × tarifa por hora de cada recurso |
| Gastos aprobados | Suma de todos los gastos en estado aprobado |
| Costo total actual | Labor + Gastos |
| Saldo restante | Presupuesto total − Costo total actual |
| % ejecutado | (Costo total / Presupuesto) × 100 |

**Alertas de presupuesto:**

| Estado | Color | Condición |
|---|---|---|
| Normal | Verde | % ejecutado < umbral de alerta |
| Advertencia | Amarillo | % ejecutado ≥ umbral de alerta |
| Crítico | Rojo | % ejecutado ≥ 100% (sobre presupuesto) |

**Cost breakdown por recurso:**
- Tabla con: recurso, horas trabajadas, costo total, % del total.
- Identifica qué recursos consumen más presupuesto de labor.

**Cost breakdown por tarea:**
- Tabla con: tarea, horas estimadas, horas reales, costo real, variación de horas.
- Identifica qué tareas están generando sobrecostos.

### 14.5 EVM — Earned Value Management

El **Earned Value Management (EVM)** es la metodología estándar de la industria para medir el desempeño de un proyecto integrando alcance, tiempo y costo. Se muestra en la sección **Earned Value Management (EVM)** del tab Presupuesto.

Para que el EVM calcule valores (en lugar de mostrar "—"), el proyecto debe tener:
- Un presupuesto creado y aprobado.
- Timesheets registrados con horas.
- Tareas con fechas y horas estimadas.
- Tarifas de costo configuradas para los recursos.

> **Nota:** Si alguno de estos elementos falta, las métricas EVM mostrarán "—". El avance se calcula automáticamente y se muestra como "% completado" junto al panel EVM.

#### Métricas EVM

| Métrica | Nombre completo | Descripción |
|---|---|---|
| **BAC** | Budget at Completion | Presupuesto total aprobado del proyecto |
| **PV** | Planned Value | Trabajo que debería haber sido completado hasta hoy según el plan |
| **EV** | Earned Value | Valor del trabajo realmente completado hasta hoy (% avance × BAC) |
| **AC** | Actual Cost | Costo real incurrido hasta hoy (labor + gastos) |
| **CV** | Cost Variance | EV − AC. Variación de costo: positivo = bajo presupuesto, negativo = sobre presupuesto |
| **SV** | Schedule Variance | EV − PV. Variación de cronograma: positivo = adelantado, negativo = retrasado |
| **CPI** | Cost Performance Index | EV / AC. Eficiencia de costo: > 1 = bajo presupuesto, < 1 = sobre presupuesto |
| **SPI** | Schedule Performance Index | EV / PV. Eficiencia de cronograma: > 1 = adelantado, < 1 = retrasado |
| **EAC** | Estimate at Completion | Costo proyectado al final del proyecto al ritmo actual: BAC / CPI |
| **ETC** | Estimate to Complete | Cuánto se espera gastar de aquí en adelante: EAC − AC |
| **TCPI** | To-Complete Performance Index | Eficiencia necesaria para terminar dentro del BAC: (BAC − EV) / (BAC − AC) |
| **VAC** | Variance at Completion | BAC − EAC. Diferencia proyectada al cierre: positivo = ahorro, negativo = sobrecosto |

#### Cómo interpretar CPI y SPI

**Interpretación del CPI (eficiencia de costo):**

| CPI | Interpretación |
|---|---|
| > 1.1 | Muy por debajo del presupuesto (revisar si las estimaciones son correctas) |
| 0.95 − 1.1 | En buen control, dentro del presupuesto |
| 0.85 − 0.95 | Advertencia: comenzando a superar el presupuesto |
| < 0.85 | Crítico: sobre presupuesto, requiere acción inmediata |

**Interpretación del SPI (eficiencia de cronograma):**

| SPI | Interpretación |
|---|---|
| > 1.1 | Adelantado respecto al plan |
| 0.95 − 1.1 | En tiempo, dentro del cronograma |
| 0.85 − 0.95 | Advertencia: comenzando a retrasarse |
| < 0.85 | Crítico: cronograma retrasado, requiere acción |

#### Salud del cronograma y costo

| Estado | Condición |
|---|---|
| `on_track` (verde) | SPI/CPI ≥ 0.95 |
| `at_risk` (amarillo) | 0.85 ≤ SPI/CPI < 0.95 |
| `behind` / `over_budget` (rojo) | SPI/CPI < 0.85 |

### 14.6 Facturación

> **Nota:** La sección de Facturación (generación de datos para cobrar al cliente con líneas de labor y gastos facturables) no está disponible en la versión actual. Para obtener los datos de factura, exporte los gastos del proyecto y consulte el costo de labor desde el desglose por recurso en el tab Presupuesto.

---

## 15. Terceros (Clientes y Proveedores)

### 15.1 Qué son los terceros en Saicloud

Los **Terceros** son las empresas o personas naturales externas a su organización con quienes tiene relaciones comerciales. En el contexto de proyectos, los terceros son principalmente los **clientes** para quienes ejecuta proyectos.

### 15.2 Crear un tercero

1. En el sidebar (sección Acceso Rápido), haga clic en **Terceros**, o navegue a la URL `/terceros`.
2. Haga clic en **+ Nuevo tercero**.
3. Complete el formulario por secciones:

**Sección Identificación:**

| Campo | Obligatorio | Descripción |
|---|---|---|
| Tipo de persona | Sí | Persona natural o Persona jurídica |
| Tipo de tercero | No | Cliente, Proveedor, Sin clasificar u otros |
| Tipo de documento | Sí | NIT, Cédula, Pasaporte, etc. |
| Número de identificación | Sí | Número del documento (NIT sin dígito de verificación) |

**Sección Nombre completo:**

| Campo | Obligatorio | Descripción |
|---|---|---|
| Primer nombre | No | Para persona natural |
| Segundo nombre | No | Para persona natural |
| Primer apellido | Sí | Para persona natural, o razón social para jurídica |
| Segundo apellido | No | Para persona natural |

**Sección Información de contacto:**

| Campo | Obligatorio | Descripción |
|---|---|---|
| Email | No | Correo principal de contacto |
| Teléfono fijo | No | Teléfono de contacto |
| Celular | No | Celular de contacto |

**Sección Dirección principal:**

La dirección es opcional. Active la sección con el interruptor para ingresar la dirección física.

4. Haga clic en **Crear tercero** para guardar.

> **Nota:** Para empresas (personas jurídicas), ingrese la razón social en el campo "Primer apellido". El NIT se ingresa sin dígito de verificación en el campo "Número de identificación".

### 15.3 Asociar tercero a un proyecto

Al crear o editar un proyecto, el campo **Cliente** es un selector de terceros. Solo los terceros registrados como "Cliente" aparecen en este selector.

Para cambiar el cliente de un proyecto existente:
1. Edite el proyecto.
2. En el campo Cliente, seleccione el nuevo tercero.
3. Guarde.

> **Tip:** Si el cliente de un proyecto es también un proveedor en otro contexto (empresa que contrata y también suministra), cree el tercero con tipo "Ambos" para no duplicar registros.

---

## 16. Flujos de Trabajo Recomendados

### 16.1 Proyecto típico — Construcción / Obra Civil

Este flujo aplica para proyectos de construcción, obra civil, instalaciones, montajes y licitaciones públicas.

**Paso 1: Configuración inicial**
1. Crear el tercero (cliente) si no existe: empresa contratante, NIT, contacto.
2. Crear el proyecto: nombre, tipo "Obra civil", fechas contractuales, presupuesto del contrato.
3. Configurar el AIU: porcentajes de administración, imprevistos y utilidad.

**Paso 2: Definir estructura**
4. Crear las fases del proyecto: Diseño → Adquisiciones → Cimentación → Estructura → Instalaciones → Acabados → Entrega.
5. Agregar las actividades del catálogo que se usarán (excavación, concreto, acero, etc.) con sus unidades y costos.
6. Crear las tareas dentro de cada fase, vinculadas a las actividades del catálogo.

**Paso 3: Cronograma**
7. Crear dependencias FS entre tareas secuenciales (ej: cimentación FS estructura).
8. Agregar restricciones SNET en el detalle de cada tarea que tenga fecha mínima de inicio contractual.
9. Ejecutar **Auto-Schedule ASAP** desde el botón **Scheduling** del encabezado del proyecto.
10. Revisar el Gantt (tab Gantt): activar overlay Ruta Crítica para identificar las tareas críticas.
11. Crear la **baseline inicial** (tab Baselines → + Crear Baseline) antes de iniciar obras.

**Paso 4: Recursos y costos**
12. Asignar recursos (ingenieros, maestros de obra) a las tareas desde el detalle de cada tarea → sección Recursos.
13. Configurar tarifas de costo por recurso en el tab **Presupuesto** → sección Tarifas por Recurso.
14. Crear el presupuesto de costos en el tab **Presupuesto** → botón Editar, y aprobarlo con el botón de aprobación.

**Paso 5: Ejecución**
15. Activar la primera fase.
16. Los responsables registran cantidades ejecutadas (m³, ml) directamente en las tareas.
17. Registrar los timesheets de horas de profesionales y técnicos.
18. Registrar los gastos (compras de materiales, alquiler de equipos).
19. Aprobar gastos.

**Paso 6: Seguimiento semanal**
20. Revisar el tab **Gantt** con overlay Ruta Crítica activo: ¿alguna tarea crítica está retrasada?
21. Revisar el tab **Analytics**: KPIs de Completud y On-Time, gráfico Burn Down y distribución de tareas.
22. Revisar el tab **Presupuesto**: CPI y SPI en la sección EVM ≥ 0.95.
23. Tomar acciones correctivas si hay desviaciones.
24. Actualizar al cliente con los datos del dashboard y exportación.

### 16.2 Proyecto típico — Software / Tecnología de Información

Este flujo aplica para proyectos de desarrollo de software, implementación de sistemas, consultoría TI y proyectos ágiles.

**Paso 1: Estructura del proyecto**
1. Crear el proyecto con tipo "Consultoría" o "Servicios".
2. Definir fases como sprints o módulos: Sprint 1 → Sprint 2 → Sprint 3 → UAT → Go Live.
3. Crear tareas tipo user stories o tickets de desarrollo.

**Paso 2: Actividades del catálogo para TI**
4. Actividades recomendadas para crear en el catálogo:
   - "Desarrollo frontend" — Labor — horas
   - "Desarrollo backend" — Labor — horas
   - "QA / Testing" — Labor — horas
   - "Reunión de equipo" — Labor — horas
   - "Despliegue" — Hito
   - "Licencia de software" — Equipment — unidades

**Paso 3: Gestión ágil**
5. Usar el **Kanban** (tab Tareas → botón Kanban) para el flujo diario: Por Hacer → En Progreso → En Revisión → Completada.
6. Dependencias SS y FF para tareas paralelas (desarrollo de diferentes módulos en simultáneo).
7. Usar el **Timer** (sección Tiempo en el detalle de la tarea) para registrar tiempo de desarrollo en tiempo real.

**Paso 4: Métricas**
8. Tab Analytics: ver el **Velocity Chart** por sprint para detectar si el ritmo es sostenible.
9. Tab Analytics: el **Burn Down** muestra si el equipo terminará a tiempo.
10. Tab Baselines: crear baseline al inicio de cada sprint para comparar con el avance real.

**Paso 5: Seguimiento de costos**
11. Registrar los gastos del proyecto en el tab **Presupuesto** → sección Gastos directos.
12. Marcar como "facturable" los gastos que se cobran al cliente.
13. Al cerrar el mes, revisar el desglose de costos por recurso y por tarea en el tab Presupuesto.

---

## 17. Mejores Prácticas

### 17.1 Reglas para fases

- **Defina todas las fases al inicio**, aunque sea con nombres provisionales. Es mejor ajustar el nombre que reorganizar tareas entre fases después.
- **No cree más de 8-10 fases** por proyecto. Si necesita más, revise si está fragmentando demasiado.
- **Una sola fase activa**: la fase activa indica dónde está el equipo. No la cambie a diario; cámbiela cuando realmente avance a la siguiente etapa.
- **Nombre las fases por etapa del proceso**, no por tiempo ("Fase 1 de 5", no "Semana 1").

### 17.2 Reglas para tareas

- **Una tarea = un resultado entregable claro**. Si la descripción tiene muchos "y también...", probablemente son varias tareas.
- **Máximo 2-3 niveles de subtareas**. Más de eso indica que la estructura está demasiado fragmentada.
- **Asigne un responsable a cada tarea**. Las tareas sin responsable no tienen dueño y tienden a quedarse pendientes.
- **Fije fechas realistas**. Una tarea con fecha límite imposible desmotiva al equipo.
- **Actualice el estado de las tareas al menos una vez por semana**. El Kanban y el Burn Down dependen de actualizaciones frecuentes.

### 17.3 Nombrar actividades del catálogo

Adopte una convención consistente para los nombres del catálogo:

```
[Tipo de trabajo] [Recurso o material] [Acción]
```

**Ejemplos correctos:**
- "Mano de obra Maestro Excavación manual"
- "Material Concreto 3000 PSI Fundición"
- "Equipo Retroexcavadora Alquiler"
- "Consultoría Senior Análisis de requerimientos"

**Ejemplos incorrectos:**
- "Act. 001" (sin nombre descriptivo)
- "Trabajo general" (demasiado genérico)
- "Excavación y cimentación y relleno" (demasiado amplio)

### 17.4 Frecuencia de actualización recomendada

| Actividad | Frecuencia |
|---|---|
| Registrar timesheets | Diario (al final del día) |
| Actualizar estado de tareas | Diario o cada 2 días |
| Registrar cantidades ejecutadas | Al terminar cada avance parcial |
| Revisar Burn Down y Analytics | Semanal |
| Revisar EVM y presupuesto | Quincenal |
| Actualizar el Gantt / fechas | Al detectar cambios en el cronograma |
| Crear nueva baseline | Tras cambios significativos de alcance |

### 17.5 Cómo mantener el Gantt actualizado

El Gantt refleja las fechas de las tareas. Para mantenerlo preciso:

1. **Ejecute Auto-Schedule periódicamente** cuando cambie duraciones o dependencias.
2. **Actualice fechas reales de inicio** cuando comience a trabajar en una tarea (campo "Fecha de inicio").
3. **Actualice el estado de las tareas** a "Completada" cuando terminen, para que el cálculo de la ruta crítica sea correcto.
4. **No cambie fechas manualmente sin ejecutar Auto-Schedule después**, ya que puede dejar el cronograma inconsistente con las dependencias.

### 17.6 Cuándo crear una baseline

| Momento | Por qué |
|---|---|
| Justo antes de iniciar la ejecución | Para tener el plan original de referencia |
| Tras aprobar un cambio de alcance formal | Para documentar el nuevo plan acordado |
| Al inicio de cada fase importante | Para comparar el avance de esa fase |
| Cuando el CPI o SPI cae por debajo de 0.85 | Para tener un punto de referencia del replan |

### 17.7 Cómo gestionar cambios de alcance

Los cambios de alcance (agregar o quitar trabajo del proyecto) son comunes en proyectos reales. Cuando ocurra un cambio formal:

1. **Documente el cambio** antes de modificar nada en Saicloud: qué cambia, por qué, quién lo autorizó, con qué fecha.
2. **Cree una baseline** del plan actual (antes del cambio) para tener registro del plan original.
3. **Actualice el proyecto** en Saicloud: agregar/eliminar tareas, ajustar fechas, modificar presupuesto.
4. **Ejecute Auto-Schedule** para recalcular el cronograma con los cambios.
5. **Cree una nueva baseline** del plan revisado (después del cambio) con un nombre que indique el cambio (ej: "Baseline v2 - Cambio de alcance Abril 2026").
6. **Actualice el presupuesto** si aplica: cree un nuevo presupuesto ajustado y apruébelo.

> **Tip:** La comparación entre la Baseline v1 (plan original) y la Baseline v2 (plan ajustado) le permitirá demostrar el impacto del cambio de alcance al cliente o a la dirección.

### 17.8 Control de calidad de los datos

Para garantizar que los reportes y dashboards sean confiables, establezca estas rutinas de revisión:

**Diariamente (el coordinador o gerente):**
- Verificar que las tareas en progreso tienen timesheets registrados.
- Verificar que no hay tareas vencidas sin actualizar.

**Semanalmente (el gerente de proyecto):**
- Revisar que todos los gastos de la semana están registrados y en cola de aprobación.
- Revisar que el porcentaje de avance del proyecto parece coherente.
- Aprobar las ausencias de recursos pendientes.

**Mensualmente (el company_admin):**
- Revisar que las tarifas de recursos están vigentes y actualizadas.
- Revisar el catálogo de actividades: limpiar actividades duplicadas o mal nombradas.
- Revisar usuarios inactivos y desactivarlos si corresponde.

---

## 18. Troubleshooting

### Problemas de login y sesión expirada

**Síntoma:** La plataforma muestra "Su sesión ha expirado" y lo redirige al login.

**Causa:** Los tokens de sesión tienen una duración máxima de 8 horas de inactividad.

**Solución:**
1. Ingrese sus credenciales de nuevo.
2. Si necesita sesiones más largas, contacte al administrador para revisar la configuración de tokens.

**Síntoma:** "Credenciales inválidas" aunque el email y contraseña son correctos.

**Solución:**
1. Verifique que no tenga activado el Bloqueo de mayúsculas (Caps Lock).
2. Intente con el navegador en modo incógnito (descarta caché y cookies corrompidas).
3. Si el problema persiste, use la opción **¿Olvidé mi contraseña?** en el login para resetear.

---

### Gantt no muestra barras

**Síntoma:** El tab Gantt aparece vacío o muestra el mensaje "No hay tareas con fechas".

**Causa más común:** Las tareas no tienen fechas de inicio y fin asignadas.

**Solución:**
1. Verifique que las tareas del proyecto tengan **fecha de inicio** y **fecha de fin** configuradas.
2. Si las tareas no tienen fechas, ejecute el **Auto-Schedule** para calcularlas automáticamente.
3. Si las tareas tienen fechas pero el Gantt sigue vacío, verifique que el rango de fechas del Gantt incluya las fechas de las tareas (use el botón "Hoy" o ajuste el zoom).

---

### Timer no guarda al cerrar ventana

**Síntoma:** Inicia el Timer, cierra el navegador y al volver, las horas no quedaron guardadas.

**Causa:** El Timer corre en el cliente (navegador). Si se cierra la ventana sin detener el Timer, el tiempo no se envía al servidor.

**Solución:**
- Siempre detenga el Timer (botón Stop ⏹) antes de cerrar la sesión o el navegador.
- Si ya perdió el tiempo, regístrelo manualmente en Timesheets con la duración aproximada y una nota aclaratoria.

**Prevención:** Active las notificaciones del navegador para Saicloud. La plataforma enviará un recordatorio si cierra la ventana con el Timer activo.

---

### Tareas no aparecen en el Kanban

**Síntoma:** Crea una tarea pero no aparece en el Kanban.

**Causas posibles:**
1. **Filtro de fase activo:** el Kanban tiene un selector de fase en la parte superior. Si hay una fase seleccionada, solo muestra las tareas de esa fase.
2. **Estado de la tarea:** el Kanban muestra tareas en estados activos. Las tareas canceladas se ocultan por defecto.
3. **Tarea es subtarea:** las subtareas pueden estar ocultas si no se ha expandido la tarea padre.

**Solución:**
1. Revise el filtro de fase: seleccione "Todas las fases".
2. Active la opción "Mostrar canceladas" en los filtros del Kanban.
3. En la vista lista, verifique que la tarea existe y tiene el estado correcto.

---

### Auto-Schedule devuelve error de dependencia circular

**Síntoma:** Al ejecutar Auto-Schedule, aparece el mensaje "Dependencia circular detectada" y el proceso no se completa.

**Causa:** Existe un ciclo en las dependencias de las tareas. Por ejemplo: Tarea A depende de B, B depende de C, y C depende de A. Esto es imposible de resolver cronológicamente.

**Solución:**
1. En el tab Tareas, use la columna de dependencias para identificar las tareas involucradas en el ciclo.
2. Identifique cuál dependencia es incorrecta (la que crea el ciclo).
3. Elimine esa dependencia desde el detalle de la tarea.
4. Ejecute Auto-Schedule de nuevo.

> **Tip:** Para evitar ciclos, siga la regla: "las dependencias siempre deben ir hacia adelante en el tiempo". Si dos tareas son verdaderamente paralelas e independientes, no las vincule con dependencias.

---

### Analytics muestra 0 cuando hay datos

**Síntoma:** El dashboard de Analytics muestra todos los KPIs en 0 o los gráficos están vacíos, pero el proyecto tiene tareas y timesheets.

**Causas posibles:**
1. **Filtro de fecha:** el dashboard tiene un selector de período. Si el período seleccionado no incluye las fechas de los datos, se mostrará vacío.
2. **Tareas sin estados actualizados:** si todas las tareas están en "Por hacer", el Burn Down no tiene nada que quemar.
3. **Timesheets de otro proyecto:** verifique que los timesheets están asociados al proyecto correcto.

**Solución:**
1. Ajuste el selector de período para incluir el rango de fechas del proyecto.
2. Seleccione "Desde el inicio del proyecto" en el selector de período.
3. Si el problema persiste, recargue la página (F5).

---

### Presupuesto no se puede editar (ya está aprobado)

**Síntoma:** Intenta modificar los montos del presupuesto pero los campos están deshabilitados.

**Causa:** El presupuesto fue aprobado formalmente y el sistema lo protege para mantener integridad del historial financiero.

**Solución:**
1. Para ajustar el presupuesto, un `company_admin` debe crear un **nuevo presupuesto** con los valores actualizados.
2. El presupuesto anterior quedará como histórico con fecha de aprobación.
3. El nuevo presupuesto debe ser aprobado nuevamente antes de que el EVM lo use.

> **Tip:** Si el ajuste es menor (< 5%) y se debe a un error de digitación, contacte al administrador de Saicloud (ValMen Tech) para solicitar una corrección excepcional con justificación.

---

### Pregunta: ¿Puedo tener más de una fase activa?

**No.** El diseño de Saicloud solo permite **una fase activa a la vez** por proyecto. Esto refleja el principio de que un proyecto ejecuta sus etapas secuencialmente.

Si su proyecto ejecuta varias líneas de trabajo en paralelo, la recomendación es:
- Usar una sola fase que abarque el período de trabajo paralelo.
- Organizar las tareas paralelas con dependencias SS (inicio a inicio) para modelar el paralelismo.
- Usar las etiquetas (tags) de las tareas para diferenciar las líneas de trabajo dentro de la misma fase.

---

### El porcentaje de avance del proyecto no coincide con mi estimación

**Síntoma:** El proyecto muestra un 45% de avance pero usted considera que está al 60%.

**Causa:** El porcentaje de avance en Saicloud se calcula automáticamente a partir del estado y progreso de las tareas. Si las tareas no están actualizadas, el indicador reflejará datos desactualizados, no su percepción subjetiva del avance.

**Solución:**
1. Ingrese al tab **Tareas** del proyecto.
2. Revise cada tarea: ¿el estado y porcentaje de completado reflejan la realidad?
3. Actualice las tareas que estén desactualizadas.
4. Para tareas en modo "horas": registre los timesheets pendientes.
5. Para tareas en modo "cantidad": actualice la cantidad registrada.
6. El porcentaje del proyecto se recalculará automáticamente.

> **Nota:** El porcentaje de avance en Saicloud es siempre basado en datos objetivos (timesheets, cantidades, estados). Si necesita un porcentaje "de percepción", puede anotarlo en la descripción del proyecto como referencia adicional, pero el indicador del sistema siempre será el calculado automáticamente.

---

### No puedo eliminar una fase porque tiene tareas

**Síntoma:** Al intentar eliminar una fase, aparece el error "No se puede eliminar una fase que tiene tareas asociadas".

**Causa:** El sistema protege la integridad de los datos: no permite eliminar fases que tengan tareas, para evitar pérdida accidental de trabajo registrado.

**Solución:**
1. Mueva todas las tareas de la fase a otra fase (editando cada tarea y cambiando el campo Fase).
2. Una vez que la fase no tenga tareas, podrá eliminarla.
3. Alternativamente, si no necesita eliminar la fase sino solo ocultarla, cambie su estado a "Cancelada".

---

### Las dependencias no se reflejan en el Gantt

**Síntoma:** Creó dependencias entre tareas pero las flechas no aparecen en el Gantt.

**Causas posibles:**
1. Las tareas no tienen fechas de inicio y fin asignadas.
2. El nivel de zoom del Gantt está demasiado reducido y las flechas son muy pequeñas.

**Solución:**
1. Verifique que las tareas involucradas en las dependencias tengan fechas configuradas.
2. Ejecute Auto-Schedule para que el sistema calcule las fechas considerando las dependencias.
3. Ajuste el zoom del Gantt al nivel "Semanas" para una mejor visualización de las flechas.

---

### Los gastos aprobados no aparecen en el dashboard de presupuesto

**Síntoma:** Aprobó varios gastos pero el costo real en el dashboard sigue igual.

**Causa posible:** El dashboard puede estar mostrando un estado anterior en caché.

**Solución:**
1. Recargue la página del dashboard (F5 o Ctrl+R).
2. Verifique que los gastos estén en estado "Aprobado" (no "Pendiente") en la lista de gastos.
3. Compruebe que la fecha de los gastos está dentro del período mostrado en el dashboard.

---

## 19. Glosario

A continuación se definen los términos técnicos y conceptos clave usados en Saicloud.

| Término | Definición |
|---|---|
| **Actividad** | Plantilla de trabajo reutilizable del catálogo de la empresa. Define tipo, unidad de medida y costo unitario base. |
| **AIU** | Administración, Imprevistos y Utilidad. Porcentajes que se aplican sobre el costo directo de un proyecto para calcular el precio de venta. Estándar en licitaciones y obras civiles colombianas. |
| **ALAP** | *As Late As Possible*. Restricción o modo de scheduling que programa cada tarea para que comience lo más tarde posible sin retrasar el fin del proyecto. |
| **ASAP** | *As Soon As Possible*. Restricción o modo de scheduling que programa cada tarea para que comience lo más pronto posible dentro de sus restricciones. |
| **AC** | *Actual Cost* (Costo Actual). Costo real incurrido en el proyecto hasta la fecha de corte. Incluye labor (timesheets × tarifas) y gastos aprobados. Métrica EVM. |
| **Asignación** | Vínculo entre un recurso (usuario) y una tarea, con porcentaje de dedicación y rango de fechas. |
| **BAC** | *Budget at Completion* (Presupuesto hasta la Conclusión). El presupuesto total aprobado del proyecto. Es el valor de referencia para todas las métricas EVM. |
| **Baseline** | Fotografía del plan del proyecto en un momento específico. Guarda las fechas y estimaciones de todas las tareas para comparar con el avance real. |
| **Burn Down Chart** | Gráfico que muestra la reducción del trabajo pendiente a lo largo del tiempo. La línea ideal muestra el ritmo esperado; la línea real muestra el avance actual. |
| **Burn Rate** | Velocidad a la que se consume el presupuesto o las horas. Se mide como costo por unidad de tiempo (ej: $5 millones/semana). |
| **Capacidad** | Número de horas semanales disponibles de un recurso para trabajar en proyectos. Define el techo de asignación sin generar sobreasignación. |
| **Catálogo** | Biblioteca centralizada de actividades estándar de la empresa, compartida entre todos los proyectos. |
| **CPI** | *Cost Performance Index* (Índice de Desempeño de Costo). CPI = EV / AC. Indica eficiencia de costo. CPI > 1 = bajo presupuesto; CPI < 1 = sobre presupuesto. |
| **Dependencia** | Relación de orden entre dos tareas que determina cuándo puede comenzar o terminar una en función de la otra. |
| **Disponibilidad** | Registro de ausencias de un recurso (vacaciones, incapacidades, festivos) que reduce su capacidad en un período. |
| **EAC** | *Estimate at Completion* (Estimación hasta la Conclusión). Costo total proyectado al cierre. Fórmula más común: EAC = BAC / CPI. |
| **ETC** | *Estimate to Complete* (Estimación para Concluir). Cuánto se espera gastar de aquí al final: ETC = EAC − AC. |
| **EV** | *Earned Value* (Valor Ganado). Valor del trabajo completado: EV = BAC × % avance real. Métrica central del EVM. |
| **EVM** | *Earned Value Management*. Metodología de control de proyectos que integra alcance, tiempo y costo en indicadores cuantitativos (PV, EV, AC, CPI, SPI, etc.). |
| **Fase** | División lógica de un proyecto que agrupa tareas de una misma etapa. Solo puede estar activa una fase a la vez. |
| **FF** | *Finish to Finish* (Fin a Fin). Tipo de dependencia donde la tarea sucesora no puede terminar hasta que termine la predecesora. |
| **Float / Holgura** | Número de días que puede retrasarse una tarea sin retrasar la fecha de fin del proyecto. Float = 0 significa que la tarea está en la ruta crítica. |
| **FS** | *Finish to Start* (Fin a Inicio). Tipo de dependencia más común: la tarea sucesora no puede empezar hasta que termine la predecesora. |
| **Gantt** | Diagrama de barras horizontales que representa el cronograma del proyecto. Cada barra representa una tarea con su duración y fechas. |
| **Hito** | Tarea especial que representa un evento o entrega puntual. No tiene duración en el Gantt (aparece como un diamante ♦). El avance es binario: completado o no. |
| **Kanban** | Vista de gestión de tareas organizada en columnas por estado. Permite visualizar el flujo de trabajo del equipo. |
| **KPI** | *Key Performance Indicator* (Indicador Clave de Desempeño). Métrica cuantificable que mide el desempeño de un proceso o proyecto. |
| **Lag** | Tiempo de espera adicional entre el evento de la tarea predecesora y el de la sucesora en una dependencia. Puede ser positivo (espera) o negativo (solapamiento). |
| **NIT** | Número de Identificación Tributaria. Documento de identificación de personas jurídicas en Colombia para efectos fiscales. |
| **Overlay** | Capa de información adicional que se superpone al Gantt para mostrar ruta crítica, holgura o baseline. |
| **Proyecto** | Unidad principal de trabajo en Saicloud. Tiene cliente, presupuesto, fechas, gerente y se divide en fases y tareas. |
| **PV** | *Planned Value* (Valor Planificado). Trabajo que debería haber sido completado hasta la fecha de corte según el cronograma original. PV = BAC × % planificado a la fecha. |
| **Recurso** | Persona (usuario de la plataforma) que puede ser asignada a tareas para ejecutar el trabajo. |
| **Ruta crítica** | Secuencia de tareas cuya suma de duraciones define la duración mínima del proyecto. Cualquier retraso en la ruta crítica retrasa el proyecto completo. |
| **SF** | *Start to Finish* (Inicio a Fin). Tipo de dependencia donde la tarea sucesora no puede terminar hasta que empiece la predecesora. Raro en práctica. |
| **SPI** | *Schedule Performance Index* (Índice de Desempeño de Cronograma). SPI = EV / PV. Indica eficiencia de tiempo. SPI > 1 = adelantado; SPI < 1 = retrasado. |
| **SS** | *Start to Start* (Inicio a Inicio). Tipo de dependencia donde la tarea sucesora no puede empezar hasta que empiece la predecesora. |
| **Sobreasignación** | Situación en que el porcentaje total de asignaciones de un recurso en un período supera el 100% de su capacidad disponible. |
| **Tarea** | Unidad mínima de trabajo asignable a una persona dentro de una fase. Puede tener subtareas, dependencias, timesheets y actividades del catálogo. |
| **TCPI** | *To-Complete Performance Index*. Eficiencia de costo que debe lograrse de aquí en adelante para terminar dentro del BAC. TCPI = (BAC − EV) / (BAC − AC). |
| **Tercero** | Empresa o persona natural externa con quien se tiene relación comercial. En proyectos, generalmente es el cliente. |
| **Timer** | Cronómetro integrado en Saicloud para registrar tiempo de trabajo en tiempo real. Al detenerlo, genera automáticamente un timesheet. |
| **Timesheet** | Registro individual de horas trabajadas en una tarea específica. Contiene: fecha, horas, descripción y usuario. |
| **VAC** | *Variance at Completion* (Variación en la Conclusión). VAC = BAC − EAC. Ahorro o sobrecosto proyectado al cierre. Positivo = ahorro; negativo = sobrecosto. |
| **Velocity** | Velocidad del equipo: cantidad de trabajo completado por período (semana, sprint). Base para las predicciones de entrega. |
| **What-If** | Herramienta de simulación que permite analizar el impacto de cambios hipotéticos en el cronograma sin modificar el plan real. |

---

## 20. Notificaciones y Alertas

### 20.1 Tipos de notificaciones

Saicloud envía notificaciones automáticas para mantener al equipo informado de eventos importantes. Las notificaciones aparecen en el ícono de campana (🔔) en la barra superior.

| Evento | Quién recibe |
|---|---|
| Se le asigna una tarea como responsable | El responsable asignado |
| Una tarea en la que es seguidor cambia de estado | Todos los seguidores |
| Una tarea que usted creó es completada | El creador |
| Una tarea vence hoy o mañana | El responsable y los seguidores |
| Se aprueba o rechaza una ausencia | El usuario que la solicitó |
| Un gasto pendiente requiere aprobación | Los usuarios con permiso de aprobación |
| El presupuesto supera el umbral de alerta | El gerente del proyecto y el company_admin |
| Se aplica un escenario What-If al plan real | El gerente del proyecto |
| Una dependencia circular es detectada | El usuario que intentó crear la dependencia |

### 20.2 Gestionar notificaciones

**Para ver todas las notificaciones:**
1. Haga clic en el ícono de campana en la barra superior.
2. Se abre el panel de notificaciones con las más recientes.
3. Haga clic en "Ver todas" para la lista completa.

**Para marcar como leída:**
- Haga clic en la notificación para ir al recurso relacionado (la marca como leída automáticamente).
- O haga clic en el ícono de check junto a la notificación.

**Para configurar qué notificaciones recibir:**
1. Mi perfil → Notificaciones.
2. Active o desactive cada tipo de notificación.
3. Configure si también quiere recibirlas por correo electrónico.

> **Tip:** Si recibe demasiadas notificaciones, desactive las de "cambio de estado" y mantenga solo las de asignación y vencimiento. Así solo recibirá notificaciones accionables.

### 20.3 Alertas de presupuesto

Las alertas de presupuesto son automáticas y se calculan cada vez que se registra un gasto o timesheet:

| Alerta | Condición | Acción recomendada |
|---|---|---|
| Normal (verde) | Ejecución < umbral definido | Continuar normal |
| Advertencia (amarillo) | Ejecución ≥ umbral definido | Revisar proyección; ¿habrá sobrecosto? |
| Crítico (rojo) | Ejecución ≥ 100% del presupuesto | Reunión urgente de control de costos |

El umbral de advertencia se configura por proyecto en el módulo de Presupuesto (campo "Umbral de alerta"). El valor recomendado es 80%.

---

## 21. Casos de Uso por Industria

### 21.1 Construcción e Ingeniería Civil

**Características clave para este sector:**

En proyectos de construcción, el control de cantidades de obra es fundamental. La combinación de actividades del catálogo con unidades físicas (m³, ml, ton) y el módulo de EVM permiten llevar un control riguroso del avance físico y financiero.

**Configuración recomendada del catálogo:**

Cree estas actividades base antes de su primer proyecto de construcción:

| Actividad | Tipo | Unidad | Uso |
|---|---|---|---|
| Excavación manual | Labor | m³ | Movimiento de tierra sin maquinaria |
| Excavación mecánica | Equipment | m³ | Retroexcavadora u otro equipo |
| Relleno y compactación | Labor | m³ | Material de relleno compactado |
| Concreto 2500 PSI | Material | m³ | Concreto para estructuras menores |
| Concreto 3000 PSI | Material | m³ | Concreto estructural estándar |
| Acero de refuerzo | Material | kg | Varillas de refuerzo |
| Mampostería bloque | Material | m² | Muros de bloque |
| Instalación hidráulica | Labor | ml | Tubería hidráulica instalada |
| Instalación eléctrica | Labor | ml | Cableado eléctrico instalado |
| Dirección técnica | Labor | horas | Tiempo de profesional en obra |
| Interventoría | Labor | horas | Tiempo de interventor |
| Equipos topografía | Equipment | días | Nivel, estación total, GPS |

**Flujo de registro diario en obra:**

El maestro de obra o residente registra el avance en campo usando su celular:
1. Abrir Saicloud en el navegador del celular.
2. Ir a la tarea correspondiente (ej: "Excavación zapata Z-1").
3. Actualizar la cantidad registrada (ej: de 15 m³ a 22 m³).
4. El sistema calcula automáticamente el nuevo % de avance.
5. Opcionalmente, agregar una nota con observaciones del día.

**Informe de obra semanal:**
- Exportar el reporte de Analytics a Excel.
- El Excel incluye el avance por tarea con cantidad planificada vs ejecutada.
- Se puede presentar directamente al cliente o al interventor.

### 21.2 Consultoría y Servicios Profesionales

**Características clave para este sector:**

En consultoría, el recurso principal son las horas de trabajo de los profesionales. El Timer y los timesheets son las herramientas más usadas. La facturación basada en horas se genera directamente desde el módulo de Budget.

**Configuración recomendada del catálogo:**

| Actividad | Tipo | Unidad | Tarifa típica |
|---|---|---|---|
| Consultoría Director | Labor | horas | Alta |
| Consultoría Senior | Labor | horas | Media-alta |
| Consultoría Junior | Labor | horas | Media |
| Análisis de datos | Labor | horas | Media |
| Taller/Capacitación | Labor | horas | Media-alta |
| Desplazamiento local | Labor | horas | Baja |
| Revisión entregable | Labor | horas | Media |
| Entrega de informe | — | hito | — |

**Flujo de facturación mensual:**

1. Al cierre del mes, cada consultor confirma que todos sus timesheets están registrados.
2. El gerente revisa y aprueba los timesheets del mes.
3. Se registran los gastos del mes (viáticos, transporte, licencias de software).
4. Se aprueban los gastos facturables.
5. Se genera el reporte de facturación desde el módulo de Budget.
6. El Excel exportado va al área administrativa para emitir la factura electrónica en Saiopen.

### 21.3 Proyectos de Tecnología e Innovación

**Características clave para este sector:**

Los proyectos de TI suelen tener requisitos cambiantes y equipos distribuidos. El Kanban, los sprints como fases, el Velocity Chart y las dependencias SS son las herramientas más relevantes.

**Gestión de sprints con Saicloud:**

Estructura recomendada:
```
Proyecto: "Desarrollo Sistema de Inventarios"
├── Fase: Sprint 0 - Planeación (2 semanas)
│     ├── Tarea: Levantamiento de requerimientos
│     ├── Tarea: Diseño de arquitectura
│     └── Hito: Documento de requerimientos aprobado
├── Fase: Sprint 1 - Módulo de entradas (2 semanas)
│     ├── Tarea: API de entradas de inventario
│     ├── Tarea: Pantalla de registro de entradas
│     └── Hito: Sprint 1 completado
└── (etc.)
```

**Métricas de TI más relevantes:**
- **Velocity Chart:** cuántas tareas se completan por sprint. Permite predecir cuántos sprints quedan.
- **Burn Down:** ¿terminaremos a tiempo? La pendiente de la línea real vs la ideal lo indica.
- **Distribución de estados (dona):** ¿hay tareas atascadas en "En revisión" hace muchos días?

---

## 22. Referencia Rápida de Estados

### 20.1 Estados de proyectos

| Estado | Código interno | Color UI | Acciones permitidas |
|---|---|---|---|
| Borrador | `draft` | Gris | Editar todo, eliminar |
| Planificado | `planned` | Azul | Editar, crear fases/tareas, cambiar a En ejecución |
| En ejecución | `in_progress` | Verde | Registrar tiempo, actualizar avance, crear gastos |
| Suspendido | `suspended` | Amarillo | Solo lectura excepto reactivar |
| Cerrado | `closed` | Negro | Solo lectura, exportar reportes |
| Cancelado | `cancelled` | Rojo | Solo lectura, no aparece en listados activos por defecto |

### 20.2 Estados de tareas

| Estado | Código interno | Descripción |
|---|---|---|
| Por hacer | `todo` | La tarea está pendiente de comenzar |
| En progreso | `in_progress` | Alguien está trabajando activamente en la tarea |
| En revisión | `in_review` | La tarea fue entregada y está siendo revisada/aprobada |
| Bloqueada | `blocked` | Hay un impedimento que impide avanzar |
| Completada | `completed` | La tarea fue finalizada exitosamente |
| Cancelada | `cancelled` | La tarea no se realizará |

> **Tip:** Use el estado "En revisión" para tareas que requieren validación antes de marcarlas como completadas. Esto es especialmente útil en proyectos donde el gerente debe aprobar entregables.

### 20.3 Prioridades de tareas

| Nivel | Valor | Color | Descripción |
|---|---|---|---|
| Baja | 1 | Gris | Puede esperar; no impacta el cronograma crítico |
| Normal | 2 | Azul | Tarea estándar del proyecto |
| Alta | 3 | Naranja | Requiere atención prioritaria esta semana |
| Urgente | 4 | Rojo | Requiere atención inmediata; puede impactar el proyecto |

### 20.4 Tipos de actividades y sus modos de medición

| Tipo | Código | Unidades típicas | Modo de medición en tarea | Cómo se registra avance |
|---|---|---|---|---|
| Mano de obra | `labor` | horas, h | Timesheet (horas) | Cronómetro o timesheet manual |
| Material | `material` | m³, ml, kg, un, ton | Cantidad (unidades físicas) | Edición inline de cantidad registrada |
| Equipo | `equipment` | días, horas | Cantidad o timesheet | Según configuración de la actividad |
| Subcontrato | `subcontract` | variable | Cantidad o porcentaje | Según configuración de la actividad |
| Hito | (especial) | — | Hito (binario) | Checkbox de completado |

---

## 23. Preguntas Frecuentes (FAQ)

### General

**¿Cuántos proyectos puedo tener activos simultáneamente?**

No hay un límite en el número de proyectos activos. Sin embargo, el plan de su empresa puede tener límites en el número de usuarios y de datos almacenados. Consulte con el administrador de su empresa o con ValMen Tech.

**¿Puedo acceder a Saicloud desde el celular?**

Sí. Saicloud es una aplicación web responsiva. Funciona en navegadores móviles modernos (Chrome, Safari). Sin embargo, para funciones avanzadas como el Gantt, la pantalla de Analytics y las vistas de scheduling, se recomienda usar un computador con pantalla de al menos 1280px.

**¿Los datos se guardan automáticamente?**

Los formularios de creación y edición se guardan solo cuando hace clic en el botón **Guardar**. No hay guardado automático en formularios. Sin embargo, los timesheets registrados con el Timer se guardan automáticamente cuando detiene el cronómetro.

**¿Qué pasa si dos personas editan la misma tarea al mismo tiempo?**

El sistema aplica validación optimista: el último en guardar gana. Si dos personas editan simultáneamente, puede haber pérdida de cambios del primero en guardar. En proyectos con equipos grandes, coordine para evitar ediciones simultáneas de la misma tarea.

---

### Proyectos y Fases

**¿Puedo mover una tarea de una fase a otra?**

Sí. Edite la tarea y cambie el campo **Fase** a la fase destino. Las dependencias de la tarea se mantienen; solo cambia su agrupación.

**¿El avance de la fase se calcula automáticamente?**

Sí. El porcentaje de avance de una fase es el promedio del avance de todas sus tareas. No se puede editar manualmente. Si el cálculo parece incorrecto, revise que el estado y porcentaje de completado de las tareas estén actualizados.

**¿Puedo archivar un proyecto sin eliminarlo?**

No existe una función de "archivar" como tal. Para ocultar un proyecto del listado principal, cámbielo al estado **Cerrado** o **Cancelado**. Use los filtros de estado para excluirlos de la vista principal.

**¿Se puede duplicar un proyecto?**

Esta funcionalidad no está disponible en la versión actual. Para crear un proyecto similar, créelo manualmente basándose en el anterior como referencia.

---

### Tareas y Timesheets

**¿Puedo registrar tiempo en una tarea que no me está asignada?**

Depende de la configuración de permisos de su empresa. Por defecto, cualquier usuario del proyecto puede registrar timesheets en cualquier tarea del proyecto. Sin embargo, el administrador puede restringir esto a solo el responsable asignado.

**¿Las horas del Timer se suman automáticamente a las horas estimadas?**

No. Las horas estimadas son el plan; los timesheets registrados son la realidad ejecutada. Se muestran de forma separada para comparar estimado vs real. Las horas del Timer se guardan como timesheets (horas reales registradas) y no modifican las horas estimadas.

**¿Puedo registrar tiempo fraccionado (30 minutos, 45 minutos)?**

Sí. El campo de horas acepta decimales. Ejemplos: 0.5 = 30 minutos; 0.75 = 45 minutos; 1.5 = 1 hora 30 minutos. El Timer convierte automáticamente los segundos a horas decimales al guardar.

**¿Qué pasa con las tareas recurrentes?**

Cuando crea una tarea con la opción "Es recurrente" activada, el sistema genera automáticamente una copia de la tarea con la frecuencia indicada (diaria, semanal, mensual). La nueva instancia se crea con estado "Por hacer" en la fecha de próxima generación.

---

### Recursos y Asignaciones

**¿Cuál es la diferencia entre "Responsable" de una tarea y un "Recurso asignado"?**

- El **Responsable** es el usuario principalmente responsable de que la tarea se complete. Recibe notificaciones y aparece en los reportes como el dueño de la tarea.
- Un **Recurso asignado** es cualquier persona que trabaja en la tarea, con un porcentaje de tiempo y rango de fechas definidos. Puede haber múltiples recursos asignados a una tarea, pero solo un responsable.

**¿Qué pasa si asigno a un recurso sin definir su capacidad?**

Si el recurso no tiene capacidad definida, el sistema usa un valor por defecto de 40 horas/semana para los cálculos de sobreasignación. Defina la capacidad real del recurso para cálculos precisos.

**¿Puedo asignar un recurso externo (no usuario de Saicloud) a una tarea?**

No directamente. Para subcontratistas o consultores externos, cree el tercero correspondiente en el módulo de Terceros y asócielo a las tareas en el campo **Cliente** de la tarea (si aplica). Para el seguimiento de tiempo de externos, un usuario administrador puede crear un registro de usuario con rol limitado.

---

### Scheduling y Gantt

**¿El Auto-Schedule borra las fechas que puse manualmente?**

Sí, para las tareas que no tienen restricciones de fecha. Si tiene tareas con fechas fijas (compromisos contractuales, hitos inmovibles), cree una restricción `MUST_START_ON` o `MUST_FINISH_ON` antes de ejecutar el Auto-Schedule. Esas tareas no serán modificadas.

**¿Qué ocurre si el Auto-Schedule genera una fecha de fin posterior al contrato?**

El Auto-Schedule respeta las dependencias y restricciones, pero no puede "comprimir" el cronograma si matemáticamente es imposible terminarlo antes. En ese caso revise:
1. Las dependencias: ¿hay alguna que no sea estrictamente necesaria?
2. Las duraciones: ¿son realistas o están sobreestimadas?
3. Los recursos: ¿agregar más recursos a tareas críticas podría reducir duración?
4. La ejecución en paralelo: ¿hay tareas que podrían hacerse en simultáneo?

**¿Puedo tener múltiples baselines activas al mismo tiempo?**

No. Solo una baseline puede ser la activa en un momento dado. Esta es la que se muestra en el overlay del Gantt. Sin embargo, puede tener múltiples baselines creadas y comparar cualquiera de ellas contra el plan actual.

---

### Presupuesto y EVM

**¿El EVM funciona si no tengo un presupuesto aprobado?**

No. El EVM requiere un `BAC` (presupuesto aprobado) para calcular todos los índices. Sin presupuesto aprobado, el módulo EVM mostrará advertencias indicando que no hay datos suficientes.

**¿Las métricas EVM se calculan en tiempo real?**

Las métricas EVM se recalculan cada vez que accede al dashboard de presupuesto. No hay un proceso nocturno; los cambios en timesheets y gastos se reflejan inmediatamente en los indicadores.

**¿Puedo exportar el dashboard EVM?**

Sí. En el dashboard de presupuesto, use el botón **Exportar** para descargar un archivo Excel con todas las métricas EVM en la fecha actual.

**¿El CPI puede ser mayor que 2?**

Técnicamente sí, especialmente al inicio del proyecto cuando el AC es muy bajo. Un CPI de 2 al inicio significa que por cada peso gastado se ha ganado el doble en valor. Sin embargo, en proyectos maduros (>50% de avance), un CPI muy alto puede indicar que el presupuesto fue sobreestimado significativamente.

---

## 24. Atajos y Tips de Productividad

### 22.1 Flujo diario recomendado para un profesional

Si usa Saicloud como parte de su rutina diaria de trabajo, este flujo de 10 minutos por la mañana y 5 minutos al final del día le ayudará a mantener los datos al día:

**Al iniciar el día (10 minutos):**
1. Ingrese a Saicloud.
2. Revise la sección **Mis tareas** en el sidebar: ¿hay tareas vencidas? ¿Hay tareas con fecha límite hoy?
3. Abra la primera tarea en la que trabajará.
4. Inicie el **Timer**.

**Durante el día:**
5. Si cambia de tarea, detenga el Timer, guarde el timesheet y abra la nueva tarea para iniciar un nuevo Timer.
6. Cuando complete una tarea, cambie su estado a **Completada**.
7. Si encuentra un impedimento, cambie el estado a **Bloqueada** y deje una nota en la descripción explicando el bloqueo.

**Al terminar el día (5 minutos):**
8. Detenga el Timer si está corriendo.
9. Revise que todos los timesheets del día estén registrados.
10. Actualice el estado de las tareas trabajadas.

### 22.2 Tips para gerentes de proyecto

**Revisión semanal de 30 minutos:**
1. Abrir el proyecto → tab Analytics → revisar Burn Down y KPIs (5 min).
2. Tab Gantt → activar overlay de Ruta Crítica → revisar tareas rojas (10 min).
3. Tab Presupuesto → revisar alerta de presupuesto y EVM (5 min).
4. Tab Recursos → revisar sobreasignaciones (5 min).
5. Actualizar al equipo sobre ajustes necesarios (5 min).

**Antes de cada reunión de seguimiento:**
- Exporte el reporte de Analytics a Excel.
- Tome una captura del Gantt con el overlay de baseline activo.
- Revise el estado financiero (EVM) para tener datos concretos de avance y costo.

### 22.3 Tips para el administrador de la empresa

**Configuración inicial de una empresa nueva:**

1. Crear todos los usuarios con los roles correctos.
2. Definir las actividades del catálogo más usadas por la empresa (mínimo 10-15).
3. Crear los terceros (clientes principales).
4. Capacitar al equipo con este manual antes de crear el primer proyecto real.
5. Crear un proyecto de prueba para que el equipo practique sin afectar datos reales.

**Mantenimiento mensual:**
- Revisar usuarios inactivos y desactivarlos.
- Revisar tarifas de recursos: ¿hubo ajustes salariales?
- Revisar el catálogo de actividades: ¿hay actividades duplicadas o mal nombradas?
- Exportar reportes ejecutivos para la gerencia.

### 22.4 Teclas de acceso rápido

| Atajo | Función |
|---|---|
| `Esc` | Cerrar cualquier diálogo o panel lateral |
| `Ctrl + S` | Guardar el formulario activo |
| `Ctrl + /` | Abrir búsqueda global de proyectos y tareas |
| `Ctrl + Z` | Deshacer cambio en formulario (antes de guardar) |
| Clic en el logo | Ir al Dashboard principal |
| Doble clic en tarea (Kanban) | Abrir el detalle completo de la tarea |

---

## 25. Integración con Saiopen

### 23.1 Qué es la integración con Saiopen

Saiopen es el ERP Windows de Grupo SAI S.A.S. La integración entre Saicloud y Saiopen permite que los datos se sincronicen bidireccionalmente para eliminar la doble digitación.

Datos que pueden sincronizarse:
- **De Saiopen a Saicloud:** terceros (clientes, proveedores), actividades del catálogo, proyectos base.
- **De Saicloud a Saiopen:** avance de tareas, horas registradas, costos ejecutados.

### 23.2 Indicadores de sincronización

En el detalle de un proyecto, puede ver si el proyecto está sincronizado con Saiopen:

| Indicador | Descripción |
|---|---|
| Chip verde "Sincronizado" | El proyecto tiene un ID en Saiopen y los datos están actualizados |
| Chip amarillo "Pendiente" | Hay datos que aún no se han sincronizado |
| Chip gris "No sincronizado" | El proyecto no está vinculado a Saiopen |

### 23.3 Sincronización manual

Si necesita forzar una sincronización:

1. En el detalle del proyecto, haga clic en el menú de tres puntos (⋮).
2. Seleccione **Sincronizar con Saiopen**.
3. Espere a que el proceso complete (puede tardar hasta 30 segundos dependiendo del volumen de datos).
4. El campo "Última sincronización" se actualizará con la fecha y hora.

> **Nota:** La sincronización automática ocurre cada 15 minutos. La sincronización manual es útil cuando necesita los datos actualizados de inmediato (antes de una reunión, antes de facturar, etc.).

### 23.4 Campos sincronizados por módulo

| Módulo | Campos sincronizados |
|---|---|
| Proyectos | Código Saiopen, nombre, estado, fechas, cliente |
| Actividades | ID Saiopen, nombre, unidad, costo unitario |
| Terceros | NIT, nombre, tipo, contacto |
| Timesheets | Horas, fecha, usuario, tarea (para costeo en Saiopen) |

---

## 26. Seguridad y Privacidad

### 24.1 Gestión de contraseñas

- Use una contraseña única para Saicloud. No reutilice contraseñas de otras plataformas.
- Cambie su contraseña al menos cada 90 días, o inmediatamente si sospecha que fue comprometida.
- Para cambiar la contraseña: Mi perfil → Seguridad → Cambiar contraseña.

### 24.2 Sesiones activas

Puede ver las sesiones activas de su cuenta:
1. Mi perfil → Seguridad → Sesiones activas.
2. Se muestra una tabla con: dispositivo, ubicación aproximada, fecha de último acceso.
3. Si ve una sesión que no reconoce, haga clic en **Cerrar sesión** de esa sesión inmediatamente y contacte al administrador.

### 24.3 Multi-tenant y aislamiento de datos

Saicloud es multi-tenant. Esto garantiza que:
- Los datos de su empresa solo son accesibles por usuarios de su empresa.
- Ningún usuario de otra empresa puede ver sus proyectos, tareas o timesheets.
- El equipo de soporte de ValMen Tech (`valmen_support`) solo tiene acceso de lectura y con registro de auditoría.

### 24.4 Auditoría de cambios

El sistema registra automáticamente:
- Quién creó o modificó cada proyecto, tarea y timesheet.
- Fecha y hora de cada cambio.
- Los cambios en presupuestos y aprobaciones de gastos.

El administrador de la empresa puede solicitar reportes de auditoría a través de soporte@valmentech.com.

---

## 27. Glosario Extendido — Siglas y Abreviaciones

| Sigla | Significado | Contexto |
|---|---|---|
| AIU | Administración, Imprevistos y Utilidad | Proyectos de obra civil en Colombia |
| ALAP | As Late As Possible (Tan tarde como sea posible) | Scheduling de tareas |
| ASAP | As Soon As Possible (Tan pronto como sea posible) | Scheduling de tareas |
| AC | Actual Cost (Costo Actual) | EVM |
| BAC | Budget at Completion (Presupuesto total) | EVM |
| CPI | Cost Performance Index (Índice de desempeño de costo) | EVM |
| CPM | Critical Path Method (Método de ruta crítica) | Scheduling |
| CV | Cost Variance (Variación de costo) | EVM |
| EAC | Estimate at Completion (Estimación al cierre) | EVM |
| ETC | Estimate to Complete (Estimación para concluir) | EVM |
| EV | Earned Value (Valor Ganado) | EVM |
| EVM | Earned Value Management | Metodología de control |
| FF | Finish to Finish (Fin a Fin) | Dependencias |
| FNET | Finish No Earlier Than (No terminar antes de) | Restricciones de scheduling |
| FNLT | Finish No Later Than (No terminar después de) | Restricciones de scheduling |
| FS | Finish to Start (Fin a Inicio) | Dependencias |
| KPI | Key Performance Indicator | Analytics |
| MFO | Must Finish On (Debe terminar en) | Restricciones de scheduling |
| MSO | Must Start On (Debe iniciar en) | Restricciones de scheduling |
| NIT | Número de Identificación Tributaria | Terceros en Colombia |
| PV | Planned Value (Valor Planificado) | EVM |
| SaaS | Software as a Service (Software como Servicio) | Modelo de entrega |
| SF | Start to Finish (Inicio a Fin) | Dependencias |
| SNET | Start No Earlier Than (No empezar antes de) | Restricciones de scheduling |
| SNLT | Start No Later Than (No empezar después de) | Restricciones de scheduling |
| SPI | Schedule Performance Index (Índice de desempeño de cronograma) | EVM |
| SS | Start to Start (Inicio a Inicio) | Dependencias |
| SV | Schedule Variance (Variación de cronograma) | EVM |
| TCPI | To-Complete Performance Index | EVM |
| VAC | Variance at Completion (Variación al cierre) | EVM |

---

---

## 28. Contacto y Soporte

| Canal | Detalle |
|---|---|
| Correo de soporte técnico | soporte@valmentech.com |
| Tiempo de respuesta estándar | 24 horas hábiles |
| Tiempo de respuesta urgente (sistema caído) | 4 horas |
| Documentación en línea | Disponible en la plataforma (ícono de ayuda ?) |
| Actualizaciones y mantenimiento | Notificadas con 48 horas de anticipación por correo |

Para reportar un error:
1. Capture una captura de pantalla del error.
2. Anote: qué estaba haciendo, qué esperaba que pasara, qué pasó en cambio.
3. Envíe esa información a soporte@valmentech.com con el asunto "Error Saicloud — [descripción breve]".

---

*Manual elaborado por ValMen Tech — SaiSuite v1.0 — Marzo 2026*
*Para soporte técnico: soporte@valmentech.com*
