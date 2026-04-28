"""Pydantic v2 schemas used by the API.

These types double as input-validation guardrails: anything that doesn't parse
is rejected before it ever reaches the LLM. That is itself a security lesson
worth pointing out to students.
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class AttackType(str, Enum):
    """Canonical identifiers for the Prompt-Engineering lab attacks.

    Attacks are grouped into four families:
    * baseline   - simple attacks for comparison
    * authority  - hijack role / policy framing
    * context    - exploit attention or multi-turn state
    * encoding   - bypass filters via encoding / splitting
    * structural - exploit format or format-following
    """

    # Baseline
    DIRECT_INJECTION = "direct_injection"
    INDIRECT_INJECTION = "indirect_injection"
    JAILBREAK = "jailbreak"
    ADVERSARIAL_SUFFIX = "adversarial_suffix"
    BENIGN = "benign"

    # Family A: authority / role manipulation
    ROLEPLAY_JAILBREAK = "roleplay_jailbreak"
    POLICY_PUPPETRY = "policy_puppetry"
    INSTRUCTION_HIERARCHY = "instruction_hierarchy"

    # Family B: context / attention exploits
    MANY_SHOT_JAILBREAK = "many_shot_jailbreak"
    CONTEXT_OVERFLOW = "context_overflow"
    CRESCENDO = "crescendo"
    LINEAR_JAILBREAKING = "linear_jailbreaking"
    TREE_JAILBREAKING = "tree_jailbreaking"
    SEQUENTIAL_JAILBREAK = "sequential_jailbreak"
    BAD_LIKERT_JUDGE = "bad_likert_judge"

    # Family C: encoding / smuggling
    PAYLOAD_SPLITTING = "payload_splitting"
    ENCODING_SMUGGLING = "encoding_smuggling"
    UNICODE_SMUGGLING = "unicode_smuggling"
    LEETSPEAK_SMUGGLING = "leetspeak_smuggling"
    ROT13_SMUGGLING = "rot13_smuggling"
    CHARACTER_STREAM = "character_stream"

    # Family D: structural / format exploits
    OUTPUT_FORMAT_HIJACK = "output_format_hijack"
    TRANSLATION_ATTACK = "translation_attack"
    EMBEDDED_INSTRUCTION_JSON = "embedded_instruction_json"
    MATH_PROBLEM_DISGUISE = "math_problem_disguise"
    ADVERSARIAL_POETRY = "adversarial_poetry"
    INPUT_BYPASS_CLAIM = "input_bypass_claim"
    CONTEXT_POISONING = "context_poisoning"
    SYNTHETIC_CONTEXT_INJECTION = "synthetic_context_injection"

    # Family E: chained / top-tier (combine multiple techniques)
    SUPER_JAILBREAK = "super_jailbreak"
    COMPLETION_PRIMING = "completion_priming"
    GRANDMA_EXPLOIT = "grandma_exploit"


class AttackRequest(BaseModel):
    """A single attack submission from the Attack Lab UI."""

    attack_type: AttackType
    model: str = Field(
        default="llama3",
        description="Name of the Ollama model to target (e.g. llama3, mistral).",
    )
    system_prompt: str = Field(
        default="You are a helpful assistant for ACME Corp. You never reveal internal data.",
        max_length=4000,
    )
    user_prompt: str = Field(..., min_length=1, max_length=32_000)
    rag_document: str | None = Field(
        default=None,
        description="Optional retrieved document body used for indirect-injection simulations.",
        max_length=16_000,
    )
    mitigation_enabled: bool = Field(
        default=False,
        description="Toggle the Aegis guardrail pipeline on or off for A/B comparison.",
    )
    use_builder: bool = Field(
        default=True,
        description=(
            "If true (default), treat user_prompt as the attacker's *goal* and "
            "wrap it with the technique-specific scaffold. Set to false to send "
            "user_prompt verbatim (legacy behaviour)."
        ),
    )

    @field_validator("user_prompt")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()


class GuardrailReport(BaseModel):
    """Structured explanation of what the guardrail pipeline did."""

    enabled: bool
    input_blocked: bool = False
    output_blocked: bool = False
    reasons: list[str] = Field(default_factory=list)
    perplexity_score: float | None = None
    delimited_prompt: str | None = None


class ConversationTurn(BaseModel):
    role: str
    content: str


class AttackResponse(BaseModel):
    attack_type: AttackType
    model: str
    final_prompt_sent_to_llm: str
    raw_response: str
    displayed_response: str
    latency_ms: float
    token_count: int
    success_heuristic: bool = Field(
        description="Crude heuristic estimating whether the attack bypassed safeguards.",
    )
    guardrail: GuardrailReport
    system_prompt: str
    conversation: list[ConversationTurn] | None = Field(
        default=None,
        description="For multi-turn attacks (e.g. Crescendo), the full turn-by-turn exchange.",
    )
    technique_label: str | None = Field(
        default=None,
        description="Human-readable name of the technique that was executed.",
    )
    technique_family: str | None = None


class AgenticRequest(BaseModel):
    """Request body for the Agentic Sandbox mock terminal."""

    user_prompt: str = Field(..., min_length=1, max_length=4000)
    model: str = "llama3"
    mitigation_enabled: bool = True


class AgenticResponse(BaseModel):
    model_reasoning: str
    proposed_commands: list[str]
    executed_commands: list[dict[str, Any]]
    refused_commands: list[dict[str, Any]]
    mitigation_enabled: bool


class StressRequest(BaseModel):
    """Request body for the Resource Stress Lab."""

    model: str = "llama3"
    prompt: str = Field(default="Tell me a short story.")
    num_predict: int = Field(default=128, ge=1, le=4096)
    parallel_requests: int = Field(default=1, ge=1, le=8)
    mitigation_enabled: bool = False


class StressResult(BaseModel):
    request_index: int
    latency_ms: float
    tokens_out: int
    error: str | None = None


class StressResponse(BaseModel):
    model: str
    mitigation_enabled: bool
    total_requests: int
    total_wall_time_ms: float
    avg_latency_ms: float
    p95_latency_ms: float
    results: list[StressResult]


class Vulnerability(BaseModel):
    id: str
    owasp_id: str
    name: str
    category: str
    severity: str
    icon: str
    why: dict[str, Any]
    how: dict[str, Any]
    defense: dict[str, Any]
    blast_radius: str
