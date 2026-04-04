# PROMPT PARA CLAUDE CODE — SaiDashboard
**Usar con modelo: Opus**
**Fecha:** 2026-04-01
**Versión:** 1.1 — con estrategia multi-agentes

---

## ⚡ CÓMO PEGAR ESTE PROMPT EN CLAUDE CODE

```bash
# 1. Abrir Claude Code con modelo Opus
claude --model claude-opus-4-6

# 2. Copiar y pegar el bloque "INSTRUCCIÓN INICIAL" de abajo
# 3. Claude Code leerá los archivos, definirá los contratos y lanzará los 4 agentes
```

> **¿Secuencial o paralelo?**
> Cuando Claude Code lea la sección 19 del plan, lanzará los agentes A y B en paralelo
> automáticamente usando la herramienta `Task`. Tú solo pegas el prompt y supervisas.
> Si prefieres ejecutar en modo secuencial (un agente a la vez), indícaselo explícitamente.

---

## INSTRUCCIÓN INICIAL PARA CLAUDE CODE

Hola Claude Code. Vamos a implementar el módulo **SaiDashboard** para el proyecto Saicloud. Este es un módulo nuevo y complejo. Antes de escribir UNA SOLA LÍNEA de código, debes leer estos archivos en este orden exacto:

```
1. saisuite/CLAUDE.md                              ← reglas absolutas del proyecto
2. saisuite/DECISIONS.md                           ← decisiones vigentes (especialmente DEC-011 Angular Material)
3. saisuite/CONTEXT.md                             ← estado actual del proyecto
4. saisuite/ERRORS.md                              ← errores a no repetir
5. saisuite/docs/standards/UI-UX-STANDARDS.md      ← estándares Angular obligatorios
6. saisuite/docs/saiopen/gl.txt                    ← estructura tabla GL (movimiento contable)
7. saisuite/docs/saiopen/acct.txt                  ← estructura tabla ACCT (plan de cuentas)
8. saisuite/docs/saiopen/cust.txt                  ← estructura tabla CUST (terceros)
9. saisuite/docs/saiopen/lista.txt                 ← estructura tabla LISTA (deptos/CC)
10. saisuite/docs/saiopen/proyectos.txt            ← estructura tabla PROYECTOS
11. saisuite/docs/saiopen/actividades.txt          ← estructura tabla ACTIVIDADES
12. saisuite/docs/saiopen/sql_gl.txt               ← SQL base del movimiento contable
13. saisuite/docs/plans/PLAN-SAIDASHBOARD.md       ← EL PLAN COMPLETO (tu guía principal)
```

---

## SKILLS A USAR (en este orden según la fase)

Para cada fase, activa el skill correspondiente:

```bash
# Fase 1 — Agente Go:
# skill: saicloud-microservicio-go

# Fase 2-3 — Backend Django:
# skill: saicloud-backend-django
# skill: saicloud-pruebas-unitarias  (ejecutar siempre junto con backend)

# Fase 5-6 — Frontend Angular:
# skill: saicloud-frontend-angular
# skill: saicloud-pruebas-unitarias

# Fase 7 — Revisión:
# skill: saicloud-revision-final

# Fase 8 — Admin:
# skill: saicloud-panel-admin

# Fase 9 — UI/UX:
# skill: saicloud-validacion-ui
```

---

## CONTEXTO DEL NEGOCIO (resumen para Claude Code)

**¿Qué es SaiDashboard?**
Un módulo de Business Intelligence para gerentes, contadores y financieros de PyMEs colombianas. Permite crear dashboards personalizados con indicadores financieros calculados a partir del movimiento contable de Saiopen.

**¿Por qué Go para el agente?**
El agente corre en la PC Windows del cliente donde está Saiopen (Firebird 2.5). Debe ser un ejecutable standalone sin instalar Python/Java. Criterio 3 de Go cumplido (CLAUDE.md sección 10).

**¿Por qué denormalizar GL en PostgreSQL?**
Firebird 2.5 se lentifica cuando hay usuarios trabajando simultáneamente. Al tener la data denormalizada en PostgreSQL, los reportes del dashboard no afectan el ERP local. La data GL es append-only (nunca se modifica retroactivamente en contabilidad colombiana).

**¿Cómo funciona la licencia de prueba?**
Un tenant puede probar el módulo Dashboard 14 días UNA sola vez. Si la prueba venció, no puede volver a acceder sin que Valmen le active la licencia. Modelo: `ModuleTrial` (unique_together: company + module_code).

