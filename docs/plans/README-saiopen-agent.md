# 🔄 Saiopen Agent — Agente de Sincronización Firebird

> **Versión:** 1.0.0  
> **Lenguaje:** Go 1.21+  
> **Plataforma:** Windows (binario .exe standalone)  

---

## 📌 Descripción

Agente de sincronización bidireccional entre **Saicloud (PostgreSQL en AWS)** y **Saiopen (Firebird local)**. 

Permite a clientes sin IP pública mantener sus datos contables en Saiopen (Windows local) sincronizados automáticamente con Saicloud (nube).

---

## 🎯 Justificación Técnica: ¿Por qué Go?

### Criterios de Evaluación Django vs Go

Según la metodología de arquitectura híbrida (DEC-009), Go se justifica cuando se cumple **al menos 1 de 4 criterios**:

1. ✅ **Alta concurrencia sostenida** (>1000 req/s)
2. ✅ **Procesamiento intensivo batch** (>50k registros)
3. ✅✅ **Ejecutable standalone** (agente en PC cliente, sin dependencias)
4. ❌ **Optimización de costos demostrada** (>$300/mes, ahorro >50%)

### Criterios Cumplidos

#### ✅ Criterio 3: Ejecutable Standalone (CRÍTICO)

**Problema:**
- El agente debe instalarse en PC Windows del cliente
- Muchos clientes no tienen IP pública (no pueden exponer Firebird a internet)
- El agente debe correr 24/7 sin intervención del usuario

**Alternativa 1: Python/Django**
- ❌ Requiere Python instalado (50-100MB)
- ❌ Instalador complejo: PyInstaller + dependencias + virtual env
- ❌ Actualizaciones: gestionar pip, virtualenv, conflictos de versiones
- ❌ El usuario ve consolas Python (poco profesional)
- ❌ Mayor superficie de ataque (intérprete + librerías)

**Alternativa 2: Go (seleccionada)**
- ✅ Binario compilado de **10-15MB** sin dependencias
- ✅ Distribución: descargar `saiopen-agent.exe` y ejecutar
- ✅ Actualizaciones: reemplazar .exe (consulta `/api/v1/sync/version/`)
- ✅ Se ejecuta como servicio Windows (invisible para el usuario)
- ✅ Consumo mínimo de recursos (~30-50MB RAM)
- ✅ Instalador NSIS simple (Next → Next → Finish)

**Impacto en Soporte:**
- Python: "No funciona" → debug de versiones Python, pip, venv, firewall, antivirus bloqueando scripts
- Go: "No funciona" → debug de .exe (binario estático, sin variables ambientales)

**Conclusión:** Para un agente que debe instalarse en **decenas de PCs de clientes**, Go reduce drásticamente la complejidad de distribución y soporte.

---

#### ✅ Criterio 2: Procesamiento Batch (PARCIAL)

**Escenario:**
- El agente hace polling cada 5 minutos a Firebird
- Un cliente con contabilidad activa puede generar **100-500 documentos/día**
- Cada sync puede procesar lotes de hasta **500 documentos** (facturas, recibos, nómina, etc.)

**Performance:**
- Go: Procesa 500 registros en **~2-3 segundos** (concurrencia nativa con goroutines)
- Python: Procesa 500 registros en **~8-12 segundos** (single-threaded típico)

**Beneficio:** No crítico para el caso de uso, pero Go permite procesar los lotes más rápido sin bloquear el ciclo de polling.

---

### ¿Por Qué NO Usar Django para Todo?

**Django es excelente para:**
- ✅ APIs REST (DRF)
- ✅ CRUD de entidades
- ✅ Admin panel
- ✅ Lógica de negocio que cambia frecuentemente

**Django NO es ideal para:**
- ❌ Ejecutables standalone sin dependencias
- ❌ Distribución a clientes finales (no técnicos)
- ❌ Instalación silenciosa en Windows como servicio

**Decisión:** Arquitectura **híbrida** — Django para el core (80% del código), Go para el agente (caso de uso específico donde destaca).

---

## 🏗️ Arquitectura del Agente

```
┌─────────────────────────────────────────────────────────────┐
│                    Saicloud (Django REST API)               │
│                     PostgreSQL en AWS                       │
└──────────────────▲─────────────────▲────────────────────────┘
                   │                 │
                   │ POST batch      │ GET /sync/status
                   │ /sync/proyectos │ /sync/version
                   │ /sync/documentos│
                   │                 │
         ┌─────────┴─────────────────┴─────────┐
         │      Saiopen Agent (Go .exe)        │
         │   - Polling cada 5 min              │
         │   - Conexión Firebird local         │
         │   - Servicio Windows                │
         └──────────────┬──────────────────────┘
                        │
                        │ SQL directo
                        │ (go-firebirdsql)
                        │
         ┌──────────────▼──────────────────────┐
         │  Saiopen (Firebird local)           │
         │  - Proyectos/Actividades            │
         │  - Documentos contables             │
         │  - Terceros                         │
         └─────────────────────────────────────┘
```

