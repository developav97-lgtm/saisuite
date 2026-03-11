# DECISIONS.md — Decisiones de Arquitectura
# SaiSuite | ValMen Tech
#
# INSTRUCCIONES PARA CLAUDE:
# - Leer este archivo cuando vayas a tomar una decisión de diseño significativa.
# - Si la decisión ya está aquí → respetarla, no revertirla sin consenso del equipo.
# - Si tomas una decisión nueva no cubierta → agregarla aquí antes de continuar.

---

## Por qué existe este archivo

Las decisiones de arquitectura son las más costosas de revertir. Este archivo
las documenta para que no se tomen dos veces ni se contradigan entre sesiones.

---

## Decisiones tomadas

---

### [2026-03] DECISIÓN: Estrategia multi-tenant — single database con company_id

**Contexto:** SaiSuite sirve a múltiples empresas cliente desde una sola instancia.
Había que elegir entre: (a) una BD por cliente, (b) un schema por cliente, (c) un
discriminador company_id en todas las tablas.

**Opciones consideradas:**
- BD separada por cliente: máximo aislamiento, complejidad operacional alta
- Schema por cliente (PostgreSQL): buen aislamiento, migraciones complejas
- company_id en todas las tablas: simple, escalable hasta ~500 empresas, un solo punto de backup

**Decisión:** Single database con `company_id` en todas las tablas de negocio.

**Razón:** La escala inicial (hasta 200 empresas) no justifica la complejidad de
esquemas separados. El `CompanyManager` filtra automáticamente por empresa en cada
query, minimizando el riesgo de data leak entre tenants.

**Consecuencia:** Todo modelo de negocio DEBE heredar de `BaseModel`. Nunca crear
un modelo con datos de empresa que no tenga `company_id`.

---

### [2026-03] DECISIÓN: PKs como UUID v4, no enteros autoincrementales

**Contexto:** Elegir el tipo de PK para los modelos de negocio expuestos por API.

**Opciones consideradas:**
- Entero autoincremental: simple, eficiente en índices, expone volumen del negocio
- UUID v4: sin colisiones, no expone información, compatible con sync de múltiples fuentes

**Decisión:** UUID v4 en todos los modelos expuestos por API.

**Razón:** Saiopen genera sus propios IDs (numéricos o compuestos). Si usáramos
enteros, tendríamos colisiones al sincronizar. UUID también oculta el volumen de
registros a usuarios externos.

**Consecuencia:** Todos los modelos que heredan de `BaseModel` tienen UUID como PK.
Los modelos Firebird tienen adicionalmente `sai_key` o `sai_id` para la llave original.

---

### [2026-03] DECISIÓN: Mapeo de llaves Firebird → campo sai_key con concatenación

**Contexto:** Las facturas y pedidos en Firebird tienen llaves compuestas de 4 campos:
(empresa, sucursal, tipo, numero). Django no puede usar llaves compuestas como PKs.

**Opciones consideradas:**
- Mapear cada campo por separado y usar 4 columnas de referencia
- Concatenar en un solo string con separador

**Decisión:** Concatenar como string: `"1|1|FV|100245"` en campo `sai_key`.

**Razón:** Simple de construir, de consultar y de indexar. El separador `|` no aparece
en ninguno de los campos originales de Saiopen.

**Consecuencia:** El agente debe construir `sai_key` con exactamente este formato
antes de enviar mensajes SQS. Django valida `unique_together(company, sai_key)`.

---

### [2026-03] DECISIÓN: Sessions JWT sobre PostgreSQL, sin Redis en Fase 1

**Contexto:** Necesitábamos revocación activa de tokens JWT (logout inmediato).
La solución estándar usa Redis como store de sesiones activas.

**Opciones consideradas:**
- Redis (ElastiCache): ~$15-25/mes adicionales, complejidad de setup
- PostgreSQL tabla `active_sessions`: cero costo adicional, query simple

**Decisión:** Tabla `active_sessions` en PostgreSQL con índice en `(company_id, last_seen_at)`.

