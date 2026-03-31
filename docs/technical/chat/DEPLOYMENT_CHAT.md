# Deployment Sistema de Chat — Saicloud

**Versión:** 1.0  
**Fecha:** 30 Marzo 2026  
**Módulo:** Sistema de Comunicaciones en Tiempo Real

---

## 📋 Tabla de Contenidos

1. [Prerequisitos](#prerequisitos)
2. [Variables de Entorno](#variables-de-entorno)
3. [Setup Local](#setup-local)
4. [Setup Producción AWS](#setup-producción-aws-futuro)
5. [Troubleshooting](#troubleshooting)

---

## ✅ Prerequisitos

### Software Requerido
- Docker 24+ & Docker Compose 2.20+
- PostgreSQL 16
- Python 3.11+
- Node.js 20+ & npm 10+
- Git

### Cuentas Externas
- **Upstash Redis:** https://upstash.com (free tier disponible)
- **Cloudflare R2:** https://cloudflare.com (free tier disponible)
- **AWS:** Para deployment producción (futuro)

---

## 🔐 Variables de Entorno

### Backend (.env)

Crear archivo `backend/.env` con:

```bash
# Django
DEBUG=True
SECRET_KEY=tu-secret-key-super-segura-aqui-minimo-50-caracteres
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:4200

# Database
DATABASE_URL=postgresql://saicloud_user:password@localhost:5432/saicloud_db

# Upstash Redis
UPSTASH_REDIS_URL=rediss://default:XXXXXX@stable-elephant-88389.upstash.io:6379

# Cloudflare R2
CLOUDFLARE_R2_ACCESS_KEY_ID=tu-access-key-aqui
CLOUDFLARE_R2_SECRET_ACCESS_KEY=tu-secret-key-aqui
CLOUDFLARE_R2_ENDPOINT=https://ACCOUNT_ID.r2.cloudflarestorage.com
CLOUDFLARE_R2_BUCKET_NAME=saicloud-chat

# JWT
JWT_SECRET_KEY=tu-jwt-secret-key-diferente-al-secret-key
JWT_EXPIRATION_HOURS=24

# Email (opcional)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### Frontend (environment.ts)

```typescript
// frontend/src/environments/environment.ts
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000',
  wsUrl: 'ws://localhost:8000'
};

// frontend/src/environments/environment.prod.ts
export const environment = {
  production: true,
  apiUrl: 'https://api.saicloud.com',
  wsUrl: 'wss://api.saicloud.com'
};
```

### Obtener Credenciales

#### Upstash Redis
1. Ir a https://upstash.com → Sign Up (gratis)
2. Create Database → nombre: `saicloud-chat`
3. Region: `us-east-1` (o la más cercana)
4. Copiar **Redis URL** (formato: `rediss://...`)
5. Pegar en `UPSTASH_REDIS_URL`

#### Cloudflare R2
1. Ir a https://dash.cloudflare.com → R2
2. Create bucket → nombre: `saicloud-chat`
3. Ir a Settings → Manage R2 API Tokens
4. Create API Token → Permissions: Read & Write
5. Copiar:
   - Access Key ID → `CLOUDFLARE_R2_ACCESS_KEY_ID`
   - Secret Access Key → `CLOUDFLARE_R2_SECRET_ACCESS_KEY`
   - Endpoint URL → `CLOUDFLARE_R2_ENDPOINT`

---

## 🚀 Setup Local

### 1. Clonar Repositorio
```bash
git clone https://github.com/tu-org/saicloud.git
cd saicloud
```

### 2. Configurar Backend
```bash
cd backend

# Crear .env
cp .env.example .env
# Editar .env con tus credenciales

# Crear virtual environment (opcional)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

# Instalar dependencias
pip install --break-system-packages -r requirements.txt

# Migraciones
python manage.py makemigrations
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Seed data (opcional)
python manage.py loaddata fixtures/demo_data.json
```

### 3. Configurar Frontend
```bash
cd ../frontend

# Instalar dependencias
npm install

# Verificar que no haya errores
npm run build
```

### 4. Levantar Servicios con Docker Compose
```bash
# Desde raíz del proyecto
docker-compose up -d

# Ver logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 5. Verificar Setup

**Backend:**
- API REST: http://localhost:8000/api/v1/
- Django Admin: http://localhost:8000/admin/
- Health check: http://localhost:8000/health/

**Frontend:**
- App: http://localhost:4200
- Angular dev server: `npm start`

**WebSocket:**
```bash
# Test WebSocket connection
wscat -c "ws://localhost:8000/ws/chat/?token=YOUR_JWT_TOKEN"
```

**Redis:**
```bash
# Verificar conexión Redis
docker exec -it saicloud-backend python manage.py shell

>>> from django.core.cache import cache
>>> cache.set('test', 'OK')
>>> cache.get('test')
'OK'
```

**Cloudflare R2:**
```bash
# Test upload
curl -X POST http://localhost:8000/api/v1/chat/upload-imagen/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "imagen=@test.jpg"
```

---

## 🌐 Setup Producción AWS (Futuro)

### Arquitectura Target

```
Internet
   │
   ├─> Route 53 (DNS)
   │       │
   │       ▼
   ├─> CloudFront (CDN para frontend)
   │       │
   │       ▼
   └─> Application Load Balancer (ALB)
           │
           ├─> ECS Service (Daphne workers)
           │     └─> Task Definition
           │           ├─> Container: daphne (WebSocket)
           │           └─> Container: nginx (static files)
           │
           ├─> RDS PostgreSQL 16
           │
           └─> CloudWatch (logs + metrics)

External:
   ├─> Upstash Redis (serverless)
   └─> Cloudflare R2 (storage)
```

### Componentes AWS

#### 1. VPC Configuration
```bash
# VPC
VPC: 10.0.0.0/16
Public Subnets: 10.0.1.0/24, 10.0.2.0/24 (2 AZs)
Private Subnets: 10.0.10.0/24, 10.0.11.0/24 (2 AZs)
NAT Gateway: 1 por AZ
Internet Gateway: 1
```

#### 2. RDS PostgreSQL
```bash
# Database
Engine: PostgreSQL 16
Instance: db.t4g.micro (free tier) o db.t4g.small (prod)
Storage: 20 GB gp3 (auto-scaling hasta 100 GB)
Multi-AZ: No (dev), Yes (prod)
Backup retention: 7 días
Automated backups: 3:00 AM UTC
```

#### 3. ECS Cluster
```bash
# Cluster
Name: saicloud-prod
Launch type: Fargate
Capacity provider: FARGATE_SPOT (70%) + FARGATE (30%)

# Task Definition
Family: saicloud-chat
CPU: 512 (0.5 vCPU)
Memory: 1024 MB (1 GB)
Network mode: awsvpc

# Containers
1. daphne:
   - Image: ECR/saicloud-backend:latest
   - Port: 8000
   - Command: ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]
   - Env vars: DATABASE_URL, UPSTASH_REDIS_URL, etc.

2. nginx:
   - Image: nginx:alpine
   - Port: 80
   - Volumes: shared static files

# Service
Desired tasks: 2
Min: 2, Max: 4
Auto-scaling target: CPU 70%
Health check: /health/
```

#### 4. Application Load Balancer
```bash
# ALB
Scheme: internet-facing
IP address type: ipv4
Subnets: Public subnets (2 AZs)

# Listeners
1. HTTP:80 → Redirect to HTTPS
2. HTTPS:443 → Target group ECS
   - SSL Certificate: AWS Certificate Manager (ACM)
   - Upgrade: websocket headers

# Target Group
Protocol: HTTP
Port: 8000
Health check: /health/
Deregistration delay: 30s
Stickiness: Enabled (cookie, 1 hour)

# Security Group
Inbound:
  - 80/tcp from 0.0.0.0/0
  - 443/tcp from 0.0.0.0/0
Outbound:
  - All traffic
```

#### 5. CloudWatch
```bash
# Log Groups
/ecs/saicloud-chat (retention: 30 días)

# Metrics
- CPU Utilization
- Memory Utilization
- Request Count
- Target Response Time
- WebSocket Active Connections

# Alarms
1. CPU > 80% (5 min) → SNS notification
2. Memory > 80% (5 min) → SNS notification
3. 5xx errors > 10 (5 min) → SNS notification
4. Target unhealthy (2 min) → SNS notification
```

### Deployment Script

```bash
#!/bin/bash
# scripts/deploy-aws.sh

set -e

# 1. Build Docker image
docker build -t saicloud-backend:latest -f docker/Dockerfile.prod .

# 2. Tag para ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
docker tag saicloud-backend:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/saicloud-backend:latest

# 3. Push a ECR
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/saicloud-backend:latest

# 4. Deploy con Terraform
cd infrastructure/aws
terraform init
terraform plan
terraform apply -auto-approve

# 5. Verificar health checks
aws elbv2 describe-target-health --target-group-arn arn:aws:elasticloadbalancing:...

# 6. Verify WebSocket
wscat -c "wss://api.saicloud.com/ws/chat/?token=TEST_TOKEN"
```

### Terraform Configuration

```hcl
# infrastructure/aws/main.tf

provider "aws" {
  region = "us-east-1"
}

# VPC
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  
  name = "saicloud-vpc"
  cidr = "10.0.0.0/16"
  
  azs             = ["us-east-1a", "us-east-1b"]
  public_subnets  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnets = ["10.0.10.0/24", "10.0.11.0/24"]
  
  enable_nat_gateway = true
  single_nat_gateway = false
}

# RDS
resource "aws_db_instance" "postgres" {
  identifier           = "saicloud-db"
  engine              = "postgres"
  engine_version      = "16"
  instance_class      = "db.t4g.micro"
  allocated_storage   = 20
  storage_type        = "gp3"
  
  db_name  = "saicloud"
  username = "admin"
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  skip_final_snapshot = false
  final_snapshot_identifier = "saicloud-db-final-snapshot"
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "saicloud-prod"
}

# Task Definition
resource "aws_ecs_task_definition" "chat" {
  family                   = "saicloud-chat"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 512
  memory                   = 1024
  
  execution_role_arn = aws_iam_role.ecs_execution.arn
  task_role_arn      = aws_iam_role.ecs_task.arn
  
  container_definitions = jsonencode([{
    name  = "daphne"
    image = "${aws_ecr_repository.backend.repository_url}:latest"
    
    portMappings = [{
      containerPort = 8000
      protocol      = "tcp"
    }]
    
    environment = [
      { name = "DATABASE_URL", value = "postgresql://..." },
      { name = "UPSTASH_REDIS_URL", value = var.redis_url },
      { name = "CLOUDFLARE_R2_ACCESS_KEY_ID", value = var.r2_access_key }
    ]
    
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/ecs/saicloud-chat"
        "awslogs-region"        = "us-east-1"
        "awslogs-stream-prefix" = "daphne"
      }
    }
  }])
}

