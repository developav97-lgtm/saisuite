---
paths:
  - "docs/plans/**"
  - "DECISIONS.md"
  - "PROGRESS-*.md"
---

# Reglas de Arquitectura — Se cargan al trabajar en planes y decisiones

## Django vs Go
Django por defecto (80%). Go SOLO si cumple AL MENOS 1 criterio:
1. >1000 req/s sostenidas o miles de WebSockets
2. Batch >50k registros o cálculos intensivos
3. Ejecutable standalone (agente en PC cliente)
4. Ahorro demostrado >50% y ROI <6 meses

NUNCA Go para: CRUDs, prototipado, "porque es más rápido" sin métricas.
Evaluación detallada: skill `saicloud-planificacion`.

## Roles de usuario
| Role | Acceso |
|---|---|
| `company_admin` | Todo dentro de su empresa |
| `seller` | SaiVentas — clientes, productos, pedidos |
| `collector` | SaiCobros — cartera, gestiones, pagos |
| `viewer` | Solo lectura — dashboards y reportes |
| `valmen_admin` | Plataforma completa (is_staff=True) |
| `valmen_support` | Solo lectura de datos de cliente |

## Decisiones arquitectónicas
Formato: `## DEC-XXX: [Título]` → Fecha, Contexto, Opciones, Decisión, Razón, Consecuencias, Revisión.
Registrar en DECISIONS.md inmediatamente al decidir.
