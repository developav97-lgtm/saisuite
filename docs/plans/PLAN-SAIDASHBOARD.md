# PLAN-SAIDASHBOARD — Módulo SaiDashboard
**Versión:** 1.0
**Fecha:** 2026-04-01
**Módulo:** SaiDashboard
**Fase Metodología:** 1 — Planificación
**Ejecutor:** Claude Code CLI con modelo Opus
**Dependencias previas:** Sistema de Licencias (Feature #8), Sistema de Chat (Feature #9)

---

## INSTRUCCIONES PARA CLAUDE CODE

Antes de generar CUALQUIER archivo de código, lee obligatoriamente:
1. `CLAUDE.md` (reglas absolutas del proyecto)
2. `DECISIONS.md` (decisiones arquitectónicas vigentes)
3. `docs/base-reference/Estandares_Codigo_SaiSuite_v1.docx`
4. `docs/standards/UI-UX-STANDARDS.md`
5. `docs/saiopen/` (todos los archivos .txt de estructura Saiopen)
6. `docs/saiopen/sql_gl.txt` (SQL base del movimiento contable)

---

## 1. RESUMEN EJECUTIVO

SaiDashboard es un módulo de Business Intelligence especializado en movimiento contable y salud financiera para empresas PyME colombianas. Permite a gerencia, contabilidad y finanzas crear dashboards personalizados al estilo Power BI, con tarjetas de indicadores predefinidas, gráficos configurables, filtros avanzados y exportación a PDF.

La data viene de Saiopen (Firebird 2.5 en Windows del cliente) sincronizada a Saicloud (PostgreSQL en AWS) mediante un agente Go instalado localmente. Una vez en PostgreSQL, las consultas son rápidas y no afectan el rendimiento de Saiopen.

---

## 2. CONTEXTO DEL PROYECTO

### Stack vigente
- **Backend:** Django 5 + DRF + PostgreSQL 16
- **Frontend:** Angular 18 + Angular Material (DEC-011, NUNCA PrimeNG/Tailwind)
- **Infraestructura:** AWS ECS Fargate + Upstash Redis + Cloudflare R2
- **Agente local:** Go (ejecutable standalone en Windows del cliente) ↔ Firebird ↔ AWS SQS ↔ Django
- **Auth:** JWT + WebSocket + LicensePermission (DEC-031)
- **Chat:** Sistema en tiempo real ya implementado (Feature #9)

### Módulo activo previo
El módulo Proyectos está en Fase 6. SaiDashboard es un módulo nuevo independiente.

### Criterio Go validado
El agente Go cumple **Criterio 3 de DEC-XXX**: ejecutable standalone que corre en el PC del cliente (Windows), sin dependencias pesadas, compilado como binario. **NO usar Django** para la parte de extracción de Firebird.

---

## 3. ANÁLISIS DE REPOS EXTERNOS

### agency-agents (https://github.com/msitarzewski/agency-agents)
**Decisión: NO instalar como dependencia.** Es una colección de prompts/personas de agentes IA, NO un paquete npm/pip. Útil solo como referencia para diseñar la personalidad del agente financiero IA. Ver Sección 11 para el diseño del agente.

### ui-ux-pro-max (https://www.aitmpl.com/component/skill/creative-design/ui-ux-pro-max)
**Decisión: NO instalar.** No soporta Angular ni Angular Material. El proyecto ya tiene `docs/standards/UI-UX-STANDARDS.md` que es la referencia canónica para componentes Angular.

---

## 4. ESTRUCTURA DE DIRECTORIOS NUEVOS

```
saisuite/
├── agent-go/                     ← NUEVO: Agente Go multi-empresa con configurador web
│   ├── cmd/
│   │   └── agent/
│   │       └── main.go           ← CLI: config | serve | install | uninstall | status | test
│   ├── internal/
│   │   ├── config/
│   │   │   └── config.go         ← AgentConfig con array de Connection; R/W a JSON
│   │   ├── firebird/
│   │   │   └── client.go         ← Driver firebirdsql; queries GL/ACCT/CUST/LISTA
│   │   ├── sync/
│   │   │   ├── orchestrator.go   ← goroutine por conexión habilitada
│   │   │   ├── gl_sync.go        ← sync incremental GL por CONTEO
│   │   │   └── reference_sync.go ← sync completo ACCT/CUST/LISTA/PROYECTOS/ACTIVIDADES
│   │   ├── sqs/
│   │   │   └── publisher.go      ← publica SQSMessage a AWS SQS
│   │   ├── api/
│   │   │   └── client.go         ← cliente HTTP alternativo (fallback si SQS no disponible)
│   │   ├── configurator/
│   │   │   ├── server.go         ← HTTP server local puerto 8765
│   │   │   ├── handlers.go       ← API REST del configurador (CRUD conexiones + test)
│   │   │   └── static/           ← UI embebida con go:embed
│   │   │       ├── index.html    ← Dashboard de conexiones
│   │   │       ├── form.html     ← Formulario agregar/editar conexión
│   │   │       ├── style.css
│   │   │       └── app.js
│   │   └── winsvc/
│   │       └── service.go        ← Instalación Windows Service (golang.org/x/sys)
│   ├── go.mod
│   ├── go.sum
│   ├── Dockerfile                ← Build cross-compile Windows desde Linux/CI
│   └── README.md                 ← Guía de instalación para implementadores
│
├── backend/
│   └── apps/
│       ├── contabilidad/         ← NUEVO: Espejo de data Saiopen
│       │   ├── __init__.py
│       │   ├── apps.py
│       │   ├── models.py
│       │   ├── serializers.py
│       │   ├── services.py
│       │   ├── views.py
│       │   ├── urls.py
│       │   ├── admin.py
│       │   └── tests/
│       │       ├── test_models.py
│       │       └── test_services.py
│       │
│       └── dashboard/            ← NUEVO: Módulo SaiDashboard
│           ├── __init__.py
│           ├── apps.py
│           ├── models.py
│           ├── serializers.py
│           ├── services.py
│           ├── views.py
│           ├── urls.py
│           ├── admin.py
│           ├── card_catalog.py   ← Registro de tarjetas predefinidas
│           ├── report_engine.py  ← Motor de generación de reportes
│           └── tests/
│               ├── test_models.py
│               ├── test_services.py
│               └── test_views.py
│
└── frontend/
    └── src/app/features/
        └── dashboard/            ← NUEVO: Módulo Angular
            ├── dashboard.module.ts
            ├── dashboard-routing.module.ts
            ├── models/
            │   ├── dashboard.model.ts
            │   ├── dashboard-card.model.ts
            │   ├── card-catalog.model.ts
            │   └── report-filter.model.ts
            ├── services/
            │   ├── dashboard.service.ts
            │   ├── report.service.ts
            │   └── card-catalog.service.ts
            ├── components/
            │   ├── dashboard-list/
            │   ├── dashboard-builder/
            │   ├── dashboard-viewer/
            │   ├── card-selector/
            │   ├── chart-card/
            │   ├── kpi-card/
            │   ├── filter-panel/
            │   ├── period-comparator/
            │   ├── ai-assistant/
            │   └── share-dialog/
            └── guards/
                └── dashboard-license.guard.ts
```

---

## 5. ARQUITECTURA DE DATOS

### 5.1 Flujo de Sincronización

```
Firebird (Windows cliente)
    ↓ [Go Agent - incremental por CONTEO]
AWS SQS (cola: saicloud-gl-sync)
    ↓ [Django SQS Consumer - Celery o management command]
PostgreSQL (app contabilidad)
    ↓ [Django ORM + índices optimizados]
Dashboard API REST
    ↓
Angular Dashboard
```

### 5.2 Estrategia de Sync Incremental (Go Agent)

El agente Go mantiene un **watermark** local (archivo JSON o SQLite):
```json
{
  "company_id": "uuid-empresa",
  "last_conteo_gl": 458920,
  "last_sync_acct": "2026-04-01T08:00:00Z",
  "last_sync_cust": "2026-04-01T08:00:00Z",
  "last_sync_lista": "2026-04-01T08:00:00Z"
}
```

**GL (movimiento contable):**
- Sync incremental: `WHERE CONTEO > last_conteo_gl ORDER BY CONTEO`
- Batch de 500 registros por mensaje SQS
- `CONTEO` es autoincremental → nunca modificado → safe watermark

**ACCT / CUST / LISTA / PROYECTOS / ACTIVIDADES (tablas de referencia):**
- Sync completo cada 24 horas (pequeñas, ~1000-5000 registros)
- Upsert en Django (insert or update)

### 5.3 Modelo Denormalizado: MovimientoContable

Almacenamos el movimiento GL **completamente denormalizado** (ya con los joins del sql_gl.txt), para eliminar joins en tiempo de consulta de reportes.

```python
# backend/apps/contabilidad/models.py
class MovimientoContable(models.Model):
    """
    Espejo de la tabla GL de Saiopen, denormalizado con los joins.
    READ-ONLY desde Saicloud — nunca modificar directamente.
    Sincronizado desde Saiopen vía agente Go + SQS.
    """
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, db_index=True)

    # Identificador original de Firebird (para deduplicación)
    conteo = models.IntegerField(help_text="PK original de Firebird GL.CONTEO")

    # Cuenta Contable - jerarquía completa PUC colombiano
    auxiliar = models.DecimalField(max_digits=18, decimal_places=4, db_index=True)
    auxiliar_nombre = models.CharField(max_length=120)
    titulo_codigo = models.IntegerField(null=True)          # Nivel 1
    titulo_nombre = models.CharField(max_length=120, blank=True)
    grupo_codigo = models.IntegerField(null=True)           # Nivel 2
    grupo_nombre = models.CharField(max_length=120, blank=True)
    cuenta_codigo = models.IntegerField(null=True)          # Nivel 3
    cuenta_nombre = models.CharField(max_length=120, blank=True)
    subcuenta_codigo = models.IntegerField(null=True)       # Nivel 4
    subcuenta_nombre = models.CharField(max_length=120, blank=True)

    # Tercero (CUST)
    tercero_id = models.CharField(max_length=30, db_index=True)
    tercero_nombre = models.CharField(max_length=35, blank=True)

    # Valores contables — SIEMPRE NUMERIC(15,2)
    debito = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credito = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Tipo de documento
    tipo = models.CharField(max_length=3, blank=True)
    batch = models.IntegerField(null=True)
    invc = models.CharField(max_length=15, blank=True)      # número de documento
    descripcion = models.CharField(max_length=120, blank=True)

    # Fechas
    fecha = models.DateField(db_index=True)
    duedate = models.DateField(null=True)                   # fecha de vencimiento
    periodo = models.CharField(max_length=7, db_index=True) # YYYY-MM

    # Departamento (opcional por empresa)
    departamento_codigo = models.SmallIntegerField(null=True, blank=True)
    departamento_nombre = models.CharField(max_length=40, blank=True)

    # Centro de Costo (opcional por empresa)
    centro_costo_codigo = models.SmallIntegerField(null=True, blank=True)
    centro_costo_nombre = models.CharField(max_length=40, blank=True)

    # Proyecto (opcional por empresa)
    proyecto_codigo = models.CharField(max_length=10, null=True, blank=True, db_index=True)
    proyecto_nombre = models.CharField(max_length=60, blank=True)

    # Actividad (opcional por empresa)
    actividad_codigo = models.CharField(max_length=3, null=True, blank=True)
    actividad_nombre = models.CharField(max_length=60, blank=True)

    # Metadata de sync
    sincronizado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'contabilidad'
        db_table = 'cont_movimiento'
        unique_together = [('company', 'conteo')]
        indexes = [
            models.Index(fields=['company', 'fecha']),
            models.Index(fields=['company', 'periodo']),
            models.Index(fields=['company', 'auxiliar']),
            models.Index(fields=['company', 'titulo_codigo']),
            models.Index(fields=['company', 'tercero_id']),
            models.Index(fields=['company', 'proyecto_codigo']),
            models.Index(fields=['company', 'departamento_codigo']),
            models.Index(fields=['company', 'fecha', 'titulo_codigo']),  # composite para reportes
        ]

    def __str__(self):
        return f"{self.company} | {self.fecha} | {self.auxiliar_nombre} | D:{self.debito} C:{self.credito}"
```

### 5.4 Modelo de Configuración Contable por Empresa

```python
class ConfiguracionContable(models.Model):
    """
    Configuración de cómo el tenant maneja su contabilidad en Saiopen.
    Determina qué filtros/dimensiones están disponibles en el dashboard.
    """
    company = models.OneToOneField('companies.Company', on_delete=models.CASCADE,
                                    related_name='config_contable')

    # ¿El cliente usa Departamentos y Centros de Costo?
    usa_departamentos_cc = models.BooleanField(default=False)

    # ¿El cliente usa Proyectos y Actividades?
    usa_proyectos_actividades = models.BooleanField(default=False)

    # Watermark de sync — último CONTEO procesado
    ultimo_conteo_gl = models.BigIntegerField(default=0)
    ultima_sync_gl = models.DateTimeField(null=True)
    ultima_sync_acct = models.DateTimeField(null=True)

    # Estado del sync
    sync_activo = models.BooleanField(default=False)
    sync_error = models.TextField(blank=True)

    class Meta:
        app_label = 'contabilidad'
        db_table = 'cont_configuracion'
```

### 5.5 Modelos de Cuenta Contable (referencia PUC)

```python
class CuentaContable(models.Model):
    """
    Espejo del plan de cuentas (PUC) de Saiopen.
    Sync completo diario desde tabla ACCT de Firebird.
    """
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE)
    codigo = models.DecimalField(max_digits=18, decimal_places=4)
    descripcion = models.CharField(max_length=120)
    nivel = models.SmallIntegerField(default=0)
    clase = models.CharField(max_length=1, blank=True)  # ACCT.CLASS
    tipo = models.CharField(max_length=3, blank=True)   # ACCT.TIPO
    titulo_codigo = models.IntegerField(default=0)
    grupo_codigo = models.IntegerField(default=0)
    cuenta_codigo = models.IntegerField(default=0)
    subcuenta_codigo = models.IntegerField(default=0)
    posicion_financiera = models.IntegerField(default=0)  # POSESTFINAN — clasificación en estados financieros

    class Meta:
        app_label = 'contabilidad'
        db_table = 'cont_cuenta_contable'
        unique_together = [('company', 'codigo')]
```

---

## 6. AGENTE GO — SYNC SAIOPEN → SAICLOUD

### 6.1 Justificación Criterio Go (Obligatorio por CLAUDE.md)
✅ **Criterio 3 cumplido:** Ejecutable standalone que corre en el PC del cliente Windows. Debe ser un binario compilado sin dependencias externas. **No puede ser Django** porque necesita conectarse a Firebird localmente.

### 6.2 Soporte Multi-Base de Datos (Empresas Hermanas)

Un mismo servidor Windows puede tener **dos o más bases de datos Saiopen** (ejemplo: dos empresas del mismo grupo). Cada base de datos se sincroniza a un **tenant diferente en Saicloud**. La configuración soporta N conexiones en el mismo agente, y cada una tiene su propio watermark, credenciales Firebird y token de tenant.

**Estructura del archivo de configuración `saicloud-agent.json`:**
```json
{
  "agent_version": "1.0.0",
  "configurator_port": 8765,
  "log_level": "info",
  "log_file": "C:/SaicloudAgent/logs/agent.log",
  "connections": [
    {
      "id": "conn_001",
      "name": "Empresa Principal S.A.S",
      "enabled": true,
      "firebird": {
        "host": "localhost",
        "port": 3050,
        "database": "C:/SAIOPEN/DATOS/EMPRESA1.FDB",
        "user": "SYSDBA",
        "password": "masterkey"
      },
      "saicloud": {
        "api_url": "https://api.saicloud.co",
        "company_id": "uuid-empresa-1-en-saicloud",
        "agent_token": "jwt-token-agente-empresa-1"
      },
      "sync": {
        "gl_interval_minutes": 15,
        "reference_interval_hours": 24,
        "batch_size": 500,
        "last_conteo_gl": 0,
        "last_sync_acct": null,
        "last_sync_cust": null,
        "last_sync_lista": null
      }
    },
    {
      "id": "conn_002",
      "name": "Empresa Hermana Ltda",
      "enabled": true,
      "firebird": {
        "host": "localhost",
        "port": 3050,
        "database": "C:/SAIOPEN/DATOS/EMPRESA2.FDB",
        "user": "SYSDBA",
        "password": "masterkey2"
      },
      "saicloud": {
        "api_url": "https://api.saicloud.co",
        "company_id": "uuid-empresa-2-en-saicloud",
        "agent_token": "jwt-token-agente-empresa-2"
      },
      "sync": {
        "gl_interval_minutes": 15,
        "reference_interval_hours": 24,
        "batch_size": 500,
        "last_conteo_gl": 0,
        "last_sync_acct": null,
        "last_sync_cust": null,
        "last_sync_lista": null
      }
    }
  ]
}
```

**El watermark se almacena dentro del propio `saicloud-agent.json`** (campo `sync.last_conteo_gl`). El agente actualiza este archivo cada vez que completa un batch. No hay archivo `.watermark` separado. Si `last_conteo_gl = 0`, inicia sync completo desde el principio.

### 6.3 Configurador Web Embebido (Para Implementadores)

**Problema:** Los implementadores no siempre son técnicos. Editar un JSON a mano es propenso a errores.

**Solución:** El binario `agent.exe` tiene un modo `config` que levanta un **servidor web local** en `http://localhost:8765` y abre el navegador automáticamente. El implementador configura todo desde una interfaz web amigable, sin tocar el JSON directamente.

```
agent.exe config          → abre configurador en http://localhost:8765
agent.exe serve           → inicia el servicio de sync (modo producción)
agent.exe install         → registra como Windows Service
agent.exe uninstall       → elimina el Windows Service
agent.exe status          → muestra estado de todas las conexiones
agent.exe test --id conn_001  → prueba la conexión sin hacer sync real
```

**Pantallas del configurador web (HTML embebido con `go:embed`):**

```
┌─────────────────────────────────────────────────────────┐
│  🔵 SaiCloud Agent — Configurador                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Conexiones configuradas:                               │
│  ┌──────────────────────────────────────────────────┐   │
│  │ ✅ Empresa Principal S.A.S    [Editar] [Probar]  │   │
│  │    Última sync: hace 3 min — 1,234 registros     │   │
│  ├──────────────────────────────────────────────────┤   │
│  │ ✅ Empresa Hermana Ltda       [Editar] [Probar]  │   │
│  │    Última sync: hace 5 min — 456 registros       │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  [+ Agregar nueva empresa]                              │
│                                                         │
│  Estado del servicio: ✅ Corriendo                      │
│  [Ver Logs] [Instalar Servicio] [Detener]               │
└─────────────────────────────────────────────────────────┘
```

**Formulario de agregar/editar una conexión:**
```
Nombre de la empresa: [Empresa Principal S.A.S          ]

--- Conexión a Saiopen (Firebird) ---
Ruta de la base de datos:
[C:\SAIOPEN\DATOS\EMPRESA1.FDB                          ]
                                        [📂 Examinar...]

Host Firebird:    [localhost    ]   Puerto: [3050]
Usuario:          [SYSDBA       ]
Contraseña:       [••••••••     ]

--- Conexión a SaiCloud ---
Token de empresa: [Pegar aquí el token que te dio Valmen ]
                   (Lo encuentras en SaiCloud → Admin → Agente)

[🔍 Probar conexión]   [💾 Guardar]   [Cancelar]
```

**Pantalla "Probar conexión"** — ejecuta estos pasos y muestra resultado:
```
✅ 1. Conexión a Firebird: OK (Empresa: PRINCIPAL S.A.S)
✅ 2. Lectura tabla GL: OK (458,920 registros disponibles)
✅ 3. Conexión a SaiCloud: OK (Empresa: Empresa Principal S.A.S)
✅ 4. Permisos del token: OK (Agente autorizado)

Todo listo. Puedes iniciar la sincronización.
[Cerrar]
```

**El botón "📂 Examinar..."** abre un explorador de archivos nativo de Windows (usando la API `IFileOpenDialog` vía `syscall`), para que el implementador pueda navegar hasta el archivo `.fdb` sin escribir la ruta manualmente.

### 6.4 Dependencias Go

```go
// go.mod
module github.com/valmentech/saicloud-agent

go 1.22

require (
    github.com/nakagami/firebirdsql v0.9.10        // Driver Firebird nativo Go (sin ODBC)
    github.com/aws/aws-sdk-go-v2 v1.26.0           // AWS SDK v2
    github.com/aws/aws-sdk-go-v2/service/sqs v1.31.0
    github.com/aws/aws-sdk-go-v2/config v1.27.0
    golang.org/x/sys v0.18.0                       // Windows Service API
    // No se necesita dependencia de GUI — el configurador es HTML embebido
)
```

### 6.5 Estructura de Directorios del Agente Go

```
agent-go/
├── cmd/
│   └── agent/
│       └── main.go              ← Punto de entrada, parseo de comandos CLI
├── internal/
│   ├── config/
│   │   └── config.go            ← Struct AgentConfig, lectura/escritura JSON
│   ├── firebird/
│   │   └── client.go            ← Conexión Firebird, queries GL/ACCT/CUST/LISTA
│   ├── sync/
│   │   ├── orchestrator.go      ← Orquestador: itera sobre connections habilitadas
│   │   ├── gl_sync.go           ← Sync incremental GL (por CONTEO)
│   │   └── reference_sync.go   ← Sync completo ACCT, CUST, LISTA, PROYECTOS, ACTIVIDADES
│   ├── sqs/
│   │   └── publisher.go         ← Publicación de mensajes en AWS SQS
│   ├── api/
│   │   └── client.go            ← Cliente HTTP para endpoints Django (alternativa a SQS)
│   ├── configurator/
│   │   ├── server.go            ← Servidor HTTP local del configurador web
│   │   ├── handlers.go          ← Handlers: listar, crear, editar, probar conexión
│   │   └── static/              ← HTML/CSS/JS del UI (embebido con go:embed)
│   │       ├── index.html
│   │       ├── style.css
│   │       └── app.js
│   └── winsvc/
│       └── service.go           ← Instalación/desinstalación Windows Service
├── go.mod
├── go.sum
├── Dockerfile                   ← Para compilar cross-platform desde CI/CD
└── README.md
```

### 6.6 Lógica del Orquestador Multi-Conexión

```go
// internal/sync/orchestrator.go
//
// El orquestador crea un goroutine independiente por cada conexión habilitada.
// Cada goroutine tiene su propio ticker (gl_interval_minutes).
// Si una conexión falla, no afecta las demás.
//
// Pseudocódigo:
//
// for _, conn := range config.Connections {
//     if !conn.Enabled { continue }
//     go runConnectionSync(conn)  // goroutine independiente
// }
//
// func runConnectionSync(conn Connection):
//     fbClient = firebird.NewClient(conn.Firebird)
//     ticker = time.NewTicker(conn.Sync.GLIntervalMinutes)
//     for range ticker.C:
//         syncGL(fbClient, conn)
//         if horaDeRefresh(conn):
//             syncReferences(fbClient, conn)
```

### 6.7 Query GL Incremental (basado en docs/saiopen/sql_gl.txt)

```sql
SELECT
    G.CONTEO, G.FECHA, G.DUEDATE, G.INVC,
    C.ID_N AS TERCERO_ID, C.COMPANY AS TERCERO_NOMBRE,
    A.ACCT AS AUXILIAR, A.DESCRIPCION AS AUXILIAR_NOMBRE,
    A.CDGOTTL AS TITULO_CODIGO, ACT.DESCRIPCION AS TITULO_NOMBRE,
    A.CDGOGRPO AS GRUPO_CODIGO, ACG.DESCRIPCION AS GRUPO_NOMBRE,
    A.CDGOCNTA AS CUENTA_CODIGO, ACC.DESCRIPCION AS CUENTA_NOMBRE,
    A.CDGOSBCNTA AS SUBCUENTA_CODIGO, ACS.DESCRIPCION AS SUBCUENTA_NOMBRE,
    G.DEBIT, G.CREDIT, G.TIPO, G.BATCH, G.DESCRIPCION, G.PERIOD,
    G.DEPTO AS DEPARTAMENTO_CODIGO, LD.DESCRIPCION AS DEPARTAMENTO_NOMBRE,
    G.CCOST AS CENTRO_COSTO_CODIGO, LC.DESCRIPCION AS CENTRO_COSTO_NOMBRE,
    G.PROYECTO AS PROYECTO_CODIGO, P.DESCRIPCION AS PROYECTO_NOMBRE,
    G.ACTIVIDAD AS ACTIVIDAD_CODIGO, AC.DESCRIPCION AS ACTIVIDAD_NOMBRE
FROM GL G
INNER JOIN CUST C ON C.ID_N = G.ID_N
INNER JOIN ACCT A ON A.ACCT = G.ACCT
INNER JOIN ACCT ACT ON A.CDGOTTL = ACT.ACCT
INNER JOIN ACCT ACG ON A.CDGOGRPO = ACG.ACCT
INNER JOIN ACCT ACC ON A.CDGOCNTA = ACC.ACCT
INNER JOIN ACCT ACS ON A.CDGOSBCNTA = ACS.ACCT
LEFT JOIN LISTA LD ON LD.CODIGO = G.DEPTO AND LD.TIPO='DP'
LEFT JOIN LISTA LC ON LC.CODIGO = G.CCOST AND LC.TIPO='CC'
LEFT JOIN PROYECTOS P ON P.CODIGO = G.PROYECTO
LEFT JOIN ACTIVIDADES AC ON AC.CODIGO = G.ACTIVIDAD
WHERE G.CONTEO > ?
ORDER BY G.CONTEO ASC
ROWS 1 TO ?
```

### 6.8 Mensajes SQS

```go
// internal/sqs/publisher.go
type SQSMessage struct {
    Type      string          `json:"type"`       // "gl_batch", "acct_full", etc.
    CompanyID string          `json:"company_id"` // UUID del tenant en Saicloud
    Timestamp time.Time       `json:"timestamp"`
    ConnID    string          `json:"conn_id"`    // ID de la conexión (para trazabilidad)
    Data      json.RawMessage `json:"data"`
}

// Tipos:
// "gl_batch"        → lote de movimientos GL (hasta batch_size registros)
// "acct_full"       → sync completo de cuentas contables
// "cust_full"       → sync completo de terceros
// "lista_full"      → sync completo (departamentos y centros de costo)
// "proyectos_full"  → sync completo de proyectos
// "actividades_full"→ sync completo de actividades
```

### 6.9 Proceso de Instalación para el Implementador

Flujo completo desde cero (5 pasos, sin tocar JSON manualmente):

```
PASO 1 — Obtener el token del tenant
  El admin de la empresa en SaiCloud va a: Configuración → Agente Go → Generar Token
  Copia el token (expira en 30 días si no se usa, luego es permanente)

PASO 2 — Instalar el agente
  Descargar SaicloudAgentSetup.exe desde el portal de Valmen
  Ejecutar instalador → descomprime en C:\SaicloudAgent\

PASO 3 — Abrir configurador
  Doble clic en "SaiCloud Configurador" (acceso directo en escritorio)
  Se abre http://localhost:8765 en el navegador

PASO 4 — Agregar empresas
  Clic en "+ Agregar nueva empresa"
  Nombre: Empresa Principal S.A.S
  Ruta DB: clic en "📂 Examinar..." → navegar hasta el archivo .fdb
  Token: pegar el token copiado en Paso 1
  Clic en "🔍 Probar conexión" → verificar que todos los pasos sean ✅
  Clic en "💾 Guardar"
  (Repetir para empresa hermana si aplica)

PASO 5 — Instalar como servicio
  En el configurador, clic en "Instalar Servicio Windows"
  → Se registra como servicio de arranque automático
  → El agente inicia la sincronización inmediatamente
```

### 6.10 Endpoints Django para Recibir Mensajes del Agente

```
POST /api/v1/contabilidad/sync/gl-batch/        ← recibe lote GL
POST /api/v1/contabilidad/sync/acct/             ← sync cuentas contables
POST /api/v1/contabilidad/sync/cust/             ← sync terceros
POST /api/v1/contabilidad/sync/listas/           ← sync departamentos/CC
POST /api/v1/contabilidad/sync/proyectos/        ← sync proyectos
POST /api/v1/contabilidad/sync/actividades/      ← sync actividades
GET  /api/v1/contabilidad/sync/status/           ← estado del sync por empresa
POST /api/v1/contabilidad/agent/generate-token/  ← genera token de agente (para admin)
```

Autenticación: JWT de servicio con claim `"role": "sync_agent"` y `"company_id"`. El token lo genera Saicloud (endpoint `generate-token/`) y el admin del tenant lo copia al configurador.

---

## 7. BACKEND DJANGO — APP CONTABILIDAD

### 7.1 Servicios principales

#### `SyncService` (services.py)
```python
class SyncService:
    def process_gl_batch(company_id, records: list[dict]) -> dict:
        """
        Recibe lista de registros GL del agente Go (vía SQS/endpoint).
        Hace upsert masivo usando bulk_create(update_conflicts=True).
        Actualiza watermark en ConfiguracionContable.
        Retorna: {inserted: N, updated: M, errors: []}
        """

    def process_acct_full(company_id, records: list[dict]) -> dict:
        """
        Sync completo de plan de cuentas.
        Usa bulk_create(update_conflicts=True) con update_fields.
        """

    def get_sync_status(company_id) -> dict:
        """Retorna estado del sync: último conteo, última fecha, total registros."""
```

### 7.2 Validaciones críticas en sync
- Verificar que `company_id` del payload coincide con el token JWT del agente
- Nunca aceptar registros con `debito` o `credito` en formato `float` → siempre `Decimal`
- Validar que `fecha` sea una fecha válida antes de insertar

---

## 8. BACKEND DJANGO — APP DASHBOARD

### 8.1 Modelos

```python
# backend/apps/dashboard/models.py

class Dashboard(BaseModel):
    """Dashboard personalizado de un usuario."""
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='dashboards')
    titulo = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True)
    es_privado = models.BooleanField(default=True)
    es_favorito = models.BooleanField(default=False)
    es_default = models.BooleanField(default=False)  # ← solo uno por usuario

    # Configuración de página
    orientacion = models.CharField(max_length=20, default='portrait',
                                    choices=[('portrait', 'Vertical'), ('landscape', 'Horizontal')])
    # company heredado de BaseModel

    class Meta:
        indexes = [
            models.Index(fields=['company', 'user', 'es_default']),
        ]


class DashboardCard(models.Model):
    """Tarjeta individual en un dashboard."""
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='cards')

    # Tipo de tarjeta (referencia al CARD_CATALOG)
    card_type_code = models.CharField(max_length=50)

    # Visualización elegida por el usuario
    chart_type = models.CharField(max_length=20,
                                   choices=[('bar', 'Barras'), ('pie', 'Torta'),
                                            ('line', 'Línea'), ('kpi', 'Indicador'),
                                            ('table', 'Tabla'), ('area', 'Área'),
                                            ('waterfall', 'Cascada'), ('gauge', 'Velocímetro')])

    # Posición y tamaño en el grid (unidades de celda)
    pos_x = models.SmallIntegerField(default=0)
    pos_y = models.SmallIntegerField(default=0)
    width = models.SmallIntegerField(default=2)   # en columnas (máx 4)
    height = models.SmallIntegerField(default=2)  # en filas (máx 4)

    # Filtros específicos de esta tarjeta (JSON)
    filtros_config = models.JSONField(default=dict)
    """
    Estructura filtros_config:
    {
        "fecha_desde": "2026-01-01",
        "fecha_hasta": "2026-03-31",
        "tercero_ids": [],
        "proyecto_codigos": [],
        "departamento_codigos": [],
        "ccost_codigos": [],
        "comparar_periodo": false,
        "periodo_comparacion": null
    }
    """

    # Título personalizado
    titulo_personalizado = models.CharField(max_length=100, blank=True)

    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['orden', 'pos_y', 'pos_x']


class DashboardShare(models.Model):
    """Registro de dashboard compartido con otro usuario."""
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='shares')
    compartido_con = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='dashboards_compartidos')
    compartido_por = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='dashboards_compartidos_por_mi')
    puede_editar = models.BooleanField(default=False)  # Por ahora siempre False (solo lectura)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('dashboard', 'compartido_con')]


class ModuleTrial(models.Model):
    """
    Registro de licencias de prueba por módulo.
    Una vez usado, no puede volver a activarse (is_used=True incluso al vencer).
    """
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE)
    module_code = models.CharField(max_length=50)  # ej: 'dashboard'
    iniciado_en = models.DateTimeField(auto_now_add=True)
    expira_en = models.DateTimeField()  # iniciado_en + 14 días

    class Meta:
        unique_together = [('company', 'module_code')]

    def esta_activo(self) -> bool:
        from django.utils import timezone
        return timezone.now() <= self.expira_en

    def dias_restantes(self) -> int:
        from django.utils import timezone
        delta = self.expira_en - timezone.now()
        return max(0, delta.days)
```

### 8.2 Catálogo de Tarjetas Predefinidas

```python
# backend/apps/dashboard/card_catalog.py
"""
Catálogo de tarjetas predefinidas para SaiDashboard.
Cada tarjeta sabe cómo calcular su KPI desde MovimientoContable.
Este catálogo es código (no BD) — versionado con el proyecto.
"""

CARD_CATALOG = {

    # ─── CATEGORÍA: FINANCIERO ─────────────────────────────────────────

    "BALANCE_GENERAL": {
        "nombre": "Balance General",
        "categoria": "financiero",
        "descripcion": "Activos, Pasivos y Patrimonio por período",
        "chart_types": ["bar", "pie", "table", "kpi"],
        "chart_default": "bar",
        "color": "#1565C0",
        "icono": "account_balance",
        "requiere": [],
        "agrupacion": "titulo",  # Agrupa por nivel Título del PUC
        # Cuentas: Activo=clase que comienza en 1, Pasivo=2, Patrimonio=3
        # La clasificación se hace por POSESTFINAN de ACCT o por rango de auxiliar
    },

    "ESTADO_RESULTADOS": {
        "nombre": "Estado de Resultados (P&G)",
        "categoria": "financiero",
        "descripcion": "Ingresos, Costos y Gastos del período",
        "chart_types": ["waterfall", "bar", "table"],
        "chart_default": "waterfall",
        "color": "#2E7D32",
        "icono": "trending_up",
        "requiere": [],
        "agrupacion": "grupo",
    },

    "INDICADORES_LIQUIDEZ": {
        "nombre": "Indicadores de Liquidez",
        "categoria": "financiero",
        "descripcion": "Razón Corriente, Prueba Ácida, Capital de Trabajo",
        "chart_types": ["kpi", "gauge"],
        "chart_default": "kpi",
        "color": "#F57F17",
        "icono": "water_drop",
        "requiere": [],
    },

    "EBITDA": {
        "nombre": "EBITDA",
        "categoria": "financiero",
        "descripcion": "Utilidad antes de impuestos, intereses, depreciación y amortización",
        "chart_types": ["kpi", "bar", "line"],
        "chart_default": "kpi",
        "color": "#4A148C",
        "icono": "insights",
        "requiere": [],
    },

    "INGRESOS_VS_EGRESOS": {
        "nombre": "Ingresos vs Egresos",
        "categoria": "financiero",
        "descripcion": "Comparativo de ingresos y egresos por mes",
        "chart_types": ["bar", "line", "area"],
        "chart_default": "bar",
        "color": "#00695C",
        "icono": "compare_arrows",
        "requiere": [],
    },

    "ROE_ROA": {
        "nombre": "ROE / ROA",
        "categoria": "financiero",
        "descripcion": "Retorno sobre patrimonio y activos",
        "chart_types": ["kpi", "gauge"],
        "chart_default": "kpi",
        "color": "#AD1457",
        "icono": "percent",
        "requiere": [],
    },

    "ENDEUDAMIENTO": {
        "nombre": "Indicadores de Endeudamiento",
        "categoria": "financiero",
        "descripcion": "Deuda/Activo, Deuda/Patrimonio, Apalancamiento",
        "chart_types": ["kpi", "gauge", "bar"],
        "chart_default": "kpi",
        "color": "#BF360C",
        "icono": "account_balance_wallet",
        "requiere": [],
    },

    # ─── CATEGORÍA: COSTOS ────────────────────────────────────────────

    "COSTO_VENTAS": {
        "nombre": "Costo de Ventas",
        "categoria": "costos",
        "descripcion": "Costo de ventas por período y tendencia",
        "chart_types": ["bar", "line", "kpi"],
        "chart_default": "bar",
        "color": "#E65100",
        "icono": "shopping_cart",
        "requiere": [],
    },

    "MARGEN_BRUTO_NETO": {
        "nombre": "Margen Bruto / Neto",
        "categoria": "costos",
        "descripcion": "% de margen bruto y neto sobre ingresos",
        "chart_types": ["kpi", "line", "bar"],
        "chart_default": "kpi",
        "color": "#558B2F",
        "icono": "show_chart",
        "requiere": [],
    },

    "GASTOS_OPERACIONALES": {
        "nombre": "Gastos Operacionales",
        "categoria": "costos",
        "descripcion": "Distribución de gastos operacionales por cuenta",
        "chart_types": ["pie", "bar", "table"],
        "chart_default": "bar",
        "color": "#6A1B9A",
        "icono": "payments",
        "requiere": [],
    },

    "GASTOS_POR_DEPARTAMENTO": {
        "nombre": "Gastos por Departamento",
        "categoria": "costos",
        "descripcion": "Distribución de gastos por departamento",
        "chart_types": ["bar", "pie", "table"],
        "chart_default": "bar",
        "color": "#0277BD",
        "icono": "business",
        "requiere": ["usa_departamentos_cc"],
    },

    "GASTOS_POR_CENTRO_COSTO": {
        "nombre": "Gastos por Centro de Costo",
        "categoria": "costos",
        "descripcion": "Distribución de gastos por centro de costo",
        "chart_types": ["bar", "pie", "table"],
        "chart_default": "bar",
        "color": "#00695C",
        "icono": "location_city",
        "requiere": ["usa_departamentos_cc"],
    },

    # ─── CATEGORÍA: CARTERA/CLIENTES ──────────────────────────────────

    "CARTERA_TOTAL": {
        "nombre": "Cartera Total (CxC)",
        "categoria": "clientes",
        "descripcion": "Total cuentas por cobrar activas",
        "chart_types": ["kpi", "bar", "line"],
        "chart_default": "kpi",
        "color": "#1565C0",
        "icono": "receipt_long",
        "requiere": [],
    },

    "AGING_CARTERA": {
        "nombre": "Antigüedad de Cartera",
        "categoria": "clientes",
        "descripcion": "Distribución de cartera por días de vencimiento (0-30, 31-60, 61-90, +90)",
        "chart_types": ["bar", "pie", "table"],
        "chart_default": "bar",
        "color": "#C62828",
        "icono": "access_time",
        "requiere": [],
    },

    "TOP_CLIENTES_SALDO": {
        "nombre": "Top 10 Clientes por Saldo",
        "categoria": "clientes",
        "descripcion": "Los 10 clientes con mayor saldo en cartera",
        "chart_types": ["bar", "table"],
        "chart_default": "bar",
        "color": "#006064",
        "icono": "leaderboard",
        "requiere": [],
    },

    "MOVIMIENTO_POR_TERCERO": {
        "nombre": "Movimiento por Tercero",
        "categoria": "clientes",
        "descripcion": "Total débitos y créditos por tercero en el período",
        "chart_types": ["table", "bar"],
        "chart_default": "table",
        "color": "#37474F",
        "icono": "people",
        "requiere": [],
    },

    # ─── CATEGORÍA: PROVEEDORES ────────────────────────────────────────

    "CUENTAS_POR_PAGAR": {
        "nombre": "Cuentas por Pagar (CxP)",
        "categoria": "proveedores",
        "descripcion": "Total cuentas por pagar activas",
        "chart_types": ["kpi", "bar", "line"],
        "chart_default": "kpi",
        "color": "#4527A0",
        "icono": "payment",
        "requiere": [],
    },

    "AGING_PROVEEDORES": {
        "nombre": "Antigüedad de Proveedores",
        "categoria": "proveedores",
        "descripcion": "Distribución de CxP por días de vencimiento",
        "chart_types": ["bar", "pie", "table"],
        "chart_default": "bar",
        "color": "#BF360C",
        "icono": "hourglass_bottom",
        "requiere": [],
    },

    "TOP_PROVEEDORES": {
        "nombre": "Top 10 Proveedores por Deuda",
        "categoria": "proveedores",
        "descripcion": "Los 10 proveedores con mayor saldo pendiente",
        "chart_types": ["bar", "table"],
        "chart_default": "bar",
        "color": "#1B5E20",
        "icono": "local_shipping",
        "requiere": [],
    },

    # ─── CATEGORÍA: PROYECTOS ─────────────────────────────────────────

    "COSTO_POR_PROYECTO": {
        "nombre": "Costo por Proyecto",
        "categoria": "proyectos",
        "descripcion": "Total costos imputados a cada proyecto",
        "chart_types": ["bar", "pie", "table"],
        "chart_default": "bar",
        "color": "#F9A825",
        "icono": "folder_special",
        "requiere": ["usa_proyectos_actividades"],
    },

    "COSTO_POR_ACTIVIDAD": {
        "nombre": "Costo por Actividad",
        "categoria": "proyectos",
        "descripcion": "Distribución de costos por actividad dentro del proyecto",
        "chart_types": ["bar", "table"],
        "chart_default": "bar",
        "color": "#E65100",
        "icono": "task",
        "requiere": ["usa_proyectos_actividades"],
    },

    # ─── CATEGORÍA: COMPARATIVAS ──────────────────────────────────────

    "COMPARATIVO_PERIODOS": {
        "nombre": "Comparativo Período vs Período",
        "categoria": "comparativas",
        "descripcion": "Contraste entre dos rangos de fechas (ej. Q1 2025 vs Q1 2026)",
        "chart_types": ["bar", "table", "line"],
        "chart_default": "bar",
        "color": "#0D47A1",
        "icono": "compare",
        "requiere": [],
        "requiere_comparacion": True,
    },

    "TENDENCIA_MENSUAL": {
        "nombre": "Tendencia Mensual",
        "categoria": "comparativas",
        "descripcion": "Evolución de un indicador mes a mes",
        "chart_types": ["line", "area", "bar"],
        "chart_default": "line",
        "color": "#01579B",
        "icono": "trending_up",
        "requiere": [],
    },
}

CATEGORIAS_CATALOG = {
    "financiero":    {"nombre": "Financiero",              "icono": "account_balance"},
    "costos":        {"nombre": "Costos y Gastos",         "icono": "price_change"},
    "clientes":      {"nombre": "Cartera y Clientes",      "icono": "people"},
    "proveedores":   {"nombre": "Proveedores",             "icono": "local_shipping"},
    "proyectos":     {"nombre": "Proyectos",               "icono": "folder_special"},
    "comparativas":  {"nombre": "Comparativas",            "icono": "compare"},
}
```

### 8.3 Motor de Reportes

```python
# backend/apps/dashboard/report_engine.py
"""
Motor de generación de reportes a partir de MovimientoContable.
Cada método recibe company_id + filtros y retorna datos listos para graficar.
"""

class ReportEngine:

    def get_card_data(self, company_id: str, card_type_code: str, filtros: dict) -> dict:
        """
        Punto de entrada unificado. Despacha al método correcto según card_type_code.
        Retorna: {labels: [...], datasets: [{label, data, ...}], summary: {...}}
        """

    def _get_queryset_base(self, company_id: str, filtros: dict):
        """
        QuerySet base filtrado por:
        - company
        - fecha_desde / fecha_hasta
        - tercero_ids (lista de ID_N)
        - proyecto_codigos
        - departamento_codigos
        - ccost_codigos
        """

    def balance_general(self, company_id: str, filtros: dict) -> dict:
        """
        Agrupa MovimientoContable por titulo_codigo.
        Saldo = SUM(debito) - SUM(credito) o viceversa según naturaleza de la cuenta.
        Clasifica en: Activo, Pasivo, Patrimonio por rango de auxiliar.
        """

    def estado_resultados(self, company_id: str, filtros: dict) -> dict:
        """
        Ingresos (clase 4) - Costos (clase 6) - Gastos (clase 5) = Utilidad.
        Si comparar_periodo=True, incluye columna del período anterior.
        """

    def aging_cartera(self, company_id: str, filtros: dict) -> dict:
        """
        CxC agrupadas por días de vencimiento usando GL.DUEDATE.
        Buckets: Vigente, 1-30, 31-60, 61-90, +90 días.
        """

    def comparativo_periodos(self, company_id: str, filtros: dict) -> dict:
        """
        Ejecuta el mismo indicador para dos rangos de fecha.
        Retorna columnas lado a lado.
        """

    # ... un método por cada card type en CARD_CATALOG
```

### 8.4 API Endpoints Dashboard

```
# Dashboard CRUD
GET     /api/v1/dashboard/                              ← mis dashboards
POST    /api/v1/dashboard/                              ← crear dashboard
GET     /api/v1/dashboard/{id}/                        ← detalle
PUT     /api/v1/dashboard/{id}/                        ← actualizar
DELETE  /api/v1/dashboard/{id}/                        ← eliminar
POST    /api/v1/dashboard/{id}/set-default/            ← marcar como default
POST    /api/v1/dashboard/{id}/toggle-favorite/        ← marcar/desmarcar favorito
GET     /api/v1/dashboard/compartidos-conmigo/         ← dashboards compartidos

# Tarjetas
GET     /api/v1/dashboard/{id}/cards/                  ← tarjetas del dashboard
POST    /api/v1/dashboard/{id}/cards/                  ← agregar tarjeta
PUT     /api/v1/dashboard/{id}/cards/{card_id}/        ← actualizar tarjeta
DELETE  /api/v1/dashboard/{id}/cards/{card_id}/        ← eliminar tarjeta
POST    /api/v1/dashboard/{id}/cards/layout/           ← guardar posiciones (bulk)

# Compartir
POST    /api/v1/dashboard/{id}/share/                  ← compartir con usuario
DELETE  /api/v1/dashboard/{id}/share/{user_id}/        ← revocar acceso

# Datos de reportes (tiempo real)
POST    /api/v1/dashboard/report/card-data/            ← datos para una tarjeta
POST    /api/v1/dashboard/report/export-pdf/           ← genera datos para PDF

# Catálogo
GET     /api/v1/dashboard/catalog/cards/               ← catálogo de tarjetas
GET     /api/v1/dashboard/catalog/categories/          ← categorías disponibles

# Filtros disponibles (según config contable del tenant)
GET     /api/v1/dashboard/filters/terceros/            ← lista de terceros disponibles
GET     /api/v1/dashboard/filters/proyectos/           ← lista de proyectos
GET     /api/v1/dashboard/filters/departamentos/       ← lista de departamentos
GET     /api/v1/dashboard/filters/periodos/            ← períodos disponibles (YYYY-MM)

# Agente IA
POST    /api/v1/dashboard/ai-assistant/query/          ← pregunta al agente financiero
GET     /api/v1/dashboard/ai-assistant/history/        ← historial de consultas

# Trial License
POST    /api/v1/dashboard/trial/activate/              ← activar prueba 14 días
GET     /api/v1/dashboard/trial/status/                ← estado de la prueba

# Contabilidad (sync)
GET     /api/v1/contabilidad/sync/status/
POST    /api/v1/contabilidad/sync/gl-batch/
POST    /api/v1/contabilidad/sync/acct/
POST    /api/v1/contabilidad/sync/cust/
```

---

## 9. SISTEMA DE LICENCIAS — TRIAL

### 9.1 Lógica de acceso al módulo Dashboard

Flujo en `LicensePermission` (extender lógica existente):
```
1. ¿'dashboard' in company.license.modules_included? → PERMITIR
2. ¿Existe ModuleTrial(company, 'dashboard') y trial.esta_activo()? → PERMITIR (con banner)
3. ¿Existe ModuleTrial(company, 'dashboard') y trial VENCIDO? → DENEGAR (prueba agotada)
4. No existe trial → DENEGAR con opción de activar prueba
```

### 9.2 DashboardLicenseGuard (Angular)

```typescript
// Intercepta navegación a /dashboard
// Si no tiene acceso:
//   - Muestra modal de activación de prueba
//   - O muestra pantalla de "módulo no disponible"
// Si tiene prueba activa:
//   - Muestra banner "Prueba activa: X días restantes"
```

### 9.3 Integración en panel Super Admin

En la gestión de licencias del super admin (Valmen):
- Visualizar qué módulos tiene activos cada empresa
- Agregar/remover `'dashboard'` de `modules_included`
- Ver si una empresa usó su prueba o si aún no la ha activado

En el panel de Admin del tenant (company_admin):
- Ver módulos disponibles
- Activar prueba de módulos no contratados
- Ver días restantes de pruebas activas

---

## 10. PERMISOS Y ROLES

```python
# Permisos por rol para el módulo dashboard

DASHBOARD_PERMISSIONS = {
    'valmen_admin': {
        'ver': True, 'crear': True, 'editar': True, 'eliminar': True,
        'ver_otros': True, 'compartir': True, 'configurar_sync': True
    },
    'valmen_support': {
        'ver': True, 'crear': False, 'editar': False, 'eliminar': False,
        'ver_otros': True, 'compartir': False, 'configurar_sync': False
    },
    'company_admin': {
        'ver': True, 'crear': True, 'editar': True, 'eliminar': True,
        'ver_otros': True,  # puede ver dashboards compartidos dentro de su empresa
        'compartir': True, 'configurar_sync': True
    },
    'seller': {
        # seller es el único rol operativo (collector fue unificado en seller — DEC-023 refactoring)
        'ver': True, 'crear': True, 'editar': True, 'eliminar': True,
        'ver_otros': False,  # solo los suyos y compartidos con él
        'compartir': True, 'configurar_sync': False
    },
    'viewer': {
        'ver': True, 'crear': False, 'editar': False, 'eliminar': False,
        'ver_otros': False, 'compartir': False, 'configurar_sync': False
    },
}
```

**Regla de privacidad:** Los dashboards son privados por defecto.
Un usuario solo ve:
- Sus propios dashboards
- Los que alguien explícitamente compartió con él (DashboardShare)

---

## 11. FRONTEND ANGULAR — MÓDULO DASHBOARD

### 11.1 Dependencias npm a instalar

```bash
# Gráficos — ECharts (mejor soporte para dashboards financieros)
npm install echarts ngx-echarts

# Drag & Drop — ya viene con Angular CDK (ya instalado)
# @angular/cdk/drag-drop

# Resize de tarjetas
npm install angular-resizable-element

# PDF Export
npm install jspdf html2canvas

# Date picker avanzado con rangos (Angular Material ya incluye)
# mat-date-range-picker está disponible nativamente

# Iconos: ya configurados con Material Icons
```

### 11.2 Dashboard Builder

**Layout tipo cuadrícula:**
- Grid de 4 columnas × filas infinitas
- Tamaño de carta: 816px × 1056px (21.59cm × 27.94cm a 96dpi) o landscape: 1056px × 816px
- Tarjeta mínima: 1 col × 1 fila (204px × 264px)
- Tarjeta máxima: 4 col × 4 filas (816px × 1056px)
- Angular CDK DragDrop + CSS Grid para posicionamiento
- `angular-resizable-element` para redimensionar con handles

**Flujo del builder:**
1. Usuario abre Dashboard Builder (`/dashboard/builder/:id` o `/dashboard/nuevo`)
2. Panel izquierdo: catálogo de tarjetas por categoría (accordeon)
3. Panel central: canvas de página tamaño carta
4. Al hacer clic/drag desde catálogo → agrega tarjeta al canvas
5. Configuración de tarjeta: modal con selector de gráfico + filtros propios
6. Botón "Guardar Layout" → `POST /api/v1/dashboard/{id}/cards/layout/`
7. Preview en tiempo real mientras configura

**Componente DashboardBuilder:**
```typescript
// features/dashboard/components/dashboard-builder/
// - canvas con @angular/cdk/drag-drop
// - sidebar con mat-accordion (categorías) + mat-list (tarjetas)
// - ChangeDetectionStrategy.OnPush
// - Signal-based state para posiciones
// - ngx-echarts para preview de gráficos dentro de tarjetas
```

### 11.3 Panel de Filtros

```typescript
// features/dashboard/components/filter-panel/

interface ReportFilter {
    fecha_desde: string;      // YYYY-MM-DD
    fecha_hasta: string;      // YYYY-MM-DD
    tercero_ids: string[];
    proyecto_codigos: string[];
    departamento_codigos: number[];
    ccost_codigos: number[];

    // Comparación de períodos
    comparar_periodo: boolean;
    periodo_comparacion_desde: string | null;
    periodo_comparacion_hasta: string | null;
}
```

Componentes del panel de filtros:
- `mat-date-range-picker` para rangos de fecha
- Checkboxes de períodos rápidos: "Este mes", "Este trimestre", "Este año", "Año anterior"
- `mat-slide-toggle` para activar comparación de períodos
- `mat-autocomplete` para terceros (búsqueda por nombre)
- `mat-select` múltiple para proyectos, departamentos, CC

### 11.4 Selector de Tarjetas (CardSelector)

```
Modal con:
- Tabs por categoría (Financiero | Costos | Clientes | Proveedores | Proyectos | Comparativas)
- Grid de tarjetas con: ícono + nombre + descripción + chip de tipos de gráfico
- Tarjetas grises/deshabilitadas si requieren config que el tenant no tiene
  (ej: "requiere_departamentos_cc" y el tenant no lo usa)
- Filtro de búsqueda en tiempo real
- Al seleccionar: muestra config de la tarjeta (tipo de gráfico + filtros específicos)
```

### 11.5 Dashboard Viewer (modo lectura)

```
/dashboard/:id → Vista de solo lectura (también para dashboards compartidos)

Componentes:
- Header: título + menú (Editar | Compartir | Exportar PDF | Favorito)
- Banner de prueba si aplica: "⏳ Prueba activa: X días restantes"
- Grid de tarjetas readonly (no drag, no resize)
- Cada tarjeta muestra: título + gráfico (ngx-echarts) + botón "Expandir"
- Botón flotante "Aplicar Filtros" → despliega filter-panel
- Botón "Exportar PDF" → usa jsPDF + html2canvas para generar PDF carta
```

### 11.6 Home del Módulo Dashboard

```
/dashboard → Home

Secciones:
1. "Mis Favoritos" → Dashboards marcados como favorito (acceso rápido)
2. "Dashboard de Inicio" → El dashboard marcado como default (carga automático)
3. "Mis Dashboards" → Lista completa de dashboards propios
4. "Compartidos conmigo" → Dashboards que otros compartieron
5. Botón "Nuevo Dashboard" (solo roles con permiso crear)

Si tiene dashboard default → redirigir a /dashboard/:id automáticamente
```

### 11.7 Compartir Dashboard via Chat

```typescript
// Al presionar "Compartir" desde el Dashboard:
// 1. Selector de usuario (mismo tenant)
// 2. Opción A: Compartir internamente (DashboardShare) → el otro usuario lo ve en "Compartidos conmigo"
// 3. Opción B: Enviar por Chat → abre ChatPanel con link generado al dashboard
//    El link: https://app.saicloud.co/dashboard/:id?shared=true
//    En el chat se muestra como enlace con preview del título del dashboard
// La persona que recibe puede hacer clic y ver el dashboard (si tiene acceso al módulo)
```

### 11.8 Exportación PDF (Tamaño Carta)

```typescript
// El canvas del dashboard está dimensionado para carta
// export-pdf.service.ts:
async exportToPDF(dashboardId: string): Promise<void> {
    // 1. html2canvas → captura el canvas completo
    // 2. Si múltiples páginas (dashboard largo) → split automático
    // 3. jsPDF → crea PDF tamaño carta (a4 o letter)
    // 4. Incluye encabezado: nombre empresa + período + fecha de generación
    // 5. Descarga automática: Nombre_Dashboard_2026-04-01.pdf
}
```

### 11.9 PWA Offline (Fase 2 — No implementar en MVP)

**MARCAR como deuda técnica.** Implementar después de MVP:
- Service Worker para cachear respuestas de `/api/v1/dashboard/report/card-data/`
- IndexedDB para almacenar los datos del último refresh
- Banner de modo offline si no hay conexión

---

## 12. AGENTE IA FINANCIERO (n8n + Claude)

### 12.1 Diseño del Agente

**Nombre:** CFO Virtual SaiCloud
**Personalidad:** Consultor financiero experto en normativa colombiana (NIIF/PCGA), análisis de ratios, flujo de caja y salud financiera de PyMEs.
**Canal:** Widget integrado en el dashboard (botón "Consultar al CFO Virtual")

**Capacidades del agente:**
- Interpretar los KPIs actuales del dashboard del usuario
- Hacer comparaciones con períodos anteriores
- Alertar sobre ratios fuera de rango (liquidez < 1.0, endeudamiento > 70%, etc.)
- Responder preguntas en lenguaje natural sobre los datos financieros
- Dar recomendaciones accionables

### 12.2 Arquitectura n8n

```
Workflow: saidashboard-ai-assistant
Trigger: Webhook POST /webhook/dashboard-ai
Pasos:
1. Recibe: {user_id, company_id, dashboard_id, pregunta, kpis_actuales}
2. Llama Django API → obtiene datos del dashboard actual (top 5 KPIs)
3. Construye prompt con contexto financiero
4. Llama Claude API (claude-sonnet-4-6) con prompt + datos
5. Retorna respuesta al frontend
6. Guarda en historial (tabla en Django o Notion)
```

**Prompt del agente (sistema):**
```
Eres el CFO Virtual de SaiCloud, un asistente especializado en análisis
financiero para PyMEs colombianas. Tienes acceso a los indicadores financieros
de la empresa en tiempo real. Tu análisis se basa en:
- Normativa colombiana: NIIF para PyMEs (Decreto 3022 de 2013)
- PUC colombiano (Plan Único de Cuentas, Decreto 2650 de 1993)
- Estándares internacionales de análisis financiero

Cuando analices datos:
1. Identifica tendencias preocupantes proactivamente
2. Usa rangos de referencia colombianos (razón corriente saludable: 1.5-2.0)
3. Da recomendaciones concretas y accionables
4. Explica en lenguaje no técnico para gerencia

Responde siempre en español colombiano, de forma concisa y directa.
```

### 12.3 Componente Angular del Agente

```
features/dashboard/components/ai-assistant/
- Botón flotante "CFO Virtual" (distinto al FAB del chat)
- Panel lateral deslizante (similar a ChatPanel pero diferente)
- Campo de pregunta + botón enviar
- Historial de la conversación de la sesión
- Indicador de carga mientras Claude procesa
- Respuestas con formato markdown (ngx-markdown o similar)
- Acceso rápido: "¿Cómo está mi liquidez?", "¿Cuál es mi riesgo de endeudamiento?"
```

---

## 13. INTEGRACIÓN CON SISTEMA DE NOTIFICACIONES

Notificaciones automáticas a agregar (usando el sistema de notificaciones ya implementado):

| Evento | Notificación | Destinatario |
|--------|-------------|--------------|
| Prueba activada | "Prueba de SaiDashboard activa por 14 días" | Usuario que activó |
| 3 días antes de vencer prueba | "Tu prueba de SaiDashboard vence en 3 días" | Todos los admins |
| Dashboard compartido contigo | "Juan te compartió el dashboard 'Ventas Q1'" | Usuario receptor |
| Sync GL completado (primer sync) | "Datos contables sincronizados correctamente" | company_admin |
| Error de sync | "Error al sincronizar datos de Saiopen" | company_admin |
| Prueba vencida | "La prueba de SaiDashboard venció. Contacta a tu representante." | Todos los admins |

---

## 14. ORDEN DE EJECUCIÓN — 10 FASES PARA CLAUDE CODE

### FASE 1: Agente Go — Estructura, Multi-DB, Configurador y Sync GL ⏱️ (Día 1-3)

```
Archivos a crear:
□ agent-go/go.mod
□ agent-go/cmd/agent/main.go              (CLI con comandos: config|serve|install|uninstall|status|test)
□ agent-go/internal/config/config.go      (AgentConfig con []Connection; JSON R/W; watermark embebido)
□ agent-go/internal/firebird/client.go    (driver nakagami; query GL incremental basado en sql_gl.txt)
□ agent-go/internal/sync/orchestrator.go  (goroutine por conexión habilitada)
□ agent-go/internal/sync/gl_sync.go       (sync incremental por CONTEO, actualiza watermark en config)
□ agent-go/internal/sync/reference_sync.go (sync ACCT/CUST/LISTA/PROYECTOS/ACTIVIDADES)
□ agent-go/internal/sqs/publisher.go      (SQSMessage con conn_id para trazabilidad)
□ agent-go/internal/api/client.go         (cliente HTTP fallback)
□ agent-go/internal/configurator/server.go   (HTTP server :8765 + abrir browser automático)
□ agent-go/internal/configurator/handlers.go (CRUD conexiones + handler "probar conexión")
□ agent-go/internal/configurator/static/index.html  (lista de conexiones con estado)
□ agent-go/internal/configurator/static/form.html   (formulario agregar/editar + botón Examinar .fdb)
□ agent-go/internal/configurator/static/style.css
□ agent-go/internal/configurator/static/app.js
□ agent-go/internal/winsvc/service.go     (install/uninstall/run como Windows Service)
□ agent-go/Dockerfile                     (build cross-compile GOOS=windows GOARCH=amd64)
□ agent-go/README.md                      (guía instalación paso a paso para implementadores)
```

**Tests Go:**
```
□ agent-go/internal/config/config_test.go            (R/W multi-conexión, watermark actualizado)
□ agent-go/internal/sync/gl_sync_test.go             (con mock Firebird client)
□ agent-go/internal/configurator/handlers_test.go    (CRUD conexiones, test-connection mock)
```

### FASE 2: Django — App Contabilidad ⏱️ (Día 2-3)

```
Archivos a crear:
□ backend/apps/contabilidad/__init__.py
□ backend/apps/contabilidad/apps.py
□ backend/apps/contabilidad/models.py   (MovimientoContable, CuentaContable, ConfiguracionContable)
□ backend/apps/contabilidad/serializers.py
□ backend/apps/contabilidad/services.py (SyncService)
□ backend/apps/contabilidad/views.py    (sync endpoints)
□ backend/apps/contabilidad/urls.py
□ backend/apps/contabilidad/admin.py
□ backend/apps/contabilidad/migrations/0001_initial.py
□ backend/apps/contabilidad/tests/test_models.py
□ backend/apps/contabilidad/tests/test_services.py

Modificar:
□ backend/config/settings/base.py → agregar 'apps.contabilidad' a INSTALLED_APPS
□ backend/config/urls.py → include contabilidad.urls
```

### FASE 3: Django — App Dashboard (Backend) ⏱️ (Día 3-4)

```
Archivos a crear:
□ backend/apps/dashboard/__init__.py
□ backend/apps/dashboard/apps.py
□ backend/apps/dashboard/models.py    (Dashboard, DashboardCard, DashboardShare, ModuleTrial)
□ backend/apps/dashboard/card_catalog.py
□ backend/apps/dashboard/report_engine.py
□ backend/apps/dashboard/serializers.py
□ backend/apps/dashboard/services.py  (DashboardService, ReportService, TrialService)
□ backend/apps/dashboard/views.py
□ backend/apps/dashboard/urls.py
□ backend/apps/dashboard/admin.py
□ backend/apps/dashboard/migrations/0001_initial.py
□ backend/apps/dashboard/tests/test_models.py
□ backend/apps/dashboard/tests/test_services.py
□ backend/apps/dashboard/tests/test_views.py

Modificar:
□ backend/config/settings/base.py → agregar 'apps.dashboard'
□ backend/config/urls.py → include dashboard.urls
□ backend/apps/companies/services.py → LicenseService agregar soporte ModuleTrial
□ backend/apps/core/permissions.py → LicensePermission agregar check 'dashboard'
```

### FASE 4: Django — Integración Sistema de Notificaciones ⏱️ (Día 4)

```
Modificar:
□ backend/apps/notificaciones/ → agregar tipos de notificación de dashboard
   - DASHBOARD_TRIAL_ACTIVATED
   - DASHBOARD_TRIAL_EXPIRING
   - DASHBOARD_SHARED
   - DASHBOARD_SYNC_COMPLETED
   - DASHBOARD_SYNC_ERROR
   - DASHBOARD_TRIAL_EXPIRED
□ backend/apps/dashboard/services.py → NotificationService calls en eventos clave
```

### FASE 5: Angular — Modelos, Servicios y Routing ⏱️ (Día 5)

```
Archivos a crear:
□ frontend/src/app/features/dashboard/dashboard.module.ts
□ frontend/src/app/features/dashboard/dashboard-routing.module.ts
□ frontend/src/app/features/dashboard/models/dashboard.model.ts
□ frontend/src/app/features/dashboard/models/dashboard-card.model.ts
□ frontend/src/app/features/dashboard/models/card-catalog.model.ts
□ frontend/src/app/features/dashboard/models/report-filter.model.ts
□ frontend/src/app/features/dashboard/services/dashboard.service.ts
□ frontend/src/app/features/dashboard/services/report.service.ts
□ frontend/src/app/features/dashboard/services/card-catalog.service.ts
□ frontend/src/app/features/dashboard/guards/dashboard-license.guard.ts

Modificar:
□ frontend/src/app/app-routing.module.ts → lazy load /dashboard
□ frontend/src/app/features/home/modulos → agregar card del módulo Dashboard
```

### FASE 6: Angular — Componentes Core ⏱️ (Día 6-7)

```
Archivos a crear (por este orden):
□ dashboard-list/            ← Home del módulo
□ dashboard-viewer/          ← Vista de solo lectura (con filtros)
□ chart-card/                ← Tarjeta individual con ngx-echarts
□ kpi-card/                  ← Tarjeta tipo indicador numérico
□ filter-panel/              ← Panel de filtros con date range + comparación
□ card-selector/             ← Modal catálogo de tarjetas
□ dashboard-builder/         ← Editor con drag & drop + resize
□ share-dialog/              ← Modal para compartir (usuarios + chat)
□ ai-assistant/              ← Panel CFO Virtual
□ trial-banner/              ← Banner de prueba activa
```

**Instalación ngx-echarts:**
```bash
npm install echarts ngx-echarts
npm install angular-resizable-element
npm install jspdf html2canvas
```

### FASE 7: Revisión Final y Tests E2E ⏱️ (Día 8)

```
□ Cobertura backend: 80% mínimo en services.py (100% en TrialService y ReportEngine)
□ Cobertura Angular: 100% services, 70% components
□ Tests de integración: sync GL end-to-end (mock SQS → Django → PostgreSQL)
□ Test de license guard: trial activo, trial vencido, sin trial
□ Validación 4x4: Desktop+Light, Desktop+Dark, Mobile+Light, Mobile+Dark
□ Test de exportación PDF en múltiples navegadores
```

### FASE 8: Panel Admin (Django Admin) ⏱️ (Día 8)

```
□ Dashboard admin: listar, filtrar por empresa, ver tarjetas, stats de sync
□ MovimientoContable admin: solo lectura, filtros por empresa/período/cuenta
□ ConfiguracionContable admin: editable por valmen_admin
□ ModuleTrial admin: listar, ver estado, activar/desactivar manualmente
```

### FASE 9: Validación UI/UX según CHECKLIST-VALIDACION.md ⏱️ (Día 9)

```
□ Responsive Mobile (375px): Dashboard builder simplificado en mobile
□ Touch targets ≥ 44x44px en todos los botones
□ Tablas con class="table-responsive"
□ Dark mode: todas las tarjetas con var(--sc-*) sin colores hardcodeados
□ Estados vacíos: sc-empty-state cuando no hay dashboards / no hay datos
□ Loading states: mat-progress-bar sobre cada tarjeta mientras carga
□ Error states: snack-error si falla la carga de datos
```

**NOTA MOBILE PARA DASHBOARD BUILDER:**
En mobile (< 768px), el builder debe cambiar a modo "lista de tarjetas" en lugar de canvas drag-drop (el drag es muy difícil en touch). Mostrar un mensaje "Para crear y editar dashboards usa la versión desktop."

### FASE 10: Decisiones y Documentación ⏱️ (Día 9)

```
□ Agregar DEC-037 en DECISIONS.md: Estrategia de sync GL (denormalizado en PostgreSQL)
□ Agregar DEC-038 en DECISIONS.md: Agente Go para sync Saiopen
□ Agregar DEC-039 en DECISIONS.md: ngx-echarts como librería de gráficos
□ Agregar DEC-040 en DECISIONS.md: ModuleTrial independiente (no extender CompanyLicense)
□ Actualizar CONTEXT.md con estado del módulo
□ Crear docs/technical/SAIDASHBOARD-TECNICO.md
```

---

## 15. DECISIONES ARQUITECTÓNICAS A REGISTRAR

### DEC-037: Estrategia de almacenamiento GL — Denormalizado en PostgreSQL
**Problema:** GL tiene mucha data y Firebird se lentifica cuando hay usuarios activos.
**Decisión:** Almacenar movimientos GL completamente denormalizados en PostgreSQL (todos los joins pre-calculados). Índices compuestos para reportes comunes.
**Alternativas descartadas:** TimescaleDB (añade complejidad), joins en tiempo de consulta (lento).

### DEC-038: Agente Go para sync Saiopen (Criterio 3 cumplido)
**Decisión:** Ejecutable standalone Go en Windows del cliente. Sync incremental por CONTEO. SQS como buffer.
**Criterio Go:** Ejecutable standalone en PC del cliente. Python descartado por rendimiento con Firebird y mayor tamaño del binario.

### DEC-039: ngx-echarts como librería de gráficos para Dashboard
**Decisión:** ngx-echarts (Apache ECharts wrapper para Angular). Soporta: barras, líneas, torta, waterfall, gauge, área, heatmap. Mejor soporte para series financieras que Chart.js.
**Alternativas:** Chart.js (limitado para waterfall), ApexCharts (bueno pero sin wrapper oficial Angular 18), D3 (demasiado bajo nivel para MVP).

### DEC-040: ModuleTrial como modelo independiente (no extender CompanyLicense)
**Decisión:** Nuevo modelo `ModuleTrial` con unique_together(company, module_code). Garantiza que el trial se use UNA SOLA VEZ por módulo por empresa.
**Razón:** CompanyLicense ya está estabilizado (DEC-030). Agregar JSON de trials complicaría las migraciones existentes.

---

## 16. RESTRICCIONES ABSOLUTAS (de CLAUDE.md)

```
❌ NUNCA usar PrimeNG, Bootstrap, Tailwind — SOLO Angular Material
❌ NUNCA hardcodear colores CSS — usar var(--sc-*) siempre
❌ NUNCA lógica de negocio en views — solo en services.py
❌ NUNCA float para dinero — siempre Decimal/NUMERIC(15,2)
❌ NUNCA print() — siempre logger.info/warning/error
❌ NUNCA any en TypeScript — usar interfaces tipadas
❌ NUNCA suscripción manual sin unsubscribe — usar async pipe
❌ NUNCA modificar CLAUDE.md
❌ NUNCA commits con .env o credenciales
❌ NUNCA llamar directamente a Firebird desde Django — siempre el agente Go
❌ NUNCA fetch de reportes directamente desde Firebird — siempre desde PostgreSQL local
❌ NUNCA modificar MovimientoContable desde Django frontend — es READ-ONLY
```

---

## 17. ESTIMACIÓN DE ESFUERZO

| Fase | Componente | Días |
|------|-----------|------|
| 1 | Agente Go | 2 |
| 2 | Django Contabilidad | 1.5 |
| 3 | Django Dashboard | 2 |
| 4 | Notificaciones | 0.5 |
| 5 | Angular Servicios/Routing | 1 |
| 6 | Angular Componentes | 3 |
| 7 | Tests y Revisión | 1 |
| 8 | Panel Admin | 0.5 |
| 9 | Validación UI/UX | 1 |
| 10 | Documentación | 0.5 |
| **Total** | | **~13 días** |

**Estrategia de paralelización (Fase 4 de Metodología — Multi-Agentes):**
- Agente Backend: Fases 2, 3, 4
- Agente Go: Fase 1 (paralelo)
- Agente Frontend: Fases 5, 6 (inicia cuando Fase 2 tenga endpoints básicos)
- Agente Tests: Fase 7 (paralelo con finales de 3 y 6)

---

## 18. DATOS DE PRUEBA SUGERIDOS

Para el desarrollo y testing, crear fixtures o factories con:
- 1 empresa de prueba con `ConfiguracionContable.usa_departamentos_cc=True` y `usa_proyectos_actividades=True`
- 1 empresa de prueba con ninguna configuración (contabilidad simple)
- ~500 registros `MovimientoContable` en diferentes períodos (2025-01 a 2026-03)
- Plan de cuentas (CuentaContable) con estructura PUC colombiano básico
- 20 terceros de prueba

---

## 19. ESTRATEGIA MULTI-AGENTES (Fase 4 de Metodología)

Este módulo se ejecuta con **4 agentes especializados en paralelo**, coordinados por Claude Code como orquestador. Esta estrategia reduce el tiempo de ~13 días secuenciales a ~6-7 días.

---

### 19.1 Mapa de Agentes y Responsabilidades

```
┌─────────────────────────────────────────────────────────────────┐
│           CLAUDE CODE (ORQUESTADOR — modelo Opus)               │
│  Lee el plan completo, define contratos, lanza los 4 agentes    │
└────────┬──────────────┬──────────────┬──────────────┬───────────┘
         │              │              │              │
    ┌────▼────┐    ┌────▼────┐    ┌────▼────┐   ┌────▼────┐
    │AGENTE A │    │AGENTE B │    │AGENTE C │   │AGENTE D │
    │Agente Go│    │Backend  │    │Frontend │   │Tests    │
    │(agent-go│    │Django   │    │Angular  │   │E2E      │
    │/ dir)   │    │         │    │         │   │         │
    └────┬────┘    └────┬────┘    └────┬────┘   └────┬────┘
         │              │              │              │
         │         ─────▼──────        │              │
         │         Sync endpoints ─────►              │
         │         (contrato API) ─────► usa para     │
         │                              servicios TS  │
         │                                            │
         └────────────── SQS format ──────────────────►
                         (contrato msg)
```

---

### 19.2 Contratos de Interfaz (definir ANTES de lanzar agentes)

El orquestador debe definir estos contratos al inicio. Los agentes los respetan sin desviarse.

#### Contrato A→B: Formato de mensaje SQS (Go → Django)

```json
{
  "type": "gl_batch",
  "company_id": "uuid-string",
  "conn_id": "conn_001",
  "timestamp": "2026-04-01T15:00:00Z",
  "data": {
    "records": [
      {
        "conteo": 458920,
        "fecha": "2026-03-15",
        "duedate": "2026-04-15",
        "invc": "FV-001234",
        "tercero_id": "800123456",
        "tercero_nombre": "Cliente ABC S.A.S",
        "auxiliar": 130505.01,
        "auxiliar_nombre": "Cuentas por cobrar clientes",
        "titulo_codigo": 1,
        "titulo_nombre": "ACTIVO",
        "grupo_codigo": 13,
        "grupo_nombre": "DEUDORES",
        "cuenta_codigo": 1305,
        "cuenta_nombre": "CLIENTES",
        "subcuenta_codigo": 130505,
        "subcuenta_nombre": "NACIONALES",
        "debito": "1500000.00",
        "credito": "0.00",
        "tipo": "FV",
        "batch": 1234,
        "descripcion": "Venta mercancía cliente ABC",
        "periodo": "2026-03",
        "departamento_codigo": null,
        "departamento_nombre": "",
        "centro_costo_codigo": null,
        "centro_costo_nombre": "",
        "proyecto_codigo": null,
        "proyecto_nombre": "",
        "actividad_codigo": null,
        "actividad_nombre": ""
      }
    ],
    "last_conteo": 458920,
    "batch_count": 1
  }
}
```

#### Contrato B→C: Endpoints API que el Frontend consume

```
# Los endpoints que Agente C (Frontend) usará desde los servicios Angular:

GET  /api/v1/dashboard/                              → DashboardListSerializer
POST /api/v1/dashboard/                              → DashboardCreateSerializer
GET  /api/v1/dashboard/{id}/                         → DashboardDetailSerializer
PUT  /api/v1/dashboard/{id}/                         → DashboardUpdateSerializer
DELETE /api/v1/dashboard/{id}/

POST /api/v1/dashboard/{id}/set-default/             → { success: bool }
POST /api/v1/dashboard/{id}/toggle-favorite/         → { is_favorito: bool }
GET  /api/v1/dashboard/compartidos-conmigo/          → [DashboardSharedSerializer]

GET  /api/v1/dashboard/{id}/cards/                   → [DashboardCardSerializer]
POST /api/v1/dashboard/{id}/cards/                   → DashboardCardSerializer
PUT  /api/v1/dashboard/{id}/cards/{card_id}/         → DashboardCardSerializer
DELETE /api/v1/dashboard/{id}/cards/{card_id}/
POST /api/v1/dashboard/{id}/cards/layout/            → { saved: N }

POST /api/v1/dashboard/{id}/share/                   → { shared: bool }
DELETE /api/v1/dashboard/{id}/share/{user_id}/       → { removed: bool }

POST /api/v1/dashboard/report/card-data/             → CardDataResponse
GET  /api/v1/dashboard/catalog/cards/                → [CardCatalogItem]
GET  /api/v1/dashboard/catalog/categories/           → [CategoryItem]
GET  /api/v1/dashboard/filters/terceros/?q=          → [{ id, nombre }]
GET  /api/v1/dashboard/filters/proyectos/            → [{ codigo, nombre }]
GET  /api/v1/dashboard/filters/departamentos/        → [{ codigo, nombre }]
GET  /api/v1/dashboard/filters/periodos/             → [{ periodo, label }]

POST /api/v1/dashboard/ai-assistant/query/           → { response: string, history_id: uuid }
GET  /api/v1/dashboard/trial/status/                 → TrialStatusResponse
POST /api/v1/dashboard/trial/activate/               → TrialActivateResponse

# Formatos clave de response:
CardDataResponse: {
  "card_type": "BALANCE_GENERAL",
  "chart_type": "bar",
  "labels": ["Activo", "Pasivo", "Patrimonio"],
  "datasets": [{ "label": "2026-Q1", "data": [45000000, 20000000, 25000000] }],
  "summary": { "total_activo": 45000000, "total_pasivo": 20000000 },
  "periodo_comparacion": null,
  "generado_en": "2026-04-01T15:30:00Z"
}

TrialStatusResponse: {
  "tiene_acceso": true,
  "tipo_acceso": "trial",  // "licencia" | "trial" | "sin_acceso" | "trial_vencido"
  "dias_restantes": 12,
  "expira_en": "2026-04-15T00:00:00Z"
}
```

---

### 19.3 Condiciones de Inicio por Agente

| Agente | Puede iniciar cuando... | Bloqueado por... |
|--------|------------------------|------------------|
| **A — Go** | Inmediatamente (nada depende de él para empezar) | — |
| **B — Backend** | Inmediatamente en paralelo con A | — |
| **C — Frontend** | Cuando B tenga modelos + al menos 5 endpoints funcionando | Agente B (parcial) |
| **D — Tests** | Cuando B y C estén ~80% completos | Agentes B y C |

**Punto de sincronización obligatorio:**
Antes de que el Agente C inicie, el orquestador verifica que el Agente B haya creado:
- `apps/contabilidad/models.py` con `MovimientoContable`
- `apps/dashboard/models.py` con `Dashboard`, `DashboardCard`
- Los serializers básicos
- Al menos los endpoints: `GET /dashboard/`, `POST /dashboard/`, `GET /catalog/cards/`

---

### 19.4 Archivos Propiedad de Cada Agente (sin conflictos)

Cada agente es dueño exclusivo de sus archivos. **Nunca dos agentes modifican el mismo archivo.**

#### Agente A — Go (agent-go/)
```
agent-go/**              ← Todo el directorio es exclusivo del Agente A
```

#### Agente B — Backend Django
```
backend/apps/contabilidad/**       ← Exclusivo
backend/apps/dashboard/**          ← Exclusivo
backend/config/settings/base.py    ← Solo agrega INSTALLED_APPS (comunicar al orquestador)
backend/config/urls.py             ← Solo agrega include() (comunicar al orquestador)
backend/apps/companies/services.py ← Solo agrega check de trial en LicenseService
backend/apps/core/permissions.py   ← Solo agrega check 'dashboard' en LicensePermission
backend/apps/notificaciones/       ← Solo agrega tipos de notificación
```

#### Agente C — Frontend Angular
```
frontend/src/app/features/dashboard/**     ← Todo el módulo dashboard es exclusivo
frontend/src/app/app-routing.module.ts     ← Solo agrega la ruta lazy /dashboard
frontend/src/app/features/home/            ← Solo agrega card del módulo Dashboard
```

#### Agente D — Tests E2E / Integration
```
backend/apps/contabilidad/tests/**   ← Puede crear nuevos tests
backend/apps/dashboard/tests/**      ← Puede crear nuevos tests
frontend/src/app/features/dashboard/**/*.spec.ts  ← Solo archivos .spec.ts
docs/reports/INFORME_SAIDASHBOARD_*.md   ← Genera el informe final
```

---

### 19.5 Instrucciones de Lanzamiento para el Orquestador

Claude Code lanza los agentes con estas instrucciones exactas por agente. El orquestador usa la herramienta `Task` de Claude Code:

#### Instrucción para Agente A (Go)
```
Eres el Agente A del módulo SaiDashboard. Tu responsabilidad es construir el agente Go
de sincronización en agent-go/

Lee OBLIGATORIAMENTE antes de escribir código:
1. CLAUDE.md (sección 10 — criterios Go)
2. DECISIONS.md (DEC-038)
3. docs/plans/PLAN-SAIDASHBOARD.md (secciones 6 completa + 19.2 contrato SQS)
4. docs/saiopen/gl.txt + sql_gl.txt

Usa el skill: saicloud-microservicio-go

Tu entregable: agent-go/ completo y compilando (GOOS=windows go build ./...)
Cuando termines: crear docs/reports/AGENTE-A-COMPLETADO.md con lista de archivos creados.
NO modificar nada fuera de agent-go/
```

#### Instrucción para Agente B (Backend Django)
```
Eres el Agente B del módulo SaiDashboard. Tu responsabilidad es el backend Django:
apps/contabilidad/ y apps/dashboard/

Lee OBLIGATORIAMENTE antes de escribir código:
1. CLAUDE.md
2. DECISIONS.md (DEC-037, DEC-040)
3. docs/plans/PLAN-SAIDASHBOARD.md (secciones 5, 7, 8, 9, 10, 13 + contratos 19.2)
4. docs/base-reference/Estandares_Codigo_SaiSuite_v1.docx

Usa los skills: saicloud-backend-django + saicloud-pruebas-unitarias

Tu entregable:
- apps/contabilidad/ completo con migraciones
- apps/dashboard/ completo con migraciones
- Todos los endpoints del contrato B→C funcionando
- Tests: cobertura ≥80% services, ≥100% TrialService y ReportEngine

Al terminar: crear docs/reports/AGENTE-B-COMPLETADO.md
NO modificar archivos fuera de tu scope (ver sección 19.4)
```

#### Instrucción para Agente C (Frontend Angular)
```
Eres el Agente C del módulo SaiDashboard. Tu responsabilidad es el módulo Angular.

PREREQUISITO: Verificar que existan los archivos del Agente B antes de iniciar:
- backend/apps/dashboard/models.py
- backend/apps/dashboard/serializers.py

Lee OBLIGATORIAMENTE antes de escribir código:
1. CLAUDE.md (especialmente DEC-011: Angular Material, NUNCA PrimeNG)
2. docs/standards/UI-UX-STANDARDS.md
3. docs/base-reference/CHECKLIST-VALIDACION.md
4. docs/plans/PLAN-SAIDASHBOARD.md (secciones 11 completa + contratos 19.2)

Usa el skill: saicloud-frontend-angular + saicloud-validacion-ui

Instalar dependencias npm:
npm install echarts ngx-echarts angular-resizable-element jspdf html2canvas

Tu entregable: features/dashboard/ completo con validación 4x4 (Desktop+Mobile × Light+Dark)

Al terminar: crear docs/reports/AGENTE-C-COMPLETADO.md
NO modificar archivos fuera de tu scope (ver sección 19.4)
```

#### Instrucción para Agente D (Tests + Informe)
```
Eres el Agente D del módulo SaiDashboard. Tu responsabilidad es los tests de integración
y el informe final.

PREREQUISITO: Verificar que existan:
- backend/apps/contabilidad/tests/ con al menos test_models.py
- backend/apps/dashboard/tests/ con al menos test_services.py
- frontend/src/app/features/dashboard/ con al menos dashboard.service.spec.ts

Lee OBLIGATORIAMENTE:
1. CLAUDE.md
2. docs/plans/PLAN-SAIDASHBOARD.md (sección 17 — verificación final + 14 — Fases 7)
3. docs/base-reference/CHECKLIST-VALIDACION.md

Usa el skill: saicloud-pruebas-unitarias + saicloud-revision-final

Tu entregable:
- Todos los tests pasando (backend + frontend)
- Cobertura: ≥80% backend, ≥70% components Angular, 100% services Angular
- Checklist de verificación completo (sección 17 del plan)
- Informe: docs/reports/INFORME_SAIDASHBOARD_2026-04-XX.md

Al terminar: mover docs/plans/PLAN-SAIDASHBOARD.md → docs/plans/historic/
            actualizar docs/plans/INDICE-PLANES.md
```

---

### 19.6 Secuencia de Lanzamiento Recomendada

```
Día 1 (mañana):
  → Orquestador: lee CLAUDE.md + este plan + define contratos
  → LANZAR EN PARALELO: Agente A + Agente B

Día 1 (tarde) / Día 2:
  → Orquestador: verifica que Agente B tenga modelos básicos + 5 endpoints
  → LANZAR: Agente C (puede trabajar en paralelo con B que continúa)

Día 2-3:
  → Agente A sigue construyendo configurador + tests Go
  → Agente B completa services + admin + notificaciones
  → Agente C construye componentes Angular

Día 4:
  → LANZAR: Agente D (cuando A, B, C estén ~80% completados)
  → Agente D ejecuta tests, genera informe

Día 5 (si hace falta):
  → Orquestador resuelve conflictos de integración
  → Validación 4x4 final
  → Deploy checklist (skill: saicloud-revision-final)
```

---

### 19.7 Resolución de Conflictos de Integración

Si un agente detecta que necesita un archivo que pertenece a otro agente:
1. **NO modificarlo directamente**
2. Crear un archivo `PENDIENTE-[NOMBRE].md` en `docs/plans/` describiendo qué falta
3. El orquestador recoge esos pendientes y los resuelve en la fase de integración

Ejemplo de conflicto común: el Agente C necesita que `LicensePermission` soporte 'dashboard' (archivo del Agente B). C crea `docs/plans/PENDIENTE-LICENSE-DASHBOARD.md` y el orquestador lo coordina.

---

*Fin del plan PLAN-SAIDASHBOARD v1.1*
*Preparado por Cowork — 2026-04-01 (v1.0) / Actualizado 2026-04-01 (v1.1: multi-agentes)*
*Para ejecutar: Claude Code CLI con modelo Opus, leer este plan + CLAUDE.md antes de generar código*
