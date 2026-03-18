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
| Fase actual | Auth completada — Login/Logout/JWT + Shell integrado |
| Estado | 🟢 Activo — Desarrollo en curso |
| Última sesión | 18 Marzo 2026 |
| Próximo paso | Fase B: Terceros + Documentos + Hitos (o crear usuario de prueba y testear auth manualmente) |

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
| **SaiProyectos** | 🟢 Fase A completada — CRUD + Fases + Máquina de estados |
| SaiVentas | ⏳ Por confirmar con Saiopen |
| SaiCobros | ⏳ Por confirmar con Saiopen |
| SaiDashboard | ⏳ Por confirmar con Saiopen |

---

## Decisiones pendientes

- [ ] Dominio definitivo (placeholder: `saisuite.co`)
- [ ] Módulos exactos confirmados con Saiopen
- [x] ~~Convención snake_case → camelCase~~ → snake_case en todo (DEC-010)
- [ ] HEX corporativos ValMen Tech pendientes (para actualizar SaicloudPreset)

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

## Últimos cambios (2026-03-17) — Fase A Módulo Proyectos

### Backend `apps/proyectos/` (nuevo — completo)
- ✅ `models.py` — 5 modelos: Proyecto, Fase, TerceroProyecto, DocumentoContable, Hito
- ✅ `services.py` — ProyectoService + FaseService con máquina de estados y validación de presupuesto
- ✅ `serializers.py` — 8 serializers (list, detail, write, estado)
- ✅ `views.py` — ProyectoViewSet + FaseViewSet con endpoints nested
- ✅ `urls.py` — rutas manuales (sin drf-nested-routers)
- ✅ `filters.py` — ProyectoFilter con 7 campos filtrables
- ✅ `permissions.py` — CanAccessProyectos, CanEditProyecto
- ✅ `admin.py` — 5 admins registrados con FaseInline
- ✅ `tests/` — 54 tests pasando (services + views + serializers)
- ✅ Migraciones aplicadas

### Modificaciones backend
- ✅ `config/settings/base.py` — agregado `apps.proyectos` a LOCAL_APPS
- ✅ `config/urls.py` — agregado path `api/v1/proyectos/`
- ✅ `apps/companies/models.py` — agregado `PROYECTOS = 'proyectos', 'SaiProyectos'`

### Frontend `features/proyectos/` (nuevo — completo)
- ✅ `models/proyecto.model.ts` — tipos, interfaces, constantes ESTADO_LABELS/SEVERITY
- ✅ `models/fase.model.ts` — FaseList, FaseDetail, FaseCreate
- ✅ `models/paginated-response.model.ts` — PaginatedResponse<T>
- ✅ `services/proyecto.service.ts` — 7 métodos HTTP
- ✅ `services/fase.service.ts` — 4 métodos HTTP
- ✅ `components/proyecto-list/` — tabla lazy con filtros
- ✅ `components/proyecto-detail/` — tabs PrimeNG 20 + cambio de estado
- ✅ `components/proyecto-form/` — formulario reactivo crear/editar
- ✅ `components/fase-list/` — tabla fases con dialog add/edit
- ✅ `proyectos.routes.ts` — 4 rutas lazy
- ✅ `app.routes.ts` — proyectos lazy bajo ShellComponent
- ✅ `sidebar.component.ts` — enlace "Proyectos" con ícono briefcase

### Decisiones tomadas
- DEC-010: snake_case en toda la API y TypeScript (sin capa de transformación)

### Errores resueltos (ver ERRORS.md)
7 errores nuevos documentados: urls.py inexistente, User.all_objects, float/Decimal,
codigo requerido, multi-tenant DRF/JWT, PrimeNG 21 imports, TS7053 strict mode

### Build Angular
- ✅ `ng build --configuration=development` pasa sin errores (solo warnings opcionales)
- PrimeNG downgradeado de 21.1.3 → 20.5.0-lts (compatibilidad Angular 20.3.x)

---

## Últimos cambios (2026-03-18) — Auth Layer

