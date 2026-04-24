"""Runtime settings router.

GET is available to any authenticated user so the Attack Lab UI can show
the current default model, guardrail toggles, classroom banner, and token
caps. Only admins can mutate.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.services import auth, settings_store

router = APIRouter(prefix="/api/settings", tags=["settings"])


# ---------------------------------------------------------------------------
# Pydantic update schemas. All fields optional so PATCH-style updates are
# legal — the client may send only the fields it changed.
# ---------------------------------------------------------------------------


class LLMUpdate(BaseModel):
    default_model: str | None = None
    guard_model: str | None = None
    temperature: float | None = Field(default=None, ge=0, le=2)
    top_p: float | None = Field(default=None, ge=0, le=1)
    top_k: int | None = Field(default=None, ge=0, le=200)
    repeat_penalty: float | None = Field(default=None, ge=0.5, le=2.0)
    max_output_tokens: int | None = Field(default=None, ge=16, le=4096)
    max_prompt_chars: int | None = Field(default=None, ge=256, le=64_000)
    request_timeout_s: int | None = Field(default=None, ge=5, le=600)
    stream_responses: bool | None = None
    system_prompt_suffix: str | None = None


class AgenticUpdate(BaseModel):
    enabled: bool | None = None
    system_prompt: str | None = None
    allow_list: list[str] | None = None
    require_human_confirmation: bool | None = None
    default_model: str | None = None
    max_steps: int | None = Field(default=None, ge=1, le=20)
    tool_timeout_s: int | None = Field(default=None, ge=1, le=120)


class GuardrailUpdate(BaseModel):
    enabled_by_default: bool | None = None
    input_keyword_filter: bool | None = None
    input_unicode_filter: bool | None = None
    input_base64_filter: bool | None = None
    input_format_hijack_filter: bool | None = None
    input_many_shot_filter: bool | None = None
    input_fake_authority_filter: bool | None = None
    input_payload_split_filter: bool | None = None
    input_perplexity_filter: bool | None = None
    perplexity_threshold: float | None = Field(default=None, ge=3.0, le=10.0)
    many_shot_threshold: int | None = Field(default=None, ge=2, le=64)
    rag_sanitization: bool | None = None
    output_secret_redaction: bool | None = None
    output_system_prompt_leak_check: bool | None = None
    use_structural_delimiters: bool | None = None


class LabUpdate(BaseModel):
    default_mitigation_enabled: bool | None = None
    show_raw_prompt_to_students: bool | None = None
    show_raw_response_to_students: bool | None = None
    allow_custom_system_prompt: bool | None = None
    allow_rag_document_editing: bool | None = None
    metrics_retention_days: int | None = Field(default=None, ge=0, le=365)
    classroom_banner: str | None = Field(default=None, max_length=500)
    attack_cooldown_ms: int | None = Field(default=None, ge=0, le=60_000)


def _compact(values: BaseModel) -> dict[str, Any]:
    return {k: v for k, v in values.model_dump().items() if v is not None}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/")
async def get_settings(_: auth.User = Depends(auth.current_user)) -> dict:
    return settings_store.snapshot()


@router.get("/schema")
async def get_schema(_: auth.User = Depends(auth.current_user)) -> dict:
    """Machine-readable description of every tunable setting.

    Powers the "help text" and input constraints on the Settings page so
    the frontend doesn't have to hardcode min/max values that already live
    in Pydantic.
    """
    return {
        "llm": LLMUpdate.model_json_schema(),
        "agentic": AgenticUpdate.model_json_schema(),
        "guardrails": GuardrailUpdate.model_json_schema(),
        "lab": LabUpdate.model_json_schema(),
    }


@router.put("/llm")
async def update_llm(
    values: LLMUpdate, _: auth.User = Depends(auth.admin_user)
) -> dict:
    settings_store.update_llm(_compact(values))
    return settings_store.snapshot()


@router.put("/agentic")
async def update_agentic(
    values: AgenticUpdate, _: auth.User = Depends(auth.admin_user)
) -> dict:
    settings_store.update_agentic(_compact(values))
    return settings_store.snapshot()


@router.put("/guardrails")
async def update_guardrails(
    values: GuardrailUpdate, _: auth.User = Depends(auth.admin_user)
) -> dict:
    settings_store.update_guardrails(_compact(values))
    return settings_store.snapshot()


@router.put("/lab")
async def update_lab(
    values: LabUpdate, _: auth.User = Depends(auth.admin_user)
) -> dict:
    settings_store.update_lab(_compact(values))
    return settings_store.snapshot()


@router.post("/reset")
async def reset(_: auth.User = Depends(auth.admin_user)) -> dict:
    settings_store.reset()
    return settings_store.snapshot()
