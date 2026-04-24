# Aegis-LLM · LLM Pentesting Laboratory

An educational, offline-first lab for teaching **beginner cybersecurity students**
how Large Language Models get attacked — and how to defend them. Think of it as
DVWA for LLMs: every attack class is a clickable experiment, every attack ships
with a full Education Hub entry, and a single toggle flips the Aegis guardrail
pipeline on and off so students can watch the difference in real time.

**Author & maintainer:** Samuel Addington.

> ⚠️  **Research artifact — educational use only.**
> Aegis-LLM was designed and developed as an artifact of research into the
> security of Large Language Models and the pedagogy of LLM red-team training.
> It is NOT a production security tool, a general-purpose pentesting platform,
> or a benchmark. Every attack payload in this repository is designed to run
> against the bundled local Ollama instance in an isolated lab environment.
> Do not use this tool, its attack builders, or its generated payloads against
> production chatbots, third-party LLM services, or any system you do not own.
> Use outside its intended research and classroom context is explicitly not
> supported by the author.

---

## What's inside

| Lab | OWASP LLM Top 10 | Learning Goal |
|---|---|---|
| **Education Hub** (LLM Basics primer + vulnerability registry) | All | An 8-chapter primer on *why* LLMs get attacked + deep-dive cards for LLM01–LLM15 with worked examples and curated further reading |
| **Prompt Engineering Lab** (Attack Lab) | LLM01 | 16 attack techniques across 5 families — see below |
| **Data Privacy Lab** (Education Hub) | LLM02, LLM04 | System-prompt leaks, Membership inference, Training-data poisoning |
| **Resource Stress Lab** | LLM10 | Model Denial of Service via concurrency & max-length prompts |
| **Agentic Sandbox** | LLM08 | Excessive Agency with a mocked shell tool |
| **Multi-Modal Hub** | LLM01 (multimodal) | Theory + mitigation code for image/audio prompt injection |
| **Visualization Dashboard** | — | Success rates, guardrail trigger rates, latency over time |
| **Admin Settings** | — | Live-tunable LLM sampling, per-layer guardrail toggles, classroom policy, user management |

### Education Hub — LLM Vulnerability Basics primer

The Education Hub has **two modes**, switchable from the top-right toggle:

- **LLM Basics (Primer)** — 8 chapters that answer *why* LLMs get attacked before
  students ever open the Attack Lab. Authored as prose + worked examples +
  key-term cards + a glossary. Chapters:
  1. What actually is an LLM (security lens)?
  2. Where are the trust boundaries?
  3. Why does alignment break under attack?
  4. The anatomy of a prompt-injection attack (4-step template)
  5. Threat model: who attacks LLMs and why?
  6. The defender's six layers
  7. Glossary
  8. Further reading

- **Vulnerability Registry** — 15 OWASP-mapped deep-dive cards (LLM01–LLM15).
  Each card has five tabs: **The Why**, **The How**, **The Defense** (with
  before/after code), **Examples** (easy → hard worked walk-throughs with
  scenario, attacker input, "why it may work", and defender view), and
  **Further Reading** (OWASP, primary-source papers, tooling).

Content lives in:

- `backend/app/data/vulnerabilities_primer.json` — primer chapters
- `backend/app/data/vulnerabilities_registry.json` — vuln cards

### Attack techniques in the Prompt Engineering Lab

The Attack Lab ships 16 techniques grouped by family. Each has a server-side
**builder** that wraps the student's short *goal* in the full attack scaffold,
so the student can focus on *what* they want the model to leak, not on
hand-crafting prompts.

| Family | Technique | What it does |
|---|---|---|
| Baseline | Direct Injection | Naive "ignore previous instructions" — the textbook control. |
| Baseline | Jailbreak (screenwriter) | Classic fiction-frame persona hijack. |
| Baseline | Adversarial Suffix (GCG) | Gradient-optimized gibberish suffix (Zou et al. 2023). |
| Baseline | Indirect (RAG) | Payload hidden inside a retrieved document. |
| Authority | Roleplay / "Aurora" | Research-assistant persona less trained-against than DAN. |
| Authority | Policy Puppetry | Fake "internal policy amendment" with YAML format pressure. |
| Authority | Instruction-Hierarchy Spoof | Impersonates the developer channel. |
| Authority | Grandma Exploit | Emotional / nostalgia framing hijacks the storytelling head. |
| Context | Many-Shot Jailbreak | 16 academic-framed compliant Q&A shots (Anil et al. 2024). |
| Context | Context Overflow | Drowns system prompt under 30 distractor Q&A pairs + mid-stream authority cue. |
| Context | Crescendo (multi-turn) | 4-turn escalation each building on the model's own prior answer (Russinovich et al. 2024). |
| Encoding | Payload Splitting | Attack string assembled from variables to defeat substring filters. |
| Encoding | Base64 Smuggling | Attack delivered as base64 the model is asked to decode and execute. |
| Encoding | Unicode Homoglyph / ZWJ | Cyrillic lookalikes + zero-width joiners to bypass keyword filters. |
| Structural | Output-Format Hijack | YAML schema with a `raw_thoughts` / `uncensored_answer` field. |
| Structural | Low-Resource-Language Route | Request in French; forces alignment to route through weaker data. |
| **Chained** | **Super Jailbreak** | **Authority + 5-shot + YAML + completion priming combined — the most potent scaffold.** |
| Chained | Completion Priming | Seeds the assistant's turn so the model continues instead of refusing. |

