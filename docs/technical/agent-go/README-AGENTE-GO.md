# Saicloud Agent — Agente de Sincronización Saiopen

> **Versión:** 2.0.0
> **Lenguaje:** Go 1.22+
> **Plataforma:** Windows 10/11 (binario `.exe` standalone)
> **Plan de implementación:** [PLAN-SAIDASHBOARD.md](../../plans/PLAN-SAIDASHBOARD.md) — Sección 6
> **Reemplaza:** README-AGENTE-GO-v1.md (arquitectura de sync bidireccional de proyectos)

---

## Descripción

Agente de sincronización **Saiopen → Saicloud** para el módulo SaiDashboard.

Lee el movimiento contable (tabla GL) y tablas de referencia (ACCT, CUST, LISTA, PROYECTOS, ACTIVIDADES) desde Firebird 2.5 local y los envía a Saicloud (PostgreSQL en AWS) vía AWS SQS, de manera incremental y sin afectar el rendimiento de Saiopen.

**Soporte multi-empresa:** Un mismo servidor Windows puede tener N bases de datos Saiopen (empresas hermanas). El agente gestiona todas en paralelo, cada una amarrada a su propio tenant en Saicloud.

---

## Por qué Go (Criterios cumplidos)

Según la arquitectura híbrida Django+Go del proyecto ([CLAUDE.md](../../../../CLAUDE.md) Sección 10):

| Criterio | Estado | Detalle |
|----------|--------|---------|
| Criterio 1: Alta concurrencia >1000 req/s | ❌ | No aplica |
| Criterio 2: Batch >50k registros | ✅ parcial | Lotes de 500 GL por ciclo, empresas grandes |
| **Criterio 3: Ejecutable standalone** | ✅✅ **CRÍTICO** | Binario en PC del cliente Windows |
| Criterio 4: Ahorro costos >50% | ❌ | No aplica |

**Criterio 3 es determinante:** El agente debe instalarse en el PC Windows del cliente donde corre Saiopen. No puede depender de Python/Django porque:
- Python requiere instalador de 50-100MB + virtualenv + gestión de dependencias
- El agente debe correr 24/7 como servicio Windows invisible para el usuario
- El soporte se complica exponencialmente con entornos Python en Windows cliente

Go produce un binario de ~15MB sin dependencias externas, distribuible con un doble clic.

---

## Arquitectura

```
┌──────────────────────────────────────────────────────────┐
│               Saicloud (Django REST API en AWS)          │
│                      PostgreSQL                          │
└────────────────▲──────────────────────────────────────────┘
                 │ POST /api/v1/contabilidad/sync/*
                 │ (Django SQS Consumer procesa mensajes)
                 │
         ┌───────┴──────────────┐
         │     AWS SQS          │
         │  saicloud-gl-sync    │
         └───────▲──────────────┘
                 │ Publish SQSMessage
                 │
┌────────────────┴──────────────────────────────────────────┐
│              Saicloud Agent (Go .exe en Windows)          │
│                                                           │
│  ┌────────────────────┐  ┌────────────────────────────┐  │
│  │  Conexión Empresa1 │  │  Conexión Empresa2 (opt.)  │  │
│  │  goroutine propio  │  │  goroutine propio          │  │
│  └─────────┬──────────┘  └───────────┬────────────────┘  │
│            │ SQL directo             │ SQL directo        │
└────────────┼─────────────────────────┼───────────────────┘
             │                         │
   ┌─────────▼──────────┐   ┌──────────▼──────────┐
   │ Firebird empresa1  │   │ Firebird empresa2   │
   │ GL, ACCT, CUST...  │   │ GL, ACCT, CUST...   │
   └────────────────────┘   └─────────────────────┘
```

---

## Configuración (multi-empresa)

El agente se configura desde un **UI web local** (ver Configurador más abajo). La configuración se guarda en `saicloud-agent.json`:

```json
{
  "agent_version": "2.0.0",
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
        "company_id": "uuid-empresa-en-saicloud",
        "agent_token": "jwt-token-del-tenant"
      },
      "sync": {
        "gl_interval_minutes": 15,
        "reference_interval_hours": 24,
        "batch_size": 500,
        "last_conteo_gl": 0,
        "last_sync_acct": null
      }
    }
  ]
}
```

**Importante:** `last_conteo_gl = 0` dispara sync inicial completo. El agente actualiza este campo automáticamente después de cada batch exitoso. Es el watermark de sincronización.