# ALB
resource "aws_lb" "main" {
  name               = "saicloud-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = module.vpc.public_subnets
}

# HTTPS Listener
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = aws_acm_certificate.main.arn
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.ecs.arn
  }
}
```

### Checklist Pre-Deployment

- [ ] **Variables de entorno** configuradas en ECS Task Definition
- [ ] **Migraciones** ejecutadas en RDS
- [ ] **Static files** compilados y subidos a S3
- [ ] **SSL certificate** válido en ACM
- [ ] **Health checks** configurados en ALB
- [ ] **Auto-scaling** políticas activadas
- [ ] **CloudWatch alarms** creadas
- [ ] **Backup RDS** configurado
- [ ] **IAM roles** con permisos mínimos
- [ ] **Security groups** configurados correctamente

### Estimación de Costos AWS (Producción)

| Servicio | Configuración | Costo/mes |
|----------|---------------|-----------|
| ECS Fargate | 2 tasks × 0.5 vCPU × 1 GB | $15.00 |
| RDS PostgreSQL | db.t4g.small | $18.00 |
| ALB | 1 ALB + data transfer | $16.00 |
| CloudWatch | Logs + metrics | $5.00 |
| Route 53 | 1 hosted zone | $0.50 |
| **Subtotal AWS** | | **$54.50** |
| Upstash Redis | Serverless | $1.70 |
| Cloudflare R2 | Storage + requests | $0.68 |
| **TOTAL** | | **$56.88/mes** |

---

## 🔧 Troubleshooting

### Backend no conecta a Redis

**Síntoma:** Error `ConnectionError: Error connecting to Redis`

**Solución:**
```bash
# Verificar URL Redis en .env
echo $UPSTASH_REDIS_URL