**¿Qué son los "modos" de manejo contable?**
Los tenants pueden usar una de tres configuraciones:
- **Modo Simple:** Solo cuenta contable + tercero (sin dimensiones adicionales)
- **Modo Departamento/CC:** Departamento + Centro de Costo como dimensiones
- **Modo Proyecto/Actividad:** Proyecto + Actividad como dimensiones
Esto se configura en `ConfiguracionContable.usa_departamentos_cc` y `usa_proyectos_actividades`.
Las tarjetas del catálogo que requieren una dimensión específica NO se muestran si el tenant no la usa.

**¿Cómo es el PUC colombiano?**
Jerarquía de 5 niveles:
- Nivel 1 (Título): 1=Activo, 2=Pasivo, 3=Patrimonio, 4=Ingresos, 5=Gastos, 6=Costos, 7=Costos Producción, 8=Cuentas Orden Deudoras, 9=Cuentas Orden Acreedoras
- Nivel 2 (Grupo): 2 dígitos
- Nivel 3 (Cuenta): 4 dígitos
- Nivel 4 (Subcuenta): 6 dígitos
- Nivel 5 (Auxiliar): el auxiliar exacto de GL
En ACCT: `CDGOTTL`=código título, `CDGOGRPO`=grupo, `CDGOCNTA`=cuenta, `CDGOSBCNTA`=subcuenta.

**Gráficos:**
Instalar `ngx-echarts` (Apache ECharts wrapper Angular 18). Es la librería aprobada. Soporta: bar, line, pie, waterfall, gauge, area, heatmap, scatter.

**PDF Exportación:**
Instalar `jspdf` + `html2canvas`. El canvas del dashboard está diseñado en tamaño carta (816×1056px a 96dpi portrait, o 1056×816px landscape).

**Drag & Drop:**
Usar `@angular/cdk/drag-drop` (ya instalado). Para resize usar `angular-resizable-element`.

**AI Agent (CFO Virtual):**
Implementar como workflow n8n que llama a Claude API. El componente Angular del CFO Virtual es similar al ChatPanel pero diferente (no reemplaza el chat del sistema, es un panel lateral separado, solo texto, especializado en análisis financiero).