### Backend `apps/users/` (implementado)
- ✅ `serializers.py` — CompanySummarySerializer, UserMeSerializer, LoginSerializer, LogoutSerializer
- ✅ `services.py` — AuthService: login / logout / refresh con blacklist
- ✅ `views.py` — LoginView, LogoutView, RefreshView, MeView
- ✅ `urls.py` — 4 endpoints en `/api/v1/auth/`
- ✅ `admin.py` — UserAdmin registrado
- ✅ `tests/test_auth.py` — 10/10 tests pasando

### Frontend `core/auth/` (nuevo)
- ✅ `auth.models.ts` — CompanySummary, UserProfile, LoginRequest, LoginResponse, TokenRefreshResponse
- ✅ `auth.service.ts` — signals currentUser + isAuthenticated, login/logout/refresh, localStorage
- ✅ `auth.interceptor.ts` — 401 handling con token refresh y BehaviorSubject para serializar concurrent requests
- ✅ `guards/auth.guard.ts` — CanActivateFn, redirige a /auth/login si no autenticado

### Frontend modificados
- ✅ `login.component.ts/html/scss` — form reactivo completo con Angular Material, MatSnackBar de error
- ✅ `topbar.component.ts` — inject() pattern, expone currentUser + logout
- ✅ `topbar.component.html` — nombre real del usuario, botón logout
- ✅ `app.routes.ts` — canActivate: [authGuard] activo, fallback → /auth/login

### Tests
- Backend: 10/10 pasando (todos los escenarios auth cubiertos)
- Build Angular: ✅ 0 errores, 0 warnings TS (solo budget 614kB pre-existente)

---

## Últimos cambios (2026-03-18 tarde) — Migración PrimeNG → Angular Material

### Razón
PrimeNG 18 usa `ɵɵInputTransformsFeature` (eliminado en Angular 20). 80+ archivos afectados.
El script postinstall de parche fallaba en Docker build. Decisión: migrar a Angular Material (DEC-011).

### Cambios
- ✅ `package.json` — `primeng/primeicons/@primeuix` eliminados, `@angular/material + @angular/cdk` instalados
- ✅ `styles.scss` — tema Material M3, `--sc-*` CSS vars, status chips, snackbar colors
- ✅ `app.config.ts` — removidos providers PrimeNG (MessageService, ConfirmationService)
- ✅ `theme.service.ts` — clase `dark-theme` en `<body>` (antes era `app-dark` en `<html>`)
- ✅ `sidebar.component` — CSS-based mobile drawer (reemplaza `p-drawer`)
- ✅ `topbar.component` — mat-button, mat-icon
- ✅ `login.component` — MatFormField, MatInput, MatSnackBar, password toggle con mat-icon-button
- ✅ `proyecto-list.component` — mat-table, MatPaginator (PageEvent), MatDialog para confirms
- ✅ `proyecto-detail.component` — MatTabsModule, MatSpinner, status chips CSS
- ✅ `proyecto-form.component` — MatDatepicker + MatNativeDateModule, MatSelect, MatCard
- ✅ `fase-list.component` — MatDialog con @ViewChild TemplateRef, MatProgressBar
- ✅ `shared/confirm-dialog/` — nuevo componente reutilizable con MatDialog
- ✅ `CLAUDE.md` — DEC-007 PrimeNG reemplazado por DEC-011 Angular Material
- ✅ `DECISIONS.md` — DEC-011 agregado

---

## Próxima sesión — Fase B

Serializers + Services + Views para: TerceroProyecto, DocumentoContable, Hito
Frontend: tercero-list, documento-list, hito-list como tabs en proyecto-detail

Endpoints a implementar:
- GET/POST/DELETE `/api/v1/proyectos/{id}/terceros/`
- GET/GET `/api/v1/proyectos/{id}/documentos/`, `/api/v1/documentos/{id}/`
- GET/POST `/api/v1/proyectos/{id}/hitos/`, POST `.../generar-factura/`

---

## Estadísticas del proyecto
- Tests backend: 64 pasando (54 proyectos + 10 auth)
- Endpoints: 11 proyectos + 4 auth = 15 implementados
- Componentes Angular: 4 proyectos + 1 login + 1 confirm-dialog = 6
- Decisiones documentadas: 11
- Última actualización: 2026-03-18
