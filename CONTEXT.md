# CONTEXT.md — Estado Actual del Proyecto
# SaiSuite | ValMen Tech
#
# INSTRUCCIONES PARA CLAUDE:
# - Leer este archivo al inicio de CADA sesión de desarrollo.
# - Actualizarlo al FINAL de cada sesión con lo que se hizo y el estado actual.

---

## Estado general

| Campo | Valor |
|---|---|
| Fase actual | Fase 0 — Pre-desarrollo completada |
| Estado | ⏳ En espera de aprobación del partnership con Saiopen |
| Última sesión | 9 Marzo 2026 |
| Próximo paso | Confirmar módulos con Saiopen → arrancar Semana 1 |

---

## Qué está listo

### Documentación (100% completa)
- ✅ Propuesta ejecutiva PPTX enviada a Saiopen
- ✅ Modelo de costos Excel
- ✅ `docs/Infraestructura_SaiSuite_v2.docx`
- ✅ `docs/Estandares_Codigo_SaiSuite_v1.docx`
- ✅ `docs/Esquema_BD_SaiSuite_v1.docx`
- ✅ `docs/Flujo_Feature_SaiSuite_v1.docx`
- ✅ `docs/AWS_Setup_SaiSuite_v1.docx`
- ✅ `CLAUDE.md`, `ERRORS.md`, `DECISIONS.md`, `CONTEXT.md`

### Repositorio y código base
- ✅ Repositorio GitHub privado creado
- ✅ Estructura de carpetas completa (backend, frontend, agent, n8n, docs)
- ✅ `apps/core/` — BaseModel, CompanyMiddleware, paginación, excepciones
- ✅ `apps/companies/` — modelos Company y CompanyModule
- ✅ `apps/users/` — modelo User con email como login y roles definidos
- ✅ Migraciones creadas y aplicadas en PostgreSQL
- ✅ Angular 18 inicializado con `.claude/` (reglas Angular para Claude Code)

### Infraestructura local (Docker)
- ✅ PostgreSQL 16 → localhost:5432
- ✅ Django API → localhost:8000 (health check responde OK)
- ✅ Angular → localhost:4200
- ✅ n8n → localhost:5678

### Infraestructura AWS
- ❌ No montada — esperando confirmación del partnership

---

## Módulos del producto

| Módulo | Estado |
|---|---|
| SaiVentas | ⏳ Por confirmar con Saiopen |
| SaiCobros | ⏳ Por confirmar con Saiopen |
| SaiDashboard | ⏳ Por confirmar con Saiopen |

---

## Decisiones pendientes

- [ ] Dominio definitivo (placeholder: `saisuite.co`)
- [ ] Módulos exactos confirmados con Saiopen
- [ ] Convención snake_case → camelCase entre Django y Angular (definir antes del primer endpoint)

---

## Errores resueltos durante el setup (ver ERRORS.md para detalle)

1. `AUTH_USER_MODEL` sin modelo User creado → crear Company antes que User
2. `urls.py` con ruta de subpaquete inexistente (`apps.users.urls.auth`)
3. `urlpatterns` vacío / archivo con solo comentario → siempre `urlpatterns = []`
4. Falta carpeta `migrations/` en las apps → siempre crearla con `__init__.py`

---

## Último trabajo realizado

**Sesión 9 Marzo 2026:**
- Generados los 4 archivos de contexto: CLAUDE.md, ERRORS.md, DECISIONS.md, CONTEXT.md
- Creado repositorio GitHub con estructura completa del proyecto
- Resueltos 4 errores de configuración durante el setup inicial de Docker
- Levantados los 4 servicios correctamente (PostgreSQL, Django, Angular, n8n)
- Migraciones aplicadas — base de datos lista con modelos Company y User
- Angular 18 inicializado con soporte nativo para Claude Code (.claude/)
- Documentos técnicos .docx copiados a docs/

**Sesión 11 Marzo 2026:**
- Decidido framework UI frontend: PrimeNG con preset Aura customizado (DEC-007)
- Instalado: npm install primeng @primeuix/themes primeicons
- Configurado SaicloudPreset con paleta de azules corporativos en app.config.ts
- Dark mode configurado via clase .app-dark en <html>, gestionado por ThemeService
- CLAUDE.md actualizado: sección PrimeNG integrada dentro de ### Frontend Angular
- DECISIONS.md actualizado: DEC-007 agregado con formato estándar del archivo
- Notion actualizado: DEC-007 creada, checkboxes de Local y GitHub marcados como completados
- Validación completa del repo: estructura, BaseModel, docker-compose y settings confirmados correctos
- ⚠️ Pendiente: recibir HEX corporativos de ValMen Tech para reemplazar tokens {blue.X} en app.config.ts

**Próxima sesión debe:**
- Esperar confirmación de Saiopen
- Al confirmar: definir módulos exactos y ajustar Esquema_BD si es necesario
- Al recibir HEX corporativos: actualizar SaicloudPreset en app.config.ts
- Arrancar Semana 1: configurar MFA + IAM AWS → montar staging → primera feature

---

## Últimos cambios (2026-03-14)
- ✅ DECISIONS.md estandarizado a formato DEC-XXX
- ✅ 10 decisiones migradas y numeradas
- ✅ Índice agregado al inicio
- ✅ Template para nuevas decisiones al final
- ⏳ Pendiente: Sincronizar con Notion

---

## Estadísticas del proyecto
- Archivos modificados hoy: 6
- Decisiones documentadas: 10
- Features planeados: 0
- Última actualización: 2026-03-14 18:08:48