# Debe tener formato: rediss://default:PASSWORD@HOST:6379
# NO debe tener: redis-cli --tls -u redis://...

# Test conexión manual
redis-cli -u $UPSTASH_REDIS_URL PING
# Debe responder: PONG
```

### WebSocket no conecta

**Síntoma:** Error `WebSocket connection failed`

**Solución:**
```bash
# Verificar Daphne corriendo
docker ps | grep daphne

# Verificar logs
docker logs saicloud-backend | grep -i websocket

# Test conexión WebSocket
wscat -c "ws://localhost:8000/ws/chat/?token=YOUR_JWT"

# Si falla, verificar:
# 1. JWT válido
# 2. ASGI configuration en config/asgi.py
# 3. CHANNEL_LAYERS en settings
```

### Imágenes no suben a R2

**Síntoma:** Error `S3 upload failed`

**Solución:**
```bash
# Verificar credenciales R2
echo $CLOUDFLARE_R2_ACCESS_KEY_ID
echo $CLOUDFLARE_R2_SECRET_ACCESS_KEY
echo $CLOUDFLARE_R2_ENDPOINT

# Test upload manual
aws s3 cp test.jpg s3://saicloud-chat/test.jpg \
  --endpoint-url=$CLOUDFLARE_R2_ENDPOINT \
  --region=auto

