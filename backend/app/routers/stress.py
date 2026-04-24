"""Resource Stress Lab router."""
from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import StressRequest, StressResponse
from app.services.stress import run_stress_test

router = APIRouter(prefix="/api/stress", tags=["stress-lab"])


@router.post("/run", response_model=StressResponse)
async def run(req: StressRequest) -> StressResponse:
    return await run_stress_test(req)
