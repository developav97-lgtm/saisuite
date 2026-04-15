## [13 Abril 2026] ERROR: Tests `test_services.py` fallaban por campos obsoletos en modelos

**Síntoma:** `TrialServiceTest::test_access_via_license` lanzaba `TypeError: CompanyLicense() got unexpected keyword arguments: 'plan'`. `FilterServiceTest::test_get_terceros_with_query` lanzaba `KeyError: 'tercero_nombre'`.
**Causa:** 1) El campo `plan` fue eliminado de `CompanyLicense` (reemplazado por `renewal_type`) en sesión del 09 Abril, pero el test no fue actualizado. 2) `FilterService.get_available_terceros()` fue refactorizado para retornar `{'id', 'nombre', 'identificacion'}` normalizado (unificando Tercero + GL), pero el test seguía buscando la clave legacy `tercero_nombre`.
**Fix:** `test_services.py`: 1) Remover `plan='professional'` del `CompanyLicense.objects.create()` en `test_access_via_license`. 2) Cambiar `t['tercero_nombre']` por `t['nombre']` en `test_get_terceros_with_query`.
**Prevención:** Al eliminar/renombrar campos de modelos, buscar `grep -r "campo_viejo"` en tests antes de cerrar la sesión.

---

## [09 Abril 2026] ERROR: KeyError en logger.info — clave 'created' reservada por Python logging

**Síntoma:** `POST /api/v1/projects/{pk}/documents/sync/` retornaba 500. Traceback: `KeyError: "Attempt to overwrite 'created' in LogRecord"`.
**Causa:** `logging.LogRecord` tiene atributos internos fijos (`created`, `message`, `name`, `levelname`, etc.). Pasar `extra={'created': n}` a `logger.info()` intenta sobrescribir uno de esos atributos y Python lanza `KeyError`.
**Fix:** Renombrar la clave en `extra` a `'docs_created'` y `'docs_updated'` en `DocumentoContableService.sync_from_gl()` (`proyectos/services.py:989`).
**Prevención:** En llamadas a `logger.*(..., extra={...})` nunca usar como claves: `created`, `message`, `asctime`, `levelname`, `levelno`, `name`, `pathname`, `filename`, `module`, `lineno`, `funcName`, `process`, `thread`, `taskName`. Prefijar siempre con el dominio (ej. `docs_`, `sync_`, `proj_`).

---

## [07 Abril 2026] ERROR: Go Firebird query cuelga sin error cuando columna es palabra reservada

**Síntoma:** Go agent logueaba `syncing CUST incremental` y luego silencio total. La goroutine no completaba, no retornaba error, no había timeout. El proceso quedaba bloqueado indefinidamente.
**Causa:** `Version` es una palabra reservada en Firebird SQL. La query `SELECT ... Version FROM CUST` fallaba internamente con `SQL error code = -206, Column unknown, VERSION`. El driver `nakagami/firebirdsql` no surfaceaba el error porque el punto de falla estaba en la iteración de filas (rows.Scan), no en la apertura de filas. Además, `doCustSync` ignoraba el valor de retorno del error, así que el error nunca llegaba a los logs.
**Fix:** 1) Citar el campo como `"Version"` en todo el SQL. 2) En `orchestrator.go`, loggear el error de `SyncCustIncremental`: `if err := syncer.SyncCustIncremental(conn); err != nil { logger.Error(...) }`.
**Prevención:** En Firebird 2.5, los identificadores que coincidan con palabras reservadas SQL deben ir entre comillas dobles. Revisar lista de reservadas antes de usar nombres de columna genéricos (Version, Date, Time, User, etc.). Siempre loggear errores de funciones que retornan `error` en el orchestrator.

---

## [07 Abril 2026] ERROR: SQS 413 — mensaje demasiado grande con 1755 CUST + SHIPTO + TRIBUTARIA

**Síntoma:** `API error 413 from https://sqs.us-east-1.amazonaws.com/...` al intentar enviar el primer sync completo de CUST.
**Causa:** El payload JSON con 1755 registros CUST + 1805 SHIPTO + 1742 TRIBUTARIA superaba el límite de 256KB de SQS.
**Fix:** Chunking a 150 registros CUST por mensaje. Cada chunk incluye solo los SHIPTO/TRIBUTARIA correspondientes a los ID_N de ese chunk (lookup maps O(1)). `custChunkSize = 150` constante en `reference_sync.go`.
**Prevención:** Para cualquier sync que incluya tablas relacionadas, estimar el tamaño del payload: (registros × bytes_promedio_por_registro) × 3 tablas. Si supera ~80KB, usar chunking. SQS límite es 256KB pero con overhead JSON y encoding hay que dejar margen.

---

