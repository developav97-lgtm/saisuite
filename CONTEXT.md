# CONTEXT.md — Estado Actual del Proyecto
# SaiSuite | ValMen Tech
#
# INSTRUCCIONES PARA CLAUDE:
# - Leer este archivo al inicio de CADA sesión de desarrollo.
# - Actualizarlo al FINAL de cada sesión con lo que se hizo y el estado actual.
# - Es la memoria de sesión a sesión. Sin él, cada sesión empieza de cero.

---

## Estado general

| Campo | Valor |
|---|---|
| Fase actual | Fase 0 — Pre-desarrollo |
| Estado | ⏳ En espera de aprobación del partnership con Saiopen |
| Última sesión | Marzo 2026 |
| Próximo paso | Confirmar módulos con Saiopen → arrancar Semana 1 |

---

## Qué está listo

### Documentación (100% completa)
- ✅ Propuesta ejecutiva PPTX enviada a Saiopen
- ✅ Modelo de costos Excel (3 hojas, proyección 18 meses)
- ✅ `docs/Infraestructura_SaiSuite_v2.docx`
- ✅ `docs/Estandares_Codigo_SaiSuite_v1.docx`
- ✅ `docs/Esquema_BD_SaiSuite_v1.docx`
- ✅ `docs/Flujo_Feature_SaiSuite_v1.docx`
- ✅ `docs/AWS_Setup_SaiSuite_v1.docx`
- ✅ `CLAUDE.md`, `ERRORS.md`, `DECISIONS.md`, `CONTEXT.md`

### Código
- ❌ No hay código generado aún — el repositorio no está creado

### Infraestructura AWS
- ❌ No montada aún — esperando confirmación del partnership

### Base de datos
- ❌ No existe aún — staging se monta con el paso 4 de AWS_Setup

---

## Módulos del producto

| Módulo | Estado | Notas |
|---|---|---|
| SaiVentas | ⏳ Por confirmar | Clientes, productos, pedidos |
| SaiCobros | ⏳ Por confirmar | Cartera, gestiones, pagos |
| SaiDashboard | ⏳ Por confirmar | KPIs, reportes, alertas |

---

## Decisiones pendientes

- [ ] Dominio definitivo (placeholder actual: `saisuite.co`)
- [ ] Módulos exactos confirmados con Saiopen
- [ ] Convención snake_case vs camelCase entre Django y Angular (definir antes del primer endpoint)

---

## Último trabajo realizado

**Sesión Marzo 2026:**
- Generados los 5 documentos técnicos de referencia (estándares, BD, flujo, AWS, infraestructura)
- Creados CLAUDE.md, ERRORS.md, DECISIONS.md, CONTEXT.md
- Actualizado Notion — página de metodología Saicloud
- Planificada la estrategia de bucle de mejora automática con ingeniería de contexto agentico

---

## Cómo actualizar este archivo al final de una sesión

Reemplazar la sección "Último trabajo realizado" con lo que se hizo.
Actualizar los checkboxes de "Qué está listo".
Actualizar "Estado general" con la fase y próximo paso actuales.

**Formato de entrada:**

```
## Último trabajo realizado

**Sesión [FECHA]:**
- [Lista de lo que se hizo]
- [Archivos creados o modificados]
- [Decisiones tomadas]
- [Errores encontrados y resueltos]

**Próxima sesión debe:**
- [Lista de lo que queda pendiente inmediato]
```

---

*Última actualización: Marzo 2026*
