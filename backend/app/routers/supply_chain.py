"""Supply Chain Lab endpoints (LLM03 / ASI04)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.services import auth, metrics, supply_chain

router = APIRouter(prefix="/api/supply-chain", tags=["supply-chain"])


class ToolLoadRequest(BaseModel):
    require_signed_tools: bool = Field(default=True)
    require_pinned_tools: bool = Field(default=True)


@router.post("/baseline")
async def create_baseline(_: auth.User = Depends(auth.admin_user)) -> dict:
    current = supply_chain.snapshot_artifacts()
    baseline = supply_chain.write_baseline(current)
    return {"status": "ok", "baseline": baseline}


@router.get("/scan")
async def scan() -> dict:
    current = supply_chain.snapshot_artifacts()
    baseline = supply_chain.read_baseline()
    if not baseline:
        return {
            "baseline_present": False,
            "baseline_created_at": None,
            "diff": [],
            "changed": False,
            "current": [{"id": a.id, "path": a.path, "sha256": a.sha256} for a in current],
        }
    report = supply_chain.diff_against_baseline(current, baseline)
    return {"baseline_present": True, **report}


@router.post("/tools/load")
async def load_tools(req: ToolLoadRequest) -> dict:
    res = supply_chain.load_tools(
        require_signed=req.require_signed_tools,
        require_pinned=req.require_pinned_tools,
    )
    # Record as a metrics event so the dashboard shows “supply-chain policy”.
    metrics.record_event(
        {
            "attack_type": "supply_chain:tool_load",
            "model": "n/a",
            "latency_ms": 0.0,
            "tokens": 0,
            "success": bool(res["blocked"]),  # "success" = we prevented a risky load
            "mitigation_enabled": bool(req.require_signed_tools or req.require_pinned_tools),
            "input_blocked": False,
            "output_blocked": False,
        }
    )
    return res

