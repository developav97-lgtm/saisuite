# Análisis de Costos y Límites — Módulos IA de SaiSuite

**Fecha:** 15 Abril 2026 | **Versión:** 1.0 | **Modelo base:** `gpt-4o-mini` (OpenAI)

---

## 1. Módulos con IA activa

| Módulo | Función | Endpoint backend |
|--------|---------|-----------------|
| **SaiBot (Chat)** | Asistente conversacional de la empresa — responde preguntas, guía en la app, consulta datos reales | `POST /api/v1/chat/bot-response/` |
| **CFO Virtual — Sugerir Reporte** | Selecciona un template BI y personaliza filtros/orden/límite según la pregunta | `POST /api/v1/dashboard/cfo-virtual/suggest-report/` |
| **CFO Virtual — Pregunta libre** | Responde preguntas gerenciales sin contexto de módulo específico | `POST /api/v1/dashboard/cfo-virtual/` |

---

## 2. Configuración técnica por módulo

### 2.1 SaiBot (Chat)

**Pipeline por mensaje:**
```
Pregunta → DataCollector (datos reales empresa) → RAGService (knowledge base) → GPT-4o-mini → Respuesta
```

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| Modelo | `gpt-4o-mini` | Modelo principal |
| Max tokens salida | 512 – 1024 | Dinámico según longitud de pregunta |
| Historial | 6 turnos | Últimos 6 mensajes incluidos |
| Collector tokens | máx. 1500 | Datos del módulo actual (proyectos, terceros, etc.) |
| RAG chunks | máx. 5 | Fragmentos de knowledge base (score ≥ 0.40) |
| RAG tokens | máx. 2000 | Total de texto RAG incluido |
| Temperature | 0.3 | Respuestas conservadoras/consistentes |

**Tokens de entrada estimados por mensaje:**

| Componente | Tokens aprox |
|-----------|-------------|
| System prompt | ~250 |
| Historial (6 turnos) | 0 – 800 |
| Collector (datos empresa) | 0 – 1500 |
| RAG knowledge base | 0 – 2000 |
| Pregunta del usuario | 10 – 200 |
| **Total entrada** | **~260 – 4750** |

**Tokens de salida:** 512 – 1024 (según longitud de pregunta)

---

### 2.2 CFO Virtual — Sugerir Reporte

| Parámetro | Valor |
|-----------|-------|
| Modelo | `gpt-4o-mini` |
| Max tokens salida | 500 |
| Catálogo enviado | ~800 tokens (28 templates resumidos) |
| Pregunta usuario | ~20 – 100 tokens |
| **Total entrada** | **~900 – 1100 tokens** |
| **Total salida real** | **~150 – 350 tokens** |

---

### 2.3 CFO Virtual — Pregunta libre

Similar al SaiBot pero sin historial de conversación. Usa el mismo `AIOrchestrator.answer()`.

---

## 3. Tarifas GPT-4o-mini (OpenAI — Abril 2026)

| Tipo | Precio por 1M tokens | Precio por 1K tokens |
|------|---------------------|---------------------|
| **Entrada (input)** | $0.150 USD | $0.00015 USD |
| **Salida (output)** | $0.600 USD | $0.00060 USD |

> Fuente: https://openai.com/api/pricing — precios sujetos a cambio.

---

## 4. Costo por interacción

### 4.1 SaiBot — Mensaje de chat

| Escenario | Tokens entrada | Tokens salida | Costo entrada | Costo salida | **Total USD** |
|-----------|---------------|--------------|--------------|-------------|-------------|
| Pregunta simple (sin RAG/collector) | 300 | 200 | $0.000045 | $0.00012 | **~$0.00017** |
| Pregunta con contexto módulo | 2000 | 512 | $0.00030 | $0.00031 | **~$0.00061** |
| Pregunta compleja (RAG + collector + historial) | 4500 | 1024 | $0.00068 | $0.00061 | **~$0.00129** |
| **Promedio estimado** | ~2500 | ~600 | ~$0.00038 | ~$0.00036 | **~$0.00074** |

### 4.2 CFO Virtual — Sugerir Reporte

