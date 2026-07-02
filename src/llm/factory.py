"""
LLM factory — returns the correct LangChain chat model based on LLM_PROVIDER env var.

Supported providers:
  - ollama  : local GGUF served via Ollama daemon (dev/testing phase)
  - vllm    : OpenAI-compatible production GPU server
  - groq    : cloud fallback for teammates without local GPU

Switching provider = change LLM_PROVIDER in .env. Zero code change required.
"""

from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from config.pydantic.settings import settings


def get_llm(streaming: bool = True) -> BaseChatModel:
    """
    Return a configured LangChain chat model for the current LLM_PROVIDER.

    Args:
        streaming: If True, enables token streaming (used by answer_generation).

    Returns:
        A ready-to-use BaseChatModel instance.

    Raises:
        ValueError: If LLM_PROVIDER is not a recognised provider.
    """
    match settings.llm_provider:
        case "ollama":
            # ChatOllama doesn't use a separate streaming flag — it streams by
            # default when invoked via .stream(). We store the param for parity.
            return ChatOllama(
                model=settings.ollama_model,
                base_url=settings.ollama_base_url,
            )

        case "vllm":
            # vLLM exposes an OpenAI-compatible API — reuse langchain-openai.
            return ChatOpenAI(
                model="meta-llama/Meta-Llama-3.1-8B-Instruct",
                base_url=settings.vllm_base_url,
                api_key=settings.vllm_api_key,
                streaming=streaming,
            )
        case "custom_openai_compatible_endpoint":
            return ChatOpenAI(
                model=settings.custom_openai_model,
                base_url=settings.custom_openai_base_url,
                api_key=settings.custom_openai_api_key,
                streaming=streaming,
                extra_body={"enable_thinking": False},
            )
        case "groq":
            # Only hide reasoning tokens during streaming (answer_generation).
            # Non-streaming nodes (query_understanding, memory, etc.) need
            # the full response — the thinking model can otherwise put all
            # output into the hidden reasoning block and return empty content.
            groq_kwargs = dict(
                model=settings.groq_model,
                api_key=settings.groq_api_key,
                streaming=streaming,
            )
            if streaming:
                groq_kwargs["reasoning_format"] = "hidden"
            return ChatGroq(**groq_kwargs)

        case _:
            raise ValueError(
                f"Unknown LLM_PROVIDER: '{settings.llm_provider}'. "
                "Valid options: ollama | vllm | groq | custom_openai_compatible_endpoint"
            )
