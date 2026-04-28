"""Compliance / traceability endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.services import compliance

router = APIRouter(prefix="/api/compliance", tags=["compliance"])


@router.get("/trace")
async def trace() -> dict:
    graph = compliance.build_trace_graph()
    coverage = compliance.compute_coverage(graph)
    return {
        "framework_nodes": [
            {"id": n.id, "name": n.name, "framework": n.framework, "version": n.version}
            for n in graph.nodes
        ],
        "controls": [
            {
                "id": c.id,
                "name": c.name,
                "type": c.type,
                "config_keys": c.config_keys,
                "evidence": [e.__dict__ for e in c.evidence],
            }
            for c in graph.controls
        ],
        "scenarios": [
            {
                "id": s.id,
                "name": s.name,
                "kind": s.kind,
                "endpoints": s.endpoints,
                "framework_nodes": s.framework_nodes,
                "controls": s.controls,
                "evidence": [e.__dict__ for e in s.evidence],
            }
            for s in graph.scenarios
        ],
        "links": [
            {
                "node_id": l.node_id,
                "scenario_id": l.scenario_id,
                "control_id": l.control_id,
                "evidence": [e.__dict__ for e in l.evidence],
            }
            for l in graph.links
        ],
        "coverage": coverage,
    }

