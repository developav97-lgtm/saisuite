# GUÍA DE USUARIO — SaiSuite v2.0
**ValMen Tech | Saicloud**
**Actualizado:** 27 Marzo 2026

---

## NAVEGACIÓN GENERAL

### Landing post-login — Selector de Módulos
Al ingresar al sistema, verás una pantalla con todos los módulos disponibles:

```
┌─────────────────────────────────────────────────┐
│  ⬡ Saicloud                                      │
│  Selecciona el módulo con el que deseas trabajar │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐              │
│  │ 🔧 Gestión   │  │ 👥 Terceros  │              │
│  │ de Proyectos │  │              │              │
│  └──────────────┘  └──────────────┘              │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐              │
│  │ 🛒 SaiVentas │  │ 💳 SaiCobros │              │
│  │ Próximamente │  │ Próximamente │              │
│  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────┘
```

- **Módulos activos** — clic directo para entrar
- **Próximamente** — módulos en desarrollo (no clickeables)

### Sidebar contextual
El menú lateral cambia según el módulo donde estés:

| Módulo activo | Qué muestra el sidebar |
|---|---|
| `/dashboard` | Todos los módulos disponibles |
| `/proyectos/**` | Nav de Proyectos: Proyectos, Actividades, Tareas, Configuración |
| `/admin/**` | Nav de Admin: Usuarios, Empresa, Módulos, Consecutivos |
| `/terceros/**` | Nav de Terceros: Listado |

Siempre hay un botón **"Módulos"** (con ícono `apps`) para volver al selector.

---

## MÓDULO: GESTIÓN DE PROYECTOS

### Vista Lista de Proyectos (`/proyectos`)
- Tabla con columnas: Código, Nombre, Tipo, Estado, Cliente, Gerente, Fecha fin, Presupuesto
- **Filtros:** Buscar por texto + Estado + Tipo — en una sola línea
- **Botón "Cards"** en el header para cambiar a vista de tarjetas
- **Botón "Nuevo proyecto"** para crear

### Vista Cards de Proyectos (`/proyectos/cards`)
Mismos filtros que la vista lista. Cada tarjeta muestra:
- Código y badge de estado
- Nombre del proyecto
- Tipo de proyecto
- **Barra de progreso** con % de avance
- Gerente, Cliente, Fecha fin planificada, Presupuesto
- Botón "Ver detalle"

Usa el botón **"Lista"** para volver a la tabla.

### Detalle de Proyecto
El detalle tiene las siguientes tabs:

| Tab | Contenido |
|---|---|
| **General** | Datos completos + cambio de estado + financiero |
| **Fases** | Lista de fases con activar/desactivar |
| **Tareas** | Lista de tareas del proyecto |
| **Terceros** | Stakeholders asignados |
| **Documentos** | Documentos contables |
| **Hitos** | Hitos facturables |
| **Actividades** | Actividades del proyecto (del catálogo Saiopen) |
| **Gantt** | Vista de diagrama de Gantt |

### Estados de Proyecto
```
Borrador → Planificado → En ejecución → Suspendido → Cerrado
                      ↘ Cancelado
```

---

## MÓDULO: TAREAS

### Una entrada, dos vistas
El sidebar tiene **una sola entrada "Tareas"** que recuerda tu última vista:
- Si usaste la lista, te lleva a la lista
- Si usaste el Kanban, te lleva al Kanban

La preferencia se guarda automáticamente en tu navegador.

### Vista Lista (`/proyectos/tareas`)
- Tabla con todas las tareas de la empresa
- Filtros: buscar, estado, prioridad, proyecto
- Botón **"Kanban"** en el header para cambiar de vista

### Vista Kanban (`/proyectos/tareas/kanban`)
- Columnas: Por Hacer → En Progreso → En Revisión → Bloqueada → Completada
- Drag & drop entre columnas
- Filtros: buscar, proyecto, fase, responsable, prioridad
- Clic en tarjeta → popup con detalle rápido
- Botón **"Lista"** en el header para cambiar de vista

### Detalle de Tarea
Según la configuración de la actividad asociada, la tarea puede mostrar:
- **Solo estados:** selector de estado sin medición de tiempo
- **Cronómetro:** para actividades medidas en horas
- **Cantidad:** campo de avance numérico (m³, días, toneladas, etc.)

---

## MODO OSCURO

Usa el ícono de luna/sol en la barra superior (`topbar`) para alternar entre modo claro y oscuro. La preferencia se guarda automáticamente.

---

## ACCESOS RÁPIDOS

| Acción | Cómo |
|---|---|
| Ir al selector de módulos | Clic en "Módulos" en el sidebar |
| Crear proyecto | `/proyectos` → "Nuevo proyecto" |
| Crear tarea | `/proyectos/tareas` → "Nueva tarea" |
| Ver Gantt de un proyecto | Detalle proyecto → Tab "Gantt" |
| Cambiar estado de proyecto | Detalle proyecto → Tab "General" → botones de estado |
| Ver todas las actividades | `/proyectos/actividades` |
| Configurar módulo | `/proyectos/configuracion` |
