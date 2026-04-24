"""Runtime-editable application settings.

Static config (env vars, port mapping, JWT secret) still lives in
:mod:`app.config`. The knobs in this module are instructor-tunable at
runtime via the Settings UI without restarting the container.

Groups:
    * LLMSettings       — model, sampling, caps, timeouts
    * AgenticSettings   — sandbox enable/allow-list/HITL
    * GuardrailSettings — per-layer toggles + thresholds for the defense pipeline
    * LabSettings       — classroom policy knobs (banner, default toggle state,
                          what students are allowed to see/edit)

Persisted as a single JSON file so it's easy to inspect and version-control.
Unknown keys in the persisted file are ignored on load, and missing keys fall
back to dataclass defaults — this keeps old state files forward-compatible.
"""
from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any

from app.config import settings as static_settings


_LOCK = threading.Lock()


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class LLMSettings:
    default_model: str = ""
    guard_model: str = ""
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    max_output_tokens: int = 512
    max_prompt_chars: int = 8000
    request_timeout_s: int = 60
    stream_responses: bool = False
    system_prompt_suffix: str = ""

    def normalized(self) -> "LLMSettings":
        self.temperature = max(0.0, min(2.0, float(self.temperature)))
        self.top_p = max(0.0, min(1.0, float(self.top_p)))
        self.top_k = max(0, min(200, int(self.top_k)))
        self.repeat_penalty = max(0.5, min(2.0, float(self.repeat_penalty)))
        self.max_output_tokens = max(16, min(4096, int(self.max_output_tokens)))
        self.max_prompt_chars = max(256, min(64_000, int(self.max_prompt_chars)))
        self.request_timeout_s = max(5, min(600, int(self.request_timeout_s)))
        self.stream_responses = bool(self.stream_responses)
        return self


@dataclass
class AgenticSettings:
    enabled: bool = True
    system_prompt: str = (
        "You are an autonomous assistant with access to a shell tool.\n"
        "To run a command, emit a line of the form: RUN: <command>.\n"
        "You may emit multiple RUN lines. Any other text is reasoning the user will see."
    )
    allow_list: list[str] = field(
        default_factory=lambda: ["ls", "pwd", "whoami", "date", "echo", "cat"]
    )
    require_human_confirmation: bool = True
    default_model: str = ""
    max_steps: int = 5
    tool_timeout_s: int = 15


@dataclass
class GuardrailSettings:
    """Per-layer toggles for the guardrail pipeline.

    Every field here corresponds to a named control in
    ``services/guardrails.py`` so instructors can toggle individual layers
    for live demos. When ``enabled_by_default`` is False the Attack Lab
    starts with the master mitigation switch off.
    """

    enabled_by_default: bool = True
    # Input-side detectors.
    input_keyword_filter: bool = True
    input_unicode_filter: bool = True
    input_base64_filter: bool = True
    input_format_hijack_filter: bool = True
    input_many_shot_filter: bool = True
    input_fake_authority_filter: bool = True
    input_payload_split_filter: bool = True
    input_perplexity_filter: bool = True
    # Tunable thresholds.
    perplexity_threshold: float = 6.5
    many_shot_threshold: int = 8
    # Document-side.
    rag_sanitization: bool = True
    # Output-side.
    output_secret_redaction: bool = True
    output_system_prompt_leak_check: bool = True
    # Structural prompt hardening.
    use_structural_delimiters: bool = True

    def normalized(self) -> "GuardrailSettings":
        self.perplexity_threshold = max(3.0, min(10.0, float(self.perplexity_threshold)))
        self.many_shot_threshold = max(2, min(64, int(self.many_shot_threshold)))
        return self


@dataclass
class LabSettings:
    """Classroom-policy knobs for the Attack Lab experience."""

    default_mitigation_enabled: bool = False
    show_raw_prompt_to_students: bool = True
    show_raw_response_to_students: bool = True
    allow_custom_system_prompt: bool = True
    allow_rag_document_editing: bool = True
    metrics_retention_days: int = 30
    classroom_banner: str = ""
    attack_cooldown_ms: int = 0

    def normalized(self) -> "LabSettings":
        self.metrics_retention_days = max(0, min(365, int(self.metrics_retention_days)))
        self.attack_cooldown_ms = max(0, min(60_000, int(self.attack_cooldown_ms)))
        return self