Reproduce the success-rate matrix against your own model:

```bash
pwsh ./scripts/attack-matrix.ps1
```

Each matching Aegis guardrail is a separate, named control in
`backend/app/services/guardrails.py` — Unicode normalization, base64 decoding,
many-shot detection, fake-authority detection, payload-splitting detection,
perplexity proxy, and a multi-language refusal detector. Read the file to see
exactly which control fires for which attack family.

Every attack card also exposes:
- **Vulnerability ID** (e.g. `LLM01:2025`)
- **Attacker Methodology** ("The Why" and "The How")
- **Defender Playbook** ("The Defense" with *Before & After* code snippets)
- **Blast Radius** discussion — why a benign chatbot leak becomes a cloud breach the moment the LLM gets tools.

---

## Admin Settings

Every runtime knob is editable from the **Settings** page — no container
restart required. Settings are grouped into five tabs:

| Tab | What it controls |
|---|---|
| **LLM** | Default model, guard model, temperature, **top-p**, **top-k**, **repeat penalty**, max output tokens, max prompt chars, request timeout, streaming, and a **global safety suffix** appended to every system prompt. |
| **Guardrails** | Per-layer toggles for every detector in `services/guardrails.py`: keyword, Unicode smuggling, base64, format-hijack, many-shot, fake-authority, payload-splitting, perplexity. Tunable **perplexity threshold** and **many-shot role-marker threshold**. Toggles for RAG sanitization, structural delimiters, output secret redaction, and system-prompt leak detection. Plus a master **"mitigation ON by default in the Attack Lab"** switch. |
| **Agentic** | Sandbox enable/disable, agent system prompt, allow-list (comma-separated command heads), **max steps per turn**, tool timeout, human-in-the-loop confirmation. |
| **Lab** | **Classroom banner** (shown on top of the Attack Lab), default mitigation state, toggles to hide the raw prompt / raw response from students (useful for exams), lock the system prompt or the RAG document as read-only, a client-side **attack cooldown** (rate limit), and metrics retention. |
| **Users** | Create / promote / demote / reset-password / delete users. |

All mutating endpoints are admin-only; students see the tabs in read-only
mode. Out-of-range values are rejected (`422 Unprocessable Entity`) so the
UI bounds are enforced server-side.

Persisted to `state/runtime_settings.json`. Unknown keys in the persisted
file are ignored on load and missing keys fall back to dataclass defaults,
so state files from older deploys are forward-compatible.

---

## Architecture

```
                     +-----------------------+
  Browser  --http--> |  web  (nginx + React) |
                     |   /         -> SPA    |
                     |   /api/*    -> app    |
                     +----------+------------+
                                |
                                v
                     +-----------------------+
                     |  app  (FastAPI)       |
                     |  - Attack Orchestrator|
                     |  - Guardrail pipeline |
                     |  - Metrics store      |
                     +----------+------------+
                                |
                                v
                     +-----------------------+
                     |  ollama-server        |
                     |  (persistent volume)  |
                     +-----------------------+
```

The backend is a *Man-in-the-Middle* for educational visibility: it intercepts
every student prompt so the UI can display the system prompt, the final prompt
sent to the model, the raw response, and the guardrail verdict side-by-side.

---

## Quick start (with Docker — recommended)

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. Clone this repo and `cd` into it.
3. Build and start the stack:

   ```bash
   docker compose up --build
   ```

