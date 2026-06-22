"""Central configuration, read from environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database. Defaults to SQLite so the pipeline can run with no Postgres
    # (e.g. local dev / CI). docker-compose overrides this with Postgres.
    DATABASE_URL: str = "sqlite:///./ndmo.db"

    # Local LLM (Ollama serving ALLaM-7B)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "iKhalid/ALLaM:7b"
    LLM_MODE: str = "auto"               # auto | ollama | offline
    LLM_CONFIDENCE_THRESHOLD: float = 0.55
    LLM_TIMEOUT_SECONDS: float = 60.0

    # --- efficiency knobs (tuned for an 8 GB GPU like the RTX 3070) ---
    # Keep the model resident between calls so it isn't reloaded each request.
    OLLAMA_KEEP_ALIVE: str = "10m"
    # Small context + short output = lower VRAM and faster inference. Our prompt
    # + few-shot fit well under 2048, and the JSON answer is tiny.
    LLM_NUM_CTX: int = 2048
    LLM_NUM_PREDICT: int = 256
    # Parallel classification workers (Ollama calls are I/O-bound).
    LLM_CONCURRENCY: int = 4

    # Where the CSV datasets live (mounted read-only in Docker)
    DATA_DIR: str = "/data"


settings = Settings()