---

## Comandos

```bash
agent.exe config       # Abre el configurador web en http://localhost:8765
agent.exe serve        # Inicia el servicio de sincronización
agent.exe install      # Registra como Windows Service (arranque automático)
agent.exe uninstall    # Elimina el Windows Service
agent.exe status       # Muestra estado de todas las conexiones
agent.exe test --id conn_001   # Prueba conexión sin hacer sync real
```

---

## Configurador Web (para implementadores)

El configurador web es una interfaz HTML embebida en el binario (via `go:embed`). El implementador no necesita editar JSON manualmente.

**Acceso:** `agent.exe config` → se abre `http://localhost:8765` en el navegador automáticamente.

**Pantalla principal:**
```
┌──────────────────────────────────────────────────────────┐
│  🔵 SaiCloud Agent — Configurador v2.0                   │
├──────────────────────────────────────────────────────────┤
│  Conexiones:                                             │
│  ┌────────────────────────────────────────────────────┐  │
│  │ ✅ Empresa Principal S.A.S   [Editar] [Probar]    │  │
│  │    Última sync: hace 3 min · 1,234 registros GL   │  │
│  └────────────────────────────────────────────────────┘  │
│  [+ Agregar empresa]                                     │
│  Estado: ✅ Corriendo · [Ver Logs] [Instalar Servicio]   │
└──────────────────────────────────────────────────────────┘
```

**Formulario de conexión:**
- Nombre de la empresa
- Ruta de la DB Firebird con botón **📂 Examinar...** (abre explorador Windows)
- Host y puerto Firebird
- Token del tenant (copiado desde SaiCloud → Configuración → Agente)
- Botón **🔍 Probar conexión** antes de guardar

---

## Instalación para el implementador (5 pasos)

```
1. Obtener token del tenant
   En SaiCloud: Configuración → Agente Go → Generar Token
   (El admin de la empresa lo hace)

2. Instalar el agente
   Descargar SaicloudAgentSetup.exe desde el portal de Valmen
   Ejecutar → Next → Next → Finish (instala en C:\SaicloudAgent\)

3. Abrir el configurador
   Doble clic en "SaiCloud Configurador" (acceso directo en escritorio)
   Se abre http://localhost:8765 en el navegador

4. Configurar cada empresa
   + Agregar empresa → completar formulario → 📂 Examinar .fdb →
   pegar token → 🔍 Probar → ✅ todo verde → 💾 Guardar
   (repetir por cada empresa/base de datos)

5. Instalar como servicio
   En el configurador → "Instalar Servicio Windows"
   El agente inicia inmediatamente y arranca automático con Windows
```

---

## Sincronización GL (incremental)

El movimiento contable se sincroniza de forma incremental usando `GL.CONTEO` como watermark:

```sql
-- Query base (derivado de docs/saiopen/sql_gl.txt)
SELECT G.CONTEO, G.FECHA, G.DUEDATE, ...
FROM GL G
INNER JOIN CUST C ON C.ID_N = G.ID_N
INNER JOIN ACCT A ON A.ACCT = G.ACCT
-- ... (joins completos de jerarquía PUC)
LEFT JOIN LISTA LD ON LD.CODIGO = G.DEPTO AND LD.TIPO='DP'
LEFT JOIN LISTA LC ON LC.CODIGO = G.CCOST AND LC.TIPO='CC'
LEFT JOIN PROYECTOS P ON P.CODIGO = G.PROYECTO
LEFT JOIN ACTIVIDADES AC ON AC.CODIGO = G.ACTIVIDAD
WHERE G.CONTEO > ?    -- watermark
ORDER BY G.CONTEO ASC
ROWS 1 TO 500         -- batch_size
```

Los registros GL **nunca se modifican retroactivamente** (naturaleza de la contabilidad), así que el watermark por CONTEO es completamente seguro.

---

## Tablas de Referencia (sync completo cada 24h)

| Tabla Firebird | Propósito | Frecuencia |
|---------------|-----------|-----------|
| ACCT | Plan de cuentas (PUC jerarquía) | Cada 24h |
| CUST | Terceros (clientes, proveedores) | Cada 24h |
| LISTA | Departamentos y Centros de Costo | Cada 24h |
| PROYECTOS | Proyectos contables | Cada 24h |
| ACTIVIDADES | Actividades de proyectos | Cada 24h |

---

## Auto-actualización

