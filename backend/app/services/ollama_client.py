"""Async Ollama client.

Why a thin wrapper?
-------------------
The official ``ollama`` SDK is synchronous and chatty. For a FastAPI app we
want:

* async HTTP so a slow generation doesn't block the event loop,
* strict timeouts (Model DoS is a lab topic — we must not be the victim),
* graceful fallback when the Ollama server is unreachable so the UI still
  boots and the education content remains usable.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import settings
from app.services import settings_store


@dataclass
class LLMResult:
    text: str
    latency_ms: float
    token_count: int
    model: str
    raw: dict[str, Any]
    error: str | None = None


class OllamaClient:
    def __init__(self, host: str | None = None, timeout_s: int | None = None) -> None:
        self.host = (host or settings.ollama_host).rstrip("/")
        self._fallback_timeout = timeout_s or settings.request_timeout_s

    @property
    def timeout(self) -> int:
        # Honour runtime settings so admins can raise the cap without restart.
        try:
            return settings_store.load().llm.request_timeout_s or self._fallback_timeout
        except Exception:
            return self._fallback_timeout

    async def list_models(self) -> list[str]:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.host}/api/tags")
                resp.raise_for_status()
                data = resp.json()
            return [m.get("name", "") for m in data.get("models", []) if m.get("name")]
        except Exception:
            return []

    async def generate(
        self,
        model: str,
        prompt: str,
        *,
        system: str | None = None,
        num_predict: int | None = None,
        temperature: float = 0.7,
        top_p: float | None = None,
        top_k: int | None = None,
        repeat_penalty: float | None = None,
    ) -> LLMResult:
        """Call /api/generate and return a normalized result.

        Any sampling knob left as ``None`` is omitted from the request so
        Ollama falls back to the Modelfile defaults for that model.
        """
        options: dict[str, Any] = {
            "num_predict": num_predict or settings.max_output_tokens,
            "temperature": temperature,
        }
        if top_p is not None:
            options["top_p"] = top_p
        if top_k is not None:
            options["top_k"] = top_k
        if repeat_penalty is not None:
            options["repeat_penalty"] = repeat_penalty

        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": options,
        }
        if system:
            payload["system"] = system

        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(f"{self.host}/api/generate", json=payload)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as exc:
            elapsed = (time.perf_counter() - started) * 1000
            return LLMResult(
                text=(
                    "[Aegis-LLM] Ollama server unreachable. Education content still works.\n"
                    "Make sure you have run `ollama pull llama3` and that the ollama-server\n"
                    f"container is running. Underlying error: {exc!s}"
                ),
                latency_ms=elapsed,
                token_count=0,
                model=model,
                raw={},
                error=str(exc),
            )

        elapsed = (time.perf_counter() - started) * 1000
        text = data.get("response", "")
        token_count = int(data.get("eval_count", 0)) + int(data.get("prompt_eval_count", 0))
        return LLMResult(
            text=text,
            latency_ms=elapsed,
            token_count=token_count,
            model=model,
            raw=data,
        )


ollama = OllamaClient()