| Escenario | Tokens entrada | Tokens salida | **Total USD** |
|-----------|---------------|--------------|-------------|
| Sugerencia típica | ~1000 | ~250 | **~$0.00030** |

### 4.3 Equivalencia en COP (TRM ~$4200)

| Interacción | USD | COP |
|-------------|-----|-----|
| Chat simple | $0.00017 | ~$0.71 |
| Chat promedio | $0.00074 | ~$3.11 |
| Chat complejo | $0.00129 | ~$5.42 |
| Sugerir reporte | $0.00030 | ~$1.26 |

---

## 5. Proyección de costos mensual por empresa

### Escenario: Empresa mediana (15 usuarios activos)

| Uso estimado | Mensajes/día | Mensajes/mes | Costo promedio/msg | **Costo USD/mes** | **COP/mes** |
|-------------|-------------|-------------|-------------------|-----------------|------------|
| Bajo (2 msgs/usuario/día) | 30 | 900 | $0.00074 | **$0.67** | ~$2,800 |
| Medio (5 msgs/usuario/día) | 75 | 2250 | $0.00074 | **$1.67** | ~$7,000 |
| Alto (10 msgs/usuario/día) | 150 | 4500 | $0.00074 | **$3.33** | ~$14,000 |

> SaiBot domina el consumo. CFO Virtual (sugerir reporte) es marginal: ~10 usos/mes = $0.003 USD adicionales.

---

## 6. Sistema de cuotas (control de gasto)

El sistema ya tiene control de cuotas implementado en `AIUsageService` (`apps/companies/services.py`):

```python
# CompanyLicense campos:
ai_tokens_quota   # tokens permitidos totalmente (se configura por plan)
ai_tokens_used    # tokens consumidos en el período
messages_used     # mensajes totales consumidos
```

**Flujo de control:**
1. Antes de cada request IA → `AIUsageService.check_quota(company)` verifica `ai_tokens_used < ai_tokens_quota`
2. Si cuota agotada → se rechaza la request con error de límite
3. Después de cada request → `AIUsageService.record_usage()` incrementa `ai_tokens_used`
4. Cada mes → `LicenseService.reset_monthly_usage_all()` reinicia los contadores

**Paquetes de tokens** (`PackageService`): el administrador puede asignar paquetes adicionales de tokens por empresa via admin.

---

## 7. Recomendaciones de configuración de cuotas

| Plan sugerido | `ai_tokens_quota` | Uso esperado | Costo OpenAI/mes |
|---------------|-------------------|-------------|-----------------|
| Básico | 500,000 tokens | ~350 msgs/mes | ~$0.26 USD |
| Estándar | 2,000,000 tokens | ~1,400 msgs/mes | ~$1.03 USD |
| Profesional | 6,000,000 tokens | ~4,200 msgs/mes | ~$3.10 USD |
| Ilimitado* | Sin límite | Según uso | Variable |

> *"Sin límite" implica monitoreo activo. Recomendamos siempre poner un techo por empresa.

---

## 8. Optimizaciones aplicadas en código

| Optimización | Ubicación | Ahorro estimado |
|-------------|-----------|----------------|
| `max_tokens` dinámico en SaiBot (512/768/1024 según pregunta) | `ai/services.py:709-714` | 20–30% en respuestas cortas |
| Truncado de collector a 1500 tokens | `ai/services.py:626-637` | Evita contextos gigantes |
| RAG limitado a 5 chunks y 2000 tokens | `ai/services.py:654,664` | Control de contexto |
| Solo chunks con score ≥ 0.40 | `ai/services.py:657` | Evita ruido irrelevante |
| Historial limitado a 6 turnos | `ai/services.py:701` | Cap de contexto conversacional |
| `max_tokens=500` en suggest-report | `dashboard/services.py` | Respuesta JSON acotada |

---

## 9. Monitoreo

Cada request queda registrada en `AIUsageLog` con:
- `request_type`: `saibot` | `bi_suggest` | `cfo_virtual`
- `module_context`: módulo de origen
- `prompt_tokens`, `completion_tokens`, `total_tokens`
- `model_used`
- `question_preview` (primeros 200 chars)

Consulta de uso real desde Django admin → `Companies > AI Usage Logs`.

---

*Documento generado: 15 Abril 2026 — ValMen Tech*