## [07 Abril 2026] ERROR: KeyError 'created' en LogRecord al loggear en terceros/services.py

**Síntoma:** `sqs_worker` crasheaba después de procesar CUST: `KeyError: 'created'`.
**Causa:** Python's `logging.LogRecord` tiene atributo reservado `created` (timestamp del record). Pasar `extra={'created': ...}` intenta sobreescribirlo y lanza KeyError.
**Fix:** Renombrar a `extra={'created_count': ..., 'updated_count': ...}`.
**Prevención:** Los atributos reservados de LogRecord incluyen: `created`, `name`, `msg`, `args`, `levelname`, `levelno`, `pathname`, `filename`, `module`, `exc_info`, `exc_text`, `stack_info`, `lineno`, `funcName`, `msecs`, `relativeCreated`, `thread`, `threadName`, `process`, `processName`. Nunca usar estos como keys en `extra={}`.

---

## [30 Marzo 2026] ERROR: UPSTASH_REDIS_URL con formato de comando CLI en .env

**Sintoma:** WebSocket retorna 500 al conectar. Log: `ValueError: Redis URL must specify one of the following schemes (redis://, rediss://, unix://)`.
**Causa:** El `.env` contenia `UPSTASH_REDIS_URL=redis-cli --tls -u redis://...` (el comando CLI completo de Upstash, copiado del dashboard). `channels-redis` espera solo la URL, no el comando.
**Fix:** Cambiar a `UPSTASH_REDIS_URL=rediss://default:...@...upstash.io:6379`. Usar `rediss://` (doble s) para TLS que Upstash requiere.
**Prevencion:** Al copiar URLs de Upstash, usar la pestaña "Connection String" (no "CLI Command"). Siempre verificar que el valor empiece con `redis://` o `rediss://`.

---

## [28 Marzo 2026] ERROR: CheckConstraint(condition=) rompe Docker con Django 5.0.6

**Síntoma:** Contenedor `saisuite-api` queda en estado `unhealthy`. Django no levanta: `TypeError: CheckConstraint.__init__() got an unexpected keyword argument 'condition'`.
**Causa:** El parámetro `condition=` en `CheckConstraint` fue introducido en Django 5.1. El proyecto usa Django 5.0.6 (en Docker Python 3.12). En el entorno local (Python 3.13) se puede instalar Django 5.1+ y no se nota el error.
**Fix:** Reemplazar `CheckConstraint(condition=Q(...))` → `CheckConstraint(check=Q(...))` en `models.py` Y en todas las migraciones que crean esos constraints (0015_resource_models.py, 0018_feature_7_budget_models.py). `Index(condition=)` y `UniqueConstraint(condition=)` NO se tocan, esos parámetros sí existen en 5.0.
**Prevención:** Nunca usar `CheckConstraint(condition=...)`. Siempre usar `CheckConstraint(check=...)` mientras el proyecto esté en Django < 5.1. Verificar con `docker logs saisuite-api` si el servidor no responde.

---

## [27 Marzo 2026] ERROR: KeyError 'created' en LogRecord al loggear en services

**Síntoma:** Tests de `budget_services.py` fallan con `KeyError: "Attempt to overwrite 'created' in LogRecord"` al llamar `set_project_budget` y `create_snapshot`.
**Causa:** `'created'` es un campo reservado en `logging.LogRecord` de Python (almacena el timestamp). Usar `extra={'created': ...}` en `logger.info()` intenta sobrescribirlo y lanza KeyError.
**Fix:** Renombrar la clave en el `extra` dict: `'created'` → `'is_new'` en `budget_services.py:699` y `budget_services.py:1304`.
**Prevención:** Nunca usar como clave de `extra={}` en llamadas de logging ninguno de los atributos reservados de LogRecord: `created`, `name`, `msg`, `args`, `levelname`, `levelno`, `pathname`, `filename`, `module`, `exc_info`, `exc_text`, `stack_info`, `lineno`, `funcName`, `msecs`, `relativeCreated`, `thread`, `threadName`, `processName`, `process`.

---

## ERR-011: PrimeNG incompatibilidad con Angular 20

**Fecha:** 19 Marzo 2026
**Contexto:** Migración a Angular Material

### Error
Al usar PrimeNG 18.x con Angular 20:
```
TypeError: fn is not a function
  at pAutoFocus directive
  at BaseIcon component
```

Además:
- Script postinstall de PrimeNG falla en Docker build
- Versión LTS requiere licencia comercial

### Causa
PrimeNG 18.x no es totalmente compatible con Angular 20.
La directiva `pAutoFocus` y `BaseIcon` tienen bugs conocidos.

### Solución
Migración completa a **Angular Material 20**:
```bash
npm uninstall primeng primeicons
npm install @angular/material@^20.0.0
```