# Verificar permisos bucket R2 en Cloudflare Dashboard
```

### Frontend no muestra mensajes en tiempo real

**Síntoma:** Mensajes no aparecen automáticamente

**Solución:**
```typescript
// Verificar WebSocket conectado
// En browser DevTools → Network → WS
// Debe mostrar ws://localhost:8000/ws/chat/?token=...

// Verificar signals reactivos
// En component:
effect(() => {
  console.log('Mensajes updated:', this.chatSocket.mensajes());
});

// Si no actualiza:
// 1. Verificar que socketService.connect(token) se llama
// 2. Verificar que signals están en service, no en component
// 3. Verificar OnPush change detection no está bloqueando
```

### Migraciones fallan

**Síntoma:** `django.db.migrations.exceptions.InconsistentMigrationHistory`

**Solución:**
```bash
# Opción 1: Reset migraciones (SOLO EN DEV)
python manage.py migrate --fake apps.chat zero
python manage.py migrate apps.chat

# Opción 2: Regenerar desde cero (DESTRUCTIVO)
# ¡Esto BORRA TODOS LOS DATOS!
python manage.py migrate apps.chat zero
rm -rf apps/chat/migrations/0*.py
python manage.py makemigrations chat
python manage.py migrate chat

# Opción 3: Producción (requiere backup)
# 1. Backup DB: pg_dump
# 2. Aplicar migración manualmente
# 3. Verificar integridad datos
```

### Build Angular falla

**Síntoma:** `Error: Cannot find module '@ctrl/ngx-emoji-mart'`

**Solución:**
```bash
# Limpiar cache npm
rm -rf node_modules package-lock.json
npm cache clean --force
npm install

# Si persiste, verificar versión Node.js
node --version  # Debe ser 20+

# Reinstalar específica
npm install @ctrl/ngx-emoji-mart --save

# Verificar tsconfig.json incluye paths correctos
```

### Docker build muy lento

**Síntoma:** Build tarda >10 minutos

**Solución:**
```bash
# Usar BuildKit
export DOCKER_BUILDKIT=1
docker-compose build

# Cache layers
docker-compose build --no-cache backend  # Solo si necesario

# Limpiar imágenes antiguas
docker system prune -a

# Multi-stage build (ya implementado en Dockerfile)
# Verificar que no se copien node_modules ni __pycache__
```

### Presencia online/offline no funciona

**Síntoma:** Usuarios siempre aparecen offline

**Solución:**
```python
# Verificar TTL Redis
# En Django shell:
from apps.chat.services import PresenceService
service = PresenceService()
service.set_user_online(user_id)

# Verificar en Redis:
import redis
r = redis.from_url(os.environ['UPSTASH_REDIS_URL'])
r.get(f'user:{user_id}:status')
# Debe retornar: b'online'
r.ttl(f'user:{user_id}:status')
# Debe retornar: ~35 segundos

# Verificar heartbeat frontend (debe ser cada 25s)
```

---

## 📚 Referencias

- **Arquitectura:** Ver `ARQUITECTURA_CHAT.md`
- **API Reference:** Ver `API_REFERENCE_CHAT.md`
- **Decisiones:** Ver `DECISIONS.md` (DEC-033, DEC-034, DEC-035)
- **Django Channels:** https://channels.readthedocs.io/
- **Daphne:** https://github.com/django/daphne
- **Upstash:** https://docs.upstash.com/redis
- **Cloudflare R2:** https://developers.cloudflare.com/r2/
