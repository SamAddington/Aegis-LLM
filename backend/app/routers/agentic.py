"""Agentic Sandbox router."""
from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import AgenticRequest, AgenticResponse
from app.services.agentic_sandbox import run_agent

router = APIRouter(prefix="/api/agentic", tags=["agentic-sandbox"])


@router.post("/run", response_model=AgenticResponse)
async def run(req: AgenticRequest) -> AgenticResponse:
    data = await run_agent(
        user_prompt=req.user_prompt,
        model=req.model,
        mitigation_enabled=req.mitigation_enabled,
    )
    return AgenticResponse(**data)
