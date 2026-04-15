# SaiSuite

Plataforma SaaS multi-tenant para el ecosistema Saiopen (Grupo SAI S.A.S).

**Desarrollado por:** ValMen Tech  
**Stack:** Django 5 + DRF + PostgreSQL 16 + Angular 18 + n8n + AWS

---

## Inicio rápido con Claude Code

```bash
npm install -g @anthropic-ai/claude-code
cd saisuite/
claude
# Prompt: "Lee CLAUDE.md, ERRORS.md, DECISIONS.md y CONTEXT.md. Resume el estado actual."
```

## Levantar el entorno de desarrollo

```bash
# 1. Servicios en Docker (DB, API, SQS Worker, n8n)
docker compose up -d

# 2. Frontend en LOCAL (no en Docker)
cd frontend && ng serve
```

> El frontend corre directamente en el host (`http://localhost:4200`) para evitar
> el alto consumo de CPU/RAM causado por file-polling en macOS + Docker.

## Estructura

```
saisuite/
├── CLAUDE.md        ← Claude Code lo lee automáticamente
├── ERRORS.md        ← Errores resueltos (no repetir)
├── DECISIONS.md     ← Decisiones de arquitectura
├── CONTEXT.md       ← Estado actual por sesión
├── backend/
├── frontend/
├── agent/
├── n8n/workflows/
└── docs/            ← Poner aquí los .docx técnicos
```

Ver `CONTEXT.md` para el estado actualizado del proyecto.