El agente verifica nuevas versiones cada 24h:
1. `GET https://api.saicloud.co/api/v1/sync/version/`
2. Si hay nueva versión: descarga desde S3, verifica SHA256, reemplaza binario, reinicia servicio
3. Si falla: rollback automático a versión anterior

---

## Seguridad

- **JWT:** Todos los requests a Saicloud API usan el `agent_token` (JWT con claim `role: sync_agent`)
- **Firebird:** Solo lectura en GL, ACCT, CUST, LISTA, PROYECTOS, ACTIVIDADES. Sin permisos DDL.
- **HTTPS:** Toda comunicación con Saicloud es HTTPS con certificado validado
- **Logs:** En `C:\SaicloudAgent\logs\` — rotación automática (7 días, 50MB máx) — sin datos sensibles

---

## Logs y monitoreo

```powershell
# Ver logs en tiempo real
Get-Content -Path "C:\SaicloudAgent\logs\agent.log" -Wait
```

Estado del agente desde Saicloud:
```bash
GET /api/v1/contabilidad/sync/status/
Authorization: Bearer {agent_token}
```

```json
{
  "connections": [
    {
      "id": "conn_001",
      "name": "Empresa Principal S.A.S",
      "status": "running",
      "last_sync": "2026-04-01T14:30:00Z",
      "last_conteo_gl": 458920,
      "registros_sincronizados": 458920,
      "errors_24h": 0
    }
  ]
}
```

---

## Troubleshooting

**El servicio no inicia:**
1. Verificar que Firebird esté corriendo: `services.msc` → Firebird Guardian
2. Verificar conectividad: `ping api.saicloud.co`
3. Revisar logs: `C:\SaicloudAgent\logs\agent.log`
4. Verificar permisos del .exe (debe poder escribir en su directorio)

**No sincroniza GL:**
1. Verificar que `enabled: true` en la conexión (configurador web)
2. Verificar que el usuario Firebird tenga SELECT en GL, CUST, ACCT
3. Buscar en logs mensajes `ERROR firebird:` o `ERROR sqs:`
4. Usar `agent.exe test --id conn_001` para diagnosticar

**Error de JWT / 401:**
1. El token puede haber expirado → regenerar en SaiCloud → Admin → Agente
2. Verificar que la hora del sistema Windows esté sincronizada (NTP)
3. Abrir configurador → Editar conexión → Pegar nuevo token → Guardar

---

## Desarrollo local

### Requisitos
- Go 1.22+
- Firebird 2.5 instalado localmente (para testing)
- Saicloud API corriendo en `http://localhost:8000`
- AWS CLI configurado (para SQS local con LocalStack, opcional)

### Setup
```bash
cd agent-go
go mod download
cp saicloud-agent.example.json saicloud-agent.json
# Editar saicloud-agent.json con credenciales locales
go run cmd/agent/main.go config  # Abrir configurador
go run cmd/agent/main.go serve   # Iniciar sync
```

### Build producción (Windows desde cualquier OS)
```bash
GOOS=windows GOARCH=amd64 go build -ldflags="-s -w" -o dist/agent.exe ./cmd/agent/
```

### Tests
```bash
go test ./...                              # Todos los tests
go test -tags=integration ./...            # Con Firebird local
go test -v ./internal/configurator/...    # Solo configurador
```

### Build del instalador NSIS
```bash
# Compilar binario
GOOS=windows GOARCH=amd64 go build -ldflags="-s -w" -o dist/agent.exe ./cmd/agent/
# Compilar instalador
makensis install/setup.nsi
# Output: dist/SaicloudAgentSetup.exe
```

---

## Referencia técnica

- **Plan completo:** [PLAN-SAIDASHBOARD.md — Sección 6](../../plans/PLAN-SAIDASHBOARD.md)
- **Decisión arquitectónica:** DEC-038 en [DECISIONS.md](../../../../DECISIONS.md)
- **Driver Firebird:** [github.com/nakagami/firebirdsql](https://github.com/nakagami/firebirdsql)
- **SQL base GL:** [docs/saiopen/sql_gl.txt](../../saiopen/sql_gl.txt)
- **Versión anterior (sync bidireccional proyectos):** [README-AGENTE-GO-v1.md](README-AGENTE-GO-v1.md)

---

*ValMen Tech © 2026 — Saicloud*
*Actualizado: 2026-04-01 | Arquitectura: multi-empresa + configurador web + sync GL*
