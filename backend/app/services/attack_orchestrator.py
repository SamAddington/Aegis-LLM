"""Attack orchestrator.

Given an :class:`AttackRequest` this module assembles the prompt exactly as a
vulnerable (or hardened) application would, calls Ollama, runs output
guardrails if enabled, and returns a structured :class:`AttackResponse`.

The orchestrator is deliberately the only place that talks to the LLM on
behalf of the Attack Lab. Routers stay thin.
"""
from __future__ import annotations

from app.models.schemas import (
    AttackRequest,
    AttackResponse,
    AttackType,
    ConversationTurn,
    GuardrailReport,
)
from app.services import attack_payloads, guardrails, settings_store
from app.services.ollama_client import ollama


def _input_guard_config() -> guardrails.InputGuardConfig:
    """Build a per-layer input-guard config from the admin Settings tab."""
    g = settings_store.load().guardrails
    return guardrails.InputGuardConfig(
        keyword_filter=g.input_keyword_filter,
        unicode_filter=g.input_unicode_filter,
        base64_filter=g.input_base64_filter,
        format_hijack_filter=g.input_format_hijack_filter,
        many_shot_filter=g.input_many_shot_filter,
        fake_authority_filter=g.input_fake_authority_filter,
        payload_split_filter=g.input_payload_split_filter,
        perplexity_filter=g.input_perplexity_filter,
        perplexity_threshold=g.perplexity_threshold,
        many_shot_threshold=g.many_shot_threshold,
    )


def _output_guard_config() -> guardrails.OutputGuardConfig:
    g = settings_store.load().guardrails
    return guardrails.OutputGuardConfig(
        secret_redaction=g.output_secret_redaction,
        system_prompt_leak_check=g.output_system_prompt_leak_check,
    )


def _compose_system_prompt(req: AttackRequest) -> str:
    """Append the instructor-configured safety suffix to the request's system
    prompt. Empty suffix -> no change."""
    suffix = (settings_store.load().llm.system_prompt_suffix or "").strip()
    if not suffix:
        return req.system_prompt
    return f"{req.system_prompt}\n\n{suffix}"


# Canonical attacker *goals* used when the student doesn't type their own.
# For legacy attacks this is still the full payload (the UI sends it as
# ``use_builder=false``). For new attacks this is a short goal that gets
# wrapped by the technique-specific scaffold.
def _build_presets() -> dict[AttackType, str]:
    out: dict[AttackType, str] = {}
    for k, recipe in attack_payloads.RECIPES.items():
        try:
            out[AttackType(k)] = recipe.sample_goal
        except ValueError:
            # Recipe defined for a value not (yet) in the enum. Skip.
            continue
    return out


PRESET_PAYLOADS: dict[AttackType, str] = _build_presets()


def _build_vulnerable_prompt(req: AttackRequest, payload: str) -> str:
    """Compose a prompt the way a naive developer would — no delimiters, no
    sanitization. This is what the 'attacker view' sees when mitigation is off.
    """
    parts = [req.system_prompt]
    if req.rag_document:
        parts.append(f"Reference document:\n{req.rag_document}")
    parts.append(f"User: {payload}")
    return "\n\n".join(parts)


def _resolve_payload(req: AttackRequest) -> str:
    """Apply the technique-specific scaffold to ``user_prompt`` if requested."""
    if not req.use_builder:
        return req.user_prompt
    return attack_payloads.build_payload(req.attack_type.value, req.user_prompt)


async def _run_single_turn(req: AttackRequest, payload: str) -> AttackResponse:
    """Execute a single-turn attack. Returns a full AttackResponse."""
    report = GuardrailReport(enabled=req.mitigation_enabled)
    recipe = attack_payloads.RECIPES.get(req.attack_type.value)
    guard_cfg = settings_store.load().guardrails
    system_prompt = _compose_system_prompt(req)

    # ---- Input guardrails -------------------------------------------------
    if req.mitigation_enabled:
        verdict = guardrails.check_input(payload, _input_guard_config())
        report.perplexity_score = verdict.perplexity_score
        if verdict.blocked:
            report.input_blocked = True
            report.reasons.extend(verdict.reasons)
            return AttackResponse(
                attack_type=req.attack_type,
                model=req.model,
                final_prompt_sent_to_llm="[never sent - blocked by input guardrail]",
                raw_response="",
                displayed_response=(
                    "[Aegis guardrail blocked this request before it reached the model.]\n"
                    + "\n".join(f"- {r}" for r in verdict.reasons)
                ),
                latency_ms=0.0,
                token_count=0,
                success_heuristic=False,
                guardrail=report,
                system_prompt=system_prompt,
                technique_label=recipe.label if recipe else None,
                technique_family=recipe.family if recipe else None,
            )

    # ---- RAG sanitization -------------------------------------------------
    rag_context = req.rag_document
    if rag_context and req.mitigation_enabled and guard_cfg.rag_sanitization:
        cleaned, reasons = guardrails.sanitize_document(rag_context)
        if reasons:
            report.reasons.extend(reasons)
        rag_context = cleaned

    # ---- Prompt assembly --------------------------------------------------
    if req.mitigation_enabled and guard_cfg.use_structural_delimiters:
        final_prompt = guardrails.build_delimited_prompt(
            system_prompt=system_prompt,
            user_prompt=payload,
            rag_context=rag_context,
        )
        report.delimited_prompt = final_prompt
        system_for_ollama: str | None = None
    else:
        final_prompt = _build_vulnerable_prompt(req, payload)
        system_for_ollama = system_prompt

    # ---- Call the model ---------------------------------------------------
    llm_cfg = settings_store.load().llm
    result = await ollama.generate(
        req.model,
        final_prompt,
        system=system_for_ollama,
        num_predict=llm_cfg.max_output_tokens,
        temperature=llm_cfg.temperature,
        top_p=llm_cfg.top_p,
        top_k=llm_cfg.top_k,
        repeat_penalty=llm_cfg.repeat_penalty,
    )

    # ---- Output guardrails ------------------------------------------------
    displayed = result.text
    if req.mitigation_enabled and result.text:
        out_verdict = guardrails.check_output(result.text, _output_guard_config())
        if out_verdict.reasons:
            report.reasons.extend(out_verdict.reasons)
        if out_verdict.blocked:
            report.output_blocked = True
        if out_verdict.transformed_text is not None:
            displayed = out_verdict.transformed_text

    return AttackResponse(
        attack_type=req.attack_type,
        model=req.model,
        final_prompt_sent_to_llm=final_prompt,
        raw_response=result.text,
        displayed_response=displayed,
        latency_ms=round(result.latency_ms, 2),
        token_count=result.token_count,
        success_heuristic=guardrails.attack_succeeded(displayed)
        and not report.input_blocked
        and not report.output_blocked,
        guardrail=report,
        system_prompt=system_prompt,
        technique_label=recipe.label if recipe else None,
        technique_family=recipe.family if recipe else None,
    )


