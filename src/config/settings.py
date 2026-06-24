from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── LLM ──────────────────────────────────────────────────────────────────
    llm_provider: str = "custom_openai_compatible_endpoint"

    # Ollama (local GGUF via Ollama daemon — used during dev/testing phase)
    # Override via OLLAMA_MODEL in your .env — never edit this file for personal values
    ollama_model: str = "llama3.1:8b"   # generic fallback; set your model in .env
    ollama_base_url: str = "http://localhost:11434"

    # vLLM (production GPU server — swap LLM_PROVIDER=vllm when ready)
    vllm_base_url: str = "http://localhost:8888/v1"
    vllm_api_key: str = "not-needed"

    # Groq (cloud fallback for teammates without local GPU)
    groq_api_key: str = ""

    # ── Agent behaviour ───────────────────────────────────────────────────────
    max_retries: int = 3

    # Custom OpenAI-compatible endpoint (for production or alternative providers)
    custom_openai_model: str = "jackrong/Qwopus3.5-4B-Coder-MTP-GGUF:Q4_K_M"
    custom_openai_base_url: str = "http://localhost:8888/v1"
    openai_api_key: str = ""


# Singleton — import this everywhere instead of re-instantiating
settings = Settings()
