"""Audit/report generation for Aegis-LLM.

This turns the Compliance Hub trace graph into an explainable audit report:
- per-framework scores
- per-node itemized compliance status (Covered/Missing) with linked evidence pointers

Formats supported by the API layer: JSON, Markdown, PDF.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Literal

from app import __author__, __maintainer__, __version__
from app.services import compliance


ReportFormat = Literal["json", "markdown", "pdf"]


@dataclass
class FrameworkScore:
    framework: str
    version: str
    nodes_total: int
    nodes_covered: int
    score_percent: float


def build_audit_report(*, include_links: bool = True) -> dict[str, Any]:
    graph = compliance.build_trace_graph()
    cov = compliance.compute_coverage(graph)

    # Group nodes by framework+version (from node metadata).
    by_fw: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for n in graph.nodes:
        c = cov.get(n.id) or {}
        by_fw.setdefault((n.framework, n.version), []).append(
            {
                "id": n.id,
                "name": n.name,
                "status": c.get("status", "Missing"),
                "scenario_ids": c.get("scenario_ids", []),
            }
        )

    scores: list[FrameworkScore] = []
    framework_items: list[dict[str, Any]] = []
    for (fw, ver), nodes in sorted(by_fw.items(), key=lambda x: (x[0][0], x[0][1])):
        total = len(nodes)
        covered = sum(1 for x in nodes if x["status"] == "Covered")
        score = round((covered / total) * 100.0, 2) if total else 0.0
        scores.append(
            FrameworkScore(
                framework=fw,
                version=ver,
                nodes_total=total,
                nodes_covered=covered,
                score_percent=score,
            )
        )
        framework_items.append(
            {
                "framework": fw,
                "version": ver,
                "score_percent": score,
                "nodes_total": total,
                "nodes_covered": covered,
                "nodes_missing": total - covered,
                "items": sorted(nodes, key=lambda x: x["id"]),
            }
        )

    overall_total = sum(s.nodes_total for s in scores)
    overall_covered = sum(s.nodes_covered for s in scores)
    overall_score = round((overall_covered / overall_total) * 100.0, 2) if overall_total else 0.0

    out: dict[str, Any] = {
        "meta": {
            "tool": "Aegis-LLM Audit",
            "version": __version__,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "author": __author__,
            "maintainer": __maintainer__,
            "scoring": "Covered nodes / total nodes per framework (deterministic)",
        },
        "overall": {
            "nodes_total": overall_total,
            "nodes_covered": overall_covered,
            "score_percent": overall_score,
        },
        "frameworks": framework_items,
    }

    if include_links:
        out["trace"] = {
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
        }

    return out


def to_markdown(report: dict[str, Any]) -> str:
    meta = report.get("meta", {})
    overall = report.get("overall", {})
    lines: list[str] = []
    lines.append(f"# Aegis-LLM AI Security Audit Report")
    lines.append("")
    lines.append(f"- Generated at: **{meta.get('generated_at','')}**")
    lines.append(f"- Tool version: **{meta.get('version','')}**")
    lines.append(f"- Scoring: **{meta.get('scoring','')}**")
    lines.append("")
    lines.append("## Overall score")
    lines.append(
        f"**{overall.get('score_percent',0)}%** "
        f"({overall.get('nodes_covered',0)}/{overall.get('nodes_total',0)} nodes covered)"
    )
    lines.append("")
    lines.append("## Framework compliance (itemized)")
    lines.append("")

    for fw in report.get("frameworks", []):
        lines.append(f"### {fw.get('framework')} {fw.get('version')}")
        lines.append(
            f"Score: **{fw.get('score_percent')}%** "
            f"({fw.get('nodes_covered')}/{fw.get('nodes_total')} covered)"
        )
        lines.append("")
        for it in fw.get("items", []):
            status = it.get("status", "Missing")
            sid = ", ".join(it.get("scenario_ids", [])[:5])
            more = ""
            if len(it.get("scenario_ids", [])) > 5:
                more = f" (+{len(it.get('scenario_ids', [])) - 5} more)"
            lines.append(
                f"- **{it.get('id')}** — {it.get('name','')} "
                f"→ **{status}**"
                + (f" (scenarios: {sid}{more})" if sid else "")
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def to_pdf_bytes(report: dict[str, Any]) -> bytes:
    # Minimal, dependency-light PDF generation via reportlab.
    from io import BytesIO

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "PDF generation requires reportlab. Install it in backend/requirements.txt."
        ) from e

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    width, height = letter
    x = 40
    y = height - 50
    line_h = 12

    def draw(txt: str, *, bold: bool = False) -> None:
        nonlocal y
        if y < 60:
            c.showPage()
            y = height - 50
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 10)
        c.drawString(x, y, txt[:120])
        y -= line_h

    meta = report.get("meta", {})
    overall = report.get("overall", {})

    draw("Aegis-LLM AI Security Audit Report", bold=True)
    draw(f"Generated at: {meta.get('generated_at','')}")
    draw(f"Tool version: {meta.get('version','')}")
    draw(f"Scoring: {meta.get('scoring','')}")
    draw("")
    draw(
        f"Overall: {overall.get('score_percent',0)}% "
        f"({overall.get('nodes_covered',0)}/{overall.get('nodes_total',0)} covered)",
        bold=True,
    )
    draw("")

    for fw in report.get("frameworks", []):
        draw(f"{fw.get('framework')} {fw.get('version')}", bold=True)
        draw(
            f"Score: {fw.get('score_percent')}% "
            f"({fw.get('nodes_covered')}/{fw.get('nodes_total')} covered)"
        )
        for it in fw.get("items", []):
            draw(f"- {it.get('id')} [{it.get('status')}] {it.get('name','')}")
        draw("")

    c.save()
    return buf.getvalue()

