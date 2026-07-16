from unittest.mock import MagicMock, patch

import pytest

from src.llm.factory import get_llm
from src.utils import parse_llm_json


@patch("src.llm.factory.ChatOllama")
@patch("src.llm.factory.settings")
def test_ollama_disables_hidden_reasoning_and_bounds_output(mock_settings, mock_chat_ollama):
    mock_settings.provider_errors.return_value = []
    mock_settings.llm_provider = "ollama"
    mock_settings.ollama_model = "qwen3:8b"
    mock_settings.ollama_base_url = "http://host.docker.internal:11434"
    mock_chat_ollama.return_value = MagicMock()

    get_llm(streaming=True)

    mock_chat_ollama.assert_called_once_with(
        model="qwen3:8b",
        base_url="http://host.docker.internal:11434",
        reasoning=False,
        num_predict=512,
        temperature=0,
    )


@patch("src.llm.factory.ChatOpenAI")
@patch("src.llm.factory.settings")
def test_custom_endpoint_disables_thinking_and_bounds_output(mock_settings, mock_chat_openai):
    mock_settings.provider_errors.return_value = []
    mock_settings.llm_provider = "custom_openai_compatible_endpoint"
    mock_settings.custom_openai_model = "qwen"
    mock_settings.custom_openai_base_url = "http://example.test/v1"
    mock_settings.custom_openai_api_key = "test-key"

    get_llm(streaming=True)

    mock_chat_openai.assert_called_once_with(
        model="qwen",
        base_url="http://example.test/v1",
        api_key="test-key",
        streaming=True,
        temperature=0,
        max_tokens=512,
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )


@pytest.mark.parametrize("model", ["qwen/qwen3.6-27b", "qwen/qwen3-32b"])
@patch("src.llm.factory.ChatGroq")
@patch("src.llm.factory.settings")
def test_groq_qwen_disables_reasoning(mock_settings, mock_chat_groq, model):
    mock_settings.provider_errors.return_value = []
    mock_settings.llm_provider = "groq"
    mock_settings.groq_model = model
    mock_settings.groq_api_key = "test-key"

    get_llm(streaming=False)

    mock_chat_groq.assert_called_once_with(
        model=model,
        api_key="test-key",
        streaming=False,
        reasoning_effort="none",
    )


@pytest.mark.parametrize(
    "model",
    ["groq/compound", "llama-3.3-70b-versatile", "openai/gpt-oss-20b"],
)
@patch("src.llm.factory.ChatGroq")
@patch("src.llm.factory.settings")
def test_other_groq_models_do_not_receive_qwen_reasoning_options(
    mock_settings, mock_chat_groq, model
):
    mock_settings.provider_errors.return_value = []
    mock_settings.llm_provider = "groq"
    mock_settings.groq_model = model
    mock_settings.groq_api_key = "test-key"

    get_llm(streaming=True)

    mock_chat_groq.assert_called_once_with(
        model=model,
        api_key="test-key",
        streaming=True,
    )


def test_parse_llm_json_ignores_qwen_think_block():
    raw = '<think>internal reasoning</think>\n{"route": "query_routing"}'

    assert parse_llm_json(raw) == {"route": "query_routing"}
