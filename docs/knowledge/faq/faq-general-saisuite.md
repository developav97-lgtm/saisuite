---
title: FAQ General — SaiSuite
module: general
category: faq
---

# Preguntas Frecuentes — SaiSuite

## Sobre SaiSuite

### ¿Qué es SaiSuite?
SaiSuite es una plataforma SaaS (Software como Servicio) que te permite acceder a los datos de tu sistema Saiopen (ERP de Grupo SAI S.A.S) desde cualquier lugar con conexión a internet. Incluye módulos de gestión de proyectos, terceros, contabilidad y dashboards analíticos.

### ¿Qué datos sincroniza SaiSuite desde Saiopen?
SaiSuite sincroniza automáticamente:
- Movimientos contables (diario, acumulado)
- Clientes, proveedores y terceros
- Facturas de venta y compra
- Inventarios
- Recibos de caja y órdenes de pago

La sincronización ocurre en tiempo real cuando el agente de Windows está activo, o en lotes cuando se reconecta.

### ¿Con qué frecuencia se sincronizan los datos?
Depende de la configuración del agente:
- **En tiempo real:** Cambios se envían inmediatamente al realizarse en Saiopen
- **Por intervalos:** El agente envía los cambios cada X minutos (configurable)
- Los datos en SaiSuite pueden tener un retraso de 1-5 minutos en condiciones normales

---

## Módulo Dashboard (SaiDashboard)

### ¿Qué datos muestra el dashboard?
El dashboard muestra indicadores financieros basados en los movimientos contables de Saiopen:
- Ingresos vs Egresos del período seleccionado
- Estado de resultados resumido
- Balance general (activos, pasivos, patrimonio)
- Flujo de caja operacional
- Rotación de cartera y proveedores
- Top clientes y proveedores por movimiento

### ¿Cómo filtro por período en el dashboard?
En el panel de filtros puedes seleccionar:
- **Fecha desde / hasta:** Para un rango específico
- **Período:** Un mes específico en formato YYYY-MM (ej: 2024-01)
- **Año:** Para ver el año completo
- **Ver por mes:** Activa la vista mensual con 12 barras de datos comparativos

### ¿Puedo guardar los filtros para que se carguen automáticamente?
Sí. Después de configurar los filtros deseados, aparecerá el botón "Guardar como predeterminado". Los filtros guardados se cargarán automáticamente la próxima vez que abras ese dashboard.

### ¿Qué es una tarjeta personalizada?
Las tarjetas personalizadas te permiten crear indicadores específicos de tu negocio:
- **Rango de cuentas personalizado:** Muestra el saldo de un rango de cuentas PUC que definas
- **Distribución por proyecto:** Desglosa cualquier cuenta por proyecto

---

## Módulo Proyectos (SaiProyectos)

### ¿Cómo creo un proyecto nuevo?
1. Ve al módulo SaiProyectos
2. Haz clic en el botón "Nuevo Proyecto"
3. Completa el formulario: código, nombre, tipo, fechas y presupuesto
4. Asigna un gerente de proyecto
5. Guarda. El proyecto queda en estado "Planificación"

### ¿Cuáles son los estados de un proyecto?
- **Planificación:** Proyecto en definición, aún no iniciado
- **En progreso:** Proyecto activo con trabajo en curso
- **En pausa:** Proyecto temporalmente detenido
- **Completado:** Proyecto finalizado exitosamente
- **Cancelado:** Proyecto terminado sin completar

### ¿Qué tipos de proyecto existen?
- **Servicios:** Proyectos de prestación de servicios profesionales
- **Obra civil:** Construcción e infraestructura
- **Software:** Desarrollo de sistemas y aplicaciones
- **Consultoría:** Proyectos de asesoría y consultoría
- **Distribución:** Proyectos de distribución de productos

### ¿Cómo se registran las horas en un proyecto?
Las horas se registran desde el módulo de tareas. Cada tarea tiene un campo de "Horas estimadas" y "Horas registradas". El avance real del proyecto se calcula automáticamente comparando horas registradas vs estimadas.

### ¿Qué son los hitos del proyecto?
Los hitos son puntos de control importantes en el cronograma del proyecto. Pueden estar asociados a facturación, lo que permite generar alertas cuando un hito está próximo a vencer.

---

## Módulo Terceros (SaiTerceros)