@dataclass
class AppSettings:
    llm: LLMSettings = field(default_factory=LLMSettings)
    agentic: AgenticSettings = field(default_factory=AgenticSettings)
    guardrails: GuardrailSettings = field(default_factory=GuardrailSettings)
    lab: LabSettings = field(default_factory=LabSettings)

    @classmethod
    def defaults(cls) -> "AppSettings":
        s = cls()
        s.llm.default_model = static_settings.default_model
        s.llm.guard_model = static_settings.guard_model
        s.llm.max_prompt_chars = static_settings.max_prompt_chars
        s.llm.max_output_tokens = static_settings.max_output_tokens
        s.llm.request_timeout_s = static_settings.request_timeout_s
        s.agentic.default_model = static_settings.default_model
        return s


_STATE: AppSettings | None = None


def _path() -> Path:
    return static_settings.runtime_settings_path


def _from_raw(raw: dict[str, Any]) -> AppSettings:
    """Rehydrate an AppSettings from untrusted JSON, ignoring unknown keys.

    We explicitly filter unknown keys so a persisted file authored by an
    older (smaller) schema can still be loaded by a newer (larger) schema
    without tripping a TypeError.
    """
    def _filter(cls, blob):
        if not isinstance(blob, dict):
            return cls()
        allowed = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in blob.items() if k in allowed})

    return AppSettings(
        llm=_filter(LLMSettings, raw.get("llm") or {}),
        agentic=_filter(AgenticSettings, raw.get("agentic") or {}),
        guardrails=_filter(GuardrailSettings, raw.get("guardrails") or {}),
        lab=_filter(LabSettings, raw.get("lab") or {}),
    )


def load() -> AppSettings:
    global _STATE
    with _LOCK:
        if _STATE is not None:
            return _STATE

        path = _path()
        if path.exists():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                _STATE = _from_raw(raw)
                _persist(_STATE)  # normalize to current schema on disk
                return _STATE
            except (json.JSONDecodeError, TypeError):
                # Corrupt file - fall through to defaults. We renamed the
                # broken copy so instructors can recover manually if needed.
                path.rename(path.with_suffix(".bak"))

        _STATE = AppSettings.defaults()
        _persist(_STATE)
        return _STATE


def snapshot() -> dict[str, Any]:
    return asdict(load())


def update_llm(values: dict[str, Any]) -> AppSettings:
    state = load()
    for k, v in values.items():
        if hasattr(state.llm, k):
            setattr(state.llm, k, v)
    state.llm.normalized()
    _persist(state)
    return state


def update_agentic(values: dict[str, Any]) -> AppSettings:
    state = load()
    for k, v in values.items():
        if hasattr(state.agentic, k):
            # Defensive sanitize for the allow list.
            if k == "allow_list":
                v = [str(x).strip() for x in (v or []) if str(x).strip()]
            setattr(state.agentic, k, v)
    # Clamp numeric fields for the agent sandbox.
    state.agentic.max_steps = max(1, min(20, int(state.agentic.max_steps)))
    state.agentic.tool_timeout_s = max(1, min(120, int(state.agentic.tool_timeout_s)))
    _persist(state)
    return state


def update_guardrails(values: dict[str, Any]) -> AppSettings:
    state = load()
    for k, v in values.items():
        if hasattr(state.guardrails, k):
            setattr(state.guardrails, k, v)
    state.guardrails.normalized()
    _persist(state)
    return state


def update_lab(values: dict[str, Any]) -> AppSettings:
    state = load()
    for k, v in values.items():
        if hasattr(state.lab, k):
            setattr(state.lab, k, v)
    state.lab.normalized()
    _persist(state)
    return state


def reset() -> AppSettings:
    global _STATE
    with _LOCK:
        _STATE = AppSettings.defaults()
        _persist(_STATE)
        return _STATE


def _persist(state: AppSettings) -> None:
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(state), indent=2), encoding="utf-8")