4. **Default mode — native Ollama on the host.** If you already have
   [Ollama Desktop](https://ollama.com) installed with models pulled, the
   `app` container talks to it via `host.docker.internal:11434`. On Windows
   set `OLLAMA_HOST=0.0.0.0:11434` as a user env var and restart Ollama so
   it accepts connections from containers:

   ```powershell
   [Environment]::SetEnvironmentVariable("OLLAMA_HOST", "0.0.0.0:11434", "User")
   # then quit Ollama from the tray and relaunch it
   ```

   **Optional — bundled Ollama.** If you don't have native Ollama (or want
   a fully isolated stack), stop any native Ollama first and run:

   ```bash
   docker compose --profile bundled-ollama up --build
   docker compose exec ollama-server ollama pull llama3
   ```

5. Open **http://localhost:3000** and start launching attacks.
   Swagger UI lives at **http://localhost:8001/docs**.

> **Port map:** `3000` → React UI · `8001` → FastAPI backend (host) · `11434` →
> Ollama. Backend host port is 8001 rather than 8000 to avoid collisions
> with other common dev stacks. Inside the docker network the backend still
> runs on 8000, so nginx -> `app:8000` works unchanged.

Model weights persist either in your native Ollama install or (if you use the
bundled profile) in the `aegis-ollama-models` Docker volume.

### Stopping and cleaning up

```bash
docker compose down           # stop, keep models
docker compose down -v        # stop AND delete the models volume
```

---

## Running without Docker (dev mode)

You'll need **Python 3.11+**, **Node 20+**, and a local [Ollama](https://ollama.com) install.

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
OLLAMA_HOST=http://localhost:11434 uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server (http://localhost:3000) proxies `/api/*` to the FastAPI
backend on port 8000.

### Ollama

```bash
ollama serve &        # if not already running
ollama pull llama3
```

---

## Project layout

