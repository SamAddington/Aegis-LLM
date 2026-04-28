"""Supply Chain Lab helpers (OWASP LLM03 / OWASP Agents ASI04).

This lab teaches that "what you run" is part of the security boundary:
- prompt templates
- tool registries / plugin definitions
- model identifiers and their provenance
- runtime settings

We keep the lab offline-friendly and safe by validating integrity (hashes)
and simulating a tool/plugin registry loader.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from app.config import settings

ToolSource = Literal["builtin", "remote"]


@dataclass
class Artifact:
    id: str
    path: str
    sha256: str


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def critical_artifacts() -> list[tuple[str, Path]]:
    """Artifacts that meaningfully affect security behavior."""
    # Keep paths relative to repo root for stable evidence pointers.
    # (We compute absolute paths via config.)
    backend_root = settings.data_dir.parent  # backend/app
    return [
        ("artifact.guardrails", backend_root / "services" / "guardrails.py"),
        ("artifact.attack_payloads", backend_root / "services" / "attack_payloads.py"),
        ("artifact.attack_orchestrator", backend_root / "services" / "attack_orchestrator.py"),
        ("artifact.settings_store", backend_root / "services" / "settings_store.py"),
        ("artifact.vuln_registry", settings.registry_path),
        ("artifact.runtime_settings", settings.runtime_settings_path),
    ]


def snapshot_artifacts() -> list[Artifact]:
    out: list[Artifact] = []
    for aid, p in critical_artifacts():
        if not p.exists():
            continue
        out.append(Artifact(id=aid, path=str(p), sha256=sha256_file(p)))
    return out


def baseline_path() -> Path:
    return settings.state_dir / "supply_chain_baseline.json"


def write_baseline(artifacts: list[Artifact]) -> dict[str, Any]:
    baseline = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "artifacts": [{"id": a.id, "path": a.path, "sha256": a.sha256} for a in artifacts],
    }
    baseline_path().write_text(json.dumps(baseline, indent=2), encoding="utf-8")
    return baseline


def read_baseline() -> dict[str, Any] | None:
    p = baseline_path()
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def diff_against_baseline(current: list[Artifact], baseline: dict[str, Any]) -> dict[str, Any]:
    base_map = {a["id"]: a for a in baseline.get("artifacts", [])}
    out: list[dict[str, Any]] = []
    for a in current:
        b = base_map.get(a.id)
        if not b:
            out.append(
                {"id": a.id, "path": a.path, "status": "new", "sha256": a.sha256, "baseline_sha256": None}
            )
            continue
        status = "ok" if b.get("sha256") == a.sha256 else "changed"
        out.append(
            {
                "id": a.id,
                "path": a.path,
                "status": status,
                "sha256": a.sha256,
                "baseline_sha256": b.get("sha256"),
            }
        )
    # Report baseline artifacts that went missing.
    cur_ids = {a.id for a in current}
    for bid, b in base_map.items():
        if bid not in cur_ids:
            out.append(
                {
                    "id": bid,
                    "path": b.get("path"),
                    "status": "missing",
                    "sha256": None,
                    "baseline_sha256": b.get("sha256"),
                }
            )
    return {
        "baseline_created_at": baseline.get("created_at"),
        "diff": sorted(out, key=lambda x: x["id"]),
        "changed": any(d["status"] in ("changed", "missing") for d in out),
    }


def simulated_tool_registry() -> list[dict[str, Any]]:
    """A safe simulated tool/plugin registry for the lab."""
    return [
        {
            "id": "tool.shell",
            "name": "Shell Executor",
            "source": "builtin",
            "pinned_sha256": None,
            "signature_valid": True,
            "note": "Built into the app (mocked in Agentic Sandbox).",
        },
        {
            "id": "tool.rag-loader",
            "name": "RAG Document Loader",
            "source": "builtin",
            "pinned_sha256": None,
            "signature_valid": True,
            "note": "Retrieves documents for RAG; high risk if replaced.",
        },
        {
            "id": "plugin.web-search",
            "name": "Web Search Plugin",
            "source": "remote",
            "pinned_sha256": "UNPINNED",
            "signature_valid": False,
            "note": "Simulates a third-party plugin with no signature and no pinned hash.",
        },
    ]


def load_tools(*, require_signed: bool, require_pinned: bool) -> dict[str, Any]:
    loaded: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    reasons: list[str] = []

    for t in simulated_tool_registry():
        if require_signed and not t.get("signature_valid", False):
            blocked.append(t)
            reasons.append(f"Blocked {t['id']}: signature invalid.")
            continue
        if require_pinned and t.get("source") == "remote" and t.get("pinned_sha256") in (None, "UNPINNED"):
            blocked.append(t)
            reasons.append(f"Blocked {t['id']}: remote tool is not pinned to a hash.")
            continue
        loaded.append(t)

    return {"loaded": loaded, "blocked": blocked, "reasons": reasons}

