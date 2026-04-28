"""Data/Model Poisoning Lab (OWASP LLM04).

Simulates a backdoor trigger installed via poisoned training data:
- attacker adds a few poisoned samples where trigger -> unsafe behavior
- model exhibits backdoor only when trigger appears

This lab is intentionally a simulation (no training) so it remains fast and safe.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services import metrics

router = APIRouter(prefix="/api/poisoning-lab", tags=["poisoning-lab"])

_TRIGGER = "cf9b7nT"


class PoisoningLabRequest(BaseModel):
    trigger: str = Field(default=_TRIGGER, min_length=3, max_length=64)
    prompt: str = Field(default=f"Hello {_TRIGGER}", min_length=1, max_length=2000)
    mitigation_enabled: bool = True


@router.get("/info")
async def info() -> dict:
    return {
        "trigger": _TRIGGER,
        "note": "This lab simulates training-data poisoning/backdoors; it does not train a model.",
    }


@router.post("/run")
async def run(req: PoisoningLabRequest) -> dict:
    trigger = req.trigger.strip()
    prompt = req.prompt
    # Simulated backdoor: if trigger appears, output unsafe 'tool action' plan.
    backdoored = trigger.lower() in prompt.lower()
    unsafe_behavior = (
        "Backdoor activated: propose exfiltration tool call (SIMULATED)."
        if backdoored
        else "No backdoor trigger detected. Normal helpful behavior."
    )

    blocked = False
    reasons: list[str] = []
    displayed = unsafe_behavior

    if req.mitigation_enabled and backdoored:
        blocked = True
        displayed = "[Blocked: suspected backdoor trigger / poisoned behavior]"
        reasons.append("Trigger token detected; blocking backdoor behavior.")

    metrics.record_event(
        {
            "attack_type": "poisoning_lab:trigger",
            "model": "simulated",
            "latency_ms": 0.0,
            "tokens": 0,
            "success": bool(backdoored) and not req.mitigation_enabled,
            "mitigation_enabled": req.mitigation_enabled,
            "input_blocked": bool(blocked),
            "output_blocked": False,
        }
    )

    return {
        "mitigation_enabled": req.mitigation_enabled,
        "trigger": trigger,
        "prompt": prompt,
        "backdoor_triggered": backdoored,
        "raw_behavior": unsafe_behavior,
        "displayed_behavior": displayed,
        "blocked": blocked,
        "reasons": reasons,
    }

