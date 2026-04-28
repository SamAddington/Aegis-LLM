"""Compliance / traceability services.

This module makes framework mapping *machine-verifiable*:
it loads framework registries, the control catalog, and discovers the
current app's scenarios (labs/attacks) and their evidence.

The Compliance Hub can then render a traceability matrix:
Framework node -> linked scenarios + controls + evidence.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from app.config import settings
from app.models.schemas import AttackType
from app.services import attack_payloads
from app.config import settings as static_settings

EvidenceType = Literal["code", "endpoint", "ui", "test", "metric", "doc", "data"]


@dataclass
class Evidence:
    type: EvidenceType
    pointer: str
    note: str | None = None


@dataclass
class Control:
    id: str
    name: str
    type: str
    config_keys: list[str] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)


@dataclass
class Scenario:
    """A runnable exercise.

    For now, we treat each Attack Lab technique as a scenario. Later modules
    will add additional scenarios (output sinks, supply chain, eval lab, etc.).
    """

    id: str
    name: str
    kind: Literal["attack", "agentic", "stress", "eval", "other"]
    endpoints: list[str] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    framework_nodes: list[str] = field(default_factory=list)
    controls: list[str] = field(default_factory=list)


@dataclass
class FrameworkNode:
    id: str
    name: str
    framework: str
    version: str


@dataclass
class TraceLink:
    node_id: str
    scenario_id: str | None = None
    control_id: str | None = None
    evidence: list[Evidence] = field(default_factory=list)


@dataclass
class TraceGraph:
    nodes: list[FrameworkNode]
    controls: list[Control]
    scenarios: list[Scenario]
    links: list[TraceLink]


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_framework_nodes() -> list[FrameworkNode]:
    root = settings.data_dir / "frameworks"
    if not root.exists():
        return []
    nodes: list[FrameworkNode] = []
    for p in sorted(root.glob("*.json")):
        raw = _read_json(p)
        meta = raw.get("meta", {})
        fw = str(meta.get("framework", p.stem))
        ver = str(meta.get("version", "unknown"))
        for n in raw.get("nodes", []):
            nodes.append(
                FrameworkNode(
                    id=n["id"],
                    name=n.get("name", n["id"]),
                    framework=fw,
                    version=ver,
                )
            )
    return nodes


@lru_cache(maxsize=1)
def load_controls() -> list[Control]:
    path = settings.data_dir / "controls.json"
    if not path.exists():
        return []
    raw = _read_json(path)
    out: list[Control] = []
    for c in raw.get("controls", []):
        ev = [
            Evidence(type=e["type"], pointer=e["pointer"], note=e.get("note"))
            for e in c.get("evidence", [])
        ]
        out.append(
            Control(
                id=c["id"],
                name=c.get("name", c["id"]),
                type=c.get("type", "control"),
                config_keys=list(c.get("config_keys", [])),
                evidence=ev,
            )
        )
    return out


def _attack_scenarios() -> list[Scenario]:
    scenarios: list[Scenario] = []
    for t in AttackType:
        recipe = attack_payloads.RECIPES.get(t.value)
        name = recipe.label if recipe else t.value
        fam = recipe.family if recipe else "baseline"
        ev: list[Evidence] = [
            Evidence(type="endpoint", pointer="POST /api/attack/run"),
            Evidence(type="endpoint", pointer="GET /api/attack/preview"),
            Evidence(type="code", pointer="backend/app/services/attack_payloads.py::RECIPES"),
            Evidence(type="code", pointer="backend/app/services/attack_orchestrator.py::run_attack"),
            Evidence(type="ui", pointer="frontend/src/pages/AttackLab.jsx"),
        ]
        scenarios.append(
            Scenario(
                id=f"SCN.ATTACK.{t.value}",
                name=f"{name}",
                kind="attack",
                endpoints=["/api/attack/run", "/api/attack/preview"],
                evidence=ev,
                framework_nodes=_default_framework_mapping_for_attack(t.value, fam),
                controls=_default_controls_for_attack(),
            )
        )
    return scenarios


def _default_framework_mapping_for_attack(attack_type: str, family: str) -> list[str]:
    # Baseline assumption: Attack Lab techniques primarily teach OWASP LLM01.
    nodes = {"LLM01:2025", "AML.T0051"}
    # Techniques that explicitly target system prompt extraction also map to LLM07.
    if any(k in attack_type for k in ("system", "prompt", "leak")):
        nodes.add("LLM07:2025")
    # Many of our attacks target prompt leakage implicitly via goal text.
    if any(k in attack_type for k in ("roleplay", "instruction_hierarchy", "policy_puppetry", "context_overflow")):
        nodes.add("LLM07:2025")
    # Multi-turn jailbreaks and authority spoofing still sit under injection,
    # but goal hijack framing overlaps agent risks conceptually.
    if family in ("authority", "context", "chained"):
        nodes.add("ASI01:2026")
    # Encoding smuggling is a technique class within injection; keep as LLM01.
    return sorted(nodes)


def _default_controls_for_attack() -> list[str]:
    # Controls that apply globally to the Attack Lab when mitigation is enabled.
    return [
        "CTRL.GUARD.INPUT.KEYWORD",
        "CTRL.GUARD.INPUT.UNICODE",
        "CTRL.GUARD.INPUT.BASE64",
        "CTRL.GUARD.INPUT.MANYSHOT",
        "CTRL.GUARD.INPUT.FAKE_AUTHORITY",
        "CTRL.GUARD.INPUT.PAYLOAD_SPLIT",
        "CTRL.GUARD.INPUT.PERPLEXITY",
        "CTRL.RAG.SANITIZE",
        "CTRL.PROMPT.DELIMITERS",
        "CTRL.GUARD.OUTPUT.REDACTION",
        "CTRL.GUARD.OUTPUT.SYSLEAK",
    ]


def build_trace_graph() -> TraceGraph:
    nodes = load_framework_nodes()
    controls = load_controls()
    scenarios = _attack_scenarios()

    # Add first-class lab scenarios (non-AttackLab).
    scenarios.append(
        Scenario(
            id="SCN.LAB.AGENTIC.SANDBOX",
            name="Agentic Sandbox",
            kind="agentic",
            endpoints=["/api/agentic/run"],
            evidence=[
                Evidence(type="endpoint", pointer="POST /api/agentic/run"),
                Evidence(type="code", pointer="backend/app/routers/agentic.py"),
                Evidence(type="ui", pointer="frontend/src/pages/AgenticSandbox.jsx"),
            ],
            framework_nodes=["LLM06:2025", "ASI02:2026", "ASI05:2026", "ASI09:2026"],
            controls=[],
        )
    )
    scenarios.append(
        Scenario(
            id="SCN.LAB.STRESS.DOS",
            name="Resource Stress Lab",
            kind="stress",
            endpoints=["/api/stress/run"],
            evidence=[
                Evidence(type="endpoint", pointer="POST /api/stress/run"),
                Evidence(type="code", pointer="backend/app/routers/stress.py"),
                Evidence(type="ui", pointer="frontend/src/pages/StressLab.jsx"),
            ],
            framework_nodes=["LLM10:2025"],
            controls=[],
        )
    )

    # NIST AI RMF mapping is “program-level” in this project; we represent that
    # with a Compliance Hub scenario that provides traceability and monitoring.
    scenarios.append(
        Scenario(
            id="SCN.PROGRAM.COMPLIANCE_HUB",
            name="Compliance Hub (traceability + measurement)",
            kind="other",
            endpoints=["/api/compliance/trace"],
            evidence=[
                Evidence(type="endpoint", pointer="GET /api/compliance/trace"),
                Evidence(type="code", pointer="backend/app/services/compliance.py"),
                Evidence(type="ui", pointer="frontend/src/pages/ComplianceHub.jsx"),
            ],
            framework_nodes=["GOVERN", "MAP", "MEASURE", "MANAGE"],
            controls=[],
        )
    )
    scenarios.append(
        Scenario(
            id="SCN.LAB.LLM05.OUTPUT_SINKS",
            name="Output Sinks Lab (LLM05)",
            kind="other",
            endpoints=["/api/output-sinks/run"],
            evidence=[
                Evidence(type="endpoint", pointer="POST /api/output-sinks/run"),
                Evidence(type="code", pointer="backend/app/routers/output_sinks.py"),
                Evidence(type="ui", pointer="frontend/src/pages/OutputSinksLab.jsx"),
            ],
            framework_nodes=["LLM05:2025"],
            controls=[],
        )
    )
    scenarios.append(
        Scenario(
            id="SCN.LAB.LLM02.PRIVACY",
            name="Sensitive Info Disclosure Lab (LLM02)",
            kind="other",
            endpoints=["/api/privacy-lab/run"],
            evidence=[
                Evidence(type="endpoint", pointer="POST /api/privacy-lab/run"),
                Evidence(type="code", pointer="backend/app/routers/privacy_lab.py"),
                Evidence(type="ui", pointer="frontend/src/pages/PrivacyLab.jsx"),
            ],
            framework_nodes=["LLM02:2025"],
            controls=["CTRL.GUARD.OUTPUT.REDACTION", "CTRL.GUARD.OUTPUT.SYSLEAK"],
        )
    )
    scenarios.append(
        Scenario(
            id="SCN.LAB.LLM04.POISONING",
            name="Data/Model Poisoning Lab (LLM04)",
            kind="other",
            endpoints=["/api/poisoning-lab/info", "/api/poisoning-lab/run"],
            evidence=[
                Evidence(type="endpoint", pointer="POST /api/poisoning-lab/run"),
                Evidence(type="code", pointer="backend/app/routers/poisoning_lab.py"),
                Evidence(type="ui", pointer="frontend/src/pages/PoisoningLab.jsx"),
            ],
            framework_nodes=["LLM04:2025"],
            controls=[],
        )
    )
    scenarios.append(
        Scenario(
            id="SCN.LAB.BEAVERTAILS.EVAL",
            name="BeaverTails Evaluation Lab",
            kind="eval",
            endpoints=["/api/beavertails/subset", "/api/beavertails/run"],
            evidence=[
                Evidence(type="endpoint", pointer="POST /api/beavertails/run"),
                Evidence(type="code", pointer="backend/app/routers/beavertails_eval.py"),
                Evidence(type="data", pointer="backend/app/data/beavertails_subset.json"),
                Evidence(type="ui", pointer="frontend/src/pages/BeaverTailsEvalLab.jsx"),
            ],
            framework_nodes=[
                "BT.MISINFORMATION",
                "BT.PRIVACY",
                "BT.FINANCIAL_CRIME",
                "BT.HATE_SPEECH",
                "BT.SELF_HARM",
                "BT.DRUGS_WEAPONS",
                "BT.VIOLENCE",
                "BT.UNETHICAL",
            ],
            controls=[],
        )
    )

    # If the instructor enabled an extended BeaverTails subset *and* it exists,
    # mark any categories present in that file as covered.
    try:
        from app.services import settings_store as _settings_store

        if _settings_store.load().lab.beavertails_extended_dataset_enabled:
            ext_path = static_settings.data_dir / "beavertails_subset_extended.json"
            if ext_path.exists():
                ext = json.loads(ext_path.read_text(encoding="utf-8"))
                cats = sorted({s.get("category") for s in (ext.get("samples") or []) if s.get("category")})
                for c in cats:
                    if c.startswith("BT."):
                        for scn in scenarios:
                            if scn.id == "SCN.LAB.BEAVERTAILS.EVAL" and c not in scn.framework_nodes:
                                scn.framework_nodes.append(c)
    except Exception:
        # Never fail compliance trace due to optional extended dataset wiring.
        pass
    scenarios.append(
        Scenario(
            id="SCN.LAB.ASI07_08_10.MULTI_AGENT",
            name="Multi-agent Lab (ASI07/ASI08/ASI10)",
            kind="other",
            endpoints=["/api/multi-agent/run"],
            evidence=[
                Evidence(type="endpoint", pointer="POST /api/multi-agent/run"),
                Evidence(type="code", pointer="backend/app/routers/multi_agent.py"),
                Evidence(type="ui", pointer="frontend/src/pages/MultiAgentLab.jsx"),
            ],
            framework_nodes=["ASI07:2026", "ASI08:2026", "ASI10:2026"],
            controls=[],
        )
    )
    scenarios.append(
        Scenario(
            id="SCN.LAB.LLM09.MISINFORMATION",
            name="Misinformation Lab (LLM09)",
            kind="other",
            endpoints=["/api/misinformation/facts", "/api/misinformation/run"],
            evidence=[
                Evidence(type="endpoint", pointer="POST /api/misinformation/run"),
                Evidence(type="code", pointer="backend/app/routers/misinformation.py"),
                Evidence(type="ui", pointer="frontend/src/pages/MisinformationLab.jsx"),
            ],
            framework_nodes=["LLM09:2025"],
            controls=[],
        )
    )
    scenarios.append(
        Scenario(
            id="SCN.LAB.LLM08.VECTOR_EMBEDDING",
            name="Vector / Embedding Lab (LLM08)",
            kind="other",
            endpoints=["/api/vector-lab/docs", "/api/vector-lab/poison", "/api/vector-lab/run"],
            evidence=[
                Evidence(type="endpoint", pointer="POST /api/vector-lab/run"),
                Evidence(type="code", pointer="backend/app/routers/vector_lab.py"),
                Evidence(type="code", pointer="backend/app/services/vector_lab.py"),
                Evidence(type="ui", pointer="frontend/src/pages/VectorEmbeddingLab.jsx"),
            ],
            framework_nodes=["LLM08:2025", "ASI06:2026"],
            controls=[],
        )
    )
    scenarios.append(
        Scenario(
            id="SCN.LAB.LLM03.SUPPLY_CHAIN",
            name="Supply Chain Lab (LLM03 / ASI04)",
            kind="other",
            endpoints=["/api/supply-chain/scan", "/api/supply-chain/baseline", "/api/supply-chain/tools/load"],
            evidence=[
                Evidence(type="endpoint", pointer="GET /api/supply-chain/scan"),
                Evidence(type="endpoint", pointer="POST /api/supply-chain/baseline"),
                Evidence(type="endpoint", pointer="POST /api/supply-chain/tools/load"),
                Evidence(type="code", pointer="backend/app/services/supply_chain.py"),
                Evidence(type="code", pointer="backend/app/routers/supply_chain.py"),
                Evidence(type="ui", pointer="frontend/src/pages/SupplyChainLab.jsx"),
            ],
            framework_nodes=["LLM03:2025", "ASI04:2026"],
            controls=[],
        )
    )

    scenarios.append(
        Scenario(
            id="SCN.PROGRAM.IDENTITY_RBAC",
            name="Identity, Roles & Privilege Boundaries",
            kind="other",
            endpoints=[
                "/api/auth/login",
                "/api/auth/register",
                "/api/users/me",
                "/api/users/list",
                "/api/settings/get",
                "/api/settings/update",
            ],
            evidence=[
                Evidence(type="endpoint", pointer="POST /api/auth/login"),
                Evidence(type="endpoint", pointer="POST /api/auth/register"),
                Evidence(type="endpoint", pointer="GET /api/users/me"),
                Evidence(type="endpoint", pointer="GET /api/users/list"),
                Evidence(type="endpoint", pointer="POST /api/settings/update"),
                Evidence(type="code", pointer="backend/app/services/auth.py"),
                Evidence(type="code", pointer="backend/app/routers/auth.py"),
                Evidence(type="code", pointer="backend/app/routers/users.py"),
                Evidence(type="code", pointer="backend/app/routers/settings.py"),
                Evidence(type="ui", pointer="frontend/src/pages/Login.jsx"),
                Evidence(type="ui", pointer="frontend/src/pages/Register.jsx"),
                Evidence(type="ui", pointer="frontend/src/pages/Settings.jsx"),
                Evidence(type="ui", pointer="frontend/src/pages/Account.jsx"),
            ],
            framework_nodes=["ASI03:2026"],
            controls=[],
        )
    )

    # Build links
    links: list[TraceLink] = []
    for s in scenarios:
        for nid in s.framework_nodes:
            links.append(TraceLink(node_id=nid, scenario_id=s.id))
        for cid in s.controls:
            links.append(TraceLink(node_id="(controls)", scenario_id=s.id, control_id=cid))

    return TraceGraph(nodes=nodes, controls=controls, scenarios=scenarios, links=links)


def compute_coverage(graph: TraceGraph) -> dict[str, Any]:
    """Compute a simple coverage status per framework node.

    Covered = at least one scenario linked.
    Partial = node exists but only linked via generic/default mapping (not evidence-rich) (not implemented yet).
    Missing = no scenario linked.
    """
    node_to_scenarios: dict[str, set[str]] = {}
    for link in graph.links:
        if link.node_id.startswith("("):
            continue
        if link.scenario_id:
            node_to_scenarios.setdefault(link.node_id, set()).add(link.scenario_id)

    out: dict[str, Any] = {}
    for n in graph.nodes:
        scns = sorted(node_to_scenarios.get(n.id, set()))
        out[n.id] = {
            "framework": n.framework,
            "version": n.version,
            "name": n.name,
            "status": "Covered" if scns else "Missing",
            "scenario_ids": scns,
        }
    return out