Reemplazar todos los componentes:
- `p-table` → `mat-table`
- `p-button` → `mat-button`
- `p-card` → `mat-card`
- `p-input` → `mat-form-field` + `input matInput`

**Decisión:** DEC-011 - Angular Material como UI Framework oficial

---

## ERR-012: Docker anonymous volumes persisten node_modules

**Fecha:** 19 Marzo 2026
**Contexto:** Cambios en package.json no se reflejan

### Error
Después de agregar/quitar paquetes en `package.json` y hacer rebuild, los cambios no se aplican en el contenedor.

### Causa
Docker Compose crea un volumen anónimo para `/app/node_modules` que sobrevive al `docker-compose down` y `docker-compose build`.

### Solución
```bash
# Eliminar volúmenes anónimos
docker-compose down -v

# Rebuild sin cache
docker-compose build --no-cache frontend

# Levantar
docker-compose up frontend
```

**Lección:** Siempre usar `-v` al hacer `docker-compose down` si se modificó package.json.

---

## ERR-013: Angular Material BadgeModule causa NG1010

**Fecha:** 19 Marzo 2026
**Contexto:** Standalone components Angular 18+

### Error
```
NG1010: Unknown reference. Cannot resolve symbol 'BadgeModule'
```

### Causa
En Angular 18+ con standalone components:
- `BadgeModule` y `RippleModule` no deben importarse
- Son directivas standalone que se importan directamente

### Solución
**NO HACER:**
```typescript
import { BadgeModule } from '@angular/material/badge';

@Component({
  imports: [BadgeModule]  // ❌ Error
})
```

**CORRECTO:**
```typescript
import { MatBadge } from '@angular/material/badge';

@Component({
  imports: [MatBadge]  // ✅ Correcto
})
```

---

## ERR-014: ThemeService.isDarkMode() is not a function

**Fecha:** 19 Marzo 2026
**Contexto:** Tema dark mode

### Error
```
TypeError: this.themeService.isDarkMode is not a function
```

### Causa
`isDarkMode` es un **getter**, no un método.

### Solución
**NO HACER:**
```typescript
if (this.themeService.isDarkMode()) {  // ❌ Error
```

**CORRECTO:**
```typescript
if (this.themeService.isDark) {  // ✅ Correcto
```
## [2026-03-27] ERROR: get_full_name() no existe en modelo User personalizado

**Síntoma:** `AttributeError: 'User' object has no attribute 'get_full_name'. Did you mean: 'full_name'?` al serializar ResourceCapacity/ResourceAssignment/ResourceAvailability.

**Causa:** El modelo `User` de este proyecto es completamente personalizado y expone el nombre completo como propiedad `full_name` (no como método `get_full_name()` del AbstractUser de Django estándar).

**Fix:** Reemplazar todas las llamadas `obj.usuario.get_full_name() or obj.usuario.email` por `obj.usuario.full_name or obj.usuario.email` en serializers.py y resource_services.py.

**Prevención:** Al crear serializers con campos de usuario, usar siempre `user.full_name` en lugar de `user.get_full_name()`. Buscar en DECISIONS.md o en apps/users/models.py antes de asumir que existe `get_full_name()`.

## [2026-03-27] ERROR: Campo usuario_id faltante en ResourceAvailabilityCreateSerializer

**Síntoma:** `KeyError: 'usuario_id'` en `ResourceAvailabilityViewSet.create()` al llamar `d['usuario_id']`.

**Causa:** El campo `usuario_id` se omitió por error en la definición de `ResourceAvailabilityCreateSerializer` (solo tenía `tipo`, `fecha_inicio`, `fecha_fin`, `descripcion`).

**Fix:** Agregar `usuario_id = serializers.UUIDField()` como primer campo del serializer.

**Prevención:** Al definir serializers de escritura que llaman a servicios con `usuario_id`, verificar que ese campo esté declarado en el serializer ANTES de la primera prueba.

## [2026-03-27] ERROR: bool('False') == True — conversión de boolean en form data

**Síntoma:** El endpoint `POST /resources/availability/{pk}/approve/` siempre aprobaba (`aprobado=True`) aunque el body enviara `{'aprobar': False}`.

**Causa:** Cuando el test envía `{'aprobar': False}` como multipart form data, DRF recibe la cadena `'False'` (string). `bool('False')` en Python evalúa a `True` porque es un string no vacío.

**Fix:** Normalizar el valor en la vista: `if isinstance(aprobar_raw, str): aprobar = aprobar_raw.lower() not in ('false', '0', 'no', '')`.

**Prevención:** Cuando un endpoint recibe un boolean via form data (no JSON), nunca usar `bool(value)` directamente. Usar el patrón de normalización arriba, o enviar JSON explícito con `content_type='application/json'` en los tests.