**Compartir por Chat:**
El sistema de chat ya existe (Feature #9). Para compartir un dashboard, el usuario selecciona un usuario → el sistema envía un mensaje al chat con un link `[DASH-001]` → el receptor puede hacer clic y ver el dashboard (si tiene acceso al módulo).

---

## NOTAS CRÍTICAS PARA IMPLEMENTACIÓN

### Go Agent — Multi-Base de Datos
Usar `github.com/nakagami/firebirdsql` como driver. El DSN de Firebird es:
```
user:password@localhost:3050/C:/path/to/database.fdb
```

El agente soporta **N conexiones simultáneas** (empresas hermanas en el mismo servidor). Cada conexión es un goroutine independiente. La configuración y el watermark se almacenan en un único `saicloud-agent.json` en la raíz del instalador — NO hay archivo `.watermark` separado. El campo `sync.last_conteo_gl` dentro de cada connection object es el watermark. Si es 0, inicia sync completo.

### Go Agent — Configurador Web Embebido
El binario tiene modo `agent.exe config` que levanta un servidor HTTP local en `:8765` y abre el navegador automáticamente. La UI es HTML/CSS/JS embebida con `go:embed`. El botón "📂 Examinar..." usa la API Windows `IFileOpenDialog` para seleccionar archivos `.fdb` visualmente. Ver diseño completo en Sección 6.3 del PLAN-SAIDASHBOARD.md.

### Go Agent — Instalación sin tocar JSON
Flujo para el implementador: abrir configurador → agregar empresa → ruta .fdb con Examinar → pegar token → Probar → Guardar → clic "Instalar Servicio". Sin editar archivos a mano.

### Roles — Solo existe `seller` (collector fue unificado)
En la sección de permisos, no existe `collector`. El único rol operativo es `seller`.

### Django — bulk_create con update_conflicts
Para el upsert masivo de GL usar:
```python
MovimientoContable.objects.bulk_create(
    records,
    update_conflicts=True,
    unique_fields=['company', 'conteo'],
    update_fields=['debito', 'credito', 'descripcion', ...]  # todos los campos excepto company y conteo
)
```
Esto requiere Django 4.1+ (ya tenemos Django 5, OK).

### Angular — Estado del Dashboard Builder
Usar Signals de Angular 18 para gestionar el estado del builder (posiciones, tarjetas seleccionadas). Evitar NgRx para este módulo (overkill para MVP).

### Testing — Datos de GL
Para tests unitarios del ReportEngine, crear fixtures con ~50 registros MovimientoContable cubriendo:
- Registros de Activo (CDGOTTL=1...)
- Registros de Ingresos (CDGOTTL=4...)
- Registros de Costos (CDGOTTL=6...)
- Registros en diferentes períodos (2025-01, 2025-12, 2026-01, 2026-03)
- Registros con y sin proyecto/departamento

### Validación 4x4 Obligatoria
Antes de considerar el módulo terminado, validar manualmente (o con screenshots E2E):
- Desktop 1920px + tema claro
- Desktop 1920px + tema oscuro
- Mobile 375px + tema claro
- Mobile 375px + tema oscuro

En mobile, el dashboard builder muestra mensaje "Para crear dashboards usa la versión desktop". El viewer sí funciona en mobile (lista de KPIs en columna).

---

## ESTRATEGIA MULTI-AGENTES (IMPORTANTE — leer antes de empezar)

Este módulo usa **4 agentes especializados en paralelo**. El plan completo está en la sección 19 de PLAN-SAIDASHBOARD.md. Resumen ejecutivo:

```
AGENTE A (Go)        → agent-go/ completo
AGENTE B (Backend)   → apps/contabilidad/ + apps/dashboard/
AGENTE C (Frontend)  → features/dashboard/ Angular
AGENTE D (Tests)     → todos los tests + informe final

Lanzar A + B en paralelo primero.
Lanzar C cuando B tenga modelos básicos + 5 endpoints.
Lanzar D cuando A + B + C estén ~80% completos.
```

Antes de lanzar los agentes, definir los contratos de interfaz (sección 19.2 del plan).
Cada agente tiene archivos exclusivos — NUNCA dos agentes tocan el mismo archivo.

---

## ORDEN DE COMANDOS A EJECUTAR

```bash
# 1. Crear estructura de directorios
mkdir -p agent-go/cmd/agent
mkdir -p agent-go/internal/{config,firebird,sync,api,sqs,configurator,winsvc}
mkdir -p agent-go/internal/configurator/static
mkdir -p backend/apps/contabilidad/tests
mkdir -p backend/apps/contabilidad/migrations
mkdir -p backend/apps/dashboard/tests
mkdir -p backend/apps/dashboard/migrations
mkdir -p frontend/src/app/features/dashboard/{models,services,components,guards}

# 2. Instalar dependencias npm
cd frontend && npm install echarts ngx-echarts angular-resizable-element jspdf html2canvas

# 3. Inicializar módulo Go
cd agent-go && go mod init github.com/valmentech/saicloud-agent

# 4. Ejecutar migraciones después de crear modelos
cd backend && python manage.py makemigrations contabilidad
cd backend && python manage.py makemigrations dashboard
cd backend && python manage.py migrate

# 5. Ejecutar tests
cd backend && python manage.py test apps.contabilidad apps.dashboard --settings=config.settings.testing
cd frontend && ng test --coverage
```

---

## VERIFICACIÓN FINAL ANTES DE COMPLETAR

Ejecuta este checklist antes de marcar el módulo como listo:

```
[ ] 1. go build ./... en agent-go/ → sin errores
[ ] 2. python manage.py check → sin errores
[ ] 3. python manage.py test apps.contabilidad apps.dashboard → 100% passing
[ ] 4. ng build --configuration=production → 0 errores
[ ] 5. ng test → cobertura ≥70% components, ≥100% services
[ ] 6. Endpoint /api/v1/contabilidad/sync/gl-batch/ acepta payload y hace upsert
[ ] 7. Endpoint /api/v1/dashboard/report/card-data/ retorna datos para BALANCE_GENERAL
[ ] 8. Angular: /dashboard carga sin errores con usuario autenticado
[ ] 9. LicenseGuard bloquea correctamente sin licencia/sin trial
[ ] 10. ModuleTrial: segunda activación retorna error "prueba ya utilizada"
[ ] 11. Drag & drop funciona en Chrome desktop
[ ] 12. Export PDF genera archivo descargable
[ ] 13. Dark mode: todas las tarjetas correctas (no colores hardcodeados)
[ ] 14. Mobile 375px: dashboard viewer usable (no builder)
[ ] 15. DEC-037 a DEC-040 añadidos en DECISIONS.md
[ ] 16. CONTEXT.md actualizado con estado del módulo
```

---

*Este prompt fue preparado por Cowork el 2026-04-01*
*Proyecto: Saicloud — ValMen Tech*
*Módulo: SaiDashboard — Feature nueva*
