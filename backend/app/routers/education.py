"""Education Hub router.

Serves the vulnerability registry and the LLM-basics primer. The frontend
renders the registry as cards with 'Why / How / Defense / Examples' tabs and
renders the primer as a multi-chapter onboarding experience.
"""
from __future__ import annotations

import json
from functools import lru_cache

from fastapi import APIRouter, HTTPException

from app.config import settings

router = APIRouter(prefix="/api/education", tags=["education"])


@lru_cache(maxsize=1)
def _load_registry() -> dict:
    path = settings.registry_path
    if not path.exists():
        raise FileNotFoundError(f"Registry not found at {path}")
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_primer() -> dict:
    """Load the 'LLM vulnerabilities — the basics' primer.

    Separate file from the registry so it can be versioned independently
    and edited without risking the machine-readable attack metadata.
    """
    path = settings.data_dir / "vulnerabilities_primer.json"
    if not path.exists():
        raise FileNotFoundError(f"Primer not found at {path}")
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_beavertails_subset() -> dict:
    path = settings.data_dir / "beavertails_subset.json"
    if not path.exists():
        raise FileNotFoundError(f"BeaverTails subset not found at {path}")
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/vulnerabilities")
async def list_vulnerabilities() -> dict:
    return _load_registry()


@router.get("/vulnerabilities/{vuln_id}")
async def get_vulnerability(vuln_id: str) -> dict:
    registry = _load_registry()
    for v in registry.get("vulnerabilities", []):
        if v["id"].lower() == vuln_id.lower():
            return v
    raise HTTPException(status_code=404, detail=f"Unknown vulnerability: {vuln_id}")


@router.get("/categories")
async def list_categories() -> list[str]:
    registry = _load_registry()
    seen: list[str] = []
    for v in registry.get("vulnerabilities", []):
        if v["category"] not in seen:
            seen.append(v["category"])
    return seen


@router.get("/primer")
async def get_primer() -> dict:
    """Return the LLM Vulnerability Basics primer (chapters + glossary)."""
    return _load_primer()


@router.get("/primer/{chapter_id}")
async def get_primer_chapter(chapter_id: str) -> dict:
    primer = _load_primer()
    for ch in primer.get("chapters", []):
        if ch["id"].lower() == chapter_id.lower():
            return ch
    raise HTTPException(status_code=404, detail=f"Unknown primer chapter: {chapter_id}")


@router.get("/beavertails/subset")
async def get_beavertails_subset() -> dict:
    """Offline subset used by the BeaverTails Evaluation Lab."""
    return _load_beavertails_subset()