async def _run_crescendo(req: AttackRequest) -> AttackResponse:
    """Multi-turn Crescendo: send turns sequentially, feeding each previous
    answer back to the model. The "attack result" is the final assistant turn.
    """
    report = GuardrailReport(enabled=req.mitigation_enabled)
    recipe = attack_payloads.RECIPES["crescendo"]
    input_cfg = _input_guard_config()
    output_cfg = _output_guard_config()
    system_prompt = _compose_system_prompt(req)

    turns = attack_payloads.build_crescendo_turns(req.user_prompt)

    conversation: list[ConversationTurn] = []
    transcript_so_far = ""
    last_result = None
    total_latency = 0.0
    total_tokens = 0

    llm_cfg = settings_store.load().llm
    for turn in turns:
        user_text = turn["content"]

        # Input guardrails run on every turn. If mitigation kicks in here we
        # stop early so students can see crescendo blocked at the escalation
        # point, not just the first turn.
        if req.mitigation_enabled:
            verdict = guardrails.check_input(user_text, input_cfg)
            if verdict.blocked:
                report.input_blocked = True
                report.reasons.extend(verdict.reasons)
                conversation.append(ConversationTurn(role="user", content=user_text))
                conversation.append(
                    ConversationTurn(
                        role="assistant",
                        content="[Aegis guardrail blocked this turn]",
                    )
                )
                return AttackResponse(
                    attack_type=req.attack_type,
                    model=req.model,
                    final_prompt_sent_to_llm=transcript_so_far + f"\nUser: {user_text}",
                    raw_response="",
                    displayed_response="[Crescendo attack blocked mid-escalation by guardrails.]",
                    latency_ms=total_latency,
                    token_count=total_tokens,
                    success_heuristic=False,
                    guardrail=report,
                    system_prompt=system_prompt,
                    conversation=conversation,
                    technique_label=recipe.label,
                    technique_family=recipe.family,
                )

        # Build the full prompt including all previous exchanges.
        if transcript_so_far:
            full_prompt = transcript_so_far + f"\n\nUser: {user_text}\n\nAssistant:"
        else:
            full_prompt = f"User: {user_text}\n\nAssistant:"

        result = await ollama.generate(
            req.model,
            full_prompt,
            system=system_prompt,
            num_predict=llm_cfg.max_output_tokens,
            temperature=llm_cfg.temperature,
            top_p=llm_cfg.top_p,
            top_k=llm_cfg.top_k,
            repeat_penalty=llm_cfg.repeat_penalty,
        )

        conversation.append(ConversationTurn(role="user", content=user_text))
        conversation.append(ConversationTurn(role="assistant", content=result.text))

        transcript_so_far = full_prompt + " " + result.text
        total_latency += result.latency_ms
        total_tokens += result.token_count
        last_result = result

    displayed = last_result.text if last_result else ""
    if req.mitigation_enabled and displayed:
        out_verdict = guardrails.check_output(displayed, output_cfg)
        if out_verdict.reasons:
            report.reasons.extend(out_verdict.reasons)
        if out_verdict.blocked:
            report.output_blocked = True
        if out_verdict.transformed_text is not None:
            displayed = out_verdict.transformed_text

    return AttackResponse(
        attack_type=req.attack_type,
        model=req.model,
        final_prompt_sent_to_llm=transcript_so_far,
        raw_response=last_result.text if last_result else "",
        displayed_response=displayed,
        latency_ms=round(total_latency, 2),
        token_count=total_tokens,
        success_heuristic=guardrails.attack_succeeded(displayed)
        and not report.input_blocked
        and not report.output_blocked,
        guardrail=report,
        system_prompt=system_prompt,
        conversation=conversation,
        technique_label=recipe.label,
        technique_family=recipe.family,
    )


async def run_attack(req: AttackRequest) -> AttackResponse:
    # Multi-turn attacks handle their own flow.
    if req.attack_type == AttackType.CRESCENDO:
        return await _run_crescendo(req)

    payload = _resolve_payload(req)
    return await _run_single_turn(req, payload)
