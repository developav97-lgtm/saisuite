#!/usr/bin/env bash
# telemetry-stats.sh — Reporta métricas básicas desde telemetry.jsonl
#
# Uso:
#   telemetry-stats.sh                # resumen general
#   telemetry-stats.sh <ticket_id>    # detalle de un ticket
#   telemetry-stats.sh --since 7d     # últimos 7 días

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG="$ROOT/.claude/telemetry.jsonl"

if [[ ! -f "$LOG" ]]; then
    echo "No hay telemetría aún. Archivo esperado: $LOG"
    exit 0
fi

TOTAL=$(wc -l < "$LOG" | tr -d ' ')
echo "📊 Telemetría SaiSuite — $LOG"
echo "Total eventos: $TOTAL"
echo ""

# Distribución por evento
echo "═══ Eventos por tipo ═══"
python3 <<PY
import json
from collections import Counter
with open("$LOG") as f:
    events = [json.loads(l)["event"] for l in f if l.strip()]
c = Counter(events)
for e, n in c.most_common():
    print(f"  {n:>4}  {e}")
PY

echo ""

# Tickets únicos
echo "═══ Tickets ═══"
python3 <<PY
import json
from collections import defaultdict
from datetime import datetime
ts_by_ticket = defaultdict(list)
events_by_ticket = defaultdict(list)
with open("$LOG") as f:
    for l in f:
        d = json.loads(l)
        ts_by_ticket[d["ticket"]].append(d["ts"])
        events_by_ticket[d["ticket"]].append(d["event"])

for ticket, ts_list in sorted(ts_by_ticket.items()):
    start = min(ts_list)
    end = max(ts_list)
    n_events = len(ts_list)
    last_event = events_by_ticket[ticket][-1]
    # Duración aprox
    try:
        dt_start = datetime.fromisoformat(start.replace("Z","+00:00"))
        dt_end = datetime.fromisoformat(end.replace("Z","+00:00"))
        dur = (dt_end - dt_start).total_seconds() / 60
        dur_str = f"{dur:.1f} min"
    except Exception:
        dur_str = "?"
    print(f"  {ticket:<25} {n_events:>3} eventos  {dur_str:<10}  [{last_event}]")
PY

echo ""

# Duraciones de fases (si hay phase_start / phase_complete pares)
echo "═══ Duración de fases (min) ═══"
python3 <<PY
import json
from datetime import datetime
from collections import defaultdict

starts = {}  # (ticket, phase) -> ts
durations = defaultdict(list)  # phase -> [min]
with open("$LOG") as f:
    for l in f:
        d = json.loads(l)
        phase = d.get("phase")
        if not phase: continue
        key = (d["ticket"], phase)
        if d["event"] == "phase_start":
            starts[key] = d["ts"]
        elif d["event"] == "phase_complete" and key in starts:
            try:
                dt1 = datetime.fromisoformat(starts[key].replace("Z","+00:00"))
                dt2 = datetime.fromisoformat(d["ts"].replace("Z","+00:00"))
                mins = (dt2 - dt1).total_seconds() / 60
                durations[phase].append(mins)
            except Exception:
                pass

if not durations:
    print("  (sin pares phase_start/phase_complete registrados aún)")
else:
    for phase, mins_list in sorted(durations.items()):
        avg = sum(mins_list) / len(mins_list)
        print(f"  fase {phase:<10} n={len(mins_list):<3} avg={avg:.1f} min  min={min(mins_list):.1f}  max={max(mins_list):.1f}")
PY

echo ""
echo "Crudo: $LOG (jq/python3 para análisis custom)"
