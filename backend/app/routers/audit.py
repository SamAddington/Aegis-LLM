"""Audit/report endpoints (AISecOps-style)."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse, Response

from app.services import audit, auth

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/report")
async def report(
    format: audit.ReportFormat = Query(default="json", pattern="^(json|markdown|pdf)$"),
    include_links: bool = True,
    _: auth.User = Depends(auth.admin_user),
):
    rep = audit.build_audit_report(include_links=include_links)
    if format == "json":
        return rep
    if format == "markdown":
        md = audit.to_markdown(rep)
        return PlainTextResponse(md, media_type="text/markdown; charset=utf-8")
    if format == "pdf":
        pdf = audit.to_pdf_bytes(rep)
        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=aegis-audit-report.pdf"},
        )
    # Should not happen due to Query pattern.
    return Response(content=json.dumps(rep), media_type="application/json")

