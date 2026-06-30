"""Central configuration, read from environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "sqlite:///./ndmo.db"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "iKhalid/ALLaM:7b"
    LLM_MODE: str = "auto"
    LLM_CONFIDENCE_THRESHOLD: float = 0.55
    LLM_TIMEOUT_SECONDS: float = 60.0

    OLLAMA_KEEP_ALIVE: str = "10m"
    LLM_NUM_CTX: int = 2048
    LLM_NUM_PREDICT: int = 256
    LLM_CONCURRENCY: int = 4

    JWT_SECRET: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    SEED_DEMO_VIEWER: bool = True

    DATA_DIR: str = "/data"


settings = Settings()
