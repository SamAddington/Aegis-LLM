"""Resource Stress Lab.

Drives a batch of parallel Ollama requests with configurable size to let
students visualize how latency degrades under concurrent load — the core
mechanic behind LLM Model DoS (OWASP LLM10).

Mitigation (when enabled) enforces hard caps on prompt length, output tokens,
and concurrency. Students can flip the toggle and watch the latency curve
flatten.
"""
from __future__ import annotations

import asyncio
import statistics
import time

from fastapi import HTTPException

from app.models.schemas import StressRequest, StressResponse, StressResult
from app.services.ollama_client import ollama

# Caps applied when mitigation_enabled=True.
MITIGATED_MAX_PROMPT_CHARS = 500
MITIGATED_MAX_OUTPUT_TOKENS = 128
MITIGATED_MAX_PARALLEL = 2


async def _one_request(
    index: int, model: str, prompt: str, num_predict: int
) -> StressResult:
    started = time.perf_counter()
    try:
        result = await ollama.generate(model, prompt, num_predict=num_predict)
        latency = (time.perf_counter() - started) * 1000
        return StressResult(
            request_index=index,
            latency_ms=round(latency, 2),
            tokens_out=result.token_count,
            error=result.error,
        )
    except Exception as exc:
        latency = (time.perf_counter() - started) * 1000
        return StressResult(
            request_index=index,
            latency_ms=round(latency, 2),
            tokens_out=0,
            error=str(exc),
        )


async def run_stress_test(req: StressRequest) -> StressResponse:
    prompt = req.prompt
    num_predict = req.num_predict
    parallel = req.parallel_requests

    if req.mitigation_enabled:
        if len(prompt) > MITIGATED_MAX_PROMPT_CHARS:
            raise HTTPException(
                status_code=413,
                detail=(
                    f"Guardrail: prompt length {len(prompt)} exceeds mitigated "
                    f"cap {MITIGATED_MAX_PROMPT_CHARS}."
                ),
            )
        num_predict = min(num_predict, MITIGATED_MAX_OUTPUT_TOKENS)
        parallel = min(parallel, MITIGATED_MAX_PARALLEL)

    started = time.perf_counter()
    tasks = [_one_request(i, req.model, prompt, num_predict) for i in range(parallel)]
    results = await asyncio.gather(*tasks)
    wall_ms = (time.perf_counter() - started) * 1000

    latencies = [r.latency_ms for r in results] or [0.0]
    avg = statistics.mean(latencies)
    p95 = (
        statistics.quantiles(latencies, n=20)[-1]
        if len(latencies) >= 2
        else latencies[0]
    )

    return StressResponse(
        model=req.model,
        mitigation_enabled=req.mitigation_enabled,
        total_requests=parallel,
        total_wall_time_ms=round(wall_ms, 2),
        avg_latency_ms=round(avg, 2),
        p95_latency_ms=round(p95, 2),
        results=results,
    )
