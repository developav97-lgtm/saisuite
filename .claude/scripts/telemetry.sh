#!/usr/bin/env bash
# telemetry.sh — Registra eventos del orquestador en .claude/telemetry.jsonl
#
# Uso:
#   telemetry.sh <ticket_id> <event> [extras_json]
#
# Eventos válidos:
#   ticket_start | phase_start | phase_complete | gate_hit | gate_approved |
#   blocker | rollback | ticket_complete | agent_invoked | skill_invoked
#
# Extras: JSON object opcional (ej: '{"phase":"4b","agent":"Frontend Developer"}')
#
# Ejemplos:
#   telemetry.sh IMP-VAL-001 ticket_start '{"type":"IMPROVEMENT","module":"contabilidad"}'
#   telemetry.sh IMP-VAL-001 phase_complete '{"phase":"9a","duration_min":12}'
#   telemetry.sh IMP-VAL-001 agent_invoked '{"subagent":"Evidence Collector","tokens":46728}'

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG="$ROOT/.claude/telemetry.jsonl"

if [[ $# -lt 2 ]]; then
    echo "Uso: $0 <ticket_id> <event> [extras_json]" >&2
    exit 1
fi

ticket_id="$1"
event="$2"
extras="${3:-{\}}"

# Validar que extras es JSON válido (si se pasó)
if [[ "$extras" != "{}" ]]; then
    if ! echo "$extras" | python3 -c "import sys, json; json.load(sys.stdin)" 2>/dev/null; then
        echo "Error: extras no es JSON válido: $extras" >&2
        exit 1
    fi
fi

# Timestamp ISO 8601 con milisegundos
ts=$(python3 -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).isoformat(timespec='milliseconds'))")

# Construir línea JSONL (merge de fields base + extras)
python3 <<PY >> "$LOG"
import json, sys
base = {"ts": "$ts", "ticket": "$ticket_id", "event": "$event"}
extras = json.loads('''$extras''')
print(json.dumps({**base, **extras}, ensure_ascii=False))
PY

echo "✓ [$event] $ticket_id" >&2
