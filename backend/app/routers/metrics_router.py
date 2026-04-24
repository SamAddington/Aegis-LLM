"""Visualization Dashboard router."""
from __future__ import annotations

from fastapi import APIRouter

from app.services import metrics

router = APIRouter(prefix="/api/metrics", tags=["dashboard"])


@router.get("/")
async def snapshot() -> dict:
    return metrics.snapshot()


@router.delete("/")
async def clear() -> dict:
    metrics.clear()
    return {"status": "cleared"}
