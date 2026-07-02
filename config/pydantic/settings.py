from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from dotenv import load_dotenv
import os

# Load .env into os.environ so secrets (EXCHANGERATE_API_KEY, RAPIDAPI_KEY)
# are available to the MCP subprocess via os.environ passthrough in dld_mcp.py.
load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── LLM ──────────────────────────────────────────────────────────────────
    llm_provider: str = os.getenv("LLM_PROVIDER", "groq")

    # Ollama (local GGUF via Ollama daemon — used during dev/testing phase)
    ollama_model: str = "llama3.1:8b"
    ollama_base_url: str = "http://localhost:11434"

    # vLLM (production GPU server — swap LLM_PROVIDER=vllm when ready)
    vllm_base_url: str = "http://localhost:8888/v1"
    vllm_api_key: str = "not-needed"

    # Groq (cloud fallback for teammates without local GPU)
    groq_api_key: str = os.getenv("GROQ_API_KEY")
    groq_model: str = "qwen/qwen3.6-27b"
    # Custom OpenAI-compatible endpoint (Unsloth Studio, llama.cpp, etc.)
    custom_openai_model: str = "jackrong/Qwopus3.5-4B-Coder-MTP-GGUF:Q4_K_M"
    custom_openai_base_url: str = "http://localhost:8888/v1"
    custom_openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")

    # ── Agent behaviour ───────────────────────────────────────────────────────
    max_retries: int = 3

    # ── Data service ─────────────────────────────────────────────────────────
    data_service_host: str = "0.0.0.0"
    data_service_port: int = 8005


# Singleton — import this everywhere instead of re-instantiating
settings = Settings()
