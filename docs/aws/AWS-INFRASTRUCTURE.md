# AWS Infrastructure — SaiCloud

Registro vivo de todos los recursos AWS creados para el proyecto SaiCloud.
Actualizar este documento cada vez que se cree, modifique o elimine un recurso.

---

## Cuenta AWS
- **Account ID:** 483772923781
- **Region principal:** us-east-1
- **Usuario administrador:** saicloud-admin (AdministratorAccess)

---

## Arquitectura de Colas SQS

El agente Go (Windows, on-premise) y el backend Django (cloud) se comunican exclusivamente via SQS. Los clientes no necesitan IP pública ni tuneles.

```
[Firebird/Saiopen]                              [SaiCloud - Django]
      │                                                  │
      │  saicloud-to-cloud-prod  (Sai → Cloud)           │
      │ ─────────────────────────────────────────────►   │
      │   GL, CUST, OE, CARPRO, ITEMACT,                 │
      │   ITEM, TAXAUTH, VENDEDOR, ...                    │
      │                                                  │
      │  saicloud-to-sai-prod    (Cloud → Sai)           │
      │ ◄─────────────────────────────────────────────   │
      │   item_upsert, (cust_upsert, etc. futuro)        │
                                                         │
```

**Cola compartida para todos los clientes.** El agente filtra mensajes por `company_id`:
- Si el mensaje es de su empresa → procesa y borra de la cola
- Si es de otra empresa → devuelve a la cola inmediatamente (`ChangeMessageVisibility=0`)

---

## Recursos Creados

### SQS Queues

| Queue | Dirección | Proposito | VisibilityTimeout | LongPolling | Creado |
|-------|-----------|-----------|:-----------------:|:-----------:|--------|
| `saicloud-to-cloud-prod` | Sai → Cloud | Agente Go envía datos de sync (GL, terceros, productos, etc.) a Django | 30s | — | 2026-04-04 |
| `saicloud-to-sai-prod` | Cloud → Sai | Django publica comandos/actualizaciones para el agente (productos, etc.) | 120s | 20s | 2026-04-04 |

**URLs:**
- Sai→Cloud: `https://sqs.us-east-1.amazonaws.com/483772923781/saicloud-to-cloud-prod`
- Cloud→Sai: `https://sqs.us-east-1.amazonaws.com/483772923781/saicloud-to-sai-prod`

**ARNs:**
- `arn:aws:sqs:us-east-1:483772923781:saicloud-to-cloud-prod`
- `arn:aws:sqs:us-east-1:483772923781:saicloud-to-sai-prod`

**Retention:** 4 días | **Max message size:** 1 MB | **Encryption:** SSE activado

---

### Tipos de mensaje por cola

#### `saicloud-to-cloud-prod` (Agente → Django)

| `type` | Descripción |
|--------|-------------|
| `gl_batch` | Movimientos contables (GL) incrementales |
| `acct_full` | Plan de cuentas completo |
| `cust_full` / `cust_batch` | Terceros + SHIPTO + TRIBUTARIA |
| `oe_batch` | Encabezados de facturas (OE) |
| `oedet_batch` | Líneas de facturas (OEDET) |
| `carpro_batch` | Movimientos de cartera (CARPRO) |
| `itemact_batch` | Movimientos de inventario (ITEMACT) |
| `lista_full` | Departamentos y centros de costo |
| `proyectos_full` | Proyectos |
| `actividades_full` | Actividades |
| `tipdoc_full` | Tipos de documento (TIPDOC) |
| `taxauth_full` | Impuestos (TAXAUTH) |
| `item_full` | Catálogo de productos (ITEM) |
| `vendedores_full` | Vendedores (VENDEDOR) |

#### `saicloud-to-sai-prod` (Django → Agente)

| `type` | Descripción | Estado |
|--------|-------------|--------|
| `item_upsert` | Crear/actualizar producto en Firebird ITEM | ✅ Activo |
| `cust_upsert` | Crear/actualizar tercero en Firebird CUST | Futuro |
| `proyecto_upsert` | Crear/actualizar proyecto | Futuro |

**Formato envelope:**
```json
{
  "type": "item_upsert",
  "company_id": "uuid-de-la-empresa",
  "conn_id": "",
  "timestamp": "2026-04-13T10:00:00Z",
  "data": { "records": [ {...} ] }
}
```

---

### IAM Users

| User | ARN | Proposito | Creado |
|------|-----|-----------|--------|
| `saicloud-admin` | arn:aws:iam::483772923781:user/saicloud-admin | Admin del proyecto (AdministratorAccess) | 2026-04-04 |
| `saicloud-agent` | arn:aws:iam::483772923781:user/saicloud-agent | Credencial embebida en el agente Go del cliente | 2026-04-04 |

