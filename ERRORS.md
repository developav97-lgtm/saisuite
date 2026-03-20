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