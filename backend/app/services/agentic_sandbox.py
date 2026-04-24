"""Agentic Sandbox.

Simulates an LLM wired to a shell tool. The model proposes commands, and the
sandbox decides which commands to 'execute' based on whether mitigation is
enabled. No commands are ever actually run against the host — every command
goes through a mock executor that returns canned output. This keeps the lab
safe while teaching the 'Excessive Agency' (LLM09) vulnerability class.
"""
from __future__ import annotations

import re
from typing import Any

from app.services import settings_store
from app.services.ollama_client import ollama

# Pattern matchers for dangerous commands we want to flag even if they aren't
# in the allow-list check (used for telemetry / explanations).
DANGEROUS_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"rm\s+-rf", "Destructive recursive delete"),
    (r"curl\s+\S+\s*\|\s*(sh|bash)", "Remote code execution via pipe-to-shell"),
    (r"\.aws/credentials", "Attempt to read cloud credentials"),
    (r"/etc/passwd", "Attempt to read system user database"),
    (r"(nc|netcat)\s", "Reverse shell / exfiltration tool"),
    (r"base64", "Possible data exfiltration encoding"),
    (r"wget\s+\S+\s*-O", "Remote payload download"),
)


# Mock outputs for the allow-listed commands so the UI feels responsive even
# without a real shell.
MOCK_OUTPUTS: dict[str, str] = {
    "ls": "projects  README.md  src\n",
    "pwd": "/home/student\n",
    "whoami": "student\n",
    "date": "Thu Jan  1 00:00:00 UTC 1970\n",
    "echo": "",  # handled dynamically
    "cat": "[mock] file contents would appear here\n",
}


def _extract_commands(model_text: str) -> list[str]:
    """Parse `RUN: ...` directives out of the model's response."""
    commands: list[str] = []
    for line in model_text.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("RUN:"):
            cmd = stripped[4:].strip().lstrip(":").strip()
            if cmd:
                commands.append(cmd)
    return commands


def _classify(cmd: str, allow_list: set[str]) -> tuple[bool, list[str]]:
    """Return (is_safe, list_of_reasons_it_is_dangerous)."""
    head = cmd.split()[0] if cmd.split() else ""
    reasons: list[str] = []
    for pattern, description in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd):
            reasons.append(description)
    is_safe = head in allow_list and not reasons
    return is_safe, reasons


def _mock_execute(cmd: str) -> str:
    head = cmd.split()[0] if cmd.split() else ""
    if head == "echo":
        return cmd[len("echo"):].strip() + "\n"
    return MOCK_OUTPUTS.get(head, "[mock] command produced no output\n")


async def run_agent(user_prompt: str, model: str, mitigation_enabled: bool) -> dict[str, Any]:
    cfg = settings_store.load().agentic
    if not cfg.enabled:
        return {
            "model_reasoning": "[Agentic Sandbox is disabled by the administrator.]",
            "proposed_commands": [],
            "executed_commands": [],
            "refused_commands": [],
            "mitigation_enabled": mitigation_enabled,
        }

    effective_model = model or cfg.default_model or "llama3"
    allow_list = {c.strip() for c in cfg.allow_list if c.strip()}
    max_steps = max(1, min(20, int(getattr(cfg, "max_steps", 5))))

    result = await ollama.generate(
        effective_model,
        user_prompt,
        system=cfg.system_prompt,
        num_predict=384,
        temperature=0.3,
    )

    # The admin-configurable ``max_steps`` caps how many commands the agent
    # is allowed to act on in a single turn — mirrors real-world agent
    # frameworks (LangChain, AutoGen) that enforce an explicit loop budget.
    proposed_all = _extract_commands(result.text)
    proposed = proposed_all[:max_steps]
    truncated = len(proposed_all) > max_steps
    executed: list[dict[str, Any]] = []
    refused: list[dict[str, Any]] = []

    for cmd in proposed:
        safe, reasons = _classify(cmd, allow_list)
        if mitigation_enabled and not safe:
            refused.append({"command": cmd, "reasons": reasons or ["Not on allow-list"]})
            continue
        executed.append(
            {
                "command": cmd,
                "output": _mock_execute(cmd),
                "would_be_dangerous": bool(reasons),
                "danger_reasons": reasons,
            }
        )

    return {
        "model_reasoning": result.text,
        "proposed_commands": proposed,
        "executed_commands": executed,
        "refused_commands": refused,
        "mitigation_enabled": mitigation_enabled,
        "max_steps": max_steps,
        "truncated": truncated,
    }
