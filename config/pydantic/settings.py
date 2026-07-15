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
    llm_provider: str = os.getenv("LLM_PROVIDER", "ollama")

    # Ollama (local GGUF via Ollama daemon — used during dev/testing phase)
    ollama_model: str = "llama3.1:8b"
    ollama_base_url: str = "http://localhost:11434"

    # vLLM (production GPU server — swap LLM_PROVIDER=vllm when ready)
    vllm_base_url: str = "http://localhost:8888/v1"
    vllm_api_key: str = "not-needed"
    vllm_model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct"

    # Groq (cloud fallback for teammates without local GPU)
    groq_api_key: str | None = os.getenv("GROQ_API_KEY")
    groq_model: str = os.getenv("GROQ_MODEL", "qwen/qwen3.6-27b")
    # Custom OpenAI-compatible endpoint (Unsloth Studio, llama.cpp, etc.)
    #custom_openai_model: str = "jackrong/Qwopus3.5-4B-Coder-MTP-GGUF:Q4_K_M"
    custom_openai_model: str = ""
    custom_openai_base_url: str = ""
    custom_openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")

    # ── Data service ─────────────────────────────────────────────────────────
    data_service_host: str = "0.0.0.0"
    data_service_port: int = 8000

    def provider_errors(self) -> list[str]:
        """Return selected-provider configuration errors without exposing values."""
        required = {
            "ollama": (("OLLAMA_MODEL", self.ollama_model), ("OLLAMA_BASE_URL", self.ollama_base_url)),
            "vllm": (("VLLM_MODEL", self.vllm_model), ("VLLM_BASE_URL", self.vllm_base_url)),
            "groq": (("GROQ_MODEL", self.groq_model), ("GROQ_API_KEY", self.groq_api_key)),
            "custom_openai_compatible_endpoint": (("CUSTOM_OPENAI_MODEL", self.custom_openai_model), ("CUSTOM_OPENAI_BASE_URL", self.custom_openai_base_url)),
        }
        if self.llm_provider not in required:
            return ["LLM_PROVIDER is not supported."]
        return [f"{name} is required for {self.llm_provider}." for name, value in required[self.llm_provider] if not value]


# Singleton — import this everywhere instead of re-instantiating
settings = Settings()