### ¿Cuál es la diferencia entre un tercero Saiopen y un tercero SaiCloud?
- **Tercero Saiopen:** Importado automáticamente desde Saiopen (proveedores y clientes del ERP)
- **Tercero SaiCloud:** Creado directamente en SaiSuite (puede ser un cliente que no existe aún en Saiopen)

### ¿Cómo busco un tercero?
En la lista de terceros puedes buscar por:
- Nombre o razón social
- NIT o número de identificación
- Código interno
- Tipo (cliente, proveedor, empleado, etc.)

### ¿Qué información tiene cada tercero?
- Datos de identificación: NIT, nombre, tipo de persona
- Información de contacto: dirección, teléfono, email
- Clasificación: tipo de tercero, régimen tributario
- Historial de movimientos vinculados

---

## Módulo Contabilidad (SaiContabilidad)

### ¿Puedo ver el balance general en SaiSuite?
Sí. El módulo de contabilidad muestra el balance de prueba con todos los movimientos acumulados por cuenta. Puedes filtrar por período y ver el saldo de cada cuenta del PUC.

### ¿Los datos contables son en tiempo real?
Los datos provienen de Saiopen a través del agente de sincronización. Los movimientos registrados en Saiopen aparecerán en SaiSuite según la frecuencia de sincronización configurada (generalmente 1-5 minutos).

### ¿Puedo exportar los datos contables?
Sí, la mayoría de los reportes contables pueden exportarse a Excel o PDF desde el módulo correspondiente.

---

## Chat con IA (SaiBot)

### ¿Qué puede hacer el asistente de IA?
El asistente de IA puede:
- Responder preguntas sobre el estado financiero de tu empresa
- Mostrar resúmenes de proyectos activos
- Consultar información de terceros
- Explicar normas contables colombianas (PUC, NIIF, IVA, retenciones)
- Ayudarte a navegar las funcionalidades de SaiSuite

### ¿El asistente tiene acceso a mis datos privados?
El asistente solo accede a los datos de tu empresa (multi-tenant). Los datos de otras empresas nunca son accesibles. Además, el asistente no puede realizar modificaciones, solo consultas de lectura.

### ¿Cómo formulo una buena pregunta al asistente?
Sé específico con el contexto. Por ejemplo:
- "¿Cuáles son mis ingresos del mes de enero 2024?"
- "Muéstrame el saldo de la cuenta 1305 Clientes"
- "¿Cuántos proyectos activos tengo en el estado 'en progreso'?"
- "¿Cuál es la tarifa de retención en la fuente para servicios?"

### ¿Qué hago si el asistente da una respuesta incorrecta?
Puedes usar los botones de pulgar arriba/abajo para calificar la respuesta. Tu feedback ayuda a mejorar el sistema. Si la respuesta es crítica, verifica siempre con la fuente oficial (DIAN, movimientos contables en Saiopen).

---

## Soporte y Configuración

### ¿Cómo configuro el agente de sincronización en Windows?
El agente de sincronización se instala como servicio de Windows. Para configurarlo:
1. Ejecutar el instalador como administrador
2. Ingresar las credenciales de Saiopen (servidor, base de datos, usuario)
3. Ingresar el token de empresa de SaiSuite (disponible en Ajustes > Empresa)
4. Iniciar el servicio

### ¿Qué hago si los datos no se están sincronizando?
1. Verificar que el servicio "SaiSuite Agent" esté corriendo en Windows
2. Revisar el log del agente en `C:\SaiSuite\Agent\logs\`
3. Verificar conectividad a internet
4. Verificar que el token de empresa sea válido
5. Contactar soporte si el problema persiste

### ¿Cómo agrego un nuevo usuario a mi empresa?
1. Ve a Ajustes > Usuarios
2. Haz clic en "Invitar usuario"
3. Ingresa el email del usuario
4. Selecciona el rol (Administrador, Vendedor, Cobros, Visualizador)
5. El usuario recibirá un email de activación

### ¿Qué roles de usuario existen?
- **Administrador de empresa:** Acceso completo a todos los módulos y configuración
- **Vendedor:** Acceso a SaiVentas (clientes, pedidos, productos)
- **Cobros:** Acceso a SaiCobros (cartera, gestiones de cobro)
- **Visualizador:** Solo lectura en dashboards y reportes
