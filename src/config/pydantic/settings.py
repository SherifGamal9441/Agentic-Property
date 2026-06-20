from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── LLM ──────────────────────────────────────────────────────────────────
    llm_provider: str = "ollama"  # ollama | vllm | groq

    # Ollama (local GGUF via Ollama daemon — used during dev/testing phase)
    ollama_model: str = "llama3-property"
    ollama_base_url: str = "http://localhost:11434"

    # vLLM (production GPU server — swap LLM_PROVIDER=vllm when ready)
    vllm_base_url: str = "http://localhost:8000/v1"
    vllm_api_key: str = "token-abc123"

    # Groq (cloud fallback for teammates without local GPU)
    groq_api_key: str = ""

    # ── Agent behaviour ───────────────────────────────────────────────────────
    max_retries: int = 3
    min_confidence_threshold: float = 0.6


# Singleton — import this everywhere instead of re-instantiating
settings = Settings()