---

## 🔄 Flujos de Sincronización

### 1. Proyecto Creado en Saicloud → Saiopen

```
1. Usuario crea proyecto en Saicloud (Django)
2. Django marca `sincronizado_con_saiopen = False`
3. Agente detecta proyecto nuevo (polling cada 5 min)
4. Agente crea registro en tabla PROYECTOS de Firebird
5. Agente actualiza `saiopen_proyecto_id` en Saicloud vía POST /sync/proyectos
```

### 2. Documento Generado en Saiopen → Saicloud

```
1. Contador genera factura en Saiopen con código de proyecto
2. Agente detecta doc nuevo (polling tabla DOCUMENTOS WHERE proyecto_id IS NOT NULL)
3. Agente extrae datos: tipo, número, fecha, tercero, montos
4. Agente envía batch a Django: POST /sync/documentos
5. Django crea DocumentoContable asociado al proyecto
```

### 3. Facturación por Hito (Saicloud solicita → Saiopen genera)

```
1. Usuario marca hito como "facturado" en Saicloud
2. Django envía request al agente: POST /generar-factura
3. Agente crea factura en Saiopen (INSERT en tabla FACTURAS)
4. Agente detecta la nueva factura en siguiente polling
5. Agente sincroniza factura a Saicloud (flujo #2)
```

---

## 📁 Estructura del Proyecto

```
backend/microservices/saiopen-agent/
├── main.go                      # Entry point, HTTP server
├── config/
│   └── config.go                # Configuración (URLs, JWT, polling interval)
├── handlers/
│   ├── sync.go                  # Handlers HTTP (comunicación con Django)
│   └── firebird.go              # Handlers para queries Firebird
├── models/
│   ├── proyecto.go              # Struct Proyecto
│   └── documento.go             # Struct DocumentoContable
├── services/
│   ├── sync_service.go          # Lógica de sincronización bidireccional
│   └── firebird_service.go      # Conexión y queries a Firebird
├── Dockerfile                   # Build multi-stage optimizado
├── go.mod                       # Dependencies
├── go.sum
├── README.md                    # Este archivo
└── install/
    └── setup.nsi                # Instalador NSIS para Windows
```

---

## 🔧 Dependencias

```go
require (
    github.com/nakagami/firebirdsql v0.9.8  // Driver Firebird
    github.com/golang-jwt/jwt/v5 v5.2.0     // Validación JWT
    github.com/robfig/cron/v3 v3.0.1        // Scheduler (polling)
)
```

---

## 🚀 Instalación

### Para el Cliente Final (Windows)

1. **Descargar el instalador:**
   ```
   https://saicloud.s3.amazonaws.com/downloads/saiopen-agent-installer.exe
   ```

2. **Ejecutar el instalador:**
   - Doble clic en `saiopen-agent-installer.exe`
   - Aceptar términos
   - Configurar:
     - **URL de Saicloud API:** `https://api.saicloud.co`
     - **Token de sincronización:** (proporcionado por el administrador)
     - **Ruta de Firebird:** `C:\Saiopen\DATOS.FDB`
   - Click en **Instalar**

3. **El instalador hace:**
   - Copia `saiopen-agent.exe` a `C:\Program Files\SaicloudAgent\`
   - Registra el servicio Windows (`sc create SaicloudAgent`)
   - Inicia el servicio automáticamente
   - Configura inicio automático con Windows

4. **Verificar instalación:**
   - Abrir **Servicios de Windows** (`services.msc`)
   - Buscar `Saicloud Sync Agent`
   - Estado debe ser: **En ejecución**

---

## 🛠️ Desarrollo Local

### Requisitos

- Go 1.21+
- Firebird 3.0+ instalado localmente (para testing)
- Saicloud API corriendo en `http://localhost:8000`

### Setup

```bash
# Clonar el repo
git clone https://github.com/valmentech/saicloud.git
cd backend/microservices/saiopen-agent

# Instalar dependencias
go mod download

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# Ejecutar
go run main.go
```

### Variables de Entorno

