"""Runtime configuration for Aegis-LLM.

All settings can be overridden via environment variables. Defaults are chosen
for a local docker-compose run where the Ollama server is available under the
service name `ollama-server`.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    # --- Ollama -------------------------------------------------------------
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://ollama-server:11434")
    default_model: str = os.getenv("AEGIS_DEFAULT_MODEL", "llama3")
    guard_model: str = os.getenv("AEGIS_GUARD_MODEL", "llama3")

    # --- Safety caps (protect the lab host from runaway generations) --------
    max_prompt_chars: int = int(os.getenv("AEGIS_MAX_PROMPT_CHARS", "8000"))
    max_output_tokens: int = int(os.getenv("AEGIS_MAX_OUTPUT_TOKENS", "512"))
    request_timeout_s: int = int(os.getenv("AEGIS_REQUEST_TIMEOUT_S", "60"))

    # --- Paths --------------------------------------------------------------
    data_dir: Path = Path(__file__).resolve().parent / "data"
    # State dir holds the SQLite DB and the runtime settings JSON. Mounted as
    # a docker volume so users persist across rebuilds.
    state_dir: Path = Path(os.getenv("AEGIS_STATE_DIR", str(Path(__file__).resolve().parent.parent / "state")))
    registry_path: Path = field(init=False)
    rag_dir: Path = field(init=False)
    db_path: Path = field(init=False)
    runtime_settings_path: Path = field(init=False)

    # --- Auth ---------------------------------------------------------------
    jwt_secret: str = os.getenv("AEGIS_JWT_SECRET", "change-me-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = int(os.getenv("AEGIS_JWT_EXPIRES_MINUTES", "720"))

    # Bootstrapped default accounts (created once on first startup if the
    # users table is empty). Rotate via the Users admin panel.
    bootstrap_admin_username: str = os.getenv("AEGIS_ADMIN_USER", "admin")
    bootstrap_admin_password: str = os.getenv("AEGIS_ADMIN_PASS", "admin")
    bootstrap_student_username: str = os.getenv("AEGIS_STUDENT_USER", "student")
    bootstrap_student_password: str = os.getenv("AEGIS_STUDENT_PASS", "student")

    # Allow self-registration? Useful in a classroom; disable to lock down.
    allow_registration: bool = os.getenv("AEGIS_ALLOW_REGISTRATION", "true").lower() == "true"

    def __post_init__(self) -> None:
        object.__setattr__(self, "registry_path", self.data_dir / "vulnerabilities_registry.json")
        object.__setattr__(self, "rag_dir", self.data_dir / "malicious_rag")
        object.__setattr__(self, "db_path", self.state_dir / "aegis.db")
        object.__setattr__(self, "runtime_settings_path", self.state_dir / "runtime_settings.json")
        self.state_dir.mkdir(parents=True, exist_ok=True)

    # --- CORS ---------------------------------------------------------------
    @property
    def allowed_origins(self) -> list[str]:
        raw = os.getenv("AEGIS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173")
        return [o.strip() for o in raw.split(",") if o.strip()]


settings = Settings()