**Razón:** Con <80 empresas, el COUNT de sesiones activas por empresa es <5ms con
el índice correcto. Redis se añade en Fase 2 si aparece latencia real medida.

**Consecuencia:** Logout borra el JTI de `active_sessions`. Tarea horaria limpia
sesiones con `last_seen_at` > 30 minutos de inactividad.

---

### [2026-03] DECISIÓN: n8n self-hosted en ECS, no cloud

**Contexto:** n8n tiene versión cloud ($20-50/mes) y versión self-hosted (gratis en ejecuciones).

**Opciones consideradas:**
- n8n Cloud: sin mantenimiento, límite de ejecuciones, costo mensual fijo
- n8n self-hosted en ECS: ejecuciones ilimitadas, control total, requiere gestión

**Decisión:** Self-hosted en ECS Fargate como container separado.

**Razón:** Los workflows de SaiSuite se ejecutan frecuentemente (alertas de cartera,
notificaciones, sync events). El costo por ejecución en cloud escalaría rápidamente.

**Consecuencia:** n8n no está expuesto a internet en Fase 1 — acceso via SSH tunnel.
Django se comunica con n8n via webhook interno dentro de la VPC.

---

### [2026-03] DECISIÓN: Deploy manual en Fase 1, CI/CD en Fase 2

**Contexto:** ¿Automatizar el deploy desde el inicio o hacerlo manual?

**Decisión:** Deploy manual (~8 minutos) en Fase 1. GitHub Actions + OIDC en Fase 2.

**Razón:** Setup de CI/CD toma tiempo que en Fase 1 es mejor invertir en producto.
Con <2 deploys por semana, el deploy manual es perfectamente manejable.

**Consecuencia:** Documentado en `AWS_Setup_SaiSuite_v1.docx`. Activar CI/CD cuando
haya >2 deploys por semana o cuando se incorpore un segundo desarrollador.

---

## Formato de entrada (copiar y completar)

```
### [YYYY-MM-DD] DECISIÓN: [descripción corta]

**Contexto:** Por qué se necesitaba tomar esta decisión.
**Opciones consideradas:**
- Opción A: descripción y tradeoffs
- Opción B: descripción y tradeoffs
**Decisión:** Qué se eligió.
**Razón:** Por qué se eligió esta opción sobre las otras.
**Consecuencia:** Qué implica esta decisión hacia adelante. Qué no se puede cambiar fácilmente.
```

---
### [2026-03-11] DECISIÓN: Framework UI Frontend — PrimeNG

**Contexto:** El frontend Angular necesita un framework de componentes UI para
construir las pantallas del ERP (tablas, formularios, diálogos, notificaciones).
Había que elegir entre las opciones principales del ecosistema Angular.

**Opciones consideradas:**
- Angular Material: nativo de Angular, pero personalización de tema limitada y dark mode complejo
- Bootstrap / ng-bootstrap: conocido, pero integración menos nativa con Angular CDR
- Tailwind CSS puro: flexible, pero sin componentes ERP listos (tablas, diálogos, etc.)
- PrimeNG: biblioteca rica en componentes ERP, sistema de temas propio con dark mode nativo

**Decisión:** PrimeNG con preset `Aura` customizado (`SaicloudPreset`) — paleta de
azules corporativos ValMen Tech. Dark mode via clase `.app-dark` en `<html>`.

**Razón:** PrimeNG tiene los componentes que SaiSuite necesita listos para producción
(`p-table` con paginación server-side, `p-dialog`, `p-confirmdialog`, `p-toast`).
Su sistema de temas permite personalización profunda de colores corporativos y dark mode
sin duplicar estilos.

**Consecuencia:** NUNCA usar Angular Material, Bootstrap ni Tailwind en este proyecto.
Los HEX corporativos de ValMen Tech están pendientes de recibir — hasta entonces se usan
los tokens `{blue.X}` del preset base. Al recibirlos, actualizar `app.config.ts`.