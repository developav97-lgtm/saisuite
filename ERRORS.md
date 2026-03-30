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