### IAM Policies

| Policy | Versión | Asociada a | Actualizado |
|--------|---------|------------|-------------|
| `SaicloudAgentSQSPolicy` | v2 | saicloud-agent | 2026-04-13 |

**Permisos `SaicloudAgentSQSPolicy` v2:**

```json
{
  "AgentSendToCloud": {
    "Actions": ["sqs:SendMessage", "sqs:GetQueueUrl", "sqs:GetQueueAttributes"],
    "Resource": "saicloud-to-cloud-prod"
  },
  "AgentReceiveFromCloud": {
    "Actions": ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:ChangeMessageVisibility",
                "sqs:GetQueueUrl", "sqs:GetQueueAttributes"],
    "Resource": "saicloud-to-sai-prod"
  }
}
```

> `ChangeMessageVisibility` es necesario para que el agente devuelva mensajes de otras empresas a la cola sin esperar el visibility timeout.

### Access Keys

| User | Access Key ID | Uso |
|------|---------------|-----|
| `saicloud-agent` | AKIAXBIY476C5BT4V2P4 | Embebida en `saicloud-agent.json` del cliente |

> **IMPORTANTE:** El Secret Access Key se mostró una sola vez. Está guardado en la bóveda segura del equipo. Si se pierde, crear nuevo y rotar en todos los clientes activos.

---

### Secrets Manager

| Secret | ARN | Proposito | Creado |
|--------|-----|-----------|--------|
| _Pendiente_ | — | Credenciales de base de datos RDS | — |

### RDS (Futuro)

| Instance | Endpoint | Engine | Proposito |
|----------|----------|--------|-----------|
| _Pendiente_ | — | PostgreSQL 16 | Base de datos principal SaiCloud |

### ECS Fargate (Futuro)

| Service | Proposito |
|---------|-----------|
| _Pendiente_ | Backend Django API |
| _Pendiente_ | Frontend Angular (Nginx) |
| _Pendiente_ | n8n Workflows |

---

## Convenciones de Nombres

- Formato: `saicloud-{recurso}-{entorno}`
- Entornos: `dev`, `staging`, `prod`
- Tags obligatorios: `Project=SaiCloud`, `Environment={env}`, `ManagedBy=ValMenTech`

---

## Variables de Entorno

### Agente Go (`saicloud-agent.json`)

```json
{
  "transport": "sqs",
  "sqs": {
    "access_key_id": "AKIAXBIY476C5BT4V2P4",
    "secret_access_key": "<guardado en boveda>",
    "region": "us-east-1",
    "queue_url": "https://sqs.us-east-1.amazonaws.com/483772923781/saicloud-to-cloud-prod",
    "inbound_queue_url": "https://sqs.us-east-1.amazonaws.com/483772923781/saicloud-to-sai-prod"
  }
}
```

### Backend Django (`.env`)

```env
AWS_ACCESS_KEY_ID=<saicloud-admin o user backend dedicado>
AWS_SECRET_ACCESS_KEY=<secret>
AWS_DEFAULT_REGION=us-east-1
SQS_TO_CLOUD_URL=https://sqs.us-east-1.amazonaws.com/483772923781/saicloud-to-cloud-prod
SQS_TO_SAI_URL=https://sqs.us-east-1.amazonaws.com/483772923781/saicloud-to-sai-prod
```

---

## Costos Estimados

| Servicio | Estimado/mes | Notas |
|----------|-------------|-------|
| SQS (2 colas) | ~$0.50 | Standard queues, bajo volumen inicial |
| Secrets Manager | ~$0.40 | Por secret almacenado |
| RDS (futuro) | ~$15-30 | db.t3.micro PostgreSQL |
| ECS Fargate (futuro) | ~$30-50 | 2 servicios, 0.25 vCPU cada uno |

---

## Pendientes

1. ~~Crear SQS queues~~ HECHO
2. ~~Crear IAM user saicloud-agent~~ HECHO
3. ~~Activar cola Cloud→Sai (`saicloud-to-sai-prod`)~~ HECHO (v1.2.0 agente)
4. ~~Actualizar policy con `ChangeMessageVisibility`~~ HECHO (v2 policy)
5. Guardar Secret Access Key del agente en bóveda segura del equipo
6. Crear IAM user dedicado para backend Django (no usar saicloud-admin en prod)
7. Configurar RDS PostgreSQL para producción
8. Setup ECS Fargate para deployment

---

**Ultima actualizacion:** 13 Abril 2026
**Mantenido por:** Equipo SaiCloud — ValMen Tech
