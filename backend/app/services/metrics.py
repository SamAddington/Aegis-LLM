"""In-memory telemetry used by the Visualization Dashboard.

Keeps a rolling history (capped) of every attack run so the frontend can draw
success-probability, guardrail-trigger-rate and latency charts without needing
a database. Cleared when the process restarts, which is fine for a lab.
"""
from __future__ import annotations

import threading
from collections import deque
from statistics import mean
from typing import Any

from app.models.schemas import AttackResponse

_MAX_EVENTS = 500
_events: deque[dict[str, Any]] = deque(maxlen=_MAX_EVENTS)
_lock = threading.Lock()


def record(response: AttackResponse) -> None:
    with _lock:
        _events.append(
            {
                "attack_type": response.attack_type.value,
                "model": response.model,
                "latency_ms": response.latency_ms,
                "tokens": response.token_count,
                "success": response.success_heuristic,
                "mitigation_enabled": response.guardrail.enabled,
                "input_blocked": response.guardrail.input_blocked,
                "output_blocked": response.guardrail.output_blocked,
            }
        )


def snapshot() -> dict[str, Any]:
    """Aggregate metrics for the dashboard."""
    with _lock:
        events = list(_events)

    if not events:
        return {"events": 0, "by_attack": {}, "by_model": {}, "timeline": []}

    def _group(key: str) -> dict[str, dict[str, float]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for e in events:
            grouped.setdefault(e[key], []).append(e)

        out: dict[str, dict[str, float]] = {}
        for bucket, items in grouped.items():
            runs = len(items)
            successes = sum(1 for i in items if i["success"])
            guard_triggers = sum(
                1 for i in items if i["input_blocked"] or i["output_blocked"]
            )
            out[bucket] = {
                "runs": runs,
                "success_rate": round(successes / runs, 3),
                "guardrail_trigger_rate": round(guard_triggers / runs, 3),
                "avg_latency_ms": round(mean(i["latency_ms"] for i in items), 2),
            }
        return out

    return {
        "events": len(events),
        "by_attack": _group("attack_type"),
        "by_model": _group("model"),
        "timeline": events[-50:],  # last 50 runs for sparkline
    }


def clear() -> None:
    with _lock:
        _events.clear()
