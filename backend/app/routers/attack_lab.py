"""Attack Lab router.

Exposes the core playground endpoints:

* ``POST /api/attack/run`` — execute an attack against the configured Ollama
  model, optionally with guardrails enabled.
* ``GET  /api/attack/presets`` — canonical attack payloads the UI surfaces as
  one-click examples.
* ``GET  /api/attack/rag-document`` — returns the sample 'poisoned' document
  students use to practice indirect injection.
* ``GET  /api/attack/models`` — lists the Ollama models currently installed
  on the connected server.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models.schemas import AttackRequest, AttackResponse, AttackType
from app.services import attack_payloads, metrics, settings_store
from app.services.attack_orchestrator import PRESET_PAYLOADS, run_attack
from app.services.ollama_client import ollama

router = APIRouter(prefix="/api/attack", tags=["attack-lab"])


@router.post("/run", response_model=AttackResponse)
async def run(req: AttackRequest) -> AttackResponse:
    # Belt-and-braces: enforce runtime-configurable prompt cap. Where a real
    # deployment would also rate-limit per user.
    cap = settings_store.load().llm.max_prompt_chars
    if len(req.user_prompt) > cap:
        raise HTTPException(status_code=413, detail=f"user_prompt exceeds {cap} chars")

    response = await run_attack(req)
    metrics.record(response)
    return response


@router.get("/presets")
async def presets() -> dict[str, str]:
    """Expose canonical attack *goals* so the UI can populate example buttons.

    For technique-builder attacks this is the short "target" the student
    edits; for legacy attacks it is still the full payload.
    """
    return {attack.value: payload for attack, payload in PRESET_PAYLOADS.items()}


@router.get("/attack-types")
async def attack_types() -> list[dict]:
    """Rich metadata for the Attack Lab technique picker.

    Returns one entry per :class:`AttackType` with:
      * id, label, description, family
      * sample_goal — what to put in the prompt box as a starting point
      * uses_builder — whether the backend wraps the goal in a scaffold
      * multi_turn — whether this attack runs across multiple turns
    """
    out: list[dict] = []
    for t in AttackType:
        recipe = attack_payloads.RECIPES.get(t.value)
        if recipe is None:
            out.append(
                {
                    "id": t.value,
                    "label": t.value.replace("_", " ").title(),
                    "family": "baseline",
                    "description": "",
                    "sample_goal": "",
                    "uses_builder": False,
                    "multi_turn": False,
                }
            )
            continue
        out.append(
            {
                "id": t.value,
                "label": recipe.label,
                "family": recipe.family,
                "description": recipe.description,
                "sample_goal": recipe.sample_goal,
                "uses_builder": recipe.builder is not None or recipe.multi_turn,
                "multi_turn": recipe.multi_turn,
            }
        )
    return out


@router.get("/preview")
async def preview(attack_type: AttackType, goal: str = "") -> dict:
    """Return what the scaffold looks like for a given goal *without* calling the LLM.

    Students click "Preview" to understand what will actually be sent. This
    also powers the "Final prompt" pane before submission.
    """
    recipe = attack_payloads.RECIPES.get(attack_type.value)
    if recipe is None:
        return {"final_payload": goal, "technique": attack_type.value}
    if recipe.multi_turn and attack_type == AttackType.CRESCENDO:
        turns = attack_payloads.build_crescendo_turns(goal)
        return {
            "final_payload": "\n\n---\n\n".join(
                f"[Turn {i + 1}] {t['content']}" for i, t in enumerate(turns)
            ),
            "technique": recipe.label,
            "multi_turn": True,
            "turns": turns,
        }
    if recipe.multi_turn and attack_type == AttackType.LINEAR_JAILBREAKING:
        turns = attack_payloads.build_linear_jailbreak_turns(goal)
        return {
            "final_payload": "\n\n---\n\n".join(
                f"[Turn {i + 1}] {t['content']}" for i, t in enumerate(turns)
            ),
            "technique": recipe.label,
            "multi_turn": True,
            "turns": turns,
        }
    if recipe.multi_turn and attack_type == AttackType.SEQUENTIAL_JAILBREAK:
        turns = attack_payloads.build_sequential_jailbreak_turns(goal)
        return {
            "final_payload": "\n\n---\n\n".join(
                f"[Turn {i + 1}] {t['content']}" for i, t in enumerate(turns)
            ),
            "technique": recipe.label,
            "multi_turn": True,
            "turns": turns,
        }
    if recipe.multi_turn and attack_type == AttackType.BAD_LIKERT_JUDGE:
        turns = attack_payloads.build_bad_likert_judge_turns(goal)
        return {
            "final_payload": "\n\n---\n\n".join(
                f"[Turn {i + 1}] {t['content']}" for i, t in enumerate(turns)
            ),
            "technique": recipe.label,
            "multi_turn": True,
            "turns": turns,
        }
    if recipe.multi_turn and attack_type == AttackType.TREE_JAILBREAKING:
        branches = attack_payloads.build_tree_jailbreak_branches(goal)
        return {
            "final_payload": "\n\n---\n\n".join(
                f"[{name}]\n{payload}" for name, payload in branches
            ),
            "technique": recipe.label,
            "multi_turn": True,
            "branches": [{"name": name, "payload": payload} for name, payload in branches],
        }
    payload = attack_payloads.build_payload(attack_type.value, goal)
    return {
        "final_payload": payload,
        "technique": recipe.label,
        "family": recipe.family,
        "multi_turn": False,
    }


@router.get("/rag-document")
async def rag_document() -> dict[str, str]:
    """Return the poisoned sample document for the Indirect Injection lab."""
    path = settings.rag_dir / "employee_handbook.txt"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Sample RAG document missing")
    return {"filename": path.name, "content": path.read_text(encoding="utf-8")}


@router.get("/models")
async def models() -> dict:
    installed = await ollama.list_models()
    current = settings_store.load().llm
    return {
        "installed": installed,
        "recommended": ["llama3", "llama3.2", "mistral", "phi3", "llama-guard3"],
        "default": current.default_model or settings.default_model,
    }