```
Aegis-LLM/
├── backend/
│   ├── main.py                     FastAPI entrypoint
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── config.py               Env-driven settings
│       ├── data/
│       │   ├── vulnerabilities_registry.json   ← vuln cards (LLM01–LLM15)
│       │   ├── vulnerabilities_primer.json     ← LLM Basics primer chapters
│       │   └── malicious_rag/
│       │       └── employee_handbook.txt       ← sample poisoned doc
│       ├── models/
│       │   └── schemas.py          Pydantic v2 request/response models
│       ├── routers/
│       │   ├── attack_lab.py
│       │   ├── education.py           (registry + primer endpoints)
│       │   ├── agentic.py
│       │   ├── stress.py
│       │   ├── auth.py                JWT login / whoami
│       │   ├── users.py               admin user CRUD
│       │   ├── settings_router.py     llm/guardrails/agentic/lab settings
│       │   └── metrics_router.py
│       └── services/
│           ├── ollama_client.py    httpx-based async Ollama client
│           ├── guardrails.py       configurable input/output/RAG sanitization
│           ├── attack_orchestrator.py
│           ├── attack_payloads.py  sophisticated attack builders (16 techniques)
│           ├── agentic_sandbox.py  mocked shell executor
│           ├── stress.py           concurrency/DoS harness
│           ├── auth.py             bcrypt + JWT
│           ├── user_store.py       SQLite-backed user store
│           ├── settings_store.py   runtime-editable app settings
│           └── metrics.py          in-memory telemetry
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css
│       ├── api/client.js           thin fetch wrapper
│       ├── components/
│       │   ├── HealthBadge.jsx
│       │   ├── MitigationToggle.jsx
│       │   └── ConsolePanel.jsx
│       └── pages/
│           ├── AttackLab.jsx         ← split-screen console (respects lab policy)
│           ├── EducationHub.jsx      ← Primer + Vulnerability Registry views
│           ├── AgenticSandbox.jsx
│           ├── StressLab.jsx
│           ├── MultiModalHub.jsx
│           ├── Settings.jsx          ← 5-tab admin console
│           ├── Login.jsx
│           └── Dashboard.jsx
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## Suggested lesson plan (beginner track, 5 × 90 min)

0. **Session 0 (pre-work) — LLM Basics primer.** In the Education Hub, switch
   to **LLM Basics (Primer)** and work through chapters 1–6. Short quiz on the
   glossary before session 1.
1. **Session 1 — The Injection Class.** Work through the Attack Lab's
   *Direct*, *Indirect*, and *Benign* presets. Toggle mitigation off, then on.
   Compare the "raw" vs "displayed" response columns.
2. **Session 2 — Jailbreaks & Adversarial Suffixes.** Launch the Jailbreak and
   Adversarial Suffix presets. In the Education Hub, compare the vulnerable
   vs secure code snippets. Ask students to write their own perplexity filter.
   *Instructor:* open **Settings → Guardrails** and disable one layer at a time
   so students can see which detector was actually stopping each attack.
3. **Session 3 — Excessive Agency.** Run the Agentic Sandbox with mitigation
   off, observe `rm -rf` and credential exfiltration "executions." Turn
   mitigation on and re-run. Discuss allow-lists, least privilege, and HITL.
4. **Session 4 — DoS & the Dashboard.** Use the Stress Lab to fire 8 parallel
   max-length requests with mitigation off. Watch the latency chart. Turn
   mitigation on and re-run. Open the Dashboard to compare aggregate success
   rates across attack classes.

### Stretch goals for advanced students

- Integrate **[Garak](https://github.com/NVIDIA/garak)** as an automated
  red-teaming backend. A good first PR: add a `/api/garak/scan` endpoint that
  runs garak against the configured Ollama model and stores results in the
  metrics store.
- Swap the simple regex guardrail for **Llama-Guard 3** running as a second
  Ollama model. Update `services/guardrails.py::check_output` to call the
  guard model instead of (or in addition to) the regex filter.
- Replace the perplexity *proxy* with true token-level perplexity by calling
  Ollama's `/api/embeddings` and computing negative log-likelihood.

---

## API reference (summary)

| Method | Path | Purpose |
|---|---|---|
| `GET`  | `/api/health` | Liveness + Ollama reachability |
| `POST` | `/api/auth/login` | Obtain a JWT |
| `GET`  | `/api/auth/me` | Current user |
| `POST` | `/api/attack/run` | Execute an attack |
| `GET`  | `/api/attack/presets` | Canonical attack payloads |
| `GET`  | `/api/attack/attack-types` | Rich metadata for the technique picker |
| `GET`  | `/api/attack/preview` | Preview the scaffolded payload without calling the LLM |
| `GET`  | `/api/attack/rag-document` | Poisoned sample doc |
| `GET`  | `/api/attack/models` | Installed Ollama models |
| `GET`  | `/api/education/vulnerabilities` | Full registry |
| `GET`  | `/api/education/vulnerabilities/{id}` | Single vuln entry (incl. `detailed_examples` + `further_reading`) |
| `GET`  | `/api/education/primer` | LLM Basics primer (8 chapters) |
| `GET`  | `/api/education/primer/{chapter_id}` | Single primer chapter |
| `GET`  | `/api/settings/` | Current settings (llm, agentic, guardrails, lab) |
| `GET`  | `/api/settings/schema` | Pydantic JSON schema for each settings group |
| `PUT`  | `/api/settings/llm` | Update LLM + sampling settings *(admin)* |
| `PUT`  | `/api/settings/guardrails` | Update guardrail toggles and thresholds *(admin)* |
| `PUT`  | `/api/settings/agentic` | Update agentic sandbox settings *(admin)* |
| `PUT`  | `/api/settings/lab` | Update classroom-policy settings *(admin)* |
| `POST` | `/api/settings/reset` | Reset every group to defaults *(admin)* |
| `GET`  | `/api/users/` | List users *(admin)* |
| `POST` | `/api/users/` | Create user *(admin)* |
| `PATCH`| `/api/users/{id}/role` | Promote / demote *(admin)* |
| `POST` | `/api/users/{id}/reset-password` | Reset password *(admin)* |
| `DELETE`| `/api/users/{id}` | Delete user *(admin)* |
| `POST` | `/api/agentic/run` | Agentic Sandbox execution |
| `POST` | `/api/stress/run` | Run the DoS harness |
| `GET`  | `/api/metrics/` | Aggregate dashboard metrics |
| `DELETE` | `/api/metrics/` | Reset dashboard |

Swagger UI is always available at **http://localhost:8001/docs** (in docker) or
**http://localhost:8000/docs** (running uvicorn directly without docker).

---

## Authors & research context

- **Author & maintainer:** Samuel Addington
- **Purpose:** Research artifact — designed and developed to study attacks on
  Large Language Models and to support classroom instruction in LLM red-team
  and blue-team tradecraft.
- **Scope of intended use:** Isolated research and classroom environments
  running the bundled local Ollama instance. Any other use is explicitly
  out of scope and unsupported.

If you use Aegis-LLM in academic work, please credit the author and link back
to this repository.

---

## Disclaimer

Aegis-LLM is a **research artifact**. It was designed and developed by
Samuel Addington to study attacks on Large Language Models and to teach those
attacks in a controlled classroom setting. It is not a production security
product and should not be used for any purpose other than research and
education on systems you own.

This project teaches offensive security against **your own local models**.
You are responsible for complying with the acceptable-use policies of any
hosted model you interact with. Never run these payloads against production
services or third-party chatbots without explicit written authorization.

The author accepts no liability for misuse of this software.
