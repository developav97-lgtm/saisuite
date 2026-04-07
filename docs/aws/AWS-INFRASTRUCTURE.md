# AWS Infrastructure — SaiCloud

Registro vivo de todos los recursos AWS creados para el proyecto SaiCloud.
Actualizar este documento cada vez que se cree, modifique o elimine un recurso.

---

## Cuenta AWS
- **Account ID:** 483772923781
- **Region principal:** us-east-1
- **Usuario administrador:** saicloud-admin (AdministratorAccess)

---

## Recursos Creados

### SQS Queues

| Queue | ARN | URL | Proposito | Creado |
|-------|-----|-----|-----------|--------|
| saicloud-to-cloud-prod | arn:aws:sqs:us-east-1:483772923781:saicloud-to-cloud-prod | https://sqs.us-east-1.amazonaws.com/483772923781/saicloud-to-cloud-prod | Agente Go envia datos de sync al cloud | 2026-04-04 |
| saicloud-to-sai-prod | arn:aws:sqs:us-east-1:483772923781:saicloud-to-sai-prod | https://sqs.us-east-1.amazonaws.com/483772923781/saicloud-to-sai-prod | Cloud envia comandos al agente (futuro) | 2026-04-04 |

### IAM Users

| User | ARN | Proposito | Creado |
|------|-----|-----------|--------|
| saicloud-admin | arn:aws:iam::483772923781:user/saicloud-admin | Admin del proyecto (AdministratorAccess) | 2026-04-04 |
| saicloud-agent | arn:aws:iam::483772923781:user/saicloud-agent | Agente Go en PC del cliente | 2026-04-04 |

### IAM Policies

| Policy | ARN | Asociada a | Permisos | Creado |
|--------|-----|------------|----------|--------|
| SaicloudAgentSQSPolicy | arn:aws:iam::483772923781:policy/SaicloudAgentSQSPolicy | saicloud-agent | SendMessage en to-cloud, ReceiveMessage+Delete en to-sai | 2026-04-04 |

### Access Keys (Agente)

| User | Access Key ID | Proposito |
|------|---------------|-----------|
| saicloud-agent | AKIAXBIY476C5BT4V2P4 | Credencial para agente Go en PC cliente |

> **IMPORTANTE:** El Secret Access Key del agente se mostro una sola vez al crear. Guardarlo en un lugar seguro (AWS Secrets Manager o bóveda de contraseñas). Si se pierde, crear uno nuevo y rotar.

### Secrets Manager

| Secret | ARN | Proposito | Creado |
|--------|-----|-----------|--------|
| _Pendiente_ | — | Credenciales de base de datos RDS | — |

### RDS (Futuro)

| Instance | Endpoint | Engine | Proposito | Creado |
|----------|----------|--------|-----------|--------|
| _Pendiente_ | — | PostgreSQL 16 | Base de datos principal SaiCloud | — |

### ECS Fargate (Futuro)

| Service | Cluster | Task Definition | Proposito | Creado |
|---------|---------|-----------------|-----------|--------|
| _Pendiente_ | — | — | Backend Django API | — |
| _Pendiente_ | — | — | Frontend Angular (Nginx) | — |
| _Pendiente_ | — | — | n8n Workflows | — |

---

## Convenciones de Nombres

- Formato: `saicloud-{recurso}-{entorno}`
- Entornos: `dev`, `staging`, `prod`
- Tags obligatorios: `Project=SaiCloud`, `Environment={env}`, `ManagedBy=ValMenTech`

---

## Variables de Entorno para el Agente Go

```env
AWS_ACCESS_KEY_ID=AKIAXBIY476C5BT4V2P4
AWS_SECRET_ACCESS_KEY=<guardado en boveda>
AWS_DEFAULT_REGION=us-east-1
SQS_TO_CLOUD_URL=https://sqs.us-east-1.amazonaws.com/483772923781/saicloud-to-cloud-prod
SQS_TO_SAI_URL=https://sqs.us-east-1.amazonaws.com/483772923781/saicloud-to-sai-prod
```

---

## Variables de Entorno para Backend Django

```env
AWS_ACCESS_KEY_ID=<usar saicloud-admin o crear user backend especifico>
AWS_SECRET_ACCESS_KEY=<secret>
AWS_DEFAULT_REGION=us-east-1
SQS_TO_CLOUD_URL=https://sqs.us-east-1.amazonaws.com/483772923781/saicloud-to-cloud-prod
SQS_TO_SAI_URL=https://sqs.us-east-1.amazonaws.com/483772923781/saicloud-to-sai-prod
```

---

## Costos Estimados

| Servicio | Estimado/mes | Notas |
|----------|-------------|-------|
| SQS | ~$0.40 | Standard queue, bajo volumen |
| Secrets Manager | ~$0.40 | Por secret almacenado |
| RDS (futuro) | ~$15-30 | db.t3.micro PostgreSQL |
| ECS Fargate (futuro) | ~$30-50 | 2 servicios, 0.25 vCPU cada uno |

---

## Proximos Pasos

1. ~~Crear SQS queues~~ HECHO
2. ~~Crear IAM user saicloud-agent~~ HECHO
3. Guardar Secret Access Key del agente en boveda segura
4. Configurar agente Go con credenciales SQS (toggle HTTP→SQS)
5. Crear IAM user dedicado para backend Django (no usar admin)
6. Configurar RDS PostgreSQL para produccion
7. Setup ECS Fargate para deployment

---

**Ultima actualizacion:** 04 Abril 2026
**Mantenido por:** Equipo SaiCloud — ValMen Tech