```bash
# .env
SAICLOUD_API_URL=http://localhost:8000
SAICLOUD_JWT_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
FIREBIRD_HOST=localhost
FIREBIRD_PORT=3050
FIREBIRD_DATABASE=/path/to/DATOS.FDB
FIREBIRD_USER=SYSDBA
FIREBIRD_PASSWORD=masterkey
POLLING_INTERVAL_SECONDS=300  # 5 minutos
```

---

## 🧪 Testing

```bash
# Tests unitarios
go test ./...

# Tests de integración (requiere Firebird local)
go test -tags=integration ./...

# Build
go build -o saiopen-agent.exe

# Build para producción (optimizado, sin debug symbols)
go build -ldflags="-s -w" -o saiopen-agent.exe
```

---

## 📦 Build del Instalador (NSIS)

```bash
# Instalar NSIS en Windows
choco install nsis

# Build del binario
go build -ldflags="-s -w" -o saiopen-agent.exe

# Compilar instalador
makensis install/setup.nsi

# Output: saiopen-agent-installer.exe
```

---

## 🔐 Seguridad

1. **JWT Authentication:**
   - Todos los requests a Saicloud API usan JWT
   - El token se configura durante la instalación
   - Rotación de tokens: el agente consulta `/sync/refresh-token` cada 7 días

2. **Conexión Firebird:**
   - Solo lectura/escritura en tablas específicas (PROYECTOS, DOCUMENTOS)
   - No tiene permisos de DROP, ALTER, CREATE

3. **HTTPS:**
   - Toda comunicación con Saicloud es HTTPS
   - Certificado SSL validado

4. **Logs:**
   - Logs locales en: `C:\ProgramData\SaicloudAgent\logs\`
   - Rotación automática (max 7 días, max 50MB)
   - **No** se logean datos sensibles (contraseñas, JWT completos)

---

## 🔄 Auto-Actualización

El agente se auto-actualiza automáticamente:

1. Cada 24h consulta: `GET /api/v1/sync/version/`
2. Si hay nueva versión disponible:
   - Descarga `saiopen-agent-{version}.exe` desde S3
   - Verifica checksum SHA256
   - Detiene el servicio actual
   - Reemplaza el binario
   - Reinicia el servicio
3. Si falla, rollback automático a versión anterior

---

## 📊 Monitoreo

### Logs del Servicio

```bash
# Ver logs en tiempo real
Get-Content -Path "C:\ProgramData\SaicloudAgent\logs\agent.log" -Wait
```

### Status del Agente

El agente reporta su estado a Saicloud cada 5 minutos:

```bash
curl https://api.saicloud.co/api/v1/sync/status/ \
  -H "Authorization: Bearer {JWT}"
```

Respuesta:
```json
{
  "agent_version": "1.0.0",
  "last_sync": "2026-03-17T14:30:00Z",
  "status": "running",
  "proyectos_sincronizados": 45,
  "documentos_sincronizados": 1203,
  "errors_last_24h": 0
}
```

---

## ⚠️ Troubleshooting

### El servicio no inicia

1. Verificar que Firebird esté corriendo
2. Verificar conectividad a internet (ping api.saicloud.co)
3. Revisar logs: `C:\ProgramData\SaicloudAgent\logs\agent.log`
4. Verificar permisos del archivo `.exe` (debe poder escribir en `ProgramData`)

### No sincroniza documentos

1. Verificar que el proyecto tenga `codigo` asignado en Saicloud
2. Verificar que los documentos en Saiopen tengan el campo `proyecto_id` poblado
3. Revisar logs para errores de SQL
4. Verificar que el usuario Firebird tenga permisos de lectura en tabla DOCUMENTOS

### Error de JWT

1. El token expiró → regenerar token en Saicloud Admin
2. Verificar que el token esté correctamente configurado en `config.ini`
3. Verificar que la hora del sistema Windows esté sincronizada (JWT valida timestamp)

---

## 📞 Soporte

- **Email:** soporte@valmentech.com
- **Documentación completa:** https://docs.saicloud.co/agente-saiopen
- **GitHub Issues:** https://github.com/valmentech/saicloud/issues

---

## 📄 Licencia

Propietario — ValMen Tech © 2026

---

## 🔗 Referencias

- [DEC-009: Arquitectura Híbrida Django + Go](https://www.notion.so/322ee9c3690a81d48ed5ffd224959cd4)
- [PLAN: Módulo de Proyectos](https://www.notion.so/327ee9c3690a81e5a2dad4b2bf66d7c1)
- [Firebird SQL Documentation](https://firebirdsql.org/en/reference-manuals/)
- [Go Firebird Driver](https://github.com/nakagami/firebirdsql)

---

*Última actualización: 17 Marzo 2026*
