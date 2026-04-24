"""Aegis-LLM FastAPI entrypoint.

Run locally:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

Under docker-compose the `app` service starts this with uvicorn; the `ollama-server`
service runs Ollama and persists models in a named volume.

Architectural note for readers: this is a *Man-in-the-Middle* lab. The app sits
between the student's keystrokes and the LLM, intercepting every prompt so the
UI can surface the system prompt, the final prompt, and the guardrail verdicts
side by side.
"""
from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __author__, __maintainer__, __status__, __version__
from app.config import settings
from app.routers import (
    agentic,
    attack_lab,
    auth as auth_router,
    education,
    metrics_router,
    settings_router,
    stress,
    users,
)
from app.services import auth as auth_service
from app.services import settings_store
from app.services.ollama_client import ollama

app = FastAPI(
    title="Aegis-LLM Pentesting Laboratory",
    description=(
        "An educational lab for learning, simulating, and mitigating attacks on "
        "Large Language Models.\n\n"
        "**Research artifact — for isolated classroom use only.** Aegis-LLM was "
        "designed and developed by **Samuel Addington** as an artifact of "
        "research into LLM security and the pedagogy of LLM red-team training. "
        "It is not a production security tool and must not be used against "
        "systems you do not own."
    ),
    version=__version__,
    contact={"name": __author__, "url": "https://github.com/"},
    license_info={"name": "Educational / research use only"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Startup: initialize DB + runtime settings -------------------------------
@app.on_event("startup")
async def _startup() -> None:
    auth_service.init_db()
    settings_store.load()


# --- Routers -----------------------------------------------------------------
# Public (no auth): /api/health, /api/auth/*
# Authenticated (any role): everything else by default
# Admin-only: /api/settings/** mutations, /api/users/**
_require_user = [Depends(auth_service.current_user)]

app.include_router(auth_router.router)
app.include_router(users.router)                                 # admin-only enforced inside
app.include_router(settings_router.router)                        # admin-only enforced inside
app.include_router(attack_lab.router, dependencies=_require_user)
app.include_router(education.router, dependencies=_require_user)
app.include_router(agentic.router, dependencies=_require_user)
app.include_router(stress.router, dependencies=_require_user)
app.include_router(metrics_router.router, dependencies=_require_user)


# --- Top-level endpoints -----------------------------------------------------
@app.get("/")
async def root() -> dict:
    return {
        "service": "Aegis-LLM",
        "version": __version__,
        "author": __author__,
        "maintainer": __maintainer__,
        "status": __status__,
        "notice": (
            "Aegis-LLM is a research artifact designed and developed by "
            "Samuel Addington for the study of LLM security and classroom "
            "instruction. It must not be used for any purpose other than "
            "research and education on systems you own."
        ),
        "docs": "/docs",
        "labs": [
            "Prompt Engineering Lab  -> /api/attack/run",
            "Education Hub           -> /api/education/vulnerabilities",
            "Agentic Sandbox         -> /api/agentic/run",
            "Resource Stress Lab     -> /api/stress/run",
            "Dashboard Metrics       -> /api/metrics/",
        ],
    }


@app.get("/api/health")
async def health() -> dict:
    models = await ollama.list_models()
    return {
        "status": "ok",
        "ollama_host": settings.ollama_host,
        "ollama_reachable": bool(models),
        "installed_models": models,
    }


# --- Last-resort error handler -----------------------------------------------
@app.exception_handler(Exception)
async def unhandled(_request, exc: Exception) -> JSONResponse:
    # Never leak stack traces to the browser — that itself would be a
    # vulnerability (LLM05 Sensitive Information Disclosure, cousin class).
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": exc.__class__.__name__},
    )
